"""Matriz de equivalência de acessos — spec 018, F1 (R10).

BASELINE capturada ANTES de qualquer alteração aos checks (T002): cada célula
perfil × módulo afirma o comportamento do gate REAL no código atual. Esta
matriz é o contrato de equivalência de toda a spec 018:

- F1 (higiene): a matriz corre INALTERADA depois da unificação dos checks —
  prova de zero mudança de comportamento (SC-005).
- F2 (modelo): a matriz é atualizada DELIBERADAMENTE — o diff deste ficheiro
  é a lista exata das mudanças de acesso decididas (SC-001, revisável).

Os gates por CARGO (atos, eleições, assembleias — `permissions.is_*`) ficam
fora da matriz: não mudam na spec 018 e têm testes próprios.

Perfis: admin, financeiro, moderador, socio puro, socio+privilégio relevante
do módulo, socio+view_finances_readonly (Conselho Fiscal), conta técnica.
"""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

import routes.benefits as benefits_routes
import routes.comunicados as comunicados_routes
import routes.documents as documents_routes
import routes.events as events_routes
import routes.finances as finances_routes
import routes.gallery as gallery_routes
import routes.notifications as notifications_routes
import routes.ranking as ranking_routes
import routes.regulamentos as regulamentos_routes
import routes.users as users_routes
import routes.wall as wall_routes
from models import GalleryAlbumUpdate, User, UserAdminUpdate

pytestmark = pytest.mark.unit


# --------------------------------------------------------------------------- #
# Perfis
# --------------------------------------------------------------------------- #


