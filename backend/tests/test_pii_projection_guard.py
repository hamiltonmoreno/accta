"""PII sensível de terceiros não vaza fora de users.py — spec 019, G4/FR-005 (T053).

Levantamento (2026-07): TODAS as projeções de utilizador voltadas a terceiros /
agregações — ranking (`id/name/member_id/cargo/photo_url/status`), `_VOTER_PROJ`
(assembleias), `_MEMBER_PROJECTION` (comunicados), notify helpers (`id`-only),
listagens admin (allowlist) — EXCLUEM os SENSITIVE_PROFILE_FIELDS. O único sítio
que os devolve é `users.py` via `_user_projection(include_sensitive=True)`, e só
ao próprio. **Superfície = nula → aceite** (research.md, M-PII/G4).

Guarda de regressão: nenhum ficheiro fora de `users.py` inclui um campo sensível
numa projeção (`"nif": 1`) — apanha uma agregação futura que passe a devolvê-lo.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from routes.users import SENSITIVE_PROFILE_FIELDS

pytestmark = pytest.mark.unit

BACKEND = Path(__file__).resolve().parent.parent
# "city" é omitido do guard: é um termo genérico (moradas de eventos/parceiros) que
# daria falsos positivos fora do contexto de utilizador. Os campos inequivocamente
# de PII de utilizador bastam para travar a regressão.
_GUARDED = [f for f in SENSITIVE_PROFILE_FIELDS if f != "city"]
_SENSITIVE_INCLUSION = re.compile(rf'"(?:{"|".join(map(re.escape, _GUARDED))})"\s*:\s*1\b')


def test_no_sensitive_pii_projection_outside_users():
    scan = sorted((BACKEND / "routes").glob("*.py")) + [
        BACKEND / "ranking.py",
        BACKEND / "comunicados_service.py",
        BACKEND / "helpers.py",
    ]
    offenders = [
        f"{f.name}:{lineno}: {line.strip()}"
        for f in scan
        if f.name != "users.py"
        for lineno, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1)
        if _SENSITIVE_INCLUSION.search(line)
    ]
    assert not offenders, (
        "PII sensível incluída numa projeção fora de users.py (FR-005) — usar allowlist "
        "sem estes campos ou gate self-only:\n" + "\n".join(offenders)
    )


def test_pii_guard_self_check():
    assert _SENSITIVE_INCLUSION.search('{"_id": 0, "nif": 1, "name": 1}')
    assert _SENSITIVE_INCLUSION.search('{"emergency_contact_phone": 1}')
    assert not _SENSITIVE_INCLUSION.search('{"_id": 0, "name": 1, "member_id": 1, "cargo": 1}')
