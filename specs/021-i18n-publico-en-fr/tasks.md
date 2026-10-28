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

- [x] T011 [P] Home + `home/*` (ns `home`)
- [x] T012 [P] `content/cta` → `locales/{en,fr}/cta.js` (mesma forma)
- [x] T013 [P] Sobre (+ aviso corpos sociais), Profissão + componentes (ns `sobre`, `profissao`)
- [x] T014 [P] Plataforma, Benefícios, Validador, Contactos
- [x] T015 [P] Notícias (+ detalhe c/ aviso), Galeria, Publicações, Eventos
- [x] T016 [P] Login, Criar Conta, Recuperar/Redefinir palavra-passe, Configurar Conta + seletor nas páginas sem layout + Turnstile `language`

## F3 — Verificação (Princípio VII)

- [x] T017 Suíte frontend completa + eslint + `craco build` (chunks EN/FR separados)
- [x] T018 Grep de literais PT residuais nas páginas públicas
- [x] T019 Quickstart em navegador (cenários 1–11)
- [x] T020 Code review do diff

## F4 — Go-live (STOP)

- [ ] T021 Revisão humana EN/FR (FR-020) → remover marca `REVISÃO HUMANA PENDENTE`
- [ ] T022 PR feature→develop, release→main (confirmação do dono), validação em prod (Vercel)

## Review (2026-10-27)

- Suíte frontend 24 suites / 161 testes ✓; eslint 0 erros; `craco build` ✓ (chunks `i18n-en` 13.8 KB / `i18n-fr` 15 KB; main +12 KB).
- Validação em Chrome headless contra o dev server (o preview Vercel está protegido): `/fr/sobre` → `lang=fr`, título/descrição FR, 4 `hreflang`, shell FR, aviso «Ce contenu est en portugais»; `/en/xyz` → 404 EN; `/sobre` com `--lang=fr` → redireciona p/ FR; `--lang=pt-PT` → PT `pt-CV`; Googlebot → fica PT; `/dashboard` sem sessão → `/en/login`. Varrimento das 16 páginas em EN/FR: só nomes próprios/dados da API em PT. Mobile 500px: seletor visível, sem overflow.
- Não validado interativamente: clique no seletor (lógica coberta por `withLocale`/`stripLocale` testados); área privada autenticada (código não tocado; `PrivateLayout.test` ✓).
- Code review: 0 CRITICAL; W1 (interceptor 401 em `/en`,`/fr`) e S3 (meta description criada) corrigidos em `e548c4d`.
