---
description: "Task list for Comunicados Segmentados (v2) implementation"
---

# Tasks: Comunicados Segmentados (v2)

**Input**: Design documents from `specs/001-comunicados-segmentados/`

**Prerequisites**: plan.md, spec.md, research.md (D1–D3 confirmados), data-model.md, contracts/, quickstart.md

**Tests**: INCLUÍDOS (backend pytest) — a spec é orientada a acceptance scenarios,
o quickstart nomeia os ficheiros de teste e a constituição (Princípio VII) exige
verificação. Frontend validado em browser (o projecto não tem suite JS).

**Decisões do dono (2026-06-20)**: D1 = `+ comunicar_intra_orgao` (US4 entra);
D2 = incluir ciclo de rascunho; D3 = `enviado_parcial` ≡ `parcial` (aditivo).

**Web app** — caminhos: backend em `backend/`, frontend em `frontend/src/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode correr em paralelo (ficheiros diferentes, sem dependências)
- **[Story]**: US1–US4 (mapeia para as user stories da spec)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: baseline verde e ambiente antes de tocar no módulo

- [X] T001 Estabelecer baseline: correr `cd backend && pytest tests/test_comunicados_routes.py tests/test_comunicados_service.py tests/test_email_comunicado.py -q` e confirmar verde (legado intacto antes de estender)
- [X] T002 Confirmar `bcrypt==4.0.1` no venv e `ENVIRONMENT` não-`production` no `.env` de dev (pré-requisito de testes de password + dry-run; ver CLAUDE.md / quickstart)

**Checkpoint**: módulo legado verde, ambiente pronto

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: o motor de resolução de audiência + modelos + status, partilhados por TODAS as user stories. Funções puras, sem superfície HTTP — totalmente testáveis em unidade.

**⚠️ CRITICAL**: nenhuma user story pode começar antes desta fase

- [X] T003 [P] Adicionar modelo `AudienceFilter` (cargos/orgaos/categorias/statuses/joined_after/joined_before/nominal_member_ids/nominal_emails) + `model_validator` (≥1 critério; enums fechadas validadas: `cargos`⊆`governance.CARGO_KEYS`, **`orgaos`⊆{`direcao`,`mesa_ag`,`conselho_fiscal`}** — exactamente as keys aceites por `helpers.members_of_orgao`, NÃO `assembleia_geral` (I2), `categorias`⊆`MEMBER_CATEGORIES`, `statuses`⊆status válidos; `joined_after<=joined_before`) em `backend/models.py` (ver data-model §1)
- [X] T004 [P] Estender `COMUNICADO_STATUSES` aditivamente com `"rascunho"` e `"cancelado"` (manter `parcial`; `enviado_parcial`≡`parcial`) em `backend/models.py` (data-model §4 / R5)
- [X] T005 Estender `ComunicadoCreate` em `backend/models.py`: `audience_filter: Optional[AudienceFilter]`, `dry_run: bool=False`, tornar `segment` opcional, `model_validator` "exactamente um de segment/audience_filter" (data-model §3) — depende de T003
- [X] T006 Estender `_MEMBER_PROJECTION` com `status`, `member_id`, `admission_date` e adicionar `_filter_base(statuses=["ativo"])` (parametriza status, mantém sempre exclusão de `account_type=technical`) em `backend/comunicados_service.py` (R1)
- [X] T007 Implementar `resolve_audience(audience_filter, *, channel, tipo)` em `backend/comunicados_service.py`: OR-dentro-do-tipo / AND-entre-tipos via intersecção de sets; órgãos via **`helpers.members_of_orgao`** (keys `direcao`/`mesa_ag`/`conselho_fiscal`, FR-012 — NB: a key inválida cairia no fallback de admins, por isso T003 fecha o enum); período por `admission_date` (None ⇒ não casa, R6); nominal por `member_id` **e** email (OR interno) com recolha dos não-encontrados; exclusão de `technical` incondicional após intersecção (FR-003); filtros de email (opt-out informativo, sem email) — depende de T003, T006
- [X] T008 [P] Implementar `describe_audience(audience_filter) -> str` (rótulo PT legível: "Direcção" / "12 sócios — Categoria ordinário admitidos antes de 2024") em `backend/comunicados_service.py` (FR-007 / R8)
- [X] T009 Implementar `preview_audience(audience_filter, *, tipo, channels) -> dict` (recipients_count, sample≤5, more, per_type_counts, intersected_count, warnings[technical_excluded/nominal_not_found/intersection_reduced/includes_unapproved]) em `backend/comunicados_service.py` (contracts/preview-audience.md) — depende de T007
- [X] T010 [P] Confirmar em `backend/database.py` `ensure_schema()` que os índices de `comunicados` cobrem o histórico (created_at/status/created_by); registar comentário de que a resolução é in-memory e não exige índice novo (data-model §6) — sem alteração de schema esperada
- [X] T011 [P] Escrever `backend/tests/test_comunicados_audience.py`: OR-dentro/AND-entre-tipos; exclusão `technical`; período com `admission_date=None`; nominal inexistente recolhido; nominal **por email** resolve (C2); **órgão `mesa_ag` resolve para os membros da Mesa da AG — NÃO para a lista de admins (regressão de I2)**; `member_id` snapshot estável (usar `mock_db`, wire `comunicados`/`users`) — cobre T003/T007

**Checkpoint**: motor de audiência resolvido e testado em unidade — endpoints e UI podem começar

---

## Phase 3: User Story 1 — Direcção comunica internamente (Priority: P1) 🎯 MVP

**Goal**: um membro da Direcção (ou admin) compõe um comunicado filtrado por **Órgão: Direcção**, vê preview, envia; só a Direcção recebe; existe rascunho persistido e audit log. Entrega a fatia vertical completa (endpoints + envio + snapshot + rascunho + UI).

**Independent Test**: via quickstart US1 — preview órgão Direcção mostra contagem/amostra; envio (dry-run) persiste `audience_resolved` + audit `comunicado_enviado`; `socio` sem privilégio → 403; rascunho reabre/edita/cancela.

### Tests for User Story 1 ⚠️

- [X] T012 [P] [US1] `backend/tests/test_comunicados_preview.py`: `POST /comunicados/preview-audience` órgão Direcção → count+sample+more; RBAC 403 para `socio`; sem efeitos colaterais (contracts/preview-audience.md)
- [X] T013 [P] [US1] `backend/tests/test_comunicados_draft.py`: ciclo create(`rascunho`)→PATCH→`/enviar`→snapshot+audit; DELETE só em rascunho (409 em terminal); envio bloqueia 0-destinatários (FR-006); `dry_run` não chama email/notify (mock `send_comunicado_batch`/`notify_users`)

### Implementation for User Story 1

- [X] T014 [US1] Adicionar `POST /comunicados/preview-audience` em `backend/routes/comunicados.py` com guard `_can_send` (RBAC FR-008), delegando a `preview_audience()` — depende de T009
- [X] T015 [US1] Estender `POST /comunicados` em `backend/routes/comunicados.py`: caminho `audience_filter` cria `status="rascunho"` (sem dispatch); manter caminho `segment` legado/auto inalterado — depende de T005
- [X] T016 [US1] Adicionar `PATCH /comunicados/{id}` (editar rascunho; só `rascunho`) em `backend/routes/comunicados.py` (contracts/create-comunicado.md)
- [X] T017 [US1] Adicionar `POST /comunicados/{id}/enviar` em `backend/routes/comunicados.py`: re-resolve no envio (FR-010), bloqueia 0-destinatários 422 (FR-006), persiste `audience_resolved`(member_id)+`recipients_count`+`failed_member_ids`+`dry_run` (FR-004), reusa CAS/dispatch existente — depende de T007, T015
- [X] T018 [US1] Estender `dispatch_comunicado`/envio em `backend/comunicados_service.py` para suportar `audience_filter` (resolver via `resolve_audience`), persistir snapshot e respeitar `dry_run` (só não-prod via `IS_PROD`): salta email+notify mas grava doc+resultado (FR-009 / R7). **Em produção (`IS_PROD`), forçar `dry_run=False` (ignorar/recusar `dry_run=true`)** — sem caminho de dry-run em prod (C1); adicionar teste em T013 que cubra esta forçagem — depende de T007
- [X] T019 [US1] Audit log do envio: usar acção `"comunicado_enviado"` com `details={comunicado_id, audience_filter, recipients_count, recipients_sample≤5, dry_run}` (FR-005, alinhar nome p/ SC-003) em `backend/routes/comunicados.py` (data-model §5). **Antes do rename, confirmar que nenhuma query de dashboard/auditoria filtra a string antiga `enviar_comunicado`** (A1) — se filtrar, manter ambas ou actualizar a query
- [X] T020 [US1] Injectar linha "Para: {describe_audience}" no email (FR-007) ligando `describe_audience` ao `comunicado_email_html`/corpo em `backend/comunicados_service.py` — depende de T008
- [X] T021 [US1] Adicionar `DELETE /comunicados/{id}` em `backend/routes/comunicados.py` → `status="cancelado"` (só em rascunho; 409 terminal; autor ou admin); audit `cancelar_comunicado` (contracts/delete-draft.md / FR-011)
- [X] T022 [P] [US1] `frontend/src/utils/api.js`: adicionar `comunicadosAPI.previewAudience(data)`, `send(id)`, `updateDraft(id,data)`, `deleteDraft(id)`
- [X] T023 [US1] `frontend/src/pages/private/comunicados/ComposerCard.js`: adicionar selector de **Órgão** (Assembleia Geral/Direcção/Conselho Fiscal, via `GET /governance/structure` — sem hard-code, FR-012)
- [X] T024 [US1] `frontend/src/pages/private/comunicados/PreviewCard.js`: render contagem + amostra (≤5) + "…mais N" (FR-002) a partir de `previewAudience` (debounced)
- [X] T025 [US1] `frontend/src/pages/private/comunicados/ConfirmDialog.js` + `AdminComunicadosPage.js`: botão "Enviar comunicado" **Floresta `#166534`** (único primário/vista); gestão de rascunho (guardar/editar) e "Eliminar rascunho" **Carmesim outline** (solid só no confirm) — Princípio V
- [X] T026 [US1] `AdminComunicadosPage.js`: badge visual de **dry-run** quando ambiente não-prod (FR-009)
- [X] T027 [US1] Validação manual em browser do fluxo US1 (quickstart US1) — preview, envio dry-run, 403, rascunho — antes de marcar a story como done (Princípio VII)
  - **Validado (2026-06-20)**: smoke browser dry-run US1 (segmentado) + cobertura in-process T046; 0 envios reais

