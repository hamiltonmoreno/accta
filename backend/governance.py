"""Núcleo de governança estatutária da ACCTA (spec-governanca-estatutaria.md).

Fonte ÚNICA de verdade para órgãos sociais, cargos, categorias de membro,
privilégios, roles, mandatos e regras de quórum/maioria/eleição.

`models.py` re-exporta as constantes daqui para preservar imports e testes
existentes. Este módulo NÃO importa de `models` (evita ciclo) — só stdlib.

Cargos são persistidos pela **key canónica** (`dir_tesoureiro`), nunca pelo
label (`Tesoureiro`). Labels existem só para a UI. Os endpoints aceitam key,
label canónico ou alias legado, mas gravam sempre a key (`normalize_cargo`).
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional

# --------------------------------------------------------------------------- #
# Órgãos sociais (Estatutos arts. 16-18, 27, 35)
# --------------------------------------------------------------------------- #

ASSEMBLEIA_GERAL = "assembleia_geral"
DIRECAO = "direcao"
CONSELHO_FISCAL = "conselho_fiscal"

ORGAOS: dict[str, dict] = {
    ASSEMBLEIA_GERAL: {
        "id": ASSEMBLEIA_GERAL,
        "nome": "Assembleia Geral",
        "tipo": "deliberativo",
        "tem_mesa": True,
        "mandato_anos": 3,
        "suplentes": 1,
        "slot_prefix": "ag",
        "artigos": ["16", "17", "18"],
    },
    DIRECAO: {
        "id": DIRECAO,
        "nome": "Direcção",
        "tipo": "executivo",
        "tem_mesa": False,
        "mandato_anos": 3,
        "suplentes": 2,
        "slot_prefix": "dir",
        "artigos": ["16", "27"],
    },
    CONSELHO_FISCAL: {
        "id": CONSELHO_FISCAL,
        "nome": "Conselho Fiscal",
        "tipo": "fiscalizacao",
        "tem_mesa": False,
        "mandato_anos": 3,
        "suplentes": 1,
        "slot_prefix": "cf",
        "artigos": ["16", "35"],
    },
}

# --------------------------------------------------------------------------- #
# Catálogo de cargos estatutários (spec §5.1)
# --------------------------------------------------------------------------- #
# `privileges = "ALL"` expande para a lista completa em `privileges_for_cargo`.
# `seats`: dir_vogal = 3 (1 base + até 2 fora da sede); socio = 0 (sem limite).

CARGOS_CATALOG: list[dict] = [
    {"key": "ag_presidente", "label": "Presidente da Mesa da AG",
     "orgao": ASSEMBLEIA_GERAL, "ordem": 1, "seats": 1,
     "role": "socio", "privileges": ["manage_events"]},
    {"key": "ag_vice_presidente", "label": "Vice-Presidente da Mesa da AG",
     "orgao": ASSEMBLEIA_GERAL, "ordem": 2, "seats": 1,
     "role": "socio", "privileges": []},
    {"key": "ag_secretario", "label": "Secretário da Mesa da AG",
     "orgao": ASSEMBLEIA_GERAL, "ordem": 3, "seats": 1,
     "role": "socio", "privileges": ["manage_documents"]},

    {"key": "dir_presidente", "label": "Presidente da Direcção",
     "orgao": DIRECAO, "ordem": 1, "seats": 1,
     "role": "admin", "privileges": "ALL", "is_president_accta": True},
    {"key": "dir_vice_presidente", "label": "Vice-Presidente da Direcção",
     "orgao": DIRECAO, "ordem": 2, "seats": 1,
     "role": "admin", "privileges": "ALL"},
    {"key": "dir_secretario", "label": "Secretário da Direcção",
     "orgao": DIRECAO, "ordem": 3, "seats": 1,
     "role": "admin",
     "privileges": ["manage_users", "manage_events", "manage_documents", "moderate_content"]},
    {"key": "dir_tesoureiro", "label": "Tesoureiro",
     "orgao": DIRECAO, "ordem": 4, "seats": 1,
     "role": "financeiro", "privileges": ["manage_finances", "view_audit_logs"]},
    {"key": "dir_vogal", "label": "Vogal da Direcção",
     "orgao": DIRECAO, "ordem": 5, "seats": 3,
     "role": "moderador", "privileges": ["moderate_content", "manage_events"]},

    {"key": "cf_presidente", "label": "Presidente do Conselho Fiscal",
     "orgao": CONSELHO_FISCAL, "ordem": 1, "seats": 1,
     "role": "socio", "privileges": ["view_finances_readonly", "view_audit_logs"]},
    {"key": "cf_relator", "label": "Relator do Conselho Fiscal",
     "orgao": CONSELHO_FISCAL, "ordem": 2, "seats": 1,
     "role": "socio", "privileges": ["view_finances_readonly", "view_audit_logs"]},
    {"key": "cf_vogal", "label": "Vogal do Conselho Fiscal",
     "orgao": CONSELHO_FISCAL, "ordem": 3, "seats": 1,
     "role": "socio", "privileges": ["view_finances_readonly", "view_audit_logs"]},

    {"key": "socio", "label": "Sócio",
     "orgao": None, "ordem": 99, "seats": 0,
     "role": "socio", "privileges": []},
]

# Key da conta técnica de sistema (admin@controlador.cv). Fora do catálogo
# estatutário: não vota, não recebe mandato, excluída de listagens de membros.
TECHNICAL_CARGO = "tecnico_sistema"

# --------------------------------------------------------------------------- #
# Categorias de membro, privilégios e roles (spec §5.2)
# --------------------------------------------------------------------------- #

MEMBER_CATEGORIES = ["fundador", "ordinario", "honorario"]
MEMBER_CATEGORY_LABELS = {
    "fundador": "Fundador",
    "ordinario": "Ordinário",
    "honorario": "Honorário",
}
# Honorário não vota (salvo representação admitida no Regimento, tratada à parte).
VOTING_CATEGORIES = {"fundador", "ordinario"}
DEFAULT_MEMBER_CATEGORY = "ordinario"

PRIVILEGES = [
    "manage_users",
    "manage_finances",
    "manage_events",
    "manage_documents",
    "moderate_content",
    "manage_benefits",
    "view_audit_logs",
    "view_finances_readonly",
]

ROLES = ["admin", "financeiro", "moderador", "socio"]
MANDATO_ANOS = 3

# Default de titulares da Direcção por mandato (spec decisão #3: 5 ou 7).
# Os 2 vogais extra (afectos a órgãos ATC fora da sede) activam-se com 7.
DEFAULT_DIRECAO_TITULARES = 5

# --------------------------------------------------------------------------- #
# Aliases legados (spec §5.3) — label histórico -> key canónica.
# "Administrador" e "Técnico de Sistema" NÃO mapeiam (são labels técnicos).
# --------------------------------------------------------------------------- #

LEGACY_CARGO_ALIASES = {
    "Presidente": "dir_presidente",
    "Vice-Presidente": "dir_vice_presidente",
    "Secretário-Geral": "dir_secretario",
    "Secretario-Geral": "dir_secretario",
    "Secretário": "dir_secretario",
    "Secretario": "dir_secretario",
    "Tesoureiro": "dir_tesoureiro",
    "Vogal": "dir_vogal",
    "Vogal da Direcção": "dir_vogal",
    "Vogal da Direção": "dir_vogal",
    "Membro da Direcção": "dir_vogal",
    "Membro da Direção": "dir_vogal",
    "Presidente do Conselho Fiscal": "cf_presidente",
    "Relator do Conselho Fiscal": "cf_relator",
    "Vogal do Conselho Fiscal": "cf_vogal",
    "Conselho Fiscal": "cf_vogal",
    "Presidente da Mesa": "ag_presidente",
    "Presidente da Mesa da AG": "ag_presidente",
    "Vice-Presidente da Mesa": "ag_vice_presidente",
    "Secretário da Mesa": "ag_secretario",
    "Secretario da Mesa": "ag_secretario",
    "Sócio": "socio",
    "Socio": "socio",
    "Direcção": "dir_vogal",
    "Direção": "dir_vogal",
}

# --------------------------------------------------------------------------- #
# Lookup maps internos
# --------------------------------------------------------------------------- #

_CATALOG_BY_KEY: dict[str, dict] = {c["key"]: c for c in CARGOS_CATALOG}
_KEY_SET = frozenset(_CATALOG_BY_KEY)
_LABEL_TO_KEY = {c["label"]: c["key"] for c in CARGOS_CATALOG}

# Lookup case-insensitive combinando keys, labels e aliases legados.
_LOOKUP_CI: dict[str, str] = {}
for _k in _KEY_SET:
    _LOOKUP_CI[_k.lower()] = _k
for _label, _key in _LABEL_TO_KEY.items():
    _LOOKUP_CI.setdefault(_label.lower(), _key)
for _alias, _key in LEGACY_CARGO_ALIASES.items():
    _LOOKUP_CI.setdefault(_alias.lower(), _key)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(value: str) -> Optional[datetime]:
    """Parse tolerante de ISO-8601 (aceita sufixo 'Z' e datas sem hora)."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


