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

## Progresso F2

### US1 — modelo (T008–T013) COMPLETA
- [x] T008 defaults de cargo D3 (só presidente/vice mantêm admin)
- [x] T009 enum {admin,socio} + tradução D4 em **4 superfícies** (invite,
  PATCH /users, approve de registo, promote/transfer — o research R6
  subcontava 2); `resolve_legacy_role` com seed on-demand (M1); audit
  `legacy_role_translated`
- [x] T010 alerta R8 (`_SENSITIVE_PRIVILEGES`) + reserved names R5
- [x] T011 matriz atualizada DELIBERADAMENTE (perfis seed_*; legados negam
  tudo; equivalência: Moderador exata, Financeiro ⊇ com delta
  +users_manage/+photo assinalado) + `test_role_transition_018.py` (20) +
  8 testes existentes atualizados; **suíte 1552+15 passed, ruff limpo**
- [x] T012 frontend por privilégios (AuthContext flags de compat, 3 rotas,
  nav, tokens ROLES=2, Mural, FiltersBar degradação A1); eslint 0 erros,
  jest 8/8, build OK
- [x] T013 emenda constitucional **v1.1.0** + CLAUDE.md + rules/api.md
  reconciliados (commit isolado p/ cherry-pick se o dono quiser PR próprio)

### US2 — migração (T014–T016) COMPLETA
- [x] T014 `scripts/migrate_roles_018.py` (dry-run/apply/--restore, backup,
  audit, R3, idempotente) · T015 15 testes verdes
- [x] T016 **validação local (quickstart 1–2) no `accta-pg-dev`**: 3+1 users
  legados → dry-run correto → apply (seeds criadas, 4 migrados, backup, 4
  audits `role_model_migrated`) → re-run = 0 (idempotente) → **restore live
  repõe os 4 → re-apply** → teste decisivo via API: ex-financeiro login →
  finanças 200 + listagem users 200 + audit-logs 403; ex-moderador → wall
  pending 200 + finanças 403; convite com `role=financeiro` → doc socio +
  privilégios da seed + `custom_role_id` ✓

### US3 — UI (T017–T018) COMPLETA
- [x] T017 «Nível de acesso» (D2) + modal em 2 secções com proveniência dos
  privilégios (função «X» / manuais) + nota D5 no departamento (Edit+Invite)
- [x] T018 ajuda (gates Aparência/Finanças + texto) e páginas restantes

### Polish
- [x] T019 gate final: ruff limpo + `pytest -m unit` **1567 passed** +
  eslint 0 erros + jest (AuthContext 8/8, ajuda/visibility 29/29) + build OK

### Revisão adversarial pré-release (2026-07-05) — findings + fixes
Revisão de 5 dimensões sobre `develop...HEAD`. Gate reverificado: **`pytest -m
unit` 1572 passed**, ruff+eslint limpos.
- [x] **W3 (CRÍTICO) — escalada via promote/transfer/demote FECHADA**: o fix W1
  só cobria `admin_update_user`; `promote_user`/`demote_user`/
  `transfer_cargo_endpoint` gravavam `role`/`privileges` do corpo guardados só
  por `_require_manage_users` → um `manage_users` não-admin promovia-se a admin
  (D3 contornada). Fix: helper `_require_cargo_admin` (admin-only) nas 3
  mutações; leituras ficam em `_require_manage_users`; proclamação de eleições
  (escreve direto) intacta. +3 testes de regressão em `test_cargos_routes.py`.
  Ver [[L16]].
- [x] **MÉDIO — `scripts/seed_data.py`**: `financeiro@controlador.cv` era
  `role="financeiro"` sem privilégios (não-funcional pós-018 + role legado
  persistido) → `role="socio"` + `[manage_finances, manage_users]`.
- [x] **Colisão de nome `resolve_legacy_role` — RESOLVIDA**: reservei de novo
  «financeiro»/«moderador» em `_RESERVED_NAMES` (`routes/custom_roles.py`) — são
  a identidade que a tradução D4 resolve por nome; reservar impede uma homónima
  que a tradução captaria (corrige a janela pré-seed da R5). Seeds criadas direto
  (bypassam a reserva). +3 casos no parametrize `test_collision_with_fixed_400`;
  R5 (research.md) sincronizada. Escolhi reservar (não `seed_key`) porque a
  unicidade de nome já garante 1 só «Financeiro» — `seed_key` sozinho não fecha
  a colisão do índice único de nome.
- [ ] **Dono — janela deploy→migração**: user `role=financeiro`/`priv=[]` perde
  acesso até a migração correr (prod=no-op, 0 legados). Correr `--apply` na
  mesma janela do deploy, antes de servir tráfego.
