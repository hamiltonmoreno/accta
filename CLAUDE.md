# Portal ACCTA - Project Brain

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

- A task requires **dropping or migrating data** in MongoDB (destructive schema change)
- A task requires **changing the JWT secret** or auth algorithm (all sessions invalidated)
- A task requires **modifying CORS origins** in production
- A task would **remove a route** that the frontend actively calls
- A task would **change a Pydantic model** in a way that breaks existing documents in DB
- **CI is failing** and the fix isn't obvious after one investigation pass
- **Two consecutive approaches have failed** — re-plan before attempting a third
- The scope of a "small fix" expands to touch **more than 3 files**
- Any action that **sends emails** to real users (invite, reset, welcome)
- Any action that **pushes to `main`** — always confirm first

---

## Stack

- **Frontend**: React 19 + Tailwind CSS 3 + shadcn/ui + Framer Motion + Recharts + Craco
- **Backend**: FastAPI (Python 3.11) + Motor (async MongoDB driver)
- **Database**: MongoDB — collections: `users`, `transactions`, `projects`, `events`, `wall_posts`, `notifications`, `polls`, `invoices`, `documents`, `gallery_albums`, `gallery_photos`, `audit_logs`, `password_resets`, `finance_settings`
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

- **Language**: Portuguese (PT) for all user-facing text; comments in PT or EN
- **Components**: Functional components + hooks only; shadcn/ui (New York style) for primitives
- **Styling**: Tailwind CSS only — no inline styles; brand tokens: Carmesim `#C7202F`, Grafite `#3A3A3A`
- **Backend**: Async/await everywhere; Pydantic models for all request/response validation
- **Auth**: Role-based access check on every protected endpoint; audit log on every admin action
- **No dark mode** — disabled by design decision, do not add
- **No inadimplente status** — quotas are payroll-deducted; statuses are only `ativo` / `inativo` / `pendente_convite`
- **Photo approval workflow** — all gallery photos require admin approval before visibility
- **Notifications** — SSE real-time stream; fallback to 30s polling

---

## Environment Variables

| Scope | Variable |
|-------|----------|
| Frontend | `REACT_APP_BACKEND_URL` |
| Backend | `SECRET_KEY`, `MONGO_URL`, `DB_NAME`, `CORS_ORIGINS`, `FRONTEND_URL`, `RESEND_API_KEY`, `SENDER_EMAIL` |

---

## Project Structure

```
/app
├── frontend/src/
│   ├── components/ui/    # shadcn/ui (40+ components)
│   ├── components/       # Custom: NotificationBell, PollResults, ACCTALogo…
│   ├── contexts/         # AuthContext, NotificationContext
│   ├── layouts/          # PrivateLayout (sidebar), PublicLayout (marketing)
│   ├── pages/public/     # 14 public pages (Home, Login, Transparencia…)
│   ├── pages/private/    # 16 private pages (Dashboard, Financeiro, Projetos…)
│   └── utils/api.js      # Axios client + all API groups (40+ endpoints)
├── backend/
│   ├── server.py         # FastAPI app entry + CORS + rate limiting
│   ├── database.py       # MongoDB connection + all index definitions
│   ├── auth.py           # JWT creation/validation + bcrypt
│   ├── models.py         # Pydantic models (request/response)
│   ├── helpers.py        # create_notification, create_audit_log, notify_*
│   ├── email_service.py  # Resend integration (invite, reset, welcome)
│   └── routes/           # 18 route modules (one per domain)
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
| financeiro | Finance module, transactions, invoices, settings |
| moderador | Content moderation — wall posts, gallery photos |
| socio | Member portal — dashboard, carteira, events, voting, mural |

---

## API Conventions

- All endpoints prefixed with `/api/`
- Auth: `Authorization: Bearer {token}` header
- File uploads: `multipart/form-data` to `/api/upload/{category}`
- Categories: `documents` (10MB), `proofs` (5MB), `logos` (2MB), `avatars` (2MB)
- Rate limits: login 10/min, forgot-password 3/min, default 200/min
