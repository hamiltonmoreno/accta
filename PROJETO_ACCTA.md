# Portal ACCTA — Associação dos Controladores de Tráfego Aéreo de Cabo Verde

## Visão Geral

Portal institucional completo e Sistema de Gestão Associativa (SGA) para a ACCTA, oferecendo transparência institucional, eficiência administrativa e valorização da profissão de Controlador de Tráfego Aéreo em Cabo Verde.

**URL Produção:** https://controlador.cv  
**API:** https://controlador.cv/api

---

## Funcionalidades

### Área Pública (Institucional)
- **Homepage Hero** — Apresentação impactante com temática aeronáutica
- **Sobre a Profissão** — Informações completas sobre controladores de tráfego aéreo
- **Transparência Financeira** — Página pública com métricas e prestação de contas (dados reais da API)
- **Galeria de Fotos** — Álbuns públicos aprovados pelo admin
- **Validador de Carteira** — Validação pública de carteiras de sócios via QR Code
- **Formulário de Contacto** — Envia email para secretariado@controlador.cv via Resend API

### Área Privada (Portal do Associado)
- **Dashboard Personalizado** — Resumo financeiro, votações abertas, eventos próximos, feed de atividade recente
- **Carteira Digital** — Identificação digital com QR Code criptografado (SHA-256)
- **Gestão Financeira** — Acompanhamento de contribuições (desconto em folha salarial) com export PDF/CSV
- **Sistema de Votações** — Participação democrática em decisões da associação
- **Gestão de Projetos** — CRUD completo com tarefas, milestones, comentários e orçamento
- **Eventos/Agenda** — Sistema de eventos com inscrição e calendário
- **Documentos** — Acesso a atas, estatutos e balancetes (upload/download admin)
- **Mural de Comunicação** — Canal de interação entre sócios com pesquisa, filtros, likes e moderação
- **Galeria de Fotos Privada** — Upload com workflow de aprovação, álbuns privados
- **Clube de Benefícios** — Descontos exclusivos com validação QR Code
- **Notificações Avançadas** — Central de notificações com broadcast admin, filtros por tipo, auto-trigger, SSE real-time

### Área Administrativa
- **Gestão de Utilizadores** — CRUD com alteração de cargo, função e privilégios
- **Dashboard Financeiro** — Gráficos de receitas/despesas, DRE, cash flow (Recharts)
- **Gestão de Galeria** — Aprovação de fotos, CRUD de álbuns
- **Audit Logs** — Rastreio completo de ações administrativas

---

## Stack Técnico

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React 19 + Tailwind CSS 3 + shadcn/ui (New York) + Framer Motion + Recharts + Craco |
| Backend | FastAPI (Python 3.11) + asyncpg (PostgreSQL/Supabase) |
| Base de Dados | PostgreSQL (Supabase) — DAO assíncrono Mongo-compatível sobre asyncpg em database.py |
| Autenticação | JWT HS256 (24h expiry) + RBAC (admin, financeiro, moderador, socio) |
| Email | Resend API |
| Real-time | SSE (Server-Sent Events) + fallback polling 30s |
| CI/CD | GitHub Actions → SSH → Nginx + Supervisord |
| Design | Identidade ACCTA — **neutro + acento único**: Carmesim #C7202F só como acento contido (1 botão primário/tela, nunca texto em fundo escuro), Grafite #3A3A3A, Open Sans, modo claro. Canônico: `/frontend-design` |

---

## Credenciais de Demonstração

| Perfil | Email | Senha |
|--------|-------|-------|
| Administrador | admin@controlador.cv | admin123 |
| Financeiro | financeiro@controlador.cv | fin123 |
| Sócio Ativo | socio1@controlador.cv | socio123 |

---

## Regras de Negócio Importantes

- Quotas são descontadas em folha salarial — não existem cotas pendentes
- Statuses de sócio: `ativo`, `inativo`, `pendente_convite` — sem "inadimplente"
- Modo escuro **desativado** por decisão de design
- Fotos submetidas por sócios requerem aprovação do admin antes de serem visíveis
- QR Code da carteira usa hash SHA-256 com salt interno — não alterar sem invalidar todos os QR Codes existentes

