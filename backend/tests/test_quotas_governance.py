"""Unit tests para quota/jóia ligadas a deliberação de AG (spec-governanca §14/§18).

Alterar quota/jóia exige deliberação de AG por maioria 3/4; a versão anterior
é registada em finance_settings_history. quota_description (label) não exige
deliberação.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes import finances as finances_route
from models import FinanceSettingsUpdate


pytestmark = [pytest.mark.asyncio]


def _coll(**methods):
    c = MagicMock()
    c.find_one = AsyncMock(return_value=None)
    c.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
    c.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    cur = MagicMock()
    cur.sort.return_value = cur
    cur.to_list = AsyncMock(return_value=[])
    c.find = MagicMock(return_value=cur)
    for k, v in methods.items():
        setattr(c, k, v)
    return c


@pytest.fixture
def fin_env(mock_db, monkeypatch):
    mock_db.assembleia_deliberacoes = _coll()
    mock_db.finance_settings_history = _coll()
    mock_db.finance_settings.find_one = AsyncMock(
        return_value={"id": "finance_settings", "quota_amount": 2000.0, "joia_multiplier": 2.0}
    )
    monkeypatch.setattr(finances_route, "create_audit_log", AsyncMock())
    monkeypatch.setattr(finances_route, "notify_admins", AsyncMock())
    return mock_db


class TestQuotaGovernance:
    async def test_quota_sem_deliberacao_400(self, fin_env, admin_user):
        with pytest.raises(HTTPException) as exc:
            await finances_route.update_finance_settings(
                data=FinanceSettingsUpdate(quota_amount=3000), current_user=admin_user
            )
        assert exc.value.status_code == 400

    async def test_deliberacao_nao_3_4_400(self, fin_env, admin_user):
        fin_env.assembleia_deliberacoes.find_one = AsyncMock(
            return_value={"aprovado": True, "tipo_maioria": "absoluta"}
        )
        with pytest.raises(HTTPException) as exc:
            await finances_route.update_finance_settings(
                data=FinanceSettingsUpdate(quota_amount=3000, assembleia_id="a1", deliberacao_id="d1"),
                current_user=admin_user,
            )
        assert exc.value.status_code == 400

    async def test_deliberacao_nao_aprovada_400(self, fin_env, admin_user):
        fin_env.assembleia_deliberacoes.find_one = AsyncMock(
            return_value={"aprovado": False, "tipo_maioria": "qualificada_3_4_universo"}
        )
        with pytest.raises(HTTPException) as exc:
            await finances_route.update_finance_settings(
                data=FinanceSettingsUpdate(quota_amount=3000, assembleia_id="a1", deliberacao_id="d1"),
                current_user=admin_user,
            )
        assert exc.value.status_code == 400

    async def test_quota_com_3_4_regista_historico(self, fin_env, admin_user):
        fin_env.assembleia_deliberacoes.find_one = AsyncMock(
            return_value={"aprovado": True, "tipo_maioria": "qualificada_3_4_universo"}
        )
        snapshot = {}
        fin_env.finance_settings_history.insert_one = AsyncMock(side_effect=lambda d: snapshot.update(d))
        upd = {}
        fin_env.finance_settings.update_one = AsyncMock(side_effect=lambda f, u: upd.update(u["$set"]))

        result = await finances_route.update_finance_settings(
            data=FinanceSettingsUpdate(quota_amount=3000, assembleia_id="a1", deliberacao_id="d1"),
            current_user=admin_user,
        )
        assert "atualizadas" in result["message"].lower()
        # versão anterior arquivada
        assert snapshot["quota_amount"] == 2000.0
        assert snapshot["deliberacao_id"] == "d1"
        # nova versão liga à deliberação e resolve a jóia (2x a nova quota)
        assert upd["quota_amount"] == 3000
        assert upd["quota_fixed_by_deliberacao_id"] == "d1"
        assert upd["joia_amount"] == 6000.0
        assert upd["effective_from"]

    async def test_descricao_so_nao_exige_deliberacao(self, fin_env, admin_user):
        upd = {}
        fin_env.finance_settings.update_one = AsyncMock(side_effect=lambda f, u: upd.update(u["$set"]))
        result = await finances_route.update_finance_settings(
            data=FinanceSettingsUpdate(quota_description="Quota Anual"), current_user=admin_user
        )
        assert "atualizadas" in result["message"].lower()
        assert upd["quota_description"] == "Quota Anual"
        # não toca em campos de quota fixada
        assert "quota_fixed_by_deliberacao_id" not in upd
