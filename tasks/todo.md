# Spec 012 — Lembrete de Ato pendente ao próprio proponente (Revisão)

**Feita** (branch `feature/aviso-proponente-ato-pendente`): no varrimento diário existente
(spec 010) que avisa a Direção de um Ato (Art. 54) pendente há > X dias, passar a avisar
**também o próprio proponente** (`created_by`) — **uma única vez por Ato**, partilhando a marca
`overdue_notified_at` da spec 010. Desenho minimalíssimo: **sem schema/migração/agendador/limiar/
campo novos, zero deps, sem frontend.**

- T002/T003 `backend/routes/atos.py` (`_notify_overdue_atos_locked`):
  - +counter `notified_proponentes` no dict `counters`.
  - **Uma** query a `db.users` (`{"id": {"$in": distintos created_by overdue}, "status": "ativo",
    "account_type": {"$ne": "technical"}}`) → `eligible_proponentes` (sem N+1). O DAO compila
    `$ne` para `IS DISTINCT FROM`, logo `account_type` ausente (= membro) **casa** corretamente
    (não é a armadilha NULL/`$exists` da spec 010).
  - No loop por Ato: o aviso à Direção fica **exatamente como está** (SC-004) e, a seguir, avisa o
    proponente **sse** `created_by not in direcao_ids` (dedup, FR-005) **e** `created_by in
    eligible_proponentes` (FR-007), via `notify_users([created_by], "financeiro", "O seu ato
    continua pendente", «…descrição… continua pendente há N dias…», "/financeiro/co-aprovacoes")`.
    Partilha a marca acima ⇒ uma única vez por Ato (Q1=A). Mantém «sem Direção ⇒ não marca/avisa».
- T004 `backend/tests/test_atos_overdue.py` (+5 casos): proponente sócio comum avisado 1× (idade +
  link), **dedup** proponente∈Direção (`notified_proponentes==0`, só aviso da Direção),
  inativo/`technical` excluídos (Direção avisada na mesma), **idempotência** (2.ª avaliação não
  re-avisa), e **sem-Direção** não marca nem avisa o proponente. Helper `_wire_users` honra o filtro
  de elegibilidade. Spec 010 intacta.

**Revisão adversarial (code-reviewer)** — 0 CRITICAL, 2 WARNING, ambas corrigidas:
- **W1 (ordenação de entrega)**: o aviso ao proponente disparava *depois* de gravar a marca
  `overdue_notified_at`; uma falha de `insert_many` no aviso perdia-o em silêncio (marca já
  escrita). Corrigido: ambos os avisos (Direção + proponente) *antes* da marca única — entrega
  ≥1× como o aviso à Direção (spec 010). +teste `test_proponente_falha_entrega_nao_marca_ato`.
- **W2 (FR-002)**: o corpo ao proponente só tinha a descrição; juntou-se `tipo`+`valor` (paridade
  com o aviso à Direção). Teste estendido a afirmar `tipo`/`valor` no corpo.

**Verificação**: `pytest tests/test_atos_overdue.py tests/test_atos.py` → **52 passed**
(6 novos + 46 existentes, incl. spec 010 e fluxo de Atos). `ruff check` limpo; `ruff format`
aplicado ao teste (só wrap de linha). DAO `$ne` confirmado `IS DISTINCT FROM` (database.py:349).
Todos os FR-001..008 e SC-001..004 mapeados ao código.

**Por fechar (fora do âmbito de codificação):** PR → `develop`; release `develop→main` exige
**Via B** (toca `backend/`, fora de `tests/`); verificação prod = `POST /api/atos/notify-overdue`
sem token → 401 (rota viva) **e** a resposta do disparo inclui `notified_proponentes`. Só após
RELEASED+deployed renomear `specs/012-...` para `-concluido`. Validação funcional ponta-a-ponta
(Cenário, navegador) = Princípio VII (dono).
