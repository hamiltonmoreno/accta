# Contract: DELETE /api/comunicados/{id} (eliminar rascunho)

Cancela/elimina um comunicado **em estado `rascunho`** (FR-011). Comunicados
`enviado` / `parcial` / `falhado` / `cancelado` são imutáveis.

> Depende de **D2**. Se o ciclo de rascunho não for adoptado, este endpoint não
> existe.

## Auth

`Authorization: Bearer`. RBAC: `send_comunicados` (+ `comunicar_intra_orgao` se
D1). Recomendado: só o `created_by` ou um admin pode eliminar o rascunho.

## Comportamento

- Estado `rascunho` → transita para `cancelado` (soft) **ou** remove o
  documento. **Decisão**: marcar `status="cancelado"` (mantém rasto; coerente
  com "histórico imutável" da spec) — sem `delete_one` físico.
- Audit log: `create_audit_log(user.id, "cancelar_comunicado", id, request=...)`.

## Respostas

| Código | Caso |
|--------|------|
| 200 | `{ "id": "uuid", "status": "cancelado" }` |
| 403 | não é autor nem admin / sem privilégio |
| 404 | inexistente |
| 409 | `{"detail": "Comunicado já enviado — imutável"}` se estado terminal |

## UI

Botão "Eliminar rascunho" = **Carmesim outline** (destrutivo) por defeito;
**Carmesim solid** só dentro do confirm dialog irreversível (constituição V).
