#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Alerta de espaço em disco do VPS ACCTA.
#
# Alerta quando o uso de / passar do limite (default 85%). Sem webhook, escreve
# para stdout — o cron envia por email qualquer output (configure MAILTO).
#
# Variáveis:
#   DISK_ALERT_THRESHOLD  limite em % (default 85)
#   MOUNT                 ponto de montagem a vigiar (default /)
#   UPLOADS_DIR           pasta de uploads p/ reportar tamanho (default /srv/accta/uploads)
#   ALERT_WEBHOOK_URL     (opcional) URL p/ POST do alerta (Slack/Discord/Telegram/genérico)
#   ALERT_WEBHOOK_FIELD   campo JSON do texto (default "text"; use "content" p/ Discord)
#
# Cron sugerido (cada 30 min):
#   */30 * * * * /srv/accta/repo/scripts/check_disk_space.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

THRESHOLD="${DISK_ALERT_THRESHOLD:-85}"
MOUNT="${MOUNT:-/}"
UPLOADS_DIR="${UPLOADS_DIR:-/srv/accta/uploads}"

USE_PCT="$(df --output=pcent "${MOUNT}" 2>/dev/null | awk 'NR==2 {gsub("%",""); gsub(" ",""); print}')"
if [[ -z "${USE_PCT:-}" ]]; then
  echo "ERRO: não foi possível ler o uso de disco de ${MOUNT}" >&2
  exit 2
fi

UPLOADS_SIZE="n/a"
if [[ -d "${UPLOADS_DIR}" ]]; then
  UPLOADS_SIZE="$(du -sh "${UPLOADS_DIR}" 2>/dev/null | cut -f1 || echo n/a)"
fi

if [[ "${USE_PCT}" -ge "${THRESHOLD}" ]]; then
  MSG="⚠️ VPS accta: disco ${MOUNT} a ${USE_PCT}% (limite ${THRESHOLD}%). uploads/=${UPLOADS_SIZE}"
  echo "${MSG}"
  if [[ -n "${ALERT_WEBHOOK_URL:-}" ]]; then
    FIELD="${ALERT_WEBHOOK_FIELD:-text}"
    # --data-urlencode evita partir o JSON se a msg tiver caracteres especiais.
    curl -fsS -m 10 -X POST "${ALERT_WEBHOOK_URL}" \
      -H "Content-Type: application/json" \
      --data "$(printf '{"%s":"%s"}' "${FIELD}" "${MSG}")" \
      >/dev/null || echo "AVISO: falha ao enviar alerta para o webhook" >&2
  fi
  exit 1
fi

# Silencioso quando OK (não poluir email do cron). Descomente para verbose:
# echo "OK: disco ${MOUNT} a ${USE_PCT}% (< ${THRESHOLD}%). uploads/=${UPLOADS_SIZE}"
exit 0
