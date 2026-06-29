"""Unit tests — co-aprovação / dupla assinatura (spec-controlos §4.1, Art. 54).

Cobre as regras puras (`atos_rules`), os endpoints de `routes/atos.py` e o gate
de pagamentos em `routes/finances.py`. Sem DB real (mock_db). A colecção `atos`
não está pré-ligada no `conftest.mock_db` — é ligada em-teste por `_wire_atos`.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from atos_rules import evaluate_status, requisitos_for_tipo
from models import AtoCreate, AtoExecute, AtoSign, TransactionCreate, User
from routes import atos as atos_route
from routes import finances as finances_route

pytestmark = pytest.mark.unit


# --------------------------------------------------------------------------- #
# Factories
# --------------------------------------------------------------------------- #


def _user(role="socio", cargo="socio", privileges=None, uid=None) -> User:
    return User(
        id=uid or str(uuid.uuid4()),
        name=f"Test {role}",
        email=f"{uuid.uuid4().hex[:6]}@example.cv",
        role=role,
        status="ativo",
        cargo=cargo,
        privileges=privileges or [],
        consent_data=True,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def _request():
    """Fake Request para satisfazer assinaturas dos endpoints atos. O
    create_audit_log lê client.host + headers via extract_request_meta."""

    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test", "origin": "https://accta.cv"}

    return _R()


def _sig(cargo, decisao="aprovado", user_id=None) -> dict:
    return {
        "user_id": user_id or str(uuid.uuid4()),
        "cargo": cargo,
        "decisao": decisao,
        "signed_at": "2026-05-23T00:00:00+00:00",
    }


def _wire_atos(mock_db, doc=None, find_list=None):
    """Liga uma colecção `atos` ao fake_db (não pré-ligada no conftest)."""
    coll = MagicMock(name="atos")
    coll.find_one = AsyncMock(return_value=doc)
    coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
    coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    cur = MagicMock()
    cur.to_list = AsyncMock(return_value=find_list or [])
    cur.sort = MagicMock(return_value=cur)
    coll.find = MagicMock(return_value=cur)
    mock_db.atos = coll
    return coll


def _wire_sign_atomic(monkeypatch, doc):
    """Substitui `database.sign_ato_atomic` (importado em `routes/atos.py`) por um
    fake fiel que opera sobre `doc` em memória — a assinatura+reapuramento corre
    sob lock no DAO real, aqui simula-se a transação. Espelha o padrão de
    `cast_ballot`/`register_event_attendee` nos outros testes unitários. Devolve o
    AsyncMock para asserções; o `doc` é mutado in-place (status/assinaturas)."""

    async def _fake(ato_id, user_id, assinatura, compute_status):
        if doc is None:
            return {"outcome": "not_found"}
        if doc.get("status") != "pendente":
            return {"outcome": "not_pending"}
        if any(a.get("user_id") == user_id for a in (doc.get("assinaturas") or [])):
            return {"outcome": "already_signed"}
        novas = list(doc.get("assinaturas") or []) + [assinatura]
        doc["assinaturas"] = novas
        doc["status"] = compute_status(novas, doc.get("requisitos") or {})
        return {"outcome": "signed", "ato": doc}

    mock = AsyncMock(side_effect=_fake)
    monkeypatch.setattr(atos_route, "sign_ato_atomic", mock)
    return mock


# --------------------------------------------------------------------------- #
# Regras puras
# --------------------------------------------------------------------------- #


class TestRequisitos:
    def test_vinculativo(self):
        assert requisitos_for_tipo("vinculativo") == {
            "min_direcao": 2,
            "exige_presidente": True,
            "exige_tesoureiro": False,
        }

    def test_pagamento_exige_tesoureiro(self):
        assert requisitos_for_tipo("pagamento")["exige_tesoureiro"] is True

    def test_devolve_copia_independente(self):
        r = requisitos_for_tipo("pagamento")
        r["min_direcao"] = 99
        assert requisitos_for_tipo("pagamento")["min_direcao"] == 2


class TestEvaluateStatus:
    def test_sem_assinaturas_pendente(self):
        assert evaluate_status([], requisitos_for_tipo("vinculativo")) == "pendente"

    def test_vinculativo_aprova_2_direcao_incl_presidente(self):
        sigs = [_sig("dir_presidente"), _sig("dir_vogal")]
        assert evaluate_status(sigs, requisitos_for_tipo("vinculativo")) == "aprovado"

    def test_vinculativo_2_direcao_sem_presidente_pendente(self):
        sigs = [_sig("dir_tesoureiro"), _sig("dir_vogal")]
        assert evaluate_status(sigs, requisitos_for_tipo("vinculativo")) == "pendente"

    def test_vinculativo_so_presidente_falta_segundo(self):
        assert evaluate_status([_sig("dir_presidente")], requisitos_for_tipo("vinculativo")) == "pendente"

    def test_pagamento_sem_tesoureiro_pendente(self):
        # 2 Direção incl. Presidente, mas sem Tesoureiro.
        sigs = [_sig("dir_presidente"), _sig("dir_vogal")]
        assert evaluate_status(sigs, requisitos_for_tipo("pagamento")) == "pendente"

    def test_pagamento_aprova_presidente_e_tesoureiro(self):
        # Presidente conta como 1 dos 2 da Direção; Tesoureiro satisfaz o resto.
        sigs = [_sig("dir_presidente"), _sig("dir_tesoureiro")]
        assert evaluate_status(sigs, requisitos_for_tipo("pagamento")) == "aprovado"

    def test_rejeicao_fecha(self):
        sigs = [_sig("dir_presidente"), _sig("dir_vogal", "rejeitado")]
        assert evaluate_status(sigs, requisitos_for_tipo("vinculativo")) == "rejeitado"

    def test_nao_direcao_nao_conta(self):
        sigs = [_sig("dir_presidente"), _sig("socio")]
        assert evaluate_status(sigs, requisitos_for_tipo("vinculativo")) == "pendente"


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestCreateAto:
    async def test_socio_403(self, mock_db):
        _wire_atos(mock_db)
        with pytest.raises(HTTPException) as e:
            await atos_route.create_ato(
                AtoCreate(tipo="vinculativo", descricao="X"), _request(), current_user=_user("socio", "socio")
            )
        assert e.value.status_code == 403

    async def test_direcao_cria_pendente(self, mock_db):
        coll = _wire_atos(mock_db)
        ato = await atos_route.create_ato(
            AtoCreate(tipo="vinculativo", descricao="Contrato de fornecimento"),
            _request(),
            current_user=_user("socio", "dir_vogal"),
        )
        assert ato.status == "pendente"
        assert ato.requisitos["exige_tesoureiro"] is False
        coll.insert_one.assert_awaited_once()

    async def test_pagamento_sem_valor_400(self, mock_db):
        _wire_atos(mock_db)
        with pytest.raises(HTTPException) as e:
            await atos_route.create_ato(
                AtoCreate(tipo="pagamento", descricao="Pagamento"), _request(), current_user=_user("admin", "dir_presidente")
            )
        assert e.value.status_code == 400

    async def test_tipo_invalido_400(self, mock_db):
        _wire_atos(mock_db)
        with pytest.raises(HTTPException) as e:
            await atos_route.create_ato(AtoCreate(tipo="xpto", descricao="Y"), _request(), current_user=_user("admin"))
        assert e.value.status_code == 400

    async def test_aviso_de_criacao_aponta_pendencias(self, mock_db, monkeypatch):
        """spec 015 (US2): o aviso de um Ato novo (pendente) à Direção leva ao
        painel acionável `/pendencias`, não à área genérica de co-aprovações."""
        _wire_atos(mock_db)
        notify = AsyncMock()
        monkeypatch.setattr(atos_route, "notify_users", notify)
        monkeypatch.setattr(atos_route, "members_of_orgao", AsyncMock(return_value=["d1", "d2"]))
        await atos_route.create_ato(
            AtoCreate(tipo="vinculativo", descricao="Contrato"), _request(), current_user=_user("socio", "dir_vogal")
        )
        notify.assert_awaited_once()
        assert notify.await_args.args[4] == atos_route._LINK_PENDENTE


@pytest.mark.asyncio
class TestSignAto:
    def _pendente(self, tipo="vinculativo", assinaturas=None):
        return {
            "id": "a1",
            "tipo": tipo,
            "status": "pendente",
            "requisitos": requisitos_for_tipo(tipo),
            "created_by": "prop",
            "assinaturas": assinaturas or [],
        }

    async def test_nao_direcao_403(self, mock_db):
        _wire_atos(mock_db, doc=self._pendente())
        with pytest.raises(HTTPException) as e:
            await atos_route.sign_ato(
                "a1", AtoSign(decisao="aprovado"), _request(), current_user=_user("financeiro", "socio", ["manage_finances"])
            )
        assert e.value.status_code == 403

    async def test_decisao_invalida_400(self, mock_db):
        _wire_atos(mock_db, doc=self._pendente())
        with pytest.raises(HTTPException) as e:
            await atos_route.sign_ato("a1", AtoSign(decisao="talvez"), _request(), current_user=_user("socio", "dir_vogal"))
        assert e.value.status_code == 400

    async def test_status_nao_pendente_409(self, mock_db, monkeypatch):
        doc = self._pendente()
        doc["status"] = "aprovado"
        _wire_atos(mock_db, doc=doc)
        _wire_sign_atomic(monkeypatch, doc)
        with pytest.raises(HTTPException) as e:
            await atos_route.sign_ato("a1", AtoSign(decisao="aprovado"), _request(), current_user=_user("socio", "dir_vogal"))
        assert e.value.status_code == 400

    async def test_assinante_duplicado_409(self, mock_db, monkeypatch):
        doc = self._pendente(assinaturas=[_sig("dir_vogal", user_id="dup")])
        _wire_atos(mock_db, doc=doc)
        _wire_sign_atomic(monkeypatch, doc)
        with pytest.raises(HTTPException) as e:
            await atos_route.sign_ato(
                "a1", AtoSign(decisao="aprovado"), _request(), current_user=_user("socio", "dir_presidente", uid="dup")
            )
        # Idempotência de assinatura duplicada → 409 (era 400 antes do lock atómico).
        assert e.value.status_code == 409

    async def test_segunda_assinatura_aprova(self, mock_db, monkeypatch):
        # Vogal já assinou; o Presidente assina → 2 Direção incl. Presidente → aprovado.
        doc = self._pendente(assinaturas=[_sig("dir_vogal", user_id="v1")])
        _wire_atos(mock_db, doc=doc)
        mock = _wire_sign_atomic(monkeypatch, doc)
        notify = AsyncMock()
        monkeypatch.setattr(atos_route, "notify_users", notify)
        await atos_route.sign_ato(
            "a1", AtoSign(decisao="aprovado"), _request(), current_user=_user("socio", "dir_presidente", uid="pres")
        )
        mock.assert_awaited_once()
        assert doc["status"] == "aprovado"
        assert len(doc["assinaturas"]) == 2
        # spec 015 (C2): Ato DECIDIDO (aprovado) mantém o link de co-aprovações (não /pendencias)
        assert notify.await_args.args[4] == atos_route._LINK

    async def test_rejeicao_fecha(self, mock_db, monkeypatch):
        doc = self._pendente()
        _wire_atos(mock_db, doc=doc)
        _wire_sign_atomic(monkeypatch, doc)
        await atos_route.sign_ato(
            "a1",
            AtoSign(decisao="rejeitado", motivo="Motivo de teste"),  # motivo obrigatório (spec 011)
            _request(),
            current_user=_user("socio", "dir_presidente"),
        )
        assert doc["status"] == "rejeitado"

    async def test_locked_contencao_409(self, mock_db, monkeypatch):
        # lock_timeout esgotado (assinatura concorrente segura o lock) → outcome
        # "locked" → 409 (contenção transitória, retry) em vez de 500 opaco.
        doc = self._pendente()
        _wire_atos(mock_db, doc=doc)
        monkeypatch.setattr(atos_route, "sign_ato_atomic", AsyncMock(return_value={"outcome": "locked"}))
        with pytest.raises(HTTPException) as e:
            await atos_route.sign_ato(
                "a1", AtoSign(decisao="aprovado"), _request(), current_user=_user("socio", "dir_presidente")
            )
        assert e.value.status_code == 409


@pytest.mark.asyncio
class TestExecuteAto:
    def _aprovado_pagamento(self, **kw):
        base = {
            "id": "a1",
            "tipo": "pagamento",
            "status": "aprovado",
            "valor": 5000.0,
            "descricao": "Pagamento a fornecedor",
            "created_by": "prop",
            "transaction_id": None,
        }
        base.update(kw)
        return base

    async def test_nao_tesoureiro_403(self, mock_db):
        _wire_atos(mock_db, doc=self._aprovado_pagamento())
        with pytest.raises(HTTPException) as e:
            await atos_route.execute_ato("a1", AtoExecute(), _request(), current_user=_user("socio", "dir_vogal"))
        assert e.value.status_code == 403

    async def test_nao_aprovado_400(self, mock_db):
        _wire_atos(mock_db, doc=self._aprovado_pagamento(status="pendente"))
        with pytest.raises(HTTPException) as e:
            await atos_route.execute_ato("a1", AtoExecute(), _request(), current_user=_user("socio", "dir_tesoureiro"))
        assert e.value.status_code == 400

    async def test_vinculativo_nao_executavel_400(self, mock_db):
        _wire_atos(mock_db, doc=self._aprovado_pagamento(tipo="vinculativo", valor=None))
        with pytest.raises(HTTPException) as e:
            await atos_route.execute_ato("a1", AtoExecute(), _request(), current_user=_user("admin"))
        assert e.value.status_code == 400

    async def test_executa_cria_despesa_ligada(self, mock_db, monkeypatch):
        coll = _wire_atos(mock_db, doc=self._aprovado_pagamento())
        notify = AsyncMock()
        monkeypatch.setattr(atos_route, "notify_users", notify)
        await atos_route.execute_ato(
            "a1", AtoExecute(category="operacional"), _request(), current_user=_user("socio", "dir_tesoureiro", uid="tes")
        )
        mock_db.transactions.insert_one.assert_awaited_once()
        tx = mock_db.transactions.insert_one.call_args.args[0]
        assert tx["type"] == "despesa" and tx["ato_id"] == "a1" and tx["amount"] == 5000.0
        upd = coll.update_one.call_args.args[1]["$set"]
        assert upd["status"] == "executado" and upd["transaction_id"]
        # spec 015 (C2): Ato DECIDIDO (executado) mantém o link de co-aprovações (não /pendencias)
        assert notify.await_args.args[4] == atos_route._LINK

    async def test_categoria_invalida_400(self, mock_db):
        _wire_atos(mock_db, doc=self._aprovado_pagamento())
        with pytest.raises(HTTPException) as e:
            await atos_route.execute_ato(
                "a1", AtoExecute(category="inexistente"), _request(), current_user=_user("admin")
            )
        assert e.value.status_code == 400


@pytest.mark.asyncio
class TestCancelAto:
    def _pendente(self):
        return {"id": "a1", "tipo": "vinculativo", "status": "pendente", "created_by": "prop"}

    async def test_proponente_cancela(self, mock_db):
        coll = _wire_atos(mock_db, doc=self._pendente())
        await atos_route.cancel_ato("a1", _request(), current_user=_user("socio", "socio", uid="prop"))
        assert coll.update_one.call_args.args[1]["$set"]["status"] == "cancelado"

    async def test_outro_socio_403(self, mock_db):
        _wire_atos(mock_db, doc=self._pendente())
        with pytest.raises(HTTPException) as e:
            await atos_route.cancel_ato("a1", _request(), current_user=_user("socio", "socio", uid="outro"))
        assert e.value.status_code == 403

    async def test_admin_cancela(self, mock_db):
        coll = _wire_atos(mock_db, doc=self._pendente())
        await atos_route.cancel_ato("a1", _request(), current_user=_user("admin"))
        assert coll.update_one.call_args.args[1]["$set"]["status"] == "cancelado"

    async def test_nao_pendente_400(self, mock_db):
        doc = self._pendente()
        doc["status"] = "aprovado"
        _wire_atos(mock_db, doc=doc)
        with pytest.raises(HTTPException) as e:
            await atos_route.cancel_ato("a1", _request(), current_user=_user("admin"))
        assert e.value.status_code == 400


@pytest.mark.asyncio
class TestPaymentGate:
    def _despesa(self, amount):
        return TransactionCreate(
            type="despesa", category="operacional", description="Compra", amount=amount, date="2026-05-23"
        )

    async def test_despesa_acima_limiar_bloqueada(self, mock_db, financeiro_user):
        mock_db.finance_settings.find_one = AsyncMock(
            return_value={"id": "finance_settings", "coaprovacao_limiar": 1000.0}
        )
        with pytest.raises(HTTPException) as e:
            await finances_route.create_transaction(self._despesa(5000), _request(), current_user=financeiro_user)
        assert e.value.status_code == 400

    async def test_despesa_abaixo_limiar_passa(self, mock_db, financeiro_user):
        mock_db.finance_settings.find_one = AsyncMock(
            return_value={"id": "finance_settings", "coaprovacao_limiar": 1000.0}
        )
        tx = await finances_route.create_transaction(self._despesa(500), _request(), current_user=financeiro_user)
        assert tx.type == "despesa"
        mock_db.transactions.insert_one.assert_awaited_once()

    async def test_limiar_zero_desligado(self, mock_db, financeiro_user):
        # finance_settings.find_one → None (default) ⇒ limiar 0 ⇒ despesa grande passa.
        tx = await finances_route.create_transaction(self._despesa(999999), _request(), current_user=financeiro_user)
        assert tx.type == "despesa"

    async def test_receita_nao_afetada_pelo_gate(self, mock_db, financeiro_user):
        mock_db.finance_settings.find_one = AsyncMock(
            return_value={"id": "finance_settings", "coaprovacao_limiar": 1000.0}
        )
        data = TransactionCreate(
            type="receita", category="quotas", description="Quota", amount=5000, date="2026-05-23"
        )
        tx = await finances_route.create_transaction(data, _request(), current_user=financeiro_user)
        assert tx.type == "receita"
