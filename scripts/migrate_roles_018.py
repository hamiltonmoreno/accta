#!/usr/bin/env python3
"""
Migração do modelo de acessos (spec 018, US2) — roles legados → modelo novo.

Converte os utilizadores com `role` legado (financeiro/moderador) para o
modelo consolidado {admin, socio} com equivalência de acesso:

- Cria (se em falta) as funções personalizadas seed «Financeiro»/«Moderador»
  (privilégios de `governance.LEGACY_ROLE_SEEDS`, derivados da matriz de
  acessos) — inserção direta na coleção, fora da API.
- Regra R3 por utilizador:
    * privilégios atuais ⊆ privilégios da seed → socio + `custom_role_id` da
      seed (ligação viva da spec 017; privilégios materializados = seed).
    * caso contrário (extras manuais)         → socio + privilégios diretos =
      união(atuais, seed), SEM função — preserva o invariante de propagação
      da 017 (holder de função tem exatamente os privilégios dela).
- Backup JSON pré-migração (estado before de cada utilizador afetado).
- Audit log `role_model_migrated` por utilizador com before/after + regra.
- Idempotente: re-correr não altera nada (role=socio já não casa).
- `--restore <backup.json>` repõe o estado before de cada utilizador
  (caminho de rollback exercitável — finding M3), auditado.

Uso:
    python scripts/migrate_roles_018.py                      # dry-run (default)
    python scripts/migrate_roles_018.py --apply --confirm    # aplica de facto
    python scripts/migrate_roles_018.py --restore backup.json --confirm

⚠️  STOP CONDITION: `--apply`/`--restore` ESCREVEM em `users`/`custom_roles`.
    Exigem `--confirm` + confirmação explícita do dono (cerimónia de release).
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from governance import LEGACY_ROLE_SEEDS  # noqa: E402

# Campos de acesso que a migração toca (e que o backup/restore preserva).
ACCESS_FIELDS = ("role", "privileges", "custom_role_id")


def plan_user_migration(doc: dict, seed_ids: dict) -> dict | None:
    """PURA (sem DB): devolve {"set": {...}, "regra": "seed"|"privilegios_diretos"}
    para um user doc com role legado, ou None se nada a migrar (idempotente).
    `seed_ids` = {"financeiro": <id da seed>, "moderador": <id>}.
    Aplica-se a QUALQUER status (incl. pendente_convite/pendente_aprovacao)."""
    role = doc.get("role")
    seed_def = LEGACY_ROLE_SEEDS.get(role or "")
    if not seed_def:
        return None
    current = list(doc.get("privileges") or [])
    seed_privs = list(seed_def["privileges"])
    if set(current) <= set(seed_privs):
        return {
            "set": {"role": "socio", "privileges": seed_privs, "custom_role_id": seed_ids[role]},
            "regra": "seed",
        }
    # Extras manuais: união sem duplicados (ordem: seed primeiro, extras depois),
    # SEM função — o invariante da 017 (privilégios do holder == os da função)
    # não se pode quebrar.
    union = seed_privs + [p for p in current if p not in seed_privs]
    return {
        "set": {"role": "socio", "privileges": union, "custom_role_id": None},
        "regra": "privilegios_diretos",
    }


async def ensure_seeds(db) -> dict:
    """Garante as funções seed na coleção (inserção direta, fora da API).
    Devolve {"financeiro": <id>, "moderador": <id>}."""
    from models import CustomRole

    seed_ids: dict = {}
    for role, seed_def in LEGACY_ROLE_SEEDS.items():
        existing = await db.custom_roles.find_one({"name": seed_def["name"]}, {"_id": 0})
        if existing:
            seed_ids[role] = existing["id"]
            continue
        doc = CustomRole(
            name=seed_def["name"],
            description="Função seed da migração do modelo de acessos (spec 018)",
            privileges=list(seed_def["privileges"]),
            created_by="system",
        ).model_dump()
        await db.custom_roles.insert_one(doc)
        seed_ids[role] = doc["id"]
        print(f"  + Função seed criada: «{seed_def['name']}» ({doc['id']})")
    return seed_ids


async def migrate(db, apply: bool, backup_path: str) -> None:
    from helpers import create_audit_log

    seed_ids: dict = {}
    if apply:
        seed_ids = await ensure_seeds(db)
    else:
        # dry-run não escreve: usa os ids existentes ou um marcador legível
        for role, seed_def in LEGACY_ROLE_SEEDS.items():
            existing = await db.custom_roles.find_one({"name": seed_def["name"]}, {"_id": 0})
            seed_ids[role] = existing["id"] if existing else f"<seed «{seed_def['name']}» a criar>"

    users = await db.users.find(
        {"role": {"$in": list(LEGACY_ROLE_SEEDS)}}, {"_id": 0, "password": 0}
    ).to_list(None)
    planned = [(u, plan_user_migration(u, seed_ids)) for u in users]
    to_change = [(u, p) for u, p in planned if p]

    print("=" * 70)
    print(f"  Migração de roles (spec 018) — {len(users)} utilizador(es) com role legado")
    print("=" * 70)
    for u, p in to_change:
        print(f"  • {u.get('email', u.get('id'))} [{u.get('status')}]")
        print(f"      {u.get('role')!r} + {sorted(u.get('privileges') or [])}")
        print(f"      → socio + {p['set']['privileges']} (regra: {p['regra']}, "
              f"função: {p['set']['custom_role_id']})")

    if not to_change:
        print("  Nada a migrar — nenhum utilizador com role legado.")

    if not apply:
        print("-" * 70)
        print("  DRY-RUN: nenhuma escrita efectuada. Use --apply --confirm para aplicar.")
        return

    # Backup before (só os afetados; campos de acesso + identificação).
    backup = [
        {"id": u["id"], "email": u.get("email"), **{f: u.get(f) for f in ACCESS_FIELDS}}
        for u, _ in to_change
    ]
    with open(backup_path, "w", encoding="utf-8") as fh:
        json.dump(backup, fh, ensure_ascii=False, indent=2)
    print("-" * 70)
    print(f"  Backup pré-migração: {backup_path} ({len(backup)} utilizador(es))")

    for u, p in to_change:
        await db.users.update_one({"id": u["id"]}, {"$set": p["set"]})
        await create_audit_log(
            "system",
            "role_model_migrated",
            u["id"],
            details={
                "before": {f: u.get(f) for f in ACCESS_FIELDS},
                "after": p["set"],
                "regra": p["regra"],
                "spec": "018",
            },
        )
    print(f"  OK: {len(to_change)} utilizador(es) migrado(s).")


async def restore(db, backup_path: str) -> None:
    from helpers import create_audit_log

    with open(backup_path, encoding="utf-8") as fh:
        backup = json.load(fh)
    print(f"  A REPOR {len(backup)} utilizador(es) do backup {backup_path}...")
    restored = 0
    for entry in backup:
        set_fields = {f: entry.get(f) for f in ACCESS_FIELDS}
        result = await db.users.update_one({"id": entry["id"]}, {"$set": set_fields})
        if getattr(result, "modified_count", 1):
            restored += 1
        await create_audit_log(
            "system",
            "role_model_migration_restored",
            entry["id"],
            details={"restored": set_fields, "spec": "018"},
        )
    print(f"  OK: {restored} utilizador(es) repostos. (As funções seed ficam — inofensivas.)")


async def run(args) -> None:
    from database import close_pool, db  # import tardio: só liga à DB ao correr

    try:
        if args.restore:
            await restore(db, args.restore)
        else:
            await migrate(db, apply=args.apply, backup_path=args.backup)
    finally:
        await close_pool()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001 — best-effort; não crítico
        pass

    default_backup = f"backup-roles-018-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json"
    parser = argparse.ArgumentParser(description="Migracao de roles legados para o modelo {admin, socio} (spec 018).")
    parser.add_argument("--apply", action="store_true", help="Escreve as alteracoes na DB (default: dry-run).")
    parser.add_argument("--confirm", action="store_true", help="Confirmacao obrigatoria para --apply/--restore.")
    parser.add_argument("--restore", metavar="BACKUP_JSON", help="Repoe o estado before a partir do backup.")
    parser.add_argument("--backup", default=default_backup, help="Caminho do backup JSON pre-migracao.")
    args = parser.parse_args()

    if (args.apply or args.restore) and not args.confirm:
        print("AVISO: --apply/--restore ESCREVEM em `users`/`custom_roles` (STOP condition).")
        print("       Requerem tambem --confirm. Para ver o que mudaria, corra sem flags (dry-run).")
        sys.exit(2)

    asyncio.run(run(args))


if __name__ == "__main__":
    main()
