# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Portal ACCTA — Project Brain**

---

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project context

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes — don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests — then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

---

## Task Management

1. **Plan First** — Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan** — Check in before starting implementation on complex tasks
3. **Track Progress** — Mark items complete as you go
4. **Explain Changes** — High-level summary at each step
5. **Document Results** — Add review section to `tasks/todo.md` when done
6. **Capture Lessons** — Update `tasks/lessons.md` after any correction

---

## Core Principles

- **Simplicity First** — Make every change as simple as possible. Impact minimal code.
- **No Laziness** — Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact** — Only touch what's necessary. No side effects, no new bugs.

---

## Stop Conditions

STOP and check in with the user when:

- A task requires **dropping or migrating data** in PostgreSQL/Supabase (destructive schema change)
- A task requires **changing the JWT secret** or auth algorithm (all sessions invalidated)
- A task requires **modifying CORS origins** in production
- A task would **remove a route** that the frontend actively calls
- A task would **change a Pydantic model** in a way that breaks existing documents in DB
- **CI is failing** and the fix isn't obvious after one investigation pass
- **Two consecutive approaches have failed** — re-plan before attempting a third
- The scope of a "small fix" expands to touch **more than 3 files**
- Any action that **sends emails** to real users (invite, reset, welcome)
- Any action that **pushes to `main`** — always confirm first (`main` is reached
  only via a release/hotfix PR; see Git Workflow)

---

## Git Workflow (GitFlow)

The project uses **GitFlow** — `CONTRIBUTING.md` is the canonical source; this is
the summary and defers to it on any conflict.

- `main` — production; every merge is a release. **Never push/PR directly to it.**
- `develop` — integration; **everything goes here first.**
- `feature/*` → branch off `develop`, PR back into `develop`.
- `release/*` → branch off `develop`, PR into `main`, then merge back to `develop`; tag the release.
- `hotfix/*` → branch off `main`, PR into `main` **and** `develop`.

Normal path: `feature/* → develop → (release) → main`. Commits follow
Conventional Commits with a scope (`feat(escopo): …`, `fix(escopo): …`).

---

## Stack

- **Frontend**: React 19 + Tailwind CSS 3 + shadcn/ui + Framer Motion + Recharts + Craco
- **Backend**: FastAPI (Python 3.11) + asyncpg (PostgreSQL/Supabase via a Mongo-compatible async DAO in `database.py`)
- **Database**: PostgreSQL (Supabase) — 64 tables `(pk bigserial, doc jsonb)`, one per logical collection (= `len(database.COLLECTIONS)`): `users`, `transactions`, `projects`, `events`, `wall_posts`, `notifications`, `polls`, `documents`, `gallery_albums`, `gallery_photos`, `audit_logs`, `password_resets`, `finance_settings`, plus governança: `assembleias`, `assembleia_presencas`, `assembleia_deliberacoes`, `eleicoes`, `eleicao_listas`, `eleicao_voter_receipts`, `eleicao_ballots`, `sancoes`, `finance_settings_history`; prestação de contas: `exercicios`, `balancetes`, `regulamentos`, `regulamento_versoes`; comunicação: `comunicados`, …
- **Auth**: JWT (HS256, 24h expiry) + RBAC (admin, socio, financeiro, moderador)
- **Email**: Resend API
- **Deploy**: GitHub Actions CI/CD → SSH → Nginx + Supervisord
- **Package Manager**: Yarn (frontend), pip + venv (backend)

---

## Commands

```bash
# Frontend
cd frontend && yarn install                                      # Install deps
cd frontend && yarn start                                        # Dev server
cd frontend && yarn build                                        # Production build
cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60 # Lint

# Backend
cd backend && pip install -r requirements.txt
cd backend && uvicorn server:app --reload --port 8001
cd backend && ruff check .                                       # Lint
cd backend && ruff format .                                      # Format
cd backend && pytest                                             # Tests

# Scripts
python scripts/seed_data.py     # Seed demo data
python scripts/create_admin.py  # Create admin user
python scripts/seed_gallery.py  # Seed gallery data
```

---

## Conventions

