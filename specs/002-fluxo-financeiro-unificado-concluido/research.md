# Research & Decisions: Fluxo Financeiro Unificado

Consolidação das decisões técnicas. Todas as ambiguidades materiais foram fechadas no brainstorming; este documento regista o porquê e as alternativas rejeitadas, ancorado no código atual.

## Decisão 1 — Modelo unificado: despesa de projeto = transação com `project_id`

**Decisão**: Adicionar `project_id: Optional[str] = None` ao modelo `Transaction` (`models.py:1232`). Uma despesa de projeto passa a ser uma `Transaction type="despesa"` com `project_id` preenchido. A coleção `project_expenses` deixa de ser escrita (fica legível como legado até à migração; depois irrelevante — FR-014).

**Rationale**: Fonte única de verdade elimina por construção a dessincronização entre `project.spent` e o caixa. As agregações financeiras (`compute_financial_summary` em `finances.py:282`, `compute_dre_report` em `finances.py:360`) varrem `transactions` sem filtro de origem — logo as despesas de projeto entram **automaticamente** no resumo/DRE/balancete/CSV assim que forem transações, sem tocar nessas funções (satisfaz FR-008 a custo zero).

**Alternativas rejeitadas**:
- *Espelho automático* (manter `project_expenses` + criar transação espelhada): dois escritos a manter atómicos, risco de divergência se um falhar. Mais código, contra Princípio I.
- *Ação manual "lançar ao caixa"*: mantém fricção e um estado intermédio; o dono escolheu o modelo unificado no brainstorming.

**Campo aditivo-opcional** ⇒ não quebra documentos existentes (`Transaction` tem `model_config = ConfigDict(extra="ignore")`). Não é STOP condition #5.

## Decisão 2 — `project.spent` derivado por agregação

**Decisão**: `spent` deixa de ser um contador escrito (`projects.py:553`) e passa a derivar de:
```
aggregate([{ $match: { project_id, type: "despesa" } }, { $group: { _id: null, total: { $sum: "$amount" } } }])
```
sobre `transactions`. Na **listagem** de projetos, uma única agregação `{$match:{type:"despesa", project_id:{$ne:null}}}, {$group:{_id:"$project_id", total:{$sum:"$amount"}}}` devolve o spent de todos os projetos de uma vez (evita N+1).

**Rationale**: O campo `Project.spent` (`models.py:1400`) mantém-se no modelo por compatibilidade, mas é recomputado/preenchido a partir das transações na leitura, não autoritativo. Orçado vs. Realizado por projeto = `budget` (previsão, inalterado) vs. `spent` (agregado) — satisfaz FR-002/FR-004.

**Alternativa rejeitada**: manter `spent` denormalizado e atualizá-lo em cada escrita de transação com `project_id` — reintroduz a classe de bug que estamos a eliminar (divergência). O DAO já suporta `$group`/`$sum` (ver `.claude/rules/database.md`).

## Decisão 3 — Gate de co-aprovação (Art. 54) nas despesas de projeto

**Decisão**: `POST /projects/{id}/expenses` passa a aplicar o mesmo gate de `finances.create_transaction` (`finances.py:172-181`): se `amount > coaprovacao_limiar` (lido por `_coaprovacao_limiar()`), recusa com 400 e mensagem PT a orientar para criar um Ato de pagamento, identificando o projeto. Reutiliza-se o helper `_coaprovacao_limiar` (exportá-lo/partilhá-lo ou replicar a leitura defensiva).

**Rationale**: Fecha o atalho atual (despesa de projeto de qualquer valor sem dupla assinatura). Coerência com FR-006. O limiar a 0 mantém o comportamento direto (não-quebra).

**Alternativas rejeitadas**: "permitir mas marcar pendente de Ato" (estado intermédio extra) e "isentar" (mantém o buraco) — o dono escolheu o mesmo gate no brainstorming.

## Decisão 4 — Execução de Ato propaga `project_id`

**Decisão**: Adicionar `project_id: Optional[str]` a `Ato` (`models.py:1349`) e a `AtoCreate` (`models.py:1325`). `execute_ato` (`atos.py:219-228`) copia `ato.get("project_id")` para a `Transaction` criada. Quando uma despesa de projeto excede o limiar, o fluxo de criação do Ato é iniciado com `project_id` pré-preenchido (frontend) — ao executar, a despesa fica ligada a Ato **e** projeto (FR-007).

**Rationale**: Mantém o rasto de co-aprovação e a contagem para o `spent` do projeto. Campos aditivos-opcionais, não quebram Atos existentes.

## Decisão 5 — Permissão para registar despesa de projeto (RESOLVIDA pelo dono, 2026-06-20)

**Decisão (confirmada pelo dono)**: Manter `can_manage_project` como guard de `POST/DELETE /projects/{id}/expenses` (responsável/gestor do projeto), **adicionando `create_audit_log`** (hoje ausente em `add_expense`/`delete_expense`).

**Rationale**: Quem executa o projeto é quem conhece e regista o gasto; impor `manage_finances` criaria fricção. Os valores grandes já passam pelo gate Art. 54 (Direção + Tesoureiro), por isso o risco de um gestor de projeto escrever no livro-caixa está limitado a montantes abaixo do limiar e fica auditado. Cumpre Princípio III (audit em escrita).

