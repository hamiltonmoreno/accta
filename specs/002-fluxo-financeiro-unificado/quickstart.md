# Quickstart / Validação: Fluxo Financeiro Unificado

Guia de validação end-to-end. Detalhes de campos/endpoints em `data-model.md` e `contracts/`.

## Pré-requisitos

- Backend a correr local: `cd backend && uvicorn server:app --reload --port 8001` (DB Postgres acessível).
- Login dev (ver memória `local-dev-run`): `dev@accta.cv`.
- `bcrypt==4.0.1` instalado se venv recriado.
- Testes: `cd backend && pytest` (unit/in-process com `mock_db`; lembrar de pré-ligar `project_expenses`/`transactions` mocks conforme `conftest.py`).

## Cenário 1 — Despesa de projeto entra no caixa (US1)

1. Garantir `coaprovacao_limiar = 0` (ou despesa abaixo do limiar) em `finance_settings`.
2. Criar projeto com `budget=50000`, aprová-lo.
3. `POST /api/projects/{id}/expenses` com `{ "description":"Sala", "amount":5000, "category":"eventos" }`.
4. **Esperado**:
   - `GET /api/finances/transactions?project_id={id}` devolve a despesa.
   - `GET /api/projects/{id}` → `spent=5000`, bloco `orcamento_execucao={budget:50000, realizado:5000, desvio:45000}`.
   - `GET /api/finances/summary` do mês → `total_despesas` aumentou 5000.
   - Existe entrada de audit log da criação.

## Cenário 2 — Gate Art. 54 em despesa de projeto (US2)

1. Definir `coaprovacao_limiar = 50000`.
2. `POST /api/projects/{id}/expenses` com `amount=80000` → **400** com mensagem PT a pedir Ato.
3. `POST /api/atos` `{tipo:"pagamento", valor:80000, project_id:"{id}", descricao:...}`; recolher assinaturas (2 Direção + Presidente + Tesoureiro).
4. `POST /api/atos/{ato}/executar` → cria despesa com `ato_id` **e** `project_id`.
5. **Esperado**: `GET /api/projects/{id}` reflete `spent+=80000`; a transação aparece no caixa com `ato_id` preenchido; `GET /api/finances/transactions?project_id={id}` inclui-a.
6. `DELETE /api/projects/{id}/expenses/{essa_transacao}` → **400** (tem `ato_id`).

## Cenário 3 — Relatório e Contas gerado (US3)

1. Exercício do ano com transações registadas.
2. `GET /api/exercicios/{ano}/relatorio/pdf` → devolve PDF com capa + DRE + balancete + orçado vs. realizado + folha de assinaturas.
3. Conferir que os totais do PDF == `GET /api/finances/summary?year={ano}`.
4. `POST /api/exercicios/{ano}/relatorio` com `{}` (sem `document_id`) → **200**, estado `relatorio_submetido`, `dre_snapshot` congelado.
5. (Opcional) repetir com `document_id` de um anexo → publica o anexo, números inalterados.

## Cenário 4 — UX prestação de contas (US4)

1. Abrir Finanças → Prestação de Contas no browser.
2. **Esperado**: secção "Relatórios gerados pelo sistema" com downloads (DRE, balancete, Relatório e Contas anual, fluxo de caixa); upload numa zona rotulada "anexos (opcional)".
3. Verificar contraste/botões neutros (Princípio V): download = botão neutro; nenhum Carmesim como primário positivo.

## Migração (STOP — só após confirmação do dono)

1. **Dry-run** (default): `python scripts/migrate_project_expenses_to_transactions.py`
   - Imprime: nº de `project_expenses`, nº de transações candidatas, **lista de suspeitos de duplicado** (despesa sem `project_id`, mesmo `amount`, data próxima).
   - Não escreve nada.
2. Rever o relatório com o dono.
3. **Aplicar** (após OK explícito): `python scripts/migrate_project_expenses_to_transactions.py --apply`
   - Insere transações; marca `project_expenses` migradas. Idempotente.
4. **Esperado**: caixa passa a incluir o histórico de despesas de projeto; sem duplicados (SC-007).

## Critério de pronto (Verification — Princípio VII)

- [ ] `pytest` verde para os novos testes (despesas, gate, filtro, submissão sem upload).
- [ ] Cenários 1–3 validados via HTTP.
- [ ] Cenário 4 validado no browser (screenshot).
- [ ] Migração validada em dry-run; `--apply` só após confirmação.
