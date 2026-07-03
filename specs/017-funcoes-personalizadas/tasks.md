# Tasks: Funções personalizadas com privilégios à medida

**Input**: Design documents from `/specs/017-funcoes-personalizadas/`

**Prerequisites**: plan.md, spec.md, research.md (D1–D6), data-model.md, contracts/custom-roles-api.md, quickstart.md

**Tests**: incluídos — a suíte pytest é a guarda de regressão do projeto (SC-002) e a constituição exige verificação antes de marcar tarefas.

**Organization**: por user story; cada fase é um incremento testável de forma independente.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [X] T001 Criar branch `feature/017-funcoes-personalizadas` a partir de `develop` atualizado (`git switch develop && git pull && git switch -c feature/017-funcoes-personalizadas`)

## Phase 2: Foundational (bloqueia todas as user stories)

- [X] T002 Acrescentar `"custom_roles"` a `COLLECTIONS` em `backend/database.py` (comentário PT: funções personalizadas — spec 017; `ensure_schema()` cria a tabela; sem índices dedicados)
- [X] T003 Modelos em `backend/models.py`: `CustomRoleCreate`/`CustomRoleUpdate`/`CustomRole` (validação: name 1–60 trim, description ≤200, privileges ≥1 ⊆ `PRIVILEGES` sem duplicados — reusar import de governance) + campo aditivo `custom_role_id: Optional[str] = None` em `UserBase`, `UserAdminUpdate` e `InviteCreate`

**Checkpoint**: `cd backend && ruff check . && pytest -m unit` verdes (nada de comportamento muda ainda).

---

## Phase 3: User Story 1 — Criar e gerir funções personalizadas (P1) 🎯 MVP

**Goal**: catálogo CRUD de funções personalizadas, admin-only, auditado; as 4 fixas intocáveis.

**Independent Test**: criar «Coordenador de Eventos» com 2 privilégios via API/UI, listar com rótulos PT e contagem, editar nome, recusar duplicado, eliminar quando sem utilizadores.

- [X] T004 [US1] Criar `backend/routes/custom_roles.py` (prefixo `/api/admin/custom-roles`, guard `current_user.role == "admin"` → 403): `GET /` (lista + `user_count` numa única passagem sobre `users` por `custom_role_id`), `POST /` (nome único trim+casefold, recusa colisão com labels/keys das 4 fixas → 400 «Já existe uma função com este nome»), `DELETE /{id}` (409 com contagem se em uso; 404 se inexistente), tudo com `create_audit_log` (`custom_role_created`/`custom_role_deleted`) — contrato em `contracts/custom-roles-api.md`; registar o router em `backend/server.py`
- [X] T005 [US1] `PATCH /{id}` em `backend/routes/custom_roles.py`: editar name/description/privileges (mesmas validações; audit `custom_role_updated` com before/after) — a propagação aos sócios fica para T012 (US3); por agora `propagated_to: 0`
- [X] T006 [P] [US1] Testes unit em `backend/tests/test_custom_roles.py`: criar/listar/editar/eliminar, 403 não-admin (socio/financeiro/moderador), 400 duplicado e colisão com fixas, 422 privileges vazio/desconhecido/duplicado, 409 delete em uso, 404, audit chamado — wire `mock_db.custom_roles` em-teste (NÃO está pré-wired no conftest; `find_one`/`find`/`update_many` como `AsyncMock`)
- [X] T007 [P] [US1] Grupo `customRolesAPI` em `frontend/src/utils/api.js` (list/create/update/remove → `/admin/custom-roles`)
- [X] T008 [US1] Criar `frontend/src/pages/private/usuarios/CustomRolesManager.js`: lista (nome, descrição, privilégios via `privilegeLabel()` de `lib/cargoLabels.js`, contagem de sócios), diálogo criar/editar (checkboxes dos 12 privilégios), eliminar com confirm dialog destrutivo (Carmesim outline→solid no diálogo) e erro 409 legível; TanStack Query + toasts; design `frontend-design` (botão positivo Floresta único)
- [X] T009 [US1] Entrada para o gestor em `frontend/src/pages/private/AdminUsuariosPage.js` (botão/secção «Funções personalizadas», visível só a admin)

**Checkpoint**: US1 completa e testável sozinha — catálogo funciona de ponta a ponta; sócios ainda não são afetados.

---

## Phase 4: User Story 2 — Aplicar uma função personalizada a um sócio (P1)

**Goal**: seletor «Função no Sistema» oferece as funções personalizadas na edição e no convite; atribuição materializa `role="socio"` + privilégios; escritas explícitas destacam.

**Independent Test**: aplicar a função a um sócio → sócio ganha exatamente os módulos da função; voltar a uma fixa → destaque; convite com função personalizada nasce correto.

