# Deploy Alternativo — Vercel + Render + MongoDB Atlas

> Opção para quem prefere plataformas cloud geridas em vez de VPS próprio.
> Para o deploy recomendado (VPS Hostinger), ver [HOSTINGER_DEPLOY.md](HOSTINGER_DEPLOY.md).

## Arquitectura

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│    Vercel     │────>│  Backend (API)   │────>│   MongoDB    │
│  (Frontend)   │     │  Render.com      │     │  Atlas Cloud │
│  React SPA    │     │  FastAPI Python  │     │              │
└──────────────┘     └──────────────────┘     └──────────────┘
```

---

## Passo 1: MongoDB Atlas (Base de Dados)

1. Aceder a [mongodb.com/atlas](https://www.mongodb.com/atlas)
2. Criar cluster gratuito (M0 Free Tier)
3. Criar utilizador de base de dados (guardar user + password)
4. Em **Network Access** → adicionar `0.0.0.0/0` (permitir de qualquer IP)
5. Copiar a connection string:
   ```
   mongodb+srv://user:password@cluster.mongodb.net/accta_portal
   ```

---

## Passo 2: Backend no Render.com

### 2.1 Configurar no Render

1. Aceder a [render.com](https://render.com) → New → Web Service
2. Conectar repositório GitHub
3. Configurar:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
4. Adicionar variáveis de ambiente:
   ```env
   SECRET_KEY=<gerar com: python3 -c "import secrets; print(secrets.token_urlsafe(64))">
   MONGO_URL=mongodb+srv://user:password@cluster.mongodb.net/accta_portal
   DB_NAME=accta_portal
   CORS_ORIGINS=https://SEU-PROJETO.vercel.app
   FRONTEND_URL=https://SEU-PROJETO.vercel.app
   RESEND_API_KEY=re_xxxxxxxxxxxxx
   SENDER_EMAIL=noreply@controlador.cv
   ```
5. Deploy → Anotar URL (ex: `https://accta-api.onrender.com`)

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
4. Adicionar variável de ambiente:
   ```env
   REACT_APP_BACKEND_URL=https://accta-api.onrender.com
   ```
5. Deploy

### 3.2 (Opcional) Atualizar vercel.json

Se quiser que o Vercel faça proxy das chamadas `/api/`:

```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://accta-api.onrender.com/api/$1" }
  ]
}
```

---

## Passo 4: Actualizar CORS no Backend

No Render, actualizar `CORS_ORIGINS` com o URL final do Vercel:

```env
CORS_ORIGINS=https://SEU-PROJETO.vercel.app
```

---

## Passo 5: Domínio Personalizado (Opcional)

### Vercel (Frontend):
1. Settings → Domains → Adicionar `controlador.cv` ou `portal.controlador.cv`
2. Configurar DNS: CNAME → `cname.vercel-dns.com`

### Render (Backend):
1. Settings → Custom Domains → Adicionar `api.controlador.cv`
2. Configurar DNS conforme indicado pelo Render

### Actualizar CORS após domínio personalizado:
```env
CORS_ORIGINS=https://controlador.cv,https://www.controlador.cv
```

---

## Passo 6: Criar Primeiro Admin

```bash
# Localmente, com MONGO_URL apontando para Atlas
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

### Backend (Render)

| Variável | Exemplo |
|----------|---------|
| `SECRET_KEY` | `<gerar aleatoriamente — 64 chars>` |
| `MONGO_URL` | `mongodb+srv://user:pass@cluster.mongodb.net/accta_portal` |
| `DB_NAME` | `accta_portal` |
| `CORS_ORIGINS` | `https://controlador.cv` |
| `FRONTEND_URL` | `https://controlador.cv` |
| `RESEND_API_KEY` | `re_xxxxxxxxxxxxx` |
| `SENDER_EMAIL` | `noreply@controlador.cv` |

### Frontend (Vercel)

| Variável | Exemplo |
|----------|---------|
| `REACT_APP_BACKEND_URL` | `https://accta-api.onrender.com` |

---

## Checklist Pré-Deploy

- [ ] MongoDB Atlas configurado com connection string
- [ ] Backend no Render com todas as env vars
- [ ] Frontend no Vercel com `REACT_APP_BACKEND_URL`
- [ ] `CORS_ORIGINS` no backend inclui o URL do Vercel
- [ ] Primeiro admin criado via `create_admin.py`
- [ ] Domínio `controlador.cv` verificado no Resend
- [ ] Testar login, convite por email, dashboard, notificações
