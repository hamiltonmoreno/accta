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

### Fase 2 — RBAC granular (ADITIVO — `role OR privilege`, sem regressão)
- [ ] `auth.py`: helpers `can_view_finances(user)`, `can_manage_finances(user)`,
      `has_privilege(user, priv)` (role existente **OU** privilégio).
- [ ] `finances.py`: GET → `can_view_finances`; POST/PATCH/DELETE/quotas →
      `can_manage_finances`; `/settings` PATCH mantém admin-only.
- [ ] events/documents/content(wall)/benefits/audit: aceitar privilégio relevante
      **além** do role já permitido (aditivo). Módulos fora de escopo ficam
      explícitos aqui e não recebem privilégio "falso".
- [ ] Frontend Finanças: modo só-leitura quando `view` sem `manage` (esconde
      botões criar/editar/eliminar; menu visível para quem pode ver).
- [ ] Testes: view-only não escreve; manage escreve; admin/financeiro inalterados.

### Fase 3 — Endpoints backend
- [ ] `admin.py`: `POST /admin/users/{id}/promote`, `/demote`,
      `POST /admin/cargos/transfer` (usa `transfer_cargo` atómico),
      `GET /admin/cargos`, `GET /admin/cargos/candidates`.
      RBAC: `role=admin` **ou** `manage_users`. Audit + notify em cada acção.
      Valida `account_type=member`, `status=ativo`, `CARGO_SEATS`.
- [ ] `users.py`: `GET /users` filtra `account_type` member-or-missing +
      `?include_technical=true`; `GET /users/cargos` (metadata completa:
      CARGOS, CARGOS_ORGAOS_SOCIAIS, PRIVILEGES, CARGO_DEFAULTS, CARGO_SEATS);
      `GET /users/{id}/cargo-history` (próprio ou admin).
- [ ] Integração auto-registo: ao aprovar com cargo≠"Sócio", criar 1ª entrada
      em `cargo_history` (toca `admin.py` approve).
- [ ] Testes unitários (`mock_db`): promote/demote/transfer/seats/RBAC/404.

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
