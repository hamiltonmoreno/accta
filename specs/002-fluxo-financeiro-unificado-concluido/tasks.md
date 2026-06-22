---
description: "Task list — Fluxo Financeiro Unificado"
---

# Tasks: Fluxo Financeiro Unificado

**Input**: Design documents from `specs/002-fluxo-financeiro-unificado-concluido/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: INCLUÍDOS para o backend (Princípio VII da Constitution + critério "pytest verde" no quickstart). Frontend é verificado no browser (não há suite automática de UI). Testes unit/in-process usam `mock_db` do `conftest.py`.

**Organization**: Tarefas agrupadas por user story (US1–US4 da spec) + Setup, Foundational, Migração (STOP) e Polish.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode correr em paralelo (ficheiros distintos, sem dependência por completar)
- **[Story]**: US1–US4; Setup/Foundational/Migração/Polish sem label

## Path Conventions

Web app: `backend/` (FastAPI) + `frontend/src/` (React). Scripts em `scripts/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar terreno; branch `feature/fluxo-financeiro-unificado` já criado off `develop`.

- [X] T001 Confirmar baseline verde: `cd backend && pytest -q` e registar nº de testes a passar antes de qualquer alteração (linha de base para detetar regressões).
- [X] T002 [P] Rever fixtures de `backend/tests/conftest.py` e confirmar que `transactions`, `projects`, `atos`, `finance_settings`, `exercicios` estão pré-ligados no `mock_db`; anotar que `project_expenses` precisa de wiring in-test (`mock_db.project_expenses = MagicMock(...)`) conforme CLAUDE.md.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Alterações de modelo (aditivas-opcionais) e schema que TODAS as stories usam.

**⚠️ CRITICAL**: nenhuma user story arranca antes desta fase estar completa.

- [X] T003 [P] Adicionar `project_id: Optional[str] = None` ao modelo `Transaction` em `backend/models.py` (após `ato_id`/`proof_url`/`conferido`; comentário PT a explicar o vínculo ao projeto).
- [X] T004 [P] Adicionar `project_id: Optional[str] = None` a `Ato` e a `AtoCreate` em `backend/models.py` (campos aditivos-opcionais).
- [X] T005 [P] Adicionar `category: Optional[str] = None` a `ProjectExpenseCreate` em `backend/models.py`.
- [X] T006 [P] Tornar `RelatorioContasSubmit.document_id` `Optional[str] = None` em `backend/models.py`.
- [X] T007 Adicionar índice de expressão em `transactions(doc->>'project_id')` dentro de `ensure_schema()` em `backend/database.py` (idempotente; junto aos índices de `transactions`).
- [X] T008 Extrair/partilhar o helper de limiar: garantir que `_coaprovacao_limiar()` de `backend/routes/finances.py` é importável por `routes/projects.py` (mover para um módulo comum leve OU importar diretamente de `routes.finances`), sem duplicar a leitura defensiva.

**Checkpoint**: modelos e schema prontos — stories podem começar.

---

## Phase 3: User Story 1 - Despesa de projeto aparece no caixa (Priority: P1) 🎯 MVP

**Goal**: Registar/listar/apagar despesa de projeto como `Transaction` com `project_id`; `spent` derivado; filtro por projeto em finanças; despesas entram automaticamente no resumo/DRE/balancete.

**Independent Test**: criar projeto+despesa (abaixo do limiar) e confirmar que aparece em `/finances/transactions?project_id=`, que `spent` reflete a soma e que `/finances/summary` do período aumenta — sem ação extra em Finanças.

### Tests for User Story 1 ⚠️

- [X] T009 [P] [US1] Teste: `POST /projects/{id}/expenses` cria uma `Transaction` (`type="despesa"`, `project_id`, `category`) e NÃO escreve em `project_expenses`, em `backend/tests/test_projects_expenses.py`.
- [X] T010 [P] [US1] Teste: `GET /projects/{id}/expenses` devolve as transações do projeto; `DELETE` remove a transação e recomputa `spent`, em `backend/tests/test_projects_expenses.py`.
- [X] T011 [P] [US1] Teste: `GET /finances/transactions?project_id=` filtra corretamente, em `backend/tests/test_finances_project_filter.py`.
- [X] T012 [P] [US1] Teste: `spent` derivado por agregação no detalhe do projeto e na listagem (sem N+1), em `backend/tests/test_projects_spent_derived.py`.

### Implementation for User Story 1

