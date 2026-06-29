# Data Model: Escalonamento de lembretes de Ato pendente

**Sem entidades novas. Sem campos novos. Sem migração.** Esta feature **re-semantiza** um
campo existente.

## Entidade tocada: `Ato` (coleção `atos`)

| Campo | Tipo | Antes (specs 010/012) | Agora (spec 013) |
|-------|------|------------------------|------------------|
| `overdue_notified_at` | ISO-8601 string \| ausente/`null` | **Flag single-shot**: `null`/ausente = "nunca avisado"; uma vez gravado, nunca mais re-avalia. | **Cursor "último lembrete"**: `null`/ausente = "nunca avisado"; um timestamp = instante do **último** lembrete. Re-elegível quando `≤ now − X dias`. |

- A **escrita** não muda: o loop continua a fazer `$set overdue_notified_at = now.isoformat()`
  a cada lembrete (agora isso "avança o cursor" em vez de "marcar para sempre").
- Os restantes campos do Ato (`status`, `created_at`, `created_by`, `tipo`, `descricao`,
  `valor`, `assinaturas[]`) **não são tocados**.

## Configuração reutilizada (sem alteração)

- `FinanceSettings.ato_overdue_dias` (default 7) — serve **simultaneamente** de limiar do
  1.º aviso (idade > X) e de **intervalo da recorrência** (a cada X dias). Sem campo de
  config novo.

## Estados / transições relevantes (do Ato)

```
pendente ──(age > X, cursor None ou ≤ now−X)──► [lembrete enviado; cursor := now] ──► pendente
   │                                                                                      │
   └────────────────── aprovado / rejeitado / executado / cancelado ◄────────────────────┘
                                   (sai de 'pendente' ⇒ deixa de qualificar; FR-007)
```

- **Invariante de cadência**: entre dois lembretes do mesmo Ato decorrem **≥ X dias**
  (o cursor só fica ≤ cutoff passado X). ⇒ nunca dois no mesmo dia (SC-002).
- **Paragem**: não há teto; a única saída do ciclo é o Ato deixar de estar `pendente`
  (SC-003/SC-005).
- **Compatibilidade**: Atos com `overdue_notified_at` ausente (legados) entram pelo ramo
  `None`; Atos com marca recente não qualificam até envelhecer — sem reprocessamento.
