"""Validação executável do quickstart (comunicados-segmentados v2) — DRY-RUN.

Exercita as ROTAS + SERVIÇO reais ponta-a-ponta (preview → criar rascunho →
enviar dry-run → snapshot → audit) sobre um universo representativo, sem servidor
nem DB (mock_db + coleções stateful em memória). Mapeia 1:1 para
`specs/001-comunicados-segmentados/quickstart.md` (US1–US4 + edge cases + SC-003/004).

Nenhum email/notificação real é disparado (asserções `assert_not_awaited`).
"""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from starlette.requests import Request
from fastapi import BackgroundTasks

import routes.comunicados as cmod
import comunicados_service as svc
from models import User, ComunicadoCreate, ComunicadoUpdate, AudiencePreviewRequest


# --------------------------------------------------------------------------- #
# Universo representativo (mirror do quickstart §Pré-requisitos)
# --------------------------------------------------------------------------- #

def _u(uid, mid, cargo, cat, status, adm, *, account_type="member"):
    return {
        "id": uid, "name": uid.upper(), "email": f"{uid}@x.cv", "role": "socio",
        "account_type": account_type, "member_category": cat, "cargo": cargo,
        "status": status, "member_id": mid, "admission_date": adm,
    }


UNIVERSE = [
    _u("d1", "ACCTA-0001", "dir_presidente", "ordinario", "ativo", "2022-05-01"),
    _u("d2", "ACCTA-0002", "dir_tesoureiro", "fundador", "ativo", "2024-03-10"),
    _u("c1", "ACCTA-0010", "cf_presidente", "ordinario", "ativo", "2021-01-01"),
    _u("c2", "ACCTA-0011", "cf_relator", "ordinario", "ativo", "2020-02-02"),
    _u("a1", "ACCTA-0020", "ag_presidente", "ordinario", "ativo", "2020-06-01"),
    _u("s1", "ACCTA-0030", "socio", "ordinario", "ativo", "2019-01-01"),
    _u("p1", "ACCTA-0041", "socio", "ordinario", "pendente_aprovacao", "2025-01-01"),
    _u("p2", "ACCTA-0042", "socio", "ordinario", "pendente_aprovacao", "2025-02-01"),
    _u("p3", "ACCTA-0043", "socio", "ordinario", "pendente_aprovacao", "2025-03-01"),
    _u("sys", "ACCTA-9000", "socio", "ordinario", "ativo", "2018-01-01", account_type="technical"),
]

ORGAO_MEMBERS = {
    "direcao": ["d1", "d2"],
    "conselho_fiscal": ["c1", "c2"],
    "mesa_ag": ["a1"],
}


# --------------------------------------------------------------------------- #
# Coleção stateful mínima (in-memory) para comunicados + audit_logs
# --------------------------------------------------------------------------- #

class FakeCollection:
    def __init__(self):
        self.docs = []

    @staticmethod
    def _match(doc, query):
        return all(doc.get(k) == v for k, v in query.items() if not isinstance(v, dict))

    async def insert_one(self, doc):
        self.docs.append(dict(doc))
        return SimpleNamespace(inserted_id=doc.get("id"))

    async def find_one(self, query, projection=None):
        for d in self.docs:
            if self._match(d, query):
                return dict(d)
        return None

    async def update_one(self, query, update):
        for d in self.docs:
            if self._match(d, query):
                if "$set" in update:
                    d.update(update["$set"])
                return SimpleNamespace(modified_count=1)
        return SimpleNamespace(modified_count=0)

    async def count_documents(self, query=None):
        return len(self.docs)


def _req():
    return Request({"type": "http", "headers": [], "method": "POST",
                    "path": "/api/comunicados", "query_string": b"", "client": ("test", 0)})


# --------------------------------------------------------------------------- #
# Ambiente: universo + coleções + monkeypatches (sem email/notify reais)
# --------------------------------------------------------------------------- #

@pytest.fixture
def env(mock_db, monkeypatch):
    mock_db.users.find.return_value.to_list = AsyncMock(return_value=list(UNIVERSE))
    mock_db.comunicados = FakeCollection()
    mock_db.audit_logs = FakeCollection()

    async def _members_of_orgao(o):
        return list(ORGAO_MEMBERS.get(o, []))

    monkeypatch.setattr(svc, "members_of_orgao", _members_of_orgao)
    monkeypatch.setattr(svc, "IS_PROD", False)
    monkeypatch.setattr(cmod, "IS_PROD", False)
    monkeypatch.setattr(cmod.limiter, "enabled", False)
    notify = AsyncMock()
    send = AsyncMock(return_value={"sent": 0, "failed": 0})
    monkeypatch.setattr(svc, "notify_users", notify)
    monkeypatch.setattr(svc, "send_comunicado_batch", send)
    return SimpleNamespace(comunicados=mock_db.comunicados, audit=mock_db.audit_logs,
                           notify=notify, send=send)


