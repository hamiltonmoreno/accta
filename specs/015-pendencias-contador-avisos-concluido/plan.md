# Implementation Plan: Pendências v2 — contador no menu + avisos apontam ao painel

**Branch**: `feature/pendencias-contador-avisos` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/015-pendencias-contador-avisos/spec.md`

## Summary

Dois remates sobre o painel `/pendencias` da spec 014:

1. **US1 (P1/MVP)** — um **contador** (badge) junto ao item de menu «As minhas pendências» na
   barra lateral, com o **mesmo total role-aware** que o painel mostraria, número exato com cap
   **"9+"**, escondido quando é zero, fresco no carregamento/navegação (reutiliza a cache do
   TanStack Query — sem stream/polling dedicado).
2. **US2 (P2)** — re-apontar a **ligação** dos avisos de Atos **pendentes** (specs 010/012/013)
   para `/pendencias`, **mantendo** os avisos de Atos **decididos** (aprovação/rejeição, incl.
   spec 011) a apontar para `/financeiro/co-aprovacoes` (onde o Ato decidido é visível).

**Abordagem técnica**: a derivação do total (4 `useQuery` + filtros cliente, hoje inline em
`PendenciasPage.js`) é extraída para um hook partilhado `usePendencias()` — **uma única fonte
de verdade** que a página e a barra lateral consomem (garante SC-002: contador ≡ painel, sem
deriva). O backend ganha uma 2.ª constante de link (`_LINK_PENDENTE = "/pendencias"`) aplicada
**só** aos 3 call-sites de Atos pendentes; os 2 de decididos ficam em `_LINK`.

## Technical Context

**Language/Version**: Python 3.11 (backend), JavaScript / React 19 (frontend)

**Primary Dependencies**: FastAPI + asyncpg (backend); React 19 + TanStack Query v5 +
Tailwind + lucide-react (frontend). **Zero dependências novas.**

**Storage**: N/A — o contador é **derivado** (não persistido). O campo `link` da notificação
já existe (`Notification.link`, `models.py`); só muda o **valor** gravado em 3 call-sites.

**Testing**: pytest (backend — `tests/test_atos.py`, `test_atos_overdue.py`,
`test_atos_rejeicao_motivo.py`); validação de UI no navegador (Princípio VII, critério do dono).

**Target Platform**: Web (PWA) — Vercel (frontend) + Docker/Nginx no VPS (backend).

**Project Type**: Web application (frontend React + backend FastAPI).

**Performance Goals**: a barra lateral está presente em todas as páginas; o contador **reutiliza
a cache** (TanStack `staleTime: 30s`, `refetchOnWindowFocus`). Para um sócio comum só disparam
2 queries (polls + events); as 2 de Atos têm `enabled: isDir`. SC-004: sem degradação percetível.

**Constraints**: role-aware obrigatório (FR-009 / SC-005) — **não** pedir dados de Atos a um
sócio comum (sem 403); voto secreto **fora** (herdado: o painel só lê `polls` + `events` + `atos`,
nunca `eleicoes`/`deliberacoes`). Backend tocado ⇒ release **exige Via B**.

**Scale/Scope**: ≤ algumas centenas de sócios; 1 hook novo + 2 ficheiros frontend editados +
1 ficheiro backend editado + testes.

## Constitution Check

*GATE: avaliado contra `.specify/memory/constitution.md` v1.0.0.*

| Princípio | Avaliação |
|-----------|-----------|
| **I. Simplicity First** | ✅ Hook partilhado = 1 definição, 2 consumidores (não é abstração especulativa: elimina a deriva que o SC-002 proíbe). Backend = split de constante (4 linhas). Sem flags, sem shims. |
| **II. Root-Cause Discipline** | ✅ O destino do aviso muda **na origem** (a constante por categoria), não com remendos por-notificação. |
| **III. RBAC + Audit** | ✅ Sem endpoint novo, sem write novo ⇒ sem novo audit log. Frontend role-aware (Atos só com `enabled: isDir` ⇒ FR-009, sem 403). Sem SQL cru. |
| **IV. Language** | ✅ User-facing PT (`aria-label` do badge em PT, sem linguagem de inadimplência); identificadores EN (`usePendencias`, `_LINK_PENDENTE`). |
| **V. Design System** | ✅ O badge **reutiliza o padrão de badge da barra lateral já existente** (o de «Pedidos de Inscrição»: bolha carmesim, mesmas classes). Não introduz cor/decisão nova — apenas estende um padrão ratificado em uso. |
| **VI. GitFlow + Via B** | ✅ `feature/* → develop`; backend tocado ⇒ release `develop→main` precisa de **Via B** (`runbook-deploy-backend-via-b.md`). |
| **VII. Verification Before Done** | ✅ Backend: pytest (asserts de link) verde. Frontend: validação no navegador (dono). |

**Resultado: PASS — zero violações.** Sem entradas em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/015-pendencias-contador-avisos/
├── spec.md              # Especificação (já existe)
├── checklist.md         # (já existe)
├── plan.md              # Este ficheiro
├── research.md          # Decisões de desenho (Fase 0)
├── data-model.md        # Entidades derivadas / campo link (Fase 1)
├── contracts/
│   └── pendencias-contract.md   # Invariante contador≡painel + contrato de link dos avisos
├── quickstart.md        # Cenários de validação ponta-a-ponta
└── tasks.md             # (gerado por /speckit-tasks — NÃO por este comando)
```

### Source Code (repository root)

```text
frontend/src/
├── hooks/
│   └── usePendencias.js          # NOVO — fonte única: 4 queries + filtros + total (role-aware)
├── pages/private/
│   └── PendenciasPage.js         # EDITADO — consome usePendencias() (remove derivação inline)
└── layouts/
    └── PrivateLayout.js          # EDITADO — badge 'pendencias' no item /pendencias (cap "9+")

backend/
├── routes/
│   └── atos.py                   # EDITADO — +_LINK_PENDENTE; 3 sites pendentes → /pendencias
└── tests/
    ├── test_atos.py              # EDITADO — assert create_ato link == /pendencias
    └── test_atos_overdue.py      # EDITADO — assert overdue links == /pendencias
```

**Structure Decision**: Web application (Opção 2). O contador é frontend puro (US1); o
re-apontamento dos avisos é backend puro (US2). As duas histórias são independentes e podem
ir em PRs separados, mas partilham o mesmo branch/feature.

## Design Detail

### US1 — Contador (frontend)

**Hook `frontend/src/hooks/usePendencias.js` (novo).** Encapsula exatamente a derivação que
hoje vive inline em `PendenciasPage.js:74-99,155`:

- 4 `useQuery` com os **mesmos `queryKeys`** (`polls.list()`, `events.upcoming()`,
  `atos.list({mine:true})`, `atos.list({status:'pendente'})`) ⇒ **partilham a cache** com o
  painel (sem pedidos extra quando já carregado).
- `isDir = Boolean(isAdmin || isDirecao)` (de `useAuth`); as 2 queries de Atos com `enabled: isDir`.
- Filtros cliente idênticos: votações (`status==='aberta' && !has_voted`), eventos
  (`!attendees.includes(user.id)`), assinatura (`items`), propostos (`items.filter(created_by===user.id)`).
- Devolve `{ votacoes, eventos, assinaturaItems, propostosItems, total, isLoading, anyError, isDir }`.
  `total = votacoes.length + eventos.length + (isDir ? assinaturaItems.length + propostosItems.length : 0)`.

**`PendenciasPage.js` (editado).** Substitui os 4 `useQuery`/filtros/`total` inline por
`const { votacoes, eventos, assinaturaItems, propostosItems, total, isLoading, anyError } = usePendencias();`.
Mantém o mapeamento `sections` (display) e o resto do JSX intactos (o banner de erro da review
da spec 014 continua a usar `anyError`).

**`PrivateLayout.js` (editado).**
- Linha 56: adicionar `badge: 'pendencias'` ao item `{ label: 'As minhas pendências', path: '/pendencias', ... }`.
- `const { total: pendenciasCount } = usePendencias();` (role-aware via o próprio hook).
- Novo ramo de render espelhando o de `'registration'` (linhas 383-396): mostra só se
  `pendenciasCount > 0`; valor = `pendenciasCount > 9 ? '9+' : pendenciasCount`; **mesmas classes**
  (bolha carmesim; ponto no estado colapsado).

> **Nota de perf (SC-004):** o hook na barra lateral faz com que `polls` + `events` passem a
> ser lidos em **todas** as páginas privadas (Atos só para Direção). É aceite pela spec
> (Assumptions: cache + frescura no carregamento); payloads pequenos, `staleTime 30s` limita
> refetches. Sem stream/polling novo.

### US2 — Avisos apontam ao painel (backend)

`backend/routes/atos.py` linha 45 — `_LINK = "/financeiro/co-aprovacoes"`. Introduzir:

```python
_LINK = "/financeiro/co-aprovacoes"   # Atos DECIDIDOS (visíveis aqui)
_LINK_PENDENTE = "/pendencias"        # Atos PENDENTES (painel acionável — spec 015)
```

Aplicar `_LINK_PENDENTE` **só** nos 3 sites de Atos **pendentes**; os 2 de **decididos** ficam:

| Call site | Linhas | Evento | Estado | Link |
|-----------|--------|--------|--------|------|
| `create_ato()` | 115-122 | Novo Ato a aguardar assinatura | **pendente** | → `_LINK_PENDENTE` |
| `_notify_overdue_atos_locked()` (Direção) | 405-411 | Varrimento atrasados (010/013) | **pendente** | → `_LINK_PENDENTE` |
| `_notify_overdue_atos_locked()` (proponente) | 421-427 | Varrimento atrasados (012) | **pendente** | → `_LINK_PENDENTE` |
| `sign_ato()` | 219-226 | Aprovado/rejeitado (incl. motivo 011) | **decidido** | mantém `_LINK` |
| `execute_ato()` | 277-284 | Pagamento executado | **decidido** | mantém `_LINK` |

> **NÃO é swap cego da constante** — `_LINK` continua a existir e a servir os decididos.

## Complexity Tracking

> Sem violações constitucionais — secção não aplicável.
