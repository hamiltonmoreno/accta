"""Validação executável do quickstart (spec-fluxo-financeiro-unificado) — Cenários 1–3.

Exercita as ROTAS reais ponta-a-ponta (despesa de projeto → caixa → spent
derivado/orçamento-execução/summary; gate Art. 54 + Ato propaga project_id +
guarda de delete; Relatório e Contas gerado em PDF + submissão sem upload com
`dre_snapshot` congelado) sobre um universo em memória **stateful** — a
transação inserida num passo é mesmo lida no agregado/summary/PDF do passo
seguinte (ao contrário do unit test, que isola cada rota com mocks por-teste).

Mapeia 1:1 para `specs/002-fluxo-financeiro-unificado-concluido/quickstart.md`:
  - Cenário 1 (US1): despesa de projeto entra no caixa (spent + orçamento_execução)
  - Cenário 2 (US2): gate Art. 54 + Ato↔projeto + guarda de delete (ato_id)
  - Cenário 3 (US3): Relatório e Contas gerado (PDF) + submissão sem upload

Cenário 4 (UX prestação de contas) é validado no browser — ver `quickstart.md`
§Cenário 4 e o checklist em
`specs/002-fluxo-financeiro-unificado-concluido/T037-cenario4-browser.md`.

Sem servidor, sem DB, sem email/notificação real (audit/notify mockados).
"""

from __future__ import annotations

import copy
import re

import pytest
from fastapi import HTTPException

from routes import atos as atos_route
from routes import finances as finances_route
from routes import prestacao_contas as pc_route
from routes import projects as projects_route

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


# --------------------------------------------------------------------------- #
# Request mínimo (audit/notify mockados ⇒ só o IP é tocado)
# --------------------------------------------------------------------------- #
def _request():
    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test", "origin": "https://accta.cv"}

    return _R()


# --------------------------------------------------------------------------- #
# Coleção stateful em memória — subset Mongo que estas rotas usam:
# insert_one / find / find_one / count_documents / update_one / delete_one /
# aggregate ($match + $group/$sum). Filtros: igualdade + $gte/$lte/$lt/$gt/
# $exists/$regex. O cursor de aggregate suporta `async for` E `.to_list()`
# (o _project_spent agrega com .to_list(1); _spent_by_project itera com async for).
# --------------------------------------------------------------------------- #
def _match_field(val, cond):
    if isinstance(cond, dict) and cond and all(str(k).startswith("$") for k in cond):
        for op, operand in cond.items():
            if op == "$gte":
                if val is None or not (val >= operand):
                    return False
            elif op == "$lte":
                if val is None or not (val <= operand):
                    return False
            elif op == "$lt":
                if val is None or not (val < operand):
                    return False
            elif op == "$gt":
                if val is None or not (val > operand):
                    return False
            elif op == "$exists":
                if (val is not None) != bool(operand):
                    return False
            elif op == "$regex":
                if not (isinstance(val, str) and re.search(operand, val, re.IGNORECASE)):
                    return False
            else:  # operador não suportado pelo fake → falha explícita
                raise NotImplementedError(f"FakeCollection: operador {op} não suportado")
        return True
    return val == cond


def _match(doc, query):
    return all(_match_field(doc.get(k), cond) for k, cond in query.items())


class _Cursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def sort(self, field, direction=1):
        self._docs.sort(key=lambda d: (d.get(field) is None, d.get(field)), reverse=(direction == -1))
        return self

    def skip(self, n):
        self._docs = self._docs[n:]
        return self

    def limit(self, n):
        if n is not None:
            self._docs = self._docs[:n]
        return self

    async def to_list(self, n=None):
        return [copy.deepcopy(d) for d in (self._docs if n is None else self._docs[:n])]


