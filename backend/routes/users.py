from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Optional
import re
from models import (
    User,
    UserProfileUpdate,
    UserAdminUpdate,
    CARGOS,
    CARGOS_ORGAOS_SOCIAIS,
    CARGO_DEFAULTS,
    CARGO_SEATS,
    MFA_SECRET_FIELDS,
    PRIVILEGES,
    USER_STATUSES,
)
from governance import (
    CARGO_KEYS,
    normalize_cargo,
    orgao_of_cargo,
)
from database import db
from auth import get_current_user, has_role_or_privilege
from helpers import create_audit_log, create_notification, delete_upload_file

router = APIRouter(tags=["users"])


# PII sensível do perfil (feature/perfil): dados pessoais/saúde/morada/contacto
# de emergência que NÃO devem sair em listagens nem para terceiros (staff).
# Só o próprio (via /auth/me ou GET /users/{self}) os recebe — minimização de
# dados. Excluídos da listagem em massa e das leituras por terceiros.
SENSITIVE_PROFILE_FIELDS = [
    "blood_type",
    "nif",
    "date_of_birth",
    "address",
    "postal_code",
    "city",
    "emergency_contact_name",
    "emergency_contact_phone",
    "emergency_contact_relationship",
]


def _user_projection(include_sensitive: bool) -> dict:
    """Projeção base (sem _id/password); oculta a PII sensível salvo para o próprio."""
    proj = {"_id": 0, "password": 0, **dict.fromkeys(MFA_SECRET_FIELDS, 0)}
    if not include_sensitive:
        proj.update({f: 0 for f in SENSITIVE_PROFILE_FIELDS})
    return proj


# ===== LIST USERS =====
@router.get("/users", response_model=List[User])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    cargo: Optional[str] = None,
    include_technical: bool = False,
    current_user: User = Depends(get_current_user),
):
    if not has_role_or_privilege(current_user, ("admin", "financeiro"), "manage_users"):
        raise HTTPException(status_code=403, detail="Sem permissão")

    query = {}
    # `$and` acumula os dois `$or` possíveis (pesquisa + filtro account_type)
    # sem colisão de chaves (um dict só pode ter um `$or`).
    and_clauses = []
    if search:
        # Truncar ANTES de escape — re.escape pode duplicar bytes (ex: '*' -> '\\*')
        # e cortar a meio uma sequencia escapada deixaria backslash final = regex
        # invalido. Cap input bruto a 100 chars (ReDoS guard) + escape.
        safe = re.escape(search.strip()[:100])
        and_clauses.append(
            {
                "$or": [
                    {"name": {"$regex": safe, "$options": "i"}},
                    {"email": {"$regex": safe, "$options": "i"}},
                    {"member_id": {"$regex": safe, "$options": "i"}},
                ]
            }
        )
    if role:
        query["role"] = role
    if status:
        query["status"] = status
    if cargo:
        query["cargo"] = cargo
    # Por defeito oculta contas técnicas (spec-identidade-cargos). Retro-compat:
    # documentos sem account_type tratam-se como "member".
    if not include_technical:
        and_clauses.append({"$or": [{"account_type": "member"}, {"account_type": {"$exists": False}}]})
    if and_clauses:
        query["$and"] = and_clauses

    limit = min(limit, 100)
    # Listagem em massa nunca expõe PII sensível (saúde/morada/contacto de emergência).
    users = await db.users.find(query, _user_projection(include_sensitive=False)).skip(skip).limit(limit).to_list(limit)
    return users


# ===== GET SINGLE USER =====
@router.get("/users/{user_id}")
async def get_user(user_id: str, current_user: User = Depends(get_current_user)):
    # Self ou staff (admin/financeiro) — restantes não veem PII de terceiros
    is_self = current_user.id == user_id
    is_staff = current_user.role in ("admin", "financeiro")
    if not (is_self or is_staff):
        raise HTTPException(status_code=403, detail="Sem permissão")

    # Só o próprio vê a PII sensível; staff a ver terceiros recebe a vista reduzida.
    user_doc = await db.users.find_one({"id": user_id}, _user_projection(include_sensitive=is_self))
    if not user_doc:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    return user_doc