# --------------------------------------------------------------------------- #
# Helpers de cargo (spec §5.4)
# --------------------------------------------------------------------------- #


def cargo_info(cargo_key_or_label: str) -> Optional[dict]:
    """Entrada do catálogo para uma key/label/alias. None se desconhecido."""
    key = normalize_cargo(cargo_key_or_label)
    return _CATALOG_BY_KEY.get(key)


def normalize_cargo(value: str) -> str:
    """Converte key/label/alias legado para a key canónica. Valor desconhecido
    (ex.: label técnico livre) é devolvido sem alteração — a validação rejeita."""
    if not value:
        return value
    v = value.strip()
    if v in _KEY_SET:
        return v
    if v in _LABEL_TO_KEY:
        return _LABEL_TO_KEY[v]
    if v in LEGACY_CARGO_ALIASES:
        return LEGACY_CARGO_ALIASES[v]
    return _LOOKUP_CI.get(v.lower(), v)


def cargo_label(cargo: str) -> str:
    """Label humano para a UI. Valor desconhecido devolve-se como está."""
    info = cargo_info(cargo)
    return info["label"] if info else cargo


def privileges_for_cargo(cargo: str) -> list[str]:
    """Privilégios default do cargo, com 'ALL' expandido para a lista completa."""
    info = cargo_info(cargo)
    if not info:
        return []
    privs = info["privileges"]
    if privs == "ALL":
        return list(PRIVILEGES)
    return list(privs)


