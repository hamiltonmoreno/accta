# Task — Spec 017: Funções personalizadas com privilégios à medida

## Contexto
O admin cria funções nomeadas (pacotes de privilégios do catálogo canónico,
ex.: «Coordenador de Eventos») e aplica-as a sócios no seletor «Função no
Sistema» (edição + convite). Decisões do dono: Q1 = ligação viva (editar a
função propaga a todos os sócios que a têm); Q2 = base sempre «Sócio» +
privilégios (nunca concede nível Financeiro/Moderador/Admin).
Plano: `specs/017-funcoes-personalizadas/plan.md`; tarefas: `tasks.md` (18).

## Progresso (17/18)

### Backend — completo, 29/29 testes verdes
- [x] T002 `database.py` — coleção `custom_roles`
- [x] T003 `models.py` — `CustomRoleCreate/Update/CustomRole` + `custom_role_id` aditivo em `UserBase`/`UserAdminUpdate`/`InviteCreate`
- [x] T004/T005 `routes/custom_roles.py` — CRUD `/api/admin/custom-roles` (admin-only, auditado, nomes reservados, 409 em uso, `user_count` sem N+1)
- [x] T010 `routes/users.py` — atribuição com precedência (materializa socio+privilégios) e destaque por escrita explícita; `custom_role_id` no audit sensitive
- [x] T011 `routes/admin.py` + `routes/eleicoes.py` — convite com função; promote/demote/transfer/proclamação limpam `custom_role_id` (D5)
- [x] T014 propagação viva no PATCH (update_many + notificações, `propagated_to`)
- [x] T006/T012/T015 `tests/test_custom_roles.py` — 29 testes (CRUD, RBAC 403, validações 422, 409, propagação, atribuição, convite, promote)

### Frontend — completo, eslint 0 erros, build OK
- [x] T007 `utils/api.js` `customRolesAPI` + queryKey `customRoles.list`
- [x] T008/T016 `usuarios/CustomRolesManager.js` — lista+form num Dialog, rótulos via `privilegeLabel()`, aviso de impacto «aplica-se a N sócio(s)», delete destrutivo com 409 legível
- [x] T009 `AdminUsuariosPage.js` — botão «Funções Personalizadas» (secundário neutro) + query partilhada + `custom_role_id` no payload de guardar
- [x] T013 `EditUserModal.js` (optgroup, privilégios read-only com nota, confirm no botão de predefinições — FR-010) + `InviteModal.js` (optgroup) + `tokens.js` (EMPTY_INVITE)

### Verificação (T017) — feita
- backend: `ruff check` limpo; `ruff format --check` limpo nos ficheiros da spec
  (deriva pré-existente noutros 80 ficheiros = versão do ruff, fora de âmbito);
  `pytest -m unit` **1403 passed** (suíte inteira, SC-002 guardada)
- frontend: `eslint --max-warnings=60` → 0 erros / 22 warnings; `yarn build` OK
- de caminho: `eslint.config.js` +1 global `Notification` (corrige 3 erros
  pré-existentes da spec 009 em push.js/PushPrefs.js)

## Por fazer
- [ ] T018 — Validação manual dos cenários 1–6 do `quickstart.md` no navegador
  + validação final do dono (Princípio VII) antes de fechar a spec.

## Notas de release
- Toca `backend/` ⇒ release precisa de **Via B**. Sem migração:
  `ensure_schema()` cria a tabela no arranque; campos novos são aditivos.
