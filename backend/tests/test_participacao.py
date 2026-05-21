"""Unit tests para participação do sócio (spec-voz-participacao-socio).

F1 — Patrocínio de admissão (Art. 8.3): confirmação/recusa pelos padrinhos.
A colecção `patrocinios` não está pré-cablada no conftest — cablamos aqui.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from routes import participacao as p
from models import PatrocinioRespond

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _req() -> Request:
    return Request(
        {"type": "http", "method": "POST", "path": "/x", "headers": [], "client": ("127.0.0.1", 1), "query_string": b""}
    )


@pytest.fixture
def env(mock_db, monkeypatch):
    monkeypatch.setattr(p, "create_audit_log", AsyncMock())
    monkeypatch.setattr(p, "notify_admins", AsyncMock())
    mock_db.patrocinios = MagicMock(name="patrocinios")
    mock_db.patrocinios.find_one = AsyncMock(return_value=None)
    mock_db.patrocinios.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    mock_db.patrocinios.count_documents = AsyncMock(return_value=1)
    return mock_db


class TestConfirmar:
    async def test_non_voting_member_403(self, env, socio_user):
        socio_user.member_category = "honorario"  # honorário não vota/patrocina
        with pytest.raises(HTTPException) as exc:
            await p.confirmar_patrocinio("c1", _req(), PatrocinioRespond(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_non_sponsor_403(self, env, socio_user):
        env.patrocinios.find_one = AsyncMock(return_value=None)  # não é padrinho deste candidato
        with pytest.raises(HTTPException) as exc:
            await p.confirmar_patrocinio("c1", _req(), PatrocinioRespond(), current_user=socio_user)
        assert exc.value.status_code == 403

    async def test_already_responded_409(self, env, socio_user):
        env.patrocinios.find_one = AsyncMock(
            return_value={"candidate_id": "c1", "sponsor_user_id": socio_user.id, "status": "confirmado"}
        )
        with pytest.raises(HTTPException) as exc:
            await p.confirmar_patrocinio("c1", _req(), PatrocinioRespond(), current_user=socio_user)
        assert exc.value.status_code == 409

    async def test_confirmar_flips_and_audits(self, env, socio_user):
        env.patrocinios.find_one = AsyncMock(
            return_value={"candidate_id": "c1", "sponsor_user_id": socio_user.id, "status": "pendente"}
        )
        result = await p.confirmar_patrocinio("c1", _req(), PatrocinioRespond(), current_user=socio_user)
        assert result["status"] == "confirmado"
        env.patrocinios.update_one.assert_awaited()
        assert any(c.args[1] == "patrocinio_confirmado" for c in p.create_audit_log.await_args_list)
        p.notify_admins.assert_not_awaited()  # só 1 confirmado

    async def test_second_confirmation_notifies_admins(self, env, socio_user):
        env.patrocinios.find_one = AsyncMock(
            return_value={"candidate_id": "c1", "sponsor_user_id": socio_user.id, "status": "pendente"}
        )
        env.patrocinios.count_documents = AsyncMock(return_value=2)  # 2.º confirmado completa
        env.users.find_one = AsyncMock(return_value={"name": "Cand"})
        await p.confirmar_patrocinio("c1", _req(), PatrocinioRespond(), current_user=socio_user)
        p.notify_admins.assert_awaited_once()


class TestRecusar:
    async def test_recusar_flips(self, env, socio_user):
        env.patrocinios.find_one = AsyncMock(
            return_value={"candidate_id": "c1", "sponsor_user_id": socio_user.id, "status": "pendente"}
        )
        result = await p.recusar_patrocinio(
            "c1", _req(), PatrocinioRespond(note="não conheço"), current_user=socio_user
        )
        assert result["status"] == "recusado"
        assert any(c.args[1] == "patrocinio_recusado" for c in p.create_audit_log.await_args_list)


class TestPendentes:
    async def test_inbox_lists_my_pending(self, env, socio_user):
        cur = MagicMock()
        cur.to_list = AsyncMock(return_value=[{"candidate_id": "c1", "status": "pendente", "created_at": "2026-05-21"}])
        env.patrocinios.find = MagicMock(return_value=cur)
        env.users.find_one = AsyncMock(return_value={"name": "Cand", "member_id": "ACCTA-0009"})
        result = await p.patrocinios_pendentes(current_user=socio_user)
        assert len(result) == 1
        assert result[0]["candidate_name"] == "Cand"
        assert result[0]["candidate_member_id"] == "ACCTA-0009"
