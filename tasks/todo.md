# Todo — Remover patrocínio de admissão (Art. 8.3)

Decisão do dono: **remover a funcionalidade inteira**; **manter** aprovação do admin
(só cai o gate dos 2 padrinhos). Coleção `patrocinios` + dados ficam em DB (sem drop).

## Backend
- [ ] `routes/auth_routes.py` — remover validação de padrinhos + criação de patrocinios + notify padrinhos no `register`; limpar imports (`Patrocinio`, `is_voting_member`, `notify_users`)
- [ ] `routes/admin.py` — remover gate `confirmados < 2` + `waive_sponsorship` + resumo `sponsors`/`confirmed_count` na listagem
- [ ] `routes/participacao.py` — remover endpoints `/patrocinios/*` + import `PatrocinioRespond`
- [ ] `models.py` — remover `sponsors` (RegistrationRequest), `waive_sponsorship` (RegistrationApprove), classes `Patrocinio` + `PatrocinioRespond`
- [ ] `database.py` — SEM alteração (coleção/índices/dados ficam)

## Frontend
- [ ] `pages/public/CriarContaPage.js` — remover bloco padrinhos + sponsors no submit
- [ ] `utils/authSchemas.js` — remover sponsor1/sponsor2 + refine
- [ ] `utils/api.js` — remover `patrociniosAPI`
- [ ] `App.js` — remover import + rota `/participacao/patrocinios`
- [ ] `layouts/PrivateLayout.js` — remover item nav + breadcrumb + import `Handshake`
- [ ] `pages/private/PatrociniosPage.js` — APAGAR
- [ ] `pages/private/AdminPedidosInscricaoPage.js` — remover coluna Patrocínios + gate + waive
- [ ] `content/ajuda/governanca.js` — remover menções a patrocínios

## Tests
- [ ] `tests/test_participacao.py` — remover bloco patrocínio (fixture `env`, `_req`, classes, import)
- [ ] `tests/test_auto_registo.py` — reescrever testes que dependem de padrinhos/gate/waive
- [ ] `utils/__tests__/authSchemas.test.js` — remover asserts de sponsor
- [ ] `content/ajuda/__tests__/integrity.test.js` — tirar `/participacao/patrocinios` de ROTAS_VALIDAS

## Verificação
- [x] `ruff check` (6 ficheiros) — All checks passed
- [x] `pytest tests/test_auto_registo.py tests/test_participacao.py` — 67 passed
- [x] eslint (7 ficheiros alterados) — limpo
- [x] jest authSchemas + ajuda integrity — 27 passed

## Review
Todos os itens acima feitos. Funcionalidade Art. 8.3 removida ponta-a-ponta
(registo, validação, gate de aprovação, página/endpoints, nav, ajuda).
Aprovação do admin mantida (sem o gate dos 2 padrinhos). `database.py` intacto
— coleção `patrocinios` + índices + dados ficam em DB (dormentes, sem drop).
Hits remanescentes só em `tasks/spec-voz-participacao-socio-concluido.md`
(registo histórico) e `.understand-anything/` (artefactos gerados) — não-código.
Não commitei (aguarda decisão do dono sobre branch/PR).
