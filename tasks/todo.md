# TODO — Voz e Participação do Sócio (spec-voz-participacao-socio.md)

Plano faseado da §11. PRs pequenos `feature/* → develop` (GitFlow).

| Fase | Funcionalidade | Estado |
|------|----------------|--------|
| F0 | Transversais (`member_category`, helpers de órgão, `is_voting_member`, `count_voting_members`, schema das 7 colecções, router registado) | ✅ #87 |
| F1 | 1.1 Patrocínio de admissão (Art. 8.3) | ✅ #87 |
| F2 | 1.3 Petição para AG extraordinária (Art. 9.f/19.2.d) | ✅ #88 |
| F3 | 1.6 Esclarecimentos + 1.5 Reclamações (Art. 9.j/9.i) | ✅ #89 |
| F4 | 1.4 Propostas/temas para a ordem de trabalhos (Art. 9.g/9.h) | ✅ #91 (merged em develop) |
| **F5** | **1.2 Honorários (nomeação + votação 2/3 via poll; categoria)** | 🔄 **branch `feature/participacao-f5-honorarios`** |
| F6 | Reconciliação com `Assembleia` (encaixes §2.4) | ⬜ depende da governança |

## F5 — Membros honorários (Art. 8.4) — esta entrega

Decisões do dono (gates §14 confirmados 2026-05-22):
- **Base 2/3** = votos válidos emitidos (`favor + contra`, abstenções fora). `aprovado = favor >= ceil(2/3 * base)`.
- **Honorário externo** = permitido (`nominee_email` → cria `pendente_convite` + convite se eleito).
- **Módulo** = `routes/participacao.py` (interim; migra p/ governança quando o `Assembleia` existir).

Schema (`honorarios_nominations` + índices `status`/`nominee_user_id`) já existia desde F0. A votação reusa `polls`/`user_votes` (sem colecção nova).

### Backend
- [x] `models.py`: `HonorarioNomination` (proposta/em_votacao/eleito/rejeitado) + `HonorarioCreate`.
- [x] `helpers.py`: `voting_member_ids()` (ids dos votantes; `count_voting_members` passa a reusá-lo) — para notificar só votantes na abertura.
- [x] `routes/participacao.py`:
  - `POST /honorarios` (Direcção/admin → cria `proposta`; notifica Mesa).
  - `GET /honorarios` / `GET /honorarios/{id}` (Direcção/Mesa/admin).
  - `POST /honorarios/{id}/abrir-votacao` (Mesa/admin → cria poll `[A favor, Contra, Abstenção]`, `em_votacao`, notifica votantes tipo `poll`).
  - `POST /honorarios/{id}/apurar` (Mesa/admin → fecha poll, 2/3 sobre válidos, `eleito`/`rejeitado`).
  - **Email = identificador universal** em `_aplicar_honorario_eleito`: `nominee_user_id` ou email de sócio existente → eleva (`member_category=honorario`); email de pessoa nova → `pendente_convite` + convite; sem identificador → fica eleito sem conta.
- [x] Audit: `honorario_nomeado`, `honorario_votacao_aberta`, `honorario_apurado`.

### Frontend
- [x] `api.js`: `honorariosAPI = { list, get, create, abrirVotacao, apurar }`.
- [x] `App.js`: lazy `HonorariosPage` + rota `/governanca/honorarios`.
- [x] `PrivateLayout.js`: item de sidebar "Honorários" (ícone Medal) em "Órgãos Sociais", gating `match: 'governanca'` (admin/Direcção/Mesa) + `isMesaAG` no destructure + título da página.
- [x] `HonorariosPage.js`: listar + nomear (dialog: nome + email opcional + justificação) + abrir votação + apurar/ver resultado 2/3; sem permissão → empty state; design neutral-led (único primário = "Nomear honorário"). Sócio vota na página `Votações` existente.

### Testes & verificação
- [x] `tests/test_participacao.py` — `TestHonorario` (15 casos): nomear exige Direcção; nomeado interno inválido 422; abrir/apurar exige Mesa/admin; abrir só de `proposta` (409); abrir cria poll + notifica só votantes (tipo poll); apuramento 2/3 com `ceil` (exacto, just-below, base 0); eleito interno seta categoria; externo cria convite; email de membro existente eleva sem convite.
- [x] `pytest tests/test_participacao.py` → 45 passed.
- [x] `pytest -m unit` → 655 passed, 2 failed (pré-existentes em `test_users_routes` — regex search, não relacionadas).
- [x] `ruff check` + `ruff format` ✓ backend.
- [x] `eslint` ✓ (HonorariosPage, App, PrivateLayout, api) — 0 erros; `craco build` ✓.
- [ ] Verificação manual no browser (golden path) — pendente do dono.

### STOP conditions a respeitar (§13)
- Envio de email real (convite de honorário externo eleito): código implementado, mas o envio dispara só no `apurar` de um nominee externo eleito — validar com inbox de dev (sem sócios reais em produção).
- Nada destrutivo em `users` (categoria é aditiva).

## Review (F5)
- Padrão 1:1 com F1–F4: módulo único `participacao.py`, RBAC explícito, audit em toda a escrita, notificação ao destinatário. Votação reusa `polls`/`user_votes` (sem colecção nova).
- RBAC: nomear = Direcção/admin; abrir/apurar = Mesa AG/admin; votar = `is_voting_member` (já enforced em `routes/polls.py`, exclui honorário/técnico/inactivo/suspenso).
- 2/3 sobre votos válidos (favor+contra), `favor >= ceil(2/3*base)`, `base==0` → rejeitado (decisão do dono).
- Refactor mínimo: `count_voting_members = len(voting_member_ids())` (sem duplicar a query/regra de elegibilidade).
- Elegância: o email como identificador universal evita um seletor de membro (GET /users é admin/financeiro-only, logo inacessível à Direcção role=socio) e cobre interno+externo num só campo.
- Integração futura (§2.4): `assembleia_id`/`deliberacao_id` ficam `None`; migra para `AssembleiaDeliberacao` (`tipo_maioria=qualificada_2_3`) quando o módulo Assembleia existir (F6).
- STOP respeitado: o único email real (convite de honorário externo eleito) dispara só no `apurar` de um nominee externo; sem sócios reais em produção. Nada destrutivo em `users` (categoria aditiva).
