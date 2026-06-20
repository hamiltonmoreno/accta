# Implementation Plan: Comunicados Segmentados (v2)

**Branch**: `001-comunicados-segmentados` | **Date**: 2026-06-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-comunicados-segmentados/spec.md`

## Summary

Substituir o envio "para todos os sócios activos" do módulo de comunicados
existente (PR #113, deployed) por uma **audiência definida pelo autor** —
composta por cargo / órgão / categoria / status / período de filiação / lista
nominal — com **preview** antes do envio e **snapshot auditável** da audiência
efectivamente resolvida.

**Abordagem técnica (additiva, não reescrita)**: o módulo actual já tem
resolução de destinatários (`comunicados_service.resolve_recipients`), fan-out
por canais (in-app + Resend), audit log, índices e UI. O v2 adiciona, ao lado
do `ComunicadoSegment` (single-kind) existente, um **`AudienceFilter` composto
tipado** e um resolvedor `resolve_audience()` que aplica **OR dentro do tipo /
AND entre tipos** (FR-014). O dispatch já resolve no momento do envio (FR-010 ✓);
acrescenta-se a persistência do `audience_filter` + `audience_resolved`
(snapshot de `member_id`) no documento. A composição legada (`segment`) e os
gatilhos automáticos de governança continuam intactos.

## Technical Context

**Language/Version**: Python 3.11 (backend), React 19 / JS (frontend)

**Primary Dependencies**: FastAPI + asyncpg (Mongo-compatible DAO em
`backend/database.py`); Pydantic v2; Resend (email); React 19 + Tailwind 3 +
shadcn/ui + Framer Motion + TanStack Query (frontend)

**Storage**: PostgreSQL/Supabase via DAO. Colecção `comunicados` já existe
(`database.COLLECTIONS`) com índices em `created_at`, `status`, `created_by`,
`source_kind/ref_id`. Datas como strings ISO-8601. Sem `_id` real — `id` é
`str(uuid4())`.

**Testing**: pytest (unit/in-process via `tests/conftest.py` + `mock_db`;
asyncio_mode=auto). Integração live é fora de escopo local.

**Target Platform**: Linux server (Docker, deploy Via B) + Vercel (frontend)

**Project Type**: Web application (frontend React + backend FastAPI)

**Performance Goals**: escala ≤ ~200 sócios; resolução de audiência server-side
in-memory sobre `users` activos — sem novas filas (assumption da spec).
Preview p95 < 500ms para o universo actual.

**Constraints**: NÃO quebrar documentos `comunicados` existentes em prod
(constituição STOP #5). Extensão de `COMUNICADO_STATUSES` é **aditiva**
(`rascunho`, `cancelado`); o estado `enviado_parcial` da spec **reutiliza** o
`parcial` existente (sem rename). Envio real de email a sócios é STOP #6 —
mitigado por `dry_run` em não-produção (FR-009).

**Scale/Scope**: 1 colecção estendida, ~3 modelos Pydantic novos/alterados,
~3 endpoints (1 novo de preview, create estendido, delete de rascunho),
1 página admin estendida (composer + preview), ~2 ficheiros de teste novos.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação | Estado |
|-----------|-----------|--------|
| **I. Simplicity First** | Extensão aditiva; reutiliza dispatch/email/notify/audit/índices existentes. Sem filas novas (assumption). Snapshot é um campo no doc, não uma tabela nova. | ✅ PASS |
| **II. Root-Cause Discipline** | Reconciliação de status feita aditivamente (não rename destrutivo nem shim); `enviado_parcial`→`parcial` documentado, não duplicado. | ✅ PASS |
| **III. RBAC + Audit (NON-NEG)** | Cada endpoint protegido verifica privilégio à entrada (`send_comunicados` + overlay `comunicar_intra_orgao` — ver D1); `comunicado_enviado` em cada envio; sem SQL cru (só DAO); índices só em `ensure_schema()`; órgão→cargos resolvido server-side via `governance.py` (FR-012, sem hard-code no frontend). | ✅ PASS |
| **IV. Language Discipline** | UI/email/detail em PT; identificadores EN genéricos (`audience_filter`, `resolve_audience`, `recipients_count`); domínio PT (`comunicado`, `socio`, `orgao`, `cargo`, `rascunho`). | ✅ PASS |
| **V. Design System (NON-NEG)** | "Enviar comunicado" = Floresta `#166534` (único primário positivo/vista); "Eliminar rascunho" = Carmesim outline (solid só no confirm dialog irreversível). Aviso de dry-run neutro. Sem dark mode. | ✅ PASS |
| **VI. GitFlow + Confirmation** | Feature off `develop`, PR→`develop`. STOP #5 (modelo Pydantic): mitigado — alterações aditivas/opcionais. STOP #6 (email a sócios reais): `dry_run` em não-prod + o envio real continua a exigir confirmação do autor (preview→confirmar). | ⚠ Gated → ver Complexity / D2 |
| **VII. Verification (NON-NEG)** | Backend: pytest verde (resolução, preview, snapshot, RBAC, dry-run). Frontend: composer+preview exercitados em browser antes de "done". | ✅ PASS |

**Owner-decision gates** (a spec defere explicitamente — confirmar antes de
`/speckit-implement`, conforme `confirm-spec-decisoes-before-implementing`):

