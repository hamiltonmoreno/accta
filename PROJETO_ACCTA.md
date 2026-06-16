# Portal ACCTA — Associação dos Controladores de Tráfego Aéreo de Cabo Verde

## Visão Geral

Portal institucional completo e Sistema de Gestão Associativa (SGA) para a ACCTA, oferecendo transparência institucional, eficiência administrativa, governança estatutária digital e valorização da profissão de Controlador de Tráfego Aéreo em Cabo Verde.

**URL Produção:** https://controlador.cv  
**API:** https://api.controlador.cv/api

---

## Funcionalidades

### Área Pública (Institucional)
- **Homepage Hero** — Apresentação institucional e da profissão
- **Sobre** — A associação e os órgãos sociais (corpos sociais dinâmicos via `/api/governance/corpos-sociais`)
- **Profissão** — Informação sobre os controladores de tráfego aéreo
- **Notícias / Blog** — Listagem com filtros e detalhe de artigo
- **Publicações públicas (Cat 5)** — Produção profissional dos sócios
- **Galeria de Fotos** — Álbuns públicos aprovados pelo admin
- **Benefícios e Eventos públicos**
- **Validador de Carteira** — Validação pública de carteiras via QR Code
- **Formulário de Contacto** — Email para o secretariado via Resend API

### Área Privada (Portal do Associado)
- **Dashboard Personalizado** — Resumo por perfil + feed de atividade recente
- **Carteira Digital** — Identificação com QR Code criptografado (SHA-256)
- **Gestão Financeira** — Quotas (desconto em folha), jóia, export PDF/CSV + **co-aprovações** de atos financeiros (Art. 54)
- **Votações / Polls** — Participação democrática
- **Gestão de Projetos** — CRUD com tarefas, milestones, comentários e orçamento
- **Eventos / Agenda** — Inscrição e calendário
- **Documentos** — Atas, estatutos, balancetes (controlo de acesso)
- **Mural de Comunicação** — Posts, pesquisa, filtros, likes e moderação
- **Galeria Privada** — Upload com workflow de aprovação
- **Clube de Benefícios** — Descontos com validação QR Code
- **Notificações** — SSE em tempo real + broadcast admin + auto-triggers
- **Central de Ajuda** (`/ajuda`) — Secções filtradas por papel + pesquisa client-side
- **Regulamentos** internos versionados e **Ranking de participação**
- **Fins profissionais (Cat 5)** — Formações, publicações, defesa profissional, relações externas

### Governança Estatutária
- **Assembleias** — Convocatória, presenças, quórum, expediente, uso da palavra, moções e deliberações com voto
- **Eleições** — Listas, candidaturas, **voto secreto** (recibos + urna), proclamação que regista mandatos em `cargo_history`
- **Disciplina** — Sanções (suspensões, multas) por deliberação
- **Prestação de Contas** — Exercícios e balancetes (ciclo anual)
- **Comunicados** — Disparo combinado email + notificação in-app

### Participação dos Sócios
- Petições (com assinaturas), Propostas para a AG, Reclamações, Esclarecimentos e Nomeações de honorários

### Área Administrativa
- **Gestão de Utilizadores** — CRUD com papel, função e privilégios
- **Gestão de Cargos** — Promover/demover/transferir nos órgãos sociais (`/admin/cargos`)
- **Pedidos de Inscrição** — Aprovação de auto-registo
- **Dashboard Financeiro** — Receitas/despesas, DRE, cash flow (Recharts)
- **Aparência** — Marca + banners; **Notícias** e **Comunicados**
- **Galeria** — Aprovação de fotos e CRUD de álbuns
- **Assembleias / Eleições / Disciplinar**
- **Audit Logs** — Rastreio completo (com integridade HMAC) de ações administrativas

---

## Stack Técnico

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React 19 + Tailwind CSS 3 + shadcn/ui (New York) + Framer Motion + Recharts + Craco |
| Backend | FastAPI (Python 3.11) + asyncpg (PostgreSQL/Supabase) |
| Base de Dados | PostgreSQL (Supabase) — DAO assíncrono Mongo-compatível sobre asyncpg em `database.py` |
| Autenticação | JWT HS256 (24h, cookie httpOnly) + RBAC + privilégios aditivos + cargos estatutários |
| Email | Resend API |
| Real-time | SSE (Server-Sent Events) + fallback polling 30s |
| Deploy | Frontend → Vercel · Backend → Docker/GHCR no VPS (nginx-proxy-manager) |
| Design | Identidade ACCTA — **neutro + acento único**: Carmesim #C7202F como identidade/destrutivo, Floresta #166534 como ação positiva, Grafite #3A3A3A, Open Sans, modo claro. Canónico: `/frontend-design` |

