---

description: "Task list — Dashboard unificado para todos os sócios (spec 020)"
---

# Tasks: Dashboard unificado para todos os sócios

**Input**: Design documents from `/specs/020-dashboard-unificado/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/dashboard-overview.md](./contracts/dashboard-overview.md), [quickstart.md](./quickstart.md)

**Tests**: incluídos — o plano exige tripwire PII (`test_overview_no_pii`) + paridade
admin/socio como evidência-chave de SC-001/SC-002. Sem tripwire, a garantia da spec
regride silenciosamente.

**Organization**: tarefas agrupadas por user story (US1/US2/US3) para permitir
implementação e teste independente. Foundational (Fase 2) contém o endpoint agregador
partilhado — bloqueio único para todas as user stories.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: pode correr em paralelo (ficheiros diferentes, sem dependências)
- **[Story]**: user story a que pertence (US1, US2, US3)
- Todos os paths são relativos ao repo root (`accta-main/accta/`)

## Path Conventions (deste projeto)

- **Backend**: `backend/routes/`, `backend/models.py`, `backend/tests/`
- **Frontend**: `frontend/src/pages/private/`, `frontend/src/pages/private/dashboard/`, `frontend/src/utils/api.js`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: preparar branch e confirmar pré-condições.

- [X] T001 Criar branch `feature/dashboard-unificado` a partir de `develop` (`git switch -c feature/dashboard-unificado develop`)
- [ ] T002 [P] Confirmar em dev isolado (Docker `accta-pg-dev` porta 5433) que temos contas seed `admin@dev.cv` + `socio1@dev.cv` — se faltarem, criar via `scripts/create_admin.py` / seed
- [X] T003 [P] `cd backend && pytest -m unit` na base — smoke que a suíte está verde ANTES de tocar (guardar contagem esperada como baseline)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: endpoint agregador + response model + tripwire — bloqueio único para US1/US2/US3.

**⚠️ CRITICAL**: nenhuma tarefa de US1/US2/US3 pode começar até T009 estar verde.

### Modelos + endpoint

- [X] T004 Adicionar Pydantic models `MonthlyPoint`, `FinanceOverview`, `SociosOverview`, `AtosOverview`, `UltimaVotacao`, `VotacoesOverview`, `ProximaAssembleia`, `AssembleiasOverview`, `DashboardOverview` em `backend/models.py` (secção de modelos de resposta; conforme [data-model.md](./data-model.md))
- [X] T005 Criar `backend/routes/dashboard.py` com `router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])` e `GET /overview` autenticado (`get_current_user`), `response_model=DashboardOverview` — implementação reutiliza `compute_financial_summary` e `compute_dre_report` de `routes/finances.py` (imports directos; **não** duplicar)
- [X] T006 [US1] Preencher no endpoint o bloco `finance` (saldo actual, receitas/despesas/resultado do ano, quotas do mês, monthly[12], despesas_por_categoria, mes_atual/mes_anterior) — usa apenas `db.transactions` via as duas `compute_*`
- [X] T007 [US3] Preencher no endpoint os blocos `socios` (activos + novos 90d), `atos` (pendentes + aguarda_direcao + aguarda_proposta via count/aggregate), `votacoes` (abertas + ultima_fechada com `participacao_pct`) e `assembleias` (proximas ≤ 3 com id/titulo/data/tipo) — conforme [data-model.md](./data-model.md) tabela de derivações
- [X] T008 Registar o novo router em `backend/server.py`: `from routes.dashboard import router as dashboard_router` + `app.include_router(dashboard_router)` (seguir padrão dos routers existentes)

### Testes (tripwire + paridade)

- [X] T009 [P] Criar `backend/tests/test_dashboard_routes.py` com: (a) `test_admin_get_overview` → 200 + shape completo; (b) `test_socio_get_overview` → 200 + shape idêntico ao admin (**paridade**); (c) `test_no_auth_returns_401`; (d) **`test_overview_no_pii`** — walker recursivo com `FORBIDDEN_KEYS={"email","phone","member_id","name","cpf","password","photo_url","address"}` (ver [research.md#R6](./research.md)); (e) `test_reuses_compute_functions` — mock de `compute_financial_summary`/`compute_dre_report` a comprovar que o endpoint chama-as sem duplicar lógica
- [X] T010 [P] Adicionar em `backend/tests/test_access_matrix.py` a nova rota `/api/dashboard/overview` como coluna nova, com célula `socio → 200` (matriz é fonte da evidência da spec 018 sobre paridade de acessos). **Não** adicionar comparações inline de `role` — a tripwire da spec 018 (`test_no_inline_role_checks`) MUST continuar verde
- [X] T011 [P] Correr `cd backend && pytest tests/test_dashboard_routes.py tests/test_access_matrix.py -v` — verde antes de avançar

**Checkpoint**: `GET /api/dashboard/overview` devolve 200 a admin e sócio comum com payload idêntico, tripwire PII passa, matriz de acessos actualizada. US1/US2/US3 podem começar em paralelo.

---

## Phase 3: User Story 1 — Sócio comum vê evolução financeira agregada (P1) 🎯 MVP

**Goal**: sócio comum abre `/dashboard` e vê os mesmos widgets financeiros agregados que o admin (saldo, gráfico mensal, categorias, quotas do mês).

**Independent Test**: login `socio1@dev.cv` → `/dashboard` → confirmar que `FinanceSummary`, `AdminStats` (renomeado, ver T014), `FinanceCharts` estão renderizados (com dados do endpoint agregador) sem que o menu Finanças apareça.

### Implementação

- [X] T012 [US1] Em `frontend/src/utils/api.js`, adicionar grupo `dashboardAPI` com `overview: () => api.get('/dashboard/overview')` (padrão dos outros grupos)
- [X] T013 [US1] Em `frontend/src/lib/queryClient.js`, adicionar `queryKeys.dashboard = { overview: () => ['dashboard', 'overview'] }` (padrão dos outros)
- [X] T014 [US1] Em `frontend/src/pages/private/DashboardPage.js`:
  1. Remover a variável `hasFinance` e as 3 queries `statsQuery`/`financeSummaryQuery`/`dreQuery` (linhas ~75–91)
  2. Adicionar `overviewQuery = useQuery({ queryKey: queryKeys.dashboard.overview(), queryFn: () => dashboardAPI.overview().then(r => r.data) })`
  3. Derivar `stats`, `financeSummary`, `dreData` do payload do overview (ver mapeamento em [research.md#R8](./research.md))
  4. Remover os `{hasFinance && …}` guards em torno de `AdminStats`, `FinanceCharts` e `FinanceSummary` — passam a renderizar sempre
  5. Actualizar `loading` para depender de `overviewQuery.isLoading` em vez das 3 antigas
- [X] T015 [US1] Em `frontend/src/pages/private/dashboard/AdminStats.js`, renomear função exportada para `InstitutionalStats` (ou manter `AdminStats` mas actualizar prop label — "Total Sócios"/"Sócios Activos"/"Eventos Activos"/"Receita Anual" continuam correctos para todos os perfis; **decisão ponytail**: renomear ficheiro apenas se não gerar diff extra; caso contrário, mantém-se o nome interno e não se toca). Se o consumidor mudar (T014), refactor coincide num só sítio
- [ ] T016 [US1] Verificação funcional em dev: `yarn start` com `REACT_APP_BACKEND_URL=http://localhost:8001`, login `socio1@dev.cv`, abrir `/dashboard`, DevTools Network filtrar `overview` → confirmar payload com blocos `finance/socios/atos/votacoes/assembleias` e widgets financeiros renderizados

