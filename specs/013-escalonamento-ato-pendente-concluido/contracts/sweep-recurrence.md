# Contrato: recorrência do varrimento de Atos pendentes

Função interna afetada: **`_notify_overdue_atos_locked()`** em `backend/routes/atos.py`
(introduzida na spec 010, estendida na 012). Sem nova rota; o endpoint admin
`POST /api/atos/notify-overdue` e o loop diário invocam-na sem alteração de assinatura.

## A única mudança de comportamento — query de elegibilidade

**Antes (single-shot):**
```python
atos = await db.atos.find(
    {"status": "pendente", "overdue_notified_at": None}, {"_id": 0}
).to_list(None)
```

**Depois (recorrente, a cada X dias):**
```python
dias = await _overdue_limiar_dias()
now = datetime.now(timezone.utc)
cutoff = (now - timedelta(days=dias)).isoformat()
atos = await db.atos.find(
    {"status": "pendente", "$or": [
        {"overdue_notified_at": None},
        {"overdue_notified_at": {"$lte": cutoff}},
    ]},
    {"_id": 0},
).to_list(None)
```

(`now`/`dias` já são calculados na função; reordenar para o cutoff ficar disponível antes da
query. Importar `timedelta` se ainda não estiver importado.)

## Invariantes que NÃO podem mudar (regressão proibida)

| Invariante | Origem | Garantia |
|------------|--------|----------|
| Aviso à Direção idêntico (corpo, destinatários, contadores) | spec 010 / SC-004 | Loop e `notify_users(direcao_ids, …)` inalterados. |
| Aviso ao proponente deduplicado (`created_by ∉ direcao_ids`, conta elegível), **antes** da marca | spec 012 | Bloco do proponente inalterado. |
| Exclusão `technical`/`inativo` | specs 010/012 | Query de elegibilidade do proponente inalterada. |
| "Sem Direção ⇒ não marca nem avisa" | spec 010 | Early-return inalterado. |
| Marca escrita **após** ambos os avisos | spec 012 (W1) | Ordenação do loop inalterada. |
| `age > X` continua a ser o gate de "atrasado" | spec 010 | Inalterado. |

## Comportamento esperado (entradas → saídas)

| Estado do Ato (pendente) | `overdue_notified_at` | Resultado neste varrimento |
|--------------------------|------------------------|----------------------------|
| age ≤ X | qualquer | não qualifica (gate de idade) |
| age > X | ausente/`null` | **1.º lembrete** (= specs 010/012); cursor := now |
| age > X | `> now − X` (lembrete recente) | **não** re-avisa (anti-spam) |
| age > X | `≤ now − X` (lembrete antigo ≥ X dias) | **novo lembrete**; cursor := now |
| qualquer | qualquer, mas `status ≠ pendente` | não qualifica (FR-007) |

## Contadores devolvidos

Inalterados na forma (`evaluated`, `overdue`, `notified_atos`, `recipients`,
`notified_proponentes`). Agora `notified_atos`/`notified_proponentes` contam **também** os
lembretes recorrentes (não só os primeiros) — é o sinal observável da recorrência.
