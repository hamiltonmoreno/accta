# Research: Dashboard unificado

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-07-13

## R1 — Backend hoje bloqueia sócio comum nos endpoints financeiros / stats / atos?

**Descoberta** (grep em `backend/routes/`):

| Endpoint | Gate actual | 403 para `role=socio`? |
|----------|-------------|------------------------|
| `GET /api/stats` (`routes/stats.py:17`) | `has_role_or_privilege(user, ("admin",), "manage_finances")` | **Sim** |
| `GET /api/finances/summary` (`routes/finances.py:424`) | `require_view_finances(user)` (admin/financeiro/`view_finances_readonly`) | **Sim** |
| `GET /api/finances/dre` (`routes/finances.py:486`) | `require_view_finances(user)` | **Sim** |
| `GET /api/atos` (`routes/atos.py:127`) | `_require_view` = `can_view_finances OR is_direcao` | **Sim** |
| `GET /api/assembleias` (`routes/assembleias.py:363`) | `get_current_user` | Não (OK) |
| `GET /api/polls` (`routes/polls.py:54`) | `get_current_user` (filtra `rascunho`) | Não (OK) |

**Consequência**: a entrega **não pode** ser frontend-only. É preciso backend →
release **Via B**. Assumption da spec ("provável frontend-only") **fica reprovada** por
esta descoberta — actualização da spec: nenhuma, o próprio texto da assumption previa este
cenário ("*se sim, ajuste mínimo aditivo → Via B*").

## R2 — Novo endpoint agregador vs. abrir os endpoints existentes

**Alternativas consideradas**:

1. **Loosen os 4 endpoints existentes** — mudar `require_view_finances` para
   `get_current_user` em `/stats`, `/summary`, `/dre`, `/atos`. Menos linhas, mas:
   - `/atos` devolve **detalhes por Ato** (não é agregado) → não podemos abrir.
   - `/summary` e `/dre` são agregados hoje, mas o contrato é implícito — se alguém
     acrescentar um campo com PII, todos os sócios passam a vê-lo.
   - Requer 4 tripwires PII (um por endpoint) para blindar o futuro.

2. **Endpoint agregador dedicado** `GET /api/dashboard/overview` — recolhe os 10 KPIs
   de v1 num único payload, com `response_model` estrito (Pydantic), servido a qualquer
   utilizador autenticado.
   - 1 endpoint, 1 contrato, 1 tripwire.
   - Frontend faz 1 round-trip em vez de 3-4.
   - As funções `compute_financial_summary` e `compute_dre_report` já estão extraídas
     e são invocáveis (`routes/finances.py:361/434`).
   - Endpoints antigos ficam intactos, `/financeiro` continua a usá-los.

**Decisão**: **opção 2 — endpoint agregador**.

**Racional**: o custo em linhas é comparável (a opção 1 obriga a tripwires + refactor de
`_require_view` em `/atos` para expor apenas contagem sem detalhes = mais mudanças
distribuídas); a opção 2 concentra tudo num contrato explícito e diminui a superfície de
regressão. **Root-cause discipline** (Princípio II): o problema é o Dashboard estar
acoplado a rotas do módulo Financeiro; a correcção estrutural é desacoplá-los.

**Rejeitado**: loosening dos 4 endpoints.

## R3 — Contagem agregada de Atos pendentes sem dar acesso à lista

**Problema**: FR-007 pede A.5 "Atos pendentes agregados (contagem por estado)". O endpoint
`/api/atos` está gated por bom motivo (contém detalhes). Sócio comum **não** pode listar
atos, mas **pode** ver a contagem agregada.

**Decisão**: a contagem é feita dentro de `/dashboard/overview` via
`db.atos.count_documents({"status": "pendente"})` (+ discriminação simples por
`assinaturas_needed`/`assinaturas_dadas` para "aguarda proposta" vs "aguarda Direcção",
se relevante). Nada é exposto além dos números.

**Alternativas**:
- Loosen `/atos?count_only=true` — introduz um caminho paralelo no endpoint principal,
  fere a coesão. Rejeitado.
- Expor `/atos/counts` — endpoint dedicado. Sobrepõe-se ao agregador. Rejeitado.

## R4 — Participação em votações (A.7): definição de "última votação fechada"

**Definição**: última `poll` com `status=fechada` (não `aberta` nem `rascunho`) ordenada
por `closed_at` desc. `participacao_pct = votos_registados / socios_votantes_no_momento
* 100`. Reutiliza o padrão de contagem de `is_voting_member(user)` (`permissions.py`) em
snapshot ou aproximação — se calcular ao vivo (sócios votantes actuais) o valor deriva
do estado corrente (aceitável para exibição, é KPI de contexto).

