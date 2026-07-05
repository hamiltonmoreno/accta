---
description: "Task list — Spec 016: Gestão de Sócios (privilégios, função, predefinições por cargo, departamento)"
---

# Tasks: Gestão de Sócios — Privilégios legíveis, Função completa, Predefinições por cargo e Departamento na inscrição

**Input**: Design documents from `specs/016-privilegios-cargo-departamento/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: incluídos apenas para o backend (pytest, convenção do projeto). O frontend valida-se no navegador (Princípio VII) + eslint/craco build — sem testes unitários de UI.

**Organização**: tarefas agrupadas por user story para implementação/validação independente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode correr em paralelo (ficheiros diferentes, sem dependências)
- **[Story]**: US1/US2/US3/US4 (mapeia à spec)
- Caminhos de ficheiro exatos incluídos

## Path Conventions

- Web app: `backend/` (FastAPI) e `frontend/src/` (React). Git root = `accta-main/accta/`.

⚠️ **Serialização por ficheiro partilhado** (não são [P] entre si, mesmo sendo histórias diferentes):
- `frontend/src/pages/private/usuarios/EditUserModal.js` → T003 (US1) → T009 (US2) → T013 (US4)
- `frontend/src/pages/private/usuarios/InviteModal.js` → T008 (US2) → T011 (US3)

---

## Phase 1: Setup

**Purpose**: preparar o branch de trabalho. Sem instalação de dependências (zero deps novas) e sem criação de estrutura (ficheiros já existem).

- [X] T001 Criar o branch `feature/016-privilegios-cargo-departamento` a partir de `develop` (`git switch develop && git switch -c feature/016-privilegios-cargo-departamento`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: infraestrutura partilhada por TODAS as histórias.

**Nenhuma tarefa foundational** — as quatro histórias são independentes e não partilham pré-requisitos bloqueadores. (A constante `DEPARTAMENTOS` é partilhada só dentro da US2, por isso vive nessa fase.)

**Checkpoint**: pode começar qualquer história após o Setup.

---

## Phase 3: User Story 1 - Privilégios sempre legíveis (Priority: P1) 🎯 MVP

**Goal**: as 12 permissões mostram sempre um rótulo legível na ficha de edição; nenhuma célula em branco.

**Independent Test**: abrir a ficha de edição de um sócio e confirmar que as 12 caixas de privilégio têm rótulo PT (incl. «Emitir Parecer (Conselho Fiscal)», «Enviar Comunicados», «Comunicar entre Órgãos»).

### Implementation for User Story 1

- [X] T002 [P] [US1] Adicionar os 3 rótulos em falta a `PRIVILEGE_LABELS` em `frontend/src/lib/cargoLabels.js` — `emit_cf_parecer: 'Emitir Parecer (Conselho Fiscal)'`, `send_comunicados: 'Enviar Comunicados'`, `comunicar_intra_orgao: 'Comunicar entre Órgãos'`
- [X] T003 [P] [US1] Em `frontend/src/pages/private/usuarios/EditUserModal.js`: importar `privilegeLabel` de `../../../lib/cargoLabels` (linha 12) e trocar `{PRIVILEGE_LABELS[priv]}` por `{privilegeLabel(priv)}` (linha ~179)

**Checkpoint**: US1 funcional e testável isoladamente (12 rótulos + fallback para a chave em privilégios futuros).

---

## Phase 4: User Story 2 - Departamento como lista suspensa (Priority: P2)

**Goal**: campo «Departamento» passa a dropdown (9 valores + «Outro» → texto livre), opcional, na inscrição pública, no convite e na edição; registos legados preservados.

**Independent Test**: na inscrição pública o campo é uma dropdown com «Outro»; `GET /api/auth/registration-options` devolve `departamentos`; ao editar um sócio com departamento legado fora da lista, o valor é preservado via «Outro».

### Tests for User Story 2 (backend)

- [X] T004 [P] [US2] Teste em `backend/tests/test_auth_routes.py`: (a) `GET /api/auth/registration-options` inclui `departamentos` == `models.DEPARTAMENTOS` (não-vazio); (b) **regressão FR-017/SC-006** — `POST /api/auth/register` com honeypot `website` preenchido devolve 201 falso e NÃO cria utilizador (depende do impl T006/T007 para passar)
- [X] T005 [P] [US2] Teste: `DEPARTAMENTOS` não-vazia e estável (9 itens) em `backend/tests/test_identidade_cargos_models.py`
  > Desvio: o teste ficou em `test_auth_routes.py` (`test_departamentos_constante_estavel`), junto ao T004 — cobertura equivalente. De caminho corrigiu-se em `test_identidade_cargos_models.py` uma assertion stale pré-existente (`len(PRIVILEGES) == 11` → 12, `comunicar_intra_orgao` em falta).

### Implementation for User Story 2

- [X] T006 [P] [US2] Adicionar a constante `DEPARTAMENTOS` (9 valores da data-model) em `backend/models.py`, junto a `CARGOS_DECLARADOS`
- [X] T007 [US2] Em `backend/routes/auth_routes.py`: importar `DEPARTAMENTOS` e fazer `registration_options()` devolver `{"cargos": CARGOS_DECLARADOS, "departamentos": DEPARTAMENTOS}` (depende de T006)
- [X] T008 [US2] Em `frontend/src/pages/private/usuarios/InviteModal.js`: substituir o `<Input>` de departamento (linhas 102-111) por um `<select>` (mesmas classes) alimentado por `DEPARTAMENTOS` + opção «Outro» → `<input>` de texto livre condicional
- [X] T009 [US2] Em `frontend/src/pages/private/usuarios/EditUserModal.js`: substituir o `<Input>` de departamento (linhas 220-227) por `<select>` + «Outro»; **preservar legado** — se `editingUser.department` ∉ lista e ≠ vazio, abrir com «Outro» selecionado e o valor no campo de texto (depende de T010 para a fonte da lista)
- [X] T010 [P] [US2] Adicionar `export const DEPARTAMENTOS = [...]` (mesmos 9 valores) em `frontend/src/pages/private/usuarios/tokens.js` (junto a `ROLES`/`STATUSES`)
- [X] T011 [US2] Em `frontend/src/pages/public/CriarContaPage.js`: substituir o `<Input>` de departamento (linhas 156-168) por `<select>` + «Outro»; obter opções de `registrationAPI.options().departamentos` com um `DEPARTAMENTOS_FALLBACK` local (à imagem de `CARGOS_FALLBACK`); resolver `department` no `onSubmit` (item escolhido ou texto de «Outro»); manter campo opcional (depende de T007 para o endpoint; funciona com fallback)

> Nota de ordem: T010 (constante frontend) antes de T008/T009 (que a consomem). T013 abaixo (US4) também toca em `EditUserModal.js` — respeitar a serialização T003→T009→T013.

**Checkpoint**: dropdown de departamento nos 3 formulários; endpoint devolve `departamentos`; legado preservado.

---

## Phase 5: User Story 3 - Função de acesso completa no convite (Priority: P2)

**Goal**: o seletor de função no convite lista as 4 funções (incl. «Administrador») com o rótulo «Função no Sistema».

**Independent Test**: abrir «Convidar Sócio» e confirmar 4 opções + rótulo «Função no Sistema».

### Implementation for User Story 3

- [X] T012 [US3] Em `frontend/src/pages/private/usuarios/InviteModal.js`: substituir os 3 `<option>` fixos (linhas 70-81) por `ROLES.map(...)` (de `./tokens`) com `ROLE_LABELS` (de `../../../lib/cargoLabels`); mudar o rótulo do campo «Funcao» → «Função no Sistema»; importar `ROLES` e `ROLE_LABELS` (mesmo ficheiro que T008 — sequencial)
  > Achado da review (W1): `POST /api/admin/invite` bloqueava `role=admin` por contrato explícito (422), pelo que a opção «Administrador» falharia sempre. **Decisão do dono: permitir admin no convite** — `routes/admin.py` passou a aceitar as 4 roles (endpoint admin-only + auditado, sem escalada); testes atualizados em `test_admin_routes.py` (+`test_admin_role_invitavel`). Backend passa de 2 para **3 ficheiros aditivos**.

**Checkpoint**: convite oferece 4 roles + rótulo consistente.

---

## Phase 6: User Story 4 - Aplicar as predefinições do cargo (Priority: P3)

**Goal**: botão «Aplicar predefinições do cargo» na edição preenche `role` + `privileges` do cargo; explícito, nunca sobrescreve sozinho; escondido em contas técnicas.

**Independent Test**: editar um sócio com cargo (ex. Tesoureiro), clicar no botão → role «Financeiro» + privilégios `manage_finances`/`view_audit_logs`; editar conta técnica → botão ausente.

### Implementation for User Story 4

- [X] T013 [US4] Em `frontend/src/pages/private/usuarios/EditUserModal.js`: adicionar `useQuery` para `governanceAPI.structure()` (de `../../../utils/api`, `queryKeys`), derivar `entry = structure.cargos.find(c => c.key === editingUser.cargo)`; renderizar botão **secundário** «Aplicar predefinições do cargo» junto à secção Privilégios, visível só se `editingUser.account_type !== 'technical'` **e** `entry` existe; `onClick` faz `setEditingUser({ ...editingUser, role: entry.role_default, privileges: [...entry.privileges_default] })` (mesmo ficheiro que T003/T009 — sequencial)

**Checkpoint**: as 4 histórias independentemente funcionais.

---

## Phase 7: Polish & Cross-Cutting

**Purpose**: verificação transversal (Princípio VII).

- [X] T014 [P] Lint frontend: `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60`
- [X] T015 [P] Build frontend: `cd frontend && yarn build` (craco build limpo)
- [X] T016 [P] Testes backend: `cd backend && pytest tests/test_auth_routes.py tests/test_identidade_cargos_models.py` (e suíte relevante)
- [X] T017 Validação no navegador (dono) do `quickstart.md`: US1 (12 rótulos), US2 (dropdown+«Outro»+legado em inscrição/convite/edição; `curl registration-options`), US3 (4 roles), US4 (botão + escondido em conta técnica)
- [X] T018 Se surgir alguma correção do dono durante a validação, registar em `tasks/lessons.md` (e memória se for insight de longa duração) antes de nova tentativa

> **Fecho (2026-07-02):** T017 validada pelo dono no navegador; T018 sem correções a registar.
> RELEASED **v0.5.53** (PR #400→develop, release #401→main, tag) e **DEPLOYED em prod Via B**
> (`sha-aa15736d5221`; teste decisivo: `registration-options` público devolve `departamentos`).
> Review 2 rondas — W1 (convite-admin 422) resolvida por decisão do dono (admin convidável).
> **SPEC CONCLUÍDA.**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências.
- **Foundational (Phase 2)**: vazia.
- **User Stories (Phase 3–6)**: podem começar após o Setup. São independentes em valor, mas partilham ficheiros (ver serialização abaixo).
- **Polish (Phase 7)**: depois de as histórias desejadas estarem completas.

### Serialização por ficheiro partilhado (crítico)

- `EditUserModal.js`: **T003 → T009 → T013** (US1 → US2 → US4), sempre no mesmo ficheiro.
- `InviteModal.js`: **T008 → T012** (US2 → US3).
- Backend: **T006 → T007**; testes T004 (após T007), T005 (após T006).

### Parallel Opportunities

- Arranque em paralelo (ficheiros distintos): **T002** (cargoLabels), **T006** (models.py), **T010** (tokens.js).
- Testes backend **T004/T005** em paralelo entre si (após o respetivo impl).
- Polish **T014/T015/T016** em paralelo.

---

## Parallel Example (arranque)

```bash
# Ficheiros distintos, sem dependências — podem ir juntos:
T002  frontend/src/lib/cargoLabels.js            (US1)
T006  backend/models.py                          (US2 — constante)
T010  frontend/src/pages/private/usuarios/tokens.js  (US2 — constante)
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Setup (T001) → US1 (T002–T003) → **validar no navegador** (12 rótulos). Entregável mínimo de valor imediato (corrige defeito visível). Frontend-only ⇒ deploy por Vercel, sem Via B.

### Incremental Delivery

1. US1 (frontend) → demo.
2. US2 (backend aditivo + frontend) → demo. **Backend tocado ⇒ release por Via B.**
3. US3 (frontend) → demo.
4. US4 (frontend) → demo.

> Como US2 é a única que toca no backend, agrupar a release de forma a que o deploy Via B cubra US2 (e o resto segue por Vercel).

## Notes

- [P] = ficheiros diferentes, sem dependências. Respeitar a serialização de `EditUserModal.js` e `InviteModal.js`.
- Zero dependências novas; zero migração; `department` continua string livre (sem enum-enforcement) — «Outro» e legado permanecem válidos.
- Não renomear chaves de privilégio/role/cargo (só rótulos de apresentação).
- Commit após cada tarefa ou grupo lógico; abrir PR para `develop`.
