# Deploy do Portal ACCTA

## Arquitectura de Deploy

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│   Vercel     │────>│  Backend (API)   │────>│   MongoDB    │
│  (Frontend)  │     │  Render/Railway  │     │  Atlas Cloud │
│  React SPA   │     │  FastAPI Python  │     │              │
└─────────────┘     └──────────────────┘     └──────────────┘
```

---

## Passo 1: MongoDB Atlas (Base de Dados)

1. Aceder a https://www.mongodb.com/atlas
2. Criar cluster gratuito (M0 Free Tier)
3. Criar utilizador de base de dados
4. Em "Network Access" → adicionar `0.0.0.0/0` (permitir de qualquer IP)
5. Copiar a connection string: `mongodb+srv://user:pass@cluster.mongodb.net/actacv`

---

## Passo 2: Backend (Render.com — Gratis)

### 2.1 Preparar repositorio
O backend esta em `/backend`. O Render precisa de:
- `requirements.txt` (ja existe)
- O ficheiro `render_start.sh` (ja criado)

### 2.2 Configurar no Render
1. Aceder a https://render.com → New → Web Service
2. Conectar repositorio GitHub
3. Configurar:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
4. Adicionar variaveis de ambiente:
   ```
   SECRET_KEY=<chave-forte-64-chars>
   MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/actacv
   DB_NAME=actacv
   CORS_ORIGINS=https://seu-projeto.vercel.app
   RESEND_API_KEY=re_e8zTccvu_Ndyp2PE421qGbL7t7v5GV6DJ
   SENDER_EMAIL=noreply@controlador.cv
   ```
5. Deploy → Anotar URL (ex: `https://actacv-api.onrender.com`)

---

## Passo 3: Frontend (Vercel)

### 3.1 Configurar no Vercel
1. Aceder a https://vercel.com → New Project
2. Importar repositorio GitHub
3. Configurar:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Create React App
   - **Build Command:** `yarn build`
   - **Output Directory:** `build`
4. Adicionar variaveis de ambiente:
   ```
   REACT_APP_BACKEND_URL=https://actacv-api.onrender.com
   ```
5. Deploy

### 3.2 Atualizar vercel.json
Abrir `vercel.json` na raiz e substituir `SEU-BACKEND-URL.com` pela URL do Render:
```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://actacv-api.onrender.com/api/$1" }
  ]
}
```

---

## Passo 4: CORS no Backend

No `.env` do Render, definir:
```
CORS_ORIGINS=https://seu-projeto.vercel.app,https://www.controlador.cv
```

---

## Passo 5: Dominio Personalizado (Opcional)

### Vercel (Frontend):
1. Settings → Domains → Add `portal.controlador.cv`
2. Configurar DNS: CNAME `portal` → `cname.vercel-dns.com`

### Render (Backend):
1. Settings → Custom Domains → Add `api.controlador.cv`
2. Configurar DNS conforme indicado

### Atualizar CORS:
```
CORS_ORIGINS=https://portal.controlador.cv,https://www.controlador.cv
```

---

## Passo 6: Criar Primeiro Admin

```bash
# Localmente, com MONGO_URL apontando para Atlas
cd scripts
python create_admin.py \
  --email admin@controlador.cv \
  --password <senha-forte> \
  --name "Administrador ACCTA"
```

---

## Passo 7: Verificar Dominio no Resend

1. Aceder a https://resend.com/domains
2. Adicionar `controlador.cv`
3. Configurar registos DNS (MX, TXT, DKIM) conforme indicado
4. Aguardar verificacao (ate 48h)
5. Emails de convite passam a ser enviados automaticamente

---

## Resumo de Variaveis de Ambiente

### Backend (Render)
| Variavel | Valor |
|----------|-------|
| SECRET_KEY | `<gerar com: python -c "import secrets;print(secrets.token_urlsafe(48))">` |
| MONGO_URL | `mongodb+srv://user:pass@cluster.mongodb.net/actacv` |
| DB_NAME | `actacv` |
| CORS_ORIGINS | `https://seu-projeto.vercel.app` |
| RESEND_API_KEY | `re_e8zTccvu_Ndyp2PE421qGbL7t7v5GV6DJ` |
| SENDER_EMAIL | `noreply@controlador.cv` |

### Frontend (Vercel)
| Variavel | Valor |
|----------|-------|
| REACT_APP_BACKEND_URL | `https://actacv-api.onrender.com` |

---

## Checklist Pre-Deploy

- [ ] MongoDB Atlas configurado com connection string
- [ ] Backend no Render com todas as env vars
- [ ] Frontend no Vercel com REACT_APP_BACKEND_URL
- [ ] CORS_ORIGINS atualizado no backend
- [ ] Primeiro admin criado via create_admin.py
- [ ] Dominio controlador.cv verificado no Resend
- [ ] Testar login, convite, dashboard