- [X] T010 [US2] Atribuição/destaque em `backend/routes/users.py` (`admin_update_user`): payload com `custom_role_id` → valida existência (400), escreve `role="socio"` + `privileges=<da função>` + `custom_role_id` (precedência sobre role/privileges do mesmo payload); payload com `role`/`privileges` explícitos sem `custom_role_id` → limpa `custom_role_id` se existia (destaque); acrescentar `custom_role_id` ao set `sensitive` do audit before/after
- [X] T011 [US2] Convite e destaque por cargos em `backend/routes/admin.py` + `backend/routes/eleicoes.py`: `invite_user` aceita `custom_role_id` opcional (valida existência; convidado nasce socio+privilégios+ref; contrato 422/role=admin da spec 016 intocado); promote/demote/transfer de `/admin/cargos` e proclamação de eleições limpam `custom_role_id` ao escrever role/privileges (D5)
- [X] T012 [P] [US2] Testes em `backend/tests/test_custom_roles.py`: atribuição via PATCH /users (materialização + precedência), 400 função inexistente, destaque por role/privileges explícitos, destaque por predefinições de cargo/promote, convite com função personalizada, audit inclui `custom_role_id`
- [X] T013 [US2] Frontend `frontend/src/pages/private/usuarios/EditUserModal.js`: `<optgroup>` «Funções personalizadas» no seletor de Função (dados de `customRolesAPI.list`); com função personalizada selecionada, checkboxes de privilégios mostram os da função em read-only; botão «Aplicar predefinições do cargo» avisa antes de substituir função personalizada (FR-010); `frontend/src/pages/private/usuarios/InviteModal.js`: mesmo optgroup; `frontend/src/pages/private/AdminUsuariosPage.js`: incluir `custom_role_id` nos payloads de guardar/convidar

**Checkpoint**: US1+US2 = feature utilizável (definir 1×, aplicar a N sócios — SC-001).

---

## Phase 5: User Story 3 — Ciclo de vida com sócios afetados (P2)

**Goal**: ligação viva efetiva (edição propaga) e proteções visíveis (contagens, avisos, eliminação bloqueada já coberta em US1).

**Independent Test**: com a função em 2 sócios, editar privilégios → os 2 refletem sem edição individual e são notificados; UI mostra contagem e avisa quantos serão afetados.

- [X] T014 [US3] Propagação em `backend/routes/custom_roles.py` (`PATCH /{id}`): se `privileges` mudou, `update_many({"custom_role_id": id}, {"$set": {"privileges": novos}})` + `create_notification` («Perfil Atualizado», link `/perfil`) a cada afetado (ids da mesma query da contagem, sem N+1); resposta `propagated_to: <n>`; audit inclui `propagated_to`
- [X] T015 [P] [US3] Testes de propagação em `backend/tests/test_custom_roles.py`: edição propaga a todos os holders (update_many com filtro/valores certos), notificações emitidas, edição sem mudança de privileges NÃO propaga, `propagated_to` correto
- [X] T016 [US3] UI de impacto em `frontend/src/pages/private/usuarios/CustomRolesManager.js`: no diálogo de edição com `user_count > 0`, aviso «Esta alteração aplica-se a N sócio(s)» antes de guardar; mensagem 409 de eliminação mostra a contagem

**Checkpoint**: todas as user stories completas.

---

## Phase 6: Polish & verificação

- [X] T017 Verificação local completa: `cd backend && ruff check . && ruff format --check . && pytest -m unit` (suíte inteira, guarda SC-002) + `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60 && yarn build` (CI está billing-locked — isto É o gate)
- [ ] T018 Validação manual dos cenários do `quickstart.md` no navegador (cenários 1–6) e registo do resultado em `tasks/todo.md`; validação final do dono (Princípio VII) antes de fechar a spec

## Dependencies

- T001 → tudo; T002–T003 (Foundational) → todas as stories
- US1 (T004–T009): T004 → T005/T008; T006/T007 paralelos após T003–T005
- US2 (T010–T013): depende de T004 (coleção/validador); T012 paralelo a T013
- US3 (T014–T016): T014 depende de T005 e conceptualmente de T010 (holders); T015/T016 após T014
- Polish (T017–T018) no fim

## Parallel Examples

- Após T005: T006 (testes backend) ∥ T007 (api.js) ∥ início de T008 (UI)
- Após T011: T012 (testes) ∥ T013 (modais)
- Após T014: T015 (testes) ∥ T016 (UI)

## Implementation Strategy

**MVP = Phase 1–3 (US1)**: catálogo CRUD entregável e demonstrável sozinho. Depois US2 (valor visível — aplicar a sócios), depois US3 (ligação viva + impacto). Backend toca `backend/` ⇒ a release final precisa de deploy **Via B**. Sem migração: `ensure_schema()` cria a tabela no arranque; campos novos são aditivos.
