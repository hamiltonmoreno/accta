"""Regressão SQLi — payloads tratados como literais parametrizados (§5.1).

(a) _WhereBuilder coloca valores de filtro em parâmetros ($1,$2,…), nunca
interpolados no SQL; (b) _safe_search_regex escapa metacaracteres e trunca a
100 chars (anti-ReDoS). Sem DB — testa as funções de defesa diretamente.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from database import _WhereBuilder, _order_by
from helpers import safe_search_regex
from routes.finances import _safe_search_regex

pytestmark = pytest.mark.unit

PAYLOADS = [
    "' OR 1=1 --",
    "'; DROP TABLE users; --",
    "1) OR ('a'='a",
    "admin'--",
    '" OR ""="',
]


@pytest.mark.parametrize("payload", PAYLOADS)
def test_equality_filter_value_is_parametrized(payload):
    wb = _WhereBuilder()
    sql = wb.build({"email": payload})
    assert any(payload in str(p) for p in wb.params)  # viaja como parâmetro
    assert payload not in sql                          # nunca no texto SQL
    assert "DROP TABLE" not in sql.upper()
    assert "$1" in sql                                 # placeholders posicionais


@pytest.mark.parametrize("payload", PAYLOADS)
def test_regex_filter_value_is_parametrized(payload):
    wb = _WhereBuilder()
    sql = wb.build({"description": {"$regex": payload, "$options": "i"}})
    assert payload in wb.params
    assert payload not in sql
    assert "~*" in sql  # regex case-insensitive → operador ~*, valor em $1


def test_jsonb_key_is_quote_escaped():
    # _lit escapa aspas simples na chave jsonb (defesa em profundidade).
    sql = _WhereBuilder().build({"ev'il": "x"})
    assert "ev''il" in sql


def test_safe_search_regex_escapes_metachars():
    assert _safe_search_regex(".*+[](){}") == re.escape(".*+[](){}")
    assert _safe_search_regex("'; DROP--") == re.escape("'; DROP--")


def test_safe_search_regex_truncates_before_escape():
    out = _safe_search_regex("a" * 250)
    assert out == "a" * 100  # trunca o bruto a 100 antes de escapar


def test_safe_search_regex_is_the_shared_helper():
    # O alias local de finances é o helper único de helpers.py (FR-013).
    assert _safe_search_regex is safe_search_regex


# ---------- spec 019 / T052 (G3/FR-014): identificador SQL / chave jsonb / sort ----------
@pytest.mark.parametrize("payload", PAYLOADS + ["'; DROP TABLE users; --", 'a") OR ("1"="1'])
def test_jsonb_key_is_never_interpolated_raw(payload):
    # Uma CHAVE hostil (posição de identificador) é escapada por _lit: cada aspa
    # simples é duplicada e a chave vive dentro de literais SQL entre aspas — nunca
    # é colada como identificador/estrutura crua.
    sql = _WhereBuilder().build({payload: "x"})
    escaped = payload.replace("'", "''")
    assert escaped in sql, "a chave devia aparecer com as aspas simples duplicadas"
    # Nenhuma aspa simples ÍMPAR (não-escapada) sobrevive: contar ' no SQL tem de
    # dar par (todas fecham um literal ou estão duplicadas).
    if "'" in payload:
        assert sql.count("'") % 2 == 0, "aspa simples não-escapada escaparia do literal"


@pytest.mark.parametrize("payload", ["name'; DROP TABLE users; --", "a' OR '1'='1"])
def test_sort_field_is_escaped(payload):
    # Um campo de ordenação hostil é escapado (aspas duplicadas), nunca cru.
    sql = _order_by([(payload, -1)])
    assert payload.replace("'", "''") in sql
    assert "DESC" in sql


@pytest.mark.parametrize(
    "cond",
    [
        {"$in": ["' OR 1=1--", "x"]},
        {"$nin": ["'; DROP--"]},
        {"$ne": "' OR '1'='1"},
        {"$gt": "'; DELETE--"},
        {"$gte": "1' OR '1"},
        {"$lt": "x'--"},
        {"$lte": "y'--"},
        {"$exists": True},
    ],
)
def test_operator_values_are_parametrized(cond):
    wb = _WhereBuilder()
    sql = wb.build({"field": cond})
    for v in cond.values():
        if isinstance(v, str):
            assert v not in sql, f"valor {v!r} interpolado no SQL"


def test_or_and_branches_parametrize_values():
    wb = _WhereBuilder()
    sql = wb.build({"$or": [{"a": "' OR 1=1--"}, {"$and": [{"b": "'; DROP--"}]}]})
    assert "' OR 1=1--" not in sql
    assert "'; DROP--" not in sql
    assert "OR" in sql.upper() and "AND" in sql.upper()


# ---------- spec 019 / T029: nenhum call site de $regex passa input não-saneado ----------
_REGEX_LINE = re.compile(r'"\$regex"\s*:\s*([A-Za-z_][\w.]*|[^,}]+)')
_SANITIZER = re.compile(r"(safe_search_regex|_safe_search_regex|re\.escape)\s*\(")


def test_regex_call_sites_are_safe():
    """Todo `$regex` recebe ou uma chamada direta a um saneador, ou uma variável
    que foi atribuída de um saneador no MESMO ficheiro (ex.: `safe = safe_search_regex(x)`
    e depois `{"$regex": safe}`). Qualquer outro argumento é suspeito (FR-013)."""
    routes_dir = Path(__file__).resolve().parent.parent / "routes"
    offenders = []
    for py in sorted(routes_dir.glob("*.py")):
        text = py.read_text(encoding="utf-8")
        # nomes atribuídos de um saneador neste ficheiro: `x = safe_search_regex(...)`
        sanitized_vars = set(re.findall(r"(\w+)\s*=\s*(?:safe_search_regex|_safe_search_regex|re\.escape)\s*\(", text))
        for lineno, line in enumerate(text.splitlines(), 1):
            m = _REGEX_LINE.search(line)
            if not m:
                continue
            arg = m.group(1).strip()
            if _SANITIZER.search(line) or arg in sanitized_vars:
                continue
            offenders.append(f"{py.name}:{lineno}: {line.strip()}")
    assert not offenders, (
        "Call site de $regex com input possivelmente não-saneado (FR-013) — usar "
        "safe_search_regex de helpers.py:\n" + "\n".join(offenders)
    )
