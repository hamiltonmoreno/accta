"""Unit tests for routes/finances.py — RBAC, transaction CRUD, summary calc."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import finances as finances_route


pytestmark = pytest.mark.unit


def _cursor(items, limit_supports=True):  # noqa: ARG001
    cursor = MagicMock()
    cursor.sort = MagicMock(return_value=cursor)
    cursor.skip = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=items)
    return cursor


class _AsyncIter:
    """Async-iterable que devolve `items` — emula `db.x.aggregate(...)` usado
    em `async for r in db.transactions.aggregate(...)` (gerador de quotas)."""

    def __init__(self, items):
        self._items = items

    async def __aiter__(self):
        for item in self._items:
            yield item


def _request():
    """Fake Request para satisfazer a assinatura dos endpoints de escrita.
    create_audit_log lê client.host + headers via extract_request_meta."""

    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test", "origin": "https://accta.cv"}

    return _R()


# --------------------------------------------------------------------------- #
# require_view_finances / require_manage_finances
# --------------------------------------------------------------------------- #


class TestFinanceGateways:
    def test_admin_passes(self, admin_user):
        finances_route.require_view_finances(admin_user)  # no raise
        finances_route.require_manage_finances(admin_user)

    def test_financeiro_passes(self, financeiro_user):
        finances_route.require_view_finances(financeiro_user)
        finances_route.require_manage_finances(financeiro_user)

    def test_socio_403(self, socio_user):
        for gate in (finances_route.require_view_finances, finances_route.require_manage_finances):
            with pytest.raises(HTTPException) as exc:
                gate(socio_user)
            assert exc.value.status_code == 403

    def test_moderador_403(self, moderador_user):
        for gate in (finances_route.require_view_finances, finances_route.require_manage_finances):
            with pytest.raises(HTTPException) as exc:
                gate(moderador_user)
            assert exc.value.status_code == 403


# --------------------------------------------------------------------------- #
# GET /transactions — list (admin/financeiro)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestListTransactions:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await finances_route.list_transactions(current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_admin_can_list(self, mock_db, admin_user):
        mock_db.transactions.find = MagicMock(return_value=_cursor([]))
        mock_db.transactions.count_documents = AsyncMock(return_value=0)
        result = await finances_route.list_transactions(current_user=admin_user)
        assert result == {"items": [], "total": 0, "skip": 0, "limit": 100}

    async def test_limit_capped_at_200(self, mock_db, admin_user):
        captured = {}

        def find(_q, _proj):
            cursor = MagicMock()
            cursor.sort = MagicMock(return_value=cursor)
            cursor.skip = MagicMock(return_value=cursor)

            def lim(n):
                captured["limit"] = n
                return cursor

            cursor.limit = lim
            cursor.to_list = AsyncMock(return_value=[])
            return cursor

        mock_db.transactions.find = find
        mock_db.transactions.count_documents = AsyncMock(return_value=0)
        await finances_route.list_transactions(limit=10000, current_user=admin_user)
        assert captured["limit"] == 200

    async def test_search_uses_safe_regex_escape(self, mock_db, admin_user):
        """Sprint 3 fix — search escapa regex metachars."""
        captured = {}

        def find(query, _proj):
            captured.update(query)
            return _cursor([])

        mock_db.transactions.find = find
        mock_db.transactions.count_documents = AsyncMock(return_value=0)
        await finances_route.list_transactions(search=".*", current_user=admin_user)
        # Expected: re.escape('.*') = '\\.\\*'
        assert captured["description"]["$regex"] == "\\.\\*"


# --------------------------------------------------------------------------- #
# POST /transactions — create
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestCreateTransaction:
    async def test_socio_403(self, mock_db, socio_user):
        from models import TransactionCreate

        data = TransactionCreate(
            type="receita",
            category="quotas",
            description="x",
            amount=100,
            date=datetime.now(timezone.utc),
        )
        with pytest.raises(HTTPException) as exc:
            await finances_route.create_transaction(data=data, request=_request(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_negative_amount_400(self, mock_db, admin_user):
        from models import TransactionCreate

        data = TransactionCreate(
            type="receita",
            category="quotas",
            description="x",
            amount=-50,
            date=datetime.now(timezone.utc),
        )
        with pytest.raises(HTTPException) as exc:
            await finances_route.create_transaction(data=data, request=_request(), current_user=admin_user)
        assert exc.value.status_code == 400

    async def test_zero_amount_400(self, mock_db, admin_user):
        from models import TransactionCreate

        data = TransactionCreate(
            type="receita",
            category="quotas",
            description="x",
            amount=0,
            date=datetime.now(timezone.utc),
        )
        with pytest.raises(HTTPException) as exc:
            await finances_route.create_transaction(data=data, request=_request(), current_user=admin_user)
        assert exc.value.status_code == 400

    async def test_invalid_category_for_type_400(self, mock_db, admin_user):
        """receita com categoria de despesa -> 400."""
        from models import TransactionCreate

        data = TransactionCreate(
            type="receita",
            category="operacional",  # operacional e categoria de despesa
            description="x",
            amount=100,
            date=datetime.now(timezone.utc),
        )
        with pytest.raises(HTTPException) as exc:
            await finances_route.create_transaction(data=data, request=_request(), current_user=admin_user)
        assert exc.value.status_code == 400

    async def test_admin_creates_valid_receita(self, mock_db, admin_user):
        from models import TransactionCreate

        # find users for notify_admins
        mock_db.users.find = MagicMock(return_value=_cursor([]))
        data = TransactionCreate(
            type="receita",
            category="quotas",
            description="quota mar/2026",
            amount=5000,
            date=datetime.now(timezone.utc),
        )
        result = await finances_route.create_transaction(data=data, request=_request(), current_user=admin_user)
        assert result.type == "receita"
        assert result.amount == 5000
        mock_db.transactions.insert_one.assert_awaited_once()

    async def test_audit_log_recebe_request(self, mock_db, admin_user, monkeypatch):
        """Regressão #280: o `request` é encaminhado ao audit log para que IP/UA
        fiquem registados na auditoria financeira (proveniência forense)."""
        from models import TransactionCreate

        mock_db.users.find = MagicMock(return_value=_cursor([]))
        captured = {}

        async def fake_audit(*args, **kwargs):
            captured.update(kwargs)

        monkeypatch.setattr(finances_route, "create_audit_log", fake_audit)
        monkeypatch.setattr(finances_route, "notify_admins", AsyncMock())
        req = _request()
        data = TransactionCreate(
            type="receita",
            category="quotas",
            description="quota",
            amount=5000,
            date=datetime.now(timezone.utc),
        )
        await finances_route.create_transaction(data=data, request=req, current_user=admin_user)
        assert captured.get("request") is req


# --------------------------------------------------------------------------- #
# PATCH /transactions/{id} — update + co-approval gate (Art. 54)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestUpdateTransaction:
    async def test_socio_403(self, mock_db, socio_user):
        from models import TransactionUpdate

        with pytest.raises(HTTPException) as exc:
            await finances_route.update_transaction(
                transaction_id="tx1", data=TransactionUpdate(description="x"), request=_request(), current_user=socio_user
            )
        assert exc.value.status_code == 403

    async def test_404_not_found(self, mock_db, admin_user):
        from models import TransactionUpdate

        mock_db.transactions.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await finances_route.update_transaction(
                transaction_id="missing", data=TransactionUpdate(description="x"), request=_request(), current_user=admin_user
            )
        assert exc.value.status_code == 404

    async def test_coaprovacao_gate_blocks_raising_despesa_above_limiar(self, mock_db, admin_user):
        """Regressão: criava-se uma despesa abaixo do limiar e inflava-se por PATCH,
        contornando a co-aprovação (Art. 54)."""
        from models import TransactionUpdate

        existing = {"id": "tx1", "type": "despesa", "amount": 100, "category": "operacional"}
        mock_db.transactions.find_one = AsyncMock(return_value=existing)
        mock_db.finance_settings.find_one = AsyncMock(return_value={"coaprovacao_limiar": 10000})
        with pytest.raises(HTTPException) as exc:
            await finances_route.update_transaction(
                transaction_id="tx1", data=TransactionUpdate(amount=500000), request=_request(), current_user=admin_user
            )
        assert exc.value.status_code == 400
        assert "limiar" in exc.value.detail.lower()
        mock_db.transactions.update_one.assert_not_awaited()

    async def test_metadata_edit_allowed_on_above_limiar_despesa(self, mock_db, admin_user):
        """Editar só metadados (sem mexer no valor/tipo) de uma despesa acima do
        limiar continua livre — o gate não dispara."""
        from models import TransactionUpdate

        existing = {"id": "tx1", "type": "despesa", "amount": 500000, "category": "operacional"}
        mock_db.transactions.find_one = AsyncMock(side_effect=[existing, {**existing, "description": "nova"}])
        mock_db.finance_settings.find_one = AsyncMock(return_value={"coaprovacao_limiar": 10000})
        result = await finances_route.update_transaction(
            transaction_id="tx1", data=TransactionUpdate(description="nova"), request=_request(), current_user=admin_user
        )
        assert result["description"] == "nova"
        mock_db.transactions.update_one.assert_awaited_once()

    async def test_ato_linked_despesa_exempt(self, mock_db, admin_user):
        """Despesa já co-aprovada por um Acto (ato_id) está isenta do gate."""
        from models import TransactionUpdate

        existing = {"id": "tx1", "type": "despesa", "amount": 100, "category": "operacional", "ato_id": "a1"}
        mock_db.transactions.find_one = AsyncMock(side_effect=[existing, {**existing, "amount": 500000}])
        mock_db.finance_settings.find_one = AsyncMock(return_value={"coaprovacao_limiar": 10000})
        result = await finances_route.update_transaction(
            transaction_id="tx1", data=TransactionUpdate(amount=500000), request=_request(), current_user=admin_user
        )
        assert result["amount"] == 500000
        mock_db.transactions.update_one.assert_awaited_once()

    async def test_below_limiar_update_passes(self, mock_db, admin_user):
        from models import TransactionUpdate

        existing = {"id": "tx1", "type": "despesa", "amount": 100, "category": "operacional"}
        mock_db.transactions.find_one = AsyncMock(side_effect=[existing, {**existing, "amount": 5000}])
        mock_db.finance_settings.find_one = AsyncMock(return_value={"coaprovacao_limiar": 10000})
        result = await finances_route.update_transaction(
            transaction_id="tx1", data=TransactionUpdate(amount=5000), request=_request(), current_user=admin_user
        )
        assert result["amount"] == 5000
        mock_db.transactions.update_one.assert_awaited_once()


# --------------------------------------------------------------------------- #
# DELETE /transactions/{id}
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestDeleteTransaction:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await finances_route.delete_transaction(transaction_id="any", request=_request(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_404_not_found(self, mock_db, admin_user):
        mock_db.transactions.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await finances_route.delete_transaction(transaction_id="missing", request=_request(), current_user=admin_user)
        assert exc.value.status_code == 404

    async def test_admin_deletes(self, mock_db, admin_user):
        mock_db.transactions.find_one = AsyncMock(return_value={"id": "tx1"})
        result = await finances_route.delete_transaction(transaction_id="tx1", request=_request(), current_user=admin_user)
        assert "removida" in result["message"].lower()
        mock_db.transactions.delete_one.assert_awaited_with({"id": "tx1"})


# --------------------------------------------------------------------------- #
# GET /summary — calculation correctness
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestSummary:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await finances_route.get_financial_summary(current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_calculates_totals_correctly(self, mock_db, admin_user):
        txs = [
            {"type": "receita", "amount": 1000, "category": "quotas", "date": "2026-01-15T00:00:00"},
            {"type": "receita", "amount": 500, "category": "donativos", "date": "2026-02-01T00:00:00"},
            {"type": "despesa", "amount": 300, "category": "operacional", "date": "2026-01-20T00:00:00"},
        ]
        mock_db.transactions.find = MagicMock(return_value=_cursor(txs))
        result = await finances_route.get_financial_summary(year=2026, current_user=admin_user)
        assert result["total_receitas"] == 1500
        assert result["total_despesas"] == 300
        assert result["resultado_liquido"] == 1200
        assert result["receitas_por_categoria"]["quotas"] == 1000
        assert result["receitas_por_categoria"]["donativos"] == 500
        assert result["despesas_por_categoria"]["operacional"] == 300
        assert result["total_transacoes"] == 3

    async def test_empty_returns_zeros(self, mock_db, admin_user):
        mock_db.transactions.find = MagicMock(return_value=_cursor([]))
        result = await finances_route.get_financial_summary(current_user=admin_user)
        assert result["total_receitas"] == 0
        assert result["total_despesas"] == 0
        assert result["resultado_liquido"] == 0


# --------------------------------------------------------------------------- #
# GET /dre — monthly breakdown
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestDRE:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await finances_route.get_dre_report(year=2026, current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_groups_by_month_correctly(self, mock_db, admin_user):
        txs = [
            {"type": "receita", "amount": 1000, "category": "quotas", "date": "2026-01-15T00:00:00"},
            {"type": "receita", "amount": 500, "category": "quotas", "date": "2026-01-30T00:00:00"},
            {"type": "despesa", "amount": 200, "category": "operacional", "date": "2026-03-10T00:00:00"},
        ]
        mock_db.transactions.find = MagicMock(return_value=_cursor(txs))
        result = await finances_route.get_dre_report(year=2026, current_user=admin_user)
        assert result["monthly"][1]["receitas"] == 1500
        assert result["monthly"][1]["despesas"] == 0
        assert result["monthly"][3]["despesas"] == 200
        assert result["monthly"][6]["receitas"] == 0  # mes sem transacoes
        assert result["total_receitas"] == 1500
        assert result["total_despesas"] == 200

    async def test_skips_invalid_dates_silently(self, mock_db, admin_user):
        txs = [
            {"type": "receita", "amount": 1000, "category": "quotas", "date": "invalid"},
            {"type": "receita", "amount": 500, "category": "quotas", "date": "2026-02-01T00:00:00"},
        ]
        mock_db.transactions.find = MagicMock(return_value=_cursor(txs))
        result = await finances_route.get_dre_report(year=2026, current_user=admin_user)
        # So a tx valida foi contabilizada.
        assert result["total_receitas"] == 500

    async def test_year_range_is_half_open(self, mock_db, admin_user):
        # O filtro tem de ser [ano-01-01, (ano+1)-01-01) com $lt — um $lte sobre
        # "{ano}-12-31T23:59:59" perderia timestamps com fracção de segundo.
        captured = {}

        def _find(query, *a, **k):
            captured["query"] = query
            return _cursor([])

        mock_db.transactions.find = MagicMock(side_effect=_find)
        await finances_route.get_dre_report(year=2026, current_user=admin_user)
        assert captured["query"]["date"] == {"$gte": "2026-01-01T00:00:00", "$lt": "2027-01-01T00:00:00"}

    async def test_le_todas_as_transacoes_sem_teto(self, mock_db, admin_user):
        # Regressão #277: o DRE truncava em 5000 e divergia do resumo (sem teto).
        # Não deve aplicar `.limit` e deve pedir todas via `to_list(None)`.
        cursor = _cursor([])
        mock_db.transactions.find = MagicMock(return_value=cursor)
        await finances_route.get_dre_report(year=2026, current_user=admin_user)
        cursor.limit.assert_not_called()
        cursor.to_list.assert_awaited_once_with(None)

    async def test_export_pdf_reuses_compute_dre(self, mock_db, admin_user, monkeypatch):
        # O export PDF deve reutilizar compute_dre_report (fonte única), não
        # recalcular — senão uma correcção num lado não chega ao outro.
        from fastapi.responses import StreamingResponse

        dre = {
            "year": 2026,
            "monthly": {m: {"receitas": 0, "despesas": 0} for m in range(1, 13)},
            "receitas_por_categoria": {"quotas": 1000},
            "despesas_por_categoria": {"operacional": 200},
            "total_receitas": 1000,
            "total_despesas": 200,
            "resultado_liquido": 800,
        }
        spy = AsyncMock(return_value=dre)
        monkeypatch.setattr(finances_route, "compute_dre_report", spy)
        result = await finances_route.export_dre_pdf(year=2026, current_user=admin_user)
        spy.assert_awaited_once_with(2026)
        assert isinstance(result, StreamingResponse)


# --------------------------------------------------------------------------- #
# Settings endpoints
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestFinanceSettings:
    async def test_get_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await finances_route.get_finance_settings(current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_update_socio_403(self, mock_db, socio_user):
        from models import FinanceSettingsUpdate

        with pytest.raises(HTTPException) as exc:
            await finances_route.update_finance_settings(
                data=FinanceSettingsUpdate(quota_amount=5000), request=_request(), current_user=socio_user
            )
        assert exc.value.status_code == 403


# --------------------------------------------------------------------------- #
# POST /generate-quotas
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestGenerateQuotas:
    async def test_only_active_member_accounts_receive_quotas(self, mock_db, admin_user, monkeypatch):
        captured = {}

        def find_users(query, projection):
            captured["query"] = query
            captured["projection"] = projection
            return _cursor([{"id": "member-1", "name": "Socio"}])

        mock_db.users.find = MagicMock(side_effect=find_users)
        mock_db.finance_settings.find_one = AsyncMock(return_value={"quota_amount": 2000.0})
        # A inserção passa pelo helper atómico (advisory lock) — mock no estilo das
        # restantes funções de lock do database.py (ex. register_presenca_locked).
        # Devolve a lista de user_id NOVOS (spec-008).
        fake_insert = AsyncMock(return_value=["member-1"])
        monkeypatch.setattr(finances_route, "insert_quotas_atomic", fake_insert)
        monkeypatch.setattr(finances_route, "create_audit_log", AsyncMock())
        fake_notify = AsyncMock()
        monkeypatch.setattr(finances_route, "create_notification", fake_notify)
        # Total acumulado por sócio (1 aggregate sobre transactions).
        mock_db.transactions.aggregate = MagicMock(return_value=_AsyncIter([{"_id": "member-1", "total": 6000.0}]))

        result = await finances_route.generate_monthly_quotas(
            request=_request(), month=5, year=2026, current_user=admin_user
        )

        assert captured["query"] == {
            "status": "ativo",
            "$or": [{"account_type": "member"}, {"account_type": {"$exists": False}}],
        }
        assert result["created"] == 1
        # 1 candidato (o único sócio activo), com (ano, mês) e categoria certos.
        fake_insert.assert_awaited_once()
        call_year, call_month, candidates = fake_insert.await_args.args
        assert (call_year, call_month) == (2026, 5)
        assert [c["user_id"] for c in candidates] == ["member-1"]
        assert candidates[0]["category"] == "quotas"
        # Lembrete informativo in-app por sócio novo, link /carteira (spec-008).
        fake_notify.assert_awaited_once()
        notify_args = fake_notify.await_args.args
        assert notify_args[0] == "member-1"
        assert notify_args[-1] == "/carteira"

    async def test_le_todos_os_socios_sem_teto(self, mock_db, admin_user, monkeypatch):
        # Regressão #278: o teto to_list(1000) deixava sócios excedentes sem quota
        # em silêncio. Deve ler todos via to_list(None).
        cursor = _cursor([])
        mock_db.users.find = MagicMock(return_value=cursor)
        mock_db.finance_settings.find_one = AsyncMock(return_value={"quota_amount": 2000.0})
        monkeypatch.setattr(finances_route, "insert_quotas_atomic", AsyncMock(return_value=[]))
        monkeypatch.setattr(finances_route, "create_audit_log", AsyncMock())
        monkeypatch.setattr(finances_route, "create_notification", AsyncMock())

        await finances_route.generate_monthly_quotas(
            request=_request(), month=5, year=2026, current_user=admin_user
        )
        cursor.to_list.assert_awaited_once_with(None)


class _ACtx:
    """Async context manager que entrega `value` no __aenter__."""

    def __init__(self, value):
        self._value = value

    async def __aenter__(self):
        return self._value

    async def __aexit__(self, *_):
        return False


@pytest.mark.asyncio
class TestInsertQuotasAtomic:
    async def test_dedup_under_lock(self, monkeypatch):
        """Sob o advisory lock, re-lê os existentes do mês e insere só os em
        falta — member-1 já tem quota, só member-2 é inserido."""
        import database

        executed: list = []
        inserted: list = []

        class FakeConn:
            async def execute(self, sql, *args):
                executed.append((sql, args))
                if sql.startswith("INSERT"):
                    inserted.append(args[0])

            async def fetch(self, sql, *args):
                return [{"uid": "member-1"}]  # member-1 já tem quota no mês

            def transaction(self):
                return _ACtx(None)

        class FakePool:
            def acquire(self):
                return _ACtx(FakeConn())

        monkeypatch.setattr(database, "get_pool", AsyncMock(return_value=FakePool()))

        candidates = [
            {"user_id": "member-1", "category": "quotas"},
            {"user_id": "member-2", "category": "quotas"},
        ]
        n = await database.insert_quotas_atomic(2026, 5, candidates)

        # Devolve a lista de user_id NOVOS (spec-008) — só member-2.
        assert n == ["member-2"]
        assert [d["user_id"] for d in inserted] == ["member-2"]
        # Advisory lock pedido com (namespace, ano*100+mês) ANTES de inserir.
        lock_args = next(args for sql, args in executed if "pg_advisory_xact_lock" in sql)
        assert lock_args == (database._QUOTA_LOCK_NS, 202605)

    async def test_empty_candidates_short_circuits(self, monkeypatch):
        import database

        # Se tocar no pool, falha — candidatos vazios devem sair sem ligar.
        monkeypatch.setattr(database, "get_pool", AsyncMock(side_effect=AssertionError("não devia ligar")))
        assert await database.insert_quotas_atomic(2026, 5, []) == []


# --------------------------------------------------------------------------- #
# GET /me/quotas — vista self-service do sócio (substitui invoices)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestMyQuotas:
    async def test_filters_by_own_user_id(self, mock_db, socio_user):
        captured = {}

        def find(query, _proj):
            captured["query"] = query
            return _cursor([])

        mock_db.transactions.find = MagicMock(side_effect=find)
        await finances_route.list_my_quotas(current_user=socio_user)
        # Filtro fixo pelo próprio user_id + quotas/jóias de receita.
        assert captured["query"]["user_id"] == socio_user.id
        assert captured["query"]["type"] == "receita"
        assert captured["query"]["category"] == {"$in": ["quotas", "joias"]}

    async def test_sums_total_pago(self, mock_db, socio_user):
        items = [
            {"id": "t1", "amount": 500.0, "category": "quotas"},
            {"id": "t2", "amount": 2000.0, "category": "joias"},
        ]
        mock_db.transactions.find = MagicMock(return_value=_cursor(items))
        result = await finances_route.list_my_quotas(current_user=socio_user)
        assert result["items"] == items
        assert result["total_pago"] == 2500.0

    async def test_socio_allowed_no_403(self, mock_db, socio_user):
        # Ao contrário de /transactions, o sócio PODE ver as suas quotas.
        mock_db.transactions.find = MagicMock(return_value=_cursor([]))
        result = await finances_route.list_my_quotas(current_user=socio_user)
        assert result == {"items": [], "total_pago": 0}

    async def test_bad_amount_is_tolerated(self, mock_db, socio_user):
        # amount mal-formado/ausente em doc legado não deve rebentar o endpoint.
        items = [
            {"id": "t1", "amount": 500.0},
            {"id": "t2", "amount": "abc"},
            {"id": "t3"},
            {"id": "t4", "amount": None},
        ]
        mock_db.transactions.find = MagicMock(return_value=_cursor(items))
        result = await finances_route.list_my_quotas(current_user=socio_user)
        assert result["total_pago"] == 500.0

    async def test_le_todas_as_quotas_sem_teto(self, mock_db, socio_user):
        # Coerência com o resto do módulo (#277/#278): a vista do sócio lê todas
        # as suas quotas sem teto. Trava uma regressão se alguém puser .limit(...).
        cursor = _cursor([])
        mock_db.transactions.find = MagicMock(return_value=cursor)
        await finances_route.list_my_quotas(current_user=socio_user)
        cursor.limit.assert_not_called()
        cursor.to_list.assert_awaited_once_with(None)
