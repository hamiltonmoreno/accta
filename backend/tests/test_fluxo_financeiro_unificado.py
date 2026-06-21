"""Testes — spec-fluxo-financeiro-unificado.

US1: despesa de projeto = transação no caixa (project_id); spent derivado; filtro.
US2: gate de co-aprovação (Art. 54) nas despesas de projeto; Ato propaga project_id.
US3: relatório anual gerado; submissão sem upload obrigatório.

Unit/in-process com mock_db (sem servidor/DB). Padrões herdados de
test_projects_routes.py / test_finances_routes.py.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import atos as atos_route
from routes import finances as finances_route
from routes import prestacao_contas as pc_route
from routes import projects as projects_route

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


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
    coll.aggregate = MagicMock(return_value=_agg([]))
    setattr(mock_db, name, coll)
    return coll


@pytest.fixture
def quiet(monkeypatch):
    """Silencia notificações/auditoria (testadas noutro lado)."""
    for fn in ("notify_users", "notify_admins", "create_notification", "create_audit_log"):
        monkeypatch.setattr(projects_route, fn, AsyncMock())
    for fn in ("notify_users", "create_audit_log"):
        monkeypatch.setattr(atos_route, fn, AsyncMock())


def _project(**extra):
    base = {"id": "p1", "title": "Projeto X", "created_by": "owner", "responsible_id": "owner", "budget": 0}
    base.update(extra)
    return base


# --------------------------------------------------------------------------- #
# US1 — despesa de projeto vira transação no caixa
# --------------------------------------------------------------------------- #


class TestAddExpenseCreatesTransaction:
    async def test_creates_transaction_with_project_id(self, mock_db, admin_user, quiet):
        from models import ProjectExpenseCreate

        mock_db.projects.find_one = AsyncMock(return_value=_project())
        captured = {}

        async def cap_insert(doc):
            captured.update(doc)
            return MagicMock()

        mock_db.transactions.insert_one = cap_insert
        mock_db.transactions.aggregate = MagicMock(return_value=_agg([{"_id": None, "total": 5000}]))

        data = ProjectExpenseCreate(description="Sala", amount=5000, category="eventos")
        result = await projects_route.add_expense("p1", data, _request(), admin_user)

        assert result["type"] == "despesa"
        assert result["project_id"] == "p1"
        assert result["category"] == "eventos"
        assert result["amount"] == 5000
        assert captured["project_id"] == "p1"

    async def test_default_category_operacional(self, mock_db, admin_user, quiet):
        from models import ProjectExpenseCreate

        mock_db.projects.find_one = AsyncMock(return_value=_project())
        data = ProjectExpenseCreate(description="X", amount=100)  # sem category
        result = await projects_route.add_expense("p1", data, _request(), admin_user)
        assert result["category"] == "operacional"

    async def test_invalid_category_400(self, mock_db, admin_user, quiet):
        from models import ProjectExpenseCreate

        mock_db.projects.find_one = AsyncMock(return_value=_project())
        data = ProjectExpenseCreate(description="X", amount=100, category="inexistente")
        with pytest.raises(HTTPException) as exc:
            await projects_route.add_expense("p1", data, _request(), admin_user)
        assert exc.value.status_code == 400

    async def test_project_not_found_404(self, mock_db, admin_user, quiet):
        from models import ProjectExpenseCreate

        mock_db.projects.find_one = AsyncMock(return_value=None)
        data = ProjectExpenseCreate(description="X", amount=100)
        with pytest.raises(HTTPException) as exc:
            await projects_route.add_expense("p1", data, _request(), admin_user)
        assert exc.value.status_code == 404

    async def test_socio_nao_gestor_403(self, mock_db, socio_user, quiet):
        from models import ProjectExpenseCreate

        mock_db.projects.find_one = AsyncMock(return_value=_project())  # socio != owner
        data = ProjectExpenseCreate(description="X", amount=100)
        with pytest.raises(HTTPException) as exc:
            await projects_route.add_expense("p1", data, _request(), socio_user)
        assert exc.value.status_code == 403


class TestListAndDeleteExpense:
    async def test_list_expenses_filters_project(self, mock_db, admin_user):
        mock_db.projects.find_one = AsyncMock(return_value=_project())
        captured = {}

        def find(query, _proj):
            captured.update(query)
            return _cursor([{"id": "t1", "amount": 5000, "project_id": "p1", "type": "despesa"}])

        mock_db.transactions.find = find
        result = await projects_route.list_expenses("p1", admin_user)
        assert captured["project_id"] == "p1"
        assert captured["type"] == "despesa"
        assert result["items"][0]["id"] == "t1"

    async def test_delete_expense_removes_transaction(self, mock_db, admin_user, quiet):
        mock_db.projects.find_one = AsyncMock(return_value=_project())
        mock_db.transactions.find_one = AsyncMock(
            return_value={"id": "t1", "project_id": "p1", "type": "despesa"}
        )
        deleted = {}

        async def cap_delete(q):
            deleted.update(q)
            return MagicMock(deleted_count=1)

        mock_db.transactions.delete_one = cap_delete
        result = await projects_route.delete_expense("p1", "t1", _request(), admin_user)
        assert deleted["id"] == "t1"
        assert result["message"]

    async def test_delete_expense_not_found_404(self, mock_db, admin_user, quiet):
        mock_db.projects.find_one = AsyncMock(return_value=_project())
        mock_db.transactions.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await projects_route.delete_expense("p1", "t1", _request(), admin_user)
        assert exc.value.status_code == 404


class TestSpentDerived:
    async def test_project_spent_sums_transactions(self, mock_db):
        mock_db.transactions.aggregate = MagicMock(return_value=_agg([{"_id": None, "total": 7500}]))
        assert await projects_route._project_spent("p1") == 7500

    async def test_project_spent_zero_when_empty(self, mock_db):
        mock_db.transactions.aggregate = MagicMock(return_value=_agg([]))
        assert await projects_route._project_spent("p1") == 0.0

    async def test_spent_by_project_map(self, mock_db):
        mock_db.transactions.aggregate = MagicMock(
            return_value=_async_rows([{"_id": "p1", "total": 5000}, {"_id": "p2", "total": 300}])
        )
        result = await projects_route._spent_by_project(["p1", "p2"])
        assert result == {"p1": 5000, "p2": 300}

    def test_orcamento_execucao_desvio(self):
        assert projects_route._orcamento_execucao(50000, 5000) == {
            "budget": 50000,
            "realizado": 5000,
            "desvio": 45000,
        }


class TestFinancesProjectFilter:
    async def test_list_transactions_project_id(self, mock_db, admin_user):
        captured = {}

        def find(query, _proj):
            captured.update(query)
            return _cursor([])

        mock_db.transactions.find = find
        mock_db.transactions.count_documents = AsyncMock(return_value=0)
        await finances_route.list_transactions(project_id="p1", current_user=admin_user)
        assert captured.get("project_id") == "p1"


# --------------------------------------------------------------------------- #
# US2 — gate de co-aprovação (Art. 54) + Ato propaga project_id
# --------------------------------------------------------------------------- #


class TestCoaprovacaoGate:
    async def test_above_limiar_requires_ato(self, mock_db, admin_user, quiet):
        from models import ProjectExpenseCreate

        mock_db.projects.find_one = AsyncMock(return_value=_project())
        mock_db.finance_settings.find_one = AsyncMock(return_value={"coaprovacao_limiar": 50000})
        data = ProjectExpenseCreate(description="Grande", amount=80000, category="operacional")
        with pytest.raises(HTTPException) as exc:
            await projects_route.add_expense("p1", data, _request(), admin_user)
        assert exc.value.status_code == 400
        assert "co-aprovacao" in exc.value.detail.lower() or "acto" in exc.value.detail.lower()

    async def test_below_limiar_allowed(self, mock_db, admin_user, quiet):
        from models import ProjectExpenseCreate

        mock_db.projects.find_one = AsyncMock(return_value=_project())
        mock_db.finance_settings.find_one = AsyncMock(return_value={"coaprovacao_limiar": 50000})
        data = ProjectExpenseCreate(description="Pequena", amount=1000, category="operacional")
        result = await projects_route.add_expense("p1", data, _request(), admin_user)
        assert result["amount"] == 1000

    async def test_delete_expense_with_ato_id_400(self, mock_db, admin_user, quiet):
        mock_db.projects.find_one = AsyncMock(return_value=_project())
        mock_db.transactions.find_one = AsyncMock(
            return_value={"id": "t1", "project_id": "p1", "type": "despesa", "ato_id": "a1"}
        )
        with pytest.raises(HTTPException) as exc:
            await projects_route.delete_expense("p1", "t1", _request(), admin_user)
        assert exc.value.status_code == 400


class TestExecuteAtoProjectId:
    async def test_execute_propagates_project_id(self, mock_db, admin_user, quiet):
        from models import AtoExecute

        _wire(
            mock_db,
            "atos",
            find_one={
                "id": "a1",
                "tipo": "pagamento",
                "status": "aprovado",
                "valor": 80000,
                "descricao": "Pagamento sala",
                "project_id": "p1",
                "created_by": "u9",
            },
        )
        captured = {}

        async def cap_insert(doc):
            captured.update(doc)
            return MagicMock()

        mock_db.transactions.insert_one = cap_insert
        await atos_route.execute_ato("a1", AtoExecute(category="eventos"), _request(), admin_user)
        assert captured["project_id"] == "p1"
        assert captured["ato_id"] == "a1"
        assert captured["type"] == "despesa"


# --------------------------------------------------------------------------- #
# US3 — relatório anual gerado + submissão sem upload
# --------------------------------------------------------------------------- #


class TestRelatorioContasModel:
    def test_document_id_optional(self):
        from models import RelatorioContasSubmit

        assert RelatorioContasSubmit().document_id is None
        assert RelatorioContasSubmit(document_id="doc-1").document_id == "doc-1"


class TestSubmeterRelatorioSemUpload:
    async def test_no_document_skips_validate(self, mock_db, admin_user, monkeypatch):
        from models import RelatorioContasSubmit

        _wire(mock_db, "exercicios", find_one={"id": "e1", "ano": 2026, "status": "aberto"})
        validate = AsyncMock()
        monkeypatch.setattr(pc_route, "_validate_document", validate)
        monkeypatch.setattr(pc_route, "_publish_document", AsyncMock())
        monkeypatch.setattr(pc_route, "members_of_orgao", AsyncMock(return_value=[]))
        monkeypatch.setattr(pc_route, "notify_users", AsyncMock())
        monkeypatch.setattr(pc_route, "create_audit_log", AsyncMock())

        result = await pc_route.submeter_relatorio(2026, RelatorioContasSubmit(), admin_user)
        validate.assert_not_called()
        assert result["status"] == "relatorio_submetido"

    async def test_with_document_validates(self, mock_db, admin_user, monkeypatch):
        from models import RelatorioContasSubmit

        _wire(mock_db, "exercicios", find_one={"id": "e1", "ano": 2026, "status": "aberto"})
        validate = AsyncMock()
        monkeypatch.setattr(pc_route, "_validate_document", validate)
        monkeypatch.setattr(pc_route, "_publish_document", AsyncMock())
        monkeypatch.setattr(pc_route, "members_of_orgao", AsyncMock(return_value=[]))
        monkeypatch.setattr(pc_route, "notify_users", AsyncMock())
        monkeypatch.setattr(pc_route, "create_audit_log", AsyncMock())

        await pc_route.submeter_relatorio(2026, RelatorioContasSubmit(document_id="doc-1"), admin_user)
        validate.assert_called_once()


class TestRelatorioAnualPdf:
    async def test_build_returns_pdf(self, mock_db):
        # transactions.find vazio → DRE/summary a zeros; PDF gera na mesma.
        buf = await finances_route.build_relatorio_anual_pdf(2026)
        head = buf.read(5)
        assert head.startswith(b"%PDF")

    async def test_build_with_orcamento_exec(self, mock_db):
        orc = {
            "ano_orcamento": 2027,
            "linhas": [{"categoria": "operacional", "tipo": "despesa", "orcado": 1000, "realizado": 800, "desvio": -200}],
        }
        buf = await finances_route.build_relatorio_anual_pdf(2026, orcamento_exec=orc)
        assert buf.read(5).startswith(b"%PDF")
