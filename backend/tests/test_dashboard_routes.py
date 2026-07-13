"""Dashboard universal (spec 020) — endpoint `/api/dashboard/overview`.

Contract:
- 200 para qualquer utilizador autenticado (admin, socio, financeiro, moderador).
- Payload segue `DashboardOverview` (Pydantic response_model).
- Tripwire PII: nenhum campo do payload contém `email`/`name`/`member_id`/
  `photo_url`/`phone`/etc.
- Reutiliza `compute_financial_summary` e `compute_dre_report` (não duplica).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import routes.dashboard as dashboard_module
import routes.finances as finances_module


def _wire_extra_collections(mock_db):
    """`atos` e `assembleias` não vêm pré-configuradas no fixture `mock_db`
    canónico (conftest.py). Padrão herdado das specs 014/015 (ver CLAUDE.md
    §Testing Architecture — project_tasks etc)."""
    for name in ("atos", "assembleias"):
        coll = MagicMock(name=name)
        coll.count_documents = AsyncMock(return_value=0)
        find_cursor = MagicMock()
        find_cursor.to_list = AsyncMock(return_value=[])
        find_cursor.sort = MagicMock(return_value=find_cursor)
        find_cursor.limit = MagicMock(return_value=find_cursor)
        coll.find = MagicMock(return_value=find_cursor)
        setattr(mock_db, name, coll)


# Chaves proibidas em qualquer nível do payload — comprova SC-002 (0 fugas PII).
_FORBIDDEN_KEYS = {
    "email",
    "phone",
    "member_id",
    "name",
    "cpf",
    "password",
    "photo_url",
    "address",
}


def _walk_for_pii(obj, path: str = "$") -> None:
    """Falha se encontrar qualquer chave PII em qualquer nível do payload."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in _FORBIDDEN_KEYS, f"PII leak em {path}.{k}"
            _walk_for_pii(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _walk_for_pii(v, f"{path}[{i}]")


def _prime_finance_mocks(mock_db):
    """Devolve um único doc de transacção via find(...).to_list — cobre as
    3 chamadas de compute_financial_summary + 1 de compute_dre_report + a
    query de quotas_mes. Também wire de coleções em falta (atos/assembleias)."""
    _wire_extra_collections(mock_db)
    tx_row = {
        "type": "receita",
        "amount": 100.0,
        "category": "quota",
        "description": "quota jan",
        "date": "2026-01-15T10:00:00",
    }
    mock_db.transactions.find.return_value.to_list = AsyncMock(return_value=[tx_row])


async def _call(user):
    return await dashboard_module.get_overview(current_user=user)


# --------------------------------------------------------------------------- #
# US1 — Admin recebe o payload agregado
# --------------------------------------------------------------------------- #


async def test_admin_get_overview_returns_200_with_shape(mock_db, admin_user):
    _prime_finance_mocks(mock_db)
    result = await _call(admin_user)

    payload = result.model_dump()
    assert set(payload) == {"finance", "socios", "atos", "votacoes", "assembleias"}
    # finance
    assert set(payload["finance"]) == {
        "saldo_atual",
        "receitas_ano",
        "despesas_ano",
        "resultado_ano",
        "quotas_mes",
        "monthly",
        "despesas_por_categoria",
        "mes_atual",
        "mes_anterior",
    }
    assert len(payload["finance"]["monthly"]) == 12  # DRE devolve sempre 12 pontos
    # atos
    assert "pendentes" in payload["atos"]
    # votacoes
    assert set(payload["votacoes"]) == {"abertas", "ultima_fechada"}
    # assembleias
    assert "proximas" in payload["assembleias"]


# --------------------------------------------------------------------------- #
# US1 — Sócio comum recebe o MESMO shape (paridade — evidência de SC-001)
# --------------------------------------------------------------------------- #


async def test_socio_get_overview_matches_admin_shape(mock_db, admin_user, socio_user):
    _prime_finance_mocks(mock_db)
    admin_payload = (await _call(admin_user)).model_dump()
    _prime_finance_mocks(mock_db)  # re-primar após mock ter sido consumido
    socio_payload = (await _call(socio_user)).model_dump()

    # Paridade estrutural — mesmas chaves, mesma profundidade.
    def _shape(o):
        if isinstance(o, dict):
            return {k: _shape(v) for k, v in sorted(o.items())}
        if isinstance(o, list):
            return [_shape(v) for v in o[:1]]  # só uma amostra por lista
        return type(o).__name__

    assert _shape(admin_payload) == _shape(socio_payload), (
        "sócio comum tem de receber exactamente o mesmo shape do admin (SC-001)"
    )


# --------------------------------------------------------------------------- #
# SC-002 — Tripwire PII
# --------------------------------------------------------------------------- #


async def test_overview_no_pii(mock_db, socio_user):
    _prime_finance_mocks(mock_db)
    # Adicionar dados nos outros blocos para exercitar o walker recursivamente.
    mock_db.polls.find.return_value.to_list = AsyncMock(
        return_value=[{"id": "p1", "title": "Aprovação orçamento", "end_date": "2026-05-30T18:00:00"}]
    )
    mock_db.assembleias.find.return_value.to_list = AsyncMock(
        return_value=[{"id": "a1", "titulo": "AGA Ordinária", "data": "2026-09-15", "tipo": "ordinaria"}]
    )

    result = await _call(socio_user)
    _walk_for_pii(result.model_dump())


# --------------------------------------------------------------------------- #
# Reutilização das funções compute_* (não duplica lógica)
# --------------------------------------------------------------------------- #


async def test_overview_calls_compute_financial_summary(mock_db, socio_user, monkeypatch):
    """O endpoint MUST chamar compute_financial_summary — se alguém decidir
    duplicar a lógica no dashboard.py, o teste falha e força o revert."""
    _prime_finance_mocks(mock_db)
    calls = []

    original = finances_module.compute_financial_summary

    async def _tracker(*args, **kwargs):
        calls.append(kwargs)
        return await original(*args, **kwargs)

    monkeypatch.setattr(dashboard_module, "compute_financial_summary", _tracker)

    await _call(socio_user)

    # Chamadas esperadas: total (sem args), mês actual (year+month), mês anterior.
    assert len(calls) == 3
    # 1ª = total (sem year/month)
    assert calls[0].get("year") is None and calls[0].get("month") is None
    # 2ª+3ª têm year e month
    for c in calls[1:]:
        assert c.get("year") and c.get("month")


async def test_overview_calls_compute_dre_report(mock_db, socio_user, monkeypatch):
    _prime_finance_mocks(mock_db)
    called_with = []

    original = finances_module.compute_dre_report

    async def _tracker(year):
        called_with.append(year)
        return await original(year)

    monkeypatch.setattr(dashboard_module, "compute_dre_report", _tracker)

    await _call(socio_user)

    assert len(called_with) == 1  # 1 chamada — DRE do ano em curso
    # ano positivo, plausível
    assert called_with[0] >= 2020


# --------------------------------------------------------------------------- #
# Contagens de sócios excluem contas técnicas + membros count filter é aplicado
# --------------------------------------------------------------------------- #


async def test_overview_socios_uses_member_filter(mock_db, socio_user):
    """`socios.ativos` MUST usar `_MEMBER_FILTER` (exclui `account_type=technical`)
    — mesma regra que /stats. Regressão da mesma classe de bug do stats."""
    _prime_finance_mocks(mock_db)
    await _call(socio_user)

    # Pelo menos uma das chamadas a count_documents em users tem status=ativo
    # combinado com o _MEMBER_FILTER canónico.
    calls = [c.args[0] for c in mock_db.users.count_documents.call_args_list]
    ativos_call = next(
        (
            c
            for c in calls
            if isinstance(c, dict)
            and c.get("$and")
            and any(sub.get("status") == "ativo" for sub in c["$and"] if isinstance(sub, dict))
        ),
        None,
    )
    assert ativos_call is not None, "esperada uma query com status=ativo + filtro de membros"
    # O filtro de membros tem de aparecer no $and
    assert any(isinstance(sub, dict) and sub.get("$or") for sub in ativos_call["$and"]), (
        "contagem de sócios activos tem de aplicar o filtro de membros (exclui technical)"
    )


# --------------------------------------------------------------------------- #
# Ausência de ultima_fechada é OK (não parte quando não há polls fechadas)
# --------------------------------------------------------------------------- #


async def test_overview_handles_empty_ultima_fechada(mock_db, socio_user):
    _prime_finance_mocks(mock_db)
    # polls.find retorna vazio para "fechada"
    mock_db.polls.find.return_value.to_list = AsyncMock(return_value=[])
    result = await _call(socio_user)
    assert result.votacoes.ultima_fechada is None
