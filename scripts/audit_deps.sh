#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Auditoria de dependências ACCTA (spec 019, WS-G / FR-019).
#
# Gate LOCAL de vulnerabilidades — independente do CI (billing-locked) e do
# Dependabot (que corre na infra do GitHub). Corre pip-audit no backend e o
# audit do yarn no frontend. Sai != 0 se encontrar HIGH/CRITICAL alcançável.
#
# Uso:
#   bash scripts/audit_deps.sh              # backend + frontend
#   AUDIT_SKIP_FRONTEND=1 bash scripts/audit_deps.sh   # só backend
#
# Requer: pip-audit (pip install pip-audit) e yarn. Onde faltarem, a secção
# é saltada com aviso (não falha o script por ferramenta ausente).
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
rc=0

echo "== pip-audit (backend/requirements.txt) =="
if command -v pip-audit >/dev/null 2>&1; then
    pip-audit -r "$ROOT/backend/requirements.txt" --desc on || rc=1
else
    echo "AVISO: pip-audit não instalado — 'pip install pip-audit' (secção saltada)"
fi

if [ "${AUDIT_SKIP_FRONTEND:-0}" != "1" ]; then
    echo
    echo "== yarn npm audit (frontend) =="
    if command -v yarn >/dev/null 2>&1; then
        # yarn npm audit devolve != 0 quando há vulnerabilidades; --severity high
        # filtra o ruído de low/moderate (a maioria transitivo do CRA — M-CRA).
        ( cd "$ROOT/frontend" && yarn npm audit --severity high --recursive ) || rc=1
    else
        echo "AVISO: yarn não instalado (secção saltada)"
    fi
fi

echo
if [ "$rc" -eq 0 ]; then
    echo "OK: sem vulnerabilidades HIGH/CRITICAL alcançáveis."
else
    echo "FALHOU: vulnerabilidades encontradas (ver acima) ou ferramenta em falta reportou erro."
fi
exit "$rc"
