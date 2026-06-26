"""Unit: o feed /activity/recent não vaza conteúdo protegido a quem não pode vê-lo.

Não importa `requests` → corre in-process sem servidor/DB.
"""
import asyncio
from types import SimpleNamespace

import routes.activity as activity


class _Cursor:
    def __init__(self, rows):
        self._rows = rows

    def sort(self, *a, **k):
        return self

    def limit(self, *a, **k):
        return self

    def skip(self, *a, **k):
        return self

    async def to_list(self, *a, **k):
        return list(self._rows)


class _Coll:
    def __init__(self, rows):
        self._rows = rows

    def find(self, query=None, projection=None):
        rows = self._rows
        # honrar o filtro de visibilidade de eventos {"visibility": {"$in": [...]}}
        if query and "visibility" in query and isinstance(query["visibility"], dict):
            allowed = query["visibility"].get("$in", [])
            rows = [r for r in rows if r.get("visibility") in allowed]
        # honrar {"id": {"$in": [...]}} para projects
        if query and "id" in query and isinstance(query["id"], dict):
            ids = query["id"].get("$in", [])
            rows = [r for r in rows if r.get("id") in ids]
        return _Cursor(rows)


def _fake_db():
    return SimpleNamespace(
        wall_posts=_Coll([]),
        project_comments=_Coll(
            [{"id": "c1", "project_id": "p-priv", "user_name": "X", "content": "segredo", "created_at": "2026-01-01"}]
        ),
        projects=_Coll(
            [{"id": "p-priv", "title": "Privado", "visibility": "direcao", "status": "ativo",
              "created_by": "other", "responsible_id": "other"}]
        ),
        events=_Coll(
            [
                {"id": "e1", "title": "Publico", "visibility": "publico", "created_at": "2026-01-02"},
                {"id": "e2", "title": "So Direcao", "visibility": "direcao", "created_at": "2026-01-03"},
            ]
        ),
        transactions=_Coll([]),
        project_milestones=_Coll([]),
        polls=_Coll([]),
    )


def _run(user):
    orig = activity.db
    activity.db = _fake_db()
    try:
        return asyncio.run(activity.get_recent_activity(limit=50, current_user=user))
    finally:
        activity.db = orig


def test_socio_nao_ve_evento_direcao_nem_comentario_privado():
    socio = SimpleNamespace(role="socio", id="socio-1")
    out = _run(socio)
    descrs = [a["description"] for a in out]
    assert not any("So Direcao" in d for d in descrs), "sócio viu evento de direção"
    assert not any("segredo" in d for d in descrs), "sócio viu comentário de projeto privado"
    assert any("Publico" in d for d in descrs), "evento público devia aparecer"


def test_admin_ve_tudo():
    admin = SimpleNamespace(role="admin", id="admin-1")
    descrs = [a["description"] for a in _run(admin)]
    assert any("So Direcao" in d for d in descrs)
    assert any("segredo" in d for d in descrs)


if __name__ == "__main__":
    test_socio_nao_ve_evento_direcao_nem_comentario_privado()
    test_admin_ve_tudo()
    print("OK")