def role_for_cargo(cargo: str) -> str:
    info = cargo_info(cargo)
    return info["role"] if info else "socio"


def orgao_of_cargo(cargo: str) -> Optional[str]:
    info = cargo_info(cargo)
    return info.get("orgao") if info else None


def seats_for_cargo(cargo: str) -> int:
    info = cargo_info(cargo)
    return info["seats"] if info else 0


def is_estatutary_cargo(cargo: str) -> bool:
    """True só para cargos de órgão social (têm `orgao`). `socio` é estado base,
    não mandato estatutário → False."""
    info = cargo_info(cargo)
    return bool(info and info.get("orgao"))


# --------------------------------------------------------------------------- #
# Elegibilidade e voto (spec §8)
# --------------------------------------------------------------------------- #


def rights_suspended(user_doc: dict, as_of: Optional[str] = None) -> bool:
    """True se o membro tem direitos suspensos (perda de direitos disciplinar)
    ainda vigente em `as_of` (default = agora)."""
    until = user_doc.get("rights_suspended_until")
    if not until:
        return False
    ref = as_of or _now_iso()
    ref_dt = _parse_iso(ref)
    until_dt = _parse_iso(until)
    if ref_dt and until_dt:
        return ref_dt < until_dt
    # Fallback robusto: comparação lexicográfica de ISO-8601.
    return ref < until


