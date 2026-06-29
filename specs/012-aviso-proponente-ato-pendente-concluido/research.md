# Phase 0 — Research: Lembrete de Ato pendente ao próprio proponente

`NEEDS CLARIFICATION` resolvido na spec (Q1=A: uma única vez, partilha a marca). As
decisões abaixo fecham o desenho com o critério da Simplicidade (Princípio I).

## D1 — Onde acrescentar o aviso ao proponente

- **Decision**: Dentro do **loop de overdue** em `_notify_overdue_atos_locked()`
  (`routes/atos.py`), no mesmo passo em que a Direção é avisada e a marca
  `overdue_notified_at` é gravada.
- **Rationale**: É o ponto que já decide "Ato parado há > X dias" e já grava a marca de
  idempotência. Reaproveitar garante "uma única vez" (Q1=A) **sem novo estado**.
- **Alternatives considered**: novo varrimento/loop dedicado (duplicava agendador e
  idempotência); novo campo `proponente_notified_at` (estado redundante — a marca da
  spec 010 já serve, porque o evento é o mesmo).

## D2 — Dedup proponente × Direção (FR-005, SC-004)

- **Decision**: Avisar a Direção **exatamente como hoje** (lista `direcao_ids`
  inalterada) e avisar o proponente **apenas se `created_by not in direcao_ids`**.
- **Rationale**: Mantém o aviso à Direção **100% intacto** (SC-004) e garante que um
  proponente-que-é-Direção recebe **um só** aviso (o da Direção, mais acionável para
  quem assina), sem mensagem de proponente redundante (FR-005).
- **Alternatives considered**: excluir o proponente da lista da Direção e enviar-lhe
  sempre a mensagem de proponente — alteraria a notificação que a Direção recebe hoje
  (mexe na spec 010 sem necessidade).

## D3 — Elegibilidade do proponente (FR-007)

- **Decision**: Avisar o proponente só se for **conta ativa e não-técnica**. Apurar com
  **uma única query** a `users` para o conjunto distinto de `created_by` dos Atos
  overdue (sem N+1); construir um set `eligible_proponentes`.
- **Rationale**: `created_by` é um id direto (não passa pelo filtro de
  `members_of_orgao`), logo precisa de filtragem própria (FR-007). Uma query para todos
  evita N+1.
- **Alternatives considered**: não filtrar (violaria FR-007; avisaria contas
  inativas/técnicas); `find_one` por ato (N+1 desnecessário).

## D4 — Mensagem e idempotência

- **Decision**: Mensagem PT própria do proponente, p.ex.: «O ato que propôs ("…")
  continua pendente há N dias, a aguardar assinaturas da Direção.», `type="financeiro"`,
  link `/financeiro/co-aprovacoes`. A marca `overdue_notified_at` é gravada **como
  hoje** (uma vez por Ato), cobrindo ambos os avisos.
- **Rationale**: Coerente com a mensagem à Direção (spec 010); "uma única vez" herdada
  da marca partilhada.
- **Nota de acesso**: a vista `/financeiro/co-aprovacoes` é gated; um proponente sócio
  comum recebe o **valor pelo próprio aviso** (texto), como na spec 011. Aceitável.

## D5 — Marcação quando não há Direção

- **Decision**: Manter a regra da spec 010: **sem destinatários Direção ⇒ não marca**
  (FR-009 da spec 010). O aviso ao proponente **não** altera essa condição de marcação
  (não se grava marca só para avisar o proponente). Assim, quando a Direção existir, o
  Ato volta a qualificar e ambos são avisados juntos.
- **Rationale**: Preserva o invariante da spec 010 e evita marcar um Ato que a Direção
  nunca chegou a ser avisada.
- **Alternatives considered**: marcar mesmo sem Direção (desalinharia da spec 010 e
  poderia "queimar" a marca sem a Direção ter sido avisada).

## D6 — Observabilidade

- **Decision**: Acrescentar `notified_proponentes` aos contadores devolvidos por
  `notify_overdue_atos()` (a par de `notified_atos`/`recipients`), para o log diário e
  para os testes/endpoint manual.
- **Rationale**: Verificável sem novo endpoint; útil ao disparo manual da spec 010.
