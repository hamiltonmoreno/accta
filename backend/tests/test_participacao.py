"""Unit tests para participação do sócio (spec-voz-participacao-socio)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import BackgroundTasks, HTTPException
from starlette.requests import Request

from routes import participacao as p
from models import (
    EsclarecimentoCreate,
    HonorarioCreate,
    HonorarioLigar,
    PeticaoCreate,
    PeticaoEncaminhar,
    PropostaAGCreate,
    PropostaIncluir,
    PropostaTriagem,
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

    async def test_listar_agrega_assinaturas_numa_query(self, pet_env, socio_user):
        """A listagem busca as assinaturas da página em lote (1 query), não 2
        queries por petição (N+1)."""
        rows = [{"id": "p1", "titulo": "A"}, {"id": "p2", "titulo": "B"}]
        cur_p = MagicMock()
        cur_p.sort.return_value = cur_p
        cur_p.to_list = AsyncMock(return_value=rows)
        pet_env.peticoes.find = MagicMock(return_value=cur_p)
        assinaturas = [
            {"peticao_id": "p1", "user_id": socio_user.id},
            {"peticao_id": "p1", "user_id": "outro"},
            {"peticao_id": "p2", "user_id": "outro"},
        ]
        cur_a = MagicMock()
        cur_a.to_list = AsyncMock(return_value=assinaturas)
        pet_env.peticao_assinaturas.find = MagicMock(return_value=cur_a)

        out = await p.listar_peticoes(current_user=socio_user)

        by_id = {x["id"]: x for x in out}
        assert by_id["p1"]["signature_count"] == 2
        assert by_id["p1"]["viewer_has_signed"] is True
        assert by_id["p2"]["signature_count"] == 1
        assert by_id["p2"]["viewer_has_signed"] is False
        # 1 única query às assinaturas, com $in dos ids da página
        pet_env.peticao_assinaturas.find.assert_called_once()
        q = pet_env.peticao_assinaturas.find.call_args[0][0]
        assert q == {"peticao_id": {"$in": ["p1", "p2"]}}
        # e nenhum count_documents por petição (o padrão N+1 antigo)
        pet_env.peticao_assinaturas.count_documents.assert_not_awaited()

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

    async def test_encaminhar_requires_threshold_409(self, pet_env, admin_user):
        pet_env.peticoes.find_one = AsyncMock(return_value={"id": "p1", "status": "aberta"})
        with pytest.raises(HTTPException) as exc:
            await p.encaminhar_peticao("p1", PeticaoEncaminhar(), _req(), current_user=admin_user)
        assert exc.value.status_code == 409
        pet_env.peticoes.update_one.assert_not_awaited()


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

    async def test_responder_recurso_409(self, f3_env, admin_user):
        f3_env.reclamacoes.find_one = AsyncMock(return_value={"id": "r1", "status": "recurso"})
        with pytest.raises(HTTPException) as exc:
            await p.responder_reclamacao("r1", ReclamacaoResponder(texto="x"), _req(), current_user=admin_user)
        assert exc.value.status_code == 409
        f3_env.reclamacoes.update_one.assert_not_awaited()

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

    async def test_recurso_encerrada_409(self, f3_env, socio_user):
        f3_env.reclamacoes.find_one = AsyncMock(
            return_value={
                "id": "r1",
                "created_by": socio_user.id,
                "direcao_resposta": {"text": "r"},
                "status": "encerrada",
            }
        )
        with pytest.raises(HTTPException) as exc:
            await p.abrir_recurso("r1", _req(), current_user=socio_user)
        assert exc.value.status_code == 409
        f3_env.reclamacoes.update_one.assert_not_awaited()

    async def test_decidir_recurso_requires_mesa_403(self, f3_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await p.decidir_recurso("r1", RecursoDecisao(decisao="negado"), _req(), current_user=socio_user)
        assert exc.value.status_code == 403


# --------------------------------------------------------------------------- #
# 1.4 — Propostas e temas para a ordem de trabalhos
# --------------------------------------------------------------------------- #


@pytest.fixture
def f4_env(mock_db, monkeypatch):
    monkeypatch.setattr(p, "create_audit_log", AsyncMock())
    monkeypatch.setattr(p, "notify_users", AsyncMock())
    monkeypatch.setattr(p, "members_of_orgao", AsyncMock(return_value=["o1"]))
    _wire(mock_db, "propostas_ag")
    return mock_db


def _propostas(env, rows):
    cur = MagicMock()
    cur.sort.return_value = cur
    cur.to_list = AsyncMock(return_value=rows)
    env.propostas_ag.find = MagicMock(return_value=cur)


class TestProposta:
    async def test_criar_notifica_orgaos(self, f4_env, socio_user):
        res = await p.criar_proposta(
            PropostaAGCreate(titulo="Rever quotas", descricao="proposta de medida", tipo="medida"),
            _req(),
            current_user=socio_user,
        )
        assert res.status == "submetida"
        f4_env.propostas_ag.insert_one.assert_awaited()
        p.notify_users.assert_awaited_once()
        # Triagem cabe à Mesa AG + Direcção → members_of_orgao chamado para ambos.
        assert {c.args[0] for c in p.members_of_orgao.await_args_list} == {"mesa_ag", "direcao"}

    async def test_listar_membro_ve_proprias_e_publicas(self, f4_env, socio_user):
        _propostas(
            f4_env,
            [
                {"id": "a", "created_by": socio_user.id, "status": "submetida"},
                {"id": "b", "created_by": "outro", "status": "submetida"},  # escondida
                {"id": "c", "created_by": "outro", "status": "aceite"},  # pública
            ],
        )
        out = await p.listar_propostas(current_user=socio_user)
        assert {r["id"] for r in out} == {"a", "c"}

    async def test_listar_triage_ve_todas(self, f4_env, socio_user):
        socio_user.cargo = "ag_presidente"  # Mesa da AG
        _propostas(
            f4_env,
            [
                {"id": "a", "created_by": "x", "status": "submetida"},
                {"id": "b", "created_by": "y", "status": "recusada"},
            ],
        )
        out = await p.listar_propostas(current_user=socio_user)
        assert {r["id"] for r in out} == {"a", "b"}

    async def test_obter_terceiro_403(self, f4_env, socio_user):
        f4_env.propostas_ag.find_one = AsyncMock(
            return_value={"id": "p1", "created_by": "outro", "status": "submetida"}
        )
        with pytest.raises(HTTPException) as exc:
            await p.obter_proposta("p1", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_triar_requires_role_403(self, f4_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await p.triar_proposta("p1", PropostaTriagem(decisao="aceite"), _req(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_triar_aceite_notifica_autor(self, f4_env, socio_user):
        socio_user.cargo = "dir_presidente"  # Direcção pode triar
        f4_env.propostas_ag.find_one = AsyncMock(
            return_value={"id": "p1", "created_by": "autor", "titulo": "X", "status": "submetida"}
        )
        await p.triar_proposta(
            "p1", PropostaTriagem(decisao="aceite", decisao_motivo="relevante"), _req(), current_user=socio_user
        )
        f4_env.propostas_ag.update_one.assert_awaited()
        assert any(c.args[1] == "proposta_triada" for c in p.create_audit_log.await_args_list)
        p.notify_users.assert_awaited()

    async def test_triar_requires_pending_status_409(self, f4_env, admin_user):
        f4_env.propostas_ag.find_one = AsyncMock(return_value={"id": "p1", "status": "aceite"})
        with pytest.raises(HTTPException) as exc:
            await p.triar_proposta("p1", PropostaTriagem(decisao="recusada"), _req(), current_user=admin_user)
        assert exc.value.status_code == 409
        f4_env.propostas_ag.update_one.assert_not_awaited()

    async def test_incluir_requires_mesa_403(self, f4_env, socio_user):
        socio_user.cargo = "dir_presidente"  # Direcção tria mas NÃO inclui (só Mesa/admin)
        with pytest.raises(HTTPException) as exc:
            await p.incluir_proposta("p1", PropostaIncluir(), _req(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_incluir_ok(self, f4_env, admin_user):
        f4_env.propostas_ag.find_one = AsyncMock(
            return_value={"id": "p1", "created_by": "autor", "titulo": "X", "status": "aceite"}
        )
        await p.incluir_proposta(
            "p1", PropostaIncluir(assembleia_id="ag1", ordem_index=2), _req(), current_user=admin_user
        )
        f4_env.propostas_ag.update_one.assert_awaited()
        assert any(c.args[1] == "proposta_incluida" for c in p.create_audit_log.await_args_list)

    async def test_incluir_requires_accepted_status_409(self, f4_env, admin_user):
        f4_env.propostas_ag.find_one = AsyncMock(return_value={"id": "p1", "status": "submetida"})
        with pytest.raises(HTTPException) as exc:
            await p.incluir_proposta("p1", PropostaIncluir(), _req(), current_user=admin_user)
        assert exc.value.status_code == 409
        f4_env.propostas_ag.update_one.assert_not_awaited()


# --------------------------------------------------------------------------- #
# 1.2 — Membros honorários (Art. 8.4): nomeação + votação 2/3 via poll
# --------------------------------------------------------------------------- #


@pytest.fixture
def hon_env(mock_db, monkeypatch):
    monkeypatch.setattr(p, "create_audit_log", AsyncMock())
    monkeypatch.setattr(p, "notify_users", AsyncMock())
    monkeypatch.setattr(p, "notify_admins", AsyncMock())
    monkeypatch.setattr(p, "members_of_orgao", AsyncMock(return_value=["mesa1"]))
    monkeypatch.setattr(p, "voting_member_ids", AsyncMock(return_value=["v1", "v2", "v3"]))
    monkeypatch.setattr(p, "send_invite_email", AsyncMock(return_value={"status": "sent"}))
    monkeypatch.setattr(p, "next_member_id", AsyncMock(return_value="ACCTA-0042"))
    monkeypatch.setattr(p, "generate_qr_hash", lambda uid: "qr")
    monkeypatch.setattr(p, "resolve_link_base", lambda req: "https://portal.test")
    _wire(mock_db, "honorarios_nominations", "polls", "user_votes", "assembleias")
    return mock_db


def _votes(env, rows):
    cur = MagicMock()
    cur.to_list = AsyncMock(return_value=rows)
    env.user_votes.find = MagicMock(return_value=cur)


def _dir(user):
    user.cargo = "dir_presidente"  # Direcção
    return user


def _mesa(user):
    user.cargo = "ag_presidente"  # Mesa da AG
    return user


class TestHonorario:
    async def test_nomear_requires_direcao_403(self, hon_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await p.nomear_honorario(
                HonorarioCreate(nominee_name="Fulano", justificacao="serviços"), _req(), current_user=socio_user
            )
        assert exc.value.status_code == 403

    async def test_nomear_ok_direcao_notifica_mesa(self, hon_env, socio_user):
        _dir(socio_user)
        res = await p.nomear_honorario(
            HonorarioCreate(nominee_name="Fulano de Tal", justificacao="serviços relevantes"),
            _req(),
            current_user=socio_user,
        )
        assert res.status == "proposta"
        hon_env.honorarios_nominations.insert_one.assert_awaited()
        assert any(c.args[1] == "honorario_nomeado" for c in p.create_audit_log.await_args_list)
        p.notify_users.assert_awaited_once()  # Mesa da AG

    async def test_nomear_interno_invalido_422(self, hon_env, admin_user):
        hon_env.users.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await p.nomear_honorario(
                HonorarioCreate(nominee_name="Fulano", justificacao="x", nominee_user_id="u-x"),
                _req(),
                current_user=admin_user,
            )
        assert exc.value.status_code == 422

    async def test_listar_requires_orgao_403(self, hon_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await p.listar_honorarios(current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_abrir_votacao_requires_mesa_403(self, hon_env, socio_user):
        _dir(socio_user)  # Direcção nomeia mas NÃO abre votação (só Mesa/admin)
        with pytest.raises(HTTPException) as exc:
            await p.abrir_votacao_honorario("h1", _req(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_abrir_votacao_only_proposta_409(self, hon_env, admin_user):
        hon_env.honorarios_nominations.find_one = AsyncMock(
            return_value={"id": "h1", "status": "em_votacao", "nominee_name": "X", "justificacao": "y"}
        )
        with pytest.raises(HTTPException) as exc:
            await p.abrir_votacao_honorario("h1", _req(), current_user=admin_user)
        assert exc.value.status_code == 409

    async def test_abrir_votacao_ok_cria_poll_e_notifica_votantes(self, hon_env, admin_user):
        hon_env.honorarios_nominations.find_one = AsyncMock(
            return_value={"id": "h1", "status": "proposta", "nominee_name": "X", "justificacao": "y"}
        )
        await p.abrir_votacao_honorario("h1", _req(), current_user=admin_user)
        hon_env.polls.insert_one.assert_awaited()
        upd = hon_env.honorarios_nominations.update_one.await_args.args[1]["$set"]
        assert upd["status"] == "em_votacao" and upd["poll_id"]
        assert any(c.args[1] == "honorario_votacao_aberta" for c in p.create_audit_log.await_args_list)
        # Notifica só os votantes, com tipo "poll".
        last = p.notify_users.await_args
        assert last.args[0] == ["v1", "v2", "v3"] and last.args[1] == "poll"

    async def test_apurar_requires_mesa_403(self, hon_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await p.apurar_honorario("h1", _req(), BackgroundTasks(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_apurar_nao_em_votacao_409(self, hon_env, admin_user):
        hon_env.honorarios_nominations.find_one = AsyncMock(
            return_value={"id": "h1", "status": "proposta", "nominee_name": "X"}
        )
        with pytest.raises(HTTPException) as exc:
            await p.apurar_honorario("h1", _req(), BackgroundTasks(), current_user=admin_user)
        assert exc.value.status_code == 409

    async def test_apurar_exacto_dois_tercos_elege_interno(self, hon_env, admin_user):
        hon_env.honorarios_nominations.find_one = AsyncMock(
            return_value={
                "id": "h1",
                "status": "em_votacao",
                "poll_id": "poll1",
                "nominee_name": "X",
                "nominee_user_id": "u9",
            }
        )
        _votes(
            hon_env, [{"vote_option": 1}, {"vote_option": 1}, {"vote_option": 2}]
        )  # favor=2 base=3 → ceil(2)=2 → eleito
        await p.apurar_honorario("h1", _req(), BackgroundTasks(), current_user=admin_user)
        sets = [c.args[1]["$set"] for c in hon_env.honorarios_nominations.update_one.await_args_list]
        assert any(s.get("status") == "eleito" for s in sets)
        hon_env.users.update_one.assert_awaited()
        assert hon_env.users.update_one.await_args.args[1]["$set"]["member_category"] == "honorario"
        p.notify_admins.assert_awaited()

    async def test_apurar_just_below_rejeita(self, hon_env, admin_user):
        hon_env.honorarios_nominations.find_one = AsyncMock(
            return_value={
                "id": "h1",
                "status": "em_votacao",
                "poll_id": "poll1",
                "nominee_name": "X",
                "nominee_user_id": "u9",
            }
        )
        _votes(
            hon_env, [{"vote_option": 1}, {"vote_option": 2}, {"vote_option": 2}]
        )  # favor=1 base=3 → ceil(2)=2 → rejeitado
        await p.apurar_honorario("h1", _req(), BackgroundTasks(), current_user=admin_user)
        sets = [c.args[1]["$set"] for c in hon_env.honorarios_nominations.update_one.await_args_list]
        assert any(s.get("status") == "rejeitado" for s in sets)
        hon_env.users.update_one.assert_not_awaited()

    async def test_apurar_sem_votos_validos_rejeita(self, hon_env, admin_user):
        hon_env.honorarios_nominations.find_one = AsyncMock(
            return_value={
                "id": "h1",
                "status": "em_votacao",
                "poll_id": "poll1",
                "nominee_name": "X",
                "nominee_user_id": "u9",
            }
        )
        _votes(hon_env, [{"vote_option": 3}, {"vote_option": 3}])  # só abstenções → base=0 → rejeitado
        await p.apurar_honorario("h1", _req(), BackgroundTasks(), current_user=admin_user)
        sets = [c.args[1]["$set"] for c in hon_env.honorarios_nominations.update_one.await_args_list]
        assert any(s.get("status") == "rejeitado" for s in sets)

    async def test_apurar_externo_eleito_cria_convite(self, hon_env, admin_user):
        hon_env.honorarios_nominations.find_one = AsyncMock(
            return_value={
                "id": "h1",
                "status": "em_votacao",
                "poll_id": "poll1",
                "nominee_name": "Externo",
                "nominee_email": "ext@x.cv",
            }
        )
        hon_env.users.find_one = AsyncMock(return_value=None)  # email ainda não existe
        _votes(hon_env, [{"vote_option": 1}, {"vote_option": 1}])  # favor=2 base=2 → ceil(1.33)=2 → eleito
        # O convite vai por BackgroundTask depois do CAS irrevogável (um email falhado
        # não dá 500). Captura o BackgroundTasks e verifica que a task foi agendada.
        bt = BackgroundTasks()
        await p.apurar_honorario("h1", _req(), bt, current_user=admin_user)
        hon_env.users.insert_one.assert_awaited()
        new_user = hon_env.users.insert_one.await_args.args[0]
        assert new_user["status"] == "pendente_convite"
        assert new_user["member_category"] == "honorario"
        assert new_user["account_type"] == "member"
        # send_invite_email agendado (não awaited diretamente — corre após a resposta).
        assert any(t.func is p.send_invite_email for t in bt.tasks)

    async def test_apurar_email_de_membro_existente_eleva_sem_convite(self, hon_env, admin_user):
        # Email é identificador universal: se já é sócio, eleva (não cria conta nem envia convite).
        hon_env.honorarios_nominations.find_one = AsyncMock(
            return_value={
                "id": "h1",
                "status": "em_votacao",
                "poll_id": "poll1",
                "nominee_name": "Sócio Antigo",
                "nominee_email": "socio@x.cv",
            }
        )
        hon_env.users.find_one = AsyncMock(return_value={"id": "u-existente"})
        _votes(hon_env, [{"vote_option": 1}, {"vote_option": 1}])  # eleito
        await p.apurar_honorario("h1", _req(), BackgroundTasks(), current_user=admin_user)
        hon_env.users.insert_one.assert_not_awaited()
        p.send_invite_email.assert_not_awaited()
        assert hon_env.users.update_one.await_args.args[1]["$set"]["member_category"] == "honorario"

    # F6 — reconciliação com Assembleia (§2.4): ligar honorário apurado a uma deliberação.
    async def test_ligar_requires_mesa_403(self, hon_env, socio_user):
        with pytest.raises(HTTPException) as exc:
            await p.ligar_honorario_assembleia(
                "h1", HonorarioLigar(assembleia_id="ag1"), _req(), current_user=socio_user
            )
        assert exc.value.status_code == 403

    async def test_ligar_so_apurado_409(self, hon_env, admin_user):
        hon_env.honorarios_nominations.find_one = AsyncMock(return_value={"id": "h1", "status": "em_votacao"})
        with pytest.raises(HTTPException) as exc:
            await p.ligar_honorario_assembleia(
                "h1", HonorarioLigar(assembleia_id="ag1"), _req(), current_user=admin_user
            )
        assert exc.value.status_code == 409

    async def test_ligar_assembleia_inexistente_404(self, hon_env, admin_user):
        hon_env.honorarios_nominations.find_one = AsyncMock(return_value={"id": "h1", "status": "eleito"})
        hon_env.assembleias.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await p.ligar_honorario_assembleia(
                "h1", HonorarioLigar(assembleia_id="ag-x"), _req(), current_user=admin_user
            )
        assert exc.value.status_code == 404

    async def test_ligar_ok_regista_referencia(self, hon_env, admin_user):
        hon_env.honorarios_nominations.find_one = AsyncMock(return_value={"id": "h1", "status": "eleito"})
        hon_env.assembleias.find_one = AsyncMock(return_value={"id": "ag1"})
        await p.ligar_honorario_assembleia(
            "h1", HonorarioLigar(assembleia_id="ag1", deliberacao_id="del9"), _req(), current_user=admin_user
        )
        upd = hon_env.honorarios_nominations.update_one.await_args.args[1]["$set"]
        assert upd["assembleia_id"] == "ag1" and upd["deliberacao_id"] == "del9"
        assert any(c.args[1] == "honorario_ligado_assembleia" for c in p.create_audit_log.await_args_list)