**Alternativa**: exigir `manage_finances` para qualquer despesa de projeto — mais restritivo, rejeitado por fricção sem ganho proporcional. **Sinalizado ao dono no relatório de conclusão** para veto antes da implementação.

## Decisão 6 — Remoção de despesa e Atos

**Decisão**: `DELETE /projects/{id}/expenses/{expense_id}` passa a apagar a **transação** correspondente (`project_id` = projeto, `id` = expense_id). Se a transação tiver `ato_id` (originada por Ato executado), a remoção pela via de despesa de projeto é **recusada** (mantém o rasto do Ato) — a reversão segue as regras do Ato. Audit log em ambos os casos.

**Rationale**: FR-010 + edge case "apagar despesa criada via Ato". Evita quebrar a invariante do Ato executado.

## Decisão 7 — Filtro `project_id` em `GET /finances/transactions`

**Decisão**: Adicionar parâmetro opcional `project_id` a `list_transactions` (`finances.py:74`), traduzido para `query["project_id"]`. Índice de expressão em `transactions(doc->>'project_id')` em `ensure_schema()`.

**Rationale**: FR-009. O DAO suporta filtro por igualdade; índice mantém a listagem rápida.

## Decisão 8 — Categoria na despesa de projeto

**Decisão**: Adicionar `category: Optional[str] = None` a `ProjectExpenseCreate` (`models.py:1503`). Validar contra `EXPENSE_CATEGORIES`; default `operacional` se omisso (FR-005). `ProjectExpenseCreate` mantém `description`/`amount`/`date`.

**Rationale**: Uma transação exige categoria válida. `operacional` é o default neutro (mesmo default de `execute_ato`, `atos.py:214`).

## Decisão 9 — Gerador do Relatório e Contas anual (PDF)

**Decisão**: Novo endpoint `GET /exercicios/{ano}/relatorio/pdf` (em `prestacao_contas.py` ou `finances.py`) que monta um PDF completo: capa + DRE (reutiliza a lógica de `finances.py:727-956`, hoje `GET /finances/dre/pdf`) + balancete anual (snapshot de `compute_financial_summary(year=ano)`) + orçado vs. realizado (já existe `GET /exercicios/{ano}/orcamento/execucao`) + folha de assinaturas (cargos da Direção/CF via `governance.py`/`permissions.py`). Gerado on-the-fly, sem assinatura digital ("Documento gerado automaticamente pelo Portal ACCTA").

**Rationale**: FR-015/FR-019. Reaproveita o gerador FPDF existente; números derivam exclusivamente das transações ⇒ coincidem com o resumo (SC-006).

**Alternativa rejeitada**: parsear o PDF subido pelo utilizador — o sistema já ignora o conteúdo do upload; a fonte de verdade são as transações.

## Decisão 10 — Submissão do relatório sem upload obrigatório

**Decisão**: Tornar `RelatorioContasSubmit.document_id` `Optional[str] = None` (`models.py:2336`). Em `submeter_relatorio` (`prestacao_contas.py:353`), chamar `_validate_document`/`_publish_document` só quando `document_id` for fornecido (espelha o padrão já usado em orçamento/plano, `prestacao_contas.py:394`,`425`). O `dre_snapshot` continua congelado (`compute_dre_report(ano)`), preservando auditabilidade (FR-016).

**Rationale**: O upload passa a anexo opcional (FR-017). Campo opcional ⇒ não quebra chamadas existentes que enviem `document_id`. Não remove a rota.

## Decisão 11 — Estratégia de migração (STOP condition)

**Decisão**: Script `scripts/migrate_project_expenses_to_transactions.py`:
1. **dry-run (default)**: lê todas as `project_expenses`, mapeia para transações candidatas (`type="despesa"`, `project_id`, `category="operacional"`, preservando `description`/`amount`/`date`/`created_by`), e produz um **relatório de reconciliação** que sinaliza **possíveis duplicados** — transações `despesa` já existentes sem `project_id` com o mesmo `amount` e data próxima (±janela) e/ou descrição semelhante. Imprime contagens e a lista de suspeitos. Não escreve nada.
2. **`--apply`** (só após confirmação explícita do dono): insere as transações; opcionalmente marca as `project_expenses` migradas (`migrated_to_transaction_id`) para idempotência/rasto. Idempotente: re-correr não duplica (verifica marca/transação existente).

**Rationale**: FR-012/FR-013/SC-007. Princípio VI (STOP #1: migrar dados). DB dev quase vazia ⇒ revisão tratável. Padrão alinhado com `scripts/migrate_income_categories.py` existente.

## Decisão 12 — Índices e schema

**Decisão**: Em `ensure_schema()` (`database.py`), adicionar índice de expressão em `transactions(doc->>'project_id')`. `project_expenses` mantém a tabela (sem novos índices). Nenhuma tabela é dropada (não-destrutivo no schema; a migração só insere/marca).

**Rationale**: Performance do filtro por projeto e da agregação de `spent`. Princípio III (índices só em `ensure_schema`).
