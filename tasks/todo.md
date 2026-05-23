# TODO — Finanças Cat 4.3: Jóia de admissão (Art. 6)

Spec `spec-controlos-financeiros` §6 (Feature 4.3). Empilhado sobre a fundação F0
(`feature/financas-fundacao-categorias`, PR #105). Branch `feature/financas-joia`.

Decisões do dono (gates §12 confirmados 2026-05-23):
- **§12.6** Honorário **isento** de jóia (a par de fundador + `joia_isento`).
- **§12.7** Cobrança **manual** pelo Tesoureiro (admissão só ASSINALA `joia_devida`).

## Backend
- [x] `finance_joia.py`: `joia_status`/`compute_joia`/`_qualified_more_than_months`
      (puro; jóia = `joia_amount` ou `joia_multiplier`×`quota_amount`; >4 meses estrito;
      isentos: fundador/honorário/`joia_isento`/sem `cta_qualified_since`)
- [x] `models.py`: `cta_qualified_since` em `RegistrationApprove` + `InviteCreate` (validação de data, sem futuro)
- [x] `routes/admin.py`: hook em `approve_registration` (assinala `joia_devida` + audit `joia_calculada`)
      e `invite_user` (assinala `joia_devida`); fetch de settings defensivo (`isinstance dict` → defaults)
- [x] `routes/finances.py`: `GET /finances/joia/preview?user_id=&cta_qualified_since=` (require_view_finances)

## Frontend
- [x] `api.js`: `financesAPI.getJoiaPreview(userId, ctaSince)`
- [x] `queryClient.js`: `registration.joiaPreview` key
- [x] `AdminPedidosInscricaoPage`: campo "Qualificado como CTA desde" + nota de jóia (via preview)
      no modal de aprovação; envia `cta_qualified_since` no payload

## Testes & gates
- [x] `tests/test_joia.py` (24 casos): lógica pura (qualificação, isenções incl. honorário,
      `joia_amount` sobrepõe, exatamente-4-meses não conta) + endpoint preview (403/404/override/default)
- [x] `pytest -m unit` → **728 passed, 0 failed** (auto-registo/admin não regridem)
- [x] `ruff check`/`format` ✓ · `eslint` (meus ficheiros) ✓ · `craco build` ✓

## Review
- **Cobrança manual** respeitada: a admissão só grava `joia_devida` (não cria `Transaction`).
  O Tesoureiro lança a receita via o fluxo normal (`category="joias"`, agora válida desde a fundação).
- **Fonte única da regra**: `finance_joia.py` (sem DB) usado por preview E pelos dois hooks → sem drift.
- **Não-regressivo**: fetch de settings tolera `mock_db` (find_one→None) e ausência de settings;
  audit `joia_calculada` só dispara quando há jóia → testes de auto-registo intactos.
- **STOP respeitado**: `approve_registration` já enviava email (pré-existente); o hook é aditivo,
  não envia emails novos nem toca `quota_amount`/`joia_multiplier` (esses exigem deliberação AG §14).

## Fora de escopo (fases seguintes)
- Cat 3 (regulamentos/balancetes/exercício) · Cat 4.1 atos/dupla-assinatura · Cat 5 venda
- Hook da jóia no convite tem backend pronto, mas o formulário de convite (frontend) ainda não
  expõe `cta_qualified_since` — adicionar quando se mexer nesse form