**Checkpoint**: comunicado segmentado por órgão funcional ponta-a-ponta com rascunho + audit. MVP entregável.

---

## Phase 4: User Story 2 — Convocatória de AGA para subconjunto (Priority: P2)

**Goal**: filtros compostos (categoria + status + período + lista nominal) com preview que explica a redução AND e snapshot reconciliável. O motor já suporta; o foco é UI dos tipos de filtro + reconciliação + bloqueios.

**Independent Test**: quickstart US2 — filtro composto mostra count+sample+`per_type`/`intersected`; 0-destinatários bloqueia envio; histórico mostra `audience_filter`+`audience_resolved` imutável a mudanças de cargo.

### Tests for User Story 2 ⚠️

- [X] T028 [P] [US2] `backend/tests/test_comunicados_audience.py` (estender): composição categoria+status+período (AND); `intersection_reduced` quando cai abaixo do tipo mais restritivo (FR-014)
- [X] T029 [P] [US2] `backend/tests/test_comunicados_draft.py` (estender): snapshot imutável após mudança de cargo entre preview e envio (US2-AS3); lista nominal → `nominal_not_found` + `technical_excluded` (FR-003)

### Implementation for User Story 2

- [X] T030 [US2] `frontend/src/pages/private/comunicados/ComposerCard.js`: adicionar inputs de **Categoria** (múltipla), **Status** (múltipla), **Período** (joined_after/joined_before, date range) e **Lista nominal** (member_id/email)
- [X] T031 [US2] `frontend/src/pages/private/comunicados/PreviewCard.js`: mostrar `per_type_counts` + `intersected_count` + mensagem "Filtros combinados por AND…" quando `intersection_reduced` (FR-014); render warnings `nominal_not_found`/`technical_excluded`
- [X] T032 [US2] `AdminComunicadosPage.js`: bloquear botão "Enviar" + mensagem "Filtro não selecciona nenhum sócio — revê os critérios" quando preview `recipients_count==0` (espelha o 422 do backend, FR-006)
- [X] T033 [US2] `AdminComunicadosPage.js`/`HistoryTable.js`: vista de histórico mostra `audience_filter`, `audience_resolved` (contagem), `failed_member_ids`, estado (FR-013)
- [X] T034 [US2] Validação manual em browser do fluxo US2 (quickstart US2)
  - **Validado (2026-06-20)**: cenários US2 cobertos in-process em dry-run (T046); smoke browser aceite como opcional (Princípio VII, decisão do dono)

