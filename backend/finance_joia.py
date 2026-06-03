"""Cálculo da jóia de admissão (spec-controlos-financeiros §6, Art. 6).

Jóia = `joia_amount` fixo, senão `joia_multiplier` × `quota_amount` em vigor;
devida só a quem se qualificou como CTA há MAIS de 4 meses e não está isento.
Função pura (sem DB), partilhada pelo hook de admissão (`routes/admin.py`) e
pelo endpoint de preview (`routes/finances.py`).

Isenções (decisões do dono, 2026-05-23): fundador e honorário (spec §12.6),
`joia_isento` explícito, e quem não tem `cta_qualified_since` (decisão manual).
A jóia é apenas ASSINALADA na admissão (`joia_devida`); a cobrança é manual
pelo Tesoureiro (lança `Transaction` `category="joias"`).
"""

from __future__ import annotations

import calendar
from datetime import date
from typing import Optional

# Categorias de membro isentas de jóia (a par de `joia_isento` explícito).
JOIA_EXEMPT_CATEGORIES = {"fundador", "honorario"}
# Art. 6: CTA qualificado há MAIS de 4 meses.
JOIA_QUALIFICATION_MONTHS = 4


def _qualified_more_than_months(since_iso, months: int, today: Optional[date] = None) -> bool:
    """True se `since_iso` (AAAA-MM-DD) está há ESTRITAMENTE mais de `months`
    meses no passado. Data ausente/inválida → False (trata como não qualificado)."""
    if not since_iso:
        return False
    try:
        since = date.fromisoformat(str(since_iso).strip()[:10])
    except (ValueError, TypeError):
        return False
    today = today or date.today()
    # Data em que se completam exactamente `months` meses após a qualificação.
    y = since.year + (since.month - 1 + months) // 12
    m = (since.month - 1 + months) % 12 + 1
    d = min(since.day, calendar.monthrange(y, m)[1])
    return date(y, m, d) < today  # estritamente MAIS de `months` meses


def _joia_valor(settings: dict) -> float:
    """Valor de referência da jóia: `joia_amount` fixo sobrepõe o múltiplo."""
    quota = float(settings.get("quota_amount") or 0.0)
    amount = settings.get("joia_amount")
    if amount is not None:
        return float(amount)
    multiplier = settings.get("joia_multiplier")
    if multiplier is None:
        multiplier = 2.0
    return float(multiplier) * quota


def joia_status(user_doc: dict, settings: dict, today: Optional[date] = None) -> dict:
    """Avaliação completa (para o preview/modal): valor de referência, se é
    devida, e o motivo. `joia_devida=None` ⇒ nada a cobrar."""
    valor = _joia_valor(settings)
    base = {"valor_base": valor, "quota_amount": float(settings.get("quota_amount") or 0.0)}
    if user_doc.get("joia_isento"):
        return {**base, "joia_devida": None, "isento": True, "motivo": "Isenção explícita"}
    cat = user_doc.get("member_category")
    if cat in JOIA_EXEMPT_CATEGORIES:
        return {**base, "joia_devida": None, "isento": True, "motivo": f"Categoria isenta ({cat})"}
    since = user_doc.get("cta_qualified_since")
    if not since:
        return {**base, "joia_devida": None, "isento": False, "motivo": "Sem data de qualificação CTA"}
    if not _qualified_more_than_months(since, JOIA_QUALIFICATION_MONTHS, today):
        return {**base, "joia_devida": None, "isento": False, "motivo": "Qualificado há 4 meses ou menos"}
    return {**base, "joia_devida": valor, "isento": False, "motivo": "Jóia devida"}


def compute_joia(user_doc: dict, settings: dict, today: Optional[date] = None) -> Optional[float]:
    """Atalho: só o valor da jóia devida (None se isento/não qualificado)."""
    return joia_status(user_doc, settings, today)["joia_devida"]
