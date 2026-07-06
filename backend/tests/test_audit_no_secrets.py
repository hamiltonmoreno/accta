"""audit_logs.details nunca acumula segredos — spec 019, M-AUDIT (T008).

Guarda de fonte: nenhum call site de create_audit_log passa um `details` com uma
CHAVE sensível (password/token/secret/mfa). A auditoria é retida e lida por staff
— um segredo aí registado é um leak persistente. Apanha o padrão comum (details
literal); dicts profundamente aninhados ficam de fora (guarda, não prova).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

BACKEND = Path(__file__).resolve().parent.parent
_DETAILS_BLOCK = re.compile(r"details\s*=\s*(\{.*?\})", re.DOTALL)
_SENSITIVE_KEY = re.compile(r'"[^"]*(?:password|token|secret|mfa)[^"]*"\s*:', re.IGNORECASE)


def _scan(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    hits = []
    for m in _DETAILS_BLOCK.finditer(text):
        if _SENSITIVE_KEY.search(m.group(1)):
            lineno = text[: m.start()].count("\n") + 1
            hits.append(f"{path.name}:{lineno}: {m.group(1)[:80]}")
    return hits


def test_audit_details_have_no_secret_keys():
    files = sorted((BACKEND / "routes").glob("*.py")) + [BACKEND / "helpers.py"]
    offenders = [h for f in files for h in _scan(f)]
    assert not offenders, (
        "create_audit_log com details de chave sensível (password/token/secret/mfa) — "
        "a auditoria é retida e lida por staff; não registar segredos:\n" + "\n".join(offenders)
    )


def test_audit_secret_scan_self_check(tmp_path):
    caught = tmp_path / "c.py"
    caught.write_text('details={"new_password": pw, "id": u}\n', encoding="utf-8")
    ignored = tmp_path / "i.py"
    ignored.write_text('details={"reason": "token expired", "uploaded_by": uid}\n', encoding="utf-8")
    assert _scan(caught), "devia apanhar chave sensível"
    assert not _scan(ignored), "não devia apanhar valor/chaves benignas"
