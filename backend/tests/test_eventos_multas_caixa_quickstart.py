"""Validação executável do quickstart (spec-eventos-multas-caixa) — Cenários 1–4.

Exercita as ROTAS reais ponta-a-ponta (despesa/receita de evento → caixa →
resultado/summary; gate Art. 54 + Ato propaga event_id + guarda de delete;
multa aplicada → receita idempotente; delete de evento bloqueado) sobre um
universo em memória **stateful** — a transação inserida num passo é mesmo
lida no agregado/summary do passo seguinte (ao contrário do unit test, que
isola cada rota com mocks por-teste).

Mapeia 1:1 para `specs/003-eventos-multas-caixa/quickstart.md`:
  - Cenário 1 (US1): resultado financeiro do evento
  - Cenário 2 (US3): gate Art. 54 + Ato↔evento + guarda de delete
  - Cenário 3 (US2): multa entra no caixa ao aplicar (exactly-once)
  - Cenário 4: eliminação de evento bloqueada (409)

Cenário 5 (UI) é validado no browser — ver `quickstart.md` §Cenário 5 e o
checklist em `specs/003-eventos-multas-caixa/T033-cenario5-browser.md`.

Sem servidor, sem DB, sem email/notificação real (audit/notify mockados).
"""

from __future__ import annotations

import copy
import re

import pytest
from fastapi import HTTPException

from routes import atos as atos_route
from routes import events as events_route
from routes import finances as finances_route
from routes import sancoes as sancoes_route

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
# $exists/$regex.
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

        async def _gen():
            for d in docs:
                yield copy.deepcopy(d)

        return _gen()


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def world(mock_db, monkeypatch):
    """Universo stateful partilhado por todos os cenários: instala FakeCollections
    em mock_db (já patchado em database/auth/helpers/routes.* pelo conftest) e
    silencia audit/notify."""
    mock_db.events = FakeCollection([{"id": "evt-1", "title": "Workshop CTA", "visibility": "publico"}])
    mock_db.transactions = FakeCollection()
    mock_db.sancoes = FakeCollection()
    mock_db.atos = FakeCollection()
    mock_db.users = FakeCollection([{"id": "u1", "name": "João Silva"}])
    # limiar 0 por defeito (gate desligado); o id tem de ser "finance_settings"
    # (coaprovacao_limiar lê {"id":"finance_settings"}).
    mock_db.finance_settings = FakeCollection([{"id": "finance_settings", "coaprovacao_limiar": 0}])

    for mod in (events_route, atos_route, sancoes_route):
        monkeypatch.setattr(mod, "create_audit_log", _noop, raising=False)
    for mod in (atos_route, sancoes_route):
        monkeypatch.setattr(mod, "notify_users", _noop, raising=False)
    return mock_db


async def _noop(*a, **k):
    return None


def _set_limiar(world, valor):
    world.finance_settings.docs[0]["coaprovacao_limiar"] = valor


# --------------------------------------------------------------------------- #
# Cenário 1 — Resultado financeiro do evento (US1)
# --------------------------------------------------------------------------- #
class TestCenario1Resultado:
    async def test_fluxo_completo(self, world, admin_user):
        from models import EventExpenseCreate, EventReceitaCreate

        # 2. despesa 8000 (categoria eventos); 3. receita 12000
        await events_route.add_event_expense(
            "evt-1", EventExpenseCreate(description="Sala", amount=8000, category="eventos"), _request(), admin_user
        )
        await events_route.add_event_receita(
            "evt-1", EventReceitaCreate(description="Inscricoes", amount=12000), _request(), admin_user
        )

        # 4a. GET /finances/transactions?event_id=evt-1 → 2 movimentos
        listed = await finances_route.list_transactions(event_id="evt-1", current_user=admin_user)
        assert listed["total"] == 2
        tipos = {t["type"]: t["amount"] for t in listed["items"]}
        assert tipos == {"despesa": 8000, "receita": 12000}

        # 4b. GET /events/{id} → resultado_financeiro derivado
        event = await events_route.get_event("evt-1", admin_user)
        assert event["resultado_financeiro"] == {"receitas": 12000, "despesas": 8000, "resultado": 4000}

        # 4c. /finances/summary reflete os movimentos do evento
        summary = await finances_route.compute_financial_summary()
        assert summary["total_despesas"] == 8000
        assert summary["total_receitas"] == 12000


