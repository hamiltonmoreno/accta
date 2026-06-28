---
description: "Task list — Exportar carteira de quotas em PDF"
---

# Tasks: Exportar carteira de quotas em PDF

**Input**: Design documents from `/specs/007-carteira-quotas-pdf/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: SIM — o `quickstart.md` pede um `tests/test_me_quotas_pdf.py` (unit, com
`mock_db` + token forjado). Incluídos. O download real é verificado em navegador
(Princípio VII).

**Organização**: por user story. Backend (1 endpoint + 1 renderer) + frontend (botão +
método de API). Zero deps novas; sem schema/migração; toca `backend/` → release = **Via B**.

## Format: `[ID] [P?] [Story] Description`

## ⚠️ Sobreposição de ficheiros

- `backend/routes/finances.py` — tocado por **US1 (renderer+endpoint)** e **US3
  (caso vazio)** → sequencial nesse ficheiro.
- `backend/tests/test_me_quotas_pdf.py` — **US2 + US3** escrevem nele → sequencial.
- `frontend/src/utils/api.js` e `frontend/src/pages/private/CarteiraPage.js` — **US1**,
  ficheiros distintos.

---

## Phase 1: Setup

- [X] T001 Confirmar os pontos de reutilização (sem código): em
  `backend/routes/finances.py` — `_new_relatorio_pdf()`/`_fmt()`, o padrão de cabeçalho
  Carmesim/Grafite, `StreamingResponse(media_type="application/pdf")` (~linha 1132) e a
  query de `GET /me/quotas` (~linha 122); no frontend, o idioma de download por blob
  em `CarteiraPage.js` (QR) e `financeiro/DRETab.js`.

---

## Phase 2: Foundational

- Nenhuma. A feature reutiliza infra existente (gerador PDF, query self-service,
  idioma de download). As user stories começam diretamente.

---

## Phase 3: User Story 1 — Descarregar a carteira em PDF (Priority: P1) 🎯 MVP

**Goal**: o sócio descarrega, da Carteira, um PDF *branded* ACCTA com os seus
lançamentos de quota/jóia e o total.

**Independent Test**: login como sócio com quotas → "Exportar PDF" → descarrega um PDF
legível com marca ACCTA, identificação, tabela e total. (SC-001/002, FR-002/3/4)

- [X] T002 [US1] Em `backend/routes/finances.py`, adicionar `_render_carteira(pdf, member, items, total)`
  (análogo a `_render_dre`): cabeçalho ACCTA (Carmesim/branco) + subtítulo "Carteira de
  Quotas"; bloco de identificação (nome, n.º de sócio, data de emissão UTC); tabela
  Data · Período/Descrição · Categoria (Quota/Joia) · Valor (CVE) com subtotais por ano;
  **Total pago** em destaque; rodapé "Comprovativo pessoal de uso interno — sem valor
  fiscal." Reusa `_new_relatorio_pdf`/`_fmt`; rótulos ASCII (dados PT latin-1-safe).
- [X] T003 [US1] Em `backend/routes/finances.py`, adicionar `GET /me/quotas/pdf`
  (`Depends(get_current_user)`): mesma query de `/me/quotas` (own `user_id`, `type=receita`,
  `category ∈ {quotas,joias}`, sort date desc), coerção defensiva de `amount`, gerar o PDF
  via `_render_carteira` e devolver `StreamingResponse(io.BytesIO(...), media_type="application/pdf",
  headers={"Content-Disposition": "attachment; filename=Carteira_Quotas_ACCTA_<member_id|socio>.pdf"})`.
  Sem privilégio, sem audit (leitura dos próprios dados).
- [X] T004 [P] [US1] Em `frontend/src/utils/api.js`, adicionar `financesAPI.myQuotasPdf()`
  — `GET /finances/me/quotas/pdf` com `responseType: 'blob'` (cliente axios já tem `withCredentials`).
- [X] T005 [US1] Em `frontend/src/pages/private/CarteiraPage.js`, adicionar um botão
  **"Exportar PDF" (neutro — ação de exportação)** que chama `myQuotasPdf()` e descarrega
  via o idioma de blob existente (`URL.createObjectURL(new Blob([res.data], {type:'application/pdf'}))`
  + `<a download="Carteira_Quotas_ACCTA_…pdf">`), com `toast.error` em falha.
- [X] T006 [US1] Verificar em navegador (Princípio VII): login sócio c/ quotas → Carteira →
  "Exportar PDF" → download; abrir o PDF e confirmar marca ACCTA, nome + n.º de sócio,
  data, tabela, **Total** e rodapé. Confirmar que o total coincide com a vista da Carteira
  (SC-003). 

**Checkpoint**: US1 funcional e demonstrável (MVP).

---

## Phase 4: User Story 2 — Só a própria carteira (Priority: P1)

**Goal**: a exportação devolve só os lançamentos do próprio; terceiros e não-autenticados
são recusados.

**Independent Test**: token de A → PDF só com lançamentos de A; sem token → 401.
(SC-004, FR-005/6)

> Propriedade do endpoint de US1 (sem parâmetro de "outro sócio"). Tarefas = testes.

- [X] T007 [US2] Criar `backend/tests/test_me_quotas_pdf.py` (unit, `mock_db` + `make_token`,
  importar o módulo de rota no topo): own-data → `200`, `Content-Type: application/pdf`,
  `Content-Disposition` com filename `.pdf`, corpo começa por `%PDF`; injetar lançamentos
  de **outro** `user_id` no `mock_db` e confirmar que o total/itens refletem **só** os do
  próprio (filtro por `user_id`). Desligar o limiter se aplicável (`monkeypatch`).
- [X] T008 [US2] No mesmo `test_me_quotas_pdf.py`, adicionar o caso **não autenticado** → `401`.
- [X] T009 [US2] Verificar (navegador/dados): confirmar que o PDF só contém lançamentos do
  próprio sócio. (SC-004)

---

## Phase 5: User Story 3 — Carteira vazia (Priority: P3)

**Goal**: sócio sem lançamentos obtém um PDF válido (sem erro), com "Sem lançamentos" e Total 0.

**Independent Test**: sócio sem quotas → 200, PDF válido `%PDF`, Total 0. (SC-005, FR-007)

> Depende de US1 (mesmo `finances.py` / mesmo ficheiro de testes).

- [X] T010 [US3] Em `backend/routes/finances.py`, garantir que `_render_carteira` trata a
  lista vazia: imprime "Sem lançamentos registados." e Total 0, sem rebentar (sem tabela vazia/erro).
- [X] T011 [US3] No `backend/tests/test_me_quotas_pdf.py`, adicionar o caso **carteira vazia**:
  sócio sem lançamentos → `200`, corpo `%PDF`, sem exceção.
- [X] T012 [US3] Verificar em navegador: sócio sem lançamentos → "Exportar PDF" → PDF válido
  com "Sem lançamentos" e Total 0. (SC-005)

---

## Phase 6: Polish & Cross-Cutting

- [X] T013 [P] Lint: `cd backend && ruff check routes/finances.py` e
  `cd frontend && npx eslint src/pages/private/CarteiraPage.js src/utils/api.js --ext .js,.jsx --max-warnings=60`.
- [X] T014 Correr `cd backend && pytest tests/test_me_quotas_pdf.py -q` (verde) e a checklist
  do `quickstart.md` (SC-001…SC-005); confirmar zero regressões noutros testes de finanças.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências.
- **Foundational (Phase 2)**: vazia.
- **US1 (Phase 3)**: MVP; T002→T003 (mesmo ficheiro) sequenciais; T004 [P]; T005 depende de T004; T006 depende de T002-T005.
- **US2 (Phase 4)**: depende do endpoint (US1) existir; testes.
- **US3 (Phase 5)**: T010 depois de US1 (mesmo `finances.py`); T011 depois de T007 (mesmo ficheiro de testes).
- **Polish (Phase 6)**: no fim.

### User Story Dependencies

- **US1 (P1)**: independente. **MVP.**
- **US2 (P1)**: testa propriedade do endpoint de US1 → depois de US1.
- **US3 (P3)**: pequena lógica no renderer + teste → depois de US1.

### Parallel Opportunities

- **T004** (api.js) é [P] face a T002/T003 (finances.py) — ficheiros distintos.
- **T013** (lint) [P].
- Dentro de `finances.py` e do ficheiro de testes, as tarefas são sequenciais.

---

## Parallel Example

```bash
# US1: backend e o método de API podem avançar em paralelo:
Trilho A (backend finances.py):  T002 → T003
Trilho B (frontend api.js):      T004        # [P] com A
# depois convergem: T005 (CarteiraPage usa T004) → T006 (verificação)
```

---

## Implementation Strategy

### MVP First (US1)

Phase 1 → US1 (T002-T006) → **validar download no navegador** → demo/PR se pronto.

### Incremental Delivery

US1 (MVP, download a funcionar) → US2 (testes de privacidade) → US3 (vazio) → Polish.

---

## Notes

- Reutiliza: gerador PDF *branded* `fpdf`, query `/me/quotas` (RBAC-safe), idioma de
  download por blob. **Zero deps novas; sem schema/migração.**
- Toca `backend/` → o corte `develop→main` que levar isto a prod precisa de **Via B**
  (ver [[prod-backend-deployed-state]]); o frontend vai pelo Vercel.
- Commits: Conventional Commits com escopo (`feat(finances): …`). PR para `develop` (GitFlow).
