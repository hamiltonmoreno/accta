# Tasks — Spec 021: Site público em EN e FR

Ordem: F0 → F1 → F2 (paralelo por página) → F3 → F4 (STOP).

## F0 — Governança

- [x] T001 Emenda constitucional v1.1.0 → v1.2.0 (Princípio IV) em `.specify/memory/constitution.md`
- [x] T002 Reconciliar `CLAUDE.md §Conventions` + `.claude/rules/frontend.md §UI Text`

## F1 — Infra (US1/US3/US4)

- [x] T003 `src/i18n/index.js` — provider, `t`/`lp`/`cta`, detecção, persistência (R1–R3, R5, R6)
- [x] T004 `src/i18n/usePageMeta.js` — title/description/`lang`/hreflang (R4)
- [x] T005 `src/i18n/dates.js` — `useFormatDate` (R11; separado p/ não arrastar o ESM do date-fns p/ Jest)
- [x] T006 Dicionários por namespace `locales/{pt,en,fr}/<ns>.js` + `pending.js`
- [x] T007 `LanguageSwitcher`, `PortugueseContentNotice`, `NotFoundPage` (R9, R10, R12)
- [x] T008 `App.js`: `PUBLIC_ROUTES` × `''`/`/en`/`/fr`, `LocaleGate`, 404 por prefixo, `I18nProvider`
- [x] T009 `PublicLayout` traduzido + seletor (desktop e mobile)
- [x] T010 Testes `i18n.test.js` (caminhos, detecção, crawler, fallback) + `parity.test.js`

## F2 — Páginas (US1/US2), [P] = paralelo

- [ ] T011 [P] Home + `home/*` (ns `home`)
- [ ] T012 [P] `content/cta` → `locales/{en,fr}/cta.js` (mesma forma)
- [ ] T013 [P] Sobre (+ aviso corpos sociais), Profissão + componentes (ns `sobre`, `profissao`)
- [ ] T014 [P] Plataforma, Benefícios, Validador, Contactos
- [ ] T015 [P] Notícias (+ detalhe c/ aviso), Galeria, Publicações, Eventos
- [ ] T016 [P] Login, Criar Conta, Recuperar/Redefinir palavra-passe, Configurar Conta + seletor nas páginas sem layout + Turnstile `language`

## F3 — Verificação (Princípio VII)

- [ ] T017 Suíte frontend completa + eslint + `craco build` (chunks EN/FR separados)
- [ ] T018 Grep de literais PT residuais nas páginas públicas
- [ ] T019 Quickstart em navegador (cenários 1–11)
- [ ] T020 Code review do diff

## F4 — Go-live (STOP)

- [ ] T021 Revisão humana EN/FR (FR-020) → remover marca `REVISÃO HUMANA PENDENTE`
- [ ] T022 PR feature→develop, release→main (confirmação do dono), validação em prod (Vercel)
