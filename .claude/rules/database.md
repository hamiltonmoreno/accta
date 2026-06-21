---
paths:
  - "backend/database.py"
  - "backend/models.py"
  - "scripts/**/*.py"
---

# Database Rules — ACCTA Portal (PostgreSQL / Supabase)

## Connection
- Async `asyncpg` pool via `database.py` (Supabase/PostgreSQL).
- Connection string from the `DATABASE_URL` env variable. In production use
  the Supabase connection pooler URI (port 6543, transaction mode); the pool
  is created with `statement_cache_size=0` for pgbouncer compatibility.
- `ensure_schema()` runs on app startup — creates all tables + indexes
  idempotently (no separate migration tool). Same operational contract the
  old `ensure_indexes()` had.

## Storage model — Mongo-compatible DAO
- Each logical collection is a table `(pk bigserial PRIMARY KEY, doc jsonb NOT NULL)`.
- `database.db` exposes a DAO that **faithfully emulates the Mongo API subset
  the codebase uses** (`find/find_one/insert_one/insert_many/update_one/
  update_many/delete_one/delete_many/count_documents/aggregate`, cursors with
  `.sort/.skip/.limit/.to_list`). Route/`auth`/`helpers` code calls it exactly
  as before — do NOT write raw SQL in routes.
- Supported query ops: `$in/$nin/$ne/$eq/$gt/$gte/$lt/$lte/$or/$and/$regex/$exists`.
  Update ops: `$set/$inc/$push/$pull/$addToSet/$unset`. Aggregation stages:
  `$match/$group($sum/$cond)/$count/$sort/$limit/$project`. If a new op is
  needed, extend the DAO in `database.py` — keep the Mongo-style call sites.

## Collections & Schema (64 tables = `len(database.COLLECTIONS)`)
- **users**: email (unique), role, status, invite_token, qr_code_hash,
  `account_type` (member|technical), `member_id` (immutable; via `member_id_seq`),
  `member_category` (fundador|ordinario|honorario), `orgao` (denormalized from
  cargo), `rights_suspended_until` (disciplinary), `privileges[]` (additive
  overlays), `cargo` (**canonical key from `governance.py`**, e.g.
  `dir_tesoureiro` — never a label) + `cargo_history[]` (mandate log; written
  only by `/admin/cargos` promote/demote/transfer and election proclamation —
  `transfer` is atomic via `database.transfer_cargo`)
- **transactions** (caixa central — **única fonte de verdade financeira**):
  type (receita/despesa), amount, date, category, user_id, `project_id`,
  `event_id` (**despesa/receita de evento = transação**), `ato_id`,
  `sancao_id` (**multa aplicada → receita** automática e idempotente ao
  aplicar a sanção). Não existem montantes financeiros fora desta coleção:
  `Event`/`Ato`/`Sancao` guardam só a *definição* do valor, copiada para a
  transação na execução; todos os totais e resultados derivam por agregação
  aqui (nunca leas finanças de `events`/`sancoes`/`atos`).
- **projects** (+ project_tasks, project_comments, project_expenses,
  project_milestones): title, status, team_members[]
- **events**: title, date, location, attendees[], visibility (resultado
  financeiro = receitas − despesas é **derivado** por agregação de
  `transactions` com este `event_id`; nunca guardado no doc do evento)
- **wall_posts** (+ wall_comments): content, user_id, approved, pinned, likes[]
- **notifications**: user_id, type, message, read, created_at
- **polls** (+ user_votes): title, options[], status
- **posts**, **documents** (+ document_accesses), **benefits**
  (+ benefit_validations, benefit_partners)
- **gallery_albums**, **gallery_photos**: album_id, url, status
- **audit_logs**: action, user_id, details, created_at
- **finance_settings**: quota_amount, quota_description, joia
  (`joia_multiplier`/`joia_amount`), `quota_fixed_by_assembleia/deliberacao`,
  `effective_from` (changing quota/jóia needs an AG 3/4 deliberation —
  spec-governanca §14)
- Governança estatutária (spec-governanca): **assembleias**,
  **assembleia_presencas**, **assembleia_deliberacoes**, **eleicoes**,
  **eleicao_listas**, **sancoes**, **finance_settings_history**. Secret vote
  (no Pydantic-on-doc link): **eleicao_voter_receipts** (HMAC receipt, unique
  `(eleicao_id, voter_hash)`) and **eleicao_ballots** (no `user_id`/`voter_hash`)
  — written together atomically via `database.cast_ballot`.
- Auth (no Pydantic model): **password_resets**, **tokens_revoked**,
  **login_attempts**

## Indexes (defined in database.py via ensure_schema)
- Expression indexes on `(doc->>'field')` mirroring the original Mongo indexes.
- Compound indexes for `(user_id, created_at)` patterns.
- Partial index for optional unique fields (e.g. invite_token).
- GIN indexes on array fields (`events.attendees`, `projects.team_members`).
- The formerly-TTL collections (`tokens_revoked`, `login_attempts`) are purged
  opportunistically on insert + a best-effort `pg_cron` job.

## Conventions
- Document IDs are the application-generated `id` UUID string
  (`str(uuid.uuid4())`). The Postgres surrogate `pk` is internal — never
  expose it; there is no Mongo `_id` (the old `{"_id": 0}` projection is a
  harmless no-op).
- Dates as ISO 8601 strings (`datetime.now(timezone.utc).isoformat()`).
- Embedded documents/arrays live inside the `doc` jsonb (sub-items, likes,
  attendees, options, locations).
- Never store passwords in plain text — always bcrypt hash.
- Soft delete where appropriate (status change, not actual deletion).

## Business Rules
- No "inadimplente" status — quotas are payroll-deducted
- User statuses: ativo, inativo, pendente_convite, pendente_aprovacao, rejeitado
- `account_type="technical"` accounts are hidden from member listings by default
  (`GET /users` filters member-or-missing; `?include_technical=true` to reveal)
- Gallery photos require admin approval before visibility
- Wall posts require moderation (status: pending → approved/rejected)