**Checkpoint**: US1 funcional — sócio comum vê a evolução financeira. `/financeiro` ainda gated no backend (não mexemos).

---

## Phase 4: User Story 2 — Drill-down permanece gated (widget read-only) (P1) 🎯 MVP

**Goal**: para sócios sem privilégio de finanças, os widgets financeiros do Dashboard **não** têm afordância de clique nem hyperlink para `/financeiro`.

**Independent Test**: como `socio1@dev.cv`, passar rato sobre `FinanceSummary`/`FinanceCharts` → cursor default; sem `role="button"` no DOM; nenhum link/onClick para `/financeiro`. Como admin, mesmo widget → cursor pointer + clique navega para `/financeiro`.

### Implementação

- [X] T017 [US2] Em `frontend/src/pages/private/dashboard/FinanceSummary.js`:
  1. Ler `useAuth()` para obter `isAdmin`/`isFinanceiro` (ou passar prop `clickable` de `DashboardPage.js`)
  2. Se `!clickable`: remover `onClick`, `role="button"`, `tabIndex`, `onKeyDown`, `cursor-pointer`, seta `<ArrowRight />` e `aria-label`
  3. Manter classe visual e `hover:shadow-*` (o cartão continua a viver como card, apenas não sugere clique)
- [X] T018 [US2] Em `frontend/src/pages/private/dashboard/FinanceCharts.js` (o componente lazy) aplicar o mesmo padrão: `onViewAll` só invocado / renderizado quando `clickable`; botão "Ver detalhes" escondido quando `!clickable`
- [X] T019 [US2] Em `frontend/src/pages/private/DashboardPage.js`, propagar `clickable={hasFinance}` a `<FinanceSummary />` e `<FinanceCharts />` (re-introduzir `const hasFinance = isAdmin || isFinanceiro;` como **flag de afordância**, não de renderização; comentar `// ponytail: gate visual apenas; conteúdo é universal`)
- [ ] T020 [US2] Verificação funcional em dev: login `socio1@dev.cv` → widgets financeiros sem afordância; login `admin@dev.cv` → widgets clicáveis; `curl -H "Authorization: Bearer <socio-token>" /api/financeiro/...` → mantém 403 (não é para mexer)

