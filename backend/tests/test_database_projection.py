"""
Unit tests for the DAO projection emulator (`database._apply_projection`).

Pure function — no DB, no mocks. Regression coverage for the bug where
Mongo *exclusion* projections (`{"password": 0}`) were ignored and the
full document returned, leaking excluded fields (e.g. password hashes /
invite tokens on `GET /admin/invites/pending`).
"""

from __future__ import annotations

import pytest

from database import _apply_projection

pytestmark = pytest.mark.unit


def _doc() -> dict:
    return {
        "id": "u1",
        "name": "Ana",
        "email": "ana@accta.cv",
        "password": "$2b$bcrypt-hash",
        "invite_token": "secret-token",
        "status": "ativo",
    }


class TestNoOpProjections:
    def test_none_projection_returns_full_doc(self):
        assert _apply_projection(_doc(), None) == _doc()

    def test_empty_projection_returns_full_doc(self):
        assert _apply_projection(_doc(), {}) == _doc()

    def test_id_only_exclusion_is_noop(self):
        # `_id` does not exist here; `{"_id": 0}` must return the full doc.
        assert _apply_projection(_doc(), {"_id": 0}) == _doc()


class TestInclusionProjection:
    def test_returns_only_included_fields(self):
        out = _apply_projection(_doc(), {"_id": 0, "id": 1, "name": 1})
        assert out == {"id": "u1", "name": "Ana"}

    def test_missing_included_key_is_skipped(self):
        out = _apply_projection(_doc(), {"name": 1, "absent": 1})
        assert out == {"name": "Ana"}


class TestExclusionProjection:
    def test_excludes_single_field(self):
        out = _apply_projection(_doc(), {"_id": 0, "password": 0})
        assert "password" not in out
        assert out["email"] == "ana@accta.cv"
        assert set(out) == {"id", "name", "email", "invite_token", "status"}

    def test_excludes_multiple_sensitive_fields(self):
        # The GET /admin/invites/pending scenario.
        out = _apply_projection(_doc(), {"_id": 0, "password": 0, "invite_token": 0})
        assert "password" not in out
        assert "invite_token" not in out
        assert out["name"] == "Ana"

    def test_exclusion_with_false_value(self):
        out = _apply_projection(_doc(), {"attendees": False})
        assert "attendees" not in out
        assert out["id"] == "u1"

    def test_excluding_absent_field_returns_rest(self):
        out = _apply_projection({"a": 1, "b": 2}, {"missing": 0})
        assert out == {"a": 1, "b": 2}
