# Deploy Alternativo — Vercel (frontend) + Supabase (PostgreSQL)

> Opção para quem prefere plataformas cloud geridas em vez de VPS próprio.
> Este guia foca-se no **frontend no Vercel** + **base de dados no Supabase**.
> O backend (FastAPI/uvicorn) pode correr em qualquer host que alcance o
> Supabase — para opções de hosting do backend ver [HOSTINGER_DEPLOY.md](HOSTINGER_DEPLOY.md)
> (VPS: Docker/compose ou supervisord).
> Para o deploy recomendado (VPS Hostinger), ver [HOSTINGER_DEPLOY.md](HOSTINGER_DEPLOY.md).

## Arquitectura

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│    Vercel     │────>│  Backend (API)   │────>│   Supabase   │
│  (Frontend)   │     │  FastAPI Python  │     │ (PostgreSQL) │
│  React SPA    │     │  (qualquer host) │     │   pooler     │
└──────────────┘     └──────────────────┘     └──────────────┘
```

---

## Passo 1: Supabase (Base de Dados PostgreSQL)

1. Aceder a [supabase.com](https://supabase.com) → criar projeto
2. Definir uma password de base de dados forte (guardar)
3. Ir a **Settings → Database → Connection pooling**
4. Selecionar o modo **Transaction** (porta `6543`)
5. Copiar a **connection string do pooler**, no formato:
   ```
   postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
   ```

> O backend usa o **connection pooler** do Supabase (porta `6543`, modo
> *transaction*) e define `statement_cache_size=0` (pgbouncer). O schema e os
> índices são criados idempotentemente por `ensure_schema()` em `database.py`
> no arranque. Se `DATABASE_URL` faltar, o backend aborta no arranque com
> `RuntimeError`.

---

## Passo 2: Backend (FastAPI)

O backend é FastAPI/uvicorn e pode correr em **qualquer host com acesso ao
Supabase**. Para instruções concretas de hosting do backend (VPS com
Docker/compose ou supervisord), seguir [HOSTINGER_DEPLOY.md](HOSTINGER_DEPLOY.md).

Independentemente do host, configurar as variáveis de ambiente do backend:

```env
SECRET_KEY=<gerar com: python3 -c "import secrets; print(secrets.token_urlsafe(64))">
DATABASE_URL=postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
CORS_ORIGINS=https://SEU-PROJETO.vercel.app
FRONTEND_URL=https://SEU-PROJETO.vercel.app
RESEND_API_KEY=re_xxxxxxxxxxxxx
SENDER_EMAIL=noreply@controlador.cv
```

Arranque (uvicorn): `uvicorn server:app --host 0.0.0.0 --port $PORT` (a partir
de `backend/`). Anotar o URL público do backend (ex: `https://api.controlador.cv`).

---

## Passo 3: Frontend no Vercel

### 3.1 Configurar no Vercel

1. Aceder a [vercel.com](https://vercel.com) → New Project
2. Importar repositório GitHub
3. Configurar:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Create React App
   - **Build Command:** `yarn build`
   - **Output Directory:** `build`
4. Adicionar variável de ambiente (URL público do backend):
   ```env
   REACT_APP_BACKEND_URL=https://api.controlador.cv
   ```
5. Deploy

### 3.2 vercel.json

O ficheiro `frontend/vercel.json` já está incluído neste repo e configura:
- **SPA fallback**: todas as rotas servem `index.html` (necessário para React Router)
- **Cache imutável** em `/static/*` (assets com hash)
- **Cabeçalhos de segurança**: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`

Não precisas de o editar — ele é detectado automaticamente quando defines
**Root Directory: `frontend`** no painel Vercel.

> Não use rewrites para fazer proxy do `/api/` para o backend. O frontend
> chama o backend directamente via `REACT_APP_BACKEND_URL`, o que evita
> double-billing de bandwidth e garante que CORS funciona como esperado.

---

## Passo 4: Actualizar CORS no Backend

Actualizar `CORS_ORIGINS` no backend com o URL final do Vercel:

```env
CORS_ORIGINS=https://SEU-PROJETO.vercel.app
```

---

## Passo 5: Domínio Personalizado (Opcional)

### Vercel (Frontend):
1. Settings → Domains → Adicionar `controlador.cv` ou `portal.controlador.cv`
2. Configurar DNS: CNAME → `cname.vercel-dns.com`

### Backend:
1. Configurar um domínio (ex: `api.controlador.cv`) no host do backend
   (ver [HOSTINGER_DEPLOY.md](HOSTINGER_DEPLOY.md))
2. Configurar DNS conforme indicado pelo host

### Actualizar CORS após domínio personalizado:
```env
CORS_ORIGINS=https://controlador.cv,https://www.controlador.cv
```

---

## Passo 6: Criar Primeiro Admin

```bash
# Localmente, com DATABASE_URL apontando para o pooler do Supabase
cd scripts
python create_admin.py
# Siga o prompt para definir email + password do admin
```

---

## Passo 7: Verificar Domínio no Resend

1. Aceder a [resend.com/domains](https://resend.com/domains)
2. Adicionar `controlador.cv`
3. Configurar registos DNS (SPF, DKIM, DMARC) conforme indicado
4. Aguardar verificação (até 48h)
5. Após verificação, emails de convite e reset de password são enviados automaticamente

---

## Resumo de Variáveis de Ambiente

### Backend

| Variável | Exemplo |
|----------|---------|
| `SECRET_KEY` | `<gerar aleatoriamente — 64 chars>` |
| `DATABASE_URL` | `postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres` |
| `CORS_ORIGINS` | `https://controlador.cv` |
| `FRONTEND_URL` | `https://controlador.cv` |
| `RESEND_API_KEY` | `re_xxxxxxxxxxxxx` |
| `SENDER_EMAIL` | `noreply@controlador.cv` |

### Frontend (Vercel)

| Variável | Exemplo |
|----------|---------|
| `REACT_APP_BACKEND_URL` | `https://api.controlador.cv` |

---

## Checklist Pré-Deploy

- [ ] Projeto Supabase criado + `DATABASE_URL` (pooler 6543, modo Transaction) configurado no backend
- [ ] Backend (FastAPI) em execução com todas as env vars (ver HOSTINGER_DEPLOY.md)
- [ ] Frontend no Vercel com `REACT_APP_BACKEND_URL`
- [ ] `CORS_ORIGINS` no backend inclui o URL do Vercel
- [ ] Primeiro admin criado via `create_admin.py`
- [ ] Domínio `controlador.cv` verificado no Resend
- [ ] Testar login, convite por email, dashboard, notificações