def is_voting_member(user_doc: dict, as_of: Optional[str] = None) -> bool:
    """Pode votar: sócio real, activo, categoria votante, sem direitos suspensos.
    Honorário, técnico, inactivo e suspenso NÃO votam (spec §8)."""
    if (user_doc.get("account_type") or "member") != "member":
        return False
    if user_doc.get("status") != "ativo":
        return False
    category = user_doc.get("member_category") or DEFAULT_MEMBER_CATEGORY
    if category not in VOTING_CATEGORIES:
        return False
    if rights_suspended(user_doc, as_of):
        return False
    return True


def is_eligible_for_office(user_doc: dict, as_of: Optional[str] = None) -> bool:
    """Elegível para cargo: membro votante sem direitos suspensos. Mantido
    separado de `is_voting_member` para futura divergência de regras."""
    return is_voting_member(user_doc, as_of)


# --------------------------------------------------------------------------- #
# Quórum e maiorias (spec §11)
# --------------------------------------------------------------------------- #


def required_quorum(total_voters: int, chamada: int) -> int:
    """Quórum de presença em AG.
    1.ª chamada: maioria (floor(total/2)+1). 2.ª chamada: pelo menos 1/3
    (ceil(total/3))."""
    if chamada <= 1:
        return total_voters // 2 + 1
    return math.ceil(total_voters / 3)


def required_absolute_majority(voting_power_present: int) -> int:
    """Maioria absoluta dos presentes: floor(presentes/2)+1."""
    return voting_power_present // 2 + 1


def required_three_quarters(base: int) -> int:
    """3/4 de uma base (alteração de estatutos, quota/jóia, dissolução)."""
    return math.ceil(base * 3 / 4)


# --------------------------------------------------------------------------- #
# Slots eleitorais (spec §12)
# --------------------------------------------------------------------------- #


def _orgao_cargos_ordered(orgao_id: str) -> list[dict]:
    return sorted(
        (c for c in CARGOS_CATALOG if c["orgao"] == orgao_id),
        key=lambda c: c["ordem"],
    )


def _titular_slots_for_orgao(orgao_id: str) -> list[dict]:
    slots: list[dict] = []
    for c in _orgao_cargos_ordered(orgao_id):
        seats = c["seats"]
        for i in range(1, seats + 1):
            slot_key = c["key"] if seats == 1 else f"{c['key']}_{i}"
            slots.append({
                "slot_key": slot_key, "cargo": c["key"], "orgao": orgao_id,
                "suplente": False, "seat_index": i,
            })
    return slots


def _direcao_titular_slots(direcao_titulares: int) -> list[dict]:
    """Direcção tem 5 ou 7 titulares: 4 cargos singulares + (titulares-4) vogais."""
    slots: list[dict] = []
    singles = ["dir_presidente", "dir_vice_presidente", "dir_secretario", "dir_tesoureiro"]
    for key in singles:
        slots.append({
            "slot_key": key, "cargo": key, "orgao": DIRECAO,
            "suplente": False, "seat_index": 1,
        })
    n_vogais = max(0, direcao_titulares - len(singles))
    for i in range(1, n_vogais + 1):
        slots.append({
            "slot_key": f"dir_vogal_{i}", "cargo": "dir_vogal", "orgao": DIRECAO,
            "suplente": False, "seat_index": i,
        })
    return slots