class _AggCursor:
    """Resultado de aggregate: iterável com `async for` E com `.to_list()`."""

    def __init__(self, docs):
        self._docs = list(docs)

    def __aiter__(self):
        self._i = 0
        return self

    async def __anext__(self):
        if self._i >= len(self._docs):
            raise StopAsyncIteration
        d = self._docs[self._i]
        self._i += 1
        return copy.deepcopy(d)

    async def to_list(self, n=None):
        return [copy.deepcopy(d) for d in (self._docs if n is None else self._docs[:n])]


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = [copy.deepcopy(d) for d in (docs or [])]

    def _matches(self, query):
        return [d for d in self.docs if _match(d, query)]

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))
        return type("R", (), {"inserted_id": doc.get("id")})

    def find(self, query=None, projection=None):
        return _Cursor(self._matches(query or {}))

    async def find_one(self, query=None, projection=None):
        m = self._matches(query or {})
        return copy.deepcopy(m[0]) if m else None

    async def count_documents(self, query=None):
        return len(self._matches(query or {}))

    async def update_one(self, query, update):
        for d in self.docs:
            if _match(d, query):
                for k, v in (update.get("$set") or {}).items():
                    d[k] = v
                return type("R", (), {"modified_count": 1})
        return type("R", (), {"modified_count": 0})

    async def delete_one(self, query):
        for i, d in enumerate(self.docs):
            if _match(d, query):
                del self.docs[i]
                return type("R", (), {"deleted_count": 1})
        return type("R", (), {"deleted_count": 0})

    def aggregate(self, pipeline):
        docs = list(self.docs)
        for stage in pipeline:
            if "$match" in stage:
                docs = [d for d in docs if _match(d, stage["$match"])]
            elif "$group" in stage:
                g = stage["$group"]
                id_spec = g["_id"]
                key_field = id_spec[1:] if isinstance(id_spec, str) and id_spec.startswith("$") else None
                sum_out = sum_field = None
                for k, v in g.items():
                    if k == "_id":
                        continue
                    if isinstance(v, dict) and "$sum" in v:
                        sf = v["$sum"]
                        sum_field = sf[1:] if isinstance(sf, str) and sf.startswith("$") else None
                        sum_out = k
                acc = {}
                for d in docs:
                    key = d.get(key_field) if key_field else None
                    acc[key] = acc.get(key, 0) + ((d.get(sum_field) or 0) if sum_field else 1)
                docs = [{"_id": k, sum_out: v} for k, v in acc.items()]
            else:
                raise NotImplementedError(f"FakeCollection.aggregate: stage {stage} não suportado")
        return _AggCursor(docs)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
async def _noop(*a, **k):
    return None


@pytest.fixture
def world(mock_db, monkeypatch):
    """Universo stateful partilhado: instala FakeCollections em mock_db (já
    patchado em database/auth/helpers/routes.* pelo conftest) e silencia
    audit/notify/enriquecimento de fotos."""
    mock_db.projects = FakeCollection(
        [{"id": "p1", "title": "Projeto X", "created_by": "owner", "responsible_id": "owner", "budget": 50000}]
    )
    mock_db.transactions = FakeCollection()
    mock_db.atos = FakeCollection()
    mock_db.exercicios = FakeCollection([{"id": "ex-2026", "ano": 2026, "status": "aberto"}])
    mock_db.users = FakeCollection([{"id": "owner", "name": "Dona Owner"}])
    # get_project enriquece com estas coleções (find().sort().to_list()).
    for c in ("project_tasks", "project_comments", "project_milestones"):
        setattr(mock_db, c, FakeCollection())
    # limiar 0 por defeito (gate desligado); id tem de ser "finance_settings".
    mock_db.finance_settings = FakeCollection([{"id": "finance_settings", "coaprovacao_limiar": 0}])

    for mod in (projects_route, atos_route):
        monkeypatch.setattr(mod, "create_audit_log", _noop, raising=False)
        monkeypatch.setattr(mod, "notify_users", _noop, raising=False)
    monkeypatch.setattr(projects_route, "enrich_author_photos", _noop, raising=False)
    # submissão do relatório: silenciar efeitos colaterais (testados noutro lado).
    for fn in ("_publish_document", "notify_users", "create_audit_log"):
        monkeypatch.setattr(pc_route, fn, _noop, raising=False)
    monkeypatch.setattr(pc_route, "members_of_orgao", _noop, raising=False)
    return mock_db


def _set_limiar(world, valor):
    world.finance_settings.docs[0]["coaprovacao_limiar"] = valor


# --------------------------------------------------------------------------- #
# Cenário 1 — Despesa de projeto entra no caixa (US1)
# --------------------------------------------------------------------------- #
class TestCenario1DespesaNoCaixa:
    async def test_fluxo_completo(self, world, admin_user):
        from models import ProjectExpenseCreate

        # 3. POST despesa Sala 5000 (categoria eventos)
        await projects_route.add_expense(
            "p1", ProjectExpenseCreate(description="Sala", amount=5000, category="eventos"), _request(), admin_user
        )

        # 4a. GET /finances/transactions?project_id=p1 → a despesa no caixa
        listed = await finances_route.list_transactions(project_id="p1", current_user=admin_user)
        assert listed["total"] == 1
        assert listed["items"][0]["type"] == "despesa"
        assert listed["items"][0]["amount"] == 5000

        # 4b. GET /projects/p1 → spent=5000, orçamento_execução derivado
        project = await projects_route.get_project("p1", admin_user)
        assert project["spent"] == 5000
        assert project["orcamento_execucao"] == {"budget": 50000, "realizado": 5000, "desvio": 45000}

        # 4c. /finances/summary reflete a despesa
        summary = await finances_route.compute_financial_summary()
        assert summary["total_despesas"] == 5000


