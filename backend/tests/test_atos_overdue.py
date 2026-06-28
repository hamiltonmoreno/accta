"""Unit — aviso à Direção de Ato (Art. 54) pendente há mais de X dias (spec 010).

Conduz `notify_overdue_atos()` diretamente, com `members_of_orgao`/`notify_users`
monkeypatched no módulo da rota e uma coleção `atos` falsa que HONRA o filtro
(status + ausência de `overdue_notified_at`) — para testar fielmente a
idempotência. Cobre os 7 casos do quickstart (Cenário A).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

import routes.atos as atos_mod


def _iso_days_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()


def _ato(_id: str, *, status="pendente", created_at=None, **extra) -> dict:
    d = {
        "id": _id,
        "tipo": "pagamento",
        "descricao": "Pagamento X",
        "valor": 50000,
        "status": status,
        "created_at": created_at if created_at is not None else _iso_days_ago(10),
    }
    d.update(extra)
    return d


def _atos_coll(docs: list[dict]) -> MagicMock:
    """Coleção falsa que filtra por status + `$exists:false` e aplica update_one."""
    coll = MagicMock(name="atos")

    def _find(query=None, projection=None):
        q = query or {}
        res = []
        for d in docs:
            if q.get("status") and d.get("status") != q["status"]:
                continue
            ex = q.get("overdue_notified_at")
            if isinstance(ex, dict) and ex.get("$exists") is False:
                if d.get("overdue_notified_at"):
                    continue
            res.append(dict(d))
        cur = MagicMock()
        cur.to_list = AsyncMock(return_value=res)
        return cur

    async def _update_one(filt, update):
        for d in docs:
            if d.get("id") == filt.get("id"):
                d.update(update.get("$set", {}))
        return MagicMock(modified_count=1)

    coll.find = MagicMock(side_effect=_find)
    coll.update_one = AsyncMock(side_effect=_update_one)
    return coll


@pytest.fixture
def wired(mock_db, monkeypatch):
    """Liga os colaboradores: notify_users observável, Direção com 2 membros,
    limiar X=7 por omissão. Devolve (mock_db, notify_users_mock)."""
    notify = AsyncMock()
    monkeypatch.setattr(atos_mod, "notify_users", notify)
    monkeypatch.setattr(atos_mod, "members_of_orgao", AsyncMock(return_value=["d1", "d2"]))
    mock_db.finance_settings.find_one = AsyncMock(return_value={"ato_overdue_dias": 7})
    return mock_db, notify


async def test_pendente_atrasado_avisa_direcao_com_link(wired):
    db, notify = wired
    docs = [_ato("a1", created_at=_iso_days_ago(10))]
    db.atos = _atos_coll(docs)

    result = await atos_mod.notify_overdue_atos()

    assert result["overdue"] == 1 and result["notified_atos"] == 1 and result["recipients"] == 2
    assert notify.await_count == 1
    args = notify.await_args.args
    assert args[0] == ["d1", "d2"]  # destinatários = Direção
    assert args[4] == atos_mod._LINK  # link para agir
    assert docs[0]["overdue_notified_at"]  # marca gravada


async def test_dentro_do_limiar_nao_avisa(wired):
    db, notify = wired
    db.atos = _atos_coll([_ato("a1", created_at=_iso_days_ago(3))])  # < 7

    result = await atos_mod.notify_overdue_atos()

    assert result["overdue"] == 0 and result["notified_atos"] == 0
    notify.assert_not_awaited()


async def test_idempotente_uma_unica_vez(wired):
    db, notify = wired
    docs = [_ato("a1", created_at=_iso_days_ago(10))]
    db.atos = _atos_coll(docs)

    first = await atos_mod.notify_overdue_atos()
    second = await atos_mod.notify_overdue_atos()

    assert first["notified_atos"] == 1
    assert second["notified_atos"] == 0  # já marcado ⇒ excluído pelo filtro
    assert notify.await_count == 1


async def test_resolvido_nao_avisa(wired):
    db, notify = wired
    db.atos = _atos_coll([_ato("a1", status="aprovado", created_at=_iso_days_ago(30))])

    result = await atos_mod.notify_overdue_atos()

    assert result["evaluated"] == 0 and result["overdue"] == 0
    notify.assert_not_awaited()


async def test_sem_direcao_nao_erra_nem_marca(wired, monkeypatch):
    db, notify = wired
    monkeypatch.setattr(atos_mod, "members_of_orgao", AsyncMock(return_value=[]))
    docs = [_ato("a1", created_at=_iso_days_ago(10))]
    db.atos = _atos_coll(docs)

    result = await atos_mod.notify_overdue_atos()

    assert result["overdue"] == 1 and result["recipients"] == 0 and result["notified_atos"] == 0
    notify.assert_not_awaited()
    assert "overdue_notified_at" not in docs[0]  # não marca ⇒ volta a qualificar


async def test_limiar_menor_passa_a_qualificar(wired):
    db, notify = wired
    db.finance_settings.find_one = AsyncMock(return_value={"ato_overdue_dias": 2})
    db.atos = _atos_coll([_ato("a1", created_at=_iso_days_ago(3))])  # 3 > 2

    result = await atos_mod.notify_overdue_atos()

    assert result["overdue"] == 1 and result["notified_atos"] == 1


async def test_created_at_ausente_ou_invalido_e_ignorado(wired):
    db, notify = wired
    ausente = _ato("a1")
    ausente.pop("created_at")  # campo verdadeiramente ausente
    db.atos = _atos_coll(
        [
            ausente,
            _ato("a2", created_at="not-a-date"),  # inválido
        ]
    )

    result = await atos_mod.notify_overdue_atos()

    assert result["evaluated"] == 2 and result["overdue"] == 0
    notify.assert_not_awaited()


async def test_default_7_quando_settings_ausente(wired):
    db, notify = wired
    db.finance_settings.find_one = AsyncMock(return_value=None)  # nunca configurado
    db.atos = _atos_coll([_ato("a1", created_at=_iso_days_ago(10))])  # 10 > 7 default

    result = await atos_mod.notify_overdue_atos()

    assert result["notified_atos"] == 1