# --------------------------------------------------------------------------- #
# Cenário 2 — Gate Art. 54 + Ato↔evento + guarda de delete (US3)
# --------------------------------------------------------------------------- #
class TestCenario2GateArt54:
    async def test_gate_ato_e_guarda(self, world, admin_user):
        from models import AtoExecute, EventExpenseCreate

        # 1. limiar 50000; 2. despesa 70000 → 400 (pede Ato)
        _set_limiar(world, 50000)
        with pytest.raises(HTTPException) as exc:
            await events_route.add_event_expense(
                "evt-1", EventExpenseCreate(description="Catering", amount=70000), _request(), admin_user
            )
        assert exc.value.status_code == 400
        assert "Acto" in exc.value.detail or "limiar" in exc.value.detail.lower()

        # 3. Ato de pagamento aprovado com event_id. (A cadeia de assinaturas
        #    — 2 Direção + Presidente + Tesoureiro — é doutro domínio e tem
        #    testes próprios; aqui parte-se de um Ato já `aprovado` para validar
        #    a propagação do vínculo, que é o âmbito desta spec.)
        world.atos.docs.append(
            {
                "id": "ato-1", "tipo": "pagamento", "status": "aprovado", "valor": 70000,
                "descricao": "Catering do evento", "event_id": "evt-1", "created_by": "u9",
            }
        )

        # 4. executar → despesa com ato_id E event_id
        await atos_route.execute_ato("ato-1", AtoExecute(category="eventos"), _request(), admin_user)
        movs = await finances_route.list_transactions(event_id="evt-1", current_user=admin_user)
        despesa_ato = next(t for t in movs["items"] if t.get("ato_id"))
        assert despesa_ato["ato_id"] == "ato-1"
        assert despesa_ato["event_id"] == "evt-1"
        assert despesa_ato["amount"] == 70000

        # 5. DELETE dessa despesa → 400 (tem ato_id, compromisso formal)
        with pytest.raises(HTTPException) as exc2:
            await events_route.delete_event_expense("evt-1", despesa_ato["id"], _request(), admin_user)
        assert exc2.value.status_code == 400


# --------------------------------------------------------------------------- #
# Cenário 3 — Multa entra no caixa ao aplicar (US2)
# --------------------------------------------------------------------------- #
def _sancao(sid, tipo="multa", multa_valor=6000):
    return {
        "id": sid, "tipo": tipo, "status": "decidida", "user_id": "u1",
        "motivo": "Atraso reiterado", "multa_valor": multa_valor, "decisao": {"aprovado": True},
    }


class TestCenario3MultaNoCaixa:
    async def test_multa_exactly_once_e_advertencia_sem_movimento(self, world, admin_user):
        # 1–2. multa decidida/aprovada → aplicar
        world.sancoes.docs.append(_sancao("sac-1"))
        out = await sancoes_route.aplicar_sancao("sac-1", _request(), admin_user)
        assert out["status"] == "aplicada"

        # 3. receita 6000 (extraordinarias) com sancao_id; /summary +6000
        recs = await finances_route.list_transactions(sancao_id="sac-1", current_user=admin_user)
        assert recs["total"] == 1
        assert recs["items"][0]["type"] == "receita"
        assert recs["items"][0]["amount"] == 6000
        assert recs["items"][0]["category"] == "extraordinarias"
        assert (await finances_route.compute_financial_summary())["total_receitas"] == 6000

        # 4. re-aplicar → exactly-once (sequencial: 400 pela guarda de estado
        #    decidida→aplicada; o 409 é a janela concorrente do CAS, coberta no
        #    unit test test_cas_loser_compensates_receita). Sem 2.ª receita.
        with pytest.raises(HTTPException) as exc:
            await sancoes_route.aplicar_sancao("sac-1", _request(), admin_user)
        assert exc.value.status_code in (400, 409)
        again = await finances_route.list_transactions(sancao_id="sac-1", current_user=admin_user)
        assert again["total"] == 1  # continua só 1 receita

        # 5. advertência aplicada → nenhum movimento
        world.sancoes.docs.append(_sancao("sac-2", tipo="advertencia", multa_valor=None))
        await sancoes_route.aplicar_sancao("sac-2", _request(), admin_user)
        assert (await finances_route.list_transactions(sancao_id="sac-2", current_user=admin_user))["total"] == 0


# --------------------------------------------------------------------------- #
# Cenário 4 — Eliminação de evento bloqueada
# --------------------------------------------------------------------------- #
class TestCenario4DeleteBloqueado:
    async def test_delete_evento_com_movimentos_409(self, world, admin_user):
        from models import EventReceitaCreate

        await events_route.add_event_receita(
            "evt-1", EventReceitaCreate(description="Inscricoes", amount=5000), _request(), admin_user
        )
        with pytest.raises(HTTPException) as exc:
            await events_route.delete_event("evt-1", admin_user)
        assert exc.value.status_code == 409