**Checkpoint**: US1+US2 juntas cumprem a promessa da feature — Dashboard universal, área/drill-down gated.

---

## Phase 5: User Story 3 — KPIs adicionais activados (P2)

**Goal**: mostrar no Dashboard os 5 KPIs de vida associativa seleccionados (A.1 sócios activos, A.2 novos 90d, A.3 próximas AGAs, A.5 atos pendentes, A.7 participação votações) — respeitando US1/US2.

**Independent Test**: como qualquer utilizador, `/dashboard` mostra os 5 KPIs alimentados pelo bloco `overviewQuery.data` (sem chamadas extra); nenhum expõe nome/email de sócios; drill-downs gated (Atos → `/atos` continua 403 para sócio; AGAs `/assembleias/{id}` acessível a todos).

### Implementação

- [X] T021 [P] [US3] Criar `frontend/src/pages/private/dashboard/VidaAssociativa.js` — cartão único com 4 tiles compactas (Sócios Activos, Novos 90d, Atos Pendentes, Participação Última Votação) alimentadas por `overview.socios`, `overview.atos`, `overview.votacoes.ultima_fechada`; **respeita FR-004**: tile de "Atos Pendentes" só é clicável (link para `/atos`) se `hasFinance || isDirecao` (reutiliza helper existente do frontend), tile "Participação" nunca navega (é KPI puro)
- [X] T022 [P] [US3] Criar `frontend/src/pages/private/dashboard/ProximasAssembleias.js` — lista `overview.assembleias.proximas` (até 3), cada item clicável para `/assembleias/{id}` (acessível a qualquer autenticado; sem gate)
- [X] T023 [P] [US3] Criar `frontend/src/pages/private/dashboard/QuotasMes.js` — tile compacta com `overview.finance.quotas_mes` (CVE formatado) + texto "quotas do mês em curso"; drill-down para `/financeiro/quotas` só se `clickable=hasFinance` (segue padrão US2)
- [X] T024 [US3] Em `frontend/src/pages/private/DashboardPage.js`, montar os 3 novos componentes no layout, entre `<FinanceSummary />` e `<Contribuicoes />`. Ordem: `QuotasMes` → `VidaAssociativa` → `ProximasAssembleias`
- [ ] T025 [US3] Verificação funcional em dev: seed dev com 1 assembleia marcada + 1 ato pendente + 1 votação fechada → confirmar que os 3 componentes mostram os números certos; sócio comum vê tudo, tiles gated não têm afordância de clique

**Checkpoint**: US3 completa; Dashboard tem os 10 KPIs seleccionados no Q1 + os widgets pré-existentes.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: universalização do RankingTopN (Q2), validação final e release Via B.

