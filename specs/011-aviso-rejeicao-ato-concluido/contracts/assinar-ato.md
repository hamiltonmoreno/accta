# Contract — Rejeição de Ato com motivo

Endpoint **existente**, contrato **estendido** (campo aditivo). Sem rotas novas.

## `POST /api/atos/{ato_id}/assinar`

**Auth**: Bearer (membro da Direção — `_require_sign`). Não-Direção → **403**.

**Request body** (`AtoSign`):

```json
{ "decisao": "rejeitado", "motivo": "Falta o comprovativo da despesa." }
```

| Campo | Obrigatório | Regra |
|-------|-------------|-------|
| `decisao` | sim | `"aprovado"` \| `"rejeitado"` (outro → 400) |
| `motivo` | **sim se `decisao=="rejeitado"`** | não-vazio após `strip()`, ≤ 500 carateres; ignorado se `aprovado` |

**Respostas:**

| Código | Quando |
|--------|--------|
| 200 | Assinatura aplicada; devolve o Ato atualizado (estado reapurado). Se ficou `rejeitado`, a assinatura de rejeição inclui `motivo`. |
| 400 | `decisao` inválida; **rejeição sem motivo**; **motivo > 500 carateres** |
| 401 | sem token |
| 403 | não é membro da Direção |
| 404 | Ato inexistente |
| 409 | já assinou / assinatura concorrente em curso (inalterado) |

**Mensagens PT (detail):**
- sem motivo → «É obrigatório indicar o motivo da rejeição.»
- longo → «O motivo não pode exceder 500 carateres.»

## Efeitos quando a assinatura torna o Ato `rejeitado`

1. **Aviso ao proponente** (`notify_users([ato.created_by], "financeiro", …,
   exclude_id=quem_rejeitou)`) — mensagem PT inclui o motivo:
   > «O ato que propôs foi rejeitado. Motivo: "<motivo>"»
   Entrega in-app + espelho push (reaproveitados; sem email).
2. **Auditoria** — `create_audit_log` da assinatura inclui `motivo` no `details`.
3. **Persistência** — `motivo` fica na assinatura de rejeição em `Ato.assinaturas[]`
   (visível no detalhe das co-aprovações).

## Não-objetivos do contrato

- Aprovar não exige nem grava motivo.
- Sem endpoint novo; sem alteração ao `sign_ato_atomic`/DAO; sem migração.