# ===== UPDATE OWN PROFILE =====
@router.patch("/users/me/profile")
async def update_own_profile(data: UserProfileUpdate, current_user: User = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    await db.users.update_one({"id": current_user.id}, {"$set": update_data})

    # Return updated user
    updated = await db.users.find_one(
        {"id": current_user.id}, {"_id": 0, "password": 0, **dict.fromkeys(MFA_SECRET_FIELDS, 0)}
    )
    await create_audit_log(current_user.id, "Atualizou o próprio perfil")
    return updated


# ===== ADMIN UPDATE USER =====
@router.patch("/users/{user_id}")
async def admin_update_user(
    user_id: str,
    data: UserAdminUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    if not has_role_or_privilege(current_user, ("admin",), "manage_users"):
        raise HTTPException(status_code=403, detail="Apenas administradores podem editar utilizadores")

    existing = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    # Validate cargo: aceita key/label/alias legado, grava sempre a key canónica
    # e denormaliza o órgão social (spec-governanca §4).
    if "cargo" in update_data:
        cargo_key = normalize_cargo(update_data["cargo"])
        if cargo_key not in CARGO_KEYS:
            raise HTTPException(status_code=400, detail=f"Cargo inválido. Opções: {', '.join(CARGOS)}")
        update_data["cargo"] = cargo_key
        update_data["orgao"] = orgao_of_cargo(cargo_key)

    # Validate privileges
    if "privileges" in update_data:
        invalid = [p for p in update_data["privileges"] if p not in PRIVILEGES]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Privilégios inválidos: {', '.join(invalid)}")

    # Validate role
    valid_roles = ["admin", "socio", "financeiro", "moderador"]
    if "role" in update_data and update_data["role"] not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Role inválido. Opções: {', '.join(valid_roles)}")

    # Validate status (invariante: sem "inadimplente")
    if "status" in update_data and update_data["status"] not in USER_STATUSES:
        raise HTTPException(status_code=400, detail=f"Status inválido. Opções: {', '.join(USER_STATUSES)}")

    await db.users.update_one({"id": user_id}, {"$set": update_data})

    # Audit log estruturado: details captura before/after dos campos sensiveis (role/status/privileges).
    sensitive = {"role", "status", "privileges"}
    before = {k: existing.get(k) for k in update_data if k in sensitive}
    after = {k: v for k, v in update_data.items() if k in sensitive}
    await create_audit_log(
        current_user.id,
        "user_updated",
        user_id,
        request=request,
        details={
            "target_name": existing.get("name"),
            "changes": list(update_data.keys()),
            "before": before or None,
            "after": after or None,
        },
    )

    # Notify user of role/cargo changes
    notify_fields = {"role", "privileges", "status"}
    if notify_fields & set(update_data.keys()):
        await create_notification(
            user_id,
            "profile_updated",
            "Perfil Atualizado",
            "O seu perfil foi atualizado por um administrador. Verifique as alterações.",
            "/perfil",
        )

    updated = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0, **dict.fromkeys(MFA_SECRET_FIELDS, 0)})
    return updated


# ===== UPDATE USER STATUS (legacy, kept for backwards compat) =====
@router.patch("/users/{user_id}/status")
async def update_user_status(user_id: str, status: str, current_user: User = Depends(get_current_user)):
    if not has_role_or_privilege(current_user, ("admin",), "manage_users"):
        raise HTTPException(status_code=403, detail="Sem permissão")

    if status not in USER_STATUSES:
        raise HTTPException(status_code=400, detail=f"Status inválido. Opções: {', '.join(USER_STATUSES)}")

    await db.users.update_one({"id": user_id}, {"$set": {"status": status}})
    await create_audit_log(current_user.id, "user_status_updated", user_id, details={"status": status})
    return {"message": "Status atualizado"}


# ===== DELETE USER =====
@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    if not has_role_or_privilege(current_user, ("admin",), "manage_users"):
        raise HTTPException(status_code=403, detail="Apenas administradores podem remover utilizadores")

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Não pode remover a própria conta")

    existing = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")

    await db.users.delete_one({"id": user_id})
    # Avatar fica órfão no disco se não for removido com o utilizador.
    delete_upload_file(existing.get("photo_url") or "")
    await create_audit_log(current_user.id, f"Removeu utilizador {existing.get('name', user_id)}", user_id)
    return {"message": "Utilizador removido com sucesso"}


# ===== CARGO HISTORY =====
@router.get("/users/{user_id}/cargo-history")
async def get_cargo_history(user_id: str, current_user: User = Depends(get_current_user)):
    """Histórico de mandatos de um sócio (ordenado descendente). Próprio ou admin/manage_users."""
    is_self = current_user.id == user_id
    if not (is_self or has_role_or_privilege(current_user, ("admin",), "manage_users")):
        raise HTTPException(status_code=403, detail="Sem permissão")

    user = await db.users.find_one({"id": user_id}, {"_id": 0, "cargo_history": 1, "name": 1})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")

    history = user.get("cargo_history") or []
    # Mandato mais recente primeiro (por data de início ISO-8601).
    history = sorted(history, key=lambda m: m.get("inicio") or "", reverse=True)
    return {"cargo_history": history}


# ===== SANÇÕES DO MEMBRO (spec-governanca §13) =====
@router.get("/users/{user_id}/sancoes")
async def get_user_sancoes(user_id: str, current_user: User = Depends(get_current_user)):
    """Sanções de um membro. O próprio vê (forma redigida); Direcção/admin tudo.
    Dados disciplinares são sensíveis — ocultados a quem não tem permissão."""
    from permissions import is_direcao
    from routes.sancoes import _redact

    is_self = current_user.id == user_id
    privileged = current_user.role == "admin" or is_direcao(current_user)
    if not (is_self or privileged):
        raise HTTPException(status_code=403, detail="Sem permissão")
    rows = await db.sancoes.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(200)
    if not privileged:
        rows = [_redact(r) for r in rows]
    return {"sancoes": rows}


# ===== METADATA ENDPOINTS (DEPRECATED — usar GET /api/governance/structure) =====
@router.get("/users/meta/cargos")
async def get_cargos():
    """[DEPRECATED] Alias temporário de compatibilidade. A fonte canónica é
    GET /api/governance/structure (spec-governanca §9). Mantém o shape legado
    para clientes ainda não migrados; cargos/defaults usam keys canónicas."""
    return {
        "cargos": CARGOS,
        "cargos_orgaos_sociais": CARGOS_ORGAOS_SOCIAIS,
        "privileges": PRIVILEGES,
        "cargo_defaults": CARGO_DEFAULTS,
        "cargo_seats": CARGO_SEATS,
        "deprecated": True,
        "structure_endpoint": "/api/governance/structure",
    }


@router.get("/users/meta/privileges")
async def get_privileges():
    """[DEPRECATED] Ver GET /api/governance/structure."""
    return {"privileges": PRIVILEGES, "deprecated": True, "structure_endpoint": "/api/governance/structure"}
