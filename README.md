# Portal ACCTA

Portal institucional e Sistema de Gestão Associativa (SGA) para a **Associação dos Controladores de Tráfego Aéreo de Cabo Verde**.

**Domínio:** [controlador.cv](https://controlador.cv)

---

## Funcionalidades

### Área Pública
- Homepage institucional com apresentação da profissão de Controlador de Tráfego Aéreo
- Página **Sobre** (a associação, órgãos sociais dinâmicos via API) e **Profissão**
- Notícias / blog institucional com filtros e página de detalhe
- Publicações profissionais públicas (Cat 5)
- Galeria de fotos (álbuns aprovados pelo admin)
- Benefícios e eventos públicos
- Validador de carteiras via QR Code
- Formulário de contacto (envia email para o secretariado via Resend)
- Criação de conta / login / recuperação de password

### Portal do Associado (Área Privada)
- Dashboard personalizado por perfil com feed de atividade recente
- Carteira digital com QR Code SHA-256
- Gestão financeira (quotas por desconto em folha, jóia, export PDF/CSV) + **co-aprovações** de atos financeiros (Art. 54); despesas/receitas de eventos e receitas de multas integradas no caixa central (`transactions`)
- Sistema de votações / polls
- Gestão de projetos (CRUD, tarefas, milestones, comentários, orçamento)
- Eventos e agenda com inscrição
- Documentos internos (upload/download com controlo de acesso)
- Mural de comunicação (posts, likes, moderação)
- Galeria de fotos privada (workflow de aprovação)
- Clube de benefícios com validação QR Code
- **Central de notificações** — SSE em tempo real + fallback de polling 30s
- **Central de Ajuda** (`/ajuda`) com secções filtradas por papel e pesquisa
- Regulamentos internos (versionados) e **Ranking de participação** do sócio
- **Fins profissionais (Cat 5)** — formações, publicações, defesa profissional, relações externas

### Governança Estatutária
- **Assembleias** — convocatória, presenças, quórum, expediente, uso da palavra, moções e deliberações com voto
- **Eleições** — listas, candidaturas, **voto secreto** (recibos + urna), proclamação que regista mandatos
- **Disciplina** — sanções (suspensões, multas) por deliberação
- **Prestação de contas** — exercícios e balancetes (ciclo anual)
- **Comunicados** — disparo combinado email + notificação in-app

### Participação dos Sócios
- Petições (com recolha de assinaturas), Propostas para a AG, Reclamações, Esclarecimentos e Nomeações de honorários

### Área Administrativa
- Gestão de utilizadores (CRUD, papéis, privilégios) e **gestão de cargos** (promover/demover/transferir nos órgãos sociais)
- Aprovação de pedidos de inscrição (auto-registo)
- Dashboard financeiro com gráficos (DRE, cash flow)
- Gestão de aparência (marca + banners), notícias e comunicados
- Aprovação de fotos e gestão de álbuns
- Administração de assembleias, eleições e ações disciplinares
- Audit logs completo (HMAC) de ações administrativas

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React 19 + Tailwind CSS 3 + shadcn/ui + Framer Motion + Recharts + Craco |
| Backend | FastAPI (Python 3.11) + asyncpg (PostgreSQL/Supabase via DAO Mongo-compatível) |
| Base de Dados | PostgreSQL (Supabase) — 65 tabelas `(pk bigserial, doc jsonb)` |
| Autenticação | JWT HS256 (24h, cookie httpOnly) + RBAC (admin, financeiro, moderador, socio) + privilégios aditivos + cargos estatutários |
| Email | Resend API |
| Real-time | SSE (Server-Sent Events) + fallback polling 30s |
| Deploy | Frontend → Vercel · Backend → Docker/GHCR no VPS (atrás de nginx-proxy-manager) |
| Package Manager | Yarn (frontend), pip + venv (backend) |

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

- Quotas são descontadas em folha salarial — não existe estado "inadimplente"
- Statuses de sócio: `ativo`, `inativo`, `pendente_convite`, `pendente_aprovacao`, `rejeitado`
- Uma pessoa = uma conta para a vida; `member_id` imutável. Contas `technical` (ex.: sistema) ficam fora de listagens/scoring/AGAs
- Cargos institucionais persistidos como chave canónica (`dir_tesoureiro`, nunca o rótulo); fonte de verdade em `backend/governance.py`
- RBAC = `role OR privilege` (privilégios são overlays aditivos)
- Fotos submetidas por sócios requerem aprovação do admin antes de serem visíveis
- Modo escuro desativado por decisão de design
- QR Code da carteira usa hash SHA-256 com salt interno — imutável em produção

---

## Documentação

| Documento | Descrição |
|-----------|-----------|
| [CLAUDE.md](CLAUDE.md) | Project Brain — convenções, stack, regras e arquitetura (fonte de verdade para agentes) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Fluxo de trabalho Git (GitFlow), commits e proteção de branches |
| [PROJETO_ACCTA.md](PROJETO_ACCTA.md) | Detalhes técnicos, coleções e modelo de governança |
| [DEPLOY.md](DEPLOY.md) | Pipeline CI/CD do backend (deploy.yml) e secrets do GitHub |
| [HOSTINGER_DEPLOY.md](HOSTINGER_DEPLOY.md) | Topologia de produção e setup do VPS (Docker/GHCR + nginx-proxy-manager) |
| [VERCEL_DEPLOY.md](VERCEL_DEPLOY.md) | Deploy do frontend no Vercel + base de dados no Supabase |
| [docs/runbook-deploy-backend-via-b.md](docs/runbook-deploy-backend-via-b.md) | Runbook de deploy manual do backend (Via B) |
| [SSH_SETUP.md](SSH_SETUP.md) | Configuração de chave SSH para o GitHub Actions |
| [SISTEMA_NOTIFICACOES.md](SISTEMA_NOTIFICACOES.md) | Sistema de notificações (SSE + tipos + auto-triggers) |
| [ANALISE_MELHORIAS.md](ANALISE_MELHORIAS.md) | Estado de implementação e melhorias futuras |

---

Desenvolvido por Hamilton Vicente | 2025–2026
