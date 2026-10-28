# Implementation Plan: Site Público em EN e FR (i18n)

**Branch**: `feature/021-i18n-publico-en-fr` | **Date**: 2026-07-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/021-i18n-publico-en-fr/spec.md`

## Summary

Oferecer as 16 páginas públicas em PT (canónico), EN e FR, com prefixo de URL `/en`, `/fr`
(slugs PT mantidos), detecção na 1.ª visita, seletor com rótulos nativos que preserva a
página, `hreflang`/`<title>`/`<meta description>`/`lang` por idioma, 404 traduzida e aviso
«conteúdo em português» nas rotas de conteúdo dinâmico. **Frontend-only, zero
dependências novas**: módulo próprio `src/i18n/` (provider + `t()` + `lp()` + dicionários
JS; EN/FR em chunks lazy), rotas públicas declaradas uma vez e montadas para os 3
prefixos. Área privada, emails, PDFs e backend intactos. Pré-requisito: emenda
constitucional v1.2.0 (Princípio IV). Ver [research.md](research.md).

## Technical Context

**Language/Version**: JavaScript (React 19, CRA via Craco)

**Primary Dependencies**: react-router-dom 7, date-fns 4 (locales `ptBR`/`enUS`/`fr` já
incluídos), shadcn/ui `DropdownMenu` existente — **nenhuma dependência nova** (R1)

**Storage**: `localStorage['accta.locale']` (preferência); sem backend/BD

**Testing**: Jest + Testing Library (`craco test`); validação manual em navegador
(quickstart)

**Target Platform**: browsers modernos + PWA; Vercel (rewrite SPA já cobre `/en/*`, `/fr/*`)

**Project Type**: web application (só a parte `frontend/`)

**Performance Goals**: sem flash PT em `/en`/`/fr` (SC-002); PT sem custo extra de rede;
área privada não carrega bytes EN/FR (R5)

**Constraints**: PT canónico indexável (crawlers nunca redirecionados, R3); 0 regressões na
área privada (SC-008); tradução humana revista antes do go-live (FR-020)

**Scale/Scope**: 17 ficheiros de página + `home/*` + `PublicLayout` (~4 750 linhas),
estimativa ~500–700 chaves por locale, ~45 links internos

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Estado | Nota |
|-----------|--------|------|
| I. Simplicity First | ✅ | zero deps; módulo i18n ~80 linhas; sem TMS; 404 só sob prefixo |
| II. Root-Cause | ✅ | n/a (feature) |
| III. RBAC + Audit | ✅ | sem backend; nenhuma superfície protegida tocada |
| IV. Language Discipline | ⚠️ **viola sem emenda** | UI pública em EN/FR → **emenda MINOR v1.2.0 é a 1.ª tarefa** (R15); justificado em Complexity Tracking. Identificadores/comentários continuam conforme |
| V. Design System | ✅ | seletor e aviso reutilizam primitivas/tokens do `frontend-design` |
| VI. GitFlow + STOPs | ✅ | feature→develop; STOPs: merge da emenda (revisão), go-live após revisão humana, release→main |
| VII. Verification | ✅ | quickstart com 11 cenários em navegador + teste de paridade |

**Re-check pós-design**: mantém-se. O desenho não introduziu backend, deps nem tokens.
Dois desvios menores do spec registados para decisão do dono (não da constituição):
R4 (`<html lang>` PT fica `pt-CV`) e R10 (sem 404 PT; fallback global mantém redirect).

## Project Structure

### Documentation (this feature)

```text
specs/021-i18n-publico-en-fr/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/i18n-ui-contract.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code

```text
.specify/memory/constitution.md          # emenda v1.2.0 (F0)
CLAUDE.md                                # §Conventions reconciliado (F0)

frontend/src/
├── i18n/                                # NOVO
│   ├── index.js                         # I18nProvider, useI18n, SUPPORTED_LOCALES, detecção
│   ├── usePageMeta.js                   # title/description/lang/hreflang
│   ├── pending.js
│   ├── locales/{pt,en,fr}.js
│   └── __tests__/{parity,i18n}.test.js
├── components/
│   ├── LanguageSwitcher.js              # NOVO
│   ├── PortugueseContentNotice.js       # NOVO
│   └── Turnstile.js                     # + opção language
├── pages/public/
│   ├── NotFoundPage.js                  # NOVO
│   ├── *.js, home/*.js                  # literais → t(), links → lp(), usePageMeta
├── layouts/PublicLayout.js              # nav/rodapé → t(), monta LanguageSwitcher
├── content/cta*                         # constantes PT → chaves
└── App.js                               # PUBLIC_ROUTES × ['', '/en', '/fr'] + 404 por prefixo
```

**Structure Decision**: só `frontend/` (+ constituição/CLAUDE.md). Sem `backend/` ⇒ release
sai pela Vercel, **sem Via B**.

## Phasing (input para `/speckit-tasks`)

- **F0 — Governança**: emenda constitucional v1.2.0 + CLAUDE.md (PR próprio, revisão do dono).
- **F1 — Infra (US1/US4 base)**: `src/i18n/` + testes; `PUBLIC_ROUTES` em `App.js`;
  `usePageMeta`; `LanguageSwitcher`; `NotFoundPage`; detecção/redirect; `PublicLayout`
  traduzido. Entregável: navegação em `/en`/`/fr` funciona com o shell traduzido.
- **F2 — Páginas (US1/US2)**: migrar as 16 páginas (+ `home/*`, `content/cta`) para
  `t()`/`lp()`/`formatDate`, com rascunho EN/FR; aviso de conteúdo dinâmico; Turnstile
  `language`. Paralelizável por página (ficheiros distintos; só os dicionários são
  partilhados → cada página no seu namespace).
- **F3 — Verificação**: quickstart completo em navegador, grep de literais, build.
- **F4 — Go-live (STOP)**: revisão humana EN/FR → release `develop→main` (Vercel).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Princípio IV (UI em EN/FR) | requisito central do dono: público internacional (IFATCA/ICAO, diáspora francófona) | não traduzir = não entregar a feature; resolve-se por emenda MINOR v1.2.0 restrita ao site público, não por exceção ad-hoc |
