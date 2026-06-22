# Contrato: Finanças (filtros event_id / sancao_id)

Prefixo: `/api/finances`. Guards existentes (`require_view_finances`).

## GET `/finances/transactions` — params novos

Adiciona `event_id` e `sancao_id` opcionais; quando presentes, `query["event_id"]` / `query["sancao_id"]`.

```
GET /api/finances/transactions?event_id=evt-1
GET /api/finances/transactions?sancao_id=sac-9
```

**200** (forma inalterada): `{ items, total, skip, limit }` filtrado. **Acceptance**: US1 #4.

## Efeito automático (sem endpoint novo)

`compute_financial_summary` / `compute_dre_report` / CSV **não mudam**: despesas/receitas de evento e receitas de multa, sendo `transactions`, entram nas agregações automaticamente (FR-003). Verificação: o `total` do período aumenta no montante registado.
