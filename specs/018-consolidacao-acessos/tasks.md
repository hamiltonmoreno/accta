# Tasks: Consolidação do modelo de acessos e identidade do utilizador

**Input**: Design documents from `/specs/018-consolidacao-acessos/`

**Prerequisites**: plan.md, spec.md (D1–D7 decididas), research.md (R1–R10), data-model.md, contracts/api-changes.md, quickstart.md

**Tests**: incluídos — a matriz de equivalência (`test_access_matrix.py`) É o instrumento central da spec (baseline F1, prova de SC-001 na F2), não um extra.

**Organization**: por user story, mas a ordem de execução segue a decisão **D6**: a US4 (F1 — higiene) executa PRIMEIRO como gate de todas as outras, apesar de ser P3 na spec. US1/US2/US3 formam a F2.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [ ] T001 Confirmar branch `feature/018-consolidacao-acessos` atualizada sobre `develop` (já criada; `git fetch && git rebase origin/develop` se develop tiver avançado)

## Phase 2: User Story 4 — Unificação interna dos checks (P3, mas **F1 = gate de tudo**, D6) 🎯

**Goal**: helper único + tabela canónica módulo→privilégio + matriz de equivalência como baseline; **zero mudança de comportamento** — releasable sozinha.

**Independent Test**: a matriz escrita ANTES das mudanças corre INALTERADA depois delas; suíte inteira verde; grep não encontra checks de acesso fora do helper.

- [ ] T002 [US4] Escrever `backend/tests/test_access_matrix.py` **ANTES de tocar em qualquer check** (R10): perfis (admin, financeiro, moderador, socio puro, socio+priv relevante por módulo, view_finances_readonly, técnico) × módulos (finances view/manage, users, events, documents, benefits, moderação gallery/wall, comunicados, audit em notifications.py, ranking, regulamentos) → allow/deny; mock_db; verde no código ATUAL (é a baseline/contrato de equivalência)
- [ ] T003 [US4] Tabela canónica `MODULE_ACCESS` em `backend/governance.py` (módulo → {privilege, legacy_roles}; docstring PT; ver data-model.md) — documental na F1, alimenta a matriz e a F2
- [ ] T004 [US4] Unificar helpers: `backend/auth.py` (`can_view_finances`/`can_manage_finances` reescritos sobre `MODULE_ACCESS`; `has_role_or_privilege` mantém-se o ponto único) + `backend/permissions.py` (`user_can` vira alias fino de `has_role_or_privilege` ou é absorvido — decidir no diff, ranking/regulamentos ajustados)
- [ ] T005 [US4] Eliminar checks inline (lote 1): `backend/routes/{projects,participacao,prestacao_contas,eleicoes,atos}.py` → `has_role_or_privilege`/helpers de domínio (R1; sem mudar resultados — cuidado com gates por CARGO em atos/eleições, que ficam em `permissions.py` e NÃO entram na tabela)
- [ ] T006 [US4] Eliminar checks inline (lote 2): `backend/routes/{users,regulamentos,posts,events,upload,sancoes,report}.py` + `backend/routes/documents.py:19` (check à mão → helper)
- [ ] T007 [US4] **Gate F1**: `pytest tests/test_access_matrix.py` verde SEM edições à matriz + `cd backend && ruff check . && pytest -m unit` (suíte inteira) + **teste automatizado de scan** em `test_access_matrix.py` (`test_no_inline_role_checks`: varre `routes/*.py` por `role == "`/`role in (` fora dos helpers = 0) — cumpre o «guardadas por teste» de FR-008 (finding M2) e impede regressões futuras; registar resultado em `tasks/todo.md`. F1 pode ir em release própria (invisível) se o dono quiser reduzir risco

**Checkpoint**: F1 completa — baseline capturada, comportamento provadamente intacto. NADA da F2 começa antes deste checkpoint.

---

## Phase 3: User Story 1 — Um só modelo mental para conceder acessos (P1)

**Goal**: enum {admin, socio}, defaults de cargo reescritos, tradução de roles legados (1 release), alerta de escalada redefinido, frontend a decidir por privilégios.

**Independent Test**: dar acesso de finanças só é possível via privilégio/função; seletor mostra 2 níveis + funções; PATCH/invite com role legado traduz e audita.

