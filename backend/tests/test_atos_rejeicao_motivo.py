"""Unit — aviso de rejeição de Ato com o motivo (spec 011).

Conduz `routes.atos.sign_ato` diretamente, com um `sign_ato_atomic` falso fiel
(opera sobre o doc em memória, como em test_atos.py) e `notify_users`/
`create_audit_log` observáveis. Cobre os 7 casos do quickstart (Cenário A).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from atos_rules import requisitos_for_tipo
from models import AtoSign, User
from routes import atos as atos_route


def _user(cargo="dir_presidente", uid=None) -> User:
    return User(
        id=uid or str(uuid.uuid4()),
        name="Membro Direção",
        email=f"{uuid.uuid4().hex[:6]}@example.cv",
        role="socio",
        status="ativo",
        cargo=cargo,
        consent_data=True,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def _request():
    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test", "origin": "https://accta.cv"}

    return _R()


def _pendente(assinaturas=None):
    return {
        "id": "a1",
        "tipo": "vinculativo",
        "status": "pendente",
        "requisitos": requisitos_for_tipo("vinculativo"),
        "created_by": "prop1",
        "assinaturas": assinaturas or [],
    }


def _wire(monkeypatch, doc):
    """Liga db.atos, um sign_ato_atomic falso fiel, e notify/audit observáveis."""
    coll = MagicMock(name="atos")
    coll.find_one = AsyncMock(return_value=doc)
    coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    monkeypatch.setattr(atos_route.db, "atos", coll, raising=False)

    async def _fake(ato_id, user_id, assinatura, compute_status):
        novas = list(doc.get("assinaturas") or []) + [assinatura]
        doc["assinaturas"] = novas
        doc["status"] = compute_status(novas, doc.get("requisitos") or {})
        return {"outcome": "signed", "ato": doc}

    monkeypatch.setattr(atos_route, "sign_ato_atomic", AsyncMock(side_effect=_fake))
    notify = AsyncMock()
    audit = AsyncMock()
    monkeypatch.setattr(atos_route, "notify_users", notify)
    monkeypatch.setattr(atos_route, "create_audit_log", audit)
    return doc, notify, audit


# --------------------------------------------------------------------------- #


async def test_rejeitar_sem_motivo_400(mock_db, monkeypatch):
    _wire(monkeypatch, _pendente())
    with pytest.raises(HTTPException) as e:
        await atos_route.sign_ato("a1", AtoSign(decisao="rejeitado"), _request(), current_user=_user())
    assert e.value.status_code == 400
    assert "motivo" in e.value.detail.lower()


async def test_rejeitar_motivo_so_espacos_400(mock_db, monkeypatch):
    _wire(monkeypatch, _pendente())
    with pytest.raises(HTTPException) as e:
        await atos_route.sign_ato("a1", AtoSign(decisao="rejeitado", motivo="   "), _request(), current_user=_user())
    assert e.value.status_code == 400


async def test_rejeitar_motivo_longo_400(mock_db, monkeypatch):
    _wire(monkeypatch, _pendente())
    with pytest.raises(HTTPException) as e:
        await atos_route.sign_ato(
            "a1", AtoSign(decisao="rejeitado", motivo="x" * 501), _request(), current_user=_user()
        )
    assert e.value.status_code == 400
    assert "500" in e.value.detail


async def test_rejeitar_com_motivo_persiste_na_assinatura(mock_db, monkeypatch):
    doc, _notify, _audit = _wire(monkeypatch, _pendente())
    await atos_route.sign_ato(
        "a1", AtoSign(decisao="rejeitado", motivo="  Falta o comprovativo.  "), _request(), current_user=_user()
    )
    assert doc["status"] == "rejeitado"
    assert doc["assinaturas"][-1]["motivo"] == "Falta o comprovativo."  # strip aplicado


async def test_aviso_ao_proponente_inclui_motivo_e_exclui_quem_rejeita(mock_db, monkeypatch):
    doc, notify, _audit = _wire(monkeypatch, _pendente())
    rejeitador = _user(uid="rej1")
    await atos_route.sign_ato(
        "a1", AtoSign(decisao="rejeitado", motivo="Documento em falta"), _request(), current_user=rejeitador
    )
    notify.assert_awaited()
    args, kwargs = notify.await_args
    assert args[0] == ["prop1"]  # destinatário = proponente
    assert "Documento em falta" in args[3]  # motivo no corpo do aviso
    assert kwargs.get("exclude_id") == "rej1"  # não auto-avisa quem rejeitou


async def test_auditoria_inclui_motivo(mock_db, monkeypatch):
    doc, _notify, audit = _wire(monkeypatch, _pendente())
    await atos_route.sign_ato(
        "a1", AtoSign(decisao="rejeitado", motivo="Razão auditável"), _request(), current_user=_user()
    )
    detalhes = [c.kwargs.get("details") for c in audit.await_args_list if c.kwargs.get("details")]
    assert any((d or {}).get("motivo") == "Razão auditável" for d in detalhes)


async def test_aprovar_ignora_motivo(mock_db, monkeypatch):
    # 1 aprovação num vinculativo (precisa 2 Direção) → fica pendente; motivo não é gravado.
    doc, notify, _audit = _wire(monkeypatch, _pendente())
    await atos_route.sign_ato(
        "a1", AtoSign(decisao="aprovado", motivo="nao deve gravar"), _request(), current_user=_user()
    )
    assert "motivo" not in doc["assinaturas"][-1]
    assert doc["status"] == "pendente"
    notify.assert_not_awaited()  # ainda pendente → sem aviso de decisão
