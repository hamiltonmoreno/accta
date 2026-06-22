# Implementation Plan: Fluxo Financeiro Unificado

**Branch**: `feature/fluxo-financeiro-unificado` | **Date**: 2026-06-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-fluxo-financeiro-unificado-concluido/spec.md`

## Summary

Unificar o registo de despesas de projeto no caixa central e tornar o "Relatório e Contas" anual um artefacto gerado pelo sistema. Tecnicamente: (A) a despesa de projeto deixa de viver em `project_expenses` e passa a ser uma `Transaction type="despesa"` com um novo campo `project_id`; `project.spent` passa a derivar de uma agregação sobre `transactions`; o gate de co-aprovação Art. 54 (já existente em `finances.create_transaction`) passa a aplicar-se às despesas de projeto, e a execução de Atos propaga `project_id`. (B) Um novo endpoint gera o Relatório e Contas anual em PDF reutilizando o gerador FPDF do DRE; a submissão do relatório deixa de exigir `document_id` (upload vira anexo opcional). Migração das `project_expenses` históricas via script dry-run + reconciliação, aplicado só após confirmação do dono (STOP condition).

## Technical Context

**Language/Version**: Python 3.11 (backend), React 19 (frontend)

**Primary Dependencies**: FastAPI, asyncpg (DAO Mongo-compatível em `database.py`), Pydantic v2, FPDF (PDF já usado no DRE), Tailwind + shadcn/ui + Recharts (frontend)

**Storage**: PostgreSQL/Supabase — tabelas `(pk bigserial, doc jsonb)`. Coleções tocadas: `transactions`, `projects`, `project_expenses` (a aposentar), `atos`, `exercicios`. Sem SQL cru nas rotas; índices em `ensure_schema()`.

**Testing**: pytest (unit/in-process com `mock_db` de `conftest.py`); `bcrypt==4.0.1` pinado

**Target Platform**: Linux server (backend via Via B Docker) + Vercel (frontend)

**Project Type**: Web (backend FastAPI + frontend React)

**Performance Goals**: listagem de projetos sem N+1 — `spent` de N projetos calculado numa única agregação `$group` por `project_id`

**Constraints**: datas ISO-8601 string; RBAC + audit em cada endpoint; PT em texto de utilizador; design neutral-led (Floresta `#166534` positivo, Carmesim destrutivo); sem dark mode; alterações de modelo aditivas (não quebrar docs existentes)

**Scale/Scope**: ≤ algumas centenas de sócios; volume de `project_expenses` históricas baixo (DB dev quase vazia)

## Constitution Check

*GATE: avaliado antes do Phase 0 e re-avaliado após Phase 1.*

| Princípio | Conformidade |
|-----------|--------------|
| **I. Simplicity First** | ✅ Modelo unificado (fonte única) em vez de dual-write/espelho — menos código a manter, sem shim de sincronização. `spent` derivado elimina contador divergente. |
| **II. Root-Cause Discipline** | ✅ Corrige a raiz (silos isolados), não um penso. Sem fixes temporários. |
| **III. RBAC + Audit (NON-NEGOTIABLE)** | ✅ Todos os endpoints mantêm guard de papel; **adiciona-se audit log à criação/remoção de despesa de projeto** (hoje ausente). Sem SQL cru; índices em `ensure_schema()`. Projeções continuam a excluir `password`. |
| **IV. Language Discipline** | ✅ Identificadores EN genéricos (`project_id`); texto/erros em PT; comentários PT, a condizer com o ficheiro. Sem bulk-rename. |
| **V. Design System Authority** | ✅ UI da Frente B segue neutral-led; downloads = botões neutros; nada de Carmesim como primário positivo. |
| **VI. GitFlow + Confirmation (STOP)** | ⚠️ **Migração de dados = STOP condition #1**. Script corre dry-run por defeito; `--apply` só após confirmação explícita do dono. Branch off `develop`. Tornar `RelatorioContasSubmit.document_id` opcional **não remove rota** nem quebra docs (campo aditivo-opcional). |
| **VII. Verification Before Done** | ✅ pytest para backend; Frente B exercitada no browser; teste de migração em dry-run antes de aplicar. |

**Resultado do gate**: PASS, com a migração marcada como STOP (já previsto na spec FR-013). Sem violações que exijam Complexity Tracking.

### Decisão de permissão (RESOLVIDA pelo dono, 2026-06-20)

- **Quem pode registar despesa de projeto?** **CONFIRMADO: manter `can_manage_project`** (responsável do projeto) **+ adicionar audit log**. Despesas acima do limiar passam pelo gate Art. 54 (Direção + Tesoureiro), pelo que o risco de um gestor escrever no livro-caixa fica limitado a montantes abaixo do limiar e auditado. Alternativa `manage_finances` rejeitada (fricção sem ganho). Ver `research.md` (Decisão 5).

## Project Structure

### Documentation (this feature)

```text
specs/002-fluxo-financeiro-unificado-concluido/
├── plan.md              # Este ficheiro
├── research.md          # Decisões técnicas (Phase 0)
├── data-model.md        # Entidades e deltas de campos (Phase 1)
├── quickstart.md        # Guia de validação end-to-end (Phase 1)
├── contracts/           # Contratos de endpoints (Phase 1)
│   ├── projects-expenses.md
│   ├── finances.md
│   ├── atos.md
│   └── prestacao-contas.md
└── checklists/
    └── requirements.md  # (do /speckit-specify)
```

### Source Code (repository root)

```text
backend/
├── models.py                         # +project_id em Transaction/Ato; +category em ProjectExpenseCreate;
│                                      #  document_id opcional em RelatorioContasSubmit
├── routes/
│   ├── projects.py                   # add_expense/delete_expense → transactions; gate Art.54; audit; spent derivado
│   ├── finances.py                   # filtro project_id em GET /transactions; helper spent por projeto;
│   │                                  #  gerador do Relatório e Contas anual (PDF)
│   ├── atos.py                       # execute_ato propaga project_id
│   └── prestacao_contas.py           # submeter_relatorio sem document_id obrigatório
├── database.py                       # índice em transactions(project_id); project_expenses fica legado
└── tests/
    ├── test_projects_expenses.py     # (novo) despesa→transação, gate, spent, delete
    ├── test_finances_*.py            # filtro project_id; relatório PDF
    └── test_prestacao_contas_*.py    # submissão sem upload

frontend/src/
├── pages/private/financeiro/
│   ├── PrestacaoContasTab.js         # secção "Relatórios gerados" + upload como anexo opcional
│   └── BalancetesTab.js              # (se aplicável) download em destaque
├── pages/private/FinanceiroPage.js   # entrada para relatórios gerados
├── pages/private/ProjetoDetalhe*.js  # Orçado vs. Realizado; categoria na despesa
└── utils/api.js                      # endpoints novos (relatório PDF, filtro project_id)

scripts/
└── migrate_project_expenses_to_transactions.py  # (novo) dry-run + reconciliação + --apply
```

**Structure Decision**: Web app existente (backend + frontend). A mudança é aditiva sobre módulos existentes — não se criam domínios novos. A coleção `project_expenses` permanece fisicamente (para leitura legada/auditoria pós-migração) mas deixa de ser escrita; após migração confirmada não é mais fonte de dados (FR-014).

## Complexity Tracking

> Sem violações da Constitution que exijam justificação. Tabela omitida.