**Checkpoint**: filtros compostos + reconciliação + histórico funcionais; US1 e US2 independentes.

---

## Phase 5: User Story 3 — Boas-vindas em massa a sócios em onboarding (Priority: P3)

**Goal**: filtrar por `status=pendente_aprovacao` e avisar que o envio atinge contas não aprovadas.

**Independent Test**: quickstart US3 — filtro status pendente_aprovacao lista candidatos; warning `includes_unapproved`; sócios `ativo` não contados.

### Tests for User Story 3 ⚠️

- [X] T035 [P] [US3] `backend/tests/test_comunicados_preview.py` (estender): `statuses=["pendente_aprovacao"]` alarga a base correctamente (não só `ativo`), exclui `ativo`, e gera warning `includes_unapproved` (US3-AS2)

### Implementation for User Story 3

- [X] T036 [US3] `frontend/src/pages/private/comunicados/ComposerCard.js`: expor `pendente_aprovacao` no selector de status
- [X] T037 [US3] `frontend/src/pages/private/comunicados/PreviewCard.js`: ícone/aviso visual quando warning `includes_unapproved` está presente (US3-AS2)
- [X] T038 [US3] Validação manual em browser do fluxo US3 (quickstart US3)
  - **Validado (2026-06-20)**: smoke browser dry-run US3 (pendente_aprovacao + warning includes_unapproved) + cobertura in-process T046

