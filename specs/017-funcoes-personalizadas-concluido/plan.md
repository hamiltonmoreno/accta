# Implementation Plan: Funções personalizadas com privilégios à medida

**Branch**: `017-funcoes-personalizadas` | **Date**: 2026-07-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/017-funcoes-personalizadas/spec.md`

## Summary

O admin passa a poder criar «funções personalizadas» — pacotes nomeados de privilégios (ex.: «Coordenador de Eventos» = gerir eventos + documentos) — e aplicá-las a sócios no seletor «Função no Sistema» (edição e convite). Semântica de **ligação viva** (editar a função propaga a todos os sócios que a têm) e base sempre «sócio» (decisões do dono Q1/Q2). Implementação por **denormalização com propagação**: o utilizador guarda `custom_role_id` + `privileges` materializados; editar a função faz `update_many` sobre `users`. O RBAC em runtime não muda uma linha — zero regressão para as 4 funções fixas.

## Technical Context

**Language/Version**: Python 3.11 (FastAPI) + React 19

**Primary Dependencies**: FastAPI, asyncpg (DAO Mongo-compatível em `database.py`), Pydantic v2; frontend React 19 + Tailwind + shadcn/ui + TanStack Query. **Zero dependências novas.**

**Storage**: PostgreSQL (Supabase) — nova coleção `custom_roles` (tabela `(pk, doc jsonb)` via `COLLECTIONS`/`ensure_schema()`); campo aditivo `custom_role_id` nos docs de `users`.

**Testing**: pytest (unit, `tests/conftest.py` com `mock_db` — coleção `custom_roles` NÃO está pré-wired, ligar em-teste); eslint + `craco build` no frontend. CI billing-locked → validar localmente.

**Target Platform**: web (backend Nginx/Supervisord via Via B; frontend Vercel)

**Project Type**: web application (backend + frontend)

**Performance Goals**: n/a — operações administrativas raras; propagação via 1 `update_many` (sem N+1); listagem com contagens via 1 agregação sobre `users`.

**Constraints**: sem migração de dados; campos Pydantic aditivos/Optional (não parte docs existentes); hot path de auth (`get_current_user`/`has_privilege`) intocado; PT em todo o texto de UI/erros.

**Scale/Scope**: unidades de funções personalizadas, ~dezenas de sócios; 1 route module novo, 2 modelos novos + 2 campos aditivos, 1 componente de gestão novo + retoques em 2 modais.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| I. Simplicity First | ✅ Zero deps novas; denormalização evita tocar no RBAC; sem abstrações novas (padrão CRUD igual aos módulos existentes). |
| II. Root-Cause Discipline | ✅ n/a (feature nova); a regra de destaque (D3) evita a raiz do drift função↔privilégios. |
| III. RBAC + Audit | ✅ CRUD admin-only com `create_audit_log` em todas as escritas; atribuição herda o audit before/after de `PATCH /users/{id}`; sem raw SQL — coleção nova via `COLLECTIONS`/`ensure_schema()`; sem `create_index` em rotas. |
| IV. Language Discipline | ✅ UI/`detail` em PT; identificadores EN (`custom_roles`, `custom_role_id`); comentários PT. |
| V. Design System | ✅ UI nova segue `frontend-design` (neutral-led; 1 botão positivo Floresta/vista; destrutivo Carmesim outline + confirm dialog). |
| VI. GitFlow + Confirmation | ✅ feature branch → develop; release p/ main só com confirmação; toca `backend/` ⇒ deploy Via B. |
| VII. Owner validation | ✅ validação do dono no navegador antes de fechar. |

**Pós-Phase 1 re-check**: sem violações; Complexity Tracking vazio.

## Project Structure

### Documentation (this feature)

```text
specs/017-funcoes-personalizadas/
├── plan.md              # Este ficheiro
├── research.md          # Phase 0 — decisões D1–D6
├── data-model.md        # Phase 1 — entidades e campos
├── quickstart.md        # Phase 1 — guia de validação
├── contracts/
│   └── custom-roles-api.md  # Phase 1 — contrato dos endpoints
└── tasks.md             # Phase 2 (/speckit-tasks — não criado aqui)
```

### Source Code (repository root)

```text
backend/
├── database.py                  # +"custom_roles" em COLLECTIONS (ensure_schema cria a tabela)
├── models.py                    # +CustomRole/CustomRoleCreate/CustomRoleUpdate; +custom_role_id em UserBase/UserAdminUpdate/InviteCreate
├── routes/
│   ├── custom_roles.py          # NOVO — CRUD /api/admin/custom-roles (+ registo em server.py)
│   ├── users.py                 # PATCH /users/{id}: atribuição/destaque de custom_role_id
│   ├── admin.py                 # invite: aceitar custom_role_id; cargos promote/demote/transfer: limpar custom_role_id
│   └── eleicoes.py              # proclamação: limpar custom_role_id (D5)
└── tests/
    └── test_custom_roles.py     # NOVO — CRUD, propagação, delete bloqueado, atribuição/destaque

