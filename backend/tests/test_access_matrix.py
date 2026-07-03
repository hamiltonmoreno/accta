"""Matriz de equivalência de acessos — spec 018 (R10).

BASELINE F1 capturada ANTES de qualquer alteração aos checks (T002) e provada
inalterada após a higiene (SC-005). Esta versão é a ATUALIZAÇÃO DELIBERADA da
F2 (T011): o `git diff` deste ficheiro entre a baseline e agora é a lista
exata das mudanças de acesso decididas (SC-001, revisável pelo dono):

1. Os roles legados financeiro/moderador DEIXAM de passar em qualquer gate —
   um doc que ainda os tenha (janela deploy→migração) fica como socio puro;
   o acesso vive nas funções seed (perfis seed_* abaixo) após a migração.
2. seed «Financeiro» = manage_finances + manage_users: preserva finanças e a
   listagem de utilizadores; ⚠ GANHA gestão de utilizadores e remoção de
   fotos (não existe privilégio só-de-listagem) — delta a validar pelo dono.
3. seed «Moderador» = moderate_content: preserva exatamente o acesso antigo —
   a remoção de fotos de perfil passou a aceitar também moderate_content
   (semanticamente é moderação de conteúdo).
4. Módulos que eram só-por-role ganharam o privilégio correspondente (posts/
   banners/brand → moderate_content; stats/atividade-financeira →
   manage_finances; PII de terceiros → manage_users) — fora da matriz, ver
   os testes dos módulos respetivos.

Os gates por CARGO (atos, eleições, assembleias — `permissions.is_*`) ficam
fora da matriz: não mudam na spec 018 e têm testes próprios.
"""

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

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
from governance import LEGACY_ROLE_SEEDS
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
    do módulo em teste; os restantes perfis são fixos. Os perfis financeiro/
    moderador representam docs LEGADOS ainda não migrados (janela) — negam
    tudo; os seed_* são o destino da migração (privilégios das seeds)."""
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
    if name == "seed_financeiro":
        return _user("socio", list(LEGACY_ROLE_SEEDS["financeiro"]["privileges"]))
    if name == "seed_moderador":
        return _user("socio", list(LEGACY_ROLE_SEEDS["moderador"]["privileges"]))
    raise AssertionError(f"perfil desconhecido: {name}")


PROFILES = [
    "admin",
    "financeiro",
    "moderador",
    "socio",
    "socio_priv",
    "readonly",
    "tecnico",
    "seed_financeiro",
    "seed_moderador",
]


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
        return await _route_gate(users_routes.admin_update_user("x", UserAdminUpdate(), None, current_user=user))
    if module == "users_photo_moderation":
        return await _route_gate(users_routes.remove_user_photo("x", None, current_user=user))
    if module == "events_manage":
        return _sync_gate(events_routes._require_manage_events, user)
    if module == "documents_restricted":
        return documents_routes.can_access_restricted_documents(user)
    if module == "benefits_manage":
        return await _route_gate(benefits_routes.delete_benefit("x", current_user=user))
    if module == "moderation_gallery":
        return await _route_gate(gallery_routes.update_gallery_album("x", GalleryAlbumUpdate(), current_user=user))
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
# A MATRIZ (modelo F2 — spec 018; diff vs baseline F1 = mudanças decididas)
# `priv` = privilégio relevante dado ao perfil socio_priv.
# `allow` = perfis que o gate deixa passar.
# --------------------------------------------------------------------------- #

MATRIX = {
    "finances_view": {
        "priv": "manage_finances",
        "allow": {"admin", "socio_priv", "readonly", "tecnico", "seed_financeiro"},
    },
    "finances_manage": {
        "priv": "manage_finances",
        "allow": {"admin", "socio_priv", "tecnico", "seed_financeiro"},
    },
    "users_list": {
        "priv": "manage_users",
        "allow": {"admin", "socio_priv", "tecnico", "seed_financeiro"},
    },
    "users_manage": {
        # ⚠ seed_financeiro passa por manage_users — GANHO vs role antigo
        # (financeiro só listava); delta assinalado ao dono (docstring §2).
        "priv": "manage_users",
        "allow": {"admin", "socio_priv", "tecnico", "seed_financeiro"},
    },
    "users_photo_moderation": {
        # F2: o gate aceita manage_users OU moderate_content (remoção de foto
        # é moderação de conteúdo) — preserva o acesso do antigo moderador.
        "priv": "manage_users",
        "allow": {"admin", "socio_priv", "tecnico", "seed_financeiro", "seed_moderador"},
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
        "allow": {"admin", "socio_priv", "tecnico", "seed_moderador"},
    },
    "moderation_wall": {
        "priv": "moderate_content",
        "allow": {"admin", "socio_priv", "tecnico", "seed_moderador"},
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

_CASES = [(module, profile, profile in spec["allow"]) for module, spec in MATRIX.items() for profile in PROFILES]


@pytest.mark.parametrize(
    ("module", "profile", "expected"),
    _CASES,
    ids=[f"{m}-{p}-{'allow' if e else 'deny'}" for m, p, e in _CASES],
)
async def test_access_matrix(mock_db, module, profile, expected):
    user = _profile(profile, MATRIX[module]["priv"])
    assert await _gate(module, user) is expected, (
        f"{module} × {profile}: esperado {'ALLOW' if expected else 'DENY'} "
        f"(matriz F2 — mudanças só via edição deliberada deste ficheiro)"
    )


# --------------------------------------------------------------------------- #
# Equivalência das seeds (SC-001): o acesso medido dos perfis seed_* vs o que
# os roles legados tinham na baseline F1 (financeiro = {finances_view,
# finances_manage, users_list}; moderador = {moderation_gallery,
# moderation_wall, users_photo_moderation}).
# --------------------------------------------------------------------------- #


async def _allowed_modules(mock_db_unused, user: User) -> set:
    return {m for m in MATRIX if await _gate(m, user)}


async def test_legacy_roles_grant_nothing(mock_db):
    """Docs com role legado (janela pré-migração) são socio puro nos gates."""
    assert await _allowed_modules(mock_db, _user("financeiro")) == set()
    assert await _allowed_modules(mock_db, _user("moderador")) == set()


async def test_seed_financeiro_equivalence(mock_db):
    """Seed «Financeiro» cobre TODO o acesso do antigo role (⊇ baseline).
    Delta assinalado: +users_manage e +users_photo_moderation vêm de
    manage_users (não existe privilégio só-de-listagem) — validação do dono."""
    allowed = await _allowed_modules(mock_db, _profile("seed_financeiro", ""))
    baseline = {"finances_view", "finances_manage", "users_list"}
    assert baseline <= allowed
    assert allowed - baseline == {"users_manage", "users_photo_moderation"}


async def test_seed_moderador_equivalence(mock_db):
    """Seed «Moderador» = exatamente o acesso do antigo role (equivalência exata)."""
    allowed = await _allowed_modules(mock_db, _profile("seed_moderador", ""))
    assert allowed == {"moderation_gallery", "moderation_wall", "users_photo_moderation"}


# --------------------------------------------------------------------------- #
# FR-008 (spec 018): nenhum route compara `user.role` diretamente — todos os
# checks de acesso passam pelos helpers (`auth.py`/`permissions.py`). Tripwire
# automatizado contra regressões; a matriz acima é o contrato de comportamento.
# --------------------------------------------------------------------------- #

# Casa `user.role`/`current_user.role` (e qualquer *_user.role) comparado com
# ==, !=, in ou not in. NÃO casa validação de input (ex.: `data.role not in`).
_INLINE_ROLE_CHECK = re.compile(r"user\.role\s*(?:==|!=|not\s+in\b|in\b)")


def test_no_inline_role_checks():
    routes_dir = Path(__file__).resolve().parent.parent / "routes"
    offenders = [
        f"{py.name}:{lineno}: {line.strip()}"
        for py in sorted(routes_dir.glob("*.py"))
        for lineno, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1)
        if _INLINE_ROLE_CHECK.search(line)
    ]
    assert not offenders, (
        "Checks de role inline fora dos helpers (spec 018, FR-008) — usar "
        "has_role_or_privilege/is_admin/module_gate de auth.py:\n" + "\n".join(offenders)
    )
