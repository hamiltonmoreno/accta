# Quickstart — Validação: escalonamento de Ato pendente

## Pré-requisitos

- `cd backend`
- Testes in-process (sem DB/servidor): `pytest tests/test_atos_overdue.py -q`

## Cenário A — testes automáticos (in-process)

Conduz `notify_overdue_atos()` com `members_of_orgao`/`notify_users` monkeypatched e uma
coleção `atos` falsa que honra o filtro **`status` + (`overdue_notified_at` None OU ≤
cutoff)** (estender a fake da spec 010 para suportar o ramo `$lte` por string ISO).

Casos a cobrir (além dos da spec 010/012, que têm de continuar verdes):

1. **Recorrência**: Ato pendente avisado há **> X dias** (cursor antigo) → recebe **novo**
   lembrete; `overdue_notified_at` avança para "agora"; `notified_atos == 1`.
2. **Anti-spam**: Ato pendente avisado há **< X dias** (cursor recente) → **não** qualifica;
   `evaluated`/`notified_atos == 0`. (SC-002)
3. **Primeiro aviso intacto**: Ato pendente sem marca, age > X → 1.º lembrete (= spec
   010/012), Direção + proponente avisados. (SC-004)
4. **Paragem por decisão**: Ato que sai de `pendente` (ex.: `aprovado`) → **zero** lembretes,
   mesmo com cursor antigo. (SC-003)
5. **Cadência ao longo do tempo**: 2 varrimentos com cursor a < X dias entre eles → só 1
   lembrete; só quando o cursor passa X dias é que o 2.º dispara. (SC-005)
6. **Dedup/exclusões mantidas**: proponente ∈ Direção → 1 lembrete; `technical`/`inativo`
   excluídos — comportamento da spec 012 inalterado em recorrência.

Comando: `cd backend && pytest tests/test_atos_overdue.py tests/test_atos.py -q`
Esperado: **todos verdes** (novos + os das specs 010/012 sem regressão).

## Cenário B — prova decisiva em produção (pós-deploy Via B, Princípio VII — dono)

1. `POST /api/atos/notify-overdue` **sem** token → **401** (rota viva).
2. Com token admin, disparar e inspecionar a resposta: os contadores (`notified_atos`,
   `notified_proponentes`) refletem os lembretes; repetir o disparo no **mesmo dia** **não**
   incrementa (anti-spam intra-dia).
3. Logs do `overdue_atos_loop` sem tracebacks.

> Validação funcional ponta-a-ponta (deixar um Ato pendente atravessar 2 janelas de X dias e
> confirmar 2 lembretes) fica ao critério do dono — requer tempo real ou X baixo de teste.
