# Checklist de Deploy — Hostinger VPS (ACCTA)

> Guia prático, passo-a-passo, para pôr o **backend** do Portal ACCTA a correr
> no VPS da Hostinger. O **frontend é servido pela Vercel** (deploy automático;
> ver [VERCEL_DEPLOY.md](VERCEL_DEPLOY.md)) — este guia trata só do backend.
>
> A arquitetura de produção é **Docker** (não supervisor/venv): a imagem é
> construída no CI e publicada no **GHCR**; o VPS apenas faz `docker compose
> pull && up -d`. Um **nginx-proxy-manager** (NPM) faz de borda/TLS.

---

## 🗺️ Topologia de produção

```
                         DNS
  controlador.cv ───────────────> Vercel CDN (frontend, React SPA)
  api.controlador.cv ───────────> VPS Hostinger (194.164.76.72)
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │  nginx-proxy-manager (NPM)     │  rede docker `proxy`
                         │  openresty · 80/443 · TLS LE   │  detém as portas públicas
                         └──────────────┬─────────────────┘
                                        │  proxy host:
                                        │  api.controlador.cv → http://accta-backend:8000
                                        ▼
                         ┌──────────────────────────────┐
                         │  container `accta-backend`     │  rede `proxy` (porta NÃO publicada)
                         │  uvicorn :8000 · 2 workers     │  imagem: ghcr.io/.../accta-backend
                         │  compose: /docker/accta        │  env_file: backend/.env
                         └──────────────┬─────────────────┘
                                        │  DATABASE_URL (pooler 6543)
                                        ▼
                                   Supabase (PostgreSQL gerido)
```

**Diretórios no host (não confundir):**

| Caminho | Papel |
|---------|-------|
| `/docker/accta` | **Pasta de deploy canónica** — só `docker-compose.yml` + `backend/.env`. É AQUI que se faz `docker compose pull/up`. |
| `/srv/accta/uploads` | Uploads persistidos (bind-mount → `/app/uploads` no container). Entra no backup. |
| `/opt/nginx-proxy/data` | Config persistida do NPM (proxy hosts, certificados). |
| `/opt/projetos/accta` | Cópia do source (Dockerfile/scripts). **Opcional** com GHCR — já não é precisa para o deploy. |

> ⚠️ **Armadilhas confirmadas — não fazer:**
> - **NUNCA** correr `/opt/projetos/accta/deploy.sh` nem um `docker compose` no
>   compose **órfão** desse diretório: builda para a porta **8001** e fora da
>   rede `proxy`, o que **desliga o backend do NPM** e parte o routing.
> - O container interno fala **8000** (decisão do dono). Qualquer imagem que
>   exponha só 8001 precisa do override `command: --port 8000` no compose
>   canónico (ver Etapa 2). O `Dockerfile` do repo é 8001-native; o override
>   resolve a divergência até ser reconciliada de raiz.

---

## Pré-requisitos
- VPS Hostinger com **Ubuntu 22.04/24.04** e **Docker + Docker Compose** (vem
  com o *Docker Manager* do hPanel).
- DNS: `api.controlador.cv` → **A record** → IP do VPS (`194.164.76.72`).
  (O `controlador.cv`/`www` apontam para a Vercel — ver VERCEL_DEPLOY.md.)
- Acesso SSH ao VPS.
- Projeto **Supabase** criado com a `DATABASE_URL` do pooler (porta `6543`,
  modo *transaction*).

---

## ✅ Etapa 1 — Borda: nginx-proxy-manager (uma vez)

O NPM é o único serviço que detém as portas públicas (80/443) e termina o TLS.
Corre como container, na rede docker `proxy`, com config persistida em
`/opt/nginx-proxy/data` e `restart: always`.

> Em produção isto **já está configurado**. Esta etapa documenta o estado-alvo
> para recriação/disaster-recovery.

1. Garantir a rede partilhada:
   ```bash
   docker network create proxy   # idempotente; ignora "already exists"
   ```
2. No painel web do NPM → **Proxy Hosts → Add Proxy Host**:
   - **Domain Names:** `api.controlador.cv`
   - **Scheme:** `http` · **Forward Hostname:** `accta-backend` · **Forward Port:** `8000`
   - **Websockets Support:** ✅ (necessário para o stream SSE de notificações)
   - Separador **SSL:** pedir certificado **Let's Encrypt** + **Force SSL** + HTTP/2.
3. Separador **Advanced** (custom Nginx) — para o SSE não cair aos ~60s e para
   o limite de upload, colar:
   ```nginx
   proxy_read_timeout 24h;
   proxy_buffering off;
   client_max_body_size 12M;
   ```

> **HTTPS é obrigatório**: o backend usa cookie de sessão `SameSite=None; Secure`
> — sem TLS o browser não envia o cookie e o login parte.

---

## ✅ Etapa 2 — Pasta de deploy `/docker/accta`

Esta pasta contém **só** o compose e o `.env`. A imagem vem do GHCR (não há
`build:` aqui — o build é no CI).

### 2.1 `docker-compose.yml` canónico

