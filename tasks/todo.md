# Plano de Migração: MongoDB → Supabase (PostgreSQL)

_Avaliação + plano de execução. App ainda **não está em produção** → sem migração de dados, sem downtime, sem impacto a usuários. Este é o momento mais barato para migrar._

> **Escopo**: trocar apenas a camada de dados (MongoDB/Motor → PostgreSQL no Supabase).
> A arquitetura FastAPI, os modelos Pydantic, o contrato HTTP e o **auth JWT atual permanecem**.
> O frontend **não é tocado** (já é 100% desacoplado, só fala HTTP via `utils/api.js`).

---

## Decisões recomendadas (confirmar antes da Fase 1)

- [ ] **D1 — Driver**: SQLAlchemy 2.0 async + `asyncpg`, migrações com Alembic. Conexão via string do Supabase (pooler porta 6543, modo transação → `statement_cache_size=0` no asyncpg). _Alternativas: `supabase-py`/PostgREST (inadequado p/ filtros e agregações complexas) ou asyncpg puro (mais código)._
- [ ] **D2 — Camada de acesso (a "costura")**: introduzir um **DAO assíncrono genérico** com API espelhando a do Motor (`find_one`, `find`, `insert_one`, `update_one`, `delete_one`, `count`, + métodos dedicados p/ as 7 agregações e toggles de array). Motivo: os ~296 pontos de acesso são quase todos filtros de igualdade simples → port quase mecânico, e a suíte de testes inteira passa a depender de **1 fixture** em vez de 36 arquivos.
- [ ] **D3 — Arrays**: `text[]` nativo para `privileges`, `likes`, `attendees`, `team_members`, `tags` (`$push`→`array_append`+dedupe, `$pull`→`array_remove`); `jsonb` para `polls.options` e `benefits.locations`. Sem tabelas de junção (evita reescrita desnecessária; normalizar depois se preciso).
- [ ] **D4 — Datas**: colunas `timestamptz`; o DAO converte datetime↔ISO 8601 na fronteira para preservar o comportamento atual das rotas (`models.md`: datas são strings ISO).
- [ ] **D5 — TTL** (`tokens_revoked`, `login_attempts`): jobs `pg_cron` no Supabase (1 linha SQL cada). Fallback: delete oportunista — as queries de lockout/blocklist já filtram por janela de tempo, então a correção não depende do purge.
- [ ] **D6 — Auth**: **manter JWT custom** (HS256 + cookie httpOnly + bcrypt + blocklist + lockout). NÃO adotar Supabase Auth nem RLS agora (backend é a camada confiável; conexão de serviço). Decisão separada para o futuro.
- [ ] **D7 — Chave primária**: `id uuid PRIMARY KEY` (o código já usa `id` UUID string e descarta `_id` do Mongo — mapeia 1:1).

---

## Inventário (verificado no código)

**Acoplamento**: 21 arquivos fazem `from database import db` (1 só costura). 19 routers sob `prefix="/api"`.

**27 coleções → 27 tabelas** (21 com modelo Pydantic + 6 sem). **Com modelo Pydantic (21):** users, invoices, polls, user_votes, posts, documents, benefits, wall_posts, wall_comments, events, transactions, finance_settings, projects, project_tasks, project_comments, project_expenses, project_milestones, gallery_albums, gallery_photos, notifications, audit_logs.
**Sem modelo Pydantic — também viram tabela (6):** password_resets, tokens_revoked, login_attempts, document_accesses, benefit_validations, benefit_partners. _(auth/lockout dependem destas — não podem ficar de fora.)_

**Arrays embutidos** → `text[]`: `users.privileges`, `wall_posts.likes`, `events.attendees`, `projects.team_members`, `*.tags`. → `jsonb`: `polls.options`, `benefits.locations`.

**7 agregações** (todas simples → SQL trivial):
1. `gallery.py` contagem de fotos aprovadas por álbum → `GROUP BY album_id`
2. `gallery.py` (2ª forma, get_gallery_albums) → idem
3. `projects.py` resumo de tarefas (total + concluídas) → `GROUP BY project_id` + `FILTER (WHERE status='concluido')`
4. `projects.py` total de despesas do projeto → `SUM(amount)`
5. `stats.py` receita de invoices pagas → `SUM(amount) WHERE status='pago'`
6. `report.py` documentos únicos acessados por user → `COUNT(DISTINCT document_id)`
7. `activity.py` feed → já é `find().sort().limit()`, vira `ORDER BY ... LIMIT`

**Mutações de array / contadores**: `wall_posts.likes` push/pull (toggle like); `events.attendees` push/pull; `wall_posts.comment_count` / `benefits.validation_count` `$inc`; vários `$set`. Sem transações multi-documento.

**Índices TTL**: `tokens_revoked.expires_at` (0s), `login_attempts.attempted_at` (24h) → `pg_cron`. **Multikey**: `events.attendees`, `projects.team_members` → índice GIN no `text[]`.

**Testes**: ~36 arquivos + `conftest.py`. `mock_db` imita a API do Motor e faz monkeypatch de `database.db`/`auth.db`/`helpers.db`/`routes.*`. Fixture `client` (session) sobe app + DB real (smoke). _Nota: conftest mocka coleção `failed_logins` mas o código usa `login_attempts` — inconsistência pré-existente do mock._

**CI**: `.github/workflows/ci.yml` sobe serviço `mongo:7`, `MONGO_URL`, com job unit (mockado) + integração. `deploy.yml` também referencia Mongo.

**Scripts** (Motor direto): `seed_data.py` (limpa+popula ~9 coleções), `create_admin.py`, `seed_gallery.py`. + `_bootstrap_admin_if_requested()` em `server.py`.

