# Contracts: Pendências v2

Não há endpoints novos. Os "contratos" desta feature são **invariantes** sobre superfícies
existentes — verificáveis e a manter.

## C1 — Invariante contador ≡ painel (frontend)

- **Contrato**: o número no badge da sidebar é **exatamente** `usePendencias().total`, e o painel
  `/pendencias` lista exatamente `total` itens, para o mesmo utilizador. (SC-002)
- **Como se garante**: ambos consomem o **mesmo hook** `usePendencias()` — não há duas derivações.
- **Apresentação**: `total === 0 ⇒ sem badge`; `total > 9 ⇒ "9+"`; senão o número exato. (FR-003/004)
- **Role-aware**: sócio comum ⇒ `total = votações + eventos`; Direção/admin ⇒ `+ assinatura + propostos`.

## C2 — Contrato de link dos avisos de Ato (backend)

Campo `Notification.link` criado por `routes/atos.py`:

| Tipo de aviso | Estado do Ato | `link` (MUST) |
|---------------|---------------|---------------|
| Criado, a aguardar assinatura (`create_ato`) | pendente | `/pendencias` |
| Atrasado → Direção (`_notify_overdue_atos_locked`) | pendente | `/pendencias` |
| Atrasado → proponente (`_notify_overdue_atos_locked`) | pendente | `/pendencias` |
| Aprovado / rejeitado-com-motivo (`sign_ato`) | decidido | `/financeiro/co-aprovacoes` |
| Pagamento executado (`execute_ato`) | decidido | `/financeiro/co-aprovacoes` |

- **SC-003**: 100% dos avisos de pendentes → `/pendencias`; **0%** dos de decididos → `/pendencias`.
- **Não-regressão**: `_LINK` continua a existir; só os 3 sites de pendentes mudam (não swap cego).

## C3 — Invariantes herdadas da spec 014 (MUST manter)

- **Zero 403 para sócio comum**: as queries de Atos têm `enabled: isDir`. (FR-009 / SC-005)
- **Zero voto secreto**: a derivação não lê `eleicoes`/`deliberacoes`. (SC-005)
- **Read falhado ≠ "tudo em dia"**: `anyError` continua a alimentar o banner de erro do painel
  (não regredir o fix da review da spec 014).

## Verificação (testes)

- **Backend (pytest)** — `tests/test_atos.py`, `tests/test_atos_overdue.py`: asserir o `link` de
  cada categoria conforme C2 (capturar o argumento passado a `notify_users`).
- **Frontend (navegador, Princípio VII — dono)**: C1 e C3 conforme `quickstart.md`.