- [ ] T008 [US1] `backend/governance.py`: defaults de cargo (R7/D3) — dir_secretario/dir_tesoureiro/dir_vogal → `role="socio"` (privilégios inalterados); presidente/vice mantêm admin; **sinalizar no PR a lista do Secretário para validação do dono (D3)**
- [ ] T009 [US1] Enum + tradução (R6/D4): `backend/routes/admin.py` (invite) e `backend/routes/users.py` (PATCH) — validação `role ∈ {admin, socio}` + `_LEGACY_ROLE_MAP` {financeiro, moderador} → socio + função seed + privilégios, audit `legacy_role_translated: true`, mensagens PT (contracts/api-changes.md); partilhar a lógica num helper único (1 sítio) que obtém a seed por nome e, **se ainda não existir (janela deploy→migração), a cria on-demand** com os privilégios da matriz — elimina a dependência de ordem com T014 (finding M1 do analyze)
- [ ] T010 [US1] `backend/helpers.py`: alerta de escalada R8 (`_ELEVATED_ROLES` → admin OU novos privilégios de `_SENSITIVE_PRIVILEGES` {manage_users, manage_finances, view_audit_logs}, incl. via função) + `backend/routes/custom_roles.py`: retirar financeiro/moderador de `_RESERVED_NAMES` (R5)
- [ ] T011 [P] [US1] Testes em `backend/tests/`: tradução legado→seed (PATCH e invite, audit incluído), 400/422 p/ roles desconhecidos, defaults de cargo novos (promote a tesoureiro → socio+privilégios), alerta R8 (dispara/não dispara), nomes das seeds criáveis; **atualizar `test_access_matrix.py` deliberadamente** — o diff da matriz é a lista exata de mudanças (rever com o dono) — e remover `legacy_roles` de `MODULE_ACCESS` (limpeza F2, finding I2)
- [ ] T012 [US1] Frontend decide por privilégios: `frontend/src/contexts/AuthContext.js` (`canManageFinances` etc. só por privilégio; `isFinanceiro`/`isModerador` derivados de privilégios p/ compat), `frontend/src/lib/nav/visibility.js`, `frontend/src/App.js` (3 rotas `allowedRoles` financeiro/moderador → `allowedPrivileges`; suporte já existe), `frontend/src/pages/private/usuarios/tokens.js` (`ROLES=['admin','socio']`), `frontend/src/lib/cargoLabels.js`
- [ ] T013 [US1] **Emenda constitucional v1.1.0** (R9): `.specify/memory/constitution.md` (linha «Roles {admin, financeiro, moderador, socio}» + Sync Impact Report) + reconciliar `CLAUDE.md` (§Auth) e `.claude/rules/` que mencionem o enum — mesma release (Governance da constituição). **Gate duro da F2**: a release não sai sem a emenda merged; a constituição pede PR próprio p/ emendas — confirmar com o dono se vai em PR separado ou no PR da feature com justificação (finding P1)

**Checkpoint**: modelo novo completo em código; utilizadores legados ainda existem na BD (migram na US2).

---

## Phase 4: User Story 2 — Migração sem perda nem ganho de acesso (P1)

**Goal**: migrar os utilizadores existentes com equivalência exata, auditado e reversível.

**Independent Test**: quickstart cenários 1–2 — dry-run + apply em BD local semeada; ex-financeiro opera finanças exatamente como antes; 0 docs com role legado.

- [ ] T014 [US2] `scripts/migrate_roles_018.py`: modos `--dry-run` (default) / `--apply`; cria funções seed «Financeiro»/«Moderador» (privilégios derivados da MATRIZ F1 — R4; inserção direta na coleção, fora da API); migra cada user role legado pela regra R3 (privileges ⊆ seed → socio+`custom_role_id`; extras → socio+privilégios diretos em união, SEM função); backup JSON pré-migração; **modo `--restore <backup.json>`** que repõe o estado before de cada utilizador (caminho de rollback exercitável — finding M3); audit `role_model_migrated` por utilizador com before/after; idempotente (re-run = no-op)
- [ ] T015 [P] [US2] Testes da migração em `backend/tests/test_migrate_roles_018.py`: regra R3 nos dois ramos, união sem duplicados, idempotência, dry-run não escreve, **`--restore` reverte ao estado pré-migração** (M3), seeds com os privilégios da matriz, convite `pendente_convite` com role legado também migra (edge case da spec)
- [ ] T016 [US2] Validação local (quickstart cenários 1–2): no ambiente isolado (`accta-pg-dev`), semear 1 financeiro + 1 moderador + 1 financeiro c/ `manage_events` extra → dry-run → apply → verificar os 3 resultados + audit + login do ex-financeiro a operar finanças; registar em `tasks/todo.md`