frontend/src/
├── utils/api.js                 # +grupo customRolesAPI (list/create/update/remove)
├── lib/cargoLabels.js           # (reutiliza privilegeLabel; sem mudanças ou mínimas)
├── pages/private/usuarios/
│   ├── CustomRolesManager.js    # NOVO — gestão (lista+contagens, criar/editar/eliminar)
│   ├── EditUserModal.js         # seletor com grupo «Funções personalizadas»; privilégios read-only quando ativa; aviso no botão de predefinições
│   └── InviteModal.js           # seletor idem no convite
└── pages/private/AdminUsuariosPage.js  # entrada para o CustomRolesManager + payload custom_role_id
```

**Structure Decision**: web app existente (backend FastAPI + frontend React). Um domínio novo → um route module novo (`routes/custom_roles.py`), padrão do projeto. A atribuição reutiliza os endpoints existentes de utilizador/convite (campos aditivos), sem endpoints de atribuição dedicados.

## Design (como as decisões de research se ligam)

1. **Coleção `custom_roles`** (D2): `{id, name, description, privileges[], created_by, created_at, updated_at}`. Nome único por normalização (trim+casefold) validado na rota; recusa também colisão com os 4 rótulos fixos (edge case da spec).
2. **Ligação viva por denormalização** (D1): `PATCH /admin/custom-roles/{id}` com `privileges` alterados → `update_many({"custom_role_id": id}, {"$set": {"privileges": novos}})` + notificação «Perfil Atualizado» aos afetados. RBAC runtime intocado.
3. **Atribuição/destaque** (D3): em `PATCH /users/{id}`, payload com `custom_role_id` valida existência e sobrepõe `role="socio"` + `privileges=<da função>`; payload com `role` ou `privileges` explícitos (sem `custom_role_id`) limpa `custom_role_id` (destaque). Cargos (`/admin/cargos`, proclamação) e «Aplicar predefinições do cargo» também destacam (D5) — aviso prévio na UI (FR-010).
4. **Convite** (D4): `InviteCreate.custom_role_id` opcional; convidado nasce `role="socio"` + privilégios da função + `custom_role_id`. O contrato 422 para roles desconhecidas mantém-se (decisão do dono da spec 016 — intocada).
5. **Frontend**: seletor «Função no Sistema» nos 2 modais ganha `<optgroup>` «Funções personalizadas» (dados de `GET /admin/custom-roles` via TanStack Query, admin-only); com função personalizada selecionada, checkboxes de privilégios mostram os da função em read-only. Gestão num componente próprio acessível da página de utilizadores. Menu/acessos (`visibility.js`/`AuthContext`) não mudam — continuam a ler `privileges` materializados de `/auth/me`.
6. **Eliminação protegida** (FR-006): `DELETE` → 409 com contagem se em uso; UI usa confirm dialog destrutivo (Carmesim) só quando elegível.

## Complexity Tracking

*(vazio — sem violações à constituição)*