# --------------------------------------------------------------------------- #
# Cenário 2 — Gate Art. 54 + Ato↔projeto + guarda de delete (US2)
# --------------------------------------------------------------------------- #
class TestCenario2GateArt54:
    async def test_gate_ato_e_guarda(self, world, admin_user):
        from models import AtoExecute, ProjectExpenseCreate

        # 1. limiar 50000; 2. despesa 80000 → 400 (pede Ato)
        _set_limiar(world, 50000)
        with pytest.raises(HTTPException) as exc:
            await projects_route.add_expense(
                "p1", ProjectExpenseCreate(description="Obra", amount=80000, category="operacional"),
                _request(), admin_user,
            )
        assert exc.value.status_code == 400
        assert "co-aprovacao" in exc.value.detail.lower() or "acto" in exc.value.detail.lower()

        # 3. Ato de pagamento aprovado com project_id. (A cadeia de assinaturas
        #    — 2 Direção + Presidente + Tesoureiro — é doutro domínio com testes
        #    próprios; aqui parte-se de um Ato já `aprovado` para validar a
        #    propagação do vínculo, que é o âmbito desta spec.)
        world.atos.docs.append(
            {
                "id": "ato-1", "tipo": "pagamento", "status": "aprovado", "valor": 80000,
                "descricao": "Pagamento da obra", "project_id": "p1", "created_by": "u9",
            }
        )

        # 4. executar → despesa com ato_id E project_id
        await atos_route.execute_ato("ato-1", AtoExecute(category="operacional"), _request(), admin_user)
        movs = await finances_route.list_transactions(project_id="p1", current_user=admin_user)
        despesa_ato = next(t for t in movs["items"] if t.get("ato_id"))
        assert despesa_ato["ato_id"] == "ato-1"
        assert despesa_ato["project_id"] == "p1"
        assert despesa_ato["amount"] == 80000

        # 5. spent reflete a despesa via Ato
        project = await projects_route.get_project("p1", admin_user)
        assert project["spent"] == 80000

        # 6. DELETE dessa despesa → 400 (tem ato_id, compromisso formal)
        with pytest.raises(HTTPException) as exc2:
            await projects_route.delete_expense("p1", despesa_ato["id"], _request(), admin_user)
        assert exc2.value.status_code == 400


# --------------------------------------------------------------------------- #
# Cenário 3 — Relatório e Contas gerado + submissão sem upload (US3)
# --------------------------------------------------------------------------- #
class TestCenario3RelatorioContas:
    async def test_pdf_gerado_e_submissao(self, world, admin_user):
        from models import ProjectExpenseCreate, RelatorioContasSubmit

        # 1. Exercício 2026 com transações: 1 despesa (via rota) + 1 receita.
        await projects_route.add_expense(
            "p1",
            ProjectExpenseCreate(description="Material", amount=3000, category="operacional", date="2026-03-10"),
            _request(), admin_user,
        )
        await world.transactions.insert_one(
            {"id": "r1", "type": "receita", "category": "quotas", "amount": 10000, "date": "2026-02-01T00:00:00"}
        )

        # 2. GET /exercicios/2026/relatorio/pdf → PDF (gerador real sobre o caixa)
        buf = await finances_route.build_relatorio_anual_pdf(2026)
        assert buf.read(5).startswith(b"%PDF")

        # 3. Totais do PDF == /finances/summary?year=2026
        summary = await finances_route.compute_financial_summary(year=2026)
        assert summary["total_despesas"] == 3000
        assert summary["total_receitas"] == 10000

        # 4. POST /exercicios/2026/relatorio {} (sem document_id) → relatorio_submetido,
        #    dre_snapshot congelado com os números do exercício.
        out = await pc_route.submeter_relatorio(2026, RelatorioContasSubmit(), admin_user)
        assert out["status"] == "relatorio_submetido"

        exercicio = await world.exercicios.find_one({"ano": 2026})
        assert exercicio["status"] == "relatorio_submetido"
        snap = exercicio["relatorio_contas"]["dre_snapshot"]
        assert snap["total_despesas"] == 3000
        assert snap["total_receitas"] == 10000
        assert snap["resultado_liquido"] == 7000
