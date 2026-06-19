"""Unit tests — Balancetes e auditoria do CF (spec-ciclo §5, Art. 34/37).

Cobre os endpoints de balancetes em `routes/prestacao_contas.py` e a aceitação
de `proof_url` no PATCH de transação (`routes/finances.py`). Sem DB real
(mock_db). `balancetes` não está pré-ligada no conftest — ligada em-teste.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from models import BalanceteAuditar, BalanceteCreate, TransactionUpdate, User
from routes import finances as fin_route
from routes import prestacao_contas as pc

pytestmark = pytest.mark.unit


def _request():
    """Fake Request para satisfazer a assinatura de update_transaction."""

    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test", "origin": "https://accta.cv"}

    return _R()


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


def _tesoureiro():
    return _user("financeiro", "dir_tesoureiro", ["manage_finances"])


def _cf(cargo="cf_presidente"):
    return _user("socio", cargo, ["view_finances_readonly"])


def _coll(find_one=None, find_list=None):
    coll = MagicMock()
    coll.find_one = AsyncMock(return_value=find_one)
    coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
    coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    cur = MagicMock()
    cur.to_list = AsyncMock(return_value=find_list or [])
    cur.sort = MagicMock(return_value=cur)
    cur.limit = MagicMock(return_value=cur)
    coll.find = MagicMock(return_value=cur)
    return coll


def _wire(mock_db, *, bal=None, bal_list=None, doc_exists=True):
    mock_db.balancetes = _coll(find_one=bal, find_list=bal_list)
    mock_db.documents.find_one = AsyncMock(return_value=({"id": "doc1"} if doc_exists else None))
    return mock_db


def _balancete(**kw):
    base = {
        "id": "b1",
        "tipo": "periodico",
        "periodo": "2026-03",
        "exercicio_ano": 2026,
        "snapshot": {"total_receitas": 0, "total_despesas": 0},
        "published": True,
        "published_by": "tes1",
        "cf_audit": None,
    }
    base.update(kw)
    return base


# --------------------------------------------------------------------------- #
# Publicar (Tesoureiro)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestPublishBalancete:
    async def test_socio_403(self, mock_db):
        _wire(mock_db)
        with pytest.raises(HTTPException) as e:
            await pc.publish_balancete(
                BalanceteCreate(periodo="2026-03", exercicio_ano=2026), current_user=_user("socio")
            )
        assert e.value.status_code == 403

    async def test_cf_readonly_nao_publica_403(self, mock_db):
        # CF tem view_finances_readonly mas NÃO manage_finances → não pode publicar.
        _wire(mock_db)
        with pytest.raises(HTTPException) as e:
            await pc.publish_balancete(
                BalanceteCreate(periodo="2026-03", exercicio_ano=2026), current_user=_cf()
            )
        assert e.value.status_code == 403

    async def test_tesoureiro_publica_congela_snapshot(self, mock_db, monkeypatch):
        _wire(mock_db)
        sentinel = {
            "total_receitas": 1000,
            "total_despesas": 300,
            "resultado_liquido": 700,
            "receitas_por_categoria": {"quotas": 1000},
            "despesas_por_categoria": {"operacional": 300},
            "total_transacoes": 2,
        }
        monkeypatch.setattr(pc, "compute_financial_summary", AsyncMock(return_value=sentinel))
        out = await pc.publish_balancete(
            BalanceteCreate(periodo="2026-03", exercicio_ano=2026, month=3), current_user=_tesoureiro()
        )
        assert out.published is True
        assert out.published_by is not None
        doc = mock_db.balancetes.insert_one.call_args.args[0]
        assert doc["snapshot"] == sentinel  # snapshot congelado no doc

    async def test_documento_inexistente_400(self, mock_db):
        _wire(mock_db, doc_exists=False)
        with pytest.raises(HTTPException) as e:
            await pc.publish_balancete(
                BalanceteCreate(periodo="2026-03", exercicio_ano=2026, document_id="doc-x"),
                current_user=_tesoureiro(),
            )
        assert e.value.status_code == 400


# --------------------------------------------------------------------------- #
# Ver
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestListGet:
    async def test_view_readonly_le_lista(self, mock_db):
        _wire(mock_db, bal_list=[_balancete()])
        out = await pc.list_balancetes(current_user=_cf())
        assert out["total"] == 1

    async def test_socio_sem_view_403(self, mock_db):
        _wire(mock_db, bal_list=[_balancete()])
        with pytest.raises(HTTPException) as e:
            await pc.list_balancetes(current_user=_user("socio"))
        assert e.value.status_code == 403

    async def test_get_404(self, mock_db):
        _wire(mock_db, bal=None)
        with pytest.raises(HTTPException) as e:
            await pc.get_balancete("b1", current_user=_tesoureiro())
        assert e.value.status_code == 404


# --------------------------------------------------------------------------- #
# Auditar (Conselho Fiscal)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestAuditar:
    async def test_cf_audita_ok(self, mock_db):
        _wire(mock_db, bal=_balancete())
        out = await pc.auditar_balancete(
            "b1", BalanceteAuditar(conferido=True, observacoes="Tudo conferido"), current_user=_cf()
        )
        assert out["cf_audit"]["conferido"] is True
        assert out["cf_audit"]["audited_by"] is not None
        set_ = mock_db.balancetes.update_one.call_args.args[1]["$set"]
        assert set_["cf_audit"]["conferido"] is True

    async def test_financeiro_nao_cf_403(self, mock_db):
        # manage_finances NÃO basta para auditar — é capability do CF.
        _wire(mock_db, bal=_balancete())
        with pytest.raises(HTTPException) as e:
            await pc.auditar_balancete(
                "b1", BalanceteAuditar(conferido=True), current_user=_tesoureiro()
            )
        assert e.value.status_code == 403

    async def test_socio_403(self, mock_db):
        _wire(mock_db, bal=_balancete())
        with pytest.raises(HTTPException) as e:
            await pc.auditar_balancete("b1", BalanceteAuditar(conferido=True), current_user=_user("socio"))
        assert e.value.status_code == 403

    async def test_balancete_404(self, mock_db):
        _wire(mock_db, bal=None)
        with pytest.raises(HTTPException) as e:
            await pc.auditar_balancete("b1", BalanceteAuditar(conferido=True), current_user=_cf())
        assert e.value.status_code == 404

    async def test_admin_pode_auditar(self, mock_db):
        # admin entra via user_can(emit_cf_parecer) → can_emit_parecer_cf True.
        _wire(mock_db, bal=_balancete())
        out = await pc.auditar_balancete(
            "b1", BalanceteAuditar(conferido=False, observacoes="rever"), current_user=_user("admin")
        )
        assert out["cf_audit"]["conferido"] is False


# --------------------------------------------------------------------------- #
# proof_url no PATCH de transação (spec §5.6)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestProofUrlPatch:
    async def test_patch_aceita_proof_url(self, mock_db):
        mock_db.transactions.find_one = AsyncMock(return_value={"id": "t1", "type": "despesa"})
        await fin_route.update_transaction(
            "t1",
            TransactionUpdate(proof_url="https://x/comprovativo.pdf"),
            _request(),
            current_user=_tesoureiro(),
        )
        set_ = mock_db.transactions.update_one.call_args.args[1]["$set"]
        assert set_["proof_url"] == "https://x/comprovativo.pdf"