---

## Credenciais de Demonstração

| Perfil | Email | Senha |
|--------|-------|-------|
| Administrador | admin@controlador.cv | admin123 |
| Financeiro | financeiro@controlador.cv | fin123 |
| Sócio Ativo | socio1@controlador.cv | socio123 |

> Credenciais de **seed/demonstração** — em produção usar passwords fortes via `create_admin.py`.

---

## Regras de Negócio Importantes

- Quotas são descontadas em folha salarial — não existe estado "inadimplente"
- Statuses de sócio: `ativo`, `inativo`, `pendente_convite`, `pendente_aprovacao`, `rejeitado`
- Uma pessoa = uma conta para a vida; `member_id` é **imutável**. Contas `technical` ficam fora de listagens/scoring/AGAs
- Cargos institucionais persistidos como **chave canónica** (`dir_tesoureiro`, nunca o rótulo); só atribuídos via `/admin/cargos` ou proclamação eleitoral
- RBAC = `role OR privilege` (privilégios são overlays aditivos)
- Modo escuro **desativado** por decisão de design
- Fotos submetidas por sócios requerem aprovação do admin antes de serem visíveis
- QR Code da carteira usa hash SHA-256 com salt interno — não alterar sem invalidar todos os QR Codes existentes

---

## Tabelas / coleções lógicas (PostgreSQL)

> Cada coleção lógica é uma tabela PostgreSQL `(pk bigserial, doc jsonb)` — **65 tabelas** no total (= `len(database.COLLECTIONS)`). O acesso faz-se via um DAO assíncrono Mongo-compatível sobre asyncpg em `database.py`. Não há `_id` real: cada documento traz um `id` `str(uuid4())`. Schema e índices são criados por `ensure_schema()`.

| Domínio | Coleções |
|---------|----------|
| Núcleo | `users`, `transactions`, `invoices`, `finance_settings`, `finance_settings_history`, `audit_logs`, `notifications` |
| Conteúdo | `posts`, `documents`, `document_accesses`, `wall_posts`, `wall_comments`, `gallery_albums`, `gallery_photos`, `page_banners`, `brand_settings` |
| Votações & Projetos | `polls`, `user_votes`, `projects`, `project_tasks`, `project_comments`, `project_expenses`, `project_milestones`, `events` |
| Governança | `assembleias`, `assembleia_presencas`, `assembleia_deliberacoes`, `assembleia_palavra`, `assembleia_votos`, `assembleia_voto_receipts`, `assembleia_voto_ballots`, `assembleia_mocoes`, `assembleia_expediente`, `assembleia_convidados`, `eleicoes`, `eleicao_listas`, `eleicao_voter_receipts`, `eleicao_ballots`, `sancoes`, `atos` |
| Prestação de contas | `exercicios`, `balancetes`, `regulamentos`, `regulamento_versoes` |
| Participação | `peticoes`, `peticao_assinaturas`, `propostas_ag`, `reclamacoes`, `esclarecimentos`, `patrocinios`, `honorarios_nominations` |
| Comunicação | `comunicados` |
| Ranking | `member_scores`, `ranking_ajustes`, `ranking_settings` |
| Fins profissionais (Cat 5) | `formacoes`, `publicacoes`, `defesa_profissional`, `relacoes_externas` |
| Benefícios | `benefits`, `benefit_partners`, `benefit_validations` |
| Auth / Sistema | `password_resets`, `tokens_revoked`, `login_attempts` |

---

## Modelo de Governança & Identidade

Fonte de verdade única: **`backend/governance.py`** (órgãos, cargos, categorias, privilégios) + **`backend/permissions.py`** (helpers RBAC/elegibilidade). `models.py` apenas re-exporta `CARGOS`/`CARGO_KEYS`/`CARGO_DEFAULTS`/`CARGO_SEATS`/`CARGOS_ORGAOS_SOCIAIS`. O frontend lê `GET /api/governance/structure` (canónico).

