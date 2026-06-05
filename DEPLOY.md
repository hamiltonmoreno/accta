# Guia de Deploy — Portal ACCTA

## Visão Geral da Pipeline

```
Push/PR para qualquer branch  →  CI (ci.yml: lint + build + tests)
Push para main                →  CD (deploy.yml): gate → build imagem → GHCR → VPS
Frontend                      →  Vercel (deploy automático, independente)
```

O **frontend** é servido pela **Vercel** (deploy automático no push para `main`;
ver [VERCEL_DEPLOY.md](VERCEL_DEPLOY.md)). O **backend** corre em **Docker** no
VPS Hostinger, atrás de um nginx-proxy-manager — ver
[HOSTINGER_DEPLOY.md](HOSTINGER_DEPLOY.md) para a topologia e o setup do servidor.

Este guia descreve o **CD do backend** (`.github/workflows/deploy.yml`):

1. **gate** — `ruff check` + testes unitários sem DB (rede de segurança; a suite
   completa corre no `ci.yml`).
2. **build** — constrói a imagem (`backend/Dockerfile`) e publica no **GHCR**:
   `ghcr.io/hamiltonmoreno/accta-backend` com as tags `:latest` e `:sha-<12>`.
3. **deploy** — SSH ao VPS → `docker compose pull && up -d backend` em
   `/docker/accta` → health-check ponta-a-ponta via `PRODUCTION_URL/api/`.

---

## 1. Secrets do GitHub (Obrigatórios)

**Repository → Settings → Secrets and variables → Actions → New repository secret**

| Secret | Descrição | Onde obter |
|--------|-----------|------------|
| `DEPLOY_HOST` | IP do VPS de produção | Painel Hostinger (`194.164.76.72`) |
| `DEPLOY_USER` | Utilizador SSH do VPS | ex.: `deploy` ou `root` |
| `DEPLOY_SSH_KEY` | Chave privada SSH (inteira, com BEGIN/END) | `ssh-keygen -t ed25519 -C "github-deploy"` |
| `PRODUCTION_URL` | URL público do backend | `https://api.controlador.cv` |
| `DEPLOY_PORT` | Porta SSH (opcional, default `22`) | Configuração do servidor |
| `DEPLOY_APP_DIR` | Pasta do compose (opcional, default `/docker/accta`) | Onde está o `docker-compose.yml` |

> O **push da imagem para o GHCR** usa o `GITHUB_TOKEN` automático (permissão
> `packages: write` já declarada no workflow) — **não** é preciso secret extra.
> O que o **VPS** precisa é de estar autenticado no GHCR para o `pull`
> (`docker login ghcr.io`, uma vez — ver HOSTINGER_DEPLOY.md §4).
> Ver [SSH_SETUP.md](SSH_SETUP.md) para a configuração das chaves SSH.

### Variáveis de ambiente do servidor

Em `/docker/accta/backend/.env` (lido pelo container via `env_file`):

```env
SECRET_KEY=<chave-secreta-forte — gere com: python3 -c "import secrets; print(secrets.token_urlsafe(64))">
DATABASE_URL=postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
CORS_ORIGINS=https://controlador.cv,https://www.controlador.cv
FRONTEND_URL=https://controlador.cv
RESEND_API_KEY=re_xxxxxxxxxxxxx
SENDER_EMAIL=noreply@controlador.cv
```

> **Base de dados**: PostgreSQL/Supabase via `asyncpg` (não MongoDB). Use o URI
> do **connection pooler** (porta `6543`, modo *transaction*). `DATABASE_URL` é
> **obrigatória** — se faltar, o backend aborta no arranque.

> O frontend **não** lê um `.env` no servidor: o `REACT_APP_BACKEND_URL`
> (`https://api.controlador.cv`) é definido no painel da **Vercel**.

---

## 2. Como fazer Deploy

### Deploy Automático (recomendado)

Merge/push para `main` aciona o `CD — Deploy Backend to Production`:

```bash
git checkout main
git merge release/minha-release    # main é alcançada via release/hotfix (ver CONTRIBUTING.md)
git push origin main
```

### Deploy Manual

**Repository → Actions → CD — Deploy Backend to Production → Run workflow**
(gatilho `workflow_dispatch`).

Ou diretamente no VPS:

```bash
cd /docker/accta
docker compose pull backend && docker compose up -d backend
```

---

## 3. Verificar Estado do Deploy

### Via GitHub Actions

**Repository → Actions →** workflow mais recente. Jobs esperados verdes:
`gate` (ruff + unit) → `build` (push GHCR) → `deploy` (SSH + health-check).

### Via Health Check direto

```bash
curl https://api.controlador.cv/api/
# Esperado: {"message": "ACCTA Portal API v1.0"}
```

### Via Logs do servidor

```bash
ssh <user>@194.164.76.72
cd /docker/accta
docker compose ps             # estado + health do container
docker compose logs -f backend
```

---

## 4. Pipeline CI em Detalhe (`ci.yml`)

Corre em **todos os pushes/PRs** (gate independente do deploy):

| Área | Passos |
|------|--------|
| Backend (FastAPI) | `ruff check` · smoke tests (Postgres em serviço) · unit tests + coverage |
| Frontend (React) | `eslint` · `yarn test` · `yarn build` |

> O `deploy.yml` tem o seu **próprio gate rápido** (ruff + unit sem DB) antes de
> construir a imagem — não depende do `ci.yml`, mas cobre o essencial do backend.

---

## 5. Rollback

As imagens são **versionadas por SHA** no GHCR — rollback sem rebuild:

```bash
cd /docker/accta
# Apontar o compose para a tag boa anterior (GitHub → Packages → accta-backend):
#   editar `image: ghcr.io/hamiltonmoreno/accta-backend:sha-XXXXXXXXXXXX`
docker compose pull backend
docker compose up -d backend
docker compose logs -f backend
```

> Alternativa: `git revert HEAD` em `main` → o CD reconstrói e publica a imagem
> corrigida automaticamente.

---

## 6. Pressupostos

- O VPS tem **Docker + Docker Compose** (Docker Manager do hPanel).
- A borda é o **nginx-proxy-manager** (rede docker `proxy`, TLS Let's Encrypt),
  com proxy host `api.controlador.cv → accta-backend:8000`.
- A pasta de deploy canónica é **`/docker/accta`** (`docker-compose.yml` +
  `backend/.env`); a imagem vem do **GHCR** (sem `build:` no host).
- O VPS está **autenticado no GHCR** (`docker login ghcr.io`) para o `pull`.
- A base de dados é PostgreSQL/Supabase (gerida) via `DATABASE_URL`.
- ⚠️ **Nunca** correr `/opt/projetos/accta/deploy.sh` nem o compose órfão desse
  diretório (buildam para 8001, fora da rede `proxy` → partem o routing do NPM).

> Setup completo do servidor: [HOSTINGER_DEPLOY.md](HOSTINGER_DEPLOY.md).