---

## Tabelas / coleções lógicas (PostgreSQL)

> Cada coleção lógica é uma tabela PostgreSQL `(pk bigserial, doc jsonb)` — 27 tabelas no total. O acesso faz-se via um DAO assíncrono Mongo-compatível sobre asyncpg em `database.py`.

| Coleção | Descrição |
|------------|-----------|
| `users` | Sócios, admins, financeiro, moderadores |
| `transactions` | Contribuições financeiras (desconto em folha) |
| `invoices` | Faturas e recibos |
| `projects` | Projetos com tarefas e milestones |
| `events` | Eventos e inscrições |
| `wall_posts` | Posts do mural de comunicação |
| `notifications` | Notificações in-app por utilizador |
| `polls` | Votações com opções e votos |
| `documents` | Documentos internos (atas, estatutos, balancetes) |
| `gallery_albums` | Álbuns da galeria (públicos e privados) |
| `gallery_photos` | Fotos com workflow de aprovação |
| `audit_logs` | Registo de ações administrativas |
| `password_resets` | Tokens de reset de password |
| `finance_settings` | Configurações do módulo financeiro |

---

## Roles & Privilégios

| Role | Acesso |
|------|--------|
| `admin` | Sistema completo — utilizadores, finanças, moderação, audit logs |
| `financeiro` | Módulo financeiro, transações, faturas, configurações |
| `moderador` | Moderação de conteúdo — posts do mural, fotos da galeria |
| `socio` | Portal do associado — dashboard, carteira, eventos, votações, mural |

---

## Estrutura do Projeto

```
/app
├── .github/workflows/
│   ├── ci.yml              # CI — lint + testes em cada push
│   └── deploy.yml          # CD — deploy para produção (branch main)
├── .claude/
│   ├── agents/             # Subagentes especializados (debugger, reviewer, etc.)
│   ├── commands/           # Comandos de utilizador (/deploy, /fix-issue, etc.)
│   ├── hooks/              # pre-commit (ruff/eslint), lint-on-save (ruff format)
│   ├── rules/              # Regras contextuais por ficheiro (frontend, api, db)
│   ├── skills/             # Skills invocáveis (design system, api boilerplate)
│   └── settings.json       # Configuração de permissões e hooks
├── frontend/
│   ├── src/
│   │   ├── components/ui/  # shadcn/ui (40+ componentes)
│   │   ├── components/     # NotificationBell, PollResults, ACCTALogo, etc.
│   │   ├── contexts/       # AuthContext, NotificationContext
│   │   ├── layouts/        # PrivateLayout (sidebar), PublicLayout (marketing)
│   │   ├── pages/public/   # HomePage, LoginPage, Transparencia, Galeria, etc.
│   │   ├── pages/private/  # Dashboard, Financeiro, Projetos, Votacoes, etc.
│   │   └── utils/api.js    # Axios client + todos os grupos de API (40+ endpoints)
│   └── tailwind.config.js
├── backend/
│   ├── server.py           # FastAPI entry point + CORS + rate limiting
│   ├── database.py         # Pool asyncpg (PostgreSQL/Supabase) + schema/índices via ensure_schema()
│   ├── auth.py             # JWT criação/validação + bcrypt
│   ├── models.py           # Pydantic models (request/response)
│   ├── helpers.py          # create_notification, create_audit_log, notify_*
│   ├── email_service.py    # Integração Resend (convite, reset, boas-vindas, contacto)
│   └── routes/             # 18 módulos de rotas (um por domínio)
├── scripts/
│   ├── seed_data.py        # Seed de dados de demonstração
│   ├── create_admin.py     # Criar utilizador admin
│   └── seed_gallery.py     # Seed de galeria
├── tasks/
│   ├── todo.md             # Plano de tarefas ativo
│   └── lessons.md          # Lições acumuladas de sessões anteriores
└── tests/                  # Testes pytest (backend)
```

---

Desenvolvido com Emergent AI | 2025–2026
