from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address
from email_service import send_email, _base_template
from turnstile import verify_turnstile
from html import escape
import os

router = APIRouter(tags=["contact"])
limiter = Limiter(key_func=get_remote_address)

CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "secretariado@controlador.cv")


def _email_header_text(value: str) -> str:
    return " ".join(str(value).splitlines()).strip()


class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str = "geral"
    message: str
    turnstile_token: str = ""  # token Cloudflare Turnstile (anti-bot); validado na rota


def _contact_email_html(name: str, email: str, subject: str, message: str) -> str:
    subject_labels = {
        "geral": "Geral",
        "imprensa": "Imprensa",
        "parcerias": "Parcerias",
        "duvidas": "Dúvidas",
    }
    safe_name = escape(name, quote=True)
    safe_email = escape(str(email), quote=True)
    safe_message = escape(message, quote=True)
    subject_label = escape(subject_labels.get(subject, subject.capitalize()), quote=True)

    content = f"""
    <h2 style="margin:0 0 8px;font-size:20px;color:#3A3A3A;">Nova mensagem via formulário de contacto</h2>
    <p style="margin:0 0 20px;font-size:14px;color:#6b7280;line-height:1.6;">
      Recebeu uma nova mensagem através do formulário de contacto do Portal ACCTA.
    </p>
    <table cellpadding="0" cellspacing="0" width="100%" style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">
      <tr><td style="padding:12px 16px;background:#f9fafb;border-bottom:1px solid #e5e7eb;">
        <span style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;">Nome</span>
        <p style="margin:4px 0 0;font-size:14px;color:#3A3A3A;font-weight:600;">{safe_name}</p>
      </td></tr>
      <tr><td style="padding:12px 16px;background:#ffffff;border-bottom:1px solid #e5e7eb;">
        <span style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;">Email</span>
        <p style="margin:4px 0 0;font-size:14px;color:#C7202F;">{safe_email}</p>
      </td></tr>
      <tr><td style="padding:12px 16px;background:#f9fafb;border-bottom:1px solid #e5e7eb;">
        <span style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;">Assunto</span>
        <p style="margin:4px 0 0;font-size:14px;color:#3A3A3A;">{subject_label}</p>
      </td></tr>
      <tr><td style="padding:12px 16px;background:#ffffff;">
        <span style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;">Mensagem</span>
        <p style="margin:8px 0 0;font-size:14px;color:#3A3A3A;line-height:1.7;white-space:pre-wrap;">{safe_message}</p>
      </td></tr>
    </table>
    <p style="margin:20px 0 0;font-size:12px;color:#9ca3af;">
      Responda directamente para <a href="mailto:{safe_email}" style="color:#C7202F;">{safe_email}</a>
    </p>"""
    return _base_template(content)


@router.post("/contact")
@limiter.limit("5/minute")
@limiter.limit("20/day")  # tecto diário por IP — trava spam lento ao CONTACT_EMAIL
async def submit_contact(request: Request, data: ContactRequest):
    # Anti-bot Turnstile primeiro. No-op se a feature estiver desligada.
    await verify_turnstile(data.turnstile_token, request)
    if len(data.message.strip()) < 10:
        raise HTTPException(status_code=400, detail="Mensagem demasiado curta")

    html = _contact_email_html(data.name, data.email, data.subject, data.message)
    result = await send_email(
        to=CONTACT_EMAIL,
        subject=f"[Contacto ACCTA] {_email_header_text(data.subject.capitalize())} - {_email_header_text(data.name)}",
        html=html,
    )

    if result.get("status") == "failed":
        raise HTTPException(status_code=500, detail="Erro ao enviar mensagem. Tente novamente.")

    return {"message": "Mensagem enviada com sucesso"}
