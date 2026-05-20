#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Backup da pasta de uploads do Portal ACCTA (rsync espelhado).
#
# Uso:
#   BACKUP_DEST="backup@HOST:/backups/accta/uploads/" ./scripts/backup_uploads.sh
#   ./scripts/backup_uploads.sh "backup@HOST:/backups/accta/uploads/"
#
# Cron sugerido (3h, baixo tráfego):
#   0 3 * * * BACKUP_DEST="backup@HOST:/backups/accta/uploads/" \
#             /srv/accta/repo/scripts/backup_uploads.sh >> /var/log/accta-backup.log 2>&1
#
# ⚠️ Uploads sem a BD (e vice-versa) são inúteis. Faça o pg_dump do Supabase
#    NO MESMO ciclo de backup (ver HOSTINGER_DEPLOY.md → "Comandos úteis").
# ⚠️ rsync --delete é ESPELHO, não versão: um ficheiro apagado/corrompido por
#    engano propaga-se ao backup. Para retenção/snapshots use restic ou borg
#    (incremental + histórico, custo extra mínimo) — recomendado a prazo.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

UPLOADS_DIR="${UPLOADS_DIR:-/srv/accta/uploads}"
BACKUP_DEST="${BACKUP_DEST:-${1:-}}"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { echo "[$(ts)] $*"; }

if [[ -z "${BACKUP_DEST}" ]]; then
  echo "ERRO: destino não definido. Use BACKUP_DEST=... ou passe como argumento." >&2
  echo "  ex: BACKUP_DEST='backup@host:/backups/accta/uploads/' $0" >&2
  exit 2
fi

# Guard crítico: se a origem não existir ou estiver VAZIA (ex.: bind-mount não
# montado), abortar — caso contrário `--delete` apagaria o backup inteiro.
if [[ ! -d "${UPLOADS_DIR}" ]]; then
  log "ERRO: origem ${UPLOADS_DIR} não existe — abortado (backup protegido)."
  exit 3
fi
if ! find "${UPLOADS_DIR}" -mindepth 1 -print -quit | grep -q .; then
  log "ERRO: origem ${UPLOADS_DIR} está vazia — abortado (não espelhar vazio sobre o backup)."
  exit 3
fi

RSYNC_OPTS=(-az --delete --partial --human-readable --stats --timeout=120)
if [[ "${DRY_RUN:-0}" == "1" ]]; then
  RSYNC_OPTS+=(--dry-run -v)
  log "DRY-RUN: nenhuma alteração será escrita no destino."
fi

log "Backup: ${UPLOADS_DIR}/ → ${BACKUP_DEST}"
rsync "${RSYNC_OPTS[@]}" "${UPLOADS_DIR}/" "${BACKUP_DEST}"
log "Backup concluído com sucesso."
