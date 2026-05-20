# Tarefa Ativa — Auto-registo de Sócios com Aprovação do Admin

Branch: `feat/auto-registo-socios`
Spec: `tasks/spec-auto-registo.md` (marcada "Pronto para implementar").

## Plano (itens verificáveis)

### Fase 1 — Backend: models + status + schema
- [x] `models.py`: `USER_STATUSES` += `pendente_aprovacao`, `rejeitado`.
- [x] `models.py`: `CARGOS_DECLARADOS`, `RegistrationRequest`, `RegistrationApprove`, `RegistrationReject`.
- [x] `database.py`: índice parcial `ix_users_status_registration` + `CREATE SEQUENCE member_id_seq` em `ensure_schema()`.
- [x] `database.py`: helper `next_member_id()` (raw SQL aqui, não nas rotas) → `ACCTA-{n:04d}`.

### Fase 2 — Email
- [x] `email_service.py`: `registration_rejected_email_html` + `send_registration_rejected_email`.

### Fase 3 — Rotas
- [x] `auth_routes.py`: `POST /register` (público, `3/hour`, honeypot, consent, anti-enumeração, member_id sequencial, notify_admins, audit).
- [x] `auth_routes.py`: `GET /registration-options` (público, devolve `CARGOS_DECLARADOS`).
- [x] `admin.py`: `GET /registration-requests`, `POST .../{id}/approve`, `POST .../{id}/reject`.

### Fase 4 — Testes backend
- [x] `tests/test_auto_registo.py` — 17/17: duplicado (3 variantes), consent=False, honeypot, cargo inválido, approve→invite+role+cargo, reject→status+email, RBAC.

### Fase 5 — Frontend
- [x] `CriarContaPage.js` + rota `/criar-conta` (PublicLayout) em `App.js`.
- [x] `LoginPage.js`: link "Ainda não é sócio? Criar conta".
- [x] `AdminPedidosInscricaoPage.js` + rota `/admin/pedidos-inscricao` + badge no `PrivateLayout` (query só-admin).
- [x] `utils/api.js`: `registrationAPI` + `/criar-conta` na allowlist do interceptor 401.
- [x] `utils/authSchemas.js`: `registrationSchema` (zod) + testes em `__tests__/authSchemas.test.js`.
- [x] `lib/queryClient.js`: `queryKeys.registration.requests`.

### Fase 6 — Verificação
- [x] `ruff check` limpo nos ficheiros alterados; suite unit backend **405 passed** (0 fail; único erro = `test_activity_feed.py` pré-existente/ambiental).
- [x] `eslint` 0 erros (1 warning pré-existente: `ACCTALogoHorizontal`); frontend `authSchemas` 18/18.
- [x] `npx craco build` — **compilado com sucesso** (chunks lazy de CriarConta + AdminPedidosInscricao gerados). Nota: dep pré-existente `@vercel/speed-insights` não estava instalada neste ambiente (igual na main) — instalada localmente sem tocar em package.json/yarn.lock.

## Notas / decisões
- `member_id` atribuído pelo servidor via sequence, formato `ACCTA-0001`, imutável.
- Aprovar gera invite (reusa `SetupAccount`), NÃO ativa diretamente.
- `role` sempre `socio` no submit; admin escolhe role final ao aprovar.
- Bootstrap de `member_id_seq` em produção (setval p/ MAX existente) = passo
  manual de deploy documentado, NÃO executado aqui (sem acesso ao VPS/DB).