**Checkpoint**: filtro de status para onboarding funcional; US1–US3 independentes.

---

## Phase 6: User Story 4 — Conselho Fiscal dirige-se à Direcção (Priority: P3)

**Goal**: habilitar emissão por privilégio granular `comunicar_intra_orgao` (D1 confirmado) para o Conselho Fiscal enviar a órgãos internos.

**Independent Test**: quickstart US4 — membro do CF com `comunicar_intra_orgao` envia para Órgão: Direcção; Direcção recebe; audit identifica autor (CF) + audiência (Direcção); quem não tem o privilégio → 403.

### Tests for User Story 4 ⚠️

- [X] T039 [P] [US4] `backend/tests/test_comunicados_routes.py` (estender): utilizador CF com `comunicar_intra_orgao` passa o guard e envia para órgão interno; utilizador sem `send_comunicados` nem `comunicar_intra_orgao` → 403; audit identifica autor

### Implementation for User Story 4

- [X] T040 [P] [US4] Registar a privilege `comunicar_intra_orgao` em `backend/governance.py` (lista `PRIVILEGES`) e adicionar helper `can_comunicar_intra_orgao(user)` em `backend/permissions.py` (D1). **Grant path (U1)**: a privilege é uma overlay **aditiva** atribuída manualmente via gestão de privilégios (NÃO auto-concedida por cargo); `can_comunicar_intra_orgao` = `user_can(user, "comunicar_intra_orgao")`. O teste T039 atribui-a explicitamente ao user CF (sem assumir auto-grant)
- [X] T041 [US4] Atualizar o guard `_can_send` em `backend/routes/comunicados.py` para aceitar `send_comunicados` **OU** `comunicar_intra_orgao`. **Âmbito permitido (U2)**: um autor que só tem `comunicar_intra_orgao` (sem `send_comunicados`/admin) só pode enviar para `audience_filter` com **`orgaos ⊆ {direcao, mesa_ag, conselho_fiscal}` e nenhum outro tipo de critério preenchido** (cargos/categorias/statuses/período/nominal vazios); qualquer audiência fora deste âmbito → **403**. Autores com `send_comunicados`/admin não têm esta restrição — depende de T040
- [X] T042 [US4] Garantir entrada de UI ao ecrã de comunicados para quem tem `comunicar_intra_orgao` (gating no `AdminComunicadosPage.js`/rota privada)
- [X] T043 [US4] Validação manual em browser do fluxo US4 (quickstart US4)
  - **Validado (2026-06-20)**: smoke browser dry-run US4 (CF com comunicar_intra_orgao restrito a órgãos internos; 403 sem privilégio) + cobertura in-process T046

