# Contrato: Finanças (filtro por projeto + relatório anual)

Prefixo: `/api/finances`. Guards existentes: `require_view_finances` (GET), `require_manage_finances` (escrita).

## GET `/finances/transactions` — filtro `project_id` (NOVO param)

Adiciona parâmetro de query opcional `project_id`. Quando presente, `query["project_id"] = project_id`.

```
GET /api/finances/transactions?project_id=proj-123
```

**Response 200** (inalterado na forma): `{ items, total, skip, limit }`, items filtrados pelo projeto.

**Acceptance**: US1 cenário 3.

## Efeito automático (sem endpoint novo)

`compute_financial_summary` (`/finances/summary`), `compute_dre_report` (`/finances/dre`, `/finances/dre/pdf`) e o CSV (`/finances/transactions/csv`) **não mudam**: como as despesas de projeto passam a ser `transactions`, entram nessas agregações automaticamente (FR-008). Verificação: somar despesas de projeto de um período e confirmar que `total_despesas` do `/summary` aumenta nesse montante.

**Acceptance**: US1 cenário 1 (efeito no resumo).

## GET `/exercicios/{ano}/relatorio/pdf` — Relatório e Contas anual gerado (NOVO)

> Localização do router a confirmar na implementação (`prestacao_contas.py` reutilizando o gerador FPDF de `finances.py:727-956`). Guard: `require_view_finances` (ou regra de visibilidade da prestação de contas).

Gera on-the-fly um PDF completo do exercício:
1. **Capa** — identificação ACCTA + ano + data de geração.
2. **DRE** — reutiliza o gerador de `/finances/dre/pdf` (mensal + por categoria + resultado líquido).
3. **Balancete anual** — snapshot de `compute_financial_summary(year=ano)`.
4. **Orçado vs. Realizado** — reutiliza `GET /exercicios/{ano}/orcamento/execucao`.
5. **Folha de assinaturas** — cargos Direção/CF (de `governance.py`/`permissions.py`), com rodapé "Documento gerado automaticamente pelo Portal ACCTA".

**Response 200**: `application/pdf` (stream). Números coincidem com `/finances/summary?year=ano` (SC-006/FR-019).

**Acceptance**: US3 cenário 1.