- **Language** — keep two axes separate; conflating them is what causes PT/EN drift:
  - **Conversation** (chat replies / explanations to the user): **PT**. This is the
    *communication* language and is **independent of the code** — "talk to me in
    Portuguese" never means "write code in Portuguese".
  - **User-facing text** (UI strings, HTTPException `detail`, notification
    titles/bodies, emails): **PT**.
  - **Identifiers** (functions, variables, jsonb fields): generic/technical names in
    **EN** (`create_transaction`, `update`, `status`, `amount`, `category`,
    `created_by`, `query`); **domain terms with no clean English equivalent stay PT**
    (`joia`, `quota`, `socio`, `exercicio`, `balancete`, `assembleia`, `deliberacao`,
    `sancao`, `aprovar`/`submeter`/`reabrir`). **Do NOT bulk-rename existing
    identifiers** — they are tied to `jsonb` keys, indexes, the API and the frontend.
  - **Comments & docstrings**: **PT** (already the majority — do not add EN ones).
  - When editing a file, **match the surrounding code**; do not switch a file's
    language to follow the chat language.
- **Components**: Functional components + hooks only; shadcn/ui (New York style) for primitives
- **Styling**: Tailwind CSS only — no inline styles. **Neutral-led**: white/`#F5F5F5` surfaces, Grafite `#3A3A3A` text. **Action color is semantic**: the single primary **positive** button per view is **Floresta `#166534`** (hover `#14532D`; Guardar/Confirmar/Criar/Aprovar/Entrar/Votar), and **Carmesim `#C7202F`** is brand identity + **destructive** (active nav, links-on-white, focus ring, logo; destructive = outline by default, solid only inside an irreversible confirm dialog) — neutral everywhere else, **never red text on dark/colored backgrounds**, never Carmesim as a positive primary. The **`/frontend-design` skill** (`.claude/skills/frontend-design/SKILL.md`) is the single source of truth for the full design system (color/contrast rules, button taxonomy, typography, spacing, animation) — follow it, don't hardcode tokens from elsewhere
- **Backend**: Async/await everywhere; Pydantic models for all request/response validation
- **Auth**: Role-based access check on every protected endpoint; audit log on every admin action
- **Identity, cargos & governança** (spec-identidade-cargos, **superada na
  taxonomia de cargos por `spec-governanca-estatutaria`**) — one person = one
  account for life. `account_type` is `member` (real sócio; missing ⇒ treated as
  member) or `technical` (system account like `admin@controlador.cv`:
  `member_id=None`, excluded from member listings/scoring/AGAs by default).
  `member_id` is **immutable** (not editable via `UserAdminUpdate`/API). `role`
  (admin/financeiro/moderador/socio) is the coarse access level; `privileges` are
  **additive overlays** (`role OR privilege`, e.g. `view_finances_readonly` for
  Conselho Fiscal). **The single source of truth for órgãos sociais, cargos,
  categorias de membro and privileges is `backend/governance.py`** (3 órgãos:
  Assembleia Geral / Direcção / Conselho Fiscal — with Relator, Secretário sem
  "-Geral", no Coordenações/Comissões). `cargo` is persisted as the **canonical
  key** (`dir_tesoureiro`, never the label `Tesoureiro`); `models.py` only
  re-exports `CARGOS`/`CARGO_KEYS`/`CARGO_DEFAULTS`/`CARGO_SEATS`/`CARGOS_ORGAOS_SOCIAIS`
  from governance. Institutional cargos are assigned only via `/admin/cargos`
  (promote/demote/transfer) and election proclamation, which record `cargo_history`
  mandates; never hand-edit a mandate. Frontend reads
  `GET /api/governance/structure` (canonical; `/users/meta/cargos` is a
  deprecated alias), never hard-codes them. RBAC/eligibility helpers live in
  `backend/permissions.py` (`is_mesa_ag`/`is_direcao`/`is_conselho_fiscal`/
  `is_voting_member`). Assembleias, eleições (voto secreto), disciplina and
  quota/jóia-by-deliberation are in `routes/{assembleias,eleicoes,sancoes}.py`
  and `governance.py`
- **No dark mode** — disabled by design decision, do not add
- **No inadimplente status** — quotas are payroll-deducted; statuses are
  `ativo` / `inativo` / `pendente_convite` / `pendente_aprovacao` / `rejeitado`
- **Photo approval workflow** — all gallery photos require admin approval before visibility
- **Notifications** — SSE real-time stream; fallback to 30s polling; **Web Push**
  (PWA) espelha todas as notificações in-app no celular (opt-in por dispositivo
  no Perfil; helper `dispatch_push` em `push_service.py` engatado em
  `create_notification`/`notify_*`)

