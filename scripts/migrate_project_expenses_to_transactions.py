#!/usr/bin/env python3
"""
Migração de despesas de projeto para o caixa central (spec-fluxo-financeiro-unificado, FR-012/013/014).

Converte cada documento de `project_expenses` numa `Transaction` de despesa
ligada ao projeto (`type="despesa"`, `project_id`, `category="operacional"`),
preservando data/descrição/autor/created_at. A partir daí, `project.spent`
deriva das transações e `project_expenses` deixa de ser fonte de dados.

Reconciliação: o dry-run sinaliza POSSÍVEIS DUPLICADOS — transações de despesa já
existentes SEM `project_id`, com o mesmo montante e data próxima (mesmo dia) —
que podem ter sido relançadas manualmente no caixa. Reveja-os antes de aplicar.

Idempotente: uma despesa já migrada (com `migrated_to_transaction_id`) é saltada.

Uso:
    python scripts/migrate_project_expenses_to_transactions.py                    # dry-run (default)
    python scripts/migrate_project_expenses_to_transactions.py --apply --confirm  # aplica

⚠️  STOP CONDITION (Constitution VI #1): `--apply` ESCREVE em `transactions`.
    Exige `--confirm` + confirmação explícita do dono. Faça backup antes.
    NÃO corra `--apply` sem ter revisto o relatório de reconciliação do dry-run.
"""

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from models import Transaction  # noqa: E402


def expense_to_transaction(expense: dict) -> dict:
    """PURA (sem DB): mapeia um project_expense para o dict de uma Transaction
    de despesa ligada ao projeto. Preserva data/descrição/autor/created_at.
    Testável sem base de dados."""
    tx = Transaction(
        type="despesa",
        category="operacional",
        description=expense.get("description") or "Despesa de projeto",
        amount=float(expense.get("amount") or 0),
        date=expense.get("date") or expense.get("created_at"),
        project_id=expense.get("project_id"),
        created_by=expense.get("created_by") or "",
    )
    d = tx.model_dump()
    # Preserva o created_at original da despesa (auditoria), se existir.
    if expense.get("created_at"):
        d["created_at"] = expense["created_at"]
    return d


def is_duplicate_suspect(expense: dict, tx: dict) -> bool:
    """PURA: True se `tx` (transação existente) parece já espelhar `expense` —
    despesa SEM project_id, mesmo montante, mesmo dia (prefixo da data)."""
    if tx.get("type") != "despesa" or tx.get("project_id"):
        return False
    try:
        same_amount = abs(float(tx.get("amount") or 0) - float(expense.get("amount") or 0)) < 0.01
    except (TypeError, ValueError):
        return False
    e_day = (expense.get("date") or "")[:10]
    t_day = (tx.get("date") or "")[:10]
    return same_amount and bool(e_day) and e_day == t_day


async def run(apply: bool):
    from database import close_pool, db  # import tardio: só liga à DB ao correr

    expenses = await db.project_expenses.find({}, {"_id": 0}).to_list(None)
    # Transações de despesa sem project_id = candidatas a duplicado.
    orphan_despesas = await db.transactions.find(
        {"type": "despesa", "project_id": {"$exists": False}}, {"_id": 0}
    ).to_list(None)

    pending = [e for e in expenses if not e.get("migrated_to_transaction_id")]
    already = len(expenses) - len(pending)

    print("=" * 72)
    print(f"  Migração project_expenses -> transactions (spec-fluxo-financeiro-unificado)")
    print(f"  {len(expenses)} despesas de projeto | {len(pending)} a migrar | {already} já migradas")
    print("=" * 72)

    suspects = []
    for e in pending:
        cands = [t.get("id") for t in orphan_despesas if is_duplicate_suspect(e, t)]
        marca = f"  ⚠ POSSÍVEL DUPLICADO de transações {cands}" if cands else ""
        print(
            f"  • expense {e.get('id')}  proj={e.get('project_id')}  "
            f"{float(e.get('amount') or 0):,.0f} CVE  {(e.get('date') or '')[:10]}  "
            f"{(e.get('description') or '')[:35]}{marca}"
        )
        if cands:
            suspects.append((e, cands))

    print("-" * 72)
    if suspects:
        print(f"  ⚠ {len(suspects)} despesa(s) com possíveis duplicados já no caixa — REVEJA antes de aplicar.")
    else:
        print("  Sem duplicados suspeitos detectados.")

    if not apply:
        print("  DRY-RUN: nenhuma escrita. Use --apply --confirm após rever (e confirmar com o dono).")
        await close_pool()
        return

    print(f"  A APLICAR {len(pending)} conversão(ões)...")
    applied = 0
    for e in pending:
        tx = expense_to_transaction(e)
        await db.transactions.insert_one(tx)
        await db.project_expenses.update_one(
            {"id": e["id"]}, {"$set": {"migrated_to_transaction_id": tx["id"]}}
        )
        applied += 1
    print(f"  OK: {applied} despesa(s) convertida(s) em transações de projeto.")
    await close_pool()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001 — best-effort
        pass

    parser = argparse.ArgumentParser(
        description="Migra project_expenses para transactions (despesa com project_id)."
    )
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
