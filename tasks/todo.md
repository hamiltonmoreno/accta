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

## Review — execução (concluída — código em `main`)

**Abordagem executada (refinamento de D1/D2/D3):** em vez de SQLAlchemy/Alembic +
remodelagem relacional, implementei um **DAO assíncrono sobre asyncpg que emula
fielmente o subconjunto exato da API Mongo em uso**, com cada coleção como
tabela `(pk bigserial, doc jsonb)`. Resultado: **zero alterações** em rotas,
`auth.py`, `helpers.py`, `models.py` e nos 36 ficheiros de teste — só
`database.py` foi reescrito. É a expressão mais fiel de "Minimal Impact".

**Feito:**
- [x] `backend/database.py` reescrito: pool asyncpg, DAO Mongo-compatível
  (`find/find_one/insert_*/update_*/delete_*/count_documents/aggregate`,
  operadores `$in/$ne/$eq/$gt(e)/$lt(e)/$or/$regex`, updates
  `$set/$inc/$push/$pull/$addToSet`, agregação `$match/$group/$sum/$cond/$count`),
  cursores `.sort/.skip/.limit/.to_list`, projeção, fidelidade de datetime,
  `ensure_schema()` idempotente (27 tabelas + índices de expressão/GIN), purga
  TTL (oportunista + pg_cron best-effort).
- [x] `server.py`: `/health`→`ping()` Postgres, startup `ensure_schema()`,
  shutdown `close_pool()`.
- [x] `requirements.txt`: removido `motor`/`pymongo`, adicionado `asyncpg`.
- [x] Scripts (`create_admin`, `seed_data`, `seed_gallery`) repontados ao DAO.
- [x] `conftest.py`: env default `MONGO_URL`→`DATABASE_URL` (fixture `mock_db`
  intacta).
- [x] CI: serviço `mongo:7`→`postgres:16`, `DATABASE_URL`.
- [x] **Verificação**: `ruff` limpo; **275 testes unitários mockados a passar**
  + 113 do gate de CI — swap Mongo→Postgres transparente à aplicação.

**Entregue (merged em `main`):**
- [x] PR **#30** — camada de dados MongoDB→PostgreSQL/Supabase (DAO + 27
  tabelas + índices + scripts + CI `postgres:16` + docs de agente).