---

## Environment Variables

| Scope | Variable |
|-------|----------|
| Frontend | `REACT_APP_BACKEND_URL` |
| Backend | `SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`, `FRONTEND_URL`, `RESEND_API_KEY`, `SENDER_EMAIL`, `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` |

> **Web Push (notificação no celular)** — `VAPID_*` alimentam o Web Push do PWA.
> Gerar o par com `python scripts/generate_vapid_keys.py` e definir as 3 vars no
> backend. **Sem elas, a feature fica desligada graciosamente** (endpoints
> `/api/push/*` devolvem 503 e o toggle no Perfil mostra-se inativo). Frontend
> obtém a chave pública via `GET /api/push/vapid-public-key` (sem rebuild).

---

## Project Structure

```
/app
├── frontend/src/
│   ├── components/ui/    # shadcn/ui (40+ components)
│   ├── components/       # Custom: NotificationBell, PollResults, ACCTALogo…
│   ├── contexts/         # AuthContext, NotificationContext
│   ├── layouts/          # PrivateLayout (sidebar), PublicLayout (marketing)
│   ├── pages/public/     # 16 public pages (Home, Login, Sobre, Profissao…)
│   ├── pages/private/    # 42 private pages (Dashboard, Financeiro, Assembleias…)
│   └── utils/api.js      # Axios client + all API groups
├── backend/
│   ├── server.py         # FastAPI app entry + CORS + rate limiting
│   ├── database.py       # PostgreSQL/asyncpg DAO (Mongo-compatible) + schema/indexes
│   ├── auth.py           # JWT creation/validation + bcrypt
│   ├── models.py         # Pydantic models (request/response)
│   ├── governance.py     # Órgãos, cargos, categorias, privilégios (source of truth)
│   ├── permissions.py    # RBAC / eligibility helpers
│   ├── helpers.py        # create_notification, create_audit_log, notify_*
│   ├── email_service.py  # Resend integration (invite, reset, welcome, comunicados)
│   └── routes/           # 32 route modules (one per domain)
├── tasks/
│   ├── todo.md           # Active task plan + progress
│   └── lessons.md        # Accumulated lessons from corrections
└── scripts/              # Admin + seed scripts
```

---

## Roles & Privileges

| Role | Access |
|------|--------|
| admin | Full system — users, finances, moderation, audit logs |
| financeiro | Finance module, transactions, quotas, settings |
| moderador | Content moderation — wall posts, gallery photos |
| socio | Member portal — dashboard, carteira, events, voting, mural |

---

## API Conventions

- All endpoints prefixed with `/api/`
- Auth: `Authorization: Bearer {token}` header
- File uploads: `multipart/form-data` to `/api/upload/{category}`
- Categories: `documents` (10MB), `proofs` (5MB), `logos` (2MB), `avatars` (2MB)
- Rate limits: login 10/min, forgot-password 3/min, default 200/min

---

## Repository Layout Gotcha

- The **git root is `accta-main/accta/`** (where `.git` lives) — operate here.
  `accta-main/` itself is NOT a git repo and contains a stale duplicate tree
  (`backend/`, `frontend/`, a second `CLAUDE.md`, …) that is **outside** the
  repo. Edits there are invisible to git. Always verify with
  `git rev-parse --show-toplevel`.
- The Bash tool's working directory **persists between calls** — a `cd backend`
  sticks for the next command. Prefer absolute paths or re-`cd` deliberately.

---

## Database Access Idiom (read before touching any route)

`database.py` is a hand-rolled **Mongo-compatible async DAO over PostgreSQL** —
not an ORM and not real MongoDB. Every logical "collection" is a Postgres table
`(pk bigserial, doc jsonb)`. Routes do:

```python
from database import db
doc = await db.users.find_one({"id": uid}, {"_id": 0, "password": 0})  # Mongo-style filter + projection
await db.users.update_one({"id": uid}, {"$set": {...}})
rows = await db.events.aggregate(pipeline).to_list(100)
```

- There is **no real `_id`** — documents carry an app-generated `str(uuid4())` `id`.
- Projections (`{"_id": 0, "password": 0}`) and `$set`/`$gte`/`$or`/aggregation
  pipelines are honored by the DAO. Never write raw SQL in routes; schema +
  indexes live in `ensure_schema()` in `database.py` (don't `create_index` from
  routes).