- [X] T013 [US1] Reescrever `add_expense` em `backend/routes/projects.py`: validar/normalizar `category` (default `operacional`, ∈ `EXPENSE_CATEGORIES`), criar `Transaction(type="despesa", project_id=project_id, …)` via `db.transactions.insert_one`, em vez de `project_expenses`; manter guard `can_manage_project`; **adicionar `create_audit_log`**; manter notificações de stakeholders + alerta de orçamento excedido (com `spent` derivado).
- [X] T014 [US1] Reescrever `delete_expense` em `backend/routes/projects.py`: apagar a `Transaction` (`{id, project_id, type:"despesa"}`) + `create_audit_log`; recomputar `spent` (agregação sobre `transactions`). (Guarda de `ato_id` entra na US2 — T020.)
- [X] T015 [US1] Adicionar `GET /projects/{id}/expenses` (ou ajustar o existente) em `backend/routes/projects.py` para listar `transactions.find({project_id, type:"despesa"}).sort(date,-1)`.
- [X] T016 [US1] Implementar `spent` derivado em `backend/routes/projects.py`: no detalhe (`GET /projects/{id}`) por agregação `SUM(transactions where project_id, type="despesa")` + bloco `orcamento_execucao={budget,realizado,desvio}`; na listagem (`GET /projects`) por **uma** agregação `$group` por `project_id` (evitar N+1).
- [X] T017 [US1] Adicionar parâmetro `project_id: Optional[str]` a `list_transactions` em `backend/routes/finances.py` (→ `query["project_id"]`).

**Checkpoint**: despesa de projeto reflete-se no caixa, resumo, DRE e balancete sem relançamento manual.

---

## Phase 4: User Story 2 - Gate de co-aprovação nas despesas de projeto (Priority: P1)

**Goal**: Despesa de projeto acima do limiar exige Ato (Art. 54); Ato propaga `project_id`; despesa originada por Ato não removível pela via simples.

**Independent Test**: com limiar positivo, despesa direta acima → 400; criar+executar Ato com `project_id` → despesa ligada a Ato e projeto; `DELETE` dessa despesa → 400.

### Tests for User Story 2 ⚠️

- [X] T018 [P] [US2] Teste: despesa de projeto `amount > limiar` é recusada (400, mensagem PT a pedir Ato), em `backend/tests/test_projects_expenses_gate.py`.
- [X] T019 [P] [US2] Teste: `execute_ato` com `project_id` cria `Transaction` com `ato_id` E `project_id`; conta para `spent`, em `backend/tests/test_atos_project.py`.
- [X] T020 [P] [US2] Teste: `DELETE /projects/{id}/expenses/{tx}` recusa (400) quando a transação tem `ato_id`, em `backend/tests/test_projects_expenses_gate.py`.

### Implementation for User Story 2

- [X] T021 [US2] Aplicar o gate Art. 54 em `add_expense` (`backend/routes/projects.py`): ler `_coaprovacao_limiar()` (de T008); se `>0` e `amount>limiar` → 400 com mensagem PT a orientar para criar um Ato de pagamento com o projeto associado.
- [X] T022 [US2] Em `delete_expense` (`backend/routes/projects.py`): se a transação tiver `ato_id` → 400 (`"Despesa originada por um Acto executado; reverta pelo Acto."`).
- [X] T023 [US2] Em `execute_ato` (`backend/routes/atos.py`): propagar `project_id=ato.get("project_id")` para a `Transaction` criada.

**Checkpoint**: o atalho que contornava o Art. 54 está fechado; despesas via Ato ligadas ao projeto.

---

## Phase 5: User Story 3 - Sistema gera o Relatório e Contas anual (Priority: P2)

**Goal**: Endpoint que gera o Relatório e Contas anual em PDF a partir dos dados; submissão sem upload obrigatório.

**Independent Test**: pedir o PDF anual e confirmar capa+DRE+balancete+orçado vs. realizado+assinaturas com totais == `/finances/summary?year=`; submeter relatório sem `document_id` → 200 com `dre_snapshot` congelado.

### Tests for User Story 3 ⚠️

- [X] T024 [P] [US3] Teste: `submeter_relatorio` sem `document_id` → 200, estado `relatorio_submetido`, `dre_snapshot` congelado; com `document_id` → publica anexo, em `backend/tests/test_prestacao_contas_relatorio_opcional.py`.
- [X] T025 [P] [US3] Teste: endpoint do Relatório e Contas anual devolve `application/pdf` e os totais coincidem com `compute_financial_summary(year)`, em `backend/tests/test_relatorio_anual_pdf.py`.

### Implementation for User Story 3

