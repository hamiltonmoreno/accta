<!--
SYNC IMPACT REPORT
==================
Version change: (none) → 1.0.0 (initial ratification)
Modified principles: N/A (first ratification)
Added sections:
  - Core Principles (I–VII)
  - Stack & Data Constraints
  - Development Workflow & Stop Conditions
  - Governance
Removed sections: N/A
Templates requiring updates:
  ✅ .specify/templates/plan-template.md — Constitution Check gate is placeholder, populated
     dynamically during /speckit-plan; no static edit required
  ✅ .specify/templates/spec-template.md — no constitution-coupled sections
  ✅ .specify/templates/tasks-template.md — no constitution-coupled categorization
  ⚠ CLAUDE.md — runtime guidance file already encodes these principles in operational form;
     no edit required, but the constitution now formally supersedes it on conflicts (see Governance)
Deferred TODOs: none
-->

# Portal ACCTA Constitution

## Core Principles

### I. Simplicity First

Every change MUST be as simple as possible and impact the minimum amount of code that
solves the stated problem. Do not add features beyond what the task requires. Do not
introduce abstractions ahead of need; three similar lines is preferable to a premature
abstraction. Do not add error handling, fallbacks, or validation for scenarios that
cannot happen — trust internal code and framework guarantees, and validate only at
system boundaries (user input, external APIs). Do not use feature flags or
backwards-compatibility shims when the code can simply be changed.

**Rationale**: complexity compounds; every shim and abstraction becomes load-bearing
the moment it is read by the next developer. Restraint is cheaper than removal.

### II. Root-Cause Discipline (NON-NEGOTIABLE)

Bugs MUST be fixed at their root cause. Temporary fixes, band-aids, and "make it work
for now" patches are forbidden. When two consecutive approaches have failed, work MUST
stop and the plan MUST be revisited before a third attempt. Tests that are skipped or
silenced to ship MUST be replaced by a tracked follow-up (issue or `tasks/todo.md`
entry) with an explicit removal condition.

**Rationale**: temporary fixes accrue interest. Stopping after two failed approaches
prevents the "third time lucky" trap that consumes hours and produces fragile code.

### III. RBAC + Audit on Every Protected Surface (NON-NEGOTIABLE)

Every protected endpoint MUST enforce a role-based access check at entry. Every admin
write MUST emit an audit log entry via `helpers.create_audit_log(...)`. Password
fields MUST never appear in API responses (use projections like
`{"_id": 0, "password": 0}`). Routes MUST NOT contain raw SQL — all data access goes
through the Mongo-compatible DAO in `backend/database.py`; schema and indexes live
only in `ensure_schema()`. Eligibility and role helpers MUST come from
`backend/permissions.py`; órgãos/cargos/categorias/privileges MUST come from
`backend/governance.py` (the single source of truth — never hand-edit a mandate or
hard-code a cargo label).

**Rationale**: the application is the trust boundary; consistent guards at entry +
auditability of writes is the minimum a member-owned organisation can accept.

### IV. Language Discipline: PT for Users, EN for Generics, Domain in PT

User-facing text — UI strings, HTTPException `detail`, notification titles/bodies,
emails, comunicados — MUST be in European Portuguese. Identifiers (functions,
variables, jsonb fields) MUST use generic/technical EN names (`create_transaction`,
`status`, `amount`); domain terms with no clean English equivalent MUST stay PT
(`joia`, `quota`, `socio`, `exercicio`, `balancete`, `assembleia`, `deliberacao`,
`sancao`, `aprovar`/`submeter`/`reabrir`). Comments and docstrings MUST be in PT
(matching the existing majority). When editing a file, the file's existing language
MUST be preserved — do not switch to follow the chat language. Bulk-renaming existing
identifiers is forbidden because they are tied to jsonb keys, indexes, the API, and
the frontend.

**Rationale**: the audience is sócios in Cabo Verde; the codebase has converged on
this split and any drift creates translation burden and PR noise.

### V. Design System Authority (NON-NEGOTIABLE)