```yaml
services:
  backend:
    image: ghcr.io/hamiltonmoreno/accta-backend:latest
    container_name: accta-backend
    restart: unless-stopped
    env_file:
      - ./backend/.env
    networks:
      - proxy
    # Override OBRIGATÓRIO: a imagem é 8001-native; o NPM fala 8000.
    command: ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8000/api/"]
      interval: 30s
      timeout: 5s
      retries: 3
    volumes:
      # Uploads no disco do host: persistem entre recriações e entram no backup.
      # 755 no host (container corre como root) para leitura por terceiros.
      - /srv/accta/uploads:/app/uploads

networks:
  proxy:
    external: true
```

### 2.2 `backend/.env` (dentro de `/docker/accta/backend/.env`)

```bash
mkdir -p /docker/accta/backend
cat > /docker/accta/backend/.env <<'EOF'
DATABASE_URL=postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
SECRET_KEY=COLOCAR_AQUI_UMA_CHAVE_FORTE
CORS_ORIGINS=https://controlador.cv,https://www.controlador.cv
FRONTEND_URL=https://controlador.cv
RESEND_API_KEY=re_xxxxxxxxxxxxx
SENDER_EMAIL=noreply@controlador.cv
EOF
```

> Gere `SECRET_KEY` com: `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`
> Sem `DATABASE_URL` o backend aborta no arranque com
> `RuntimeError: DATABASE_URL environment variable is required`.
> O schema é criado idempotentemente por `ensure_schema()` no arranque (aditivo,
> sem DROP) — não há passo de migração manual.

---

## ✅ Etapa 3 — Uploads: bind-mount + migração (uma vez)

Os uploads vivem numa pasta do **host** (`/srv/accta/uploads`) para persistirem
entre recriações do container e entrarem na rotina de backup.

> ⚠️ **Permissões**: o `backend/Dockerfile` não define `USER` → o container
> corre como **root (UID 0)**; os ficheiros ficam `root:root`. A pasta no host
> deve ser **`chmod 755`** (dir) — 755 dir + 644 ficheiros é seguro para
> uploads públicos, nunca 777.

```bash
# 1. (se vens de um volume nomeado antigo) backup preventivo
docker cp accta-backend:/app/uploads ./uploads-backup-$(date +%F) 2>/dev/null || true

# 2. Criar a pasta no host
sudo mkdir -p /srv/accta/uploads
sudo chown -R root:root /srv/accta/uploads
sudo chmod 755 /srv/accta/uploads

# 3. Migrar os uploads existentes (se houver backup do passo 1)
[ -d ./uploads-backup-* ] && sudo cp -a ./uploads-backup-*/. /srv/accta/uploads/
```

**Modelo de serviço dos uploads:** o **backend** serve `/uploads/` (montagem
estática) e aplica RBAC nos documentos em `/api/documents/{id}/download`. O NPM
apenas faz proxy de tudo para `:8000`. (Servir uploads diretamente pelo nginx
da borda seria uma otimização futura — exigiria montar `/srv/accta/uploads` no
container do NPM e reproduzir as regras de `deploy/nginx/accta.conf`; **não é
necessário**.)

---

## ✅ Etapa 4 — Autenticar no GHCR + primeiro arranque

```bash
# 1. Autenticar o host no GHCR (token GitHub com scope read:packages)
echo <GHCR_TOKEN> | docker login ghcr.io -u <github-user> --password-stdin
#    (alternativa: tornar o package `accta-backend` público e dispensar o login)

# 2. Primeiro pull + arranque
cd /docker/accta
docker compose pull backend
docker compose up -d backend
docker compose logs -f backend          # confirmar "Application startup complete"
```

### 4.1 Criar o primeiro admin

```bash
docker compose exec backend python scripts/create_admin.py
# Segue o prompt: email + password do admin
```

### 4.2 Teste de fumo

```bash
curl https://api.controlador.cv/api/
# Esperado: {"message":"ACCTA Portal API v1.0"}
```

---

## ✅ Etapa 5 — Deploy automático (GitHub Actions → GHCR → VPS)

O workflow **`.github/workflows/deploy.yml`** (`CD — Deploy Backend to
Production`) dispara no push para `main`: corre o gate (ruff + unit), constrói
e publica a imagem no GHCR, e faz SSH ao VPS para `docker compose pull && up -d`.

### 5.1 Chave SSH para o deploy
```bash
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/accta_deploy
cat ~/.ssh/accta_deploy.pub | ssh <user>@194.164.76.72 "cat >> ~/.ssh/authorized_keys"
```
> Ver [SSH_SETUP.md](SSH_SETUP.md) para detalhes de geração/configuração de chaves.

### 5.2 Secrets do GitHub (**Settings → Secrets and variables → Actions**)

| Secret | Valor |
|--------|-------|
| `DEPLOY_HOST` | `194.164.76.72` |
| `DEPLOY_USER` | utilizador SSH do VPS |
| `DEPLOY_SSH_KEY` | conteúdo **completo** de `~/.ssh/accta_deploy` (chave privada) |
| `PRODUCTION_URL` | `https://api.controlador.cv` |
| `DEPLOY_PORT` | *(opcional)* porta SSH, default `22` |
| `DEPLOY_APP_DIR` | *(opcional)* default `/docker/accta` |

