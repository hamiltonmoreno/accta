# Contrato: Prestação de Contas (upload opcional)

Prefixo: `/api/` (router `prestacao_contas.py`). Guards de prestação de contas inalterados.

## POST `/exercicios/{ano}/relatorio` — `document_id` opcional

`RelatorioContasSubmit.document_id` passa a `Optional[str] = None`.

**Request body**:
```json
{ "document_id": null }     // ou omitido; ou um id de anexo opcional
```

**Comportamento** (`submeter_relatorio`, `prestacao_contas.py:353`):
1. 400 se exercício não está "aberto" (inalterado).
2. **Só** valida/publica documento se `document_id` for fornecido (espelha o padrão de orçamento/plano em `prestacao_contas.py:394`,`425`). Sem `document_id` → segue sem anexo.
3. `dre_snapshot = compute_dre_report(ano)` **sempre congelado** (auditabilidade preservada).
4. Estado → `relatorio_submetido`; audit log.

**Response 200**: `{ "ano": ano, "status": "relatorio_submetido", "aviso": ... }`.

**Acceptance**: US3 cenários 2 e 3.

## Upload de PDF — passa a anexo opcional

`POST /prestacao-contas/documentos?kind=relatorio` mantém-se funcional, mas deixa de ser **obrigatório** no fluxo. UI re-rotula como "anexo (opcional) — versão assinada à mão" (FR-017, US4). Os números do relatório **nunca** vêm do PDF (FR-019).
