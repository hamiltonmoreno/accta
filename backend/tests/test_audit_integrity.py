"""Testes do F4 — tamper-evidence do audit log (spec-verificacao-seguranca-saas
§8.1). Unit in-process com mock_db. O HMAC deriva do SECRET_KEY (fora da BD),
logo uma alteração pós-facto de uma entrada é detetável.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

pytestmark = pytest.mark.unit


def _cursor(items):
    cur = MagicMock()
    cur.sort = MagicMock(return_value=cur)
    cur.skip = MagicMock(return_value=cur)
    cur.limit = MagicMock(return_value=cur)
    cur.to_list = AsyncMock(return_value=items)
    return cur


def _entry(**over):
    base = {
        "id": "a1", "user_id": "u", "action": "login_success", "target_id": None,
        "ip": "1.2.3.4", "user_agent": "ua", "details": {"k": "v"},
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    base.update(over)
    return base


# ===================== hash determinístico e sensível ===================== #
def test_audit_entry_hash_deterministic_and_field_sensitive():
    import helpers

    base = _entry()
    h1 = helpers.audit_entry_hash(base)
    assert h1 == helpers.audit_entry_hash(dict(base))  # determinístico
    assert helpers.audit_entry_hash(_entry(action="outra")) != h1  # sensível a alteração
    # o próprio entry_hash não entra no cálculo (evita auto-referência)
    assert helpers.audit_entry_hash(_entry(entry_hash="qualquer")) == h1


def test_verify_audit_entry_detects_tampering():
    import helpers

    doc = _entry()
    doc["entry_hash"] = helpers.audit_entry_hash(doc)
    assert helpers.verify_audit_entry(doc) is True
    # adulterar um campo sem refazer o HMAC (atacante sem SECRET_KEY) → deteta
    doc["details"] = {"k": "ADULTERADO"}
    assert helpers.verify_audit_entry(doc) is False


def test_verify_audit_entry_false_for_missing_hash():
    import helpers

    assert helpers.verify_audit_entry(_entry()) is False  # legada/sem hash


# ===================== create_audit_log encadeia o hash =================== #
@pytest.mark.asyncio
async def test_create_audit_log_stores_verifiable_hash(mock_db):
    import helpers

    mock_db.audit_logs = MagicMock()
    mock_db.audit_logs.insert_one = AsyncMock()

    await helpers.create_audit_log("u1", "test_action", "t1", details={"campo": "valor"})

    stored = mock_db.audit_logs.insert_one.call_args[0][0]
    assert stored["entry_hash"]
    assert helpers.verify_audit_entry(stored) is True
    # round-trip: re-verificar após uma "leitura" não muda nada
    stored["action"] = "alterado_a_posteriori"
    assert helpers.verify_audit_entry(stored) is False


# ===================== endpoint de verificação =========================== #
@pytest.mark.asyncio
async def test_verify_endpoint_flags_tampered_and_counts_legacy(mock_db, admin_user):
    import helpers
    import routes.notifications as notif

    good = _entry(id="a1")
    good["entry_hash"] = helpers.audit_entry_hash(good)
    tampered = _entry(id="a2")
    tampered["entry_hash"] = helpers.audit_entry_hash(tampered)
    tampered["action"] = "ADULTERADA"  # hash já não bate
    legacy = {"id": "a3", "user_id": "u", "action": "x", "created_at": "2026-01-03T00:00:00+00:00"}

    mock_db.audit_logs = MagicMock()
    mock_db.audit_logs.find = MagicMock(return_value=_cursor([good, tampered, legacy]))

    res = await notif.verify_audit_logs(current_user=admin_user)
    assert res["ok"] is False
    assert res["total"] == 3
    assert res["verified"] == 2
    assert res["legacy_unhashed"] == 1
    assert res["tampered_count"] == 1
    assert "a2" in res["tampered_ids"]
    assert "a1" not in res["tampered_ids"]


@pytest.mark.asyncio
async def test_verify_endpoint_ok_when_clean(mock_db, admin_user):
    import helpers
    import routes.notifications as notif

    e1 = _entry(id="a1")
    e1["entry_hash"] = helpers.audit_entry_hash(e1)
    e2 = _entry(id="a2", action="logout")
    e2["entry_hash"] = helpers.audit_entry_hash(e2)
    mock_db.audit_logs = MagicMock()
    mock_db.audit_logs.find = MagicMock(return_value=_cursor([e1, e2]))

    res = await notif.verify_audit_logs(current_user=admin_user)
    assert res["ok"] is True
    assert res["tampered_count"] == 0
    assert res["verified"] == 2


@pytest.mark.asyncio
async def test_verify_endpoint_forbidden_for_socio(mock_db, socio_user):
    import routes.notifications as notif

    with pytest.raises(HTTPException) as exc:
        await notif.verify_audit_logs(current_user=socio_user)
    assert exc.value.status_code == 403
