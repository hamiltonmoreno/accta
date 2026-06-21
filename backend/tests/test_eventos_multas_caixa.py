"""Testes — spec-eventos-multas-caixa (ronda 2 do fluxo financeiro unificado).

US1: despesa/receita de evento = transação no caixa (event_id); resultado derivado; filtro.
US2: multa aplicada → receita no caixa (sancao_id), idempotente.
US3: gate Art. 54 nas despesas de evento; Ato propaga event_id; guardas de delete.

Unit/in-process com mock_db. Padrões herdados de test_fluxo_financeiro_unificado.py.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import atos as atos_route
from routes import events as events_route
from routes import finances as finances_route
from routes import sancoes as sancoes_route

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _request():
    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test", "origin": "https://accta.cv"}

    return _R()


def _cursor(items):
    cur = MagicMock()
    cur.sort = MagicMock(return_value=cur)
    cur.skip = MagicMock(return_value=cur)
    cur.limit = MagicMock(return_value=cur)
    cur.to_list = AsyncMock(return_value=items)
    return cur


def _agg(items):
    cur = MagicMock()
    cur.to_list = AsyncMock(return_value=items)
    return cur


def _async_rows(items):
    async def rows():
        for it in items:
            yield it

    return rows()


def _wire(mock_db, name, *, find_one=None):
    coll = MagicMock(name=name)
    coll.find_one = AsyncMock(return_value=find_one)
    coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
    coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    coll.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    coll.count_documents = AsyncMock(return_value=0)
    coll.aggregate = MagicMock(return_value=_agg([]))
    setattr(mock_db, name, coll)
    return coll


def _event():
    return {"id": "evt-1", "title": "Workshop CTA", "visibility": "publico"}


@pytest.fixture
def quiet(monkeypatch):
    monkeypatch.setattr(events_route, "create_audit_log", AsyncMock())
    monkeypatch.setattr(atos_route, "create_audit_log", AsyncMock())
    monkeypatch.setattr(atos_route, "notify_users", AsyncMock())
    monkeypatch.setattr(sancoes_route, "create_audit_log", AsyncMock())
    monkeypatch.setattr(sancoes_route, "notify_users", AsyncMock())


# --------------------------------------------------------------------------- #
# US1 — finanças de evento
# --------------------------------------------------------------------------- #


class TestEventExpenseReceita:
    async def test_add_expense_creates_transaction(self, mock_db, admin_user, quiet):
        from models import EventExpenseCreate

        mock_db.events.find_one = AsyncMock(return_value=_event())
        captured = {}

        async def cap(doc):
            captured.update(doc)
            return MagicMock()

        mock_db.transactions.insert_one = cap
        data = EventExpenseCreate(description="Sala", amount=8000, category="eventos")
        result = await events_route.add_event_expense("evt-1", data, _request(), admin_user)
        assert result["type"] == "despesa"
        assert result["event_id"] == "evt-1"
        assert result["category"] == "eventos"
        assert captured["event_id"] == "evt-1"

    async def test_add_expense_default_category(self, mock_db, admin_user, quiet):
        from models import EventExpenseCreate

        mock_db.events.find_one = AsyncMock(return_value=_event())
        data = EventExpenseCreate(description="X", amount=100)
        result = await events_route.add_event_expense("evt-1", data, _request(), admin_user)
        assert result["category"] == "eventos"

    async def test_add_receita_extraordinarias(self, mock_db, admin_user, quiet):
        from models import EventReceitaCreate

        mock_db.events.find_one = AsyncMock(return_value=_event())
        data = EventReceitaCreate(description="Inscricoes", amount=12000)
        result = await events_route.add_event_receita("evt-1", data, _request(), admin_user)
        assert result["type"] == "receita"
        assert result["category"] == "extraordinarias"
        assert result["event_id"] == "evt-1"

    async def test_socio_403(self, mock_db, socio_user, quiet):
        from models import EventReceitaCreate

        with pytest.raises(HTTPException) as exc:
            await events_route.add_event_receita("evt-1", EventReceitaCreate(description="x", amount=1), _request(), socio_user)
        assert exc.value.status_code == 403

    async def test_financeiro_403(self, mock_db, financeiro_user, quiet):
        # RBAC é manage_events (não manage_finances): financeiro NÃO gere eventos.
        from models import EventExpenseCreate

        mock_db.events.find_one = AsyncMock(return_value=_event())
        with pytest.raises(HTTPException) as exc:
            await events_route.add_event_expense("evt-1", EventExpenseCreate(description="x", amount=1), _request(), financeiro_user)
        assert exc.value.status_code == 403

    async def test_privilege_manage_events_ok(self, mock_db, quiet):
        # Caminho de privilégio: socio com manage_events PASSA (não só por role).
        from conftest import _make_user_dict
        from models import EventExpenseCreate, User

        gestor = User(**_make_user_dict("socio", privileges=["manage_events"]))
        mock_db.events.find_one = AsyncMock(return_value=_event())
        result = await events_route.add_event_expense("evt-1", EventExpenseCreate(description="Sala", amount=100), _request(), gestor)
        assert result["type"] == "despesa"


class TestEventListDeleteResult:
    async def test_list_expenses_filters(self, mock_db, admin_user):
        mock_db.events.find_one = AsyncMock(return_value=_event())
        captured = {}

        def find(q, _proj):
            captured.update(q)
            return _cursor([{"id": "t1", "type": "despesa", "event_id": "evt-1"}])

        mock_db.transactions.find = find
        result = await events_route.list_event_expenses("evt-1", admin_user)
        assert captured == {"event_id": "evt-1", "type": "despesa"}
        assert result["items"][0]["id"] == "t1"

    async def test_delete_expense(self, mock_db, admin_user, quiet):
        mock_db.events.find_one = AsyncMock(return_value=_event())
        mock_db.transactions.find_one = AsyncMock(return_value={"id": "t1", "event_id": "evt-1", "type": "despesa"})
        result = await events_route.delete_event_expense("evt-1", "t1", _request(), admin_user)
        assert result["message"]

    async def test_event_result_aggregation(self, mock_db):
        mock_db.transactions.aggregate = MagicMock(
            return_value=_async_rows([{"_id": "receita", "total": 12000}, {"_id": "despesa", "total": 8000}])
        )
        r = await events_route._event_result("evt-1")
        assert r == {"receitas": 12000, "despesas": 8000, "resultado": 4000}

    async def test_get_event_attaches_result(self, mock_db, admin_user):
        mock_db.events.find_one = AsyncMock(return_value=_event())
        mock_db.transactions.aggregate = MagicMock(return_value=_async_rows([]))
        result = await events_route.get_event("evt-1", admin_user)
        assert result["resultado_financeiro"] == {"receitas": 0.0, "despesas": 0.0, "resultado": 0.0}


class TestFinancesFilters:
    async def test_event_filter_and_summary(self, mock_db, admin_user):
        # filtro event_id na listagem
        captured = {}

        def find(q, _proj):
            captured.update(q)
            return _cursor([])

        mock_db.transactions.find = find
        mock_db.transactions.count_documents = AsyncMock(return_value=0)
        await finances_route.list_transactions(event_id="evt-1", current_user=admin_user)
        assert captured.get("event_id") == "evt-1"

        # FR-003/SC-003: o resumo do período reflete as transações de evento
        mock_db.transactions.find = MagicMock(
            return_value=_cursor(
                [
                    {"type": "receita", "amount": 12000, "category": "extraordinarias", "event_id": "evt-1"},
                    {"type": "despesa", "amount": 8000, "category": "eventos", "event_id": "evt-1"},
                ]
            )
        )
        summary = await finances_route.compute_financial_summary()
        assert summary["total_receitas"] == 12000
        assert summary["total_despesas"] == 8000


# --------------------------------------------------------------------------- #
# US3 — gate Art. 54 + Ato↔evento + guardas
# --------------------------------------------------------------------------- #


class TestEventGateAndGuards:
    async def test_expense_above_limiar_requires_ato(self, mock_db, admin_user, quiet):
        from models import EventExpenseCreate

        mock_db.events.find_one = AsyncMock(return_value=_event())
        mock_db.finance_settings.find_one = AsyncMock(return_value={"coaprovacao_limiar": 50000})
        with pytest.raises(HTTPException) as exc:
            await events_route.add_event_expense(
                "evt-1", EventExpenseCreate(description="Grande", amount=70000), _request(), admin_user
            )
        assert exc.value.status_code == 400

    async def test_delete_expense_with_ato_id_400(self, mock_db, admin_user, quiet):
        mock_db.events.find_one = AsyncMock(return_value=_event())
        mock_db.transactions.find_one = AsyncMock(
            return_value={"id": "t1", "event_id": "evt-1", "type": "despesa", "ato_id": "a1"}
        )
        with pytest.raises(HTTPException) as exc:
            await events_route.delete_event_expense("evt-1", "t1", _request(), admin_user)
        assert exc.value.status_code == 400

    async def test_delete_event_blocked_with_movements(self, mock_db, admin_user, quiet):
        mock_db.transactions.count_documents = AsyncMock(return_value=3)
        with pytest.raises(HTTPException) as exc:
            await events_route.delete_event("evt-1", admin_user)
        assert exc.value.status_code == 409

    async def test_execute_ato_propagates_event_id(self, mock_db, admin_user, quiet):
        from models import AtoExecute

        _wire(
            mock_db,
            "atos",
            find_one={
                "id": "a1", "tipo": "pagamento", "status": "aprovado", "valor": 70000,
                "descricao": "Catering", "event_id": "evt-1", "created_by": "u9",
            },
        )
        captured = {}

        async def cap(doc):
            captured.update(doc)
            return MagicMock()

        mock_db.transactions.insert_one = cap
        await atos_route.execute_ato("a1", AtoExecute(category="eventos"), _request(), admin_user)
        assert captured["event_id"] == "evt-1"
        assert captured["ato_id"] == "a1"


# --------------------------------------------------------------------------- #
# US2 — multa aplicada → caixa
# --------------------------------------------------------------------------- #


def _sancao(tipo="multa", multa_valor=6000):
    return {
        "id": "sac-1", "tipo": tipo, "status": "decidida", "user_id": "u1",
        "motivo": "Atraso", "multa_valor": multa_valor, "decisao": {"aprovado": True},
    }


class TestMultaAoAplicar:
    async def test_multa_creates_receita(self, mock_db, admin_user, quiet):
        _wire(mock_db, "sancoes", find_one=_sancao())
        mock_db.users.find_one = AsyncMock(return_value={"name": "João Silva"})
        mock_db.transactions.find_one = AsyncMock(return_value=None)  # sem receita ainda
        captured = {}

        async def cap(doc):
            captured.update(doc)
            return MagicMock()

        mock_db.transactions.insert_one = cap
        result = await sancoes_route.aplicar_sancao("sac-1", _request(), admin_user)
        assert result["status"] == "aplicada"
        assert captured["type"] == "receita"
        assert captured["category"] == "extraordinarias"
        assert captured["sancao_id"] == "sac-1"
        assert captured["amount"] == 6000

    async def test_multa_idempotent(self, mock_db, admin_user, quiet):
        _wire(mock_db, "sancoes", find_one=_sancao())
        mock_db.transactions.find_one = AsyncMock(return_value={"id": "tx-existing"})  # já existe
        insert = AsyncMock()
        mock_db.transactions.insert_one = insert
        await sancoes_route.aplicar_sancao("sac-1", _request(), admin_user)
        insert.assert_not_called()

    async def test_cas_loser_compensates_receita(self, mock_db, admin_user, quiet):
        # W1: perdedor da corrida do CAS apaga a receita que criou (sem duplicado).
        sanc = _wire(mock_db, "sancoes", find_one=_sancao())
        sanc.update_one = AsyncMock(return_value=MagicMock(modified_count=0))  # CAS perdido
        mock_db.users.find_one = AsyncMock(return_value={"name": "X"})
        mock_db.transactions.find_one = AsyncMock(return_value=None)
        inserted = {}

        async def cap_ins(doc):
            inserted.update(doc)
            return MagicMock()

        deleted = {}

        async def cap_del(q):
            deleted.update(q)
            return MagicMock(deleted_count=1)

        mock_db.transactions.insert_one = cap_ins
        mock_db.transactions.delete_one = cap_del
        with pytest.raises(HTTPException) as exc:
            await sancoes_route.aplicar_sancao("sac-1", _request(), admin_user)
        assert exc.value.status_code == 409
        assert deleted.get("id") == inserted.get("id")  # apagou exatamente a receita que criou

    async def test_non_multa_no_movement(self, mock_db, admin_user, quiet):
        _wire(mock_db, "sancoes", find_one=_sancao(tipo="advertencia", multa_valor=None))
        insert = AsyncMock()
        mock_db.transactions.insert_one = insert
        await sancoes_route.aplicar_sancao("sac-1", _request(), admin_user)
        insert.assert_not_called()

    async def test_sancao_filter(self, mock_db, admin_user):
        captured = {}

        def find(q, _proj):
            captured.update(q)
            return _cursor([])

        mock_db.transactions.find = find
        mock_db.transactions.count_documents = AsyncMock(return_value=0)
        await finances_route.list_transactions(sancao_id="sac-1", current_user=admin_user)
        assert captured.get("sancao_id") == "sac-1"