def _suplente_slots(orgao_id: str, n: int) -> list[dict]:
    """Suplentes do órgão: usam o cargo mais júnior (maior `ordem`) como
    placeholder genérico (ex.: dir_vogal para a Direcção)."""
    prefix = ORGAOS[orgao_id]["slot_prefix"]
    junior = _orgao_cargos_ordered(orgao_id)[-1]["key"]
    return [
        {
            "slot_key": f"{prefix}_suplente_{i}", "cargo": junior, "orgao": orgao_id,
            "suplente": True, "seat_index": i,
        }
        for i in range(1, n + 1)
    ]


def election_slots(direcao_titulares: int = DEFAULT_DIRECAO_TITULARES) -> list[dict]:
    """Lista plana de slots a preencher numa eleição (titulares + suplentes dos
    três órgãos). Direcção configurável a 5 ou 7 titulares."""
    slots: list[dict] = []
    slots += _titular_slots_for_orgao(ASSEMBLEIA_GERAL)
    slots += _suplente_slots(ASSEMBLEIA_GERAL, ORGAOS[ASSEMBLEIA_GERAL]["suplentes"])
    slots += _direcao_titular_slots(direcao_titulares)
    slots += _suplente_slots(DIRECAO, ORGAOS[DIRECAO]["suplentes"])
    slots += _titular_slots_for_orgao(CONSELHO_FISCAL)
    slots += _suplente_slots(CONSELHO_FISCAL, ORGAOS[CONSELHO_FISCAL]["suplentes"])
    return slots


# --------------------------------------------------------------------------- #
# Estrutura para o frontend (spec §9)
# --------------------------------------------------------------------------- #


def governance_structure(direcao_titulares: int = DEFAULT_DIRECAO_TITULARES) -> dict:
    """Tudo o que o frontend precisa para deixar de hard-codar constantes."""
    return {
        "orgaos": [ORGAOS[o] for o in (ASSEMBLEIA_GERAL, DIRECAO, CONSELHO_FISCAL)],
        "cargos": [
            {
                "key": c["key"],
                "label": c["label"],
                "orgao": c["orgao"],
                "ordem": c["ordem"],
                "seats": c["seats"],
                "role_default": c["role"],
                "privileges_default": privileges_for_cargo(c["key"]),
                "is_president_accta": c.get("is_president_accta", False),
            }
            for c in CARGOS_CATALOG
        ],
        "funcoes_operacionais": [],
        "member_categories": [
            {"key": k, "label": MEMBER_CATEGORY_LABELS[k], "vota": k in VOTING_CATEGORIES}
            for k in MEMBER_CATEGORIES
        ],
        "privileges": list(PRIVILEGES),
        "roles": list(ROLES),
        "mandato_anos": MANDATO_ANOS,
        "election_slots": election_slots(direcao_titulares),
    }


# --------------------------------------------------------------------------- #
# Derivados re-exportados por models.py (compat de imports/testes)
# --------------------------------------------------------------------------- #

CARGOS = [c["label"] for c in CARGOS_CATALOG]
CARGO_KEYS = [c["key"] for c in CARGOS_CATALOG]
CARGO_DEFAULTS = {
    c["key"]: {"role": c["role"], "privileges": privileges_for_cargo(c["key"])}
    for c in CARGOS_CATALOG
}
CARGO_SEATS = {c["key"]: c["seats"] for c in CARGOS_CATALOG}

# Agrupamento por órgão (label -> [labels de cargo]); usado pelo alias deprecated
# /users/meta/cargos. "Base" agrupa o estado-base Sócio.
CARGOS_ORGAOS_SOCIAIS: dict[str, list[str]] = {}
for _c in sorted(CARGOS_CATALOG, key=lambda c: (c["ordem"] if c["orgao"] else 999)):
    _grupo = ORGAOS[_c["orgao"]]["nome"] if _c["orgao"] else "Base"
    CARGOS_ORGAOS_SOCIAIS.setdefault(_grupo, []).append(_c["label"])
