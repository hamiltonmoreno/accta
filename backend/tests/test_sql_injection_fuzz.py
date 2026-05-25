"""Regressão SQLi — payloads tratados como literais parametrizados (§5.1).

(a) _WhereBuilder coloca valores de filtro em parâmetros ($1,$2,…), nunca
interpolados no SQL; (b) _safe_search_regex escapa metacaracteres e trunca a
100 chars (anti-ReDoS). Sem DB — testa as funções de defesa diretamente.
"""
from __future__ import annotations

import re

import pytest

from database import _WhereBuilder
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