**Checkpoint**: US1+US2 = modelo novo utilizável de ponta a ponta em ambiente local. A EXECUÇÃO em prod fica para a cerimónia de release (STOP do dono).

---

## Phase 5: User Story 3 — UI que separa «Acesso» de «Identidade» (P2)

**Goal**: seletor «Nível de acesso» (D2) e modal em 2 secções com proveniência (US3/D5).

**Independent Test**: quickstart cenários 3–4 — um admin não-técnico identifica a origem de cada privilégio e o que cada campo controla.

- [ ] T017 [US3] `frontend/src/pages/private/usuarios/EditUserModal.js` + `InviteModal.js`: rótulo «Nível de acesso» (D2) com Administrador/Sócio + grupo «Funções personalizadas»; modal reorganizado em «Acesso ao sistema» (nível, função, privilégios com origem: «da função X» / «manuais») e «Identidade associativa» (cargo, categoria, departamento + nota «organizacional — não altera acessos», D5); `FiltersBar.js` filtro por nível novo (valores antigos `role=financeiro/moderador` vindos de estado/URL degradam para «todos» sem erro — finding A1); design `frontend-design`
- [ ] T018 [P] [US3] Texto e páginas restantes: `frontend/src/content/ajuda/*.js` (perfis descritos pelo modelo novo), `frontend/src/layouts/PrivateLayout.js` e páginas pontuais com referências a roles antigos (`MuralPage`, `NotificacoesPage`, `AdminPedidosInscricaoPage`, `AdminCargosPage` — inventário R1)

**Checkpoint**: todas as user stories completas em código.

---

## Phase 6: Polish & verificação

- [ ] T019 Verificação local completa: `cd backend && ruff check . && ruff format --check <ficheiros tocados> && pytest -m unit` + `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60 && yarn build` (CI billing-locked — isto É o gate); rever o diff da matriz F1→F2 com o dono
- [ ] T020 Validação manual dos cenários 3–8 do `quickstart.md` no navegador (ambiente isolado) e registo em `tasks/todo.md`; validação final do dono (Princípio VII). **A release develop→main, o deploy Via B e a migração em prod (backup → dry-run → confirmação do dono → apply → teste decisivo) são cerimónia à parte com STOPs explícitos — fora destas tasks**

## Dependencies

- T001 → tudo
- **US4/F1 (T002–T007) é gate de TODA a F2 (D6)**; dentro dela: T002 antes de T003–T006 (baseline primeiro); T007 fecha
- US1 (T008–T013): após T007; T008→T009 (tradução usa defaults); T011 ∥ T012 após T009/T010; T013 em qualquer ponto da fase
- US2 (T014–T016): após US1 (seeds dependem da matriz final + reserved names R5); T015 ∥ após T014
- US3 (T017–T018): após T012 (AuthContext novo); T018 ∥ T017
- Polish (T019–T020) no fim

## Parallel Examples

- Após T009/T010: T011 (testes backend) ∥ T012 (frontend core) ∥ T013 (constituição)
- Após T014: T015 (testes migração) ∥ T016 (validação local)
- Após T012: T017 ∥ T018

## Implementation Strategy

**F1 primeiro e isolada** (T002–T007): entregável e mergeable sozinha, sem mudança visível — candidata a release própria para encurtar o delta da F2. Depois US1 (modelo) → US2 (migração local) → US3 (UI) → Polish. A migração REAL em prod só na cerimónia de release com confirmação do dono em cada STOP (migração de dados, semântica de modelo, main). Sem schema novo; `custom_roles` já existe (spec 017). A release da 017 continua suspensa (D7) — sai junto com a 018.
