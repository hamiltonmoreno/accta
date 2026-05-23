#!/usr/bin/env python3
"""
Migração de categorias de receita estatutárias (spec-controlos-financeiros §5.2, Art. 5).

Renomeia `transactions.doc.category` de aliases legados para as keys estatutárias
(decisões do dono, 2026-05-21 — ver memory/finance-specs-alignment):

    patrocinios    -> extraordinarias
    doacoes        -> donativos
    eventos        -> extraordinarias   (SÓ receitas)
    outros_receita -> extraordinarias
    quotas         -> quotas            (inalterada; generate-quotas dedup nela)

Só transacções `type == "receita"` são afetadas — a categoria de DESPESA
"eventos" continua válida e NÃO é renomeada. A transformação é idempotente
(correr 2x não muda nada na 2.ª).

Uso:
    python scripts/migrate_income_categories.py                    # --dry-run (default): só relatório
    python scripts/migrate_income_categories.py --apply --confirm  # aplica de facto

⚠️  STOP CONDITION (spec §11): `--apply` ESCREVE em `transactions`. Exige a flag
    explícita `--confirm` + confirmação do utilizador. Faça backup da base antes.
"""

import argparse
import asyncio
import os
import sys
from typing import Optional

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from models import LEGACY_INCOME_ALIASES, canonical_income_category  # noqa: E402


def plan_transaction_change(doc: dict) -> Optional[str]:
    """PURA (sem DB): devolve a nova `category` se for uma receita com alias
    legado; None se nada muda (idempotente). Testável sem base de dados."""
    if doc.get("type") != "receita":
        return None
    current = doc.get("category")
    if not current:
        return None
    new = canonical_income_category(current)
    return new if new != current else None


async def run(apply: bool):
    from database import close_pool, db  # import tardio: só liga à DB ao correr

    txs = await db.transactions.find({}, {"_id": 0}).to_list(None)
    total = len(txs)
    planned = [(t, plan_transaction_change(t)) for t in txs]
    to_change = [(t, new) for t, new in planned if new]

    print("=" * 70)
    print(f"  Migração de categorias de receita — {total} transacções analisadas")
    print(f"  {len(to_change)} com alterações | {total - len(to_change)} já canónicas/N/A")
    print(f"  Mapa de alias: {LEGACY_INCOME_ALIASES}")
    print("=" * 70)
    for t, new in to_change:
        print(f"  • {t.get('id')}  category: {t.get('category')!r} -> {new!r}  ({t.get('description', '')[:40]})")

    if not to_change:
        print("  Nada a migrar — todas as receitas já em categorias estatutárias.")

    if not apply:
        print("-" * 70)
        print("  DRY-RUN: nenhuma escrita efectuada. Use --apply --confirm para aplicar.")
        await close_pool()
        return

    print("-" * 70)
    print(f"  A APLICAR {len(to_change)} alteracao(oes)...")
    applied = 0
    for t, new in to_change:
        await db.transactions.update_one({"id": t["id"]}, {"$set": {"category": new}})
        applied += 1
    print(f"  OK: {applied} transaccao(oes) actualizada(s).")
    await close_pool()


def main():
    # Windows: força UTF-8 no stdout para não rebentar com acentos/símbolos.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001 — best-effort; não crítico
        pass

    parser = argparse.ArgumentParser(description="Migracao de categorias de receita para keys estatutarias (Art. 5).")
    parser.add_argument("--apply", action="store_true", help="Escreve as alteracoes na DB (default: dry-run).")
    parser.add_argument("--confirm", action="store_true", help="Confirmacao obrigatoria para --apply.")
    args = parser.parse_args()

    if args.apply and not args.confirm:
        print("AVISO: --apply ESCREVE em `transactions` (STOP condition). Requer tambem --confirm.")
        print("       Faca backup da DB antes. Para ver o que mudaria, corra sem flags (dry-run).")
        sys.exit(2)

    asyncio.run(run(apply=args.apply))


if __name__ == "__main__":
    main()
