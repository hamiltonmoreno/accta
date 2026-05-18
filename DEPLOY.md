# Guia de Deploy — Portal ACCTA

## Visão Geral da Pipeline

```
Push para qualquer branch  →  CI (Lint + Build + Tests)
Push para main             →  CI + Deploy automático
Pull Request para main     →  CI (verificação antes de merge)
```

---

## 1. Secrets do GitHub (Obrigatórios)

Aceda a: **Repository → Settings → Secrets and variables → Actions → New repository secret**

| Secret | Descrição | Onde obter |
|--------|-----------|------------|
| `DEPLOY_HOST` | IP ou hostname do servidor de produção | Painel do seu provedor (Hostinger, DigitalOcean, etc.) |
| `DEPLOY_USER` | Utilizador SSH do servidor | Normalmente `deploy` (recomendado) ou `root` |
| `DEPLOY_SSH_KEY` | Chave privada SSH (inteira, incluindo BEGIN/END) | Gere com `ssh-keygen -t ed25519 -C "github-deploy"` |
| `DEPLOY_PORT` | Porta SSH (opcional, padrão: 22) | Configuração do servidor |
| `DEPLOY_APP_DIR` | Diretório da aplicação no servidor (opcional, padrão: `/app`) | Onde o código está no servidor |
| `PRODUCTION_URL` | URL pública da aplicação (ex: `https://controlador.cv`) | O domínio configurado no DNS |

> Ver [SSH_SETUP.md](SSH_SETUP.md) para instruções detalhadas de geração e configuração de chaves SSH.

### Variáveis de ambiente do servidor

No servidor de produção, `/app/backend/.env` deve conter:

```env
SECRET_KEY=<chave-secreta-forte — gere com: python3 -c "import secrets; print(secrets.token_urlsafe(64))">
DATABASE_URL=postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
CORS_ORIGINS=https://controlador.cv
FRONTEND_URL=https://controlador.cv
RESEND_API_KEY=re_xxxxxxxxxxxxx
SENDER_EMAIL=noreply@controlador.cv
```

> **Base de dados**: a app usa PostgreSQL/Supabase via `asyncpg` (não MongoDB).
> Em produção use o URI do **connection pooler** do Supabase (porta `6543`,
> transaction mode). `DATABASE_URL` é **obrigatória** — se faltar, o backend
> aborta no arranque com `RuntimeError: DATABASE_URL environment variable is required`.

E `/app/frontend/.env` (usado durante o build):

```env
REACT_APP_BACKEND_URL=https://controlador.cv
```

> O secret `PRODUCTION_URL` do GitHub é injetado em `REACT_APP_BACKEND_URL` durante o `yarn build` no workflow.

---

## 2. Como fazer Deploy

### Deploy Automático (recomendado)

Basta fazer merge ou push para a branch `main`:

```bash
git checkout main
git merge feature/minha-feature
git push origin main
```

O workflow `CD — Deploy to Production` é acionado automaticamente.

### Deploy Manual

Aceda a: **Repository → Actions → CD — Deploy to Production → Run workflow**

---

## 3. Verificar Estado do Deploy

### Via GitHub Actions

1. Aceda a **Repository → Actions**
2. Clique no workflow mais recente
3. Verifique se todos os jobs estão verdes:
   - `Backend CI` — Lint (ruff) + Tests (pytest)
   - `Frontend CI` — Lint (eslint) + Build (yarn build)
   - `Deploy to Production` — Deploy via SSH

### Via Health Check direto

```bash
curl https://controlador.cv/api/
# Esperado: {"message": "ACCTA Portal API v1.0"}
```

### Via Logs do servidor

```bash
ssh deploy@SEU_IP
sudo supervisorctl status
sudo tail -f /var/log/supervisor/backend.err.log
```

---

## 4. Pipeline CI em Detalhe

### Backend (Python/FastAPI)

| Passo | Comando | Descrição |
|-------|---------|-----------|
| Lint | `ruff check .` | Verifica erros de sintaxe e estilo |
| Tests | `pytest tests/ -v` | Executa testes (DAO mockado / Postgres em serviço) |

### Frontend (React/Craco)

| Passo | Comando | Descrição |
|-------|---------|-----------|
| Lint | `npx eslint src/ --ext .js,.jsx --max-warnings=60` | Verifica erros JS/JSX |
| Build | `yarn build` | Compila para produção |

---

## 5. Rollback

Se o deploy falhar ou introduzir bugs:

```bash
# No servidor
cd /app
git log --oneline -5           # Ver commits recentes
git revert HEAD                # Reverter último commit
sudo supervisorctl restart backend
sudo systemctl reload nginx
```

---

## 6. Pressupostos

- O servidor tem Python 3.11+, Node 20+, Yarn e Supervisor instalados
- A base de dados é PostgreSQL/Supabase (gerida) — acessível via `DATABASE_URL`; **não** é necessário instalar um servidor de base de dados local
- O repositório está clonado no servidor no diretório especificado em `DEPLOY_APP_DIR` (padrão `/app`)
- A chave SSH pública está adicionada a `~/.ssh/authorized_keys` no utilizador `DEPLOY_USER`
- O Supervisor está configurado para gerir `backend` (uvicorn porta 8001)
- O Nginx está configurado para encaminhar `/api/*` → porta 8001 e `/` → frontend build estático

> Ver [HOSTINGER_DEPLOY.md](HOSTINGER_DEPLOY.md) para o guia completo de configuração do servidor.