def _sender(uid, privileges):
    return User(id=uid, name=uid, email=f"{uid}@x.cv", role="socio", status="ativo",
                privileges=privileges)


ADMIN = User(id="admin", name="Admin", email="admin@x.cv", role="admin", status="ativo")


async def _create_and_send(env, sender, af, *, dry_run=True, channels=("in_app", "email")):
    """Cria rascunho v2 + envia (dry-run). Devolve (result, comunicado_id)."""
    payload = ComunicadoCreate(subject="Comunicado de teste", body="corpo suficientemente longo",
                               channels=list(channels), audience_filter=af, dry_run=dry_run)
    created = await cmod.create_comunicado(_req(), payload, BackgroundTasks(), current_user=sender)
    cid = created["id"]
    result = await cmod.enviar_comunicado(cid, _req(), current_user=sender)
    return result, cid


# --------------------------------------------------------------------------- #
# US1 — Direcção comunica internamente
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_US1_preview_orgao_direcao(env):
    prev = await svc.preview_audience({"orgaos": ["direcao"]}, tipo="oficial", channels=["in_app"])
    assert prev["recipients_count"] == 2                 # só a Direcção (d1, d2)
    assert set(prev["sample"]) <= {"D1", "D2"}
    assert prev["warnings"] == []


@pytest.mark.asyncio
async def test_US1_send_dry_run_snapshots_and_does_not_send(env):
    result, cid = await _create_and_send(env, ADMIN, {"orgaos": ["direcao"]}, dry_run=True)
    assert result["status"] == "enviado" and result["dry_run"] is True
    # snapshot com os member_id da Direcção; NADA enviado
    doc = await env.comunicados.find_one({"id": cid})
    assert sorted(doc["audience_resolved"]) == ["ACCTA-0001", "ACCTA-0002"]
    assert doc["dry_run"] is True
    env.notify.assert_not_awaited()
    env.send.assert_not_awaited()
    # audit comunicado_enviado com dry_run=true (SC-003)
    audit = [d for d in env.audit.docs if d.get("action") == "comunicado_enviado"]
    assert audit and audit[-1]["details"]["dry_run"] is True


