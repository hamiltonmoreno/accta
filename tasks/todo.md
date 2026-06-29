# Spec 013 — Escalonamento de lembretes de Ato pendente (Revisão)

**Feita** (branch `feature/escalonamento-ato-pendente`): o aviso de Ato (Art. 54) pendente
além do limiar X passa de **uma única vez** (specs 010/012) a **recorrente a cada X dias**,
aos mesmos destinatários (Direção + proponente, dedup spec 012), com a antiguidade crescente a
comunicar a urgência, **até o Ato sair de `pendente`** (sem teto). Decisões do dono, todas
minimalistas.

**Desenho de 1 linha** — `backend/routes/atos.py` (`_notify_overdue_atos_locked`):
- A marca `overdue_notified_at` passa de *flag* single-shot a **cursor "último lembrete"**.
- A query do varrimento muda de `{"overdue_notified_at": None}` para
  `{"$or": [{"overdue_notified_at": None}, {"overdue_notified_at": {"$lte": cutoff}}]}` com
  `cutoff = (now - timedelta(days=X)).isoformat()`. +import `timedelta`.
- **Tudo o resto inalterado**: gate de idade (`> X`), avisos Direção+proponente, dedup,
  exclusões `technical`/`inativo`, "sem Direção ⇒ não marca", e a escrita
  `overdue_notified_at = now` (que avança o cursor ⇒ ≥ X dias entre lembretes, anti-spam).

**Verificado contra o DAO real**: `$or` AND-combina com `status` (`database.py:379-387`);
`$lte` = comparação de **texto ISO** (lexicográfica = cronológica, `:308`); `_eq(None)` casa
chave-ausente OU null (`:318`) ⇒ os 3 estados da marca (ausente/legado, null/novo, ISO) cobertos.

**Testes** (`backend/tests/test_atos_overdue.py`): fake `_atos_coll` estendida para honrar
`$or`/`$lte` (espelha `NULL <= cutoff` = no-match e o compare por string). +6 casos:
recorrência (marca antiga → re-avisa, cursor avança), 1.º aviso sem marca intacto,
resolvido-com-marca-antiga não re-avisa, antiguidade crescente no corpo / mesmos destinatários,
anti-spam (marca < X dias não re-avisa), cadência (2 varrimentos → 1 lembrete). Comentário do
`test_idempotente_uma_unica_vez` atualizado para a semântica de cadência.

**Verificação**: `pytest tests/test_atos_overdue.py tests/test_atos.py` → **58 passed**
(6 novos + 52 existentes, incl. specs 010/012 sem regressão). `ruff check` + `format` limpos.
Todos os FR-001..010 e SC-001..005 mapeados.

**Por fechar (fora do âmbito de codificação):** PR → `develop`; release `develop→main` exige
**Via B** (toca `backend/` fora de `tests/`); prova decisiva prod = `POST /api/atos/notify-overdue`
sem token → 401 (rota viva) + a resposta do disparo reflete os lembretes recorrentes. Só após
RELEASED+deployed renomear `specs/013-...` para `-concluido`. Validação funcional ponta-a-ponta
(2 janelas de X) = Princípio VII (dono).
