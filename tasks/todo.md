# TODO — Voz e Participação do Sócio (spec-voz-participacao-socio.md)

Plano faseado da §11. PRs pequenos `feature/* → develop` (GitFlow).

| Fase | Funcionalidade | Estado |
|------|----------------|--------|
| F0 | Transversais (`member_category`, helpers de órgão, `is_voting_member`, `count_voting_members`, schema das 7 colecções, router registado) | ✅ #87 |
| F1 | 1.1 Patrocínio de admissão (Art. 8.3) | ✅ #87 |
| F2 | 1.3 Petição para AG extraordinária (Art. 9.f/19.2.d) | ✅ #88 |
| F3 | 1.6 Esclarecimentos + 1.5 Reclamações (Art. 9.j/9.i) | ✅ #89 |
| **F4** | **1.4 Propostas/temas para a ordem de trabalhos (Art. 9.g/9.h)** | ✅ **branch `feature/participacao-f4`** |
| F5 | 1.2 Honorários (nomeação + votação 2/3 via poll; categoria) | ⬜ próximo |
| F6 | Reconciliação com `Assembleia` (encaixes §2.4) | ⬜ depende da governança |

## F4 — Propostas para a ordem de trabalhos (esta entrega)

Schema (`propostas_ag` + índices) já existia desde F0; faltava models + rota + frontend + testes.

### Backend
- [x] `models.py`: `PropostaAG` (status submetida/em_triagem/aceite/recusada/incluida/arquivada), `PropostaAGCreate`, `PropostaTriagem`, `PropostaIncluir`.
- [x] `routes/participacao.py`: `POST /propostas-ag` (membro; notifica Mesa+Direcção), `GET /propostas-ag` (autor vê próprias+aceites/incluídas; triagem vê todas + filtro `status`), `GET /propostas-ag/{id}` (403 a terceiros sem ser pública), `POST .../triagem` (Mesa/Direcção/admin → aceite/recusada+motivo, notifica autor), `POST .../incluir` (Mesa/admin → incluida + assembleia_id/ordem_index).
- [x] Audit: `proposta_submetida`, `proposta_triada`, `proposta_incluida`.

### Frontend
- [x] `api.js`: `propostasAgAPI = { list, get, create, triar, incluir }`.
- [x] `App.js`: lazy `PropostasPage` + rota `/participacao/propostas`.
- [x] `PrivateLayout.js`: item de sidebar "Propostas" (ícone Lightbulb) + título.
- [x] `PropostasPage.js`: lista + submissão (dialog) + triagem (Aceitar/Recusar+motivo) + incluir na OT; filtro por estado para triagem; design neutral-led (único primário = "Nova proposta").

### Testes & verificação
- [x] `tests/test_participacao.py` — `TestProposta` (8 casos: criar+notifica ambos órgãos, visibilidade membro vs triagem, 403 terceiro, triagem exige cargo, triagem aceite notifica autor, incluir exige Mesa/admin).
- [x] `pytest tests/test_participacao.py` → 31 passed.
- [x] `pytest -m unit` → 630 passed, 2 failed (pré-existentes em `test_users_routes` — regex search, não relacionadas).
- [x] `ruff check` ✓ backend.
- [x] `eslint` ✓ (PropostasPage, App, PrivateLayout, api) — 0 erros.
- [x] `craco build` ✓ (build de produção compila).
- [ ] Verificação manual no browser (golden path) — pendente do dono.

## Review (F4)
- Padrão 1:1 com F1–F3: módulo único `participacao.py`, colecção dedicada, RBAC explícito, audit em toda a escrita, notificação ao destinatário.
- RBAC: submeter = qualquer membro autenticado (consistente com reclamações/esclarecimentos); triar = Mesa AG/Direcção/admin; incluir = Mesa/admin (§6.2/§6.3).
- Visibilidade: membro vê as suas + as aceites/incluídas; triagem vê todas (filtro por estado).
- Integração futura: `assembleia_id`/`ordem_index` preenchidos na inclusão (encaixe §2.4, manual até existir o módulo Assembleia).
- Sem migração destrutiva (campos jsonb; schema/índices idempotentes já em F0).
