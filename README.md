# Portal ACCTA

Portal institucional e sistema de gestão associativa para a **Associação dos Controladores de Tráfego Aéreo de Cabo Verde**.

**Domínio:** [controlador.cv](https://controlador.cv)

---

## Funcionalidades

### Área Pública
- Homepage institucional com apresentação da profissão
- Página de transparência financeira com métricas públicas
- Galeria de fotos (álbuns aprovados pelo admin)
- Validador de carteiras via QR Code
- Formulário de contacto (envia email para secretariado)

### Portal do Associado (Área Privada)
- Dashboard personalizado com feed de atividade recente
- Carteira digital com QR Code SHA-256
- Gestão financeira (contribuições, export PDF/CSV)
- Sistema de votações democráticas
- Gestão de projetos (CRUD, tarefas, milestones, orçamento)
- Eventos e agenda com inscrição
- Documentos internos (upload/download)
- Mural de comunicação (posts, likes, moderação)
- Galeria de fotos privada (workflow de aprovação)
- Clube de benefícios com validação QR Code
- Central de notificações (SSE real-time + fallback 30s)

### Área Administrativa
- Gestão de utilizadores (CRUD, cargos, privilégios)
- Dashboard financeiro com gráficos (DRE, cash flow)
- Aprovação de fotos e gestão de álbuns
- Audit logs completo de ações administrativas
- Broadcast de notificações para todos os sócios

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React 19 + Tailwind CSS 3 + shadcn/ui + Framer Motion + Recharts + Craco |
| Backend | FastAPI (Python 3.11) + asyncpg (PostgreSQL/Supabase) |
| Base de Dados | PostgreSQL (Supabase) |
| Autenticação | JWT HS256 (24h) + RBAC (admin, financeiro, moderador, socio) |
| Email | Resend API |
| CI/CD | GitHub Actions → SSH → Nginx + Supervisord |

---

## Desenvolvimento Local

### Backend
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend
```bash
cd frontend
yarn install
yarn start
```

### Seed de dados
```bash
python scripts/seed_data.py
```

---

## Variáveis de Ambiente

**Backend** (`backend/.env`):
```env
SECRET_KEY=<chave-secreta-forte>
DATABASE_URL=postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
CORS_ORIGINS=http://localhost:3000
FRONTEND_URL=http://localhost:3000
RESEND_API_KEY=re_xxxxxxxxxxxxx
SENDER_EMAIL=noreply@controlador.cv
```

**Frontend** (`frontend/.env`):
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

---

## Regras de Negócio

- Quotas são descontadas em folha salarial — não existem cotas pendentes
- Statuses de sócio: `ativo`, `inativo`, `pendente_convite` — sem "inadimplente"
- Fotos submetidas por sócios requerem aprovação do admin antes de serem visíveis
- Modo escuro desativado por decisão de design

---

## Documentação

| Documento | Descrição |
|-----------|-----------|
| [DEPLOY.md](DEPLOY.md) | Pipeline CI/CD e secrets do GitHub |
| [HOSTINGER_DEPLOY.md](HOSTINGER_DEPLOY.md) | Checklist completo para VPS Hostinger |
| [VERCEL_DEPLOY.md](VERCEL_DEPLOY.md) | Deploy alternativo Vercel + Render + MongoDB Atlas |
| [SSH_SETUP.md](SSH_SETUP.md) | Configuração de chave SSH para GitHub Actions |
| [PROJETO_ACCTA.md](PROJETO_ACCTA.md) | Detalhes técnicos e arquitetura |
| [ANALISE_MELHORIAS.md](ANALISE_MELHORIAS.md) | Status de implementação e melhorias futuras |
| [SISTEMA_NOTIFICACOES.md](SISTEMA_NOTIFICACOES.md) | Documentação do sistema de notificações |

---

Desenvolvido com Emergent AI | 2025–2026
