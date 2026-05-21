"""Teste offline (sem BD) dos 40 artigos do blog (spec-blog-artigos).

Importa `ARTICLES` + `validate_articles` do script de seed e fixa o contrato:
40 artigos, 3 categorias, slugs/ids únicos, excerpts ≤320, sem termos proibidos,
e ids deterministicos (uuid5) para garantir idempotência do seed.

O módulo do seed NÃO importa `database` no topo (só dentro de `seed()`), por
isso pode ser importado aqui sem abrir qualquer ligação à BD.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import seed_blog_articles as sba  # noqa: E402

pytestmark = pytest.mark.unit


def test_validate_articles_passes():
    # Levanta AssertionError se qualquer regra editorial/estrutural falhar.
    sba.validate_articles()


def test_exatamente_40_artigos():
    assert len(sba.ARTICLES) == 40


def test_distribuicao_de_categorias():
    counts = {t: sum(1 for a in sba.ARTICLES if a["type"] == t) for t in ("educativo", "institucional", "noticia")}
    assert counts == {"educativo": 27, "institucional": 7, "noticia": 6}


def test_tres_artigos_socios():
    socios = [a for a in sba.ARTICLES if a["visibility"] == "socios"]
    assert len(socios) == 3
    assert all(a["type"] == "institucional" for a in socios)


def test_slugs_e_ids_unicos():
    docs = [sba.build_post_doc(a, i) for i, a in enumerate(sba.ARTICLES)]
    assert len({d["slug"] for d in docs}) == 40
    assert len({d["id"] for d in docs}) == 40


def test_build_post_doc_determinista():
    d1 = sba.build_post_doc(sba.ARTICLES[0], 0)
    d2 = sba.build_post_doc(sba.ARTICLES[0], 0)
    assert d1["id"] == d2["id"]  # uuid5 estável -> seed idempotente
    assert d1["status"] == "publicado"
    assert d1["author_name"] == "ACCTA"
    assert d1["published_at"] == d1["created_at"]


def test_sem_termos_proibidos():
    for a in sba.ARTICLES:
        hay = " ".join([a["title"], a["excerpt"], a["content"], " ".join(a["tags"])]).lower()
        for term in sba.FORBIDDEN:
            assert term not in hay, f"'{term}' em '{a['title']}'"