- [x] **Tripwire regex — ENDURECIDO**: `_INLINE_ROLE_CHECK` passou de casar só
  `user.role <op>` para casar QUALQUER `*user.role` (o refactor F1 deixou 0
  acessos nos routes) → apanha comparação direta + ordem-Yoda + fonte do
  aliasing, sem operador. +`test_tripwire_catches_evasions` (guarda contra
  enfraquecer o regex). Resíduo (AST): aliasing do objeto / `getattr`.

## Por fazer (dono)
- [x] T020 validação manual dos cenários 3–8 do quickstart no navegador
  (ambiente isolado) + rever o **diff da matriz F1→F2** — em particular o
  delta da seed «Financeiro» (+users_manage/+users_photo_moderation, não há
  privilégio só-de-listagem) e a lista do Secretário (D3)
- [x] Decisão P1: emenda constitucional — **RESOLVIDA no PR da feature** (não em
  PR próprio). Já em `develop` E `main` a v1.1.0 (commit `aea6932`, spec 018 T013:
  role enum {admin, socio}). Nada a criar.
- [ ] Push + PR para develop; release/migração prod = cerimónia à parte
  (backup → dry-run → confirmação → apply → teste decisivo) com STOPs

## Pendente de outras specs
- [x] Spec 017 T018 — validação manual do dono (quickstart 1–6) no ambiente
  local isolado (Docker `accta-pg-dev` :5433; admin@dev.cv / socio1-2@dev.cv);
  release v0.5.54 suspensa (D7)

---

## Validação 017/018 — 2026-07-05 (ambiente dev isolado :5433 / :8001 / :3000)

**Stack**: `accta-pg-dev` (Postgres :5433) + backend `--env-file .env.dev` :8001
+ frontend craco :3000. Contas `admin@dev.cv` / `socio1-2@dev.cv` / `puro` etc.

### Backend (API determinística) — 16/16 asserções PASS
Spec 017 (T018) — cenários 1,2,3,4,6:
- S1 criar «Coordenador de Eventos» → 200 + `user_count=0`; duplicado → 400
  «Já existe uma função com este nome».
- S2 aplicar via `custom_role_id` → user vira `socio` + privilégios materializados
  da função.
- S3 **ligação viva**: editar a função (remover `manage_documents`) → holder
  atualizado (`propagated_to=1`) + notificação «Perfil Atualizado».
- S4 delete-in-use → **409**; após retirar a função (escrita explícita limpa
  `custom_role_id`) → delete 200.
- S6 auditoria `custom_role_created/updated/deleted`.

Spec 018 (T020) — cenários 5,7,8:
- S5 **tradução D4**: `PATCH /users/{id}` `role=financeiro` → `socio` + seed
  «Financeiro» + audit `legacy_role_translated=financeiro`; `role` desconhecido
  → **400** («Opções: admin, socio, financeiro, moderador»).
- S7 **alerta de escalada R8**: com um 2.º admin, conceder `manage_finances` →
  +1 «Escalada de privilégio» ao 2.º admin; retirar → 0 (de-escalada não alerta).
  (O 1.º teste deu 0 porque o único admin é o ator, corretamente excluído.)
- S8 auditoria contém `user_updated` (traduções/edições) + `role_model_migrated`.

### Frontend (smoke visual no navegador) — evidência capturada
- 017-S1: modal «Funções Personalizadas» lista Financeiro (2 sócios) / Moderador
  (1 sócio) com rótulos PT + nota da ligação viva.
- 017-S2 + 018-S3/S4 (modal de edição, fin.puro): secção **«Acesso ao sistema»**
  com seletor **«Nível de acesso» = Financeiro**, **proveniência** «Origem: função
  Financeiro — editam-se na função e propagam…», checkboxes **read-only** com os
  privilégios da função; secção separada **«Identidade associativa»** (cargo «gerido
  em Cargos & Mandatos», departamento «etiqueta organizacional — não altera acessos»).
- 018-S3/4/6 (seletor, proveniência, design/PT) já confirmados 15:36.

### Estado da BD dev após validação
Limpo/baseline: `custom_roles = [Financeiro, Moderador]` (seeds), sem leftover
«Coordenador de Eventos», socios de teste repostos (privilégios vazios).

### Migração prod (P1) — dry-run reconfirmado
`python scripts/migrate_roles_018.py` → **0 utilizadores com role legado** →
`--apply` é no-op para `users`. STOP: **DECISÃO DO DONO (2026-07-05, durável) = SKIP `--apply`** — o dry-run já
prova o enum {admin,socio} seguro (0 legados); as funções seed nascem on-demand
quando forem atribuídas. Nenhuma escrita em prod. P1 fechado.
