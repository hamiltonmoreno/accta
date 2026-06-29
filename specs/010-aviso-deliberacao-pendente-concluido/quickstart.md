# Quickstart — Aviso à Direção de Ato pendente

Guia de validação. Detalhes de modelo/contrato em [data-model.md](./data-model.md) e
[contracts/settings-and-trigger.md](./contracts/settings-and-trigger.md).

## Pré-requisitos

- Backend a correr (`cd backend && uvicorn server:app --reload --port 8001`) com Postgres acessível,
  **ou** suite unit in-process (sem servidor) via pytest + `mock_db`.
- Pelo menos 1 membro com cargo na **Direção** (ou, por fallback, 1 admin ativo).

## Cenário A — Unit (sem servidor): lógica de limiar, idempotência, exclusões

```bash
cd backend && pytest tests/test_atos_overdue.py -q
```

Casos que devem passar (cobrem US1/US2/US3 + edge cases / FR-002,004,005,006,007,009):

1. Ato `pendente` com `created_at` > X dias ⇒ `notify_users` chamado com os IDs da Direção, link
   `/financeiro/co-aprovacoes`; Ato fica com `overdue_notified_at`.
2. Ato `pendente` com idade < X ⇒ **nenhum** aviso.
3. Re-correr o varrimento sobre o mesmo Ato já marcado ⇒ **0** avisos novos (idempotência, FR-005).
4. Ato que passou a `aprovado/executado/rejeitado/cancelado` ⇒ **0** avisos (FR-006).
5. `members_of_orgao("direcao")` vazio ⇒ **sem erro**, varrimento conclui (FR-009).
6. `ato_overdue_dias` alterado para um valor menor ⇒ Ato na faixa nova qualifica (US2).
7. Ato com `created_at` ausente/inválido ⇒ ignorado (sem disparo).

## Cenário B — Live (servidor a correr): disparo manual + configuração

```bash
# 1) Definir o limiar (admin)
curl -X PATCH "$BASE/api/finances/settings" -H "Authorization: Bearer $ADMIN" \
     -H 'Content-Type: application/json' -d '{"ato_overdue_dias": 1}'

# 2) (ter um Ato pendente criado há > 1 dia, ou ajustar created_at em ambiente de teste)

# 3) Disparar a avaliação à mão (em vez de esperar o tick diário)
curl -X POST "$BASE/api/atos/notify-overdue" -H "Authorization: Bearer $ADMIN"
# → {"evaluated":N,"overdue":M,"notified_atos":M,"recipients":K}

# 4) Idempotência: repetir o passo 3 ⇒ "notified_atos":0
```

Verificação final: o membro da Direção vê o aviso no sino de notificações (e, se opt-in push, no
telemóvel), e o link abre `/financeiro/co-aprovacoes`.

## Verificação em produção (pós Via B — Princípio VII)

- `POST /api/atos/notify-overdue` sem token ⇒ **401** (rota viva e protegida).
- Após deploy, inspecionar logs do arranque para confirmar o agendamento do loop (linha de log do
  `overdue_atos_loop`) e ausência de tracebacks.