**Órgãos sociais** (mandato de 3 anos): Assembleia Geral (deliberativo), Direção (executivo), Conselho Fiscal (fiscalizador).

**Cargos estatutários** (chaves canónicas): `ag_presidente`, `ag_vice_presidente`, `ag_secretario`; `dir_presidente`, `dir_vice_presidente`, `dir_secretario`, `dir_tesoureiro`, `dir_vogal`; `cf_presidente`, `cf_relator`, `cf_vogal`. Default: `socio`.

**Categorias de membro:** `fundador`, `ordinario` (com voto), `honorario` (sem voto).

**Roles (acesso coarse):** `admin`, `financeiro`, `moderador`, `socio`.  
**Privilégios (overlays aditivos):** `manage_users`, `manage_finances`, `manage_events`, `manage_documents`, `moderate_content`, `manage_benefits`, `view_audit_logs`, `view_finances_readonly`, `emit_cf_parecer`, `send_comunicados`, `manage_ranking`.

**Helpers (permissions.py):** `is_mesa_ag`, `is_direcao`, `is_conselho_fiscal`, `is_voting_member`, `is_eligible_for_office`, `can_convene_assembleia`, `can_emit_parecer_cf`.

---

## Roles & Privilégios

| Role | Acesso |
|------|--------|
| `admin` | Sistema completo — utilizadores, finanças, moderação, governança, audit logs |
| `financeiro` | Módulo financeiro, transações, faturas, configurações |
| `moderador` | Moderação de conteúdo — posts do mural, fotos da galeria, notícias |
| `socio` | Portal do associado — dashboard, carteira, eventos, votações, mural, participação |

---

## Estrutura do Projeto

```
/app
├── .github/workflows/
│   ├── ci.yml              # CI — lint + testes em cada push
│   └── deploy.yml          # CD — gate → build imagem → GHCR → VPS (branch main)
├── .claude/
│   ├── agents/             # Subagentes especializados (debugger, reviewer, etc.)
│   ├── commands/           # Comandos de utilizador (/deploy, /fix-issue, etc.)
│   ├── hooks/              # pre-commit (ruff/eslint), lint-on-save
│   ├── rules/              # Regras contextuais (api, database, models, frontend)
│   ├── skills/             # Skills invocáveis (frontend-design, backend-api, ui-ux-pro-max)
│   └── settings.json       # Configuração de permissões e hooks
├── frontend/
│   ├── src/
│   │   ├── components/ui/  # shadcn/ui (40+ componentes)
│   │   ├── components/     # NotificationBell, PollResults, ACCTALogo, etc.
│   │   ├── contexts/       # AuthContext, NotificationContext
│   │   ├── layouts/        # PrivateLayout (sidebar), PublicLayout (marketing)
│   │   ├── pages/public/   # 16 páginas públicas (Home, Sobre, Profissao, Galeria…)
│   │   ├── pages/private/  # 42 páginas privadas (Dashboard, Financeiro, Assembleias…)
│   │   └── utils/api.js    # Axios client + grupos de API
│   ├── vercel.json         # SPA fallback + cache imutável + cabeçalhos de segurança
│   └── tailwind.config.js
├── backend/
│   ├── server.py           # FastAPI entry point + CORS + rate limiting
│   ├── database.py         # Pool asyncpg + DAO Mongo-compatível + ensure_schema()
│   ├── auth.py             # JWT criação/validação + bcrypt + invalidação por password_changed_at
│   ├── models.py           # Pydantic models (request/response)
│   ├── governance.py       # Órgãos, cargos, categorias, privilégios (fonte de verdade)
│   ├── permissions.py      # Helpers RBAC / elegibilidade
│   ├── helpers.py          # create_notification, create_audit_log, notify_*
│   ├── email_service.py    # Integração Resend (convite, reset, boas-vindas, contacto, comunicados)
│   └── routes/             # 32 módulos de rotas (um por domínio)
├── scripts/                # create_admin, seed_*, migrate_*, rebuild_ranking…
├── docs/                   # runbook de deploy + superpowers
├── tasks/                  # todo.md + lessons.md
└── backend/tests/          # Suite pytest (unit/in-process + integração/live)
```

---

Desenvolvido por Hamilton Vicente | 2025–2026
