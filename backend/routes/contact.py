from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from email_service import send_email, _base_template
import os

router = APIRouter(tags=["contact"])

CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "secretariado@controlador.cv")


class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str = "geral"
    message: str


def _contact_email_html(name: str, email: str, subject: str, message: str) -> str:
    subject_labels = {
        "geral": "Geral",
        "imprensa": "Imprensa",
        "parcerias": "Parcerias",
        "duvidas": "Dúvidas",
    }
    subject_label = subject_labels.get(subject, subject.capitalize())

    content = f"""
    <h2 style="margin:0 0 8px;font-size:20px;color:#3A3A3A;">Nova mensagem via formulário de contacto</h2>
    <p style="margin:0 0 20px;font-size:14px;color:#6b7280;line-height:1.6;">
      Recebeu uma nova mensagem através do formulário de contacto do Portal ACCTA.
    </p>
    <table cellpadding="0" cellspacing="0" width="100%" style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">
      <tr><td style="padding:12px 16px;background:#f9fafb;border-bottom:1px solid #e5e7eb;">
        <span style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;">Nome</span>
        <p style="margin:4px 0 0;font-size:14px;color:#3A3A3A;font-weight:600;">{name}</p>
      </td></tr>
      <tr><td style="padding:12px 16px;background:#ffffff;border-bottom:1px solid #e5e7eb;">
        <span style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;">Email</span>
        <p style="margin:4px 0 0;font-size:14px;color:#C7202F;">{email}</p>
      </td></tr>
      <tr><td style="padding:12px 16px;background:#f9fafb;border-bottom:1px solid #e5e7eb;">
        <span style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;">Assunto</span>
        <p style="margin:4px 0 0;font-size:14px;color:#3A3A3A;">{subject_label}</p>
      </td></tr>
      <tr><td style="padding:12px 16px;background:#ffffff;">
        <span style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;">Mensagem</span>
        <p style="margin:8px 0 0;font-size:14px;color:#3A3A3A;line-height:1.7;white-space:pre-wrap;">{message}</p>
      </td></tr>
    </table>
    <p style="margin:20px 0 0;font-size:12px;color:#9ca3af;">
      Responda directamente para <a href="mailto:{email}" style="color:#C7202F;">{email}</a>
    </p>"""
    return _base_template(content)


@router.post("/contact")
async def submit_contact(data: ContactRequest):
    if len(data.message.strip()) < 10:
        raise HTTPException(status_code=400, detail="Mensagem demasiado curta")

    html = _contact_email_html(data.name, data.email, data.subject, data.message)
    result = await send_email(
        to=CONTACT_EMAIL,
        subject=f"[Contacto ACCTA] {data.subject.capitalize()} — {data.name}",
        html=html,
    )

    if result.get("status") == "failed":
        raise HTTPException(status_code=500, detail="Erro ao enviar mensagem. Tente novamente.")

    return {"message": "Mensagem enviada com sucesso"}