- [X] T026 [US3] Tornar o upload opcional em `submeter_relatorio` (`backend/routes/prestacao_contas.py`): chamar `_validate_document`/`_publish_document` só quando `document_id` for fornecido (espelhar o padrão de orçamento/plano); manter `dre_snapshot = compute_dre_report(ano)` sempre.
- [X] T027 [US3] Implementar `GET /exercicios/{ano}/relatorio/pdf` reutilizando o gerador FPDF de `finances.py` (DRE). **Hospedar a função de montagem do PDF em `backend/routes/finances.py`** (onde já vive o FPDF) e expô-la/importá-la a partir de `prestacao_contas.py` — evita import circular `prestacao_contas ↔ finances`. Compor: capa + DRE + balancete anual (`compute_financial_summary(year)`) + orçado vs. realizado (`orcamento/execucao`) + folha de assinaturas (cargos de `governance.py`/`permissions.py`); guard de leitura financeira; rodapé "Documento gerado automaticamente pelo Portal ACCTA".

**Checkpoint**: relatório anual oficial sai do sistema; submissão não exige ficheiro.

---

## Phase 6: User Story 4 - Relatórios gerados em destaque (Priority: P3)

**Goal**: UI que destaca os relatórios gerados e relega o upload para anexo opcional; despesa de projeto com categoria; Orçado vs. Realizado no detalhe do projeto.

**Independent Test**: abrir Finanças/Prestação de Contas no browser e ver a secção de relatórios gerados com downloads + upload rotulado "anexos (opcional)".

### Implementation for User Story 4

- [X] T028 [P] [US4] Adicionar os endpoints novos a `frontend/src/utils/api.js`: relatório anual PDF (`GET /exercicios/{ano}/relatorio/pdf`), filtro `project_id` em transações, e `category` no payload de despesa de projeto.
- [X] T029 [US4] `frontend/src/pages/private/financeiro/PrestacaoContasTab.js`: adicionar secção "Relatórios gerados pelo sistema" com download dos **quatro** relatórios — DRE (`/finances/dre/pdf`), balancete, Relatório e Contas anual (`/exercicios/{ano}/relatorio/pdf`) e **fluxo de caixa CSV (`/finances/transactions/csv`)** — e mover o upload para zona "anexos (opcional)"; submissão deixa de exigir ficheiro. Seguir `frontend-design` (botões neutros; sem Carmesim como primário positivo).
- [X] T030 [P] [US4] `frontend/src/pages/private/FinanceiroPage.js` e/ou `BalancetesTab.js`: ponto de entrada para os relatórios gerados, coerente com a nova secção.
- [X] T031 [US4] Detalhe do projeto (`frontend/src/pages/private/` — página/aba de projeto): campo `category` no formulário de despesa e bloco "Orçado vs. Realizado" (budget vs. spent vs. desvio); mensagem amigável quando o gate Art. 54 recusa (orientar para Ato).

**Checkpoint**: UX deixa claro que o sistema gera os relatórios; upload é anexo opcional.

---

## Phase 7: Migração de dados (STOP — requer confirmação explícita do dono)

**Purpose**: Converter `project_expenses` históricas em transações sem duplicar.

