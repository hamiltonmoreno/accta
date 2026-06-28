"""Unit tests — Lembrete informativo de quotas (spec-008-lembrete-quotas).

Cobre o gerador (`POST /finances/generate-quotas` → notify por sócio novo),
o opt-out dedicado (`quota_reminder_opt_out`) e a garantia de email-off (MVP).
Tom informativo (transparência) — SEM linguagem de dívida/atraso.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from routes import finances as finances_route
from routes import comunicados as comunicados_route


pytestmark = pytest.mark.unit


def _request():
    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test", "origin": "https://accta.cv"}

    return _R()


def _cursor(items):
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=items)
    return cursor


class _AsyncIter:
    """Emula `db.transactions.aggregate(...)` em `async for r in ...`."""

    def __init__(self, items):
        self._items = items

    async def __aiter__(self):
        for item in self._items:
            yield item


def _setup_generator(mock_db, monkeypatch, *, active_users, inserted_ids, totals):
    """Arma o mock do gerador. `active_users` = docs lidos por db.users.find;
    `inserted_ids` = o que insert_quotas_atomic devolve (sócios NOVOS);
    `totals` = linhas do aggregate de total acumulado."""
    mock_db.users.find = MagicMock(return_value=_cursor(active_users))
    mock_db.finance_settings.find_one = AsyncMock(return_value={"quota_amount": 2000.0})
    mock_db.transactions.aggregate = MagicMock(return_value=_AsyncIter(totals))
    monkeypatch.setattr(finances_route, "insert_quotas_atomic", AsyncMock(return_value=inserted_ids))
    monkeypatch.setattr(finances_route, "create_audit_log", AsyncMock())
    fake_notify = AsyncMock()
    monkeypatch.setattr(finances_route, "create_notification", fake_notify)
    return fake_notify


@pytest.mark.asyncio
class TestLembreteGeracao:
    async def test_notifica_um_por_socio_novo_com_valor_total_e_carteira(
        self, mock_db, admin_user, monkeypatch
    ):
        fake_notify = _setup_generator(
            mock_db,
            monkeypatch,
            active_users=[{"id": "m1", "name": "A"}, {"id": "m2", "name": "B"}],
            inserted_ids=["m1", "m2"],
            totals=[{"_id": "m1", "total": 6000.0}, {"_id": "m2", "total": 2000.0}],
        )

        await finances_route.generate_monthly_quotas(
            request=_request(), month=5, year=2026, current_user=admin_user
        )

        assert fake_notify.await_count == 2
        for call in fake_notify.await_args_list:
            uid, ntype, title, body, link = call.args
            assert ntype == "financeiro"
            assert link == "/carteira"
            assert "acumulado" in body.lower()  # valor + total
            # Tom informativo: proibida linguagem de dívida/atraso (FR-002).
            assert not any(t in (title + body).lower() for t in ("dívida", "divida", "atraso", "inadimpl", "em falta"))

    async def test_idempotente_sem_quota_nova_nao_notifica(self, mock_db, admin_user, monkeypatch):
        # 2.º run do mesmo mês: insert devolve [] → 0 lembretes.
        fake_notify = _setup_generator(
            mock_db, monkeypatch,
            active_users=[{"id": "m1", "name": "A"}],
            inserted_ids=[],
            totals=[],
        )

        await finances_route.generate_monthly_quotas(
            request=_request(), month=5, year=2026, current_user=admin_user
        )

        fake_notify.assert_not_awaited()

    async def test_opt_out_nao_recebe(self, mock_db, admin_user, monkeypatch):
        # m1 fez opt-out → não recebe; m2 recebe.
        fake_notify = _setup_generator(
            mock_db, monkeypatch,
            active_users=[
                {"id": "m1", "name": "A", "quota_reminder_opt_out": True},
                {"id": "m2", "name": "B"},
            ],
            inserted_ids=["m1", "m2"],
            totals=[{"_id": "m1", "total": 2000.0}, {"_id": "m2", "total": 2000.0}],
        )

        await finances_route.generate_monthly_quotas(
            request=_request(), month=5, year=2026, current_user=admin_user
        )

        assert fake_notify.await_count == 1
        assert fake_notify.await_args.args[0] == "m2"

    async def test_email_off_no_mvp(self, mock_db, admin_user, monkeypatch):
        # FR-007 / STOP #6: o gerador não envia email — só notificação in-app.
        # Guard estrutural: se alguém ligar email, importa email_service no módulo.
        assert not hasattr(finances_route, "email_service")
        fake_notify = _setup_generator(
            mock_db, monkeypatch,
            active_users=[{"id": "m1", "name": "A"}],
            inserted_ids=["m1"],
            totals=[{"_id": "m1", "total": 2000.0}],
        )
        await finances_route.generate_monthly_quotas(
            request=_request(), month=5, year=2026, current_user=admin_user
        )
        fake_notify.assert_awaited_once()


@pytest.mark.asyncio
class TestPreferenciaOptOut:
    async def test_grava_quota_reminder_opt_out_no_proprio(self, mock_db, socio_user, monkeypatch):
        from models import EmailPreferencesUpdate

        captured = {}

        async def fake_update(filt, update):
            captured["filt"] = filt
            captured["set"] = update["$set"]

        mock_db.users.update_one = AsyncMock(side_effect=fake_update)

        result = await comunicados_route.update_email_preferences(
            payload=EmailPreferencesUpdate(quota_reminder_opt_out=True),
            current_user=socio_user,
        )

        assert captured["filt"] == {"id": socio_user.id}
        assert captured["set"] == {"quota_reminder_opt_out": True}
        assert result == {"quota_reminder_opt_out": True}

    async def test_so_grava_campos_presentes(self, mock_db, socio_user, monkeypatch):
        from models import EmailPreferencesUpdate

        captured = {}
        mock_db.users.update_one = AsyncMock(
            side_effect=lambda f, u: captured.update(set=u["$set"])
        )

        # Só envia email_opt_out_informativos → quota_reminder_opt_out não é tocado.
        await comunicados_route.update_email_preferences(
            payload=EmailPreferencesUpdate(email_opt_out_informativos=True),
            current_user=socio_user,
        )
        assert captured["set"] == {"email_opt_out_informativos": True}
