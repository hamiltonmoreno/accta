"""Regressão do _WhereBuilder — pertença em array (scalar-vs-array membership).

O ramo de pertença usa o operador de existência `?` com um parâmetro **text**,
NÃO `@> $n::jsonb`: o asyncpg liga um parâmetro jsonb de forma a que
`col @> $n::jsonb` nunca casa (um literal jsonb casa), portanto esse ramo era
código morto e qualquer filtro `{arrayField: scalar}` devolvia vazio sem erro
(ex.: `routes/report.py` → `events_attended` vinha sempre 0).

Sem DB — inspeciona o SQL gerado. Ver `memory/dao-array-membership-broken.md`.
"""

from database import _WhereBuilder


def test_array_membership_uses_existence_operator_not_jsonb_containment():
    wb = _WhereBuilder()
    sql = wb.build({"attendees": "u1"})
    # o valor de filtro viaja como parâmetro — nunca interpolado no SQL
    assert "u1" in wb.params
    assert "u1" not in sql
    # ramo de pertença: `?` (existência de elemento) guardado por jsonb_typeof
    assert "jsonb_typeof(doc->'attendees') = 'array'" in sql
    assert "doc->'attendees' ?" in sql
    # NÃO o padrão partido `@> $n::jsonb` (param jsonb nunca casa no asyncpg)
    assert "@>" not in sql
    assert "::jsonb" not in sql


def test_scalar_equality_branch_preserved():
    # campos escalares (não-array) continuam a casar por igualdade de texto
    wb = _WhereBuilder()
    sql = wb.build({"status": "ativo"})
    assert "(doc->>'status') = $1" in sql
    assert "ativo" in wb.params


def test_membership_value_rendered_as_text():
    # o parâmetro de pertença é o texto do escalar (como o ?| do $in), não JSON
    wb = _WhereBuilder()
    wb.build({"team_members": "user-123"})
    assert "user-123" in wb.params
    assert '["user-123"]' not in wb.params  # não a forma jsonb-array antiga


# --------------------------------------------------------------------------- #
# _order_by — sort COALESCE de campos alternativos (data efetiva de posts)
# --------------------------------------------------------------------------- #

from database import _order_by  # noqa: E402


def test_order_by_single_field_desc():
    sql = _order_by([("created_at", -1)])
    assert "ORDER BY" in sql
    assert "(doc->>'created_at') DESC" in sql
    assert "COALESCE" not in sql


def test_order_by_coalesce_alternativos():
    # Campo dado como tupla → COALESCE pela 1.ª chave presente (published_at,
    # com fallback created_at): a data efetiva de _order_by sem materializar campo.
    sql = _order_by([(("published_at", "created_at"), -1)])
    assert "COALESCE((doc->>'published_at'), (doc->>'created_at')) DESC" in sql


def test_order_by_vazio():
    assert _order_by(None) == ""
