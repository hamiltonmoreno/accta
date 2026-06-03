"""Banners das páginas públicas (spec-padronizacao-banners §5).

Molde single-doc por chave (como finance_settings): 1 doc por banner em
`page_banners`. `GET /banners/public` funde os defaults embebidos (Unsplash
atuais) com os docs gravados — antes de qualquer upload o site fica idêntico
(rollout não-destrutivo §9). Escrita: admin + moderador (D1). Audit em cada PUT.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from auth import get_current_user
from database import db
from helpers import create_audit_log, delete_upload_file
from models import PageBannerUpdate, User

router = APIRouter(prefix="/banners", tags=["banners"])

_UNSPLASH = "https://images.unsplash.com/photo-{}?q=80&w=1600&auto=format&fit=crop"

# Defaults embebidos = imagens Unsplash hoje hardcoded nas páginas (§9). 10 chaves.
BANNER_DEFAULTS: dict[str, str] = {
    "home": _UNSPLASH.format("1436491865332-7a61a109cc05"),
    "sobre": _UNSPLASH.format("1522071820081-009f0129c71c"),
    "profissao": _UNSPLASH.format("1540962351504-03099e0a754b"),
    "contactos": _UNSPLASH.format("1672856181212-b5b5a0065a08"),
    "beneficios": _UNSPLASH.format("1600880292203-757bb62b4baf"),
    "transparencia": _UNSPLASH.format("1618506060789-b63788b0cecd"),
    "galeria": _UNSPLASH.format("1436491865332-7a61a109cc05"),
    "eventos": _UNSPLASH.format("1474302770737-173ee21bab63"),
    "noticias": _UNSPLASH.format("1618506060789-b63788b0cecd"),
    "validador": _UNSPLASH.format("1540962351504-03099e0a754b"),
}
BANNER_KEYS: list[str] = list(BANNER_DEFAULTS)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_manager(current_user: User):
    if current_user.role not in ("admin", "moderador"):
        raise HTTPException(status_code=403, detail="Sem permissão para gerir banners")


async def _stored() -> dict[str, dict]:
    rows = await db.page_banners.find({}, {"_id": 0}).to_list(None)
    return {r["key"]: r for r in rows if r.get("key")}


@router.get("/public")
async def get_banners_public():
    """Público (sem auth): { key: {image_url, alt} } para todas as chaves,
    defaults fundidos com os docs gravados."""
    stored = await _stored()
    out = {}
    for k in BANNER_KEYS:
        doc = stored.get(k) or {}
        out[k] = {"image_url": doc.get("image_url") or BANNER_DEFAULTS[k], "alt": doc.get("alt")}
    return out


@router.get("")
async def get_banners(current_user: User = Depends(get_current_user)):
    """Gestão (admin/moderador): inclui metadados e flag is_default."""
    _require_manager(current_user)
    stored = await _stored()
    out = {}
    for k in BANNER_KEYS:
        doc = stored.get(k) or {}
        out[k] = {
            "image_url": doc.get("image_url") or BANNER_DEFAULTS[k],
            "alt": doc.get("alt"),
            "is_default": not doc.get("image_url"),
            "is_home": k == "home",
            "updated_at": doc.get("updated_at"),
            "updated_by": doc.get("updated_by"),
        }
    return {"banners": out, "keys": BANNER_KEYS}


@router.put("/{key}")
async def update_banner(
    key: str, request: Request, data: PageBannerUpdate, current_user: User = Depends(get_current_user)
):
    """Upsert da imagem/alt de uma chave. Limpa a imagem anterior se for um
    upload local substituído (§Q2)."""
    _require_manager(current_user)
    if key not in BANNER_KEYS:
        raise HTTPException(status_code=400, detail=f"Banner inválido: {key}")

    existing = await db.page_banners.find_one({"key": key}, {"_id": 0})
    set_fields = {"key": key, "updated_at": _now_iso(), "updated_by": current_user.id}
    if data.image_url is not None:
        set_fields["image_url"] = data.image_url
    if data.alt is not None:
        set_fields["alt"] = data.alt

    if existing:
        old = existing.get("image_url")
        # Limpa o ficheiro anterior se foi um upload local e está a ser trocado.
        if data.image_url and old and old != data.image_url and old.startswith("/uploads/banners/"):
            delete_upload_file(old)
        await db.page_banners.update_one({"key": key}, {"$set": set_fields})
    else:
        set_fields.setdefault("image_url", data.image_url or BANNER_DEFAULTS[key])
        await db.page_banners.insert_one(set_fields)

    await create_audit_log(
        current_user.id, "banner_updated", key, request=request,
        details={"image_url": set_fields.get("image_url"), "alt": set_fields.get("alt")},
    )
    return {"message": "Banner atualizado.", "key": key, "image_url": set_fields.get("image_url"), "alt": set_fields.get("alt")}