def _user(role: str = "socio", privileges: list | None = None, **overrides) -> User:
    base = {
        "id": str(uuid.uuid4()),
        "name": f"Matriz {role}",
        "email": f"{role}-{uuid.uuid4().hex[:6]}@example.com",
        "role": role,
        "status": "ativo",
        "cargo": "Sócio",
        "privileges": privileges or [],
        "consent_data": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    base.update(overrides)
    return User(**base)


def _profile(name: str, module_priv: str) -> User:
    """Constrói o utilizador-perfil. `socio_priv` recebe o privilégio relevante
    do módulo em teste; os restantes perfis são fixos."""
    if name == "admin":
        return _user("admin")
    if name == "financeiro":
        return _user("financeiro")
    if name == "moderador":
        return _user("moderador")
    if name == "socio":
        return _user("socio")
    if name == "socio_priv":
        return _user("socio", [module_priv])
    if name == "readonly":
        return _user("socio", ["view_finances_readonly"])
    if name == "tecnico":
        # Conta técnica (ex.: admin@controlador.cv): a camada RBAC decide por
        # role/privileges e IGNORA account_type — facto documentado na matriz.
        return _user("admin", account_type="technical", member_id=None)
    raise AssertionError(f"perfil desconhecido: {name}")


PROFILES = ["admin", "financeiro", "moderador", "socio", "socio_priv", "readonly", "tecnico"]


# --------------------------------------------------------------------------- #
# Gates — um por módulo, chamando o código REAL (predicado ou rota).
# Para rotas, 403 = negado; qualquer outro resultado (sucesso, 404 pós-gate,
# 400) = o gate deixou passar.
# --------------------------------------------------------------------------- #


def _sync_gate(fn, user) -> bool:
    try:
        result = fn(user)
    except HTTPException as exc:
        return exc.status_code != 403
    return bool(result) if result is not None else True


async def _route_gate(coro) -> bool:
    try:
        await coro
    except HTTPException as exc:
        return exc.status_code != 403
    return True


async def _gate(module: str, user: User) -> bool:
    if module == "finances_view":
        return _sync_gate(finances_routes.require_view_finances, user)
    if module == "finances_manage":
        return _sync_gate(finances_routes.require_manage_finances, user)
    if module == "users_list":
        return await _route_gate(users_routes.get_users(current_user=user))
    if module == "users_manage":
        return await _route_gate(
            users_routes.admin_update_user("x", UserAdminUpdate(), None, current_user=user)
        )
    if module == "users_photo_moderation":
        return await _route_gate(users_routes.remove_user_photo("x", None, current_user=user))
    if module == "events_manage":
        return _sync_gate(events_routes._require_manage_events, user)
    if module == "documents_restricted":
        return documents_routes.can_access_restricted_documents(user)
    if module == "benefits_manage":
        return await _route_gate(benefits_routes.delete_benefit("x", current_user=user))
    if module == "moderation_gallery":
        return await _route_gate(
            gallery_routes.update_gallery_album("x", GalleryAlbumUpdate(), current_user=user)
        )
    if module == "moderation_wall":
        return await _route_gate(wall_routes.get_pending_wall_posts(current_user=user))
    if module == "comunicados_send":
        return comunicados_routes._is_full_sender(user)
    if module == "audit_view":
        return await _route_gate(notifications_routes.get_audit_logs(skip=0, limit=50, current_user=user))
    if module == "ranking_manage":
        return ranking_routes._can_manage_ranking(user)
    if module == "regulamentos_manage":
        return regulamentos_routes._can_manage(user)
    raise AssertionError(f"módulo desconhecido: {module}")


# --------------------------------------------------------------------------- #
# A MATRIZ (baseline 2026-07-03, código pré-F1)
# `priv` = privilégio relevante dado ao perfil socio_priv.
# `allow` = perfis que o gate deixa passar HOJE.
# --------------------------------------------------------------------------- #

MATRIX = {
    "finances_view": {
        "priv": "manage_finances",
        "allow": {"admin", "financeiro", "socio_priv", "readonly", "tecnico"},
    },
    "finances_manage": {
        "priv": "manage_finances",
        "allow": {"admin", "financeiro", "socio_priv", "tecnico"},
    },
    "users_list": {
        # users.py: o role financeiro passa na listagem de utilizadores.
        "priv": "manage_users",
        "allow": {"admin", "financeiro", "socio_priv", "tecnico"},
    },
    "users_manage": {
        "priv": "manage_users",
        "allow": {"admin", "socio_priv", "tecnico"},
    },
    "users_photo_moderation": {
        # users.py: gate assimétrico — roles (admin, moderador) mas privilégio
        # manage_users (não moderate_content). Input direto da seed «Moderador».
        "priv": "manage_users",
        "allow": {"admin", "moderador", "socio_priv", "tecnico"},
    },
    "events_manage": {
        "priv": "manage_events",
        "allow": {"admin", "socio_priv", "tecnico"},
    },
    "documents_restricted": {
        "priv": "manage_documents",
        "allow": {"admin", "socio_priv", "tecnico"},
    },
    "benefits_manage": {
        "priv": "manage_benefits",
        "allow": {"admin", "socio_priv", "tecnico"},
    },
    "moderation_gallery": {
        "priv": "moderate_content",
        "allow": {"admin", "moderador", "socio_priv", "tecnico"},
    },
    "moderation_wall": {
        "priv": "moderate_content",
        "allow": {"admin", "moderador", "socio_priv", "tecnico"},
    },
    "comunicados_send": {
        "priv": "send_comunicados",
        "allow": {"admin", "socio_priv", "tecnico"},
    },
    "audit_view": {
        "priv": "view_audit_logs",
        "allow": {"admin", "socio_priv", "tecnico"},
    },
    "ranking_manage": {
        "priv": "manage_ranking",
        "allow": {"admin", "socio_priv", "tecnico"},
    },
    "regulamentos_manage": {
        "priv": "manage_documents",
        "allow": {"admin", "socio_priv", "tecnico"},
    },
}

_CASES = [
    (module, profile, profile in spec["allow"])
    for module, spec in MATRIX.items()
    for profile in PROFILES
]


@pytest.mark.parametrize(
    ("module", "profile", "expected"),
    _CASES,
    ids=[f"{m}-{p}-{'allow' if e else 'deny'}" for m, p, e in _CASES],
)
async def test_access_matrix(mock_db, module, profile, expected):
    user = _profile(profile, MATRIX[module]["priv"])
    assert await _gate(module, user) is expected, (
        f"{module} × {profile}: esperado {'ALLOW' if expected else 'DENY'} "
        f"(baseline pré-F1 — se isto mudou, a equivalência quebrou)"
    )


# --------------------------------------------------------------------------- #
# Derivação das seeds F2 (R4): o acesso REAL dos roles financeiro/moderador,
# medido nos gates — não intuído dos labels. É daqui que saem os privilégios
# das funções seed «Financeiro»/«Moderador» na migração.
# --------------------------------------------------------------------------- #


async def _allowed_modules(mock_db_unused, user: User) -> set:
    return {m for m in MATRIX if await _gate(m, user)}


async def test_role_financeiro_measured_access(mock_db):
    """O role financeiro passa HOJE em exatamente estes módulos."""
    allowed = await _allowed_modules(mock_db, _user("financeiro"))
    assert allowed == {"finances_view", "finances_manage", "users_list"}


async def test_role_moderador_measured_access(mock_db):
    """O role moderador passa HOJE em exatamente estes módulos."""
    allowed = await _allowed_modules(mock_db, _user("moderador"))
    assert allowed == {"moderation_gallery", "moderation_wall", "users_photo_moderation"}
