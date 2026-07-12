"""Árbitro do bump de dependências — spec 019, WS-G (T038).

Prova, pelo ENDPOINT REAL (via MultiPartParser, não `save_validated_upload`
direto), que um upload de ficheiro >1 MB atravessa o parser em
starlette 0.41.3 sem `400 "Part exceeded maximum size"`. É o gate que valida o
par fastapi/starlette bumpado: se uma versão futura reintroduzir um teto que
parta uploads de ficheiro, este teste fica VERMELHO.

Conclusão do levantamento (spec 019): o `max_part_size` (default 1 MB) do
starlette limita CAMPOS de formulário não-ficheiro, NÃO uploads de ficheiro
(que fazem spool para disco). Por isso a mitigação `max_part_size` do plano
foi dispensada — provado aqui empiricamente.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import routes.upload as upload_route
from auth import get_current_user
from server import app

pytestmark = pytest.mark.unit

# PDF mínimo válido (magic %PDF-) + padding até >1 MB.
_PDF_2MB = b"%PDF-1.4\n" + b"x" * (2 * 1024 * 1024)


@pytest.fixture
def _admin_upload_client(mock_db, admin_user, monkeypatch):
    # RBAC via override; limiter do módulo desligado (o @limiter.limit exige um
    # Request real e corre primeiro — gotcha slowapi).
    monkeypatch.setattr(upload_route.limiter, "enabled", False)
    app.dependency_overrides[get_current_user] = lambda: admin_user
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def test_file_upload_over_1mb_passes_multipart_parser(_admin_upload_client):
    resp = _admin_upload_client.post(
        "/api/upload/documents",
        files={"file": ("relatorio.pdf", _PDF_2MB, "application/pdf")},
    )
    # O parser NÃO pode devolver 400 "Part exceeded maximum size" — é o árbitro
    # do bump. 200 (guardou) é o caminho feliz; um 500 do save também prova que o
    # corpo >1 MB chegou à rota (o que interessa aqui é: não morreu no parser).
    assert resp.status_code != 400, resp.text
    assert "Part exceeded" not in resp.text
    assert resp.status_code in (200, 500)
    if resp.status_code == 200:
        assert resp.json()["size"] == len(_PDF_2MB)


def test_oversize_file_returns_413_not_400(_admin_upload_client):
    # Um ficheiro ACIMA do teto da categoria (documents=10 MB) é rejeitado pela
    # app com 413 (read_upload_capped), nunca 400 do parser.
    big = b"%PDF-1.4\n" + b"x" * (11 * 1024 * 1024)
    resp = _admin_upload_client.post(
        "/api/upload/documents",
        files={"file": ("grande.pdf", big, "application/pdf")},
    )
    assert resp.status_code == 413, resp.text
