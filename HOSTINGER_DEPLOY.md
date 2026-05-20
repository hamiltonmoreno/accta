# Checklist de Deploy — Hostinger VPS (ACCTA)

> Guia prático, passo-a-passo, para pôr o Portal ACCTA a correr no seu VPS da Hostinger.
> Cada bloco de comandos pode ser copiado diretamente para o terminal SSH.

---

## Pré-requisitos
- VPS Hostinger com **Ubuntu 22.04 ou 24.04** (painel hPanel → VPS → reinstalar SO se necessário)
- Domínio apontado para o IP do VPS (ex: `controlador.cv` → A record → IP do VPS)
- Acesso SSH como `root` (`ssh root@SEU_IP`)

---

## ✅ Etapa 1 — Preparar o VPS (executar UMA vez)

### 1.1 Atualizar sistema e criar utilizador `deploy`
```bash
apt update && apt upgrade -y
adduser deploy                         # define uma password forte
usermod -aG sudo deploy
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy  # copia chaves SSH
```

### 1.2 Instalar dependências
```bash
# Python 3.11 + Node 20 + Nginx + Supervisor + Certbot + cliente PostgreSQL
# Base de dados: Supabase/PostgreSQL (gerida) — só o cliente (pg_dump), sem servidor de BD no VPS
apt install -y software-properties-common curl gnupg git supervisor nginx certbot python3-certbot-nginx postgresql-client

# Python 3.11
add-apt-repository ppa:deadsnakes/ppa -y
apt install -y python3.11 python3.11-venv python3-pip

# Node.js 20 + Yarn
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
npm install -g yarn
```

> A base de dados é o **Supabase** (PostgreSQL gerido). Não há MongoDB nem
> qualquer servidor de BD a instalar no VPS — a app liga-se via `DATABASE_URL`
> (URI do connection pooler do Supabase, porta `6543`, transaction mode).

### 1.3 Firewall
```bash
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable
```

---

## ✅ Etapa 2 — Clonar e configurar a aplicação

### 2.1 Passar para o utilizador `deploy` e clonar
```bash
su - deploy
sudo mkdir -p /app && sudo chown deploy:deploy /app
cd /app
git clone https://github.com/SEU_USER/SEU_REPO.git .
```

### 2.2 Criar `.env` do backend
```bash
cat > /app/backend/.env <<'EOF'
DATABASE_URL=postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
SECRET_KEY=COLOCAR_AQUI_UMA_CHAVE_FORTE
CORS_ORIGINS=https://controlador.cv
RESEND_API_KEY=re_xxxxxxxxxxxxx
EMAIL_FROM=noreply@controlador.cv
FRONTEND_URL=https://controlador.cv
EOF
```

> Gere `SECRET_KEY` com: `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`

### 2.3 Criar `.env` do frontend
```bash
cat > /app/frontend/.env <<'EOF'
REACT_APP_BACKEND_URL=https://controlador.cv
EOF
```

### 2.4 Instalar dependências e fazer build
```bash
cd /app/backend
python3.11 -m venv venv
./venv/bin/pip install -r requirements.txt

cd /app/frontend
yarn install --frozen-lockfile
yarn build
```

### 2.5 Criar primeiro admin
```bash
cd /app
./backend/venv/bin/python scripts/create_admin.py
# Siga o prompt para definir email + password do admin
```

---

## ✅ Etapa 3 — Nginx (proxy reverso + SSL)

### 3.1 Instalar a configuração (ficheiro versionado)

A configuração canónica está versionada no repo em **`deploy/nginx/accta.conf`**
(não copiar/colar inline — usar o ficheiro, manter os dois em sync):

