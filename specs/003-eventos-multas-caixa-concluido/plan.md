# Implementation Plan: Eventos e Multas Ligados ao Caixa

**Branch**: `feature/eventos-multas-caixa` | **Date**: 2026-06-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-eventos-multas-caixa-concluido/spec.md`

## Summary

Ronda 2 do modelo financeiro unificado (ronda 1 = spec 002, em prod v0.5.26). Liga **eventos** e **multas** ao caixa central pelo mesmo padrão: dinheiro de domínio = `Transaction` com campo de vínculo. (A) `Transaction` ganha `event_id` e `sancao_id`; eventos passam a ter despesas (despesa + gate Art. 54) e receitas (receita, categoria `extraordinarias`) com `event_id`, e o detalhe do evento expõe `resultado_financeiro` derivado; `Ato`/`AtoCreate` ganham `event_id` e `execute_ato` propaga-o; `delete_event` bloqueia (409) com movimentos no caixa. (B) Ao aplicar uma sanção de multa, cria-se idempotentemente uma receita (`sancao_id`, `extraordinarias`) antes do CAS de "aplicada". Filtros `event_id`/`sancao_id` em `/finances/transactions`. Migração: backfill opcional de multas já aplicadas (dry-run + STOP). Reaproveita helpers e padrões da ronda 1 (`helpers.coaprovacao_limiar` #307, guarda 409 do `delete_project`, guarda `ato_id` no delete #308).

## Technical Context

**Language/Version**: Python 3.11 (backend), React 19 (frontend)

**Primary Dependencies**: FastAPI, asyncpg (DAO Mongo-compatível), Pydantic v2; Tailwind + shadcn/ui (frontend)

**Storage**: PostgreSQL/Supabase `(pk, doc jsonb)`. Coleções tocadas: `transactions`, `events`, `sancoes`, `atos`. Índices em `ensure_schema()`.

**Testing**: pytest (unit/in-process com `mock_db`); `bcrypt==4.0.1` pinado

**Target Platform**: Linux server (Via B) + Vercel (frontend)

**Project Type**: Web (backend FastAPI + frontend React)

**Performance Goals**: `resultado_financeiro` do evento por agregação; sem N+1 (o detalhe é 1 evento)

**Constraints**: datas ISO-8601 string; RBAC + audit por endpoint; PT em texto de utilizador; design neutral-led; alterações de modelo aditivas (não quebrar docs); reuso de `extraordinarias` (sem categorias novas)

**Scale/Scope**: ≤ centenas de sócios; prod com ~0 sanções/eventos com finanças (backfill provável no-op)

## Constitution Check

*GATE: avaliado antes do Phase 0 e re-avaliado após Phase 1.*

| Princípio | Conformidade |
|-----------|--------------|
| **I. Simplicity First** | ✅ Reaproveita o padrão e os helpers da ronda 1 (vínculo na Transaction, gate partilhado, guardas de delete). Sem categorias novas. FR-016 cortado por não ter fluxo (YAGNI). |
| **II. Root-Cause Discipline** | ✅ Fecha os domínios que faltavam, sem pensos. |
| **III. RBAC + Audit (NON-NEGOTIABLE)** | ✅ Endpoints de evento usam `has_role_or_privilege(admin, manage_events)`; multa via `aplicar_sancao` (já `_require_disciplina` + audit). Audit em todas as escritas novas. Sem SQL cru; índices em `ensure_schema()`. |
| **IV. Language Discipline** | ✅ Identificadores EN (`event_id`, `sancao_id`); texto/erros PT; domínio PT (`sancao`, `multa`, `evento`). |
| **V. Design System Authority** | ✅ UI de eventos neutral-led; ação positiva Floresta, destrutivo Carmesim-outline. |
| **VI. GitFlow + Confirmation (STOP)** | ⚠️ **Backfill de multas = STOP**: script dry-run por defeito; `--apply` só com confirmação do dono. Branch off `develop`. Modelos aditivos-opcionais (não dispara STOP #5). |
| **VII. Verification Before Done** | ✅ pytest para backend; frente de eventos exercitada no browser; backfill validado em dry-run. |

**Resultado**: PASS, com o backfill marcado STOP (FR-018). Sem violações que exijam Complexity Tracking.

### Ponto resolvido (era a decisão em aberto da spec)

- **FR-016 (estorno na anulação de multa) — FORA DE ÂMBITO.** Confirmado: o código de sanções **não tem** transição "aplicada → anulada" (status existe no enum, mas nenhum handler o define; `routes/sancoes.py` só tem create/comissao/decidir/recurso/aplicar). Sem fluxo de anulação, não há estorno a fazer. Fica registado para ronda futura se a anulação vier a existir.

## Project Structure

### Documentation (this feature)

```text
specs/003-eventos-multas-caixa-concluido/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/{events-finance.md, finances.md, atos.md, sancoes.md}
└── checklists/requirements.md
```

### Source Code (repository root)

```text
backend/
├── models.py                  # +event_id/+sancao_id em Transaction; +event_id em Ato/AtoCreate;
│                              #  EventExpenseCreate, EventReceitaCreate
├── routes/
│   ├── events.py              # despesas/receitas de evento (CRUD), resultado_financeiro no get_event,
│   │                          #  gate Art.54, guarda ato_id no delete, delete_event 409
│   ├── finances.py            # filtros event_id/sancao_id em list_transactions
│   ├── atos.py                # AtoCreate/Ato event_id; execute_ato propaga event_id
│   └── sancoes.py             # aplicar_sancao cria receita idempotente (sancao_id) antes do CAS
├── database.py                # índices ix_tx_event_type, ix_tx_sancao
└── tests/test_eventos_multas_caixa.py   # (novo)

frontend/src/
├── pages/private/ (detalhe de evento)  # secção financeira: despesas/receitas/resultado
└── utils/api.js               # endpoints de evento (expenses/receitas), filtros

scripts/
└── migrate_multas_to_transactions.py   # (novo) backfill dry-run + --apply (STOP)
```

**Structure Decision**: Web app existente; mudança aditiva sobre eventos/finanças/sanções/atos. Reaproveita o padrão da ronda 1.

## Complexity Tracking

> Sem violações da Constitution. Tabela omitida.