**Docs com refs a Mongo**: README.md, DEPLOY.md, HOSTINGER_DEPLOY.md, PROJETO_ACCTA.md, ANALISE_MELHORIAS.md, CLAUDE.md, `.claude/rules/database.md`, `.claude/agents/*`.

---

## Fases de execução

### Fase 0 — Decisões & spike (~0.5 dia)
- [ ] Confirmar D1–D7 com o usuário
- [ ] Criar projeto Supabase (ou reutilizar org existente) + pegar connection string (pooler) e guardar como `DATABASE_URL`
- [ ] Spike: provar conexão asyncpg+pooler a partir do ambiente de deploy (Render/etc.)

### Fase 1 — Schema + migrações (~0.5–1 dia)
- [ ] Adicionar `sqlalchemy[asyncio]`, `asyncpg`, `alembic` ao `requirements.txt`; remover `motor`/`pymongo` só na Fase 7
- [ ] Definir **27 tabelas** — 21 a partir de `models.py` + 6 sem modelo (password_resets, tokens_revoked, login_attempts, document_accesses, benefit_validations, benefit_partners) — PK `id uuid`, `text[]`/`jsonb` conforme D3, timestamps `timestamptz`
- [ ] Traduzir índices de `database.py` para SQL (compostos, parciais, GIN p/ arrays, unique em `users.email`, sparse→partial em `invite_token`)
- [ ] Alembic baseline migration; aplicar no Supabase
- [ ] Jobs `pg_cron` p/ `tokens_revoked` e `login_attempts`

### Fase 2 — Camada de acesso (a costura) (~1 dia)
- [ ] Implementar DAO assíncrono (engine/sessionmaker, lifespan startup/shutdown substituindo `client`)
- [ ] `ensure_indexes()` → `run_migrations()`/no-op (Alembic gere o schema)
- [ ] `/health` → `SELECT 1` no Postgres (substituir `client.admin.command("ping")`)
- [ ] Manter a forma `from database import db` apontando para o DAO (minimiza diff nas rotas)

### Fase 3 — Portar módulos (ordem de dependência) (~3–5 dias)
- [ ] `auth.py` (users, tokens_revoked) + `helpers.py` (audit, notifications, lockout)
- [ ] auth_routes, users, admin (password_resets, login_attempts)
- [ ] notifications, posts, documents, contact, upload, stats simples
- [ ] wall (+ wall_comments, likes `text[]`), events (attendees `text[]`)
- [ ] benefits (locations jsonb, validation_count), invoices, polls (options jsonb, user_votes)
- [ ] gallery (álbuns/fotos + agregações), documents/document_accesses
- [ ] projects (5 tabelas filhas, team_members, agregações)
- [ ] finances (transactions, finance_settings, geração de quotas)
- [ ] report, activity (agregações/feed)

### Fase 4 — Agregações & ops de array (~0.5–1 dia)
- [ ] Implementar as 7 agregações como métodos dedicados do DAO (SQL acima)
- [ ] `toggle like` / `attendees` via `array_append`/`array_remove` (+ unicidade)
- [ ] `$inc` (`comment_count`, `validation_count`) → `SET col = col + :delta`

### Fase 5 — Scripts & bootstrap (~0.5 dia)
- [ ] Portar `create_admin.py`, `seed_data.py`, `seed_gallery.py` para o DAO/SQL
- [ ] Portar `_bootstrap_admin_if_requested()` em `server.py`

### Fase 6 — Testes & CI (long pole, ~2–3 dias)
- [ ] Reescrever fixture `mock_db` → `mock_dao` (1 lugar; mapeia 1:1 onde nomes espelham Motor)
- [ ] Ajustar testes que assertam encadeamentos específicos de cursor Mongo
- [ ] CI: trocar serviço `mongo:7` → `postgres:16`; rodar Alembic; lane de integração contra **branch efêmera do Supabase** (ou Postgres do CI)
- [ ] Manter lane unit mockada; suíte inteira verde

### Fase 7 — Limpeza & docs (~0.5 dia)
- [ ] Remover `motor`/`pymongo` do `requirements.txt`
- [ ] `.env.example`: `MONGO_URL`/`DB_NAME` → `DATABASE_URL`
- [ ] Atualizar README, DEPLOY, HOSTINGER_DEPLOY, PROJETO_ACCTA, CLAUDE.md, `.claude/rules/database.md`, `deploy.yml`

### Fase 8 — Verificação & cutover (~0.5 dia)
- [ ] `pytest` 100% verde local + CI
- [ ] Smoke manual dos fluxos críticos (login, mural, finanças, projetos, galeria, notificações SSE)
- [ ] Diff de comportamento vs `main` nos endpoints sensíveis
- [ ] Configurar `DATABASE_URL` no ambiente de deploy; remover infra Mongo

---

## Estimativa & riscos

**Esforço total**: ~9–13 dias de trabalho focado. Long pole = testes/CI (Fase 6), não as rotas.

**Riscos**:
1. **Volume mecânico** (~296 pontos) → bug latente. Mitigação: DAO espelhando Motor + suíte de testes como rede de segurança + port por módulo.
2. **Testes acoplados ao Motor** → a escolha do DAO (D2) é o que reduz isso de 36 arquivos para ~1 fixture. Se D2 mudar, custo da Fase 6 sobe muito.
3. **pgBouncer + asyncpg** (prepared statements) → `statement_cache_size=0`; validar no spike (Fase 0).
4. **Sem migração de dados** = risco quase nulo aqui (pré-produção). Maior vantagem do timing.

**Sem impacto**: frontend, contrato HTTP, auth JWT, fluxos de e-mail.

---

## Review
_(preenchido ao concluir cada fase)_
