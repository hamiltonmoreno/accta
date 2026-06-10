"""
ACCTA Email Service — Resend integration for transactional emails.
Supports: invite, password reset, welcome, broadcast notifications.
"""

import os
import asyncio
import logging
from html import escape
import resend

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "noreply@controlador.cv")
APP_NAME = "Portal ACCTA"
_BATCH_CHUNK_SIZE = 100  # Resend Batch aceita até 100 por chamada

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


def _base_template(content: str) -> str:
    """Wrap content in ACCTA branded email template."""
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f4f6fa;font-family:'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6fa;padding:40px 20px;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">

<!-- Header -->
<tr><td style="background-color:#3A3A3A;padding:24px 32px;text-align:center;">
  <table cellpadding="0" cellspacing="0" align="center"><tr>
    <td style="width:8px;height:28px;background-color:#C7202F;border-radius:4px;"></td>
    <td style="padding-left:12px;font-size:18px;font-weight:700;color:#ffffff;letter-spacing:1px;">ACCTA</td>
  </tr></table>
  <p style="margin:6px 0 0;font-size:11px;color:#94a3b8;letter-spacing:0.5px;">Associacao dos Controladores de Trafego Aereo</p>
</td></tr>

<!-- Content -->
<tr><td style="padding:32px;">
{content}
</td></tr>

<!-- Footer -->
<tr><td style="padding:20px 32px;background-color:#f9fafb;border-top:1px solid #e5e7eb;text-align:center;">
  <p style="margin:0;font-size:11px;color:#9ca3af;">Este email foi enviado automaticamente pelo {APP_NAME}.</p>
  <p style="margin:4px 0 0;font-size:11px;color:#9ca3af;">Cabo Verde</p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def invite_email_html(name: str, setup_url: str) -> str:
    name = escape(name or "", quote=True)  # nome é livre/auto-registo → escapar
    content = f"""
    <h2 style="margin:0 0 8px;font-size:20px;color:#3A3A3A;">Bem-vindo a ACCTA, {name}!</h2>
    <p style="margin:0 0 20px;font-size:14px;color:#6b7280;line-height:1.6;">
      Foi convidado para se juntar ao Portal da Associacao dos Controladores de Trafego Aereo de Cabo Verde.
    </p>
    <p style="margin:0 0 24px;font-size:14px;color:#6b7280;line-height:1.6;">
      Para ativar a sua conta, clique no botao abaixo e defina a sua senha:
    </p>
    <table cellpadding="0" cellspacing="0" width="100%"><tr><td align="center">
      <a href="{setup_url}" style="display:inline-block;padding:12px 32px;background-color:#C7202F;color:#ffffff;font-size:14px;font-weight:600;text-decoration:none;border-radius:8px;">
        Ativar Conta
      </a>
    </td></tr></table>
    <p style="margin:24px 0 0;font-size:12px;color:#9ca3af;line-height:1.5;">
      Se o botao nao funcionar, copie e cole este link no seu navegador:<br>
      <a href="{setup_url}" style="color:#C7202F;word-break:break-all;">{setup_url}</a>
    </p>
    <p style="margin:16px 0 0;font-size:12px;color:#9ca3af;">
      Este convite e valido ate ser utilizado. Se nao solicitou este convite, ignore este email.
    </p>"""
    return _base_template(content)


def password_reset_email_html(name: str, reset_url: str, token: str) -> str:
    name = escape(name or "", quote=True)
    content = f"""
    <h2 style="margin:0 0 8px;font-size:20px;color:#3A3A3A;">Recuperacao de Senha</h2>
    <p style="margin:0 0 20px;font-size:14px;color:#6b7280;line-height:1.6;">
      Ola {name}, recebemos um pedido para redefinir a sua senha no Portal ACCTA.
    </p>
    <p style="margin:0 0 24px;font-size:14px;color:#6b7280;line-height:1.6;">
      Use o codigo abaixo na pagina de recuperacao:
    </p>
    <table cellpadding="0" cellspacing="0" width="100%"><tr><td align="center">
      <div style="display:inline-block;padding:14px 28px;background-color:#f4f6fa;border:2px dashed #d1d5db;border-radius:8px;font-family:monospace;font-size:18px;font-weight:700;color:#3A3A3A;letter-spacing:2px;">
        {token}
      </div>
    </td></tr></table>
    <p style="margin:24px 0 0;font-size:12px;color:#9ca3af;">
      Este codigo expira em 1 hora. Se nao solicitou a recuperacao, ignore este email.
    </p>"""
    return _base_template(content)


