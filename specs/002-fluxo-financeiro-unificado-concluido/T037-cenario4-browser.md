# T037 — Cenário 4 (UI / browser) — checklist de validação

Os Cenários 1–3 do `quickstart.md` estão **automatizados e verdes** em
`backend/tests/test_fluxo_financeiro_unificado_quickstart.py` (validação
executável ponta-a-ponta, sem servidor/DB). Falta o **Cenário 4 (US4)**, que é
UI e exige browser com a app a correr — segue o checklist abaixo.

## Pré-requisitos
- Backend: `cd backend && uvicorn server:app --reload --port 8001` (Postgres acessível).
- Frontend: `cd frontend && yarn start` (proxy mesma-origem via `setupProxy.js`).
- Login com conta `admin` ou `financeiro`.
- Ter um exercício do ano com transações registadas.

## Passos
1. Abrir **Finanças → Prestação de Contas** no browser.
2. Confirmar a secção **"Relatórios gerados pelo sistema"** com downloads:
   DRE, balancete, **Relatório e Contas anual**, fluxo de caixa.
3. Confirmar que o **upload** está numa zona rotulada **"anexos (opcional)"** —
   não é obrigatório para submeter.
4. Submeter o Relatório e Contas **sem** anexo → sucesso (estado avança).

## Critérios de aceitação (Princípio VII / Princípio V)
- [ ] Secção "Relatórios gerados pelo sistema" visível com os downloads.
- [ ] Upload claramente rotulado como **anexo opcional** (não bloqueia a submissão).
- [ ] **Design `frontend-design`**: download = botão **neutro**; nenhum Carmesim
  como primário positivo; sem vermelho sobre fundo escuro/colorido; sem dark mode.
- [ ] **Screenshot** da página Prestação de Contas (relatórios gerados + zona de
  anexo opcional) anexado ao registo da tarefa.

## Estado
- **Cenários 1–3: FEITOS e verdes** — `test_fluxo_financeiro_unificado_quickstart.py`
  (`3 passed`): C1 despesa de projeto no caixa + spent/orçamento-execução, C2 gate
  Art. 54 + Ato↔projeto + guarda de delete (ato_id), C3 Relatório e Contas em PDF +
  submissão sem upload com `dre_snapshot` congelado.
- **Cenário 4 (UI): browser-verificado na implementação, sem screenshot novo** —
  US4 (a UX da Prestação de Contas) foi verificada no browser durante a
  implementação original da spec (registo da feature), e a feature está **em prod
  (v0.5.27)**. **Fechado por decisão do dono (2026-06-22)** sem recapturar
  artefacto. Ressalva registada: para paridade total com o Princípio VII, reexecutar
  com a app a correr e anexar o screenshot quando conveniente.

## Notas
- Componentes: `frontend/src/.../PrestacaoContasTab` (+ `BudgetTab`); endpoints
  `GET /api/exercicios/{ano}/relatorio/pdf`, `POST /api/exercicios/{ano}/relatorio`.
