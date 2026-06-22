#!/usr/bin/env python3
"""
Backfill de multas já aplicadas para o caixa (spec-eventos-multas-caixa, FR-018).

A partir desta funcionalidade, ao aplicar uma sanção de multa cria-se uma receita
no caixa (`sancao_id`). Para multas **já aplicadas antes** disto, este script cria
a receita em falta — associada à sanção, categoria "extraordinarias".

Reconciliação: o dry-run lista as sanções `tipo="multa"`, `status="aplicada"`,
`multa_valor>0` que **não** têm já uma receita com esse `sancao_id`.

Idempotente: uma multa que já tenha receita (por `sancao_id`) é saltada.

Uso:
    python scripts/migrate_multas_to_transactions.py                    # dry-run (default)
    python scripts/migrate_multas_to_transactions.py --apply --confirm  # aplica

⚠️  STOP CONDITION (Constitution VI #1): `--apply` ESCREVE em `transactions`.
    Exige `--confirm` + confirmação explícita do dono. Reveja o dry-run antes.
"""

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from models import Transaction  # noqa: E402


def is_multa_candidate(sancao: dict) -> bool:
    """PURA: True se a sanção é uma multa aplicada com valor (elegível a backfill)."""
    try:
        valor = float(sancao.get("multa_valor") or 0)
    except (TypeError, ValueError):
        return False
    return sancao.get("tipo") == "multa" and sancao.get("status") == "aplicada" and valor > 0


def multa_to_transaction(sancao: dict, nome: str = None) -> dict:
    """PURA: dict da receita de multa para uma sanção. Preserva `aplicada_em`/
    `created_at` como data, se existir."""
    tx = Transaction(
        type="receita",
        category="extraordinarias",
        description=f"Multa - {nome}" if nome else "Multa",
        amount=float(sancao["multa_valor"]),
        date=sancao.get("aplicada_em") or sancao.get("created_at"),
        sancao_id=sancao["id"],
        user_id=sancao.get("user_id"),
        created_by=sancao.get("proposta_por") or "system",
    )
    return tx.model_dump()


async def run(apply: bool):
    from database import close_pool, db  # import tardio: só liga à DB ao correr

    sancoes = await db.sancoes.find({}, {"_id": 0}).to_list(None)
    candidates = [s for s in sancoes if is_multa_candidate(s)]
    # sancao_ids que já têm receita no caixa.
    existing = await db.transactions.find(
        {"type": "receita", "sancao_id": {"$exists": True}}, {"_id": 0, "sancao_id": 1}
    ).to_list(None)
    done_ids = {t.get("sancao_id") for t in existing}
    pending = [s for s in candidates if s["id"] not in done_ids]

    print("=" * 72)
    print("  Backfill multas aplicadas -> transactions (spec-eventos-multas-caixa)")
    print(f"  multas aplicadas c/ valor={len(candidates)} | a criar receita={len(pending)} | "
          f"já no caixa={len(candidates) - len(pending)}")
    print("=" * 72)
    for s in pending:
        print(f"  • sancao {s.get('id')} user={s.get('user_id')} {float(s.get('multa_valor') or 0):,.0f} CVE")

    if not pending:
        print("  Nada a migrar — todas as multas aplicadas já têm receita no caixa.")

    if not apply:
        print("-" * 72)
        print("  DRY-RUN: nenhuma escrita. Use --apply --confirm após rever (e confirmar com o dono).")
        await close_pool()
        return

    print(f"  A APLICAR {len(pending)} receita(s) de multa...")
    applied = 0
    for s in pending:
        socio = await db.users.find_one({"id": s.get("user_id")}, {"_id": 0, "name": 1})
        tx = multa_to_transaction(s, (socio or {}).get("name"))
        await db.transactions.insert_one(tx)
        applied += 1
    print(f"  OK: {applied} receita(s) de multa criada(s).")
    await close_pool()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    parser = argparse.ArgumentParser(description="Backfill de multas aplicadas para o caixa (receita com sancao_id).")
    parser.add_argument("--apply", action="store_true", help="Escreve na DB (default: dry-run).")
    parser.add_argument("--confirm", action="store_true", help="Confirmacao obrigatoria para --apply.")
    args = parser.parse_args()

    if args.apply and not args.confirm:
        print("AVISO: --apply ESCREVE em `transactions` (STOP condition). Requer tambem --confirm.")
        print("       Reveja o dry-run e confirme com o dono. Faca backup da DB antes.")
        sys.exit(2)

    asyncio.run(run(apply=args.apply))


if __name__ == "__main__":
    main()