**Decisão pragmática**: `participacao_pct = round(len(votos) / max(1, count_socios_ativos_votantes) * 100)`
calculado in-line no endpoint. Nada de snapshot novo (Ponytail Rung 1 — "does this need
to exist at all?" — o snapshot não é necessário para MVP).

**Trade-off aceite**: se a lista de sócios votantes mudar entre o fecho da votação e a
consulta, o número flutua ligeiramente. Aceitável para um KPI de Dashboard.

## R5 — Cache de `RankingSettings.visibility` em prod

**Descoberta**: `RankingSettings.visibility: Literal["all_members", "direcao_only"] =
"all_members"` (`models.py:2656`). Default = `all_members`. Q2 = universalizar → precisamos
garantir que prod está em `all_members`.

**Verificação prevista** no quickstart:
```bash
curl -H "Authorization: Bearer <admin-token>" https://api.controlador.cv/api/ranking/settings
# Confirmar "visibility": "all_members"
```

Se estiver em `direcao_only`, o admin muda via `PATCH /api/ranking/settings` (endpoint já
existente, admin-only, auditado). **Zero código a mudar por isto** — configuração
existente.

## R6 — Tripwire PII no endpoint agregador

**Objetivo**: garantir que nenhum campo do payload contém identificadores de sócios.

**Implementação** (em `test_dashboard_routes.py`):
```python
FORBIDDEN_KEYS = {"id", "email", "phone", "member_id", "name", "cpf", "password", "photo_url"}

def _walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in FORBIDDEN_KEYS, f"PII leak: {path}.{k}"
            _walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _walk(v, f"{path}[{i}]")

async def test_overview_no_pii(client, socio_user):
    r = await client.get("/api/dashboard/overview", headers=_auth(socio_user))
    _walk(r.json())
```

**Excepção**: `assembleias.proximas[].id` — é `assembleia_id` público (necessário para
linkar). Ajuste no walker: `id` só é bandeira vermelha quando o path contém `socio`,
`user`, `member`. Ou mais simples: incluir só `titulo` + `data` no payload, sem `id` —
o clique para `/assembleias/{id}` fica fora do widget universal (só admins/mesa AG têm
drill-down; sócio comum vê só o texto). Confirmar no data-model.

**Decisão**: **incluir `id` das assembleias** (necessário para toda a gente linkar para
`/assembleias/{id}` — que é acessível a qualquer autenticado por design). A tripwire lista
`id` apenas se aparecer em contextos como `socios.id` — nunca aparece porque o payload
não expõe listas de sócios.

## R7 — Frontend: remover o gate `hasFinance` sem partir a página do admin

**Problema**: `DashboardPage.js:30` faz `const hasFinance = isAdmin || isFinanceiro;` que
esconde `AdminStats`, `FinanceCharts`, `FinanceSummary`. Se removermos o gate, admins não
perdem nada — mas os widgets financeiros hoje **navegam para `/financeiro`** ao clicar
(`FinanceSummary.js:10`, `FinanceCharts.js` idem).

**Padrão para US2**: cada widget financeiro recebe um prop `clickable={hasFinance}` (ou
lê `useAuth` internamente). Quando `false`:
- `role="button"` → não; `tabIndex` → não; `onClick` → não; `cursor` → `default`;
- `aria-label` → deixa cair "Ver X"; mantém título descritivo;
- `hover:shadow-...` continua (é decorativo) mas `hover:cursor` fica `default`.

Zero mudança visual para o admin; para o sócio comum, o widget aparece mas é uma tile de
leitura.

## R8 — Endpoints do frontend a substituir

`DashboardPage.js` hoje faz 8 queries; após a feature:

| Query hoje | Após |
|------------|------|
| `statsAPI.get()` gated `hasFinance` | **substituída** por `dashboardAPI.overview()` (para todos) |
| `financesAPI.getSummary({year})` gated `hasFinance` | idem |
| `financesAPI.getDRE(year)` gated `hasFinance` | idem |
| `pollsAPI.getAll()` universal | mantém-se (fornece "votações abertas" em detalhe) |
| `eventsAPI.getUpcoming()` universal | mantém-se |
| `activityAPI.getRecent(15)` universal | mantém-se |
| `reportAPI.getPersonal()` universal | mantém-se |
| `rankingAPI.me` + `rankingAPI.leaderboard` universal | mantém-se (Q2 = universal) |

Total: **3 queries substituídas por 1**. Menos round-trips, menos código no frontend.

Nota: `pollsAPI.getAll()` continua a ser útil para o widget "Votações abertas" (mostra
título + botão votar), mas a **contagem de participação** da última fechada vem do
`/dashboard/overview`.

## R9 — RBAC no `include_router` do novo módulo

**Padrão do projecto**: cada `routes/*.py` cria um `APIRouter(prefix="/api/...")` e
`server.py` faz `include_router`. O novo `routes/dashboard.py` segue o padrão:

```python
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/overview", response_model=DashboardOverview)
async def get_overview(current_user: User = Depends(get_current_user)):
    ...
```

**Não** há inline check de role — o endpoint é universal por design; a tripwire
`test_no_inline_role_checks` (spec 018) continua verde.

## R10 — Rate limiting

**Descoberta**: `server.py` aplica `slowapi` com limite default 200/min. O Dashboard é o
ecrã inicial de qualquer sessão → 1 chamada por abertura. 200/min = folgado.

**Decisão**: sem `@limiter.limit` explícito no `/dashboard/overview` — herda o default.
