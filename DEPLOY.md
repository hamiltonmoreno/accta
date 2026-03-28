# Guia de Deploy — Portal ACTACV

## Visao Geral da Pipeline

```
Push para qualquer branch  →  CI (Lint + Build + Tests)
Push para main             →  CI + Deploy automatico
Pull Request para main     →  CI (verificacao antes de merge)
```

---

## 1. Secrets do GitHub (Obrigatorios)

Aceda a: **Repository → Settings → Secrets and variables → Actions → New repository secret**

| Secret | Descricao | Onde obter |
|--------|-----------|------------|
| `DEPLOY_HOST` | IP ou hostname do servidor de producao | Painel do seu provedor (AWS, DigitalOcean, etc.) |
| `DEPLOY_USER` | Utilizador SSH do servidor | Normalmente `root` ou `deploy` |
| `DEPLOY_SSH_KEY` | Chave privada SSH (inteira, incluindo BEGIN/END) | Gere com `ssh-keygen -t ed25519 -C "deploy"` e adicione a publica ao servidor |
| `DEPLOY_PORT` | Porta SSH (opcional, padrao: 22) | Configuracao do servidor |
| `DEPLOY_APP_DIR` | Diretorio da aplicacao no servidor (opcional, padrao: `/app`) | Onde o codigo esta no servidor |
| `PRODUCTION_URL` | URL publica da aplicacao (ex: `https://accta.cv`) | O dominio/URL configurado no DNS |

### Variaveis de ambiente do servidor (configurar no `.env` do servidor)

No servidor de producao, o ficheiro `/app/backend/.env` deve conter:

```env
SECRET_KEY=<chave-secreta-forte-gerada-aleatoriamente>
MONGO_URL=mongodb://localhost:27017
DB_NAME=accta_portal
CORS_ORIGINS=https://accta.cv
```

E `/app/frontend/.env`:

```env
REACT_APP_BACKEND_URL=https://accta.cv
```

> **Nota:** O build de producao do frontend injeta `REACT_APP_BACKEND_URL` durante o `yarn build`, por isso o secret `PRODUCTION_URL` e usado diretamente no workflow.

---

## 2. Como fazer Deploy

### Deploy Automatico (recomendado)

Basta fazer merge ou push para a branch `main`:

```bash
git checkout main
git merge feature/minha-feature
git push origin main
```

O workflow `CD — Deploy to Production` sera acionado automaticamente.

### Deploy Manual

Aceda a: **Repository → Actions → CD — Deploy to Production → Run workflow**

(Para ativar deploy manual, adicione `workflow_dispatch:` ao trigger do deploy.yml)

---

## 3. Verificar Estado do Deploy

### Via GitHub Actions

1. Aceda a **Repository → Actions**
2. Clique no workflow mais recente
3. Verifique se todos os jobs estao verdes:
   - `Backend CI` — Lint + Tests do backend
   - `Frontend CI` — Lint + Build do frontend
   - `Deploy to Production` — Deploy via SSH

### Via Health Check direto

```bash
curl https://accta.cv/api/
# Esperado: {"message": "ACCTA Portal API v1.0"}
```

### Via Logs do servidor

```bash
ssh deploy@servidor
sudo supervisorctl status
tail -f /var/log/supervisor/backend.err.log
```

---

## 4. Pipeline CI em Detalhe

### Backend (Python/FastAPI)

| Passo | Comando | Descricao |
|-------|---------|-----------|
| Lint | `ruff check .` | Verifica erros de sintaxe e estilo |
| Tests | `pytest tests/ -v` | Executa testes com MongoDB em servico |

### Frontend (React/Craco)

| Passo | Comando | Descricao |
|-------|---------|-----------|
| Lint | `npx eslint src/` | Verifica erros JS/JSX |
| Build | `yarn build` | Compila para producao |

---

## 5. Rollback

Se o deploy falhar ou introduzir bugs:

```bash
# No servidor
cd /app
git log --oneline -5          # Ver commits recentes
git revert HEAD               # Reverter ultimo commit
sudo supervisorctl restart backend frontend
```

Ou na plataforma Emergent, utilize o botao **"Rollback"** para restaurar um checkpoint anterior.

---

## 6. Pressupostos

- O servidor de producao ja tem Python 3.11+, Node 20+, MongoDB 7+ e Supervisor instalados
- O repositorio esta clonado no servidor no diretorio especificado em `DEPLOY_APP_DIR`
- A chave SSH publica esta adicionada a `~/.ssh/authorized_keys` no servidor
- O Supervisor esta configurado para gerir `backend` (uvicorn porta 8001) e `frontend` (porta 3000)
- O proxy reverso (Nginx/Caddy) esta configurado para encaminhar `/api/*` para porta 8001 e `/` para porta 3000
