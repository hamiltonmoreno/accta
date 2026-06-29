# Quickstart — Validação: Aviso de rejeição de Ato com o motivo

Guia de validação ponta-a-ponta. Detalhes de contrato em [contracts/assinar-ato.md](contracts/assinar-ato.md)
e de dados em [data-model.md](data-model.md).

## Pré-requisitos

- Backend a correr (`cd backend && uvicorn server:app --reload --port 8001`).
- Frontend (`cd frontend && yarn start`) para os cenários de UI.
- Utilizadores: um **proponente** (sócio) e um **membro da Direção** distintos.

## Cenário A — Backend (unit, sem servidor)

```bash
cd backend && pytest tests/test_atos_rejeicao_motivo.py -q
```

Cobre:
1. Rejeitar **sem motivo** → 400 («É obrigatório indicar o motivo da rejeição.»).
2. Rejeitar com motivo **só espaços** → 400 (tratado como vazio).
3. Rejeitar com motivo **> 500 carateres** → 400 (recusa, não trunca).
4. Rejeitar com motivo **válido** → 200; Ato fica `rejeitado`; a assinatura de rejeição
   contém `motivo`.
5. O **aviso ao proponente** é emitido com o motivo no corpo e `exclude_id` = quem
   rejeitou (proponente=rejeitador → sem auto-aviso).
6. A **auditoria** da assinatura inclui `motivo` no `details`.
7. **Aprovar** com/sem motivo → 200 e **não** grava motivo (comportamento inalterado).

## Cenário B — Ponta-a-ponta (navegador, Princípio VII — dono)

1. Como **proponente**, criar um Ato (`/financeiro/co-aprovacoes`).
2. Como **membro da Direção**, abrir o Ato e clicar **Rejeitar**:
   - [ ] Abre um diálogo com **textarea de motivo** obrigatória (confirmar desativado
         enquanto vazia; contador até 500).
   - [ ] Confirmar a rejeição com um motivo (ex.: "Falta o comprovativo da despesa").
3. Como **proponente**:
   - [ ] Recebo um **aviso in-app** de rejeição que **inclui o motivo** e link para o Ato.
   - [ ] Com push ativo, recebo também a **notificação no telemóvel** com o motivo.
4. Abrir o Ato rejeitado:
   - [ ] O **detalhe mostra o motivo** da rejeição e **quem** a registou.
5. Repetir aprovando outro Ato:
   - [ ] **Aprovar** não pede motivo; fluxo inalterado.

## Critérios de aceitação (mapeam SC)

- SC-001: nenhum aviso de rejeição sai sem motivo (Cenário A.1–A.5, B.3).
- SC-002/003: proponente vê o motivo no aviso e no detalhe, de imediato (B.3, B.4).
- SC-004: validação qualitativa do dono — motivo suficiente para decidir a correção.
