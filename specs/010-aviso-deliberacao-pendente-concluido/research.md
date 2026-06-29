# Research — Aviso à Direção de Ato pendente

Todas as NEEDS CLARIFICATION resolvidas. Achados ancorados em código existente.

## Decisão 1 — Mecanismo de disparo recorrente (o único ponto deixado "a definir" pela spec)

- **Decisão**: **Loop in-process diário** — `asyncio.create_task(overdue_atos_loop())` arrancado no
  `@app.on_event("startup")` de `backend/server.py`. O loop dorme ~24h, chama `notify_overdue_atos()`,
  e repete. Confirmado com o dono (resposta à pergunta do plano).
- **Rationale**: Zero setup do operador (o cron de rebuild do ranking está agendado "por fazer" desde
  spec ranking-socio — vias dependentes do operador ficam por concluir), zero nova superfície de auth
  (um endpoint de cron exigiria token/serviço), self-contained. Container único no VPS ⇒ sem duplo-disparo.
  SLA da spec é 24h (SC-001) ⇒ um tick diário chega de sobra. Rearranque reinicia o relógio, o que é
  aceitável para um SLA de 24h e inofensivo graças à idempotência.
- **Alternativas rejeitadas**:
  - *Endpoint admin + cron no VPS* — consistente com o padrão "manual + orquestração externa" do
    ranking, mas exige setup manual + auth de cron, e o precedente mostra que esses crons ficam por agendar.
  - *pg_cron* — a lógica (elegibilidade Direção, notificações in-app + push) é Python; replicá-la em
    SQL/plpgsql duplica regras e acopla — contra Princípio I.
- **Padrão de arranque** (precedente, `server.py:245-263`): seeds idempotentes embrulhados em
  `try/except` non-fatal no startup. O loop segue o mesmo (falha do loop nunca derruba o arranque).

## Decisão 2 — Âmbito da entidade: Ato (Art. 54) pendente

- **Decisão**: MVP limita-se ao **Ato** em `status == "pendente"`. Já fixado na spec (FR-001).
- **Achados**: `models.py:1403-1421` (`class Ato`), `ATO_STATUSES = ["pendente","aprovado","rejeitado",
  "executado","cancelado"]` (`models.py:1370`), coleção `atos` (`database.py:97`), rotas `routes/atos.py`.
  Um Ato nasce `pendente` ⇒ `created_at` é a "data de pendente desde" (Assumption da spec confirmada).
- **Link para agir**: `routes/atos.py:41` → `_LINK = "/financeiro/co-aprovacoes"`.
- **Resolvido = sair de pendente**: qualquer um de `aprovado/rejeitado/executado/cancelado` ⇒ filtro
  `status == "pendente"` no varrimento já satisfaz FR-006 (não re-considera resolvidos).

## Decisão 3 — Idempotência "uma única vez" (FR-005/SC-003)

- **Decisão**: marca aditiva `overdue_notified_at: Optional[str]` (ISO-8601) no doc do Ato. O varrimento
  filtra Atos `pendente` **sem** `overdue_notified_at` e cuja idade > X; ao avisar, grava
  `overdue_notified_at = now`. Avaliações seguintes não re-disparam (campo presente).
- **Rationale/precedente**: mesma filosofia "marca na fonte" do lembrete de quotas
  (`insert_quotas_atomic` devolve só os novos — `routes/finances.py:645-683`) e da multa de sanção
  (CAS/índice único — `routes/sancoes.py:333-360`). Aqui basta a marca + `update_one`, porque o loop é
  single-runner (sem concorrência real). `ponytail:` sem CAS — um update simples chega; subir a CAS só
  se o disparo passar a multi-runner.
- **Alterar X para menor** (edge case): Atos já com essa idade e ainda sem marca qualificam no próximo
  varrimento — comportamento desejado, sem reprocessar histórico.

## Decisão 4 — Configuração de X (US2 / FR-004)

- **Decisão**: campo aditivo `ato_overdue_dias: int = 7` em `FinanceSettings` (singleton
  `finance_settings`, `models.py:1334-1352`) + `FinanceSettingsUpdate.ato_overdue_dias`. Lido pelo loop;
  editável via o `PATCH /api/finances/settings` **admin-only existente** (`routes/finances.py:488-587`).
- **Rationale**: `finance_settings` já guarda parâmetros de Atos (`coaprovacao_limiar`) e tem leitura
  default-on-missing (`routes/finances.py:475-485`) ⇒ FR-004 (default 7 quando não configurado) sai de
  graça. Sem nova coleção/endpoint/ecrã.

## Decisão 5 — Destinatários, exclusões, ausência de Direção

- **Decisão**: `members_of_orgao("direcao")` (`helpers.py:425-441`) — já filtra `status=="ativo"` +
  `account_type=="member"` (exclui técnicos/inativos, FR-007) e, sem titulares, cai para admins ativos.
  Lista vazia ⇒ `notify_users([])` é no-op (FR-009: sem erro). Entrega via `notify_users(...)`
  (`helpers.py`), que já espelha para push.

## Decisão 6 — Data ausente/inválida (edge case)

- **Decisão**: Atos sem `created_at` parseável são ignorados (não disparam). Parse defensivo do ISO;
  exceção ⇒ skip silencioso desse Ato (não derruba o varrimento).
