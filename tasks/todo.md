# Tarefa Ativa — Nginx reverse proxy + hardening de uploads (VPS)

Branch: `claude/nginx-reverse-proxy-setup-2G5ka`

Contexto: o backend serve `/uploads` via `app.mount` (uvicorn). Em produção
(Docker Compose, `controlador.cv`, container `accta-backend` em `127.0.0.1:8001`)
queremos o nginx a servir os ficheiros públicos directamente do disco, mantendo
`documents` atrás da API (RBAC). Também: limpeza de órfãos, backup e
monitorização de disco. Porta mantém-se **8001** (alinha com compose/Dockerfile/
deploy.yml — não re-portar para 8000).

## Plano (itens verificáveis)

### 1. Nginx reverse proxy (ponto 1)
- [x] Criar `deploy/nginx/accta.conf` versionado: serve frontend, proxy `/api/`
      (SSE-safe), bloqueia `^~ /uploads/documents/` (return 404, espelha
      `UploadsStaticFiles`), serve `^~ /uploads/` via `alias` do bind-mount,
      `expires 7d` + `X-Content-Type-Options nosniff`, `client_max_body_size 12M`.
- [x] `docker-compose.yml`: trocar volume nomeado `accta-uploads` por bind-mount
      `/srv/accta/uploads:/app/uploads` (nginx lê do host).
- [x] `HOSTINGER_DEPLOY.md`: apontar para o ficheiro versionado + migração
      one-time do volume nomeado (STOP: migração de dados — documentada, não
      executada por mim) + permissões.

### 2. Limpeza de órfãos (ponto 5)
- [x] Extrair `_safe_unlink_url` (gallery.py) → `helpers.delete_upload_file`.
- [x] `gallery.py`: importar do helper, remover cópia local, repor 3 call-sites.
- [x] `users.py` `delete_user`: apagar avatar (`photo_url`) ao remover user.
- [x] `benefits.py`: apagar logo ao apagar benefício + ao substituir `logo_url`.
- [x] `scripts/find_orphan_uploads.py`: auditoria conservadora — dry-run por
      defeito, `--delete` explícito, `--min-age-hours` (default 24), nunca
      apaga ficheiro cuja URL apareça em qualquer tabela; `proofs` requer
      `--include-proofs` (linkagem desconhecida).

### 3. Backup + monitorização (pontos 2 e 3)
- [x] `scripts/backup_uploads.sh`: rsync (`-az --delete --partial`) p/ destino
      configurável; recusa correr se a origem estiver vazia/ausente.
- [x] `scripts/check_disk_space.sh`: alerta se uso ≥ limite (default 85%) +
      tamanho de uploads + webhook opcional.
- [x] Documentar cron (backup 3h / disco 30min / órfãos) em `HOSTINGER_DEPLOY.md`.

### 4. Permissões VPS (ponto 4)
- [x] Documentado: container corre como **root** (Dockerfile sem USER) → host
      `chown root:root` + `chmod 755` (NÃO 750 — nginx www-data levaria 403).

### 5. Verificação
- [x] `backend/tests/test_orphan_cleanup.py` — 14/14 (helper + wiring).
- [x] `ruff check .` limpo; suite unit **388 passed, 0 failed** (o único
      collection-error, `test_activity_feed.py`, é pré-existente/ambiental —
      idêntico na baseline com as mudanças em stash).
- [ ] Commit, push, abrir PR.

## Notas / decisões
- Porta **8001** mantida (re-portar p/ 8000 seria mudança gratuita e quebraria
  compose/Dockerfile/healthcheck/docs).
- Bind-mount = risco de migração de dados (STOP condition) → documentado, não
  executado (não tenho acesso ao VPS; sandbox sem egress DB — L4).
- Sweep é dry-run por defeito e nunca apaga referenciados (L1: lógica
  desenhada+testada com mocks; scan live ao Supabase não validável aqui).

## Review
- **Nginx**: ficheiro versionado `deploy/nginx/accta.conf` (HTTP baseline;
  certbot adiciona TLS). Documents bloqueados a 404 — confirmado seguro: o
  download é por `/api/documents/{id}/download` (FileResponse), nunca por URL
  directa. Headers de proxy explícitos (portável fora de Debian/Ubuntu).
- **Bind-mount**: `docker-compose.yml` agora `/srv/accta/uploads:/app/uploads`.
  Migração one-time do volume nomeado documentada (STOP: dados — não executei,
  sem acesso ao VPS). Correção factual ao utilizador: container = **root**
  (Dockerfile sem USER), logo `chown root:root` + `chmod 755` (o 750/1000:1000
  sugerido daria 403 no nginx www-data).
- **Órfãos**: `_safe_unlink_url` → `helpers.delete_upload_file` (reutilizado em
  gallery; novo em users/benefits). Documents não têm endpoint DELETE → cobertos
  só pelo sweep. Sweep conservador (dry-run, age-gate, nunca apaga referenciado).
- **Verificação**: 388 unit pass / 0 fail; ruff limpo; comportamento
  diff-ado vs baseline (stash) — refactor sem regressões. Não validável aqui:
  scan live ao Supabase (egress DB bloqueado no sandbox — L4) e aplicação no VPS.
- **Decisão**: porta mantida em 8001 (não re-portar p/ 8000 — quebraria
  compose/Dockerfile/healthcheck/docs sem ganho).
- **Codex P2 (PR #47)**: o runbook usava `docker compose exec backend python
  /app/scripts/...` mas o `backend/Dockerfile` faz `COPY backend/ ./` →
  `scripts/` não estava na imagem. Fix: Dockerfile `COPY scripts/ ./scripts/`
  + bootstrap do `find_orphan_uploads.py` que localiza `database.py` em ambos
  os layouts (repo `../backend` / container `/app`). Verificado (ruff+compile+
  resolução de path nos 2 layouts).
- **CI (PR #47)**: 2 runs, ambos os jobs falham em ~3-4s; Frontend falha sem
  qualquer alteração frontend e o Vercel build passa → falha de infra
  Actions ao nível do repo/org, não do código. Não re-kickar mais.