**⚠️ STOP (Princípio VI #1)**: o `--apply` só corre após confirmação explícita do dono, depois de rever o relatório de reconciliação do dry-run.

- [X] T032 Criar `scripts/migrate_project_expenses_to_transactions.py` com modo **dry-run por defeito**: lê `project_expenses`, mapeia para transações candidatas (`type="despesa"`, `project_id`, `category="operacional"`, preservando `description`/`amount`/`date`/`created_by`), e imprime relatório de reconciliação (contagens + **suspeitos de duplicado**: despesa sem `project_id`, mesmo `amount`, data próxima/descrição semelhante). Não escreve nada. Padrão alinhado com `scripts/migrate_income_categories.py`.
- [X] T033 Adicionar `--apply` ao script (idempotente): insere as transações e marca `project_expenses` migradas (`migrated_to_transaction_id`); re-correr não duplica. **Não executar `--apply` nesta fase** — apenas implementar.
- [X] T034 Correr o **dry-run** e anexar o relatório de reconciliação ao PR para revisão do dono (gate de confirmação antes de qualquer `--apply`).

  **Relatório dry-run (2026-06-21, contra prod via VPS, read-only):**
  `0 project_expenses | 0 projects | 0 despesas` (12 transações, todas
  receitas/quotas) → **nada a migrar**. Não há despesas legadas (registadas
  antes da feature) por reconciliar; o `--apply` seria um no-op, logo
  **dispensado**. Fase de migração concluída sem escrita em prod (STOP
  resolvido por dados).

**Checkpoint**: histórico pronto a migrar; aplicação dispensada (0 candidatos).

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T035 [P] Correr `cd backend && ruff check . && ruff format .` e `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60`; corrigir o que surgir.
- [X] T036 [P] Atualizar documentação: nota no runbook/finanças sobre "despesa de projeto = transação" e "relatório anual gerado". **Verificar o read-side cutover (FR-014)**: confirmar por busca que nenhum caminho de leitura consome `project_expenses` como fonte de dados após a unificação (todas as leituras de despesas passam por `transactions` com `project_id`); ajustar/remover menções residuais.
- [X] T037 Executar a validação do `quickstart.md` (Cenários 1–3 via HTTP; Cenário 4 no browser com screenshot) — Princípio VII.

  **Cenários 1–3: FEITOS e verdes** — automatizados como validação executável
  ponta-a-ponta em `backend/tests/test_fluxo_financeiro_unificado_quickstart.py`
  (estado partilhado em memória; `3 passed`). Mapeiam 1:1 ao quickstart: C1 despesa
  de projeto no caixa + spent/orçamento-execução + summary, C2 gate Art. 54 +
  Ato↔projeto + guarda de delete (ato_id), C3 Relatório e Contas em PDF +
  submissão sem upload com `dre_snapshot` congelado.
  **Cenário 4 (UI): browser-verificado na implementação (US4), sem screenshot
  novo** — checklist em
  `specs/002-fluxo-financeiro-unificado-concluido/T037-cenario4-browser.md`.
  Fechado por decisão do dono (2026-06-22): a UX da Prestação de Contas já estava
  verificada e a feature em prod (v0.5.27); não se recapturou artefacto. Ressalva
  registada para paridade futura com o Princípio VII.
- [X] T038 [P] Registar lição em `tasks/lessons.md` se houver correção do dono durante a implementação; atualizar memória relevante (ex.: `finance-specs-alignment`). — sem correção do dono na implementação; memória `fluxo-financeiro-unificado-state` atualizada (released + em prod via v0.5.27; migração no-op).
- [X] T039 (Opcional) `/speckit-analyze` para conferir consistência cross-artefacto antes do `/speckit-implement`/merge.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (P1)**: sem dependências.
- **Foundational (P2)**: depende de Setup; **bloqueia** todas as stories (modelos + schema + helper de limiar).
- **US1 (P3)**: depende de Foundational. MVP.
- **US2 (P4)**: depende de Foundational **e** de US1 (gate/guarda vivem em `add_expense`/`delete_expense` reescritos na US1).
- **US3 (P5)**: depende de Foundational (T006 — `document_id` opcional). Independente de US1/US2.
- **US4 (P6)**: depende de US1–US3 (consome os endpoints novos no frontend).
- **Migração (P7)**: depende de Foundational+US1 (precisa de `Transaction.project_id`). `--apply` = STOP.
- **Polish (P8)**: depois das stories desejadas.

### Within Each User Story

- Testes escritos primeiro e a FALHAR antes da implementação (Princípio VII).
- Modelos (Foundational) antes de rotas; rotas antes de frontend.

### Parallel Opportunities

- T003–T006 (modelos) em paralelo; T007/T008 a seguir.
- Testes marcados [P] de cada story em paralelo.
- US3 pode correr em paralelo com US1/US2 (ficheiros distintos: `prestacao_contas.py` vs. `projects.py`).
- Frontend (US4) [P] entre `api.js` / páginas distintas.

---

## Parallel Example: Foundational

```bash
# Modelos aditivos em paralelo (mesmo ficheiro models.py — sequenciar se houver conflito de edição):
T003 Transaction.project_id
T004 Ato/AtoCreate.project_id
T005 ProjectExpenseCreate.category
T006 RelatorioContasSubmit.document_id opcional
```

## Parallel Example: User Story 1 (testes)

```bash
T009 cria-Transaction (test_projects_expenses.py)
T010 list/delete (test_projects_expenses.py)
T011 filtro project_id (test_finances_project_filter.py)
T012 spent derivado (test_projects_spent_derived.py)
```

---

## Implementation Strategy

### MVP First (US1)

1. Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1).
2. **STOP e VALIDAR**: despesa de projeto no caixa, `spent` derivado, filtro, efeito no resumo.
3. Demonstrável como MVP.

### Incremental Delivery

US1 (caixa) → US2 (gate Art. 54) → US3 (relatório gerado) → US4 (UX) → Migração (com confirmação) → Polish. Cada incremento entrega valor sem partir o anterior.

---

## Notes

- [P] = ficheiros distintos, sem dependência por completar.
- Despesas de projeto passam a `transactions`; `project_expenses` fica legível (legado) até à migração.
- `--apply` da migração é STOP — nunca correr sem OK explícito do dono.
- Commit por tarefa ou grupo lógico; Conventional Commits com escopo (`feat(financas): …`).
- Verificar testes a falhar antes de implementar; validar cada story no checkpoint.
