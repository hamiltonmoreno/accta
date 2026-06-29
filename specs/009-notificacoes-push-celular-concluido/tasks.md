# Tasks: Notificações Push no Celular (Web Push / PWA)

**Feature**: 009-notificacoes-push-celular | **Branch**: `claude/mobile-push-notifications-i2qx2k` (merged → `develop`, PR #362)

**Input**: Design documents from `specs/009-notificacoes-push-celular/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/push-api.md, quickstart.md

**Nota**: Documentação retroativa — a funcionalidade já está implementada e merged em `develop`. Os itens estão marcados como concluídos (`[X]`) e mapeiam os ficheiros reais. Restam apenas os T-residuais de validação manual pós-deploy (Princípio VII) e os passos operacionais de release/envs.

**Tests**: A spec não pediu TDD; foi escrito um ficheiro de testes unitários (US1/US2 + segurança). Incluídos como tarefas reais.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode correr em paralelo (ficheiro diferente, sem dependências por concluir)
- **[Story]**: Mapeia para a user story (US1/US2/US3)

---

## Phase 1: Setup (infra partilhada)

- [X] T001 Adicionar dependência `pywebpush==2.0.0` em `backend/requirements.txt`
- [X] T002 [P] Criar `scripts/generate_vapid_keys.py` (gera par VAPID base64url; round-trip verificado com `py_vapid`)
- [X] T003 [P] Documentar envs `VAPID_PUBLIC_KEY`/`VAPID_PRIVATE_KEY`/`VAPID_SUBJECT` e a degradação graciosa em `CLAUDE.md`

**Checkpoint**: Dependência e gerador de chaves disponíveis; envs documentadas.

---

## Phase 2: Foundational (bloqueia todas as user stories)

- [X] T004 Adicionar coleção `push_subscriptions` a `COLLECTIONS` em `backend/database.py`
- [X] T005 Adicionar índices `ix_push_user` (`user_id`) e `ux_push_endpoint` UNIQUE (`endpoint`) em `ensure_schema()` de `backend/database.py`
- [X] T006 Adicionar modelos `PushSubscriptionKeys` e `PushSubscriptionRequest` (`extra="ignore"`) em `backend/models.py`
- [X] T007 Criar `backend/push_service.py`: `push_enabled()`, `is_safe_push_endpoint()` (anti-SSRF: HTTPS + host público, rejeita localhost/`.local`/`.internal`/IPs privados/loopback/link-local/reservados) e leitura lazy das envs VAPID
- [X] T008 Implementar `dispatch_push(user_ids, title, body, link)` em `backend/push_service.py`: no-op sem VAPID, query única `{$in: ids}`, envio via `asyncio.to_thread` (`pywebpush` lazy), best-effort, poda 404/410
- [X] T009 Registar `push_router` em `backend/routes/__init__.py`

**Checkpoint**: Esquema, modelo e motor de envio prontos — endpoints e UI podem assentar aqui.

---

## Phase 3: User Story 1 — Receber avisos no celular com a app fechada (P1) 🎯 MVP

**Goal**: Cada notificação interna criada para um sócio é espelhada como Web Push na bandeja do SO, mesmo com a app fechada; tocar abre/foca a página associada.

**Independent Test**: Com a feature ativada, gerar uma notificação (ex.: comunicado) e confirmar que aparece na bandeja com a app fechada e que o toque abre o `url`.

- [X] T010 [US1] Engatar `dispatch_push` em `create_notification`, `notify_users` e `notify_all_active_users` em `backend/helpers.py` (pontos únicos; `notify_admins` herda via `notify_users`)
- [X] T011 [US1] Handler `push` no service worker `frontend/public/sw.js` — parse JSON `{title, body, url}`, `showNotification` com `icon`/`badge`/`data.url`; `tag` só quando o backend o envia (sem colapsar avisos distintos)
- [X] T012 [US1] Handler `notificationclick` em `frontend/public/sw.js` — foca janela aberta (navega para `url`) ou abre nova; bump da cache para `accta-wallet-v5`

**Checkpoint**: Notificações chegam ao dispositivo com a app fechada e o clique navega — US1 entregável de forma independente.

---

## Phase 4: User Story 2 — Ativar/desativar por dispositivo no Perfil (P1)

**Goal**: O sócio liga/desliga o push por dispositivo, com consentimento explícito do navegador, num toggle no Perfil ao lado das preferências de email.

**Independent Test**: No Perfil, ligar o interruptor, conceder permissão, confirmar estado "ligado"; desligar e confirmar que deixa de receber.

- [X] T013 [US2] Endpoint `GET /api/push/vapid-public-key` (autenticado; 503 sem config) em `backend/routes/push.py`
- [X] T014 [US2] Endpoint `POST /api/push/subscribe` (upsert por endpoint, anti-SSRF antes de gravar, 503/400) em `backend/routes/push.py`
- [X] T015 [US2] Endpoint `POST /api/push/unsubscribe` (apaga só a do próprio: filtro `user_id`+`endpoint`; idempotente) em `backend/routes/push.py`
- [X] T016 [US2] Endpoint `POST /api/push/test` (envia push ao próprio; 400 sem dispositivos) em `backend/routes/push.py`
- [X] T017 [P] [US2] Grupo `pushAPI` (getVapidKey/subscribe/unsubscribe/test) em `frontend/src/utils/api.js`
- [X] T018 [US2] `frontend/src/utils/push.js` — `isPushSupported`, `getExistingSubscription`, `subscribeToPush` (pede permissão → `urlBase64ToUint8Array` da chave VAPID → `pushManager.subscribe` → POST ao backend), `unsubscribeFromPush`
- [X] T019 [US2] Componente `frontend/src/components/PushPrefs.js` — toggle `Switch` (`card-technical`, neutro-led), estados busy/ready, toasts de sucesso/erro
- [X] T020 [US2] Renderizar `<PushPrefs />` ao lado de `EmailPrefs` em `frontend/src/pages/private/PerfilPage.js`

**Checkpoint**: Opt-in por dispositivo funcional ponta-a-ponta; US1+US2 = produto utilizável.

---

## Phase 5: User Story 3 — Orientação no iPhone antes de instalar o PWA (P2)

**Goal**: Em iPhone/Safari antes de instalar o PWA, mostrar instrução "Adicionar à Tela de Início" em vez de um interruptor inoperante.

**Independent Test**: Abrir o portal num iPhone via Safari (sem PWA) e confirmar que aparece a instrução em vez do interruptor.

- [X] T021 [US3] `getIosNeedsInstall()` em `frontend/src/utils/push.js` — deteta iOS/iPadOS (incl. `MacIntel`+touch) fora do `standalone`, independente de `isPushSupported()`
- [X] T022 [US3] Ramo de instrução iOS em `frontend/src/components/PushPrefs.js` — render quando `iosNeedsInstall`; `return null` só quando `!supported && !iosNeedsInstall`

**Checkpoint**: Utilizadores iPhone recebem orientação acionável em vez de um controlo quebrado.

---

## Phase 6: Polish & Cross-Cutting

- [X] T023 [P] Testes unitários `backend/tests/test_push_routes.py` — subscribe insert/update, unsubscribe scoping, vapid 503/200, test 400/200, `dispatch_push` no-op + poda 410, matriz `is_safe_push_endpoint` (10 testes; liga `push_subscriptions` no mock e injeta `pywebpush` falso)
- [X] T024 [P] `ruff check .` limpo em `push_service.py`/`routes/push.py`/`tests/test_push_routes.py`
- [X] T025 [P] Atualizar bloco SPECKIT em `CLAUDE.md` (feature ativa 009)
- [X] T026 [US2] **Operador**: VAPID gerado e definido em prod (2026-06-28) — chaves geradas no container, gravadas em `/docker/accta/.env`; `push_enabled()`=True no processo vivo. NÃO regenerar (parte subscrições)
- [X] T027 **Release**: `develop→main` via **Via B** feito (release #364, tag v0.5.40, imagem `sha-fae22c0eaab2`, Up healthy; rollback `sha-5cfff3c9b0e1`)
- [ ] T028 [US1] **Validação manual pós-deploy** (Princípio VII, quickstart Cenário 1): Android com app fechada → `POST /api/push/test` → confirmar aviso na bandeja + clique abre `/carteira`
- [ ] T029 [US3] **Validação manual pós-deploy** (quickstart Cenário 4): iPhone com PWA na Tela de Início → ativar e receber; sem PWA → ver a instrução

---

## Dependencies & Execution Order

- **Setup (Phase 1)** → **Foundational (Phase 2)** bloqueiam tudo.
- **US1 (Phase 3)** depende de T008 (`dispatch_push`) e T010 (engate nos helpers); é o MVP.
- **US2 (Phase 4)** depende de Foundational; entrega o opt-in (porta de entrada para US1 na prática).
- **US3 (Phase 5)** depende de peças do frontend de US2 (`push.js`/`PushPrefs.js`) mas é incremento isolado.
- **Polish (Phase 6)**: T023–T025 já feitos; T026–T029 são operador/release/validação manual e ficam para o pós-merge.

## Parallel Opportunities

- Setup: T002, T003 em paralelo.
- Foundational: T004/T005 (database) sequenciais entre si; T006 (models) e T007 (push_service) em paralelo com a database.
- US2: T017 (api.js) em paralelo com os endpoints backend T013–T016.
- Polish: T023, T024, T025 em paralelo.

## Implementation Strategy

**MVP = US1 + US2** (ambos P1): sem o opt-in (US2) ninguém recebe push, e sem a entrega com app fechada (US1) não há "push no celular". US3 (P2) é refinamento de adoção iOS. Entrega incremental por fase, cada uma testável de forma independente.
