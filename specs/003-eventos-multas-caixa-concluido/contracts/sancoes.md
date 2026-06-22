# Contrato: Sanções (multa → caixa ao aplicar)

Prefixo: `/api/sancoes`. Guard: `_require_disciplina` (inalterado).

## POST `/sancoes/{sancao_id}/aplicar` — cria receita de multa (alterado)

`aplicar_sancao` (`sancoes.py:261`) passa a criar, **antes do CAS** `decidida→aplicada` (junto dos efeitos idempotentes), a receita da multa:

```python
if s["tipo"] == "multa" and (s.get("multa_valor") or 0) > 0:
    existing = await db.transactions.find_one({"sancao_id": sancao_id, "type": "receita"}, {"_id": 0, "id": 1})
    if not existing:
        tx = Transaction(
            type="receita", category="extraordinarias", sancao_id=sancao_id,
            amount=float(s["multa_valor"]),
            description=f"Multa - {nome do sócio}",
            created_by=current_user.id,
        )
        await db.transactions.insert_one(tx.model_dump())
# ... CAS decidida->aplicada (exactly-once) inalterado
```

**Comportamento**:
- Só para `tipo=="multa"` com `multa_valor>0` (FR-014: outras sanções não geram movimento).
- **Idempotente**: guarda por `find_one({sancao_id, type:"receita"})` ⇒ exactly-once mesmo com re-tentativa/concorrência (FR-013); o CAS final continua a garantir uma só aplicação dos restantes efeitos/notificação.
- Tratada como cobrada no momento (sem dívida — FR-015).
- Audit: `sancao_aplicada` já existente cobre a aplicação; o movimento fica rastreável por `sancao_id`.

**200**: `{ "message": "Sanção aplicada.", "status": "aplicada" }` (inalterado). **Acceptance**: US2 #1/#2/#3.

> **FR-016 (estorno na anulação): FORA DE ÂMBITO** — não existe transição "aplicada → anulada" em `sancoes.py`. Sem fluxo de anulação, sem estorno.
