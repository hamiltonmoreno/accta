# Tarefa Ativa — Modelo de Identidade e Cargos

Branch: `feat/identidade-cargos`
Spec: `tasks/spec-identidade-cargos.md` (decisões já confirmadas na secção final).

> **Princípio**: uma pessoa = uma conta para a vida. `member_id` imutável.
> Cargos (`role` + `cargo`) atribuídos pelo admin via endpoints dedicados.
> Histórico de mandatos vive na conta pessoal (`cargo_history`).
> Contas técnicas (`account_type="technical"`) saem de listagens/pontuação/AGAs.

---

## Estado actual mapeado (Fase 0 ✅)

- `models.py`: `CARGOS` (7 entradas, l.9), `PRIVILEGES` (7, l.11-19), `UserBase`
  já tem `role`/`cargo`/`privileges`/`member_id`. `UserAdminUpdate` **permite**
  mudar `member_id` (l.65). `USER_STATUSES` (l.518). `Literal` já importado (l.2).
- `helpers.py`: `create_audit_log(user_id, action, target_id, *, request=, details=)`;
  `notify_users(user_ids, type, title, message, link=, exclude_id=)`;
  `notify_admins(type, title, message, link=, exclude_id=)`.
- `routes/users.py`: `GET /users` (RBAC `role in [admin,financeiro]`, filtro
  query+regex, projeção `{_id:0,password:0}`); `PATCH /users/{id}` (admin,
  valida cargo∈CARGOS, role, status; aplica `member_id`); `GET /users/meta/cargos`
  e `/meta/privileges` (sem auth). **`/users/cargos` (sem `meta/`) NÃO existe.**
- `routes/admin.py`: prefix `/admin`; padrão audit/notify confirmado; endpoints
  auto-registo já lá.
- `routes/finances.py`: helper `require_finance_role()` (l.35-37, `role in
  [admin,financeiro]`) em 10/12 endpoints; `/settings` PATCH é admin-only;
  `/meta/categories` sem check. **NÃO existe helper RBAC genérico** em `auth.py`.
- `database.py`: `next_member_id()` + `member_id_seq` já existem; `_update`
  usa `conn.transaction()` por chamada (sem helper multi-doc → criar
  `transfer_cargo()` dedicado). `$exists`/`$or` suportados pelo DAO.
- Frontend: `usersAPI.getCargos()/getPrivileges()` existem mas **não usados** —
  `AdminUsuariosPage.js` (l.27-45), `PerfilPage.js` (l.14-22), `CriarContaPage.js`
  (l.11-14) têm listas hard-coded. `FinanceiroPage.js` (l.22-24) gate
  `isAdmin||isFinanceiro`; `CashFlowTab` mostra botões de escrita sem guard.
  `AuthContext` expõe `isAdmin/isFinanceiro/isModerador` (l.82-84).

---

## Plano por fases (1 branch, 1 commit por fase)

### Fase 1 — Schema + models (foundation, baixo risco) ✅
- [x] `models.py`: `ACCOUNT_TYPES`; `UserBase.account_type: Literal[...]="member"`;
      `UserBase.cargo_history: List[dict]=[]`.
- [x] `models.py`: `CARGOS_ORGAOS_SOCIAIS` (dict) + `CARGOS` derivada (15) +
      `view_finances_readonly` em PRIVILEGES (8 total).
- [x] `models.py`: `ROLES_VALID`, `CARGO_DEFAULTS` (15), `CARGO_SEATS` (15).
- [x] `models.py`: `CargoMandate`, `PromoteUserRequest`, `DemoteUserRequest`,
      `TransferCargoRequest`.
- [x] `models.py`: `UserAdminUpdate` — `member_id` removido (handler usa
      `model_dump()` → não quebra; verificado).
- [x] `database.py`: `transfer_cargo(...)` atómico (reusa `_WhereBuilder`/
      `_mongo_update`, 1 transação).
- [x] Testes (`tests/test_identidade_cargos_models.py`, 23) + alinhado
      `test_member_profile_crud.py` (integração) aos novos cargos.
- [x] Verificação: ruff limpo; **78 passed** (users+auto-registo+models).

### Fase 2 — RBAC granular (ADITIVO — `role OR privilege`, sem regressão) ✅
- [x] `auth.py`: `has_privilege`, `has_role_or_privilege`, `can_view_finances`,
      `can_manage_finances`.
- [x] `finances.py`: `require_view_finances` (7 GET) / `require_manage_finances`
      (4 escrita); `/settings` PATCH mantém admin-only.
