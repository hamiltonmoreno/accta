"""Rebuild do snapshot do ranking de atuação (spec-ranking-socio F5).

Invocável por cron — corre `rebuild_scores` fora do request path dos sócios
(§2.4). Idempotente: cada execução substitui o snapshot do período.

Uso:
    python scripts/rebuild_ranking.py              # ano civil atual + "all"
    python scripts/rebuild_ranking.py 2026 2025    # períodos específicos
    python scripts/rebuild_ranking.py all          # só "desde sempre"

Cron (exemplo, diário às 03:00):
    0 3 * * *  cd /app && /app/backend/venv/bin/python scripts/rebuild_ranking.py
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

from database import close_pool  # noqa: E402
from ranking import rebuild_scores  # noqa: E402


async def main(periods: list[str]) -> int:
    if not periods:
        periods = [str(datetime.now(timezone.utc).year), "all"]
    failed = False
    try:
        for period_key in periods:
            try:
                members = await rebuild_scores(period_key)
                print(f"✓ ranking '{period_key}': {members} membros")
            except Exception as exc:  # noqa: BLE001 — cron deve continuar os restantes períodos
                failed = True
                print(f"✗ ranking '{period_key}': {exc}", file=sys.stderr)
    finally:
        await close_pool()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
