# Implementation Plan: Notificações Push no Celular (Web Push / PWA)

**Branch**: `claude/mobile-push-notifications-i2qx2k` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-notificacoes-push-celular/spec.md`

**Note**: Documentação retroativa — a implementação já existe (PR #362). Este
plano descreve a abordagem técnica efetivamente seguida.

## Summary

Entregar **todas** as notificações in-app também como **Web Push** no
dispositivo do sócio, com a app fechada (Android/desktop; iOS 16.4+ via PWA na
Tela de Início). A abordagem reutiliza o PWA + service worker existentes e
adiciona: assinatura **VAPID** no backend (`pywebpush`), uma coleção de
subscrições, um helper de envio (`dispatch_push`) engatado nos pontos únicos de
criação de notificações (`create_notification` / `notify_users` /
`notify_all_active_users`), endpoints `/api/push/*`, handlers `push`/
`notificationclick` no service worker, e um toggle de opt-in no Perfil. A
funcionalidade **degrada graciosamente** sem as chaves VAPID (no-op + 503) e
**valida o endpoint** de subscrição contra SSRF.

## Technical Context

**Language/Version**: Python 3.11 (backend), JavaScript / React 19 (frontend)

**Primary Dependencies**: FastAPI + asyncpg (DAO Mongo-compatível);
`pywebpush==2.0.0` (assinatura/entrega VAPID); React 19 + service worker do PWA;
`@tanstack/react-query`, `sonner` (já presentes)

**Storage**: PostgreSQL/Supabase via DAO — nova coleção `push_subscriptions`
(tabela `(pk bigserial, doc jsonb)`), índices em `ensure_schema()`

**Testing**: pytest (unit, DB mockada via `conftest.py`) — `tests/test_push_routes.py`

**Target Platform**: Navegadores com Web Push (Android/Chrome, desktop); iOS
16.4+ apenas como PWA na Tela de Início

**Project Type**: Web (backend FastAPI + frontend React/PWA)

**Performance Goals**: Envio não bloqueia a criação da notificação de forma
percetível; broadcast resolve as subscrições numa única query (sem N+1);
entrega via threadpool (`asyncio.to_thread`) para não bloquear o event loop

**Constraints**: Degradação graciosa sem VAPID; sem dependências novas no
frontend; sem email (MVP); anti-SSRF no endpoint; um registo por dispositivo

**Scale/Scope**: ~centenas de sócios × 1–N dispositivos; 5 ficheiros novos +
~9 editados; 1 dependência backend nova

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Simplicity First** — ✅ Reutiliza PWA/SW e os pontos únicos de
  notificação (sem tocar nos call-sites espalhados). 1 dependência nova,
  justificada (padrão Web Push). Zero deps frontend novas.
- **II. Root-Cause Discipline** — ✅ Envio best-effort com poda de subscrições
  mortas na origem (404/410), não silenciando falhas com band-aids.
- **III. RBAC + Audit + sem SQL cru** — ✅ Todos os endpoints `/api/push/*`
  exigem `get_current_user`; sem `password` exposto; índices só em
  `ensure_schema()`; DAO Mongo-style (sem SQL cru). Estes endpoints são ações
  do próprio sócio (não escritas de admin), logo **sem audit-log** aplicável.
  Defesa adicional **anti-SSRF** na subscrição.
- **IV. Language Discipline** — ✅ Texto ao utilizador em PT; identificadores
  genéricos em EN (`dispatch_push`, `subscribe`, `endpoint`); comentários PT.
- **V. Design System Authority** — ✅ Toggle segue o padrão do `EmailPrefs`
  (`card-technical`, `Switch`, neutro-led); sem Carmesim como primário positivo.
- **VI. GitFlow + Confirmation** — ✅ Feature → PR para `develop` (#362). Toca
  `backend/` ⇒ release `develop→main` exige **Via B**; envs VAPID definidas pelo
  dono em produção; sem email a sócios reais.
- **VII. Verification Before Done** — ✅ 24 testes unitários verdes, ruff limpo,
  round-trip VAPID verificado, Vercel preview deployado; validação manual
  ponta-a-ponta em Android/iPhone fica como T-residual pós-deploy.

**Resultado**: PASS (sem violações; nenhuma entrada em Complexity Tracking).

## Project Structure

### Documentation (this feature)

```text
specs/009-notificacoes-push-celular/
├── plan.md              # Este ficheiro
├── research.md          # Fase 0 — decisões técnicas
├── data-model.md        # Fase 1 — entidades/coleção
├── quickstart.md        # Fase 1 — guia de validação ponta-a-ponta
├── contracts/           # Fase 1 — contratos dos endpoints /api/push
│   └── push-api.md
└── checklists/
    └── requirements.md  # Qualidade da spec (do /speckit-specify)
```

### Source Code (repository root)

```text
backend/
├── push_service.py            # NOVO — VAPID + dispatch_push + is_safe_push_endpoint
├── routes/push.py             # NOVO — /api/push (vapid-public-key, subscribe, unsubscribe, test)
├── routes/__init__.py         # registo do router
├── helpers.py                 # engata dispatch_push em create_notification/notify_*
├── models.py                  # PushSubscriptionRequest
├── database.py                # coleção push_subscriptions + índices
└── tests/test_push_routes.py  # NOVO — unit tests

frontend/
├── public/sw.js               # handlers push + notificationclick (cache v5)
├── src/utils/push.js          # NOVO — subscribe/unsubscribe + deteção iOS
├── src/utils/api.js           # pushAPI
├── src/components/PushPrefs.js # NOVO — toggle no Perfil
└── src/pages/private/PerfilPage.js # render do toggle

scripts/generate_vapid_keys.py  # NOVO — gera o par VAPID
```

**Structure Decision**: Web app (backend + frontend já existentes). O push
assenta no PWA atual; nenhuma nova app/serviço — apenas um módulo backend
(`push_service.py`), um router, e peças frontend mínimas.

## Complexity Tracking

> Sem violações da constituição — secção não aplicável.