The `frontend-design` skill (`.claude/skills/frontend-design/SKILL.md`) is the single
source of truth for the visual system. UI MUST be neutral-led: white / `#F5F5F5`
surfaces, Grafite `#3A3A3A` text. Action color is semantic — the single primary
**positive** button per view is Floresta `#166534` (hover `#14532D`); Carmesim
`#C7202F` is brand identity + **destructive** (outline by default, solid only inside
an irreversible confirm dialog). Carmesim MUST NEVER be used as a positive primary.
Red text on dark/coloured backgrounds is forbidden. There is NO dark mode (disabled
by design decision — do not add). Tailwind only — no inline styles, no hardcoded
tokens copied from other files; consult the skill.

**Rationale**: a single restrained accent reads as institutional; visual sprawl reads
as amateur. The neutral-led / Floresta-positive / Carmesim-destructive system was
ratified and reconciled across all mirrors; this constitution now locks it.

### VI. GitFlow + Confirmation Before Production

All work targets `develop` first. `main` is reached only via a `release/*` or
`hotfix/*` PR — direct pushes to `main` are forbidden. Commits MUST follow
Conventional Commits with a scope (`feat(escopo): …`, `fix(escopo): …`,
`docs(escopo): …`). The following actions REQUIRE explicit user confirmation before
proceeding (STOP conditions):

1. Dropping or migrating data in PostgreSQL/Supabase (destructive schema change)
2. Changing the JWT secret or auth algorithm (invalidates all sessions)
3. Modifying CORS origins in production
4. Removing a route the frontend actively calls
5. Changing a Pydantic model in a way that breaks existing documents in DB
6. Sending emails to real users (invite / reset / welcome / comunicados broadcast)
7. Pushing or merging to `main` (release ceremony or hotfix)
8. Expanding the scope of a "small fix" beyond 3 files
9. Re-attempting after two consecutive approaches have failed (re-plan first)

**Rationale**: the cost of an irreversible mistake at this scale (≤ a few hundred
sócios) is small in dollars but high in trust. A 10-second confirmation pays for
itself the first time it prevents a wrong deploy.

### VII. Verification Before Done (NON-NEGOTIABLE)

