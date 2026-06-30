#!/usr/bin/env python3
"""
Auditoria de ficheiros de upload órfãos (não referenciados em nenhuma tabela).

Porquê: a limpeza reativa (helpers.delete_upload_file, ligada a delete de
user/benefício/galeria) trata ficheiros NOVOS. Este script é a rede de
segurança para o BACKLOG já acumulado (avatars/logos/documents antigos que
ficaram no disco antes da limpeza existir).

Segurança (conservador por design):
  • DRY-RUN por defeito — só lista. É preciso `--delete` para apagar.
  • Um ficheiro só é "órfão" se a sua URL `/uploads/<cat>/<nome>` NÃO aparecer
    em NENHUMA linha de NENHUMA tabela (scan ao `doc::text` inteiro — apanha
    qualquer campo/forma, mesmo `proofs` cuja linkagem não está num campo fixo).
  • `--min-age-hours` (default 24): ignora ficheiros recentes (evita corrida
    com uploads em curso ou registos ainda não persistidos).
  • `proofs`: NUNCA apagado a menos que `--include-proofs` (linkagem incerta).

Uso:
  python scripts/find_orphan_uploads.py                 # relatório (dry-run)
  python scripts/find_orphan_uploads.py --delete        # apaga órfãos (exceto proofs)
  python scripts/find_orphan_uploads.py --delete --include-proofs --min-age-hours 48

Requer DATABASE_URL (lê backend/.env, como create_admin.py). No sandbox web o
egress Postgres está bloqueado — correr no VPS/host de deploy.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

_HERE = os.path.dirname(os.path.abspath(__file__))
# `database.py` vive em `backend/` no layout do repo (scripts/ + backend/
# irmãos) OU em `/app` dentro do container (Dockerfile: COPY backend/ ./
# + COPY scripts/ ./scripts/, logo o script fica em /app/scripts/).
_BACKEND_DIR = next(
    (
        os.path.abspath(p)
        for p in (os.path.join(_HERE, "..", "backend"), os.path.join(_HERE, ".."))
        if os.path.isfile(os.path.join(p, "database.py"))
    ),
    None,
)
if _BACKEND_DIR is None:
    sys.exit(
        "ERRO: database.py não encontrado (nem ../backend nem ..). Correr do repo ou via `docker compose exec backend`."
    )

load_dotenv(
    os.path.join(_BACKEND_DIR, ".env")
)  # no-op se ausente (container usa env_file)
sys.path.insert(0, _BACKEND_DIR)

from database import COLLECTIONS, UPLOAD_DIR, close_pool, get_pool  # noqa: E402

# Categorias auditáveis e o que sabemos sobre a sua linkagem.
AUDITABLE = ("avatars", "logos", "documents", "gallery", "proofs")
URL_RE = re.compile(r"/uploads/[A-Za-z0-9_.\-/]+")
_IDENT_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


def _human(n: int) -> str:
    f = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if f < 1024 or unit == "GB":
            return f"{f:.1f}{unit}"
        f /= 1024
    return f"{f:.1f}GB"


async def collect_referenced_urls() -> set[str]:
    """Uma passagem por tabela: extrai todas as ocorrências de `/uploads/...`
    do doc inteiro. Filtra no servidor (`doc::text LIKE '%/uploads/%'`) para só
    trazer as linhas relevantes — O(linhas) total e barato em memória.

    Usa `fetch` e NÃO `cursor`: o pooler do Supabase (pgbouncer, transaction
    mode) não suporta os prepared statements/portais que o cursor exige
    (rebenta com `DuplicatePreparedStatementError`). O pool é criado com
    `statement_cache_size=0`, com o qual `fetch` é pgbouncer-safe."""
    referenced: set[str] = set()
    pool = await get_pool()
    async with pool.acquire() as conn:
        for table in COLLECTIONS:
            if not _IDENT_RE.match(table):  # defesa: COLLECTIONS é constante confiável
                continue
            q = f"SELECT doc::text AS d FROM \"{table}\" WHERE doc::text LIKE '%/uploads/%'"
            for record in await conn.fetch(q):
                d = record["d"]
                if d:
                    referenced.update(URL_RE.findall(d))
    return referenced


def scan_disk(min_age_seconds: float) -> dict[str, list[tuple[Path, str, int]]]:
    """Devolve {categoria: [(path, url, size), ...]} para ficheiros mais
    velhos que min_age_seconds."""
    now = time.time()
    out: dict[str, list[tuple[Path, str, int]]] = {}
    for cat in AUDITABLE:
        cat_dir = UPLOAD_DIR / cat
        if not cat_dir.is_dir():
            continue
        items: list[tuple[Path, str, int]] = []
        for fp in cat_dir.rglob("*"):
            if not fp.is_file() or fp.is_symlink():
                continue
            try:
                st = fp.stat()
            except OSError:
                continue
            if now - st.st_mtime < min_age_seconds:
                continue  # demasiado recente — não arriscar
            rel = fp.relative_to(UPLOAD_DIR).as_posix()
            items.append((fp, f"/uploads/{rel}", st.st_size))
        if items:
            out[cat] = items
    return out


async def main() -> int:
    ap = argparse.ArgumentParser(
        description="Audita/limpa uploads órfãos do Portal ACCTA."
    )
    ap.add_argument(
        "--delete", action="store_true", help="Apaga os órfãos (default: só lista)."
    )
    ap.add_argument(
        "--include-proofs",
        action="store_true",
        help="Inclui a categoria proofs no delete (linkagem incerta — usar com cuidado).",
    )
    ap.add_argument(
        "--min-age-hours",
        type=float,
        default=24.0,
        help="Ignora ficheiros mais novos que isto (default 24h).",
    )
    args = ap.parse_args()

    min_age_seconds = max(0.0, args.min_age_hours) * 3600
    disk = scan_disk(min_age_seconds)
    if not disk:
        print("Nenhum ficheiro de upload elegível encontrado.")
        await close_pool()
        return 0

    referenced = await collect_referenced_urls()

    total_orphans = 0
    total_bytes = 0
    deleted = 0
    print(f"{'CATEGORIA':<12} {'FICHEIROS':>9} {'ÓRFÃOS':>7} {'RECUPERÁVEL':>12}")
    print("-" * 46)
    for cat, items in sorted(disk.items()):
        orphans = [(fp, url, sz) for (fp, url, sz) in items if url not in referenced]
        cat_bytes = sum(sz for _, _, sz in orphans)
        total_orphans += len(orphans)
        total_bytes += cat_bytes
        print(f"{cat:<12} {len(items):>9} {len(orphans):>7} {_human(cat_bytes):>12}")

        for fp, url, sz in orphans:
            tag = ""
            do_delete = args.delete
            if cat == "proofs" and not args.include_proofs:
                do_delete = False
                tag = "  [proofs: requer --include-proofs]"
            if do_delete:
                try:
                    fp.unlink()
                    deleted += 1
                    print(f"   APAGADO  {url} ({_human(sz)})")
                except OSError as e:
                    print(f"   ERRO     {url}: {e}")
            else:
                print(f"   ÓRFÃO    {url} ({_human(sz)}){tag}")

    print("-" * 46)
    mode = "APAGADOS" if args.delete else "DRY-RUN (nada apagado — usar --delete)"
    print(f"Total órfãos: {total_orphans} | Espaço: {_human(total_bytes)} | {mode}")
    if args.delete:
        print(f"Ficheiros apagados: {deleted}")

    await close_pool()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
