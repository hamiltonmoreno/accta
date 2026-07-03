# Task — Spec 018: Consolidação do modelo de acessos (F1 — higiene invisível)

## Contexto
Decisões D1–D7 do dono (2026-07-03). D6: duas fases — **F1 = higiene sem
mudança de comportamento** (gate da F2); F2 = enum {admin,socio} + migração +
UI. Plano: `specs/018-consolidacao-acessos/plan.md`; tarefas: `tasks.md` (20).

## Progresso F1 (T001–T007) — COMPLETA

- [x] T001 branch `feature/018-consolidacao-acessos` em dia com develop (0 atrás)
- [x] T002 `tests/test_access_matrix.py` — matriz baseline escrita ANTES de
  tocar em qualquer check e committada isolada: **100 células perfil×módulo
  verdes no código pré-F1** + medição do acesso real dos roles legados
  (financeiro = {finances_view, finances_manage, users_list}; moderador =
  {moderation_gallery, moderation_wall, users_photo_moderation}) — input R4
  das seeds F2
- [x] T003 `governance.py` `MODULE_ACCESS` — tabela canónica módulo→
  {privilege, legacy_roles} (14 módulos; gates por cargo ficam em permissions)
- [x] T004 helpers unificados: `auth.py` ganha `is_admin`/`has_any_role`/
  `module_gate` (duck-typed dict|User via `_uattr`); `can_view_finances`/
  `can_manage_finances` reescritos sobre MODULE_ACCESS; `permissions.user_can`
  vira alias fino de `has_role_or_privilege`
- [x] T005/T006 sweep: TODAS as comparações `user.role`/`current_user.role`
  eliminadas de `routes/*.py` (25 ficheiros — os 13 do plano + activity,
  stats, gallery, finances, polls, banners, brand, custom_roles, comunicados,
  notifications, admin, profissional, participacao); `documents.py`/`report.py`
  → `has_role_or_privilege`; `events.py` MEMBER_EVENT_ROLES → `has_any_role`;
  gallery: var local `is_admin` renomeada `uploaded_by_admin` (colisão com o
  helper)
- [x] T007 **Gate F1 verde**:
  - matriz corre **INALTERADA** pós-refactor: 100/100 (prova de equivalência,
    SC-005)
  - `test_no_inline_role_checks` (tripwire FR-008): scan de `routes/*.py` = 0
    ocorrências
  - `pytest -m unit` → **1503 passed** (1403 pré-existentes + 98 matriz + scan)
  - `ruff check .` limpo; `ruff format --check` limpo no ficheiro novo (deriva
    pré-existente nos 10 ficheiros de rotas já falhava em develop — fora de
    âmbito)

## Por fazer (F2 — só após decisão de release da F1)
- [ ] T008–T013 US1 modelo (enum, defaults cargo, tradução, emenda
  constitucional v1.1.0 = gate duro)
- [ ] T014–T016 US2 migração local; T017–T018 US3 UI; T019–T020 polish
- F1 é releasable sozinha (invisível) — decisão do dono se sai em release
  própria para encurtar o delta da F2

## Pendente de outras specs
- [ ] Spec 017 T018 — validação manual do dono (quickstart 1–6) no ambiente
  local isolado (Docker `accta-pg-dev` :5433; admin@dev.cv / socio1-2@dev.cv);
  release v0.5.54 suspensa (D7)
