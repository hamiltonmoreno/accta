# Implementation Plan: Consolidação do modelo de acessos e identidade do utilizador

**Branch**: `feature/018-consolidacao-acessos` | **Date**: 2026-07-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/018-consolidacao-acessos/spec.md` (decisões
D1–D7 do dono confirmadas 2026-07-03)

## Summary

Reduzir os níveis de acesso a **{admin, socio}** e fazer dos **privilégios a única fonte de
acesso granular**, com as **funções personalizadas (spec 017) como mecanismo canónico de
empacotamento** — os antigos financeiro/moderador viram funções seed e os utilizadores
existentes migram com **equivalência exata** de acesso. Em **duas fases (D6)**:
**F1 = higiene invisível** (helper único + tabela canónica módulo→privilégio + matriz de
testes de equivalência; zero mudança de comportamento) que serve de **gate e de baseline
verificável** para **F2 = modelo + migração + UI** (enum, defaults de cargo, tradução de
API por 1 release, seletor «Nível de acesso», secções «Acesso ao sistema» vs «Identidade
associativa», migração de dados em prod auditada e reversível).

## Technical Context

**Language/Version**: Python 3.11 (FastAPI) + React 19 — stack existente, zero deps novas

**Primary Dependencies**: DAO Mongo-compatível (`database.py`), `auth.py`
(`has_role_or_privilege`), `permissions.py`, `governance.py` (fonte única de
cargos/privilégios), mecânica de funções personalizadas da spec 017

**Storage**: PostgreSQL (Supabase) — sem mudança de schema; migração de DADOS (valores de
`role` em `users` + 2 docs seed em `custom_roles`)

**Testing**: pytest unit (mock_db) — novo `tests/test_access_matrix.py` como baseline F1 e
prova de equivalência F2; suíte inteira como guarda de regressão

**Target Platform**: portal web existente (backend Via B + frontend Vercel)

**Project Type**: web app (backend + frontend) — mudança transversal de RBAC

**Performance Goals**: n/a (sem novas queries quentes; migração é one-off)

**Constraints**: equivalência EXATA de acesso pré/pós (SC-001); F1 sem qualquer mudança
visível; migração reversível (backup + mapa por utilizador); histórico intacto (FR-010)

**Scale/Scope**: prod real com poucos utilizadores (pós-reset go-live) — a janela de
migração é trivial; a superfície de código é que é larga (~28 checks inline backend, ~12
ficheiros frontend com referências a roles antigos — inventário em research.md R1)

## Constitution Check

*Constituição v1.0.0 (2026-06-20).*

| Princípio | Avaliação |
|---|---|
| I Simplicity First | ✅ O objetivo É remover redundância; F1 não acrescenta abstração nova além da tabela canónica (que substitui 28 checks avulsos) |
| II Root-Cause | ✅ Ataca a causa (4 caminhos p/ o mesmo acesso), não os sintomas |
| III RBAC + Audit | ✅ Reforçado: helper único + audit da migração/tradução; `permissions.py`/`governance.py` continuam as fontes |
| IV Language | ✅ UI/msgs PT; identificadores EN; sem bulk-rename de jsonb keys (`role` mantém o nome) |
| V Design System | ✅ UI nova segue frontend-design (secções neutras; sem cor nova) |
| VI GitFlow + STOP | ⚠️ **3 STOPs ativos**: migração de dados em prod (#1), mudança de semântica de modelo Pydantic (#5 — enum de role), merge a main (#7). Mitigação: decisões D1–D7 já são a autorização de desenho; a EXECUÇÃO da migração em prod e a release têm confirmação explícita do dono no momento (F2-gate) |
| VII Verification | ✅ Matriz de equivalência ANTES de mexer (baseline) + quickstart com dry-run de migração + validação do dono no navegador |
| **Stack & Data Constraints** | ⚠️ **A constituição fixa «Roles {admin, financeiro, moderador, socio}»** — a F2 inclui emenda `docs(constitution): amend to v1.1.0` (R9) reconciliada com CLAUDE.md/rules na mesma release. Sem a emenda, a F2 violaria a constituição — é tarefa obrigatória, não opcional |

**Gate**: PASS para F1 (nenhuma violação). F2 condicionada a: F1 verde + emenda
constitucional incluída + confirmações STOP no momento da migração/release.

## Fases (D6: F1 é gate da F2)

### Fase 1 — Higiene invisível (zero mudança de comportamento)

1. **Matriz baseline**: escrever `tests/test_access_matrix.py` ANTES de tocar em qualquer
   check (R10): perfis (admin, financeiro, moderador, socio, socio+priv relevante,
   view_finances_readonly, técnico) × módulos (finances view/manage, users, events,
   documents, benefits, moderação, comunicados, audit, ranking, regulamentos) → verde no
   código ATUAL. Este ficheiro é o contrato de equivalência de toda a spec.
2. **Tabela canónica** `MODULE_ACCESS` em `governance.py` (data-model.md) — documenta
   módulo→privilégio(+legacy_roles); alimenta a matriz.
3. **Unificação**: todos os checks passam por `has_role_or_privilege` (ou helpers de
   domínio que o usam): eliminar os ~28 inline (R1), absorver `permissions.user_can`
   (mantém-se como alias fino ou remove-se — decidir no diff), corrigir `documents.py:19`.
   `can_view_finances`/`can_manage_finances` mantêm-se (semântica composta), reescritos
   sobre a tabela. Zero mudança nos resultados — a matriz de 1. corre INALTERADA.
4. **Saída/gate**: suíte inteira verde + matriz verde sem edições + grep sem checks fora
   do helper. F1 é mergeável e releasable sozinha (invisível) — pode ir em release própria
   para reduzir o risco da F2.

### Fase 2 — Modelo + migração + UI (após F1 verde)

**Backend**
1. `governance.py`: defaults de cargo (R7/D3); `MODULE_ACCESS` perde `legacy_roles` no fim.
2. Enum + tradução (R6/D4): validação `role ∈ {admin, socio}` em `admin.py` (invite) e
   `users.py` (PATCH) com `_LEGACY_ROLE_MAP` → socio+seed, auditado; mensagens PT.
3. Seeds + migração: `scripts/migrate_roles_018.py` (dry-run/apply; cria seeds «Financeiro»
   /«Moderador» com privilégios derivados da MATRIZ F1 (R4); migra users pela regra R3
   (⊆ seed → função; extras → privilégios diretos); backup JSON + audit por utilizador).
4. `helpers.py`: `_ELEVATED_ROLES` → alerta por admin/privilégios sensíveis (R8).
5. `custom_roles.py`: `_RESERVED_NAMES` sem financeiro/moderador (R5).
6. Matriz atualizada deliberadamente: o diff da matriz F1→F2 é a lista exata de mudanças
   (revisável pelo dono); testes novos p/ tradução, migração (regra R3) e alerta R8.
7. **Emenda constitucional v1.1.0** (R9) no mesmo PR.

**Frontend**
8. `AuthContext.js`: `isFinanceiro`/`isModerador` derivados de privilégios (compat de
   transição), `canManageFinances` só por privilégio; `nav/visibility.js` + `App.js`
   `ProtectedRoute` → `allowedPrivileges` (o suporte já existe).
9. Seletor «Nível de acesso» (D2) em EditUserModal/InviteModal (2 níveis + funções);
   `tokens.js` ROLES=['admin','socio']; FiltersBar (filtro por nível + por função?
   mínimo: nível); `cargoLabels.js`.
10. Modal em 2 secções (US3): «Acesso ao sistema» (nível, função, privilégios c/ origem
    função/manual) e «Identidade associativa» (cargo, categoria, departamento + nota
    «organizacional — não altera acessos», D5).
11. Conteúdo de Ajuda (`content/ajuda/*.js`): atualizar texto dos perfis.

**Release/migração (STOPs do dono no momento)**
12. Release develop→main + deploy Via B; janela: backup → `migrate_roles_018.py --dry-run`
    em prod → confirmação do dono → `--apply` → teste decisivo (login ex-financeiro opera
    finanças; 0 docs com role legado).
13. Release seguinte (futura, 1 linha): remover `_LEGACY_ROLE_MAP` (D4 fase estrita).

## Project Structure

### Documentation (this feature)

```text
specs/018-consolidacao-acessos/
├── plan.md              # este ficheiro
├── research.md          # R1–R10 (inventário, regras de migração, seeds, emenda)
├── data-model.md        # users.role, seeds, defaults de cargo, MODULE_ACCESS, mapa migração
├── quickstart.md        # validação F1 + cenários 1–8 F2 (ambiente local isolado)
├── contracts/
│   └── api-changes.md   # PATCH /users, /admin/invite, /governance/structure, custom-roles
└── tasks.md             # /speckit-tasks (não criado por este comando)
```

### Source Code (repository root)

```text
backend/
├── governance.py            # F1: MODULE_ACCESS · F2: defaults de cargo (R7)
├── auth.py                  # F1: has_role_or_privilege único; can_*_finances sobre a tabela
├── permissions.py           # F1: user_can absorvido/alias
├── helpers.py               # F2: alerta de escalada R8
├── routes/                  # F1: ~28 checks inline → helper (12 ficheiros, R1)
│   ├── users.py             # F2: enum+tradução no PATCH
│   ├── admin.py             # F2: enum+tradução no invite
│   └── custom_roles.py      # F2: _RESERVED_NAMES (R5)
├── tests/test_access_matrix.py  # F1: baseline · F2: diff deliberado
└── scripts/migrate_roles_018.py # F2: dry-run/apply (repo /scripts)

frontend/src/
├── contexts/AuthContext.js      # F2: derivações por privilégio
├── lib/nav/visibility.js        # F2: visibilidade por privilégio
├── App.js                       # F2: ProtectedRoute → allowedPrivileges
├── pages/private/usuarios/{EditUserModal,InviteModal,tokens,FiltersBar}.js  # F2: D2/US3
├── lib/cargoLabels.js           # F2: rótulos
└── content/ajuda/*.js           # F2: texto

.specify/memory/constitution.md  # F2: emenda v1.1.0 (R9)
```

**Structure Decision**: web app existente; sem módulos novos — a spec REMOVE caminhos.
Único ficheiro novo de produção: `scripts/migrate_roles_018.py` + 1 ficheiro de testes.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 3 STOPs (Princípio VI: migração prod, semântica de modelo, main) | é o objeto da spec — mudar o modelo de acessos em produção | manter os 4 roles = manter os 4 caminhos redundantes que motivaram a spec; adiar a migração criaria um 5.º estado híbrido permanente |
| Release de transição com tradução (D4) — shim temporário que o Princípio I desaconselha | dono decidiu transição suave (D4); shim de 1 mapa, com remoção agendada e tracked (release seguinte) | rejeição imediata (422) partiria fluxos do próprio admin durante a janela de adoção |
