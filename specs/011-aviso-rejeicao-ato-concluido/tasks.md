# Tasks: Aviso de rejeição de Ato com o motivo

**Feature**: `specs/011-aviso-rejeicao-ato/` · **Branch**: `feature/aviso-rejeicao-ato`
**Input**: [plan.md](plan.md) · [spec.md](spec.md) · [research.md](research.md) · [data-model.md](data-model.md) · [contracts/assinar-ato.md](contracts/assinar-ato.md) · [quickstart.md](quickstart.md)

> Desenho mínimo: o motivo vive **na assinatura de rejeição** em `Ato.assinaturas[]`
> (**sem schema/migração/DAO**); reutiliza o aviso de rejeição existente + auditoria.
> Zero deps novas. Toca `backend/` ⇒ release `develop→main` exigirá **Via B**.

## Phase 1: Setup

- [X] T001 Confirmar a branch `feature/aviso-rejeicao-ato` ativa e que NÃO se adicionam dependências (não tocar `backend/requirements.txt` nem `frontend/package.json`).

## Phase 2: Foundational (bloqueia as user stories)

- [X] T002 Adicionar campo aditivo `motivo: Optional[str] = None` à `class AtoSign` em `backend/models.py` (justificação da rejeição; comentário PT a explicar que é obrigatório só quando `decisao == "rejeitado"` e ignorado ao aprovar).

## Phase 3: User Story 1 — Proponente recebe aviso de rejeição com o motivo (P1) 🎯 MVP

**Goal**: ao rejeitar, exigir motivo; entregar ao proponente um aviso (in-app + push) que inclui o motivo; persistir o motivo na assinatura de rejeição e auditá-lo.

**Independent Test**: rejeitar um Ato com motivo → proponente recebe aviso com o motivo + link; rejeitar sem motivo → 400.

- [X] T003 [US1] Em `backend/routes/atos.py` (`sign_ato`): quando `data.decisao == "rejeitado"`, validar o motivo — obrigatório e não-vazio após `strip()` (400 PT «É obrigatório indicar o motivo da rejeição.») e `len(motivo.strip()) <= 500` (400 PT «O motivo não pode exceder 500 carateres.»); ao `aprovado`, ignorar o motivo. Incluir `motivo` (o `strip()`) no dict `assinatura` **antes** de `sign_ato_atomic` (persistência sem mudar o DAO). Validação corre antes do caminho `@limiter`/lock.
- [X] T004 [US1] Ainda em `sign_ato`, no ramo `novo_status == "rejeitado"`: enriquecer o aviso `notify_users([ato["created_by"]], "financeiro", …, exclude_id=current_user.id)` para a mensagem PT incluir o motivo («O ato que propôs foi rejeitado. Motivo: "<motivo>"») e acrescentar `motivo` ao `details` do `create_audit_log` da assinatura. Não criar segundo aviso (FR-006).
- [X] T005 [P] [US1] Em `frontend/src/utils/api.js`, fazer `atos.assinar(...)` enviar `{ decisao, motivo }` (motivo opcional na assinatura; presente na rejeição).
- [X] T006 [US1] Em `frontend/src/pages/private/CoAprovacoesPage.js`, a ação **Rejeitar** abre um confirm com **textarea de motivo** obrigatória (contador até 500; botão Confirmar desativado enquanto vazia/whitespace); botão destrutivo = **Carmesim sólido** dentro do diálogo irreversível, resto neutro, sem dark mode (`/frontend-design`). Submete `decisao:"rejeitado"` + `motivo`. **Aprovar** mantém-se sem diálogo de motivo.
- [X] T007 [US1] Escrever `backend/tests/test_atos_rejeicao_motivo.py` cobrindo o quickstart Cenário A: (1) rejeitar sem motivo→400; (2) motivo só-espaços→400; (3) motivo >500→400; (4) rejeitar com motivo→200, Ato `rejeitado`, assinatura contém `motivo`; (5) aviso ao proponente inclui o motivo + `exclude_id`; (6) auditoria com `motivo` no `details`; (7) aprovar não exige/grava motivo. Usar `mock_db` + fixtures de role; `monkeypatch.setattr(atos.limiter,"enabled",False)` + `Request` mínimo (ver CLAUDE.md Testing). `cd backend && pytest tests/test_atos_rejeicao_motivo.py -q`.

**Checkpoint US1**: rejeição com motivo funciona ponta-a-ponta (aviso + persistência + auditoria); MVP entregue.

## Phase 4: User Story 2 — Motivo visível no detalhe do Ato (P2)

**Goal**: o motivo da rejeição (e quem rejeitou) fica visível na vista de detalhe das co-aprovações, para releitura posterior.

**Independent Test**: abrir um Ato rejeitado → vê o motivo + autor da rejeição; Ato pendente → sem motivo.

- [X] T008 [US2] Em `frontend/src/pages/private/CoAprovacoesPage.js`, nos Atos com `status === "rejeitado"`, mostrar o **motivo** e **quem** rejeitou, lidos da assinatura com `decisao === "rejeitado"` em `ato.assinaturas[]` (sem novo endpoint; o payload do Ato já traz as assinaturas). Ato `pendente`/`aprovado` não mostra bloco de motivo.

**Checkpoint US2**: o motivo é consultável no detalhe, não só no aviso momentâneo.

## Phase 5: Polish & Cross-Cutting

- [X] T009 [P] `cd backend && ruff check . && ruff format --check .` limpo; `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60` limpo para os ficheiros tocados.
- [X] T010 Correr a suite backend completa `cd backend && pytest -q` sem regressões (em especial o fluxo de Atos existente: aprovar, executar, cancelar).
- [X] T011 Atualizar `tasks/todo.md` (secção de revisão) e, no fim e só após verificação, fechar a spec (renomear dir `-concluido`). Nota: toca `backend/` ⇒ release `develop→main` exige **Via B**; verificação prod = `POST /api/atos/<id>/assinar` `{"decisao":"rejeitado"}` sem motivo → 400 (e sem token → 401). Validação funcional ponta-a-ponta (Cenário B, navegador) = Princípio VII (dono).

---

## Dependencies & Execution Order

- **Setup (T001)** → **Foundational (T002)** → **US1 (T003–T007)** → **US2 (T008)** → **Polish (T009–T011)**.
- **T002** bloqueia **T003** (a rota lê `data.motivo`).
- **T003** → **T004** (mesma função `sign_ato`, edições sequenciais) → **T007** (teste valida ambos).
- **T006** e **T008** tocam o mesmo ficheiro (`CoAprovacoesPage.js`) ⇒ **sequenciais** (não `[P]` entre si).
- **US2 (T008)** só depende do backend persistir o motivo (T003); é independente de T006.

## Parallel Opportunities

- **T005** (`utils/api.js`) corre em paralelo com o trabalho de backend T003/T004 (ficheiros diferentes).
- **T007** (teste backend) pode ser escrito em paralelo com T006 (frontend), após T003/T004.
- **T009** (lint) paralelizável no fim entre backend e frontend.

## Implementation Strategy

- **MVP = US1 (T001–T007)**: entrega o valor central — o proponente passa a saber o porquê da rejeição (aviso + persistência). Demonstrável e testável sozinho.
- **Incremento US2 (T008)**: durabilidade/transparência (motivo no detalhe).
- **Polish (T009–T011)**: lint, suite verde, fecho/Via B.

## Format Validation

Todas as tarefas seguem `- [ ] [TaskID] [P?] [Story?] descrição com caminho`. Setup/Foundational/Polish sem label de story; US1/US2 com label; caminhos de ficheiro explícitos.