**Checkpoint**: todas as user stories funcionais e independentes.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T044 [P] Regressão: correr suite de comunicados completa (`pytest tests/test_comunicados_*.py -q`) + auto-dispatch de governança (garantir que o caminho `segment` legado não regrediu)
- [X] T045 [P] `cd backend && ruff check . && ruff format --check .` e `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60`
- [X] T046 Executar a validação completa do `quickstart.md` (todas as US + edge cases) e registar resultado
  - **Resultado (2026-06-20)**: validação executável in-process em DRY-RUN — `tests/test_comunicados_quickstart.py` (13 cenários: US1–US4 + edge cases + SC-003/SC-004) **PASSED**; 0 emails/notificações reais. Smoke em browser fica opcional (stack local + DB seeded).
- [X] T047 Correr `/speckit-analyze` para consistência cruzada spec↔plan↔tasks contra a constituição antes de `/speckit-implement` (Governance da constituição)
  - **Resultado (2026-06-20)**: 0 críticos, 0 altos; 14/14 FR cobertas (100%); 0 violações da constituição. Achados LOW/MEDIUM opcionais (I1 `enviado_parcial`≡`parcial`, I2 atalho AG=Mesa da AG, U1 âmbito `comunicar_intra_orgao`) documentados — backfill na spec é higiene opcional
- [X] T048 [P] Capturar quaisquer correcções do dono durante a implementação em `tasks/lessons.md` (Princípio VII)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências
- **Foundational (Phase 2)**: depende do Setup — **BLOQUEIA todas as user stories**
- **User Stories (Phase 3–6)**: dependem da Foundational
  - US1 é o MVP (constrói os endpoints + envio + rascunho + UI base)
  - US2/US3 estendem a UI do compositor e os avisos (o motor já suporta os filtros) — apoiam-se na superfície do US1 mas são testáveis independentemente
  - US4 acrescenta a privilege granular — independente das outras
- **Polish (Phase 7)**: depende das user stories desejadas

### User Story Dependencies

- **US1 (P1)**: arranca após Foundational. Sem dependência de outras stories
- **US2 (P2)**: arranca após Foundational; reutiliza endpoints do US1; testável de forma independente
- **US3 (P3)**: arranca após Foundational; reutiliza endpoints do US1; testável de forma independente
- **US4 (P3)**: arranca após Foundational; independente (toca permissions + guard)

### Within Each User Story

- Testes escritos antes da implementação (devem falhar primeiro)
- Modelos → serviços → endpoints → UI → validação em browser

### Parallel Opportunities

- T003, T004 (modelos) em paralelo; T008, T010, T011 em paralelo com a cadeia T006→T007→T009
- Testes marcados [P] de cada story em paralelo
- Após Foundational, US1 (backend) e o scaffolding de UI podem avançar em paralelo
- US2/US3/US4 podem ser distribuídas por programadores diferentes após o US1 fixar os endpoints

---

## Parallel Example: Foundational (Phase 2)

```bash
# Modelos em paralelo:
Task: "T003 AudienceFilter model em backend/models.py"
Task: "T004 estender COMUNICADO_STATUSES em backend/models.py"
# Em paralelo com o motor:
Task: "T008 describe_audience em backend/comunicados_service.py"
Task: "T011 test_comunicados_audience.py"
```

## Parallel Example: User Story 1

```bash
# Testes do US1 juntos:
Task: "T012 test_comunicados_preview.py"
Task: "T013 test_comunicados_draft.py"
# api.js em paralelo com os endpoints backend:
Task: "T022 comunicadosAPI previewAudience/send/updateDraft/deleteDraft"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 Setup → 2. Phase 2 Foundational (CRÍTICO, bloqueia tudo) →
3. Phase 3 US1 → 4. **PARAR e VALIDAR** US1 em browser (dry-run) →
5. Demo/deploy se pronto (envio real a sócios = STOP #6, confirmar com o dono).

### Incremental Delivery

1. Setup + Foundational → motor pronto
2. US1 → testar → MVP (comunicado por órgão + rascunho)
3. US2 → filtros compostos + reconciliação
4. US3 → status onboarding
5. US4 → privilege do Conselho Fiscal
Cada story acrescenta valor sem quebrar as anteriores.

---

## Notes

- [P] = ficheiros diferentes, sem dependências
- O caminho `segment` legado e os gatilhos automáticos de governança **não** são tocados — só estendidos ao lado (Princípio I)
- Alterações de modelo são **aditivas/opcionais** — não quebram docs existentes (STOP #5)
- Envio real de email a sócios é **STOP #6** — usar `dry_run` em não-prod; envio real só com confirmação do dono
- Commit após cada task ou grupo lógico; correr `/speckit-analyze` (T047) antes de `/speckit-implement`