> O push da imagem para o GHCR usa o `GITHUB_TOKEN` automático — **não** é
> preciso secret adicional para isso. O `docker login ghcr.io` da Etapa 4 é o
> que autoriza o **VPS** a fazer `pull`.

### 5.3 Testar o pipeline
```bash
git push origin main      # → GitHub → Actions → "CD — Deploy Backend to Production"
```
ou **Actions → Run workflow** (gatilho `workflow_dispatch`).

---

## ✅ Etapa 6 — Backups e manutenção (cron)

```bash
# Backup diário dos uploads (rsync espelhado, guard anti-vazio). 3h da manhã:
0 3 * * * BACKUP_DEST="backup@HOST:/backups/accta/uploads/" /opt/projetos/accta/scripts/backup_uploads.sh >> /var/log/accta-backup.log 2>&1

# Dump manual da BD (Supabase também faz backups automáticos no painel):
set -a; . /docker/accta/backend/.env; set +a
pg_dump "$DATABASE_URL" -Fc -f ~/backups/$(date +%F).dump

# Limpeza de uploads órfãos (dry-run por defeito; --delete para aplicar):
cd /docker/accta && docker compose exec backend python scripts/find_orphan_uploads.py
```

> ⚠️ `rsync --delete` é **espelho**, não versão. **Uploads sem a BD são
> inúteis** — fazer o dump do Supabase no mesmo ciclo e enviar ambos.

---

## 🧪 Comandos do dia-a-dia (sempre a partir de `/docker/accta`)

```bash
docker compose logs -f backend            # logs ao vivo
docker compose ps                          # estado + health
docker compose pull backend && docker compose up -d backend   # deploy manual
docker compose restart backend            # reiniciar
docker compose exec backend bash          # shell no container
```

---

## ↩️ Rollback

As imagens são versionadas por SHA (`ghcr.io/hamiltonmoreno/accta-backend:sha-<12>`),
o que dá rollback limpo sem rebuild:

```bash
cd /docker/accta
# 1. Descobrir a tag boa anterior (GitHub → Packages, ou no histórico de deploys)
# 2. Apontar o compose para essa tag (ou via override pontual):
docker compose pull backend                      # garante a imagem em cache
IMAGE_TAG=sha-XXXXXXXXXXXX docker compose up -d backend   # se parametrizado
#   — em alternativa, editar `image:` para a tag sha-<12> e `up -d`.
docker compose logs -f backend
```

> Alternativa rápida (reverter o código): `git revert` em `main` → o CD
> reconstrói e publica automaticamente a imagem corrigida.

---

## 🚨 Troubleshooting

| Sintoma | Causa provável | Solução |
|---------|----------------|---------|
| `502 Bad Gateway` no NPM | Container em baixo, ou a falar porta errada (8001 vs 8000) | `docker compose ps`/`logs`; confirmar o override `--port 8000` e que o NPM aponta para `accta-backend:8000` |
| NPM não resolve `accta-backend` | Container fora da rede `proxy` | Confirmar `networks: [proxy]` no compose e `proxy` `external: true` |
| Backend não arranca | `DATABASE_URL` em falta/errada | Ver `docker compose logs backend`; corrigir `backend/.env` e `up -d` |
| `pull` falha (`denied`/`unauthorized`) | VPS sem login no GHCR | Refazer `docker login ghcr.io` (Etapa 4) ou tornar o package público |
| SSE desliga em ~60s | Falta `proxy_read_timeout` no NPM | Pôr `proxy_read_timeout 24h; proxy_buffering off;` no Advanced do proxy host |
| `CORS error` no frontend | `CORS_ORIGINS` não inclui o domínio Vercel | Ajustar em `backend/.env` e `up -d backend` |
| Convite por email não chega | Domínio não verificado no Resend | Validar DNS de `controlador.cv` em resend.com/domains; até lá o link vem na resposta da API |

---

## ✅ Checklist final antes de abrir ao público

- [ ] `https://controlador.cv` carrega a homepage (Vercel)
- [ ] `https://api.controlador.cv/api/` devolve JSON (NPM → backend)
- [ ] SSL válido em ambos (cadeado verde)
- [ ] Login do admin funciona
- [ ] Convite por email chega (após validar domínio no Resend)
- [ ] Notificações em tempo real (SSE) funcionam numa conta logada
- [ ] Backups confirmados (Supabase automático + dump/uploads no cron)
- [ ] Push para `main` faz deploy verde em **CD — Deploy Backend to Production**

---

**Ficheiros-chave:**
- Pipeline CD: `.github/workflows/deploy.yml`
- Frontend (Vercel): [VERCEL_DEPLOY.md](VERCEL_DEPLOY.md)
- Guia genérico: [DEPLOY.md](DEPLOY.md)
- Este checklist: `HOSTINGER_DEPLOY.md`
