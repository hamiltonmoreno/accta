#!/usr/bin/env python3
"""
Migração de governança estatutária (spec-governanca-estatutaria §16, Fase M2).

Normaliza os documentos de `users` para o catálogo canónico de `governance.py`:
- `cargo` (label/alias legado) -> KEY canónica (ex.: "Presidente" -> "dir_presidente").
- preenche `orgao` denormalizado a partir do cargo.
- preenche `member_category="ordinario"` e `account_type="member"` onde ausentes.
- normaliza `cargo_history[].cargo` para key e guarda o `label` (snapshot).

Contas técnicas (`account_type="technical"`, ex.: admin@controlador.cv) ficam
FORA do catálogo: o cargo livre não é mexido, não recebem member_category/orgão.

Uso:
    python scripts/migrate_governance_cargos.py            # --dry-run (default): só relatório
    python scripts/migrate_governance_cargos.py --apply --confirm   # aplica de facto

⚠️  STOP CONDITION (spec §20): `--apply` ESCREVE em `users`/`cargo_history`.
    Exige a flag explícita `--confirm` e confirmação do utilizador. Faça backup
    da base antes. A transformação é idempotente (correr 2x não muda nada na 2ª).
"""

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from governance import cargo_label, normalize_cargo, orgao_of_cargo  # noqa: E402


def plan_user_changes(doc: dict) -> dict:
    """PURA (sem DB): devolve o `$set` necessário para canonizar um user doc.
    Dict vazio = já canónico (idempotente). Testável sem base de dados."""
    changes: dict = {}
    technical = doc.get("account_type") == "technical"

    # account_type ausente -> "member" (técnicas mantêm o que têm).
    if "account_type" not in doc:
        changes["account_type"] = "member"

    # cargo -> key canónica (label/alias legado resolvido; desconhecido mantém-se).
    raw_cargo = doc.get("cargo")
    new_cargo = "socio" if raw_cargo is None else normalize_cargo(raw_cargo)
    if new_cargo != doc.get("cargo"):
        changes["cargo"] = new_cargo

    # orgao denormalizado a partir do cargo (None para socio/livre/técnico).
    new_orgao = orgao_of_cargo(new_cargo)
    if new_orgao != doc.get("orgao"):
        changes["orgao"] = new_orgao

    # member_category default só para sócios (não técnicas), onde ausente.
    if not technical and "member_category" not in doc:
        changes["member_category"] = "ordinario"

    # cargo_history: cada entrada normalizada para key + label + orgao.
    history = doc.get("cargo_history") or []
    if history:
        new_history = []
        for m in history:
            nm = dict(m)
            mk = normalize_cargo(m.get("cargo") or "socio")
            nm["cargo"] = mk
            if not nm.get("label"):
                nm["label"] = cargo_label(mk)
            if nm.get("orgao") is None:
                nm["orgao"] = orgao_of_cargo(mk)
            new_history.append(nm)
        if new_history != history:
            changes["cargo_history"] = new_history

    return changes


def _summarize_change(doc: dict, changes: dict) -> str:
    parts = []
    if "cargo" in changes:
        parts.append(f"cargo: {doc.get('cargo')!r} -> {changes['cargo']!r}")
    if "orgao" in changes:
        parts.append(f"orgao: {doc.get('orgao')!r} -> {changes['orgao']!r}")
    if "account_type" in changes:
        parts.append(f"account_type: <ausente> -> {changes['account_type']!r}")
    if "member_category" in changes:
        parts.append(f"member_category: <ausente> -> {changes['member_category']!r}")
    if "cargo_history" in changes:
        parts.append(f"cargo_history: {len(changes['cargo_history'])} entrada(s) normalizada(s)")
    return "; ".join(parts)


async def run(apply: bool):
    from database import close_pool, db  # import tardio: só liga à DB ao correr

    users = await db.users.find({}, {"_id": 0}).to_list(None)
    total = len(users)
    planned = [(u, plan_user_changes(u)) for u in users]
    to_change = [(u, c) for u, c in planned if c]

    print("=" * 70)
    print(f"  Migração de governança — {total} utilizadores analisados")
    print(f"  {len(to_change)} com alterações | {total - len(to_change)} já canónicos")
    print("=" * 70)
    for u, c in to_change:
        flag = " [TÉCNICA]" if u.get("account_type") == "technical" else ""
        print(f"  • {u.get('email', u.get('id'))}{flag}")
        print(f"      {_summarize_change(u, c)}")

    if not to_change:
        print("  Nada a migrar — tudo já em forma canónica.")

    if not apply:
        print("-" * 70)
        print("  DRY-RUN: nenhuma escrita efectuada. Use --apply --confirm para aplicar.")
        await close_pool()
        return

    print("-" * 70)
    print(f"  A APLICAR {len(to_change)} alteracao(oes)...")
    applied = 0
    for u, c in to_change:
        await db.users.update_one({"id": u["id"]}, {"$set": c})
        applied += 1
    print(f"  OK: {applied} utilizador(es) actualizado(s).")
    await close_pool()


def main():
    # Windows: força UTF-8 no stdout para não rebentar com acentos/símbolos.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001 — best-effort; não crítico
        pass

    parser = argparse.ArgumentParser(description="Migracao de cargos para keys canonicas (spec-governanca, seccao 16).")
    parser.add_argument("--apply", action="store_true", help="Escreve as alteracoes na DB (default: dry-run).")
    parser.add_argument("--confirm", action="store_true", help="Confirmacao obrigatoria para --apply.")
    args = parser.parse_args()

    if args.apply and not args.confirm:
        print("AVISO: --apply ESCREVE em `users` (STOP condition). Requer tambem --confirm.")
        print("       Faca backup da DB antes. Para ver o que mudaria, corra sem flags (dry-run).")
        sys.exit(2)

    asyncio.run(run(apply=args.apply))


if __name__ == "__main__":
    main()
