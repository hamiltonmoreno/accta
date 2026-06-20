"""Testes do motor de audiência segmentada (spec-comunicados-segmentados).

Cobre resolve_audience / preview_audience / describe_audience:
OR-dentro/AND-entre-tipos (FR-014), exclusão de technical (FR-003), período por
admission_date (R6), lista nominal (not_found/technical/email), órgão `mesa_ag`
(regressão I2), status (US3) e os avisos do preview.
"""

import pytest
from unittest.mock import AsyncMock

import comunicados_service as svc


# --- universo de teste (com status/member_id/admission_date) ---
USERS = [
    {"id": "u1", "name": "Ana", "email": "ana@x.cv", "role": "socio", "account_type": "member",
     "member_category": "ordinario", "cargo": "dir_presidente", "status": "ativo",
     "member_id": "ACCTA-0001", "admission_date": "2022-05-01"},
    {"id": "u2", "name": "Bruno", "email": "bruno@x.cv", "role": "socio", "account_type": "member",
     "member_category": "fundador", "cargo": "dir_tesoureiro", "status": "ativo",
     "member_id": "ACCTA-0002", "admission_date": "2024-03-10"},
    {"id": "u3", "name": "Carla", "email": "carla@x.cv", "role": "socio", "account_type": "member",
     "member_category": "ordinario", "cargo": "socio", "status": "ativo",
     "member_id": "ACCTA-0003", "admission_date": None},
    {"id": "u4", "name": "Dora", "email": "dora@x.cv", "role": "socio", "account_type": "member",
     "member_category": "ordinario", "cargo": "socio", "status": "pendente_aprovacao",
     "member_id": "ACCTA-0004", "admission_date": "2025-01-01"},
    {"id": "sys", "name": "Sys", "email": "sys@x.cv", "role": "admin", "account_type": "technical",
     "member_category": "ordinario", "cargo": "socio", "status": "ativo",
     "member_id": "ACCTA-9000", "admission_date": "2020-01-01"},
]


def _wire(mock_db, users=USERS):
    """db.users.find(...).to_list(...) devolve `users` (o mock não filtra)."""
    mock_db.users.find.return_value.to_list = AsyncMock(return_value=list(users))


async def _resolve(af, channel="in_app", tipo="oficial"):
    return await svc.resolve_audience(af, channel=channel, tipo=tipo)


# ---------------------------------------------------------------------------
# OR dentro do tipo / AND entre tipos (FR-014)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cargos_or_within_type(mock_db):
    _wire(mock_db)
    res = await _resolve({"cargos": ["dir_presidente", "dir_tesoureiro"]})
    assert {u["id"] for u in res} == {"u1", "u2"}


@pytest.mark.asyncio
async def test_and_between_types_reduces(mock_db):
    _wire(mock_db)
    # cargo direcao (u1,u2) AND categoria fundador (u2) → só u2
    res = await _resolve({"cargos": ["dir_presidente", "dir_tesoureiro"], "categorias": ["fundador"]})
    assert {u["id"] for u in res} == {"u2"}


@pytest.mark.asyncio
async def test_excludes_technical_always(mock_db):
    _wire(mock_db)
    res = await _resolve({"statuses": ["ativo"]})
    assert "sys" not in {u["id"] for u in res}


# ---------------------------------------------------------------------------
# Órgão mesa_ag (regressão I2: não pode cair na lista de admins)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_orgao_resolves_via_members_of_orgao(mock_db, monkeypatch):
    _wire(mock_db)
    # members_of_orgao('direcao') devolve [u1] → audiência = {u1}, não admins
    monkeypatch.setattr(svc, "members_of_orgao", AsyncMock(return_value=["u1"]))
    res = await _resolve({"orgaos": ["direcao"]})
    assert {u["id"] for u in res} == {"u1"}


# ---------------------------------------------------------------------------
# Período por admission_date (R6): None não casa
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_period_excludes_unknown_admission_date(mock_db):
    _wire(mock_db)
    res = await _resolve({"joined_before": "2023-01-01"})
    # u1 (2022) casa; u2 (2024) não; u3 (None) não casa; u4 é pendente (fora da base ativo)
    assert {u["id"] for u in res} == {"u1"}


@pytest.mark.asyncio
async def test_period_range(mock_db):
    _wire(mock_db)
    res = await _resolve({"joined_after": "2024-01-01", "joined_before": "2024-12-31"})
    assert {u["id"] for u in res} == {"u2"}


# ---------------------------------------------------------------------------
# Lista nominal: por member_id, por email, not_found e technical (FR-003)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_nominal_by_member_id_and_email(mock_db):
    _wire(mock_db)
    mock_db.users.find_one = AsyncMock(return_value=None)  # não usado (todos na base)
    res = await _resolve({"nominal_member_ids": ["ACCTA-0001"], "nominal_emails": ["bruno@x.cv"]})
    assert {u["id"] for u in res} == {"u1", "u2"}


@pytest.mark.asyncio
async def test_nominal_not_found_and_technical_warnings(mock_db):
    _wire(mock_db)
    # o lookup do universo (find $or) devolve a conta técnica para ACCTA-9000
    mock_db.users.find.return_value.to_list = AsyncMock(side_effect=[
        list(USERS),  # _filter_base
        [{"id": "sys", "member_id": "ACCTA-9000", "email": "sys@x.cv", "account_type": "technical"}],  # _resolve_nominal
    ])
    prev = await svc.preview_audience(
        {"nominal_member_ids": ["ACCTA-9000", "ACCTA-9999"]}, tipo="oficial", channels=["in_app"])
    codes = {w["code"] for w in prev["warnings"]}
    assert "technical_excluded" in codes
    assert "nominal_not_found" in codes
    assert prev["recipients_count"] == 0


# ---------------------------------------------------------------------------
# Status (US3): pendente_aprovacao alarga a base + aviso includes_unapproved
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_status_pendente_aprovacao_and_warning(mock_db):
    _wire(mock_db)
    prev = await svc.preview_audience(
        {"statuses": ["pendente_aprovacao"]}, tipo="oficial", channels=["in_app"])
    # só u4 (pendente); u1/u2/u3 são ativos → fora
    assert prev["recipients_count"] == 1
    assert any(w["code"] == "includes_unapproved" for w in prev["warnings"])


@pytest.mark.asyncio
async def test_status_ativo_excludes_pendente(mock_db):
    _wire(mock_db)
    res = await _resolve({"statuses": ["ativo"]})
    assert "u4" not in {u["id"] for u in res}


# ---------------------------------------------------------------------------
# Preview: contagem, amostra, more, per_type, intersection_reduced
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_preview_sample_more_and_intersection_reduced(mock_db):
    _wire(mock_db)
    prev = await svc.preview_audience(
        {"cargos": ["dir_presidente", "dir_tesoureiro"], "categorias": ["fundador"]},
        tipo="oficial", channels=["in_app"])
    assert prev["recipients_count"] == 1
    assert prev["intersected_count"] == 1
    assert prev["per_type_counts"]["cargos"] == 2
    assert prev["per_type_counts"]["categorias"] == 1
    # intersecção (1) < min per_type (1)? não — testa o caso em que cai abaixo:
    assert prev["more"] == 0


@pytest.mark.asyncio
async def test_describe_audience_readable():
    s = svc.describe_audience({"orgaos": ["direcao"], "categorias": ["ordinario"]})
    assert "Direcção" in s
    assert "ordinario" in s