```bash
sudo cp /app/deploy/nginx/accta.conf /etc/nginx/sites-available/accta
sudo ln -sf /etc/nginx/sites-available/accta /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

O que mudou face à versão antiga (proxy puro):

- **Uploads públicos servidos pelo nginx** (`alias /srv/accta/uploads/`,
  `expires 7d`, `X-Content-Type-Options nosniff`) — liberta o worker uvicorn.
  Requer o bind-mount da **Etapa 3.5**.
- **`/uploads/documents/` → `return 404`**: documentos NUNCA são servidos do
  disco; o RBAC continua em `/api/documents/{id}/download`. Espelha o
  `UploadsStaticFiles` em `backend/server.py`.
- **`client_max_body_size 12M`** (era 20M): folga acima do maior limite de
  upload (documents = 10MB). Se subir o limite no backend, subir aqui também.
- Headers de proxy explícitos (sem `include proxy_params`, que só existe em
  Debian/Ubuntu).

### 3.2 Ativar HTTPS (Let's Encrypt)
```bash
sudo certbot --nginx -d controlador.cv -d www.controlador.cv
# Responde: email → aceita termos → redirecionar HTTP→HTTPS (opção 2)
```

> Renovação automática já está ativa via `systemctl status certbot.timer`.
> **HTTPS é obrigatório**: o backend usa cookie de sessão `SameSite=None; Secure`
> — sem TLS o browser não envia o cookie e o login parte.

---

## ✅ Etapa 3.5 — Uploads: bind-mount + migração (Docker Compose)

Para o nginx servir `/uploads/` directamente, os ficheiros têm de estar numa
pasta do **host** (`/srv/accta/uploads`), não num volume nomeado do Docker.
O `docker-compose.yml` já aponta para o bind-mount; falta criar a pasta e
**migrar os ficheiros existentes** (senão os uploads já enviados desaparecem).

> ⚠️ **Permissões**: o `backend/Dockerfile` não define `USER` → o container
> corre como **root (UID 0)**, logo os ficheiros são gravados `root:root`.
> A pasta no host tem de ser **`chmod 755`** (não 750): o nginx corre como
> `www-data` — com 750 e dono `root`, o `www-data` leva **403**. 755 dir +
> 644 ficheiros é seguro aqui (uploads públicos), nunca 777.

```bash
# 1. Backup preventivo do estado atual (do volume nomeado antigo)
docker cp accta-backend:/app/uploads ./uploads-backup-$(date +%F)

# 2. Criar a pasta no host com dono/permissões corretos (container = root)
sudo mkdir -p /srv/accta/uploads
sudo chown -R root:root /srv/accta/uploads
sudo chmod 755 /srv/accta/uploads

# 3. Migrar os uploads existentes para a nova localização
sudo cp -a ./uploads-backup-*/. /srv/accta/uploads/

# 4. Recriar o container (docker-compose.yml já tem o bind-mount)
cd /docker/accta            # onde está o docker-compose.yml gerido
docker compose down
docker compose up -d
docker compose logs -f backend     # confirmar arranque

# 5. Recarregar o nginx (config da Etapa 3.1)
sudo nginx -t && sudo systemctl reload nginx
```

**Testes de aceitação** (após migrar):

- Upload de um logo (admin) → o ficheiro aparece em `/srv/accta/uploads/logos/`.
- `GET https://controlador.cv/uploads/logos/<uuid>.png` → **200**, servido pelo
  nginx (header `X-Content-Type-Options: nosniff`, `Cache-Control` de 7d).
- `GET https://controlador.cv/uploads/documents/<uuid>.pdf` → **404** (bloqueado).
- `GET /api/documents/<id>/download` com sessão válida → **200** (pela API/RBAC).

---

## ✅ Etapa 4 — Supervisor (serviço do backend)

```bash
sudo tee /etc/supervisor/conf.d/accta-backend.conf <<'EOF'
[program:backend]
command=/app/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2
directory=/app/backend
user=deploy
autostart=true
autorestart=true
stdout_logfile=/var/log/supervisor/backend.out.log
stderr_logfile=/var/log/supervisor/backend.err.log
environment=PATH="/app/backend/venv/bin:%(ENV_PATH)s"
EOF

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status backend
```

Teste:
```bash
curl https://controlador.cv/api/
# Esperado: {"message":"ACCTA Portal API v1.0"}
```

---

## ✅ Etapa 5 — Configurar deploy automático (GitHub Actions)

### 5.1 Gerar chave SSH para o deploy (na sua máquina local OU no próprio VPS)
```bash
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/accta_deploy
# Adicionar a chave PÚBLICA ao VPS:
cat ~/.ssh/accta_deploy.pub | ssh deploy@SEU_IP "cat >> ~/.ssh/authorized_keys"
```

### 5.2 No GitHub: **Settings → Secrets and variables → Actions** — adicionar:

| Secret | Valor |
|--------|-------|
| `DEPLOY_HOST` | IP do seu VPS Hostinger |
| `DEPLOY_USER` | `deploy` |
| `DEPLOY_SSH_KEY` | Conteúdo **completo** de `~/.ssh/accta_deploy` (chave privada) |
| `DEPLOY_PORT` | `22` (ou a porta SSH que configurou) |
| `DEPLOY_APP_DIR` | `/app` |
| `PRODUCTION_URL` | `https://controlador.cv` |

### 5.3 Permitir ao `deploy` reiniciar o supervisor sem password
```bash
sudo visudo -f /etc/sudoers.d/deploy-supervisor
# Adicionar a linha:
deploy ALL=(ALL) NOPASSWD: /usr/bin/supervisorctl
```

