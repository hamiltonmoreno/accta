# Quickstart — Validação: Lembrete de Ato pendente ao próprio proponente

Detalhes em [contracts/sweep-extension.md](contracts/sweep-extension.md) e
[data-model.md](data-model.md). Reutiliza a infraestrutura da spec 010.

## Pré-requisitos

- Backend a correr (`cd backend && uvicorn server:app --reload --port 8001`).
- `ato_overdue_dias` (limiar X) configurável via `PATCH /api/finances/settings` (admin) —
  baixar para 1 ajuda a disparar sem esperar dias.

## Cenário A — Backend (unit, sem servidor)

```bash
cd backend && pytest tests/test_atos_overdue.py -q
```

Cobre (além dos casos da spec 010, que devem continuar verdes):
1. Ato pendente > X dias com proponente **sócio comum** → proponente recebe **1** aviso
   (com antiguidade + link); `notified_proponentes == 1`.
2. **Dedup**: proponente que é **Direção** → recebe só o aviso da Direção; **sem**
   aviso de proponente (`notified_proponentes` não o conta).
3. Proponente **inativo/técnico** → **não** é avisado (FR-007); Direção é avisada na
   mesma; marca gravada.
4. **Idempotência**: 2.ª avaliação → `notified_atos: 0` e `notified_proponentes: 0`
   (marca partilhada).
5. **Resolvido / fora de pendente** → nenhum aviso (proponente nem Direção).
6. **Spec 010 intacta**: a Direção continua a ser avisada exatamente como antes (SC-004).

## Cenário B — Ponta-a-ponta (navegador, Princípio VII — dono)

1. Como **sócio** (proponente), criar um Ato (`/financeiro/co-aprovacoes`).
2. Como **admin**, baixar `ato_overdue_dias` (ou usar um Ato com idade > X) e disparar
   `POST /api/atos/notify-overdue`.
3. Como **proponente**:
   - [ ] Recebo um **aviso in-app** de que o meu Ato continua pendente (idade + link).
   - [ ] Com push ativo, recebo também a **notificação no telemóvel**.
4. **Dedup**: criar um Ato cujo proponente seja membro da Direção → confirmar que recebe
   **um só** aviso (o da Direção), não dois.
5. **Idempotência**: disparar de novo → o proponente **não** recebe segundo aviso.

## Critérios de aceitação (mapeam SC)

- SC-001: todos os Atos overdue geram aviso ao proponente elegível (A.1, B.3).
- SC-002: proponente sabe que está parado sem perguntar (B.3).
- SC-003: ≤ 1 aviso por Ato/evento, sem duplicar com a Direção (A.2, A.4, B.4, B.5).
- SC-004: aviso à Direção inalterado (A.6).
