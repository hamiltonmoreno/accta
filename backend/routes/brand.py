"""Gestão da marca / logo do portal (spec-gestao-logo-marca §5).

Single-doc settings (molde finance_settings/banners). logo_*_url a None → o
frontend usa o SVG fallback (ACCTALogo) → portal idêntico ao atual antes de
qualquer upload. Escrita: admin + moderador. Audit em cada PATCH.

Semântica de "limpar": campo enviado como "" repõe o default (grava None);
campo ausente mantém o valor; uma URL substitui.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from auth import get_current_user
from database import db
from helpers import create_audit_log, delete_upload_file
from models import BrandSettings, BrandSettingsUpdate, User

router = APIRouter(prefix="/brand", tags=["brand"])

_DOC_ID = "brand_settings"
_DEFAULT_ALT = "ACCTA Cabo Verde"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_manager(current_user: User):
    if current_user.role not in ("admin", "moderador"):
        raise HTTPException(status_code=403, detail="Sem permissão para gerir a marca")


async def _get_doc() -> dict:
    return await db.brand_settings.find_one({"id": _DOC_ID}, {"_id": 0}) or {}


def _public_view(doc: dict) -> dict:
    return {
        "logo_light_url": doc.get("logo_light_url"),
        "logo_dark_url": doc.get("logo_dark_url"),
        "alt": doc.get("alt") or _DEFAULT_ALT,
    }


@router.get("/public")
async def get_brand_public():
    """Público (sem auth): logo light/dark + alt; defaults (None) se vazio.
    Não grava nada durante a leitura."""
    return _public_view(await _get_doc())


@router.get("")
async def get_brand(current_user: User = Depends(get_current_user)):
    _require_manager(current_user)
    doc = await _get_doc()
    return {**_public_view(doc), "updated_at": doc.get("updated_at"), "updated_by": doc.get("updated_by")}


@router.patch("")
async def update_brand(
    request: Request, data: BrandSettingsUpdate, current_user: User = Depends(get_current_user)
):
    _require_manager(current_user)
    provided = data.model_dump(exclude_unset=True)
    if not provided:
        raise HTTPException(status_code=400, detail="Nenhuma alteração fornecida")

    existing = await _get_doc()
    set_fields: dict = {}
    for field in ("logo_light_url", "logo_dark_url"):
        if field in provided:
            # "" repõe default (None); URL substitui.
            set_fields[field] = provided[field] or None
    if "alt" in provided:
        set_fields["alt"] = provided["alt"] or _DEFAULT_ALT

    # Limpa ficheiros de upload próprios que deixem de estar referenciados.
    new_light = set_fields.get("logo_light_url", existing.get("logo_light_url"))
    new_dark = set_fields.get("logo_dark_url", existing.get("logo_dark_url"))
    still_referenced = {u for u in (new_light, new_dark) if u}
    for field in ("logo_light_url", "logo_dark_url"):
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
        d["updated_at"] = d["updated_at"].isoformat() if hasattr(d["updated_at"], "isoformat") else d["updated_at"]
        d.update(set_fields)
        d["id"] = _DOC_ID
        await db.brand_settings.insert_one(d)

    await create_audit_log(
        current_user.id, "brand_updated", _DOC_ID, request=request,
        details={k: set_fields.get(k) for k in ("logo_light_url", "logo_dark_url", "alt") if k in set_fields},
    )
    return _public_view(await _get_doc())