- **D1 — Matriz de privilégios** (spec Assumptions §298–302): manter o
  `send_comunicados` único, ou introduzir `comunicar_intra_orgao` para o
  Conselho Fiscal poder dirigir-se à Direcção (US4)? **Recomendação**: manter
  `send_comunicados` para emissão geral (admin/Direcção) e adicionar **uma**
  privilege overlay `comunicar_intra_orgao` só se o dono quiser US4 já neste
  ciclo. Resolvido em `research.md`, confirmar com o dono.
- **D2 — Ciclo de rascunho** (US1-AS3 + FR-011): v2 introduz estado `rascunho`
  persistido (criar→guardar→editar→enviar/cancelar), ou só "compor→preview→
  enviar" numa sessão? Tem impacto na superfície de UI e endpoints.
  **Recomendação**: incluir `rascunho` (a spec pede-o em FR-011); confirmar
  âmbito.
- **D3 — Vocabulário de status**: confirmar que `enviado_parcial` (spec)
  **reutiliza** o `parcial` existente em vez de criar um valor novo (evita
  quebrar docs e o dispatch). Recomendação: reutilizar.

Nenhuma violação não-justificada bloqueia a fase de design. Os gates D1–D3 são
decisões de produto, registadas para confirmação antes da implementação.

## Project Structure

### Documentation (this feature)

```text
specs/001-comunicados-segmentados/
├── plan.md              # Este ficheiro (/speckit-plan)
├── research.md          # Fase 0 — decisões e D1–D3
├── data-model.md        # Fase 1 — Comunicado v2, AudienceFilter, status aditivo
├── quickstart.md        # Fase 1 — cenários de validação executáveis
├── contracts/           # Fase 1 — contratos dos endpoints
│   ├── preview-audience.md
│   ├── create-comunicado.md
│   └── delete-draft.md
├── checklists/
│   └── requirements.md  # (já existe)
└── tasks.md             # Fase 2 — /speckit-tasks (NÃO criado aqui)
```

### Source Code (repository root)

Web application — backend FastAPI + frontend React, ambos já existentes. O v2
toca pontos concretos (não cria pastas novas):

```text
backend/
├── models.py                     # + AudienceFilter; ComunicadoCreate.audience_filter (opcional);
│                                 #   COMUNICADO_STATUSES += ["rascunho","cancelado"] (aditivo)
├── comunicados_service.py        # + resolve_audience(); preview_audience();
│                                 #   dispatch persiste audience_resolved + failed_member_ids; dry_run
├── permissions.py                # + comunicar_intra_orgao helper (se D1 confirmar US4)
├── governance.py                 # (fonte de órgão→cargos; sem alteração — já expõe members_of_orgao)
├── database.py                   # + índice ix_comunicados (se necessário) em ensure_schema()
├── routes/comunicados.py         # + POST /comunicados/preview-audience; create estendido;
│                                 #   DELETE /comunicados/{id} (rascunho); GET histórico estende campos
└── tests/
    ├── test_comunicados_audience.py   # NOVO — resolve_audience OR/AND, technical, nominal, período
    └── test_comunicados_preview.py    # NOVO — preview count+sample+warnings+0-destinatários+dry-run

frontend/src/
├── pages/private/AdminComunicadosPage.js     # liga o novo fluxo de audiência
├── pages/private/comunicados/
│   ├── ComposerCard.js           # compositor multi-critério (cargo/órgão/categoria/status/período/nominal)
│   ├── PreviewCard.js            # contagem por tipo + após intersecção + amostra + avisos (FR-002/014)
│   └── ConfirmDialog.js          # confirmação de envio (Floresta) / eliminar rascunho (Carmesim outline)
└── utils/api.js                  # comunicadosAPI: + previewAudience(), + deleteDraft()
```

**Structure Decision**: Web application existente. O v2 **estende** o módulo
`comunicados` (backend `comunicados_service.py` + `routes/comunicados.py` +
`models.py`; frontend `pages/private/comunicados/*`). Não há projecto novo nem
nova arquitectura — a decisão central é manter o `ComunicadoSegment` legado a
funcionar (gatilhos de governança) e adicionar o caminho `AudienceFilter` ao
lado, partilhando o dispatch/email/notify existentes.

## Complexity Tracking

> Preencher só se o Constitution Check tem violações a justificar.

A única tensão é o gate de **Principle VI / STOP #5 (modelo Pydantic) e #6
(email a sócios reais)** — não é uma violação, é um gate processual:

| Tensão | Porquê necessária | Mitigação (porque não é violação) |
|--------|-------------------|------------------------------------|
| Estender `COMUNICADO_STATUSES` e `ComunicadoCreate` | FR-011 exige `rascunho`/`cancelado`; FR-001 exige `audience_filter` | Alterações **aditivas/opcionais**: `audience_filter` é `Optional`, novos status não removem os antigos, docs existentes continuam válidos. Sem quebra → STOP #5 satisfeito por design. |
| Envio real de email segmentado | É o propósito da feature | `dry_run` em não-produção (FR-009) + confirmação humana no preview antes de cada envio real → STOP #6 satisfeito pelo gate de confirmação já existente no fluxo. |