- [X] T026 [P] Verificar em prod (via `GET /api/ranking/settings` como admin) o valor de `visibility`. Se `direcao_only` → `PATCH /api/ranking/settings` com `{"visibility": "all_members"}` (endpoint existente, admin-only, auditado). Zero código a mudar; **decisão Q2** aplicada por configuração
- [X] T027 [P] Correr `cd backend && ruff check . && ruff format --check .` e `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60` — verde
- [X] T028 [P] Correr `cd backend && pytest -m unit` — verde (baseline de T003 + N novos testes de dashboard)
- [X] T029 Rodar validação end-to-end do [quickstart.md](./quickstart.md) passos 1–5 em dev — todos os checks verdes (paridade admin/sócio, tripwire PII no browser, universalização do Top-N)
- [X] T030 **STOP p/ dono** (Princípio VI): confirmar release. Merge `feature/dashboard-unificado → develop` via PR (CodeRabbit opcional); depois `release/vX.Y.Z → main` via PR de release
- [X] T031 **STOP p/ dono**: deploy backend por **Via B** ([[prod-backend-deployed-state]] + `docs/runbook-deploy-backend-via-b.md`) — Vercel deploya frontend automaticamente na `main`
- [X] T032 **Teste decisivo em prod** ([quickstart.md#6](./quickstart.md)): 3 curls a `api.controlador.cv/api/dashboard/overview` (admin 200, sócio comum 200 com payload idêntico, sem-token 401); confirmar em navegador como sócio comum que os widgets financeiros aparecem e `/financeiro` continua 403
- [ ] T033 **Validação funcional pelo dono** (Princípio VII): abrir Dashboard como sócio comum em `controlador.cv` no navegador e confirmar visualmente todos os cenários de aceitação (US1/US2/US3 na spec)
- [X] T034 Actualizar memória (`memory/prod-backend-deployed-state.md` — nova versão) + `memory/MEMORY.md` (linha de spec 020 concluída) + `CLAUDE.md` (mover 020 para "concluída")

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Fase 1)** — sem dependências, arranca imediato.
- **Foundational (Fase 2)** — depende de Fase 1; **BLOQUEIA** US1/US2/US3.
- **User Stories (Fases 3–5)** — todas dependem de T011 (endpoint verde). Podem então correr em paralelo por diferentes devs; sequencialmente por 1 dev.
- **Polish (Fase 6)** — depende de US1 + US2 verdes (US3 é P2, opcional para MVP); T026 pode correr sozinho a qualquer altura.

### User Story Dependencies

- **US1 (P1)**: depende do endpoint (T005–T009). Independente das outras.
- **US2 (P1)**: depende de US1 (o `hasFinance` é reintroduzido em T019 como flag de afordância — precisa do estado pós-T014). Trivialmente sequencial após US1.
- **US3 (P2)**: depende do endpoint (T007). Independente de US1/US2 excepto pela colocação visual em `DashboardPage.js` (T024). Se US3 for adiada, US1+US2 fecham o MVP.

### Dentro de cada história

- Backend antes de frontend (endpoint verde antes de tocar `DashboardPage.js`).
- Novos componentes visuais podem correr em paralelo dentro da mesma US (T021/T022/T023 são [P]).

### Parallel Opportunities

- **Fase 1**: T002/T003 em paralelo.
- **Fase 2**: T009/T010/T011 em paralelo (ficheiros de teste diferentes).
- **Fase 5**: T021/T022/T023 em paralelo (ficheiros diferentes) — T024 depois de todos.
- **Fase 6**: T026/T027/T028 em paralelo.

---

## Parallel Example: User Story 3

```bash
# 3 componentes novos independentes, correm em paralelo:
Task: "Criar frontend/src/pages/private/dashboard/VidaAssociativa.js"
Task: "Criar frontend/src/pages/private/dashboard/ProximasAssembleias.js"
Task: "Criar frontend/src/pages/private/dashboard/QuotasMes.js"
# Depois:
Task: "Montar os 3 em DashboardPage.js (T024)"
```

---

## Implementation Strategy

### MVP (US1 + US2)

1. Fase 1: Setup.
2. Fase 2: Foundational (endpoint + tripwire).
3. Fase 3: US1 (frontend cai o gate, wire aggregator).
4. Fase 4: US2 (afordância condicional).
5. **STOP & VALIDATE**: quickstart passos 1–3 verdes em dev.
6. Fase 6 (T026–T033): release Via B + validação em prod.

MVP é **US1 + US2**. Sem US2, US1 abre porta lateral no RBAC (widget clicável leva sócio para `/financeiro` gated → 403 confuso) → US2 é co-MVP.

### Incremental Delivery

1. Fundações → endpoint agregador verde (evidência técnica).
2. + US1 → sócio vê a evolução financeira (evidência de produto).
3. + US2 → RBAC intocado, drill-down gated (evidência de segurança).
4. + US3 → KPIs de vida associativa (evidência de valor incremental).
5. Cada passo é releasable de forma independente se houver decisão do dono.

### Notas ponytail

- Zero deps novas, zero migração, zero campo novo em `users`.
- 1 endpoint agregador em vez de 3-4 endpoints "públicos" (Rung 6 — one line? Não; Rung 7 — código mínimo com contrato explícito).
- `RankingSettings.visibility` já default `all_members` → Q2 pode ser só verificação de config (T026), sem código.
- Tripwire PII (T009) é o **check runnable** que a Constituição pede para lógica não-trivial (spec/ponytail: "não é lazy sem check").

---

## Notes

- [P] = ficheiros diferentes, sem dependências.
- [Story] = mapeamento à user story para rastreabilidade.
- Cada US é independentemente entregável (US2 é co-MVP com US1 por acoplamento de segurança).
- Verificar tripwire PII SEMPRE que se acrescentar campo ao `DashboardOverview` no futuro.
- Commit após cada tarefa ou grupo lógico; scope `feat(dashboard)` em Conventional Commits.
- **Nunca** mexer em `/financeiro/*` como parte desta feature (fora de âmbito por design; qualquer regressão aí = STOP).
