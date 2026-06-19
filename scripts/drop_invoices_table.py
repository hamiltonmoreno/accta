#!/usr/bin/env python3
"""
DROP da tabela órfã `invoices` (pós-PR #276, issue #281).

O subsistema `invoices` foi removido por completo no PR #276 (rotas, modelos,
índices e `"invoices"` saiu de `database.COLLECTIONS`). A tabela física ficou
**vazia e órfã** em produção (0 linhas verificadas no Supabase). Este script
remove-a em definitivo.

Gate de segurança (recusa dropar dados):
- Se a tabela não existir -> nada a fazer (idempotente).
- Se a tabela tiver linhas (count != 0) -> **ABORTA** sem dropar; é preciso
  investigar antes (a expectativa é 0).

⚠️  STOP CONDITION (CLAUDE.md): `--apply` faz **DROP TABLE** em produção — schema
    destrutivo. Exige `--confirm` + confirmação do dono. Faça backup antes.

⚠️  PRÉ-CONDIÇÃO: o backend em produção tem de já correr a release que inclui o
    PR #276 (sem `"invoices"` em `COLLECTIONS`). Caso contrário, `ensure_schema()`
    **recria** a tabela no próximo arranque e o drop não é durável. Ver runbook.

Uso:
    python scripts/drop_invoices_table.py                    # --dry-run (default): só verifica
    python scripts/drop_invoices_table.py --apply --confirm  # aplica o DROP de facto
"""

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


async def run(apply: bool):
    from database import close_pool, get_pool  # import tardio: só liga à DB ao correr

    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            exists = await conn.fetchval("SELECT to_regclass('public.invoices')")

            print("=" * 70)
            print("  DROP da tabela órfã `invoices` (issue #281)")
            print("=" * 70)

            if exists is None:
                print("  Tabela `invoices` NÃO existe — nada a fazer (idempotente).")
                return

            n = await conn.fetchval("SELECT count(*) FROM public.invoices")
            print(f"  Tabela `invoices` existe — {n} linha(s).")

            if n != 0:
                print("-" * 70)
                print(f"  ABORTADO: esperado 0 linhas, encontrado {n}. NÃO se dropa dados.")
                print("            Investigue a origem das linhas antes de prosseguir.")
                sys.exit(3)

            if not apply:
                print("-" * 70)
                print("  DRY-RUN: tabela vazia e pronta a remover. Nenhuma escrita efectuada.")
                print("           Use --apply --confirm para executar o DROP.")
                return

            print("-" * 70)
            print("  A executar: DROP TABLE public.invoices ...")
            await conn.execute("DROP TABLE public.invoices")
            still = await conn.fetchval("SELECT to_regclass('public.invoices')")
            if still is None:
                print("  OK: tabela `invoices` removida.")
            else:
                print("  ERRO: a tabela ainda existe após o DROP — investigar.")
                sys.exit(4)
    finally:
        await close_pool()


def main():
    # Windows: força UTF-8 no stdout para não rebentar com acentos/símbolos.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001 — best-effort; não crítico
        pass

    parser = argparse.ArgumentParser(description="DROP da tabela órfã `invoices` (issue #281).")
    parser.add_argument("--apply", action="store_true", help="Executa o DROP na DB (default: dry-run).")
    parser.add_argument("--confirm", action="store_true", help="Confirmação obrigatória para --apply.")
    args = parser.parse_args()

    if args.apply and not args.confirm:
        print("AVISO: --apply faz DROP TABLE em produção (STOP condition). Requer também --confirm.")
        print("       Faça backup da DB antes. Para verificar sem escrever, corra sem flags (dry-run).")
        sys.exit(2)

    asyncio.run(run(apply=args.apply))


if __name__ == "__main__":
    main()