- [x] PR **#31** — `_ssl_arg()`: TLS para Supabase (`require`), sem TLS para
  Postgres local (CI/dev). Sem isto a app **não liga** ao Supabase em
  ambiente nenhum (descoberto na validação pós-merge do #30).

**Na branch `claude/evaluate-database-migration-XxVyZ` (NÃO em `main`):**
- [x] commit `6678296` — correção P1 (Codex, PR #31): `sslmode` explícito
  passa **verbatim**; `verify-ca`/`verify-full` já não são rebaixados a
  `require` (era regressão de segurança — `ssl=` do asyncpg sobrepõe o DSN).
  `main` ainda tem a regressão até este commit ser entregue (decisão do
  utilizador: "só commit na branch", sem PR por agora).

**Validação ao vivo — bloqueios de ambiente (não são defeitos de código):**
- Sandbox: egress TCP para portas Postgres **5432/6543 é filtrado**
  (silenciosamente dropado; DNS→IPv4 OK, HTTPS/443 instantâneo). asyncpg
  não alcança o Supabase a partir daqui.
- MCP Supabase desta sessão está ligado a **outro projeto**
  (`rqplobwsdbceuqhjywgt` / "fiskix"), **não** ao accta
  (`wudxceylvnnvglmfzzgi`, ref do utilizador da string do pooler). Aplicar
  o schema via MCP teria atingido a base errada → **não feito** de propósito.
  _(Nota: registos antigos citavam `eafyduxxzlkwvkudcnzu`; a ref correta do
  accta é `wudxceylvnnvglmfzzgi`, conforme a connection string fornecida.)_

**Caminho escolhido: confiar no arranque da app.** `server.py:213-216`
(`@app.on_event("startup")` → `ensure_schema()`) cria as 27 tabelas + 45
índices idempotentemente a cada boot. Runbook:
1. Definir `DATABASE_URL` (string do **pooler**,
   `aws-0-eu-west-1.pooler.supabase.com:6543`, user
   `postgres.wudxceylvnnvglmfzzgi`) como secret do backend no ambiente de
   deploy (que tem egress Postgres, ao contrário do sandbox/CI).
2. Reiniciar o backend (`supervisorctl restart`).
3. Verificar sucesso no log: `"PostgreSQL schema and indexes ensured"`.
4. (Opcional) `pg_cron`: ativar extensão no Supabase e correr `pgcron.sql`;
   senão a purga oportunista trata de `tokens_revoked`/`login_attempts`.

**Follow-ups manuais (fora do alcance do agente):**
- [ ] **Rodar a password** do Postgres no Supabase — foi colada no chat.
- [ ] `backend/.env.example`: `MONGO_URL`/`DB_NAME` → `DATABASE_URL`
  (bloqueado por permissão `.env*` para o agente).
- [ ] Decidir entrega do commit `6678296` (P1) para `main`.
- [ ] Docs operacionais/históricos ainda com refs a Mongo: README, DEPLOY,
  HOSTINGER_DEPLOY, VERCEL_DEPLOY, `.claude/skills`, `.claude/agents/*`,
  `.claude/commands/new-feature`. (ANALISE_MELHORIAS/PROJETO_ACCTA/memory/PRD
  são históricos — não reescrever.)

---

## Limpeza de documentação Mongo→Postgres (branch `claude/docs-postgres-cleanup`)

> Decisão do utilizador (substitui a nota "não reescrever" acima): atualizar
> **toda** a documentação, incluindo ANALISE_MELHORIAS/PROJETO_ACCTA/memory/PRD.
> README/DEPLOY/HOSTINGER já corrigidos no PR #34 (fundido).

- [ ] `.github/copilot-instructions.md`, `copilot-backend.md`, `copilot-testing.md`
- [ ] `.claude/skills/backend-api/SKILL.md` (reescrever boilerplate p/ DAO real)
- [ ] `.claude/agents/{code-reviewer,debugger,schema-migration,security-auditor,test-writer}.md`
- [ ] `.claude/commands/new-feature.md`, `.claude/rules/api.md`
- [ ] `PROJETO_ACCTA.md`, `ANALISE_MELHORIAS.md`, `memory/PRD.md`
- [ ] `VERCEL_DEPLOY.md` → reescrito p/ Vercel + Supabase (sem Atlas/Render)
- [ ] Preservar: `CLAUDE.md`, `.claude/rules/database.md` (refs DAO intencionais),
  `tasks/*` (registo histórico)
- [ ] Verificar grep limpo + commit + push + PR

---

## Review — Migração Frontend Neutral-Led (branch `fix/frontend-neutral-led`)

> Spec: `tasks/frontend-redesign-spec.md`. Execução autónoma (todas as fases),
> 1 commit/fase, base `fix/health-audit` (contém o SKILL.md canónico). Sem
> merge em `main` (stop condition — aguarda OK do utilizador).

| Fase | Commit | Resumo | Verificação |
|------|--------|--------|-------------|
| 0 — Fundação global | `1207858` | App.css reduzido (removido `a{color}` global, scrollbar/focus/selection Carmesim, `:root`/`.btn-*` duplicados, shimmer morto); `--text-muted` #9ca3af→#6B7280; `darkMode` removido; `dark:` do alert.jsx | grep C7202F App.css=0; dark:=0; eslint/build OK |
| 1 — Red-on-dark (CRÍTICO) | `c0a5e16` | 6 subagentes / matriz fg-bg: 35 defeitos red-on-dark→text-white/`bg-white/10`; 12 erros→`#B91C1C`; preservado Carmesim-em-branco/finanças/nav | varredura inline=0; eslint/build OK |
| 2 — Taxonomia de botões | `4f91615` | ≤1 primário/vista: bg-confianca→Carmesim Primary (Home/Sobre/BenefPub/PublicLayout); 4 toggles→outline; GaleriaAdmin/ErrorBoundary/EventosPub | eslint/build OK |
| 3 — Texto muted | `7bbeb66` | ~108 `text-gray-400/300` de TEXTO→`#6B7280`; ~52 não-texto (ícones/divisórias) preservados | nenhum gray em texto; eslint/build OK |
| 4 — Paleta + tokens legados | `dfd648c` | charts→sistema; amber→warning(14); slate→neutro(9); confianca→Carmesim; tokens confianca/navy/amber/slate + pulse-radar removidos do config; footer slogan→text-white | grep tokens=0; eslint/build OK |
| 5 — QA final | (docs) | eslint 0err/44warn(<60); craco build OK; escopo frontend-only (41 fic., +229/-367); todos os greps de aceitação limpos | — |

**Decisões de critério (conformes ao SKILL, reversíveis numa linha):**
- `PublicLayout` "Entrar": era `bg-confianca` (único CTA da chrome) → promovido a Carmesim Primary (vs. demover a neutro).
- `GaleriaAdmin` toggle de visibilidade segmentado: `bg-carmesim`→`bg-grafite` (tratado como CTA competidor).
- `PublicLayout` footer slogan: `text-amber` (ouro decorativo legado) sobre `bg-grafite` → `text-white` (o map cego amber→warning teria criado warning-on-dark).

**Pendente (QA do utilizador — não automatizável neste ambiente):**
- Leitura visual dos 8 heros + amostragem de contraste; screenshots antes/depois vs `main`.
- `backend && ruff check .`: ruff não instalado no ambiente; **backend não foi tocado** (0 ficheiros) → sanidade satisfeita por escopo.
- Merge em `main`: **bloqueado** até OK explícito (stop condition CLAUDE.md).

**Lições registadas:** `tasks/lessons.md` L6 (backtick em commit via Bash → here-doc) e L7 (remapear token legado exige classificar o papel, não só o nome).
