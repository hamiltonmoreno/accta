# Implementation Plan: Painel «As minhas pendências»

**Branch**: `feature/painel-minhas-pendencias` | **Date**: 2026-06-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/014-painel-minhas-pendencias/spec.md`

## Summary

Página dedicada `/pendencias` que **agrega**, para o utilizador autenticado, tudo o que
aguarda a sua ação, **derivado** do estado dos objetos existentes e filtrado no cliente.
**Frontend-only, zero backend** (decisão do dono + confirmado pela RBAC existente). O painel
é **role-aware**:

- **Qualquer sócio**: **votações abertas por votar** (`GET /polls` → `status=aberta &&
  !has_voted`, e só se for membro votante) + **eventos próximos por confirmar**
  (`GET /events/upcoming` → `!attendees.includes(eu)`).
- **Direção/admin (adicionalmente)**: **Atos que propus** ainda pendentes
  (`GET /atos?status=pendente` → `created_by == eu`) + **Atos à minha assinatura**
  (`GET /atos?pendentes_para_mim=true`).

Cada item tem ligação para agir; estado vazio explícito quando nada está pendente.

## Technical Context

**Language/Version**: JavaScript (React 19) — frontend.

**Primary Dependencies**: Tailwind CSS 3, shadcn/ui (New York), TanStack Query (`useQuery`),
Framer Motion, lucide-react, react-router-dom. **Zero deps novas.**

**Storage**: N/A — a pendência é **derivada** dos reads existentes; **sem coleção/entidade/
schema novos**. **Backend: nenhuma alteração.**

**Testing**: validação em navegador (Princípio VII, dono) + preview Vercel; sem testes de
backend (não toca backend).

**Target Platform**: web (frontend Vercel). **Não toca `backend/` ⇒ sem Via B** — a entrega
vai pela Vercel no push a `main`.

**Project Type**: web app (frontend-led).

**Performance Goals**: as queries correm em paralelo (TanStack Query); poucos objetos por
sócio; sem N+1 (cada tipo = 1 read existente). `GET /atos?status=pendente` devolve os Atos
pendentes (poucos) e filtra-se no cliente — só chamado para Direção/admin.

**Constraints**: **respeitar o segredo do voto** (eleições/deliberações secretas NUNCA
entram); **RBAC existente** dos reads é a fronteira (um sócio que chame `GET /atos` leva 403
— logo o frontend **só** mostra as secções de Atos a quem é Direção/admin); design system
ACCTA (skill `frontend-design`); texto PT; sem inadimplência.

**Scale/Scope**: ≤ algumas centenas de sócios.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|-----------|-----------|
| **I. Simplicity First** | ✅ Frontend-only; reaproveita reads existentes; sem endpoint/entidade/coleção novos; pendência derivada. |
| **II. Root-Cause** | ✅ N/A (feature nova); sem patches. |
| **III. RBAC + Audit** | ✅ Só **leitura**; sem nova superfície protegida; a RBAC existente dos reads (`_require_view` nos Atos, etc.) é respeitada — o painel não a contorna. Sem ação de admin ⇒ sem audit. |
| **IV. Language** | ✅ UI em PT; identificadores EN; sem inadimplência. |
| **V. Design System** | ✅ Aplica o skill `frontend-design` (neutral-led, Floresta única primária positiva, Carmesim identidade/destrutivo, sem dark mode); ligações para agir, não botões a mais. |
| **VI. GitFlow + Confirmação** | ✅ `feature/*` off `develop`; **só frontend ⇒ Vercel, sem Via B**; sem STOP conditions. |
| **VII. Verification** | ✅ Exercitar em navegador (preview Vercel / dono) antes de "feito". |

**Resultado**: PASS — sem violações; **Complexity Tracking** não aplicável.

## Project Structure

### Documentation (this feature)

```text
specs/014-painel-minhas-pendencias/
├── plan.md              # Este ficheiro
├── research.md          # Fase 0 — RBAC dos reads + quem propõe Atos + filtros por-utilizador
├── data-model.md        # Fase 1 — Pendência (derivada, sem entidade nova)
├── quickstart.md        # Fase 1 — cenários de validação (sócio vs Direção; estado vazio)
├── contracts/
│   └── pendencias-ui.md      # contrato de UI: a página e os reads que a alimentam
└── tasks.md             # Fase 2 (/speckit-tasks — NÃO criado aqui)
```

### Source Code (repository root)

```text
frontend/src/
├── pages/private/
│   └── PendenciasPage.js        # nova página /pendencias (TanStack Query; secções role-aware)
├── components/
│   └── (opcional) PendenciaCard.js / secções reutilizáveis
├── App.js                       # +rota lazy /pendencias (ProtectedRoute)
├── layouts/PrivateLayout.js     # +item de menu "As minhas pendências" (sidebar do sócio)
└── utils/api.js                 # reutiliza atosAPI.list / pollsAPI / eventsAPI (sem endpoint novo;
                                 #   no máximo um helper fino de agregação no cliente)
```

**Structure Decision**: frontend-led; **nenhum** ficheiro de `backend/` tocado. Nova página +
rota + item de menu, consumindo os endpoints de leitura já existentes via `useQuery`.

## Complexity Tracking

> Sem violações constitucionais — secção não aplicável.

## Nota de descoberta (importante para o âmbito)

A RBAC existente revela que **só `admin`/Direção propõem Atos** (`_require_create`,
`routes/atos.py`). Logo, para um **sócio comum** as secções de Atos **não existem** (e
`GET /atos` devolve-lhe 403): o seu painel é **votações + eventos**. As duas secções de Atos
("que propus" e "à minha assinatura") são, na prática, **Direção/admin**. Isto **não** muda a
intenção do dono (painel role-aware de "o que aguarda a minha ação") nem exige backend — só
torna o painel adaptado ao papel. Capturado em [research.md](research.md).