- [x] events (`manage_events`), documents (`manage_documents`), wall+gallery
      (`moderate_content`, [admin,moderador]), benefits (`manage_benefits`),
      audit-logs (`view_audit_logs`), users (`manage_users`) — todos aditivos.
- [x] Frontend: `AuthContext.canViewFinances/canManageFinances/hasPrivilege`;
      `FinanceiroPage` gate por view + badge "Modo leitura"; `CashFlowTab`
      esconde criar/editar/eliminar quando `!canManage`; `PrivateLayout` +
      `App.js ProtectedRoute` mostram/permitem Financeiro por privilégio.
- [x] Verificação: ruff limpo; **266 passed** (rbac_matrix/finances/events/
      benefits/wall/notifications/users/admin + novos rbac_privileges);
      eslint 0 erros (1 warning pré-existente).
- ℹ️ Fora de escopo (sem privilégio "falso"): upload.py (documents/logos
      ainda admin-only), polls (admin-only), projects (lógica própria).

### Fase 3 — Endpoints backend ✅
- [x] `admin.py`: `POST /admin/users/{id}/promote`, `/demote`,
      `POST /admin/cargos/transfer` (usa `transfer_cargo` atómico),
      `GET /admin/cargos`, `GET /admin/cargos/candidates`.
      RBAC `_require_manage_users` (admin **ou** manage_users); valida
      account_type=member, status=ativo, CARGO_SEATS; audit + notify.
- [x] `users.py`: `GET /users` filtra account_type member-or-missing via `$and`
      + `?include_technical=true`; metadata completa em `GET /users/meta/cargos`
      (reusa client `getCargos`, evita colisão com `/users/{id}`);
      `GET /users/{id}/cargo-history` (próprio ou admin, ordem desc).
- [x] Integração auto-registo: approve com cargo≠"Sócio" cria 1ª entrada em
      `cargo_history`.
- [x] Testes: `tests/test_cargos_routes.py` (29) — promote/demote/transfer/
      seats/RBAC/404 + metadata/account_type/cargo-history. ruff limpo.
      auto-registo+admin (28) inalterados.
- ℹ️ Desvio: endpoint de metadata é `/users/meta/cargos` (não `/users/cargos`
      do spec) — evita a colisão de rota com `/users/{user_id}`; já wired no client.

### Fase 4 — UI admin
- [ ] `/admin/cargos` — tabela cargos + ocupante/Vago + modais
      atribuir/transferir/terminar (autocomplete candidates, defaults de
      CARGO_DEFAULTS, primário Carmesim único). Rota + nav (admin).
- [ ] `/admin/usuarios`: `member_id` só-leitura (remover input); timeline
      "Histórico de Cargos" no detalhe/modal existente.
- [ ] `/perfil`: secção "Os meus cargos".
- [ ] Substituir constantes hard-coded por `GET /users/cargos` (Admin/Perfil).
- [ ] `api.js` `registrationAPI`/`usersAPI`/novo grupo cargos; `queryClient` keys.
- [ ] Verificação design system (neutral-led) + eslint + build.

### Fase 5 — Migração contas (⚠️ STOP CONDITION — destrutivo)
- [ ] `create_admin.py`: cria SÓ conta técnica `admin@controlador.cv`
      (`account_type="technical"`, `member_id=None`, todos privilégios,
      `cargo_history=[]`). **CÓDIGO seguro — não destrutivo.**
- [ ] Fixtures/`conftest.py`/`seed_data.py`: entender `account_type`.
- [ ] **NÃO EXECUTADO aqui**: `DELETE FROM users` / wipe da tabela é passo
      manual de deploy (sem acesso a VPS/DB) — documentado, requer confirmação
      explícita do utilizador.

### Fase 6 — Documentação
- [ ] `CLAUDE.md`: modelo de cargos/account_type.
- [ ] `.claude/rules/database.md`: `cargo_history`/`account_type`.
- [ ] `spec-auto-registo.md`: referência cruzada.

### Verificação final
- [ ] `ruff check` limpo; suite unit backend verde (novos testes incluídos).
- [ ] `eslint` 0 erros; testes frontend; `npx craco build` OK.

---

## Notas / decisões
- `account_type` retro-compatível: ausente = `member` (default Pydantic + filtro
  `$or [{account_type:member},{account_type:{$exists:false}}]`).
- RBAC granular **aditivo**: privilégio concede acesso EXTRA; quem já tinha por
  `role` continua igual → zero regressão.
- `transfer` atómico via `database.transfer_cargo()` (raw SQL no DAO, regra api.md).
- Phase 5 wipe destrutivo NÃO é executado — STOP condition do CLAUDE.md.