### 5.4 Teste o pipeline
```bash
git push origin main
# → Vá a GitHub → Actions → veja "CD — Deploy to Production"
```

---

## ✅ Etapa 6 — Backup, monitorização e limpeza (cron)

Scripts versionados em `scripts/` (assumir o repo em `/app`; ajustar o caminho).

**6.1 Backup diário dos uploads** (rsync espelhado, com guard anti-vazio):

```bash
# 0. (uma vez) chave SSH do VPS → host de backup, e testar:
DRY_RUN=1 BACKUP_DEST="backup@HOST:/backups/accta/uploads/" /app/scripts/backup_uploads.sh

# cron (3h da manhã). `crontab -e`:
0 3 * * * BACKUP_DEST="backup@HOST:/backups/accta/uploads/" /app/scripts/backup_uploads.sh >> /var/log/accta-backup.log 2>&1
```

> ⚠️ `rsync --delete` é **espelho**, não versão. Para retenção/snapshots
> (recuperar de apagar/corromper por engano) considerar `restic`/`borg`.
> **Uploads sem a BD são inúteis** — no mesmo ciclo, fazer o dump do Supabase
> (ver "Comandos úteis" → `pg_dump`) e enviar ambos para o backup.

**6.2 Alerta de espaço em disco** (cada 30 min; alerta ≥85% + tamanho de uploads):

```bash
# Opcional: ALERT_WEBHOOK_URL para Slack/Discord/Telegram (senão, email do cron).
*/30 * * * * /app/scripts/check_disk_space.sh
```

**6.3 Limpeza de uploads órfãos** (rede de segurança p/ o backlog antigo):

A limpeza reativa já apaga o ficheiro quando se remove user/benefício/foto.
Este script trata órfãos **antigos** — **dry-run por defeito**, conservador
(só apaga o que não está referenciado em nenhuma tabela):

```bash
docker compose exec backend python /app/scripts/find_orphan_uploads.py            # relatório
docker compose exec backend python /app/scripts/find_orphan_uploads.py --delete   # aplicar
# proofs (linkagem incerta) só com --include-proofs
```

---

## 🧪 Comandos úteis do dia-a-dia

```bash
# Ver logs do backend ao vivo
sudo tail -f /var/log/supervisor/backend.err.log

# Ver logs do Nginx
sudo tail -f /var/log/nginx/error.log

# Reiniciar serviços manualmente
sudo supervisorctl restart backend
sudo systemctl reload nginx

# Backup da base de dados — o Supabase faz backups automáticos (painel do projeto).
# Dump manual (postgresql-client é instalado na Etapa 1.2); carrega DATABASE_URL do .env:
set -a; . /app/backend/.env; set +a
pg_dump "$DATABASE_URL" -Fc -f /home/deploy/backups/$(date +%F).dump

# Verificar SSL
sudo certbot certificates
```

---

## 🚨 Troubleshooting

| Sintoma | Causa provável | Solução |
|---------|----------------|---------|
| `502 Bad Gateway` | Backend não arrancou | `sudo supervisorctl status` e ler logs |
| Email de convite não chega | Domínio não verificado no Resend | Validar DNS `controlador.cv` no dashboard Resend (resend.com/domains). Enquanto não estiver validado, o link aparece na resposta da API |
| SSE desliga em ~60s | Timeout do Nginx | Confirmar `proxy_read_timeout 24h` no bloco `/api/` |
| `CORS error` no frontend | `CORS_ORIGINS` não coincide | Ajustar em `/app/backend/.env` e reiniciar backend |
| Build do frontend falha | Falta memória no VPS | Hostinger plano básico: `sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile` |

---

## ✅ Checklist final antes de abrir ao público

- [ ] `https://controlador.cv` carrega a homepage
- [ ] `https://controlador.cv/api/` devolve JSON
- [ ] SSL válido (cadeado verde no browser)
- [ ] Login do admin funciona
- [ ] Admin consegue enviar convite e email chega (após validar domínio no Resend)
- [ ] Notificações em tempo real funcionam (testar numa conta logada)
- [ ] Backups da base de dados confirmados (automáticos no painel Supabase)
- [ ] GitHub Actions faz deploy verde após push para `main`

---

**Dúvida rápida?** Os ficheiros-chave são:
- Pipeline CI/CD: `/app/.github/workflows/deploy.yml`
- Guia genérico: `/app/DEPLOY.md`
- Este checklist Hostinger: `/app/HOSTINGER_DEPLOY.md`