def welcome_email_html(name: str) -> str:
    name = escape(name or "", quote=True)
    content = f"""
    <h2 style="margin:0 0 8px;font-size:20px;color:#3A3A3A;">Conta Ativada!</h2>
    <p style="margin:0 0 20px;font-size:14px;color:#6b7280;line-height:1.6;">
      Ola {name}, a sua conta no Portal ACCTA foi ativada com sucesso.
    </p>
    <p style="margin:0 0 24px;font-size:14px;color:#6b7280;line-height:1.6;">
      Agora tem acesso a todas as funcionalidades da area reservada: dashboard, votacoes, eventos, documentos, mural e muito mais.
    </p>
    <table cellpadding="0" cellspacing="0" width="100%"><tr><td align="center">
      <a href="#" style="display:inline-block;padding:12px 32px;background-color:#C7202F;color:#ffffff;font-size:14px;font-weight:600;text-decoration:none;border-radius:8px;">
        Aceder ao Portal
      </a>
    </td></tr></table>"""
    return _base_template(content)


def registration_rejected_email_html(name: str, reason: str = None) -> str:
    name = escape(name or "", quote=True)
    reason = escape(reason, quote=True) if reason else reason
    reason_block = ""
    if reason:
        reason_block = f"""
    <div style="margin:0 0 24px;padding:14px 16px;background-color:#f9fafb;border-left:3px solid #d1d5db;border-radius:6px;">
      <p style="margin:0;font-size:13px;color:#6b7280;line-height:1.6;"><strong style="color:#3A3A3A;">Motivo:</strong> {reason}</p>
    </div>"""
    content = f"""
    <h2 style="margin:0 0 8px;font-size:20px;color:#3A3A3A;">Pedido de inscricao</h2>
    <p style="margin:0 0 20px;font-size:14px;color:#6b7280;line-height:1.6;">
      Ola {name}, agradecemos o seu interesse na Associacao dos Controladores de Trafego Aereo de Cabo Verde.
    </p>
    <p style="margin:0 0 24px;font-size:14px;color:#6b7280;line-height:1.6;">
      Apos analise, nao nos foi possivel aprovar o seu pedido de inscricao neste momento.
    </p>{reason_block}
    <p style="margin:0;font-size:13px;color:#9ca3af;line-height:1.6;">
      Se considerar que se trata de um engano, pode contactar a direcao da ACCTA.
    </p>"""
    return _base_template(content)


def _mask_email(addr: str) -> str:
    """PII nos logs: mascara o local-part (ab***@dominio) — logs centralizados
    não devem acumular emails completos de utilizadores."""
    local, _, domain = (addr or "").partition("@")
    return f"{local[:2]}***@{domain}" if domain else "***"


async def send_email(to: str, subject: str, html: str) -> dict:
    """Send email via Resend API (non-blocking)."""
    if not RESEND_API_KEY:
        logger.warning(f"RESEND_API_KEY not set. Email to {_mask_email(to)} not sent.")
        return {"status": "skipped", "reason": "no_api_key"}

    params = {
        "from": f"{APP_NAME} <{SENDER_EMAIL}>",
        "to": [to],
        "subject": subject,
        "html": html,
    }

    try:
        # Timeout: a Resend lenta/indisponível não pode prender o handler que
        # aguarda este resultado (ex.: convite/aprovação de admin) — sem isto o
        # request ficava pendurado até ao timeout do cliente HTTP.
        result = await asyncio.wait_for(asyncio.to_thread(resend.Emails.send, params), timeout=15)
        logger.info(f"Email sent to {_mask_email(to)}: {result.get('id', 'ok')}")
        return {"status": "sent", "email_id": result.get("id")}
    except TimeoutError:
        logger.error(f"Timeout (15s) ao enviar email para {_mask_email(to)}")
        return {"status": "failed", "error": "timeout"}
    except Exception as e:
        logger.error(f"Failed to send email to {_mask_email(to)}: {str(e)}")
        return {"status": "failed", "error": str(e)}


async def send_invite_email(name: str, email: str, setup_url: str) -> dict:
    html = invite_email_html(name, setup_url)
    return await send_email(email, f"Convite — {APP_NAME}", html)


