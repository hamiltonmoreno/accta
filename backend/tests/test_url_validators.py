"""Validators de URL local em campos de imagem + brand icon — spec 019, WS-F (FR-016/018).

Os modelos de ESCRITA (Create/Update) só aceitam /uploads/… (ou vazio/None) em
logo_url/cover_url/capa_url — bloqueia javascript:/data:/http(s) externo. Os
modelos Base (response) NÃO revalidam (serializam documentos legados; FR-024).
`get_brand_icon` só faz 302 para /uploads/… ou o host de FRONTEND_URL.
"""
from __future__ import annotations

import pytest

from models import (
    Benefit,
    BenefitCreate,
    BenefitUpdate,
    PostCreate,
    PostUpdate,
    PublicacaoCreate,
    PublicacaoUpdate,
)
from routes.brand import _is_safe_icon_target

pytestmark = pytest.mark.unit

GOOD = [None, "", "/uploads/covers/x.png", "/uploads/logos/y.jpg"]
BAD = ["javascript:alert(1)", "http://evil.com/x.png", "https://evil.com/x.png", "data:image/png;base64,AAAA", "//evil.com/x", "/etc/passwd"]


@pytest.mark.parametrize("v", GOOD)
def test_create_update_accept_local_urls(v):
    BenefitCreate(name="a", description="b", discount_percent=1, logo_url=v)
    BenefitUpdate(logo_url=v)
    PostCreate(title="abc", content="x", cover_url=v)
    PostUpdate(cover_url=v)
    PublicacaoCreate(titulo="t", tipo="artigo", document_id="d", data_publicacao="2026-01-01", capa_url=v)
    PublicacaoUpdate(capa_url=v)


@pytest.mark.parametrize("v", BAD)
def test_create_update_reject_external_or_dangerous_urls(v):
    for factory in (
        lambda: BenefitCreate(name="a", description="b", discount_percent=1, logo_url=v),
        lambda: BenefitUpdate(logo_url=v),
        lambda: PostCreate(title="abc", content="x", cover_url=v),
        lambda: PostUpdate(cover_url=v),
        lambda: PublicacaoCreate(titulo="t", tipo="artigo", document_id="d", data_publicacao="2026-01-01", capa_url=v),
        lambda: PublicacaoUpdate(capa_url=v),
    ):
        with pytest.raises(Exception):  # pydantic ValidationError
            factory()


def test_base_response_model_does_not_revalidate_legacy():
    # Um doc legado com URL externa continua a serializar (não parte a leitura).
    b = Benefit(id="x", name="a", description="b", logo_url="http://legacy.example/x.png", discount_percent=1)
    assert b.logo_url == "http://legacy.example/x.png"


def test_brand_icon_target_guard(monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "https://controlador.cv")
    assert _is_safe_icon_target("/uploads/brand/i.png") is True
    assert _is_safe_icon_target("https://controlador.cv/logo.png") is True
    assert _is_safe_icon_target("https://evil.com/x.png") is False
    assert _is_safe_icon_target("javascript:alert(1)") is False
    assert _is_safe_icon_target(None) is False
    assert _is_safe_icon_target("") is False
