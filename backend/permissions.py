"""Helpers de RBAC e elegibilidade para governança (spec-governanca §8).

Camada fina sobre `governance.py` que aceita objectos `User` (Pydantic) ou
dicts. Os checks de órgão derivam SEMPRE do cargo via `normalize_cargo` —
nunca confiam no campo denormalizado `orgao` (que é só para filtros/relatório).

RBAC aditivo (`role OR privilege`) é a mesma semântica de `auth.has_privilege`.
"""

from __future__ import annotations

from typing import Optional

from governance import (
    ASSEMBLEIA_GERAL,
    CONSELHO_FISCAL,
    DIRECAO,
    is_eligible_for_office as _is_eligible_doc,
    is_voting_member as _is_voting_member_doc,
    normalize_cargo,
    orgao_of_cargo,
)


def _attr(user, name, default=None):
    if isinstance(user, dict):
        return user.get(name, default)
    return getattr(user, name, default)


def _as_doc(user) -> dict:
    """Normaliza um User Pydantic (ou dict) para o dict que governance espera."""
    if isinstance(user, dict):
        return user
    if hasattr(user, "model_dump"):
        return user.model_dump()
    return {
        "account_type": _attr(user, "account_type"),
        "status": _attr(user, "status"),
        "member_category": _attr(user, "member_category"),
        "rights_suspended_until": _attr(user, "rights_suspended_until"),
        "cargo": _attr(user, "cargo"),
    }


def _cargo_key(user) -> str:
    return normalize_cargo(_attr(user, "cargo") or "")


# --------------------------------------------------------------------------- #
# RBAC
# --------------------------------------------------------------------------- #


def user_can(user, privilege: str) -> bool:
    """admin OU detentor do privilégio granular (RBAC aditivo)."""
    return _attr(user, "role") == "admin" or privilege in (_attr(user, "privileges") or [])


def is_mesa_ag(user) -> bool:
    """Titular da Mesa da Assembleia Geral (qualquer cargo `ag_*`)."""
    return _cargo_key(user).startswith("ag_")


def is_direcao(user) -> bool:
    return orgao_of_cargo(_cargo_key(user)) == DIRECAO


def is_conselho_fiscal(user) -> bool:
    return orgao_of_cargo(_cargo_key(user)) == CONSELHO_FISCAL


def is_presidente(user) -> bool:
    return _cargo_key(user) == "dir_presidente"


def is_tesoureiro(user) -> bool:
    return _cargo_key(user) == "dir_tesoureiro"


def is_assembleia_geral(user) -> bool:
    """Pertence à Mesa da AG (alias semântico para o órgão AG)."""
    return orgao_of_cargo(_cargo_key(user)) == ASSEMBLEIA_GERAL


def can_convene_assembleia(user) -> bool:
    """Pode convocar/gerir assembleias: Mesa da AG ou admin (spec §11)."""
    return _attr(user, "role") == "admin" or is_mesa_ag(user)


def can_emit_parecer_cf(user) -> bool:
    """Emitir parecer do CF / auditar balancetes: Conselho Fiscal (por cargo)
    OU detentor do privilégio `emit_cf_parecer` (spec-ciclo §3.3). Distinto de
    `manage_finances` — o CF audita mas NÃO escreve transacções (separação de
    poderes). `user_can` já inclui o admin."""
    return is_conselho_fiscal(user) or user_can(user, "emit_cf_parecer")


# --------------------------------------------------------------------------- #
# Elegibilidade / voto (delegam para governance, aceitando User Pydantic)
# --------------------------------------------------------------------------- #


def is_voting_member(user, as_of: Optional[str] = None) -> bool:
    return _is_voting_member_doc(_as_doc(user), as_of)


def is_eligible_for_office(user, as_of: Optional[str] = None) -> bool:
    return _is_eligible_doc(_as_doc(user), as_of)
