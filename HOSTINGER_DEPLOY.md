# Checklist de Deploy — Hostinger VPS (ACTACV)

> Guia prático, passo-a-passo, para pôr o Portal ACTACV a correr no seu VPS da Hostinger.
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
# Python 3.11 + Node 20 + MongoDB 7 + Nginx + Supervisor + Certbot
apt install -y software-properties-common curl gnupg git supervisor nginx certbot python3-certbot-nginx

# Python 3.11
add-apt-repository ppa:deadsnakes/ppa -y
apt install -y python3.11 python3.11-venv python3-pip

# Node.js 20 + Yarn
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
npm install -g yarn

# MongoDB 7
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
apt update && apt install -y mongodb-org
systemctl enable --now mongod
```

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
MONGO_URL=mongodb://localhost:27017
DB_NAME=accta_portal
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

### 3.1 Criar ficheiro de configuração
```bash
sudo tee /etc/nginx/sites-available/accta <<'EOF'
server {
    listen 80;
    server_name controlador.cv www.controlador.cv;

    client_max_body_size 20M;

    # API → Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE (Server-Sent Events) — notificações em tempo real
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 24h;
    }

    # Uploads servidos pelo backend
    location /uploads/ {
        proxy_pass http://127.0.0.1:8001;
    }

    # Frontend (build estático)
    location / {
        root /app/frontend/build;
        try_files $uri /index.html;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/accta /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

### 3.2 Ativar HTTPS (Let's Encrypt)
```bash
sudo certbot --nginx -d controlador.cv -d www.controlador.cv
# Responde: email → aceita termos → redirecionar HTTP→HTTPS (opção 2)
```

> Renovação automática já está ativa via `systemctl status certbot.timer`.

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

## 🧪 Comandos úteis do dia-a-dia

```bash
# Ver logs do backend ao vivo
sudo tail -f /var/log/supervisor/backend.err.log

# Ver logs do Nginx
sudo tail -f /var/log/nginx/error.log

# Reiniciar serviços manualmente
sudo supervisorctl restart backend
sudo systemctl reload nginx

# Backup da base de dados
mongodump --db accta_portal --out /home/deploy/backups/$(date +%F)

# Verificar SSL
sudo certbot certificates
```

---

## 🚨 Troubleshooting

| Sintoma | Causa provável | Solução |
|---------|----------------|---------|
| `502 Bad Gateway` | Backend não arrancou | `sudo supervisorctl status` e ler logs |
| Email de convite não chega | Domínio não verificado no Resend | Validar DNS `controlador.cv`/`controlador.cv` no dashboard Resend. Enquanto não estiver validado, o link aparece na resposta da API |
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
- [ ] Backup automático do MongoDB configurado (cron)
- [ ] GitHub Actions faz deploy verde após push para `main`

---

**Dúvida rápida?** Os ficheiros-chave são:
- Pipeline CI/CD: `/app/.github/workflows/deploy.yml`
- Guia genérico: `/app/DEPLOY.md`
- Este checklist Hostinger: `/app/HOSTINGER_DEPLOY.md`
