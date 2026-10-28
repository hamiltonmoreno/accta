# Implementation Plan: Dashboard unificado para todos os sócios

**Branch**: `feature/dashboard-unificado` | **Date**: 2026-07-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/020-dashboard-unificado/spec.md`

## Summary

Uniformizar o Dashboard: **os mesmos widgets para admin, financeiro, moderador e sócio
comum**. Inclui a **evolução financeira agregada** (saldo, receitas × despesas mensal,
resultado, quotas do mês, pizza de categorias) + **KPIs de vida associativa** (sócios
activos, novos 90d, próximas AGAs, atos pendentes agregados, participação em votações).
Área `/financeiro` e drill-down continuam gated pelos privilégios existentes (US2). Ranking
Top-N universalizado (Q2). Sem PII em widgets universais (FR-005/SC-002).

**Abordagem técnica**: **1 endpoint agregador** `GET /api/dashboard/overview` (autenticado,
sem role check), com `response_model` estrito que reutiliza as funções `compute_*` já
existentes em `routes/finances.py` — assim, o payload é o único ponto de contacto do
Dashboard com dados agregados, o contrato é explícito e uma tripwire garante que nunca
regride para PII. Frontend deixa cair o gate `hasFinance = isAdmin || isFinanceiro`, todos
os widgets ficam sempre visíveis; para quem não tem privilégio, os widgets são **read-only
sem afordância de clique** (US2). Endpoints existentes (`/finances/*`, `/stats`) **não
mudam** — continuam a servir `/financeiro`. `RankingSettings.visibility` default é já
`all_members`; só verificar (não migrar) que prod está nesse valor.

## Technical Context

**Language/Version**: Python 3.11 (backend), React 19 (frontend)

**Primary Dependencies**: FastAPI + asyncpg + Mongo-compat DAO (backend); Tailwind +
shadcn/ui + TanStack Query + Recharts (frontend). **Zero deps novas.**

**Storage**: PostgreSQL/Supabase — leitura apenas; nenhum campo novo, nenhuma migração,
nenhuma nova coleção.

**Testing**: pytest (backend); manual navegador (frontend, Princípio VII do dono).

**Target Platform**: Web (portal ACCTA em produção — `controlador.cv` + `api.controlador.cv`).

**Project Type**: Web application (backend + frontend).

**Performance Goals**: Dashboard deve renderizar em ≤ 1s p95 com dados frescos (~ `staleTime`
de 30s do TanStack Query). 1 round-trip para o agregado + queries já existentes de
polls/events/ranking em paralelo.

**Constraints**: RBAC intocado (privilégios continuam a governar `/financeiro`, `/atos`
lista, etc.); 0 PII em widgets universais; PT-PT; neutro-led + design system ACCTA; sem
dark mode; sem inadimplência.

**Scale/Scope**: ≤ algumas centenas de sócios; 4 tipos de utilizador (admin/socio +
funções seed Financeiro/Moderador); ~10 widgets no Dashboard após a feature.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Verificação | Status |
|-----------|-------------|--------|
| I. Simplicity First | 1 endpoint agregador (não 3 endpoints "públicos"), reutilizando `compute_financial_summary`/`compute_dre_report`. Frontend cai 1 flag (`hasFinance` no Dashboard). | ✅ |
| II. Root-Cause Discipline | O problema-raiz é o **gate na UI** (`hasFinance`) que confunde "área gated" com "informação gated". A correcção é remover o gate na UI e desacoplar a leitura do Dashboard das rotas gated do módulo Financeiro (via novo endpoint). Nada de patches em cada widget. | ✅ |
| III. RBAC + Audit em toda a superfície protegida | O novo endpoint é `get_current_user` (autenticado — não é rota pública). É **read-only**, portanto **sem** audit-log (auditamos escritas). Endpoints existentes continuam com os seus checks. Nenhum inline role check. | ✅ |
| IV. Language Discipline | Toda a UI em PT-PT; identificadores EN genéricos (`dashboard`, `overview`, `finance`, `socios`, `atos`); nada de PT-EN drift. | ✅ |
| V. Design System Authority | Neutro-led; Floresta positivo (não aplicável — Dashboard não tem CTAs positivos primários novos); Carmesim identidade; nenhum dark mode. | ✅ |
| VI. GitFlow + Confirmation | `feature/dashboard-unificado → develop → release/vX.Y.Z → main`. Toca `backend/` ⇒ **Via B obrigatória** ([[prod-backend-deployed-state]]). | ✅ |
| VII. Verification Before Done | Após Via B, teste decisivo: `curl -H "Authorization: Bearer <token-socio-comum>" /api/dashboard/overview` → 200 + agregado; abrir Dashboard como sócio comum em navegador. | ✅ |

**Gate: PASS** — nenhuma violação por justificar.

## Project Structure

### Documentation (this feature)

```text
specs/020-dashboard-unificado/
├── plan.md              # Este ficheiro
├── research.md          # Fase 0 (decisões técnicas)
├── data-model.md        # Fase 1 (payload agregador — sem novas entidades DB)
├── quickstart.md        # Fase 1 (guia de validação end-to-end)
├── contracts/
│   └── dashboard-overview.md   # Contrato do novo endpoint
├── checklists/
│   └── requirements.md  # Já criado por /speckit-specify
└── tasks.md             # Fase 2 (/speckit-tasks — NÃO criado aqui)
```

### Source Code (repository root)

```text
backend/
├── routes/
│   ├── dashboard.py     # NOVO — endpoint /api/dashboard/overview
│   ├── finances.py      # inalterado (as computes ficam reutilizáveis; import)
│   └── ranking.py       # inalterado — verificar apenas config em prod
├── models.py            # +DashboardOverview (Pydantic response_model estrito)
├── server.py            # +include_router(dashboard.router)
└── tests/
    ├── test_dashboard_routes.py    # NOVO — cobertura + tripwire PII
    └── test_access_matrix.py       # +1 célula (socio → /dashboard/overview → 200)

frontend/
└── src/
    ├── pages/private/
    │   ├── DashboardPage.js        # remover gate hasFinance nos widgets financeiros
    │   └── dashboard/
    │       ├── FinanceSummary.js   # tornar clique condicional a hasFinance
    │       ├── FinanceCharts.js    # idem (drill-down "Ver detalhes" só com hasFinance)
    │       ├── AdminStats.js       # renomear e adaptar (ver research R2)
    │       ├── VidaAssociativa.js  # NOVO — widgets A.1/A.2/A.3/A.5/A.7
    │       └── QuotasMes.js        # NOVO — B.11 quotas do mês
    └── utils/
        └── api.js                  # +dashboardAPI.overview()
```

**Structure Decision**: Web application (backend + frontend). Reutiliza a árvore existente
— nada de novos pacotes ou reorganização. Um único módulo novo por lado (backend
`routes/dashboard.py` + `test_dashboard_routes.py`; frontend `dashboard/VidaAssociativa.js`
+ `QuotasMes.js`).

## Complexity Tracking

*Sem violações da constituição — secção não aplicável.*

---

## Deploy

**Via B obrigatória** (toca `backend/`, [[prod-backend-deployed-state]]):

1. Merge `feature/dashboard-unificado → develop` (com testes verdes).
2. Release PR `release/vX.Y.Z → main` (tag).
3. Vercel deploya frontend automaticamente na `main`.
4. Backend deploy via **Via B** (`docs/runbook-deploy-backend-via-b.md`).
5. **Teste decisivo** — 3 curls no VPS:
   - `curl -H "Authorization: Bearer <token-admin>" https://api.controlador.cv/api/dashboard/overview` → 200 com payload.
   - `curl -H "Authorization: Bearer <token-socio-comum>" https://api.controlador.cv/api/dashboard/overview` → 200 com payload (**a evidência-chave da feature**).
   - `curl https://api.controlador.cv/api/dashboard/overview` (sem token) → 401.
6. Validação funcional em navegador (dono, Princípio VII): abrir Dashboard como sócio comum e confirmar que aparecem gráfico de receitas × despesas, saldo, quotas do mês, KPIs de vida associativa, e que o menu Finanças continua escondido.