A task is not done until its behaviour is proven. Type-checks and test suites verify
code correctness, not feature correctness. For UI/frontend changes the feature MUST
be exercised in a browser before being reported as complete; if that is not possible,
say so explicitly rather than claiming success. For backend changes the relevant
tests MUST pass; for prod-touching changes the deployed surface MUST be probed
server-side after the Via B deploy (e.g., `curl /api/health` + log inspection +
the release's "teste decisivo" in `docs/runbook-deploy-backend-via-b.md`). Any
user correction MUST be captured in `tasks/lessons.md` (and the relevant memory
file if it is a long-lived insight) before the next attempt.

**Rationale**: "it compiled" is not "it works"; the gap is where regressions live.
Verification habits + lessons capture is how the team gets faster without getting
sloppier.

## Stack & Data Constraints

- **Backend**: FastAPI (Python 3.11) + asyncpg, with a Mongo-compatible async DAO
  over PostgreSQL (`backend/database.py`). Each logical "collection" is a Postgres
  table `(pk bigserial, doc jsonb)`. Document IDs are application-generated
  `str(uuid.uuid4())`; there is no real Mongo `_id`. Dates MUST be stored as
  ISO 8601 strings (`datetime.now(timezone.utc).isoformat()`), never `datetime`
  objects in models.
- **Frontend**: React 19 + Tailwind CSS 3 + shadcn/ui (New York style) + Framer
  Motion + Recharts + Craco. Functional components + hooks only. No CSS modules,
  no inline styles, no styled-components.
- **Auth**: JWT HS256, 24h expiry. Roles {`admin`, `financeiro`, `moderador`,
  `socio`}. Additive `privileges[]` overlays (e.g., `view_finances_readonly` for
  Conselho Fiscal). MFA/2FA is removed and MUST NOT be reimplemented.
- **Email**: Resend API. Sending to real users is a STOP condition (Principle VI).
- **Deploy**: GitFlow → tag → Via B manual fallback (`docs/runbook-deploy-backend-via-b.md`)
  while GitHub Actions billing-locked. Frontend ships independently via Vercel on
  push to `main`.
- **Pinned dependencies**: `bcrypt` MUST stay at `4.0.1` (newer versions break
  `passlib`'s backend probe and every password-hash test fails). If a venv is
  rebuilt, this pin MUST be installed explicitly.
- **Database posture**: app talks to Postgres as the `postgres` role (owner /
  `BYPASSRLS`); RLS is ON with zero policies on every table in `public` as
  defence-in-depth against the Supabase Data API. The runtime role MUST keep
  `BYPASSRLS` — changing this breaks the app silently (`supabase-data-api-rls-posture`).

## Development Workflow & Stop Conditions

- **Plan first**: any non-trivial task (≥3 steps or architectural decision) starts
  in plan mode. Detailed specs reduce ambiguity and prevent re-work.
- **Subagents liberally**: research, exploration, and parallel analysis go to
  subagents to keep the main context window clean. One task per subagent.
- **Track progress**: active task plans live in `tasks/todo.md`; accumulated
  lessons from corrections live in `tasks/lessons.md`; spec-kit artifacts live in
  `.specify/memory/` and `specs/[###-feature]/`.
- **Status statuses (user)**: only `ativo` / `inativo` / `pendente_convite` /
  `pendente_aprovacao` / `rejeitado`. There is NO `inadimplente` (quotas are
  payroll-deducted).
- **Identity**: one person = one account for life. `member_id` is immutable and
  MUST NOT be editable via the API. `account_type="technical"` accounts are
  excluded from member listings/scoring/AGAs by default.
- **Approval workflows**: all gallery photos require admin approval before
  visibility; wall posts go through moderation (pending → approved/rejected).
- **CI handling**: while billing-locked, CI jobs fail with `steps: []` (never
  start). This is environmental — verify by reproducing locally before treating
  it as a code failure (`ci-billing-lock-not-code`).

## Governance

This constitution supersedes all other practices on conflict. Where `CLAUDE.md`
and this constitution overlap, `CLAUDE.md` is the *runtime guidance* file (loaded
into every agent session) and this constitution is the *policy layer*; the
runtime file MUST conform — if drift is detected, the runtime file is the one
that updates.

**Authoritative source-of-truth hierarchy** (highest to lowest, on conflict):

1. This constitution (`.specify/memory/constitution.md`)
2. `frontend-design` skill (`.claude/skills/frontend-design/SKILL.md`) — visual system
3. `.claude/rules/{api,database,models,frontend}.md` — auto-loaded backend invariants
4. `backend/governance.py` — órgãos sociais, cargos, categorias, privileges
5. `CLAUDE.md` — project brain / runtime guidance
6. Domain memories (`prod-backend-deployed-state`, `accta-prod-topology`,
   `governanca-estatutaria-state`, etc.)

**Amendment procedure**:

- Amendments are proposed via a PR titled `docs(constitution): amend to vX.Y.Z`
  that updates `.specify/memory/constitution.md` and includes a Sync Impact Report
  (HTML comment at top) listing version delta, modified principles, added/removed
  sections, and templates requiring updates.
- Version bumps follow semantic versioning:
  - **MAJOR**: backward-incompatible governance change or principle removal/redefinition
  - **MINOR**: new principle or section, or materially expanded guidance
  - **PATCH**: clarifications, wording, typo fixes, non-semantic refinements
- The PR MUST be reviewed before merge to `develop`. Merge to `main` follows the
  normal release ceremony (Principle VI).
- After merge, any divergence introduced in `CLAUDE.md`, `.claude/rules/`, the
  `frontend-design` skill, or `.specify/templates/` MUST be reconciled in the same
  release.

**Compliance review**:

- Every PR review MUST verify the changeset against the principles. Violations
  MUST be either fixed or explicitly justified in the PR description (Complexity
  Tracking section in the plan template captures principle deviations).
- The `/speckit-analyze` skill SHOULD be run before `/speckit-implement` on any
  non-trivial feature to check cross-artifact consistency against this
  constitution.

**Version**: 1.0.0 | **Ratified**: 2026-06-20 | **Last Amended**: 2026-06-20
