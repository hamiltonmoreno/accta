"""Web Push (VAPID) — entrega de notificações no celular via PWA.

Isolado dos `helpers` para manter a dependência `pywebpush` e a config VAPID
num único sítio. **Degrada graciosamente**: sem as env vars VAPID (ou sem o
pacote instalado), `push_enabled()` é False e `dispatch_push` é no-op — nada na
app quebra. O `pywebpush` é importado *lazy* (dentro das funções) para que a
ausência do pacote nunca impeça o arranque do servidor.
"""

import asyncio
import json
import logging
import os
from typing import Iterable, Optional

from database import db

logger = logging.getLogger(__name__)

VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "").strip()
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "").strip()
# `sub` do claim VAPID — tem de ser um mailto: ou URL do responsável.
VAPID_SUBJECT = os.environ.get("VAPID_SUBJECT", "mailto:admin@controlador.cv").strip()

# Limite defensivo do corpo: as bandejas de notificação truncam, e payloads
# grandes só desperdiçam quota do push service.
_MAX_BODY = 180


def push_enabled() -> bool:
    """True só quando o par VAPID está configurado."""
    return bool(VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY)


def _send_one(subscription_info: dict, payload: str) -> None:
    """Envio síncrono (corre em thread). Lança WebPushException em falha."""
    from pywebpush import webpush

    webpush(
        subscription_info=subscription_info,
        data=payload,
        vapid_private_key=VAPID_PRIVATE_KEY,
        vapid_claims={"sub": VAPID_SUBJECT},
        timeout=10,
    )


async def dispatch_push(
    user_ids: Iterable[str],
    title: str,
    body: str,
    link: Optional[str] = None,
) -> None:
    """Dispara um Web Push a todas as subscrições dos `user_ids`.

    Best-effort e tolerante a falha — nunca propaga exceção para o chamador
    (a criação da notificação in-app não pode rebentar por causa do push).
    Subscrições mortas (404/410 Gone) são podadas.
    """
    if not push_enabled():
        return
    ids = list({uid for uid in (user_ids or []) if uid})
    if not ids:
        return

    try:
        from pywebpush import WebPushException
    except Exception:  # pragma: no cover - pacote ausente => feature off
        logger.warning("pywebpush não instalado; push desativado")
        return

    subs = await db.push_subscriptions.find({"user_id": {"$in": ids}}, {"_id": 0}).to_list(None)
    if not subs:
        return

    payload = json.dumps(
        {"title": title, "body": (body or "")[:_MAX_BODY], "url": link or "/"},
        ensure_ascii=False,
    )

    async def _push(sub: dict) -> None:
        endpoint = sub.get("endpoint")
        sub_info = {
            "endpoint": endpoint,
            "keys": {"p256dh": sub.get("p256dh"), "auth": sub.get("auth")},
        }
        try:
            await asyncio.to_thread(_send_one, sub_info, payload)
        except WebPushException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (404, 410):
                # Subscrição expirada/revogada — poda silenciosa.
                await db.push_subscriptions.delete_one({"endpoint": endpoint})
            else:
                logger.warning("web push falhou (status=%s): %s", status, exc)
        except Exception as exc:  # rede, timeout, payload — nunca rebenta o fluxo
            logger.warning("web push erro inesperado: %s", exc)

    await asyncio.gather(*(_push(s) for s in subs))
