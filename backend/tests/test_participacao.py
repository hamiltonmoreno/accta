"""Unit tests para participação do sócio (spec-voz-participacao-socio).

F1 — Patrocínio de admissão (Art. 8.3): confirmação/recusa pelos padrinhos.
A colecção `patrocinios` não está pré-cablada no conftest — cablamos aqui.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from routes import participacao as p
from models import (
    EsclarecimentoCreate,
    PatrocinioRespond,
    PeticaoCreate,
    PeticaoEncaminhar,
    ReclamacaoCreate,
    ReclamacaoResponder,
    RecursoDecisao,
    RespostaTexto,
)

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _req() -> Request:
    return Request(
        {"type": "http", "method": "POST", "path": "/x", "headers": [], "client": ("127.0.0.1", 1), "query_string": b""}
    )


@pytest.fixture
def env(mock_db, monkeypatch):
    monkeypatch.setattr(p, "create_audit_log", AsyncMock())
    monkeypatch.setattr(p, "notify_admins", AsyncMock())
    mock_db.patrocinios = MagicMock(name="patrocinios")
    mock_db.patrocinios.find_one = AsyncMock(return_value=None)
    mock_db.patrocinios.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    mock_db.patrocinios.count_documents = AsyncMock(return_value=1)
    return mock_db


class TestConfirmar:
    async def test_non_voting_member_403(self, env, socio_user):
        socio_user.member_category = "honorario"  # honorário não vota/patrocina
        with pytest.raises(HTTPException) as exc:
            await p.confirmar_patrocinio("c1", _req(), PatrocinioRespond(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_non_sponsor_403(self, env, socio_user):
        env.patrocinios.find_one = AsyncMock(return_value=None)  # não é padrinho deste candidato
        with pytest.raises(HTTPException) as exc:
            await p.confirmar_patrocinio("c1", _req(), PatrocinioRespond(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_already_responded_409(self, env, socio_user):
        env.patrocinios.find_one = AsyncMock(
            return_value={"candidate_id": "c1", "sponsor_user_id": socio_user.id, "status": "confirmado"}
        )
        with pytest.raises(HTTPException) as exc:
            await p.confirmar_patrocinio("c1", _req(), PatrocinioRespond(), current_user=socio_user)
        assert exc.value.status_code == 409

    async def test_confirmar_flips_and_audits(self, env, socio_user):
        env.patrocinios.find_one = AsyncMock(
            return_value={"candidate_id": "c1", "sponsor_user_id": socio_user.id, "status": "pendente"}
        )
        result = await p.confirmar_patrocinio("c1", _req(), PatrocinioRespond(), current_user=socio_user)
        assert result["status"] == "confirmado"
        env.patrocinios.update_one.assert_awaited()
        assert any(c.args[1] == "patrocinio_confirmado" for c in p.create_audit_log.await_args_list)
        p.notify_admins.assert_not_awaited()  # só 1 confirmado

    async def test_second_confirmation_notifies_admins(self, env, socio_user):
        env.patrocinios.find_one = AsyncMock(
            return_value={"candidate_id": "c1", "sponsor_user_id": socio_user.id, "status": "pendente"}
        )
        env.patrocinios.count_documents = AsyncMock(return_value=2)  # 2.º confirmado completa
        env.users.find_one = AsyncMock(return_value={"name": "Cand"})
        await p.confirmar_patrocinio("c1", _req(), PatrocinioRespond(), current_user=socio_user)
        p.notify_admins.assert_awaited_once()


class TestRecusar:
    async def test_recusar_flips(self, env, socio_user):
        env.patrocinios.find_one = AsyncMock(
            return_value={"candidate_id": "c1", "sponsor_user_id": socio_user.id, "status": "pendente"}
        )
        result = await p.recusar_patrocinio(
            "c1", _req(), PatrocinioRespond(note="não conheço"), current_user=socio_user
        )
        assert result["status"] == "recusado"
        assert any(c.args[1] == "patrocinio_recusado" for c in p.create_audit_log.await_args_list)


class TestPendentes:
    async def test_inbox_lists_my_pending(self, env, socio_user):
        cur = MagicMock()
        cur.to_list = AsyncMock(return_value=[{"candidate_id": "c1", "status": "pendente", "created_at": "2026-05-21"}])
        env.patrocinios.find = MagicMock(return_value=cur)
        env.users.find_one = AsyncMock(return_value={"name": "Cand", "member_id": "ACCTA-0009"})
        result = await p.patrocinios_pendentes(current_user=socio_user)
        assert len(result) == 1
        assert result[0]["candidate_name"] == "Cand"
        assert result[0]["candidate_member_id"] == "ACCTA-0009"


# --------------------------------------------------------------------------- #
# 1.3 — Petição para AG extraordinária
# --------------------------------------------------------------------------- #


@pytest.fixture
def pet_env(mock_db, monkeypatch):
    monkeypatch.setattr(p, "create_audit_log", AsyncMock())
    monkeypatch.setattr(p, "notify_users", AsyncMock())
    monkeypatch.setattr(p, "members_of_orgao", AsyncMock(return_value=["mesa1"]))
    monkeypatch.setattr(p, "count_voting_members", AsyncMock(return_value=8))  # target = ceil(8*0.25) = 2
    for name in ("peticoes", "peticao_assinaturas"):
        coll = MagicMock(name=name)
        coll.find_one = AsyncMock(return_value=None)
        coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
        coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        coll.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        coll.count_documents = AsyncMock(return_value=0)
        cur = MagicMock()
        cur.sort.return_value = cur
        cur.to_list = AsyncMock(return_value=[])
        coll.find = MagicMock(return_value=cur)
        setattr(mock_db, name, coll)
    return mock_db


class TestPeticao:
    async def test_criar_requires_voting_403(self, pet_env, socio_user):
        socio_user.member_category = "honorario"
        with pytest.raises(HTTPException) as exc:
            await p.criar_peticao(
                PeticaoCreate(titulo="AG extra", fundamentacao="motivo"), _req(), current_user=socio_user
            )
        assert exc.value.status_code == 403

    async def test_criar_ok(self, pet_env, socio_user):
        res = await p.criar_peticao(
            PeticaoCreate(titulo="AG extraordinária", fundamentacao="motivo relevante"), _req(), current_user=socio_user
        )
        assert res.status == "aberta"
        pet_env.peticoes.insert_one.assert_awaited()

    async def test_assinar_reaches_threshold_notifies_once(self, pet_env, socio_user):
        pet_env.peticoes.find_one = AsyncMock(
            return_value={"id": "p1", "titulo": "X", "status": "aberta", "threshold_fraction": 0.25}
        )
        pet_env.peticao_assinaturas.count_documents = AsyncMock(return_value=2)  # atinge o alvo (2)
        res = await p.assinar_peticao("p1", _req(), current_user=socio_user)
        assert res["target_count"] == 2
        pet_env.peticoes.update_one.assert_awaited()  # vira "atingida"
        p.notify_users.assert_awaited_once()  # Mesa notificada uma vez

    async def test_assinar_below_threshold_no_notify(self, pet_env, socio_user):
        pet_env.peticoes.find_one = AsyncMock(
            return_value={"id": "p1", "titulo": "X", "status": "aberta", "threshold_fraction": 0.25}
        )
        pet_env.peticao_assinaturas.count_documents = AsyncMock(return_value=1)
        await p.assinar_peticao("p1", _req(), current_user=socio_user)
        pet_env.peticoes.update_one.assert_not_awaited()
        p.notify_users.assert_not_awaited()

    async def test_retirar_only_while_aberta_409(self, pet_env, socio_user):
        pet_env.peticoes.find_one = AsyncMock(return_value={"id": "p1", "status": "atingida"})
        with pytest.raises(HTTPException) as exc:
            await p.retirar_assinatura("p1", _req(), current_user=socio_user)
        assert exc.value.status_code == 409

    async def test_encaminhar_requires_mesa_403(self, pet_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await p.encaminhar_peticao("p1", PeticaoEncaminhar(), _req(), current_user=socio_user)
        assert exc.value.status_code == 403


# --------------------------------------------------------------------------- #
# 1.6 esclarecimentos / 1.5 reclamações
# --------------------------------------------------------------------------- #


def _wire(mock_db, *names):
    for name in names:
        coll = MagicMock(name=name)
        coll.find_one = AsyncMock(return_value=None)
        coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
        coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        cur = MagicMock()
        cur.sort.return_value = cur
        cur.to_list = AsyncMock(return_value=[])
        coll.find = MagicMock(return_value=cur)
        setattr(mock_db, name, coll)


@pytest.fixture
def f3_env(mock_db, monkeypatch):
    monkeypatch.setattr(p, "create_audit_log", AsyncMock())
    monkeypatch.setattr(p, "notify_users", AsyncMock())
    monkeypatch.setattr(p, "members_of_orgao", AsyncMock(return_value=["o1"]))
    _wire(mock_db, "esclarecimentos", "reclamacoes")
    return mock_db


class TestEsclarecimento:
    async def test_criar_notifica_orgao(self, f3_env, socio_user):
        res = await p.criar_esclarecimento(
            EsclarecimentoCreate(orgao_destino="direcao", assunto="Dúvida", pergunta="Qual o prazo?"),
            _req(),
            current_user=socio_user,
        )
        assert res.orgao_destino == "direcao"
        p.notify_users.assert_awaited_once()

    async def test_responder_terceiro_403(self, f3_env, socio_user):
        f3_env.esclarecimentos.find_one = AsyncMock(
            return_value={"id": "e1", "orgao_destino": "direcao", "created_by": "outro", "assunto": "X"}
        )
        with pytest.raises(HTTPException) as exc:
            await p.responder_esclarecimento("e1", RespostaTexto(texto="resp"), _req(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_responder_admin_ok(self, f3_env, admin_user):
        f3_env.esclarecimentos.find_one = AsyncMock(
            return_value={"id": "e1", "orgao_destino": "direcao", "created_by": "c", "assunto": "X"}
        )
        await p.responder_esclarecimento("e1", RespostaTexto(texto="resposta"), _req(), current_user=admin_user)
        f3_env.esclarecimentos.update_one.assert_awaited()
        p.notify_users.assert_awaited()

    async def test_obter_terceiro_403(self, f3_env, socio_user):
        f3_env.esclarecimentos.find_one = AsyncMock(
            return_value={"id": "e1", "orgao_destino": "mesa_ag", "created_by": "outro"}
        )
        with pytest.raises(HTTPException) as exc:
            await p.obter_esclarecimento("e1", current_user=socio_user)
        assert exc.value.status_code == 403


class TestReclamacao:
    async def test_criar_define_prazo_e_notifica(self, f3_env, socio_user):
        res = await p.criar_reclamacao(
            ReclamacaoCreate(assunto="Acto lesivo", descricao="detalhe"), _req(), current_user=socio_user
        )
        assert res.prazo_resposta is not None
        p.notify_users.assert_awaited_once()

    async def test_obter_terceiro_403(self, f3_env, socio_user):
        f3_env.reclamacoes.find_one = AsyncMock(return_value={"id": "r1", "created_by": "outro"})
        with pytest.raises(HTTPException) as exc:
            await p.obter_reclamacao("r1", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_responder_requires_direcao_403(self, f3_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await p.responder_reclamacao("r1", ReclamacaoResponder(texto="x"), _req(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_recurso_before_response_409(self, f3_env, socio_user):
        # sem resposta e prazo no futuro → não pode recorrer ainda.
        future = "2999-01-01T00:00:00+00:00"
        f3_env.reclamacoes.find_one = AsyncMock(
            return_value={"id": "r1", "created_by": socio_user.id, "prazo_resposta": future, "direcao_resposta": None}
        )
        with pytest.raises(HTTPException) as exc:
            await p.abrir_recurso("r1", _req(), current_user=socio_user)
        assert exc.value.status_code == 409

    async def test_recurso_after_response_ok(self, f3_env, socio_user):
        f3_env.reclamacoes.find_one = AsyncMock(
            return_value={"id": "r1", "created_by": socio_user.id, "direcao_resposta": {"text": "r"}}
        )
        await p.abrir_recurso("r1", _req(), current_user=socio_user)
        f3_env.reclamacoes.update_one.assert_awaited()

    async def test_decidir_recurso_requires_mesa_403(self, f3_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await p.decidir_recurso("r1", RecursoDecisao(decisao="negado"), _req(), current_user=socio_user)
        assert exc.value.status_code == 403
