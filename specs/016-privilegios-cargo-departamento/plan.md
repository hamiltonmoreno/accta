# Implementation Plan: Gestão de Sócios — Privilégios legíveis, Função completa, Predefinições por cargo e Departamento na inscrição

**Branch**: `feature/016-privilegios-cargo-departamento` | **Date**: 2026-07-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/016-privilegios-cargo-departamento/spec.md`

## Summary

Quatro melhorias de UX na gestão de sócios, sem tocar em governança institucional nem em esquema de dados:

1. **US1 (P1)** — Privilégios sempre legíveis: os 3 privilégios sem tradução (`emit_cf_parecer`, `send_comunicados`, `comunicar_intra_orgao`) recebem rótulo PT em `lib/cargoLabels.js`, e `EditUserModal` passa a usar o helper `privilegeLabel()` (fallback para a chave) em vez de indexar o mapa diretamente — nenhuma célula fica em branco, agora ou no futuro.
2. **US2 (P2)** — Departamento como lista suspensa (9 valores + «Outro» → texto livre), **opcional**, na inscrição pública, no convite e na edição. Fonte da lista no backend (`models.DEPARTAMENTOS`), exposta aditivamente no endpoint público de opções.
3. **US3 (P2)** — Convite com as 4 funções de acesso (adiciona «Administrador») e rótulo «Função no Sistema», consistente com a edição.
4. **US4 (P3)** — Botão «Aplicar predefinições do cargo» no `EditUserModal` que preenche `role` + `privileges` a partir de `CARGO_DEFAULTS[cargo]` (já disponível em `GET /api/governance/structure`); explícito, nunca sobrescreve sozinho; escondido em contas técnicas.

**Abordagem técnica**: predominantemente **frontend**. O backend muda em **2 ficheiros aditivos** (`models.py`: nova constante `DEPARTAMENTOS`; `auth_routes.py`: `registration_options()` passa a devolver também `departamentos`). Todo o resto (cargo→role→privilégios, roles, estrutura de governança) **já existe** e é apenas consumido/exposto na UI. **Zero dependências novas. Zero migração.**

## Technical Context

**Language/Version**: Python 3.11 (backend), JavaScript / React 19 (frontend)

**Primary Dependencies**: FastAPI + asyncpg (backend); React 19 + TanStack Query v5 + react-hook-form + zod + Tailwind + lucide-react (frontend). **Zero dependências novas.**

**Storage**: N/A — sem alteração de esquema. `department` já é uma string livre no `doc` jsonb do utilizador (`RegistrationRequest.department` max_length 80, `UserAdminUpdate.department` max_length 80, `InviteCreate.department`). Mantém-se string livre (validação-only na apresentação); `role`/`cargo`/`privileges` já existem.

**Testing**: pytest (backend — `tests/test_auth_routes.py` para `registration-options`; `tests/test_identidade_cargos_models.py`/governança para `DEPARTAMENTOS` e defaults de cargo); validação de UI no navegador (Princípio VII, critério do dono) para as 4 histórias.

**Target Platform**: Web (PWA) — Vercel (frontend) + Docker/Nginx no VPS (backend).

**Project Type**: Web application (frontend React + backend FastAPI).

**Performance Goals**: sem impacto percetível. As leituras adicionais são: `registration-options` (público, já chamado na inscrição) e `governance/structure` no `EditUserModal` (cacheado por TanStack Query, `staleTime` padrão). Nenhum novo stream/polling.

**Constraints**: manter intactos rate-limit (`3/hour`), Turnstile e honeypot do `register` público (FR-017). `department` continua opcional e compatível com registos legados (FR-016). Design neutral-led (Princípio V): o botão «Aplicar predefinições do cargo» é **secundário** (não é o primário positivo Floresta da vista — esse é «Guardar»). Backend tocado ⇒ release `develop→main` **exige Via B**.

**Scale/Scope**: ≤ algumas centenas de sócios. 2 ficheiros backend + 5 ficheiros frontend + testes.

## Constitution Check

*GATE: avaliado contra `.specify/memory/constitution.md` v1.0.0.*

| Princípio | Avaliação |
|-----------|-----------|
| **I. Simplicity First** | ✅ Tudo aditivo: 1 constante, 1 campo extra no payload de opções, 3 rótulos, 1 dropdown reutilizada em 3 sítios, 1 botão. Reutiliza `privilegeLabel()`, `CARGO_DEFAULTS` e `governance_structure()` já existentes. Sem novo endpoint, sem novo modelo, sem flags/shims, sem migração. |
| **II. Root-Cause Discipline** | ✅ US1 corrige na origem (mapa de rótulos + helper com fallback), não por remendo célula-a-célula. `DEPARTAMENTOS` numa fonte única. |
| **III. RBAC + Audit** | ✅ Sem endpoint protegido novo e sem write novo ⇒ sem novo audit log. `registration-options` mantém-se **público** (só ganha um campo); `governance/structure` mantém-se **autenticado**. Sem SQL cru. O botão de US4 só **pré-preenche o formulário** no cliente — o gravar continua a passar pelo fluxo `UserAdminUpdate` existente (com o seu audit). |
| **IV. Language** | ✅ User-facing PT (rótulos dos privilégios, «Função no Sistema», nomes de departamentos, «Aplicar predefinições do cargo», «Outro»). Identificadores EN/domínio (`DEPARTAMENTOS`, `privilegeLabel`, `role_default`). Chaves de privilégio/role/cargo **não** renomeadas (FR fora de âmbito). |
| **V. Design System** | ✅ Dropdown de departamento e seletor de função reutilizam o `<select>` já usado nestes forms (mesmas classes). Botão «Aplicar predefinições do cargo» = **secundário** neutro (`border-[#D1D5DB]`), nunca Carmesim-positivo nem Floresta (o primário positivo da vista é «Guardar»). Sem cor nova, sem dark mode. |
| **VI. GitFlow + Via B** | ✅ `feature/016-… → develop`. Backend tocado (`models.py`, `auth_routes.py`) ⇒ release `develop→main` **exige Via B** (`docs/runbook-deploy-backend-via-b.md`). Frontend via Vercel. |
| **VII. Verification Before Done** | ✅ Backend: pytest (opções devolvem `departamentos`; `DEPARTAMENTOS` não-vazia; defaults de cargo inalterados). Frontend: validação no navegador das 4 histórias (dono) — inscrição pública (dropdown+Outro), convite (4 roles), edição (12 rótulos, botão, departamento legado preservado). |

**Resultado: PASS — zero violações.** Sem entradas em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/016-privilegios-cargo-departamento/
├── spec.md              # Especificação (já existe)
├── plan.md              # Este ficheiro
├── research.md          # Decisões de desenho (Fase 0)
├── data-model.md        # Entidades/constantes envolvidas (Fase 1)
├── contracts/
│   ├── registration-options.md   # Contrato aditivo do endpoint público de opções
│   └── ui-behaviors.md           # Contratos de UI (rótulos, dropdown+Outro, botão de defaults)
├── quickstart.md        # Cenários de validação ponta-a-ponta
├── checklists/
│   └── requirements.md  # (já existe)
└── tasks.md             # (gerado por /speckit-tasks — NÃO por este comando)
```

### Source Code (repository root)

```text
backend/
├── models.py            # EDITADO — + DEPARTAMENTOS (junto a CARGOS_DECLARADOS)
├── routes/
│   └── auth_routes.py   # EDITADO — registration_options() devolve {cargos, departamentos}
└── tests/
    ├── test_auth_routes.py            # EDITADO/NOVO — assert registration-options inclui departamentos
    └── test_identidade_cargos_models.py  # EDITADO — assert DEPARTAMENTOS não-vazia / estável

frontend/src/
├── lib/
│   └── cargoLabels.js               # EDITADO — +3 rótulos de privilégio
├── pages/private/usuarios/
│   ├── tokens.js                    # EDITADO — + DEPARTAMENTOS (conjunto estável, junto a ROLES/STATUSES)
│   ├── InviteModal.js               # EDITADO — role: 4 opções via ROLES/ROLE_LABELS + rótulo «Função no Sistema»; departamento = dropdown+Outro
│   └── EditUserModal.js             # EDITADO — privilegeLabel(); departamento dropdown+Outro; botão «Aplicar predefinições do cargo»
└── pages/public/
    └── CriarContaPage.js            # EDITADO — departamento = dropdown+Outro (opções via registrationAPI.options() + fallback)
```

**Structure Decision**: Web application (Opção 2). US1/US3/US4 são frontend puro; US2 é frontend + 2 toques aditivos no backend. As quatro histórias são independentes e testáveis isoladamente; partilham o mesmo branch.

## Design Detail

### US1 — Privilégios legíveis (frontend)

- `frontend/src/lib/cargoLabels.js` — acrescentar ao `PRIVILEGE_LABELS` (linha 12-22):
  - `emit_cf_parecer: 'Emitir Parecer (Conselho Fiscal)'`
  - `send_comunicados: 'Enviar Comunicados'`
  - `comunicar_intra_orgao: 'Comunicar entre Órgãos'`
  - O helper `privilegeLabel()` (linha 25) já existe e já faz fallback `|| priv`.
- `frontend/src/pages/private/usuarios/EditUserModal.js:179` — trocar `{PRIVILEGE_LABELS[priv]}` por `{privilegeLabel(priv)}` e ajustar o import (linha 12) para incluir `privilegeLabel`. Garante que qualquer privilégio futuro sem rótulo mostra a chave em vez de célula vazia (FR-002).

### US2 — Departamento como lista suspensa (backend aditivo + frontend)

**Backend (fonte única + exposição):**
- `backend/models.py` — nova constante `DEPARTAMENTOS` (9 valores, ver data-model), colocada junto a `CARGOS_DECLARADOS` (linha ~324). É uma etiqueta organizacional (não governança), por isso **não** vai para `governance.py` (que, por contrato, não importa de `models` — evita ciclo).
- `backend/routes/auth_routes.py:155-159` — `registration_options()` passa a devolver `{"cargos": CARGOS_DECLARADOS, "departamentos": DEPARTAMENTOS}` (aditivo; import de `DEPARTAMENTOS`). Mantém-se **público** e sem custo (a inscrição já o chama).
- **Sem enforcement de enum** no `department`: como «Outro» permite texto livre, e para não invalidar registos legados, o backend mantém `department` como string livre (validação só de comprimento, já existente). (Princípio I.)

**Frontend público — `CriarContaPage.js`:**
- Substituir o `<Input>` de departamento (linhas 156-168) por um `<select>` alimentado por `departamentos` (de `registrationAPI.options()`, com um `DEPARTAMENTOS_FALLBACK` local à imagem de `CARGOS_FALLBACK`), com uma opção final **«Outro»**.
- Ao escolher «Outro», revelar um `<Input>` de texto livre. Como o form usa react-hook-form, gerir a escolha num estado local `deptChoice`; no `onSubmit`, resolver `department = deptChoice === 'Outro' ? values.department_other : deptChoice` e enviar em `registrationAPI.submit`. Campo **opcional** (estado inicial «Selecionar…» → `department` vazio é aceite). Sem alteração ao `registrationSchema` (department continua opcional).

**Frontend admin — `InviteModal.js` e `EditUserModal.js`:**
- `tokens.js` — adicionar `export const DEPARTAMENTOS = [...]` (mesmo conjunto), consistente com o ficheiro já albergar `ROLES`/`STATUSES` (conjuntos pequenos e estáveis).
- Substituir o `<Input>` de departamento (`InviteModal.js:102-111`, `EditUserModal.js:220-227`) por um `<select>` (mesmas classes dos outros selects do form) alimentado por `DEPARTAMENTOS` + «Outro» → texto livre condicional.
- **Preservação de legado (FR-013)**: ao abrir a edição, se `editingUser.department` não estiver na lista e não for vazio, pré-selecionar «Outro» e mostrar o valor atual no campo de texto (não perder o valor).

### US3 — Função (role) completa no convite (frontend)

- `InviteModal.js:70-81` — substituir os 3 `<option>` fixos por `ROLES.map(...)` (de `tokens.js`, já com os 4) usando `ROLE_LABELS` (de `lib/cargoLabels.js`), e mudar o rótulo do campo de «Funcao» → «Função no Sistema» (linha 70). Importar `ROLES` e `ROLE_LABELS`. `EMPTY_INVITE.role` mantém-se `'socio'` (default).
- Backend: `InviteCreate.role` já aceita qualquer string e o fluxo de convite/aprovação já lida com `admin`; sem alteração.

### US4 — Botão «Aplicar predefinições do cargo» (frontend)

- `EditUserModal.js` — adicionar `useQuery` para `governanceAPI.structure()` (cacheado). Derivar a entrada do cargo do sócio: `structure.cargos.find(c => c.key === editingUser.cargo)`.
- Renderizar um botão **secundário** «Aplicar predefinições do cargo» junto à secção de Privilégios (linha ~147-152), visível apenas quando `editingUser.account_type !== 'technical'` **e** existe entrada de catálogo para `editingUser.cargo`.
- `onClick`: `setEditingUser({ ...editingUser, role: entry.role_default, privileges: [...entry.privileges_default] })`. Explícito; só atua no clique; o admin ajusta livremente antes de «Guardar» (FR-006). Nada é gravado até «Guardar» (fluxo existente).
- Edge (cargo com `privileges_default` vazio, ex. `ag_vice_presidente`/`socio`): o clique define privilégios vazios de forma explícita — reversível antes de guardar (documentado na spec).

## Complexity Tracking

> Sem violações constitucionais — secção não aplicável.