@pytest.mark.asyncio
async def test_US1_rbac_socio_forbidden(env):
    payload = AudiencePreviewRequest(channels=["in_app"], audience_filter={"orgaos": ["direcao"]})
    with pytest.raises(Exception) as ei:
        await cmod.preview_audience(payload, current_user=_sender("x", []))
    assert getattr(ei.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_US1_draft_edit_and_cancel(env):
    payload = ComunicadoCreate(subject="Rascunho", body="corpo suficientemente longo",
                               channels=["in_app"], audience_filter={"orgaos": ["direcao"]})
    created = await cmod.create_comunicado(_req(), payload, BackgroundTasks(), current_user=ADMIN)
    cid = created["id"]
    assert created["status"] == "rascunho"
    await cmod.update_comunicado(cid, ComunicadoUpdate(subject="Rascunho editado"), _req(), current_user=ADMIN)
    assert (await env.comunicados.find_one({"id": cid}))["subject"] == "Rascunho editado"
    res = await cmod.cancelar_comunicado(cid, _req(), current_user=ADMIN)
    assert res["status"] == "cancelado"


# --------------------------------------------------------------------------- #
# US2 — Convocatória para subconjunto (composição AND)
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_US2_composite_and_with_per_type(env):
    prev = await svc.preview_audience(
        {"categorias": ["ordinario"], "statuses": ["ativo"], "joined_before": "2024-01-01"},
        tipo="oficial", channels=["in_app"])
    # ordinario ∩ ativo ∩ admitidos<2024 = d1,c1,c2,a1,s1 (d2 é fundador/2024)
    assert prev["recipients_count"] == 5
    assert prev["intersected_count"] == 5
    assert {"categorias", "statuses", "periodo"} <= set(prev["per_type_counts"])


@pytest.mark.asyncio
async def test_US2_zero_recipients_blocks_send_422(env):
    payload = ComunicadoCreate(subject="Vazio", body="corpo suficientemente longo", channels=["in_app"],
                               audience_filter={"categorias": ["fundador"], "statuses": ["pendente_aprovacao"]})
    created = await cmod.create_comunicado(_req(), payload, BackgroundTasks(), current_user=ADMIN)
    with pytest.raises(Exception) as ei:
        await cmod.enviar_comunicado(created["id"], _req(), current_user=ADMIN)
    assert getattr(ei.value, "status_code", None) == 422


@pytest.mark.asyncio
async def test_US2_history_shows_filter_and_resolved(env):
    _, cid = await _create_and_send(env, ADMIN, {"categorias": ["ordinario"], "statuses": ["ativo"]},
                                    dry_run=True, channels=["in_app"])
    doc = await cmod.get_comunicado(cid, current_user=ADMIN)
    assert doc["audience_filter"] == {"cargos": [], "orgaos": [], "categorias": ["ordinario"],
                                      "statuses": ["ativo"], "joined_after": None, "joined_before": None,
                                      "nominal_member_ids": [], "nominal_emails": []}
    assert "ACCTA-9000" not in doc["audience_resolved"]   # SC-004: technical fora


# --------------------------------------------------------------------------- #
# US3 — Onboarding (status pendente_aprovacao)
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_US3_pendente_aprovacao_warns_and_excludes_ativos(env):
    prev = await svc.preview_audience({"statuses": ["pendente_aprovacao"]}, tipo="oficial", channels=["in_app"])
    assert prev["recipients_count"] == 3                  # p1, p2, p3
    assert any(w["code"] == "includes_unapproved" for w in prev["warnings"])
    # nenhum ativo contado
    res = await svc.resolve_audience({"statuses": ["pendente_aprovacao"]}, channel="in_app", tipo="oficial")
    assert {u["id"] for u in res} == {"p1", "p2", "p3"}


# --------------------------------------------------------------------------- #
# US4 — Conselho Fiscal → Direcção (privilege comunicar_intra_orgao)
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_US4_cf_sends_to_direcao_audit_identifies_author(env):
    cf = _sender("c1", ["comunicar_intra_orgao"])
    result, cid = await _create_and_send(env, cf, {"orgaos": ["direcao"]}, dry_run=True, channels=["in_app"])
    assert result["status"] == "enviado"
    doc = await env.comunicados.find_one({"id": cid})
    assert sorted(doc["audience_resolved"]) == ["ACCTA-0001", "ACCTA-0002"]
    audit = [d for d in env.audit.docs if d.get("action") == "comunicado_enviado"][-1]
    assert audit["user_id"] == "c1"                        # autor = CF
    assert audit["details"]["audience_filter"]["orgaos"] == ["direcao"]


@pytest.mark.asyncio
async def test_US4_cf_out_of_scope_forbidden(env):
    cf = _sender("c1", ["comunicar_intra_orgao"])
    payload = ComunicadoCreate(subject="Fora de âmbito", body="corpo suficientemente longo",
                               channels=["in_app"], audience_filter={"categorias": ["ordinario"]})
    with pytest.raises(Exception) as ei:
        await cmod.create_comunicado(_req(), payload, BackgroundTasks(), current_user=cf)
    assert getattr(ei.value, "status_code", None) == 403


# --------------------------------------------------------------------------- #
# Edge cases (quickstart §Edge cases)
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_edge_nominal_not_found_and_technical(env):
    prev = await svc.preview_audience(
        {"nominal_member_ids": ["ACCTA-0001", "ACCTA-9000", "ACCTA-9999"]},
        tipo="oficial", channels=["in_app"])
    codes = {w["code"] for w in prev["warnings"]}
    assert "nominal_not_found" in codes          # ACCTA-9999
    assert "technical_excluded" in codes         # ACCTA-9000
    assert prev["recipients_count"] == 1         # só ACCTA-0001


@pytest.mark.asyncio
async def test_edge_nominal_intersects_with_filter(env):
    # lista nominal (d1, c1) AND órgão direcao (d1, d2) → só d1
    res = await svc.resolve_audience(
        {"nominal_member_ids": ["ACCTA-0001", "ACCTA-0010"], "orgaos": ["direcao"]},
        channel="in_app", tipo="oficial")
    assert {u["id"] for u in res} == {"d1"}


@pytest.mark.asyncio
async def test_SC004_no_send_to_technical_via_status(env):
    res = await svc.resolve_audience({"statuses": ["ativo"]}, channel="in_app", tipo="oficial")
    assert "sys" not in {u["id"] for u in res}   # conta técnica nunca incluída