- The asyncpg pool is **created lazily** — importing `database` opens no socket,
  but `TestClient(app)` triggers app-startup which DOES connect.

---

## Testing Architecture

`backend/tests/` has **two distinct kinds of tests** — know which you're touching:

1. **Unit / in-process** (file does NOT `import requests`): drive route
   functions directly or via `TestClient`, using fixtures from
   `tests/conftest.py`. Run with no server/DB.
2. **Integration / live** (file `import requests` at top): hit
   `REACT_APP_BACKEND_URL` over HTTP against a **running server + seeded DB**.
   Without one they error with `ConnectionRefusedError` — that is expected
   locally, not a regression.

`conftest.py` provides:

- `mock_db` — MagicMock collections with `AsyncMock` methods. Only ~22
  collections are pre-wired; **`project_tasks` / `project_comments` /
  `project_expenses` / `project_milestones` are NOT** — wire them in-test
  (`mock_db.project_tasks = MagicMock(...)`, give `find_one`/`aggregate`
  `AsyncMock`s). It also patches `database.db`, `auth.db`, `helpers.db`, and
  every already-imported `routes.*` module's `db` (import the route module at
  test top so the patch lands).
- Role fixtures `admin_user` / `socio_user` / `financeiro_user` /
  `moderador_user` (+ `_dict` variants), `make_token` (forge JWTs),
  `client` (in-process `TestClient` — **connects to the DB on startup**, so
  `test_smoke.py` errors with `ConnectionRefused` when no Postgres is
  reachable; that is environmental, not a code failure).

Commands:

```bash
cd backend && pytest                                  # full suite (testpaths=tests, asyncio_mode=auto)
cd backend && pytest tests/test_users_routes.py       # one file
cd backend && pytest tests/test_x.py::TestCls::test_y # one test
cd backend && pytest -m unit                          # by marker (see pyproject.toml)
```

- **bcrypt must stay pinned at `4.0.1`** (it is, in `requirements.txt`). Newer
  bcrypt breaks `passlib`'s backend probe
  (`module 'bcrypt' has no attribute '__about__'`) → every password-hash test
  fails. If you create a venv, install that pin explicitly.
- A `@limiter.limit(...)` (slowapi) route can't be called directly with a fake
  request — it requires a real `starlette.requests.Request` and runs first.
  In unit tests, `monkeypatch.setattr(<route_module>.limiter, "enabled", False)`
  and pass a minimal real `Request(scope)`.

---

## Authoritative Rules & Skills

`.claude/rules/{api,database,models,frontend}.md` are auto-loaded and **override
generic assumptions**. Consult them before backend work — key invariants:
audit-log every admin write, RBAC check on every protected endpoint, no raw SQL
in routes, dates stored as ISO-8601 strings (never `datetime` in models), never
expose `password` in responses, email functions are a STOP condition on real
users.

`.claude/skills/` holds the **canonical project skills** — prefer them over
ad-hoc patterns:

- **`frontend-design`** — the single source of truth for the ACCTA design
  system: **neutral-led** (white/`#F5F5F5`, Grafite `#3A3A3A`), **Carmesim
  `#C7202F` as the single restrained accent** (no red-on-dark, ≤1 primary
  button/view), button taxonomy, allowed contrast pairs, Open Sans, glass
  surfaces, Framer Motion, no dark mode. Apply it for any UI work.
- **`ui-ux-pro-max`** — design-intelligence engine (pattern/UX/chart/layout),
  ACCTA-brand-locked; defers to `frontend-design` for all tokens.
- **`backend-api`** — scaffolds FastAPI endpoints with the required auth /
  RBAC / audit-log / notification boilerplate. Use it when adding endpoints.

ℹ️ **Source-of-truth hierarchy**: `frontend-design` is canonical. The mirrors
— `design_guidelines.json`, `.github/copilot-instructions.md`,
`.github/copilot-frontend.md`, `.claude/rules/frontend.md` — have been
reconciled to the neutral-led / single-accent system and each defers to the
skill on any conflict (the old "Aero-Swiss" legacy palette — Navy `#0A1F44` /
"Radar Green" `#00FF9C` / Outfit — has been fully removed). The duplicate
`../CLAUDE.md` outside the git root is still **not tracked and out of sync**;
this in-repo file is authoritative.

