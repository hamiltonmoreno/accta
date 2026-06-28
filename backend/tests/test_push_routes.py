"""Unit tests para Web Push (notificações no celular via PWA).

Cobre as rotas /api/push (subscribe upsert, unsubscribe, vapid-public-key
gating 503/200, test 400/200) e o `push_service.dispatch_push` (no-op quando
desativado; envio + poda de subscrições mortas 410). `push_subscriptions` não
está pré-ligada no conftest — liga-se aqui. O pacote `pywebpush` pode não estar
instalado no ambiente de teste: injeta-se um módulo falso em sys.modules.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import AsyncMock, MagicMock

import pytest

import push_service
from routes import push as push_route
from models import PushSubscriptionRequest

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _request(ua="pytest-agent"):
    class _R:
        headers = {"user-agent": ua}

    return _R()


def _sub_payload(endpoint="https://push.example/abc"):
    return PushSubscriptionRequest(endpoint=endpoint, keys={"p256dh": "PPP", "auth": "AAA"})


@pytest.fixture
def push_env(mock_db, monkeypatch):
    """push_subscriptions wired + VAPID configurado (push ligado)."""
    coll = MagicMock(name="push_subscriptions")
    coll.find_one = AsyncMock(return_value=None)
    coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
    coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    coll.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    coll.count_documents = AsyncMock(return_value=0)
    find_cursor = MagicMock()
    find_cursor.to_list = AsyncMock(return_value=[])
    coll.find = MagicMock(return_value=find_cursor)
    mock_db.push_subscriptions = coll
    # push_service faz `from database import db` no topo — patch explícito.
    monkeypatch.setattr(push_service, "db", mock_db)
    monkeypatch.setattr(push_service, "VAPID_PUBLIC_KEY", "PUBKEY")
    monkeypatch.setattr(push_service, "VAPID_PRIVATE_KEY", "PRIVKEY")
    return mock_db


class TestSubscribe:
    async def test_insere_quando_nova(self, push_env, socio_user_dict):
        push_env.push_subscriptions.find_one = AsyncMock(return_value=None)
        res = await push_route.subscribe(_sub_payload(), _request(), socio_user_dict)
        assert res == {"ok": True}
        push_env.push_subscriptions.insert_one.assert_awaited_once()
        doc = push_env.push_subscriptions.insert_one.call_args.args[0]
        assert doc["user_id"] == socio_user_dict["id"]
        assert doc["endpoint"] == "https://push.example/abc"
        assert doc["p256dh"] == "PPP" and doc["auth"] == "AAA"
        assert "id" in doc and "created_at" in doc

    async def test_atualiza_quando_existe(self, push_env, socio_user_dict):
        push_env.push_subscriptions.find_one = AsyncMock(return_value={"id": "existing"})
        res = await push_route.subscribe(_sub_payload(), _request(), socio_user_dict)
        assert res == {"ok": True}
        push_env.push_subscriptions.update_one.assert_awaited_once()
        push_env.push_subscriptions.insert_one.assert_not_awaited()

    async def test_503_quando_desligado(self, push_env, monkeypatch, socio_user_dict):
        monkeypatch.setattr(push_service, "VAPID_PRIVATE_KEY", "")
        with pytest.raises(Exception) as exc:
            await push_route.subscribe(_sub_payload(), _request(), socio_user_dict)
        assert getattr(exc.value, "status_code", None) == 503


class TestUnsubscribe:
    async def test_apaga_do_proprio(self, push_env, socio_user_dict):
        res = await push_route.unsubscribe(_sub_payload(), socio_user_dict)
        assert res == {"ok": True}
        push_env.push_subscriptions.delete_one.assert_awaited_once()
        flt = push_env.push_subscriptions.delete_one.call_args.args[0]
        assert flt["user_id"] == socio_user_dict["id"]
        assert flt["endpoint"] == "https://push.example/abc"


class TestVapidKey:
    async def test_503_sem_config(self, push_env, monkeypatch, socio_user_dict):
        monkeypatch.setattr(push_service, "VAPID_PUBLIC_KEY", "")
        monkeypatch.setattr(push_service, "VAPID_PRIVATE_KEY", "")
        with pytest.raises(Exception) as exc:
            await push_route.get_vapid_public_key(socio_user_dict)
        assert getattr(exc.value, "status_code", None) == 503

    async def test_200_com_config(self, push_env, socio_user_dict):
        res = await push_route.get_vapid_public_key(socio_user_dict)
        assert res == {"publicKey": "PUBKEY"}


class TestTestPush:
    async def test_400_sem_dispositivos(self, push_env, socio_user_dict):
        push_env.push_subscriptions.count_documents = AsyncMock(return_value=0)
        with pytest.raises(Exception) as exc:
            await push_route.test_push(socio_user_dict)
        assert getattr(exc.value, "status_code", None) == 400

    async def test_200_com_dispositivos(self, push_env, monkeypatch, socio_user_dict):
        push_env.push_subscriptions.count_documents = AsyncMock(return_value=2)
        dispatch = AsyncMock()
        monkeypatch.setattr(push_route, "dispatch_push", dispatch)
        res = await push_route.test_push(socio_user_dict)
        assert res == {"ok": True, "devices": 2}
        dispatch.assert_awaited_once()


class TestDispatchPush:
    async def test_noop_quando_desligado(self, push_env, monkeypatch):
        monkeypatch.setattr(push_service, "VAPID_PRIVATE_KEY", "")
        # Não deve sequer consultar a BD.
        await push_service.dispatch_push(["u1"], "T", "B", "/x")
        push_env.push_subscriptions.find.assert_not_called()

    async def test_envia_e_poda_410(self, push_env, monkeypatch):
        # Módulo pywebpush falso: webpook normal numa sub, 410 (Gone) noutra.
        class FakeResponse:
            def __init__(self, status):
                self.status_code = status

        class WebPushException(Exception):
            def __init__(self, msg, response=None):
                super().__init__(msg)
                self.response = response

        calls = []

        def fake_webpush(subscription_info, data, vapid_private_key, vapid_claims, timeout):
            calls.append(subscription_info["endpoint"])
            if subscription_info["endpoint"].endswith("dead"):
                raise WebPushException("gone", response=FakeResponse(410))

        fake_mod = types.ModuleType("pywebpush")
        fake_mod.webpush = fake_webpush
        fake_mod.WebPushException = WebPushException
        monkeypatch.setitem(sys.modules, "pywebpush", fake_mod)

        cursor = MagicMock()
        cursor.to_list = AsyncMock(
            return_value=[
                {"endpoint": "https://push/live", "p256dh": "p1", "auth": "a1"},
                {"endpoint": "https://push/dead", "p256dh": "p2", "auth": "a2"},
            ]
        )
        push_env.push_subscriptions.find = MagicMock(return_value=cursor)
        delete = AsyncMock()
        push_env.push_subscriptions.delete_one = delete

        await push_service.dispatch_push(["u1"], "Título", "Corpo", "/carteira")

        assert set(calls) == {"https://push/live", "https://push/dead"}
        # Só a subscrição morta (410) é podada.
        delete.assert_awaited_once_with({"endpoint": "https://push/dead"})
