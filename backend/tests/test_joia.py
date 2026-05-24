"""Unit tests para a jóia de admissão (spec-controlos-financeiros §6, Art. 6).

Cobre a lógica pura (`finance_joia`) e o endpoint de preview
(`GET /finances/joia/preview`). Sem DB (mock_db para a rota).
"""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from finance_joia import compute_joia, joia_status, _qualified_more_than_months
from routes import finances as finances_route

pytestmark = pytest.mark.unit

_TODAY = date(2026, 5, 23)
_SETTINGS = {"quota_amount": 2000.0, "joia_multiplier": 2.0}


class TestQualificacao:
    def test_mais_de_4_meses(self):
        assert _qualified_more_than_months("2026-01-01", 4, _TODAY) is True

    def test_exactamente_4_meses_nao_conta(self):
        # 2026-01-23 + 4 meses = 2026-05-23 == hoje → NÃO é "mais de" 4 meses.
        assert _qualified_more_than_months("2026-01-23", 4, _TODAY) is False

    def test_menos_de_4_meses(self):
        assert _qualified_more_than_months("2026-03-01", 4, _TODAY) is False

    def test_data_ausente_ou_invalida(self):
        assert _qualified_more_than_months(None, 4, _TODAY) is False
        assert _qualified_more_than_months("", 4, _TODAY) is False
        assert _qualified_more_than_months("lixo", 4, _TODAY) is False


class TestComputeJoia:
    def test_devida_2x_quota(self):
        u = {"member_category": "ordinario", "cta_qualified_since": "2026-01-01"}
        assert compute_joia(u, _SETTINGS, _TODAY) == 4000.0

    def test_joia_amount_sobrepoe_multiplo(self):
        u = {"member_category": "ordinario", "cta_qualified_since": "2026-01-01"}
        s = {**_SETTINGS, "joia_amount": 5000.0}
        assert compute_joia(u, s, _TODAY) == 5000.0

    def test_joia_amount_zero_dispensa(self):
        # joia_amount=0.0 (jóia explicitamente dispensada) tem de devolver 0.0,
        # não cair no múltiplo joia_multiplier × quota (regressão do falsy-zero
        # em _joia_valor: `if amount:` ignorava o zero explícito).
        u = {"member_category": "ordinario", "cta_qualified_since": "2026-01-01"}
        s = {**_SETTINGS, "joia_amount": 0.0}
        assert compute_joia(u, s, _TODAY) == 0.0

    def test_joia_multiplier_zero_e_respeitado(self):
        # joia_multiplier=0.0 também tem de dispensar a jóia (0.0), não cair no
        # default 2.0 — complementa a919e09, que só tratou joia_amount=0.
        u = {"member_category": "ordinario", "cta_qualified_since": "2026-01-01"}
        s = {**_SETTINGS, "joia_multiplier": 0.0}
        assert compute_joia(u, s, _TODAY) == 0.0

    def test_sem_cta_qualified_since_isento(self):
        assert compute_joia({"member_category": "ordinario"}, _SETTINGS, _TODAY) is None

    def test_qualificado_ha_4_meses_ou_menos(self):
        u = {"member_category": "ordinario", "cta_qualified_since": "2026-03-01"}
        assert compute_joia(u, _SETTINGS, _TODAY) is None

    def test_fundador_isento(self):
        u = {"member_category": "fundador", "cta_qualified_since": "2020-01-01"}
        assert compute_joia(u, _SETTINGS, _TODAY) is None

    def test_honorario_isento(self):
        # Decisão do dono (§12.6): honorário é isento, a par de fundador.
        u = {"member_category": "honorario", "cta_qualified_since": "2020-01-01"}
        assert compute_joia(u, _SETTINGS, _TODAY) is None

    def test_joia_isento_explicito(self):
        u = {"member_category": "ordinario", "cta_qualified_since": "2020-01-01", "joia_isento": True}
        assert compute_joia(u, _SETTINGS, _TODAY) is None


class TestJoiaStatus:
    def test_devida_motivo(self):
        u = {"member_category": "ordinario", "cta_qualified_since": "2026-01-01"}
        st = joia_status(u, _SETTINGS, _TODAY)
        assert st["joia_devida"] == 4000.0 and st["isento"] is False
        assert st["valor_base"] == 4000.0 and st["quota_amount"] == 2000.0

    def test_honorario_isento_motivo(self):
        st = joia_status({"member_category": "honorario"}, _SETTINGS, _TODAY)
        assert st["joia_devida"] is None and st["isento"] is True
        assert "honorario" in st["motivo"]

    def test_sem_data_nao_isento_mas_sem_joia(self):
        st = joia_status({"member_category": "ordinario"}, _SETTINGS, _TODAY)
        assert st["joia_devida"] is None and st["isento"] is False


@pytest.mark.asyncio
class TestPreviewEndpoint:
    async def test_socio_403(self, mock_db, socio_user):
        with pytest.raises(HTTPException) as exc:
            await finances_route.preview_joia(user_id="u1", current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_user_nao_encontrado_404(self, mock_db, admin_user):
        mock_db.users.find_one = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await finances_route.preview_joia(user_id="nope", current_user=admin_user)
        assert exc.value.status_code == 404

    async def test_devolve_joia_status(self, mock_db, admin_user):
        mock_db.users.find_one = AsyncMock(
            return_value={"id": "u1", "member_category": "ordinario", "cta_qualified_since": "2020-01-01"}
        )
        mock_db.finance_settings.find_one = AsyncMock(return_value={"quota_amount": 2000.0, "joia_multiplier": 2.0})
        result = await finances_route.preview_joia(user_id="u1", current_user=admin_user)
        assert result["joia_devida"] == 4000.0

    async def test_override_cta_qualified_since(self, mock_db, admin_user):
        # Doc sem data; o override do modal torna a jóia devida.
        mock_db.users.find_one = AsyncMock(return_value={"id": "u1", "member_category": "ordinario"})
        mock_db.finance_settings.find_one = AsyncMock(return_value={"quota_amount": 2000.0, "joia_multiplier": 2.0})
        result = await finances_route.preview_joia(
            user_id="u1", cta_qualified_since="2020-01-01", current_user=admin_user
        )
        assert result["joia_devida"] == 4000.0

    async def test_settings_em_falta_usa_default(self, mock_db, admin_user):
        # finance_settings.find_one → None (default do mock); usa FinanceSettings().
        mock_db.users.find_one = AsyncMock(
            return_value={"id": "u1", "member_category": "ordinario", "cta_qualified_since": "2020-01-01"}
        )
        result = await finances_route.preview_joia(user_id="u1", current_user=admin_user)
        # default quota 2000 × 2.0 = 4000
        assert result["joia_devida"] == 4000.0
