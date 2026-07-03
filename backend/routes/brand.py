"""Gestão da marca / logo do portal (spec-gestao-logo-marca §5).

Single-doc settings (molde finance_settings/banners). logo_*_url a None → o
frontend usa o SVG fallback (ACCTALogo) → portal idêntico ao atual antes de
qualquer upload. Escrita: admin + moderador. Audit em cada PATCH.

Semântica de "limpar": campo enviado como "" repõe o default (grava None);
campo ausente mantém o valor; uma URL substitui.
"""

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from auth import get_current_user, has_any_role
from database import db
from helpers import create_audit_log, delete_upload_file
from models import BrandSettings, BrandSettingsUpdate, User

router = APIRouter(prefix="/brand", tags=["brand"])

_DOC_ID = "brand_settings"
_DEFAULT_ALT = "ACCTA Cabo Verde"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_manager(current_user: User):
    if not has_any_role(current_user, "admin", "moderador"):
        raise HTTPException(status_code=403, detail="Sem permissão para gerir a marca")


async def _get_doc() -> dict:
    return await db.brand_settings.find_one({"id": _DOC_ID}, {"_id": 0}) or {}


def _public_view(doc: dict) -> dict:
    return {
        "logo_light_url": doc.get("logo_light_url"),
        "logo_dark_url": doc.get("logo_dark_url"),
        "favicon_url": doc.get("favicon_url"),
        "icon_url": doc.get("icon_url"),
        "alt": doc.get("alt") or _DEFAULT_ALT,
    }


@router.get("/public")
async def get_brand_public():
    """Público (sem auth): logos + favicon + ícone + alt; defaults (None) se vazio.
    Não grava nada durante a leitura."""
    return _public_view(await _get_doc())


@router.get("/icon")
async def get_brand_icon():
    """Público: URL estável do ícone quadrado da marca (PWA/og). Redireciona para o
    ícone carregado ou, na sua ausência, para o default estático do frontend. Permite
    que o manifest/og apontem para um URL fixo e o ícone troque pela UI sem novo deploy."""
    doc = await _get_doc()
    icon = doc.get("icon_url")
    if not icon:
        # Default = logo512 do frontend. FRONTEND_URL em prod; sem ele, evitar um
        # Location relativo (resolveria para o host do backend, onde o ficheiro não
        # existe) caindo no domínio público conhecido.
        base = os.environ.get("FRONTEND_URL", "").rstrip("/") or "https://controlador.cv"
        icon = f"{base}/logo512.png"
    return RedirectResponse(icon, status_code=302, headers={"Cache-Control": "public, max-age=3600"})


@router.get("")
async def get_brand(current_user: User = Depends(get_current_user)):
    _require_manager(current_user)
    doc = await _get_doc()
    return {**_public_view(doc), "updated_at": doc.get("updated_at"), "updated_by": doc.get("updated_by")}


@router.patch("")
async def update_brand(request: Request, data: BrandSettingsUpdate, current_user: User = Depends(get_current_user)):
    _require_manager(current_user)
    provided = data.model_dump(exclude_unset=True)
    if not provided:
        raise HTTPException(status_code=400, detail="Nenhuma alteração fornecida")

    existing = await _get_doc()
    url_fields = ("logo_light_url", "logo_dark_url", "favicon_url", "icon_url")
    set_fields: dict = {}
    for field in url_fields:
        if field in provided:
            # "" repõe default (None); URL substitui.
            set_fields[field] = provided[field] or None
    if "alt" in provided:
        set_fields["alt"] = provided["alt"] or _DEFAULT_ALT

    # Limpa ficheiros de upload próprios que deixem de estar referenciados.
    still_referenced = {
        set_fields.get(f, existing.get(f)) for f in url_fields if set_fields.get(f, existing.get(f))
    }
    for field in url_fields:
        if field in set_fields:
            old = existing.get(field)
            if old and old.startswith("/uploads/brand/") and old not in still_referenced:
                delete_upload_file(old)

    set_fields["updated_at"] = _now_iso()
    set_fields["updated_by"] = current_user.id

    if existing:
        await db.brand_settings.update_one({"id": _DOC_ID}, {"$set": set_fields})
    else:
        default = BrandSettings()
        d = default.model_dump()
        d.update(set_fields)
        d["id"] = _DOC_ID
        await db.brand_settings.insert_one(d)

    await create_audit_log(
        current_user.id,
        "brand_updated",
        _DOC_ID,
        request=request,
        details={k: set_fields.get(k) for k in (*url_fields, "alt") if k in set_fields},
    )
    return _public_view(await _get_doc())