<!-- SPECKIT START -->
Feature Spec Kit ativa: `specs/010-aviso-deliberacao-pendente/` — **aviso à Direção de Ato
(Art. 54) pendente há > X dias** (X admin-configurável, default 7), **uma única vez** por Ato.
PLAN feito ([plan.md](specs/010-aviso-deliberacao-pendente/plan.md), branch
`feature/aviso-deliberacao-pendente`). Backend-only, zero deps novas. Disparo = **loop in-process
diário** (`asyncio.create_task` no startup do `server.py`, padrão non-fatal dos seeds); idempotência
por marca aditiva `Ato.overdue_notified_at`; X em `FinanceSettings.ato_overdue_dias` (editável pelo
`PATCH /api/finances/settings` admin existente); destinatários via `members_of_orgao("direcao")`
(exclui técnicos/inativos); entrega in-app (+push) reutilizada; **email fora do MVP**. Endpoint
opcional admin `POST /api/atos/notify-overdue` p/ disparo manual/verificação. Próximo: `/speckit-tasks`.
Last completed: `specs/009-notificacoes-push-celular-concluido/` — **notificações push
no celular (Web Push / PWA)**. Espelha **todas** as notificações in-app no dispositivo
do sócio com a app fechada (Android/desktop; iOS 16.4+ via PWA na Tela de Início), com
opt-in por dispositivo no Perfil. Backend: `push_service.py` (VAPID/`pywebpush`,
`dispatch_push` best-effort engatado em `create_notification`/`notify_*`, anti-SSRF
`is_safe_push_endpoint`, poda 404/410), `routes/push.py` (`/api/push/*` autenticados),
coleção `push_subscriptions`. Frontend: `sw.js` (push/notificationclick, cache v5),
`utils/push.js` (+deteção iOS-sem-PWA), `components/PushPrefs.js`. Degrada graciosamente
sem envs VAPID (503/no-op). **CONCLUÍDA, RELEASED v0.5.40 (#362→develop; release
#364→main) e DEPLOYED em prod Via B** (`sha-fae22c0eaab2`, 2026-06-28; rotas `/api/push/*`
gated→401, `push_enabled()`=True após **VAPID configurado em `/docker/accta/.env`**).
24 testes verdes, ruff limpo. Só residual: validação funcional em dispositivo real
(T028/T029, Princípio VII — dono). Zero deps frontend novas; 1 dep backend (`pywebpush`).
Last completed: `specs/008-lembrete-quotas-concluido/` — **lembrete informativo de quotas**
(transparência, **SEM inadimplência** — linguagem de cobrança proibida). Disparo **orientado
a evento**: ao gerar as quotas do mês (`POST /finances/generate-quotas`) substitui o aviso
genérico (que linkava `/financeiro`, gated — bug latente) por um **lembrete in-app por sócio**
(valor do período + total acumulado, link `/carteira`), só aos que receberam quota nova,
respeitando um **opt-out dedicado** (`quota_reminder_opt_out`, aditivo) e excluindo contas
`technical`/`inativo`. Email = **STOP/off no MVP** (decisão do dono). Backend:
`finances.py` (notify por-sócio + 1 aggregate de total, sem N+1), `database.py`
(`insert_quotas_atomic` devolve os `user_id` NOVOS, era `int`), `models.py` (+campo aditivo),
`comunicados.py` (`/me/email-preferences` grava só campos enviados). Frontend: 2.º toggle
em `perfil/EmailPrefs.js`. **CONCLUÍDA na branch (PR #360→develop)**; 49 testes verdes,
ruff/eslint limpos; T006/T010 (browser, Princípio VII) residual de validação manual do dono
pós-deploy. Toca `backend/` → release `develop→main` precisa de **Via B**. Zero deps novas.
Last completed: `specs/007-carteira-quotas-pdf-concluido/` — **exportar a carteira de
quotas do próprio sócio em PDF** (comprovativo pessoal de uso interno, marca ACCTA, só os
próprios dados). Endpoint self-service `GET /api/finances/me/quotas/pdf` + `_render_carteira`
em `routes/finances.py` (reutiliza a query de `/me/quotas` RBAC-safe + o gerador `fpdf`
*branded*); frontend: botão "Exportar Quotas (PDF)" na **Carteira Digital** (`/carteira`,
acessível a sócios — `MemberFinanceView`/`/financeiro` está gated). Nota de domínio: a
carteira **não tem estado por quota** (lançamentos efetivos, quotas por folha). **CONCLUÍDA
e RELEASED v0.5.38, em prod** (PR #357→develop; release #358→main; frontend Vercel + backend
Via B `sha-960e0b5367b2`; decisivo `/me/quotas/pdf` 404→401 — ver [[prod-backend-deployed-state]]).
14/14 tarefas, pytest 3/3, PDF verificado em navegador. Zero deps novas.
Anterior: `specs/006-ranking-perfil-ux-concluido/` — revisão **frontend-only** de
Ranking e Perfil: (US1) ranking responsivo no telemóvel (sem overflow a 360px); (US2)
distinção 1.º/2.º/3.º por forma+tom (Coroa carmesim / Medalha grafite / Award muted +
`sr-only`) e **posições contínuas a negrito** (corrige o rank-com-empates do servidor
4,4,4 → 4,5,6); (US3) fotos dos sócios via `UserAvatar` (`photo_url` já vinha no payload);
(US4) painel de notificações com margem 16px nos dois bordos no mobile; (US5) Perfil —
fronteira editável vs. gerido por admin (cadeados; email admin-only, Q1). Componente novo
`components/RankBadge.js`. **CONCLUÍDA e RELEASED v0.5.37, em prod** (PR #354→develop;
correção W1 do widget; release #355→main; frontend Vercel + backend Via B `sha-482320bce1ca`
porque a release bundlou também #350/#351 de backend — ver [[prod-backend-deployed-state]]).
20/20 tarefas verificadas em navegador (360/500px). Sem deps novas.
Anterior: `specs/005-icone-marca-pwa-concluido/` — ícone quadrado da marca
gerível pela UI (Aparência → Marca), distinto do favicon (`icon_url` novo), que alimenta
a marca compacta in-app + o **ícone PWA** e a **imagem de partilha (og)** via um endpoint
estável `GET /api/brand/icon` (servir dinâmico, sem deploy; 302 → ícone atual ou
`{FRONTEND_URL}/logo512.png`). Backend tocado (`models.py` `icon_url` + `field_validator`;
`routes/brand.py` endpoint). CONCLUÍDA e **RELEASED v0.5.35**, deployed em prod **Via B**
(`sha-b16773a08b8a`, 2026-06-25 — `/api/brand/icon` -L → 200, `/api/brand/public` inclui
`icon_url`; ver [[prod-backend-deployed-state]]). 15/15 tarefas; T013 C1/C3 verificados,
C2/C4/C5/C6 (UI/PWA/iOS) residual de validação manual do dono (Princípio VII).
Anterior: `specs/004-plataforma-landing-concluido/` — landing page **pública de
produto** que apresenta o Portal ACCTA como sistema/plataforma de gestão de associações,
em tom factual e **sem CTA comercial forte** (decisão do dono). Frontend-only (novo
`pages/public/PlataformaPage.js` + rota lazy em `App.js` + link discreto no rodapé e item
na navegação pública em `layouts/PublicLayout.js`). CONCLUÍDA e **RELEASED v0.5.32**
(landing) **+ v0.5.33** (item "A Plataforma" na navegação pública), em prod
(`controlador.cv/plataforma` 200). Sem Via B (delta não tocou em `backend/`).
Anterior: `specs/003-eventos-multas-caixa-concluido/` — ronda 2 do fluxo
financeiro unificado: ligar EVENTOS (custos+receitas+resultado, Transaction.event_id,
gate Art. 54) e MULTAS de sanções (auto ao aplicar → receita com sancao_id) ao caixa
central. CONCLUÍDA e **RELEASED v0.5.27, em prod** (Transaction +event_id/+sancao_id;
eventos despesas/receitas/resultado + gate Art.54 + delete 409; multa idempotente ao
aplicar; Ato.event_id; UI EventFinanceDialog). Migração de multas = no-op (T030 dry-run
prod = 0); FR-016 estorno fora de âmbito; só T027/T034 opcionais por fazer.
Anterior: `specs/002-fluxo-financeiro-unificado-concluido/` (RELEASED v0.5.26, em prod).
<!-- SPECKIT END -->