async def send_password_reset_email(name: str, email: str, reset_url: str, token: str) -> dict:
    html = password_reset_email_html(name, reset_url, token)
    return await send_email(email, f"Recuperacao de Senha — {APP_NAME}", html)


async def send_welcome_email(name: str, email: str) -> dict:
    html = welcome_email_html(name)
    return await send_email(email, f"Bem-vindo — {APP_NAME}", html)


async def send_registration_rejected_email(name: str, email: str, reason: str = None) -> dict:
    html = registration_rejected_email_html(name, reason)
    return await send_email(email, f"Pedido de inscricao — {APP_NAME}", html)


def comunicado_email_html(
    subject: str, body: str, cta_label: str = None, cta_url: str = None, *, tipo: str = "informativo"
) -> str:
    """Renderiza um comunicado no template ACCTA. Conteúdo escapado; \n\n →
    parágrafos, \n → <br>. CTA (Carmesim) só com label+url. Nota de opt-out
    apenas em comunicados informativos."""
    safe_subject = escape(subject, quote=True)
    paragraphs = ""
    for block in (body or "").split("\n\n"):
        block = block.strip()
        if not block:
            continue
        inner = escape(block, quote=True).replace("\n", "<br>")
        paragraphs += f'<p style="margin:0 0 14px;font-size:14px;color:#6b7280;line-height:1.7;">{inner}</p>'
    cta_block = ""
    resolved_cta = None
    if cta_label and cta_url:
        if cta_url.startswith("http://") or cta_url.startswith("https://"):
            resolved_cta = cta_url
        elif cta_url.startswith("/"):
            # CTA relativo (gatilhos F3, ex. /assembleias/{id}): no email tem de
            # ser absoluto. Resolve via FRONTEND_URL; sem base → sem botão.
            base = os.environ.get("FRONTEND_URL", "").rstrip("/")
            if base:
                resolved_cta = f"{base}{cta_url}"
        # caso contrário (ex.: javascript:) → resolved_cta None → sem botão
    if resolved_cta:
        safe_label = escape(cta_label, quote=True)
        safe_cta_url = escape(resolved_cta, quote=True)
        cta_block = (
            f'\n    <table cellpadding="0" cellspacing="0" width="100%"><tr><td align="center">'
            f'\n      <a href="{safe_cta_url}" style="display:inline-block;padding:12px 32px;'
            f"background-color:#C7202F;color:#ffffff;font-size:14px;font-weight:600;"
            f'text-decoration:none;border-radius:8px;">{safe_label}</a>'
            f"\n    </td></tr></table>"
        )
    optout_note = ""
    if tipo == "informativo":
        optout_note = (
            '<p style="margin:20px 0 0;font-size:12px;color:#6b7280;line-height:1.5;">'
            "Pode desactivar estes avisos informativos no seu perfil no Portal ACCTA.</p>"
        )
    content = f"""
    <h2 style="margin:0 0 16px;font-size:20px;color:#3A3A3A;">{safe_subject}</h2>
    {paragraphs}{cta_block}{optout_note}"""
    return _base_template(content)


async def send_comunicado_batch(recipients: list[str], subject: str, html: str) -> dict:
    """Envia o mesmo email a N destinatários — individualmente (sem To/CC
    partilhado). Usa Resend Batch quando disponível (chunks de 100), com
    fallback para envios individuais. Devolve {sent, failed, errors}."""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set. Comunicado a %d destinatarios nao enviado.", len(recipients))
        return {"sent": 0, "failed": len(recipients), "errors": ["resend_not_configured"]}

    sent = 0
    failed = 0
    errors: list = []
    use_batch = hasattr(resend, "Batch")
    for i in range(0, len(recipients), _BATCH_CHUNK_SIZE):
        chunk = recipients[i : i + _BATCH_CHUNK_SIZE]
        if use_batch:
            params = [
                {"from": f"{APP_NAME} <{SENDER_EMAIL}>", "to": [r], "subject": subject, "html": html} for r in chunk
            ]
            try:
                await asyncio.to_thread(resend.Batch.send, params)
                sent += len(chunk)
                continue
            except Exception as e:  # noqa: BLE001 — fallback per-recipient
                logger.error("Resend Batch falhou, fallback individual: %s", e)
        for r in chunk:
            res = await send_email(r, subject, html)
            if res.get("status") == "sent":
                sent += 1
            else:
                failed += 1
                errors.append(res.get("error", res.get("reason", "unknown")))
    return {"sent": sent, "failed": failed, "errors": errors[:20]}
