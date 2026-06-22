# Implementation Plan: Landing page da plataforma de gestão de associações

**Branch**: `feature/landing-plataforma` (spec dir `004-plataforma-landing`) | **Date**: 2026-06-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-plataforma-landing/spec.md`

## Summary

Criar uma **landing page pública de produto** que apresenta o Portal ACCTA como um **sistema/plataforma de gestão de associações** reutilizável, e ligá-la através de um **link discreto no rodapé** partilhado do `PublicLayout`. A página é **frontend-only**, conteúdo estático, em tom **informativo e sóbrio** (sem CTA comercial forte), respeitando o sistema de design ACCTA e as regras editoriais do site público. Abordagem técnica: uma nova página em `frontend/src/pages/public/PlataformaPage.js`, registada como rota lazy em `App.js` dentro do `PublicLayout`, reutilizando `PageBanner`, secções com grelha, `card-technical`/`.animate-fade-up` e tokens de marca; mais uma entrada de link discreto no rodapé em `layouts/PublicLayout.js`.

## Technical Context

**Language/Version**: JavaScript (ES2021+), React 19 (JSX), Node 18+/Yarn para build.

**Primary Dependencies**: React 19, react-router-dom (rotas), Tailwind CSS 3, `lucide-react` (ícones), Framer Motion (disponível; padrão público usa `.animate-fade-up` em CSS). **Sem novas dependências npm** (evitar `yarn add` — penduram nesta máquina; ver [[frontend-dep-install-hangs]]).

**Storage**: N/A — conteúdo estático no componente; sem backend, sem DB, sem alterações de schema/modelos.

**Testing**: lint (`npx eslint src/ --ext .js,.jsx --max-warnings=60`) + `yarn build` + verificação manual no browser (mobile/desktop) conforme `quickstart.md`. Não há suite de testes de frontend automatizada para páginas públicas; verificação é manual/visual (Constituição VII).

**Target Platform**: Web (browsers modernos), site público servido pelo Vercel; rotas client-side do React.

**Project Type**: Web application (frontend only, neste feature).

**Performance Goals**: rota lazy-loaded; sem regressão percetível; imagens (se usadas) via padrões existentes (`mediaUrl()`/banner gerido) — preferir conteúdo estático/sem imagens pesadas para LCP saudável.

**Constraints**: PT-PT em todo o texto; só Tailwind (sem inline styles); sem dark mode; neutral-led com Floresta para ação positiva pontual e Carmesim como identidade; sem números/estatísticas não oficiais; sem CTA comercial forte.

**Scale/Scope**: 1 página pública nova + 1 link no rodapé + 1 registo de rota. ~2 ficheiros tocados (PublicLayout.js, App.js) + 1 ficheiro novo (PlataformaPage.js). Bem dentro do limite de 3 ficheiros (Constituição VI/§8).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Aplicabilidade | Veredito |
|-----------|----------------|----------|
| **I. Simplicity First** | Página de conteúdo estático, sem abstrações novas, sem estado de servidor. | ✅ PASS — reutiliza padrões existentes; nenhuma abstração prematura. |
| **II. Root-Cause Discipline** | Sem bugs em causa; feature nova. | ✅ N/A |
| **III. RBAC + Audit** | Página **pública**, sem endpoints, sem escritas, sem dados sensíveis. | ✅ N/A — nada protegido, nenhum write, nenhuma rota de backend. |
| **IV. Language Discipline** | Texto visível em PT-PT; identificadores do componente em EN genérico (`PlataformaPage` — `Plataforma` é domínio aceitável). | ✅ PASS |
| **V. Design System Authority** | Neutral-led, Floresta/Carmesim/Grafite, Open Sans, sem dark mode, só Tailwind. Aplicar skill `frontend-design`. | ✅ PASS (gate verificado na revisão de código). |
| **VI. GitFlow + Confirmação** | Trabalho em `feature/landing-plataforma` ⇒ PR para `develop`. Sem STOP conditions (sem DB, sem auth, sem CORS, sem email, sem `main`, ≤3 ficheiros). | ✅ PASS |
| **VII. Verification Before Done** | UI ⇒ exercitar no browser antes de "done"; lint + build verdes. | ✅ PASS (plano inclui verificação manual + quickstart). |

**Resultado**: PASS — nenhuma violação; tabela de Complexity Tracking não necessária.

## Project Structure

### Documentation (this feature)

```text
specs/004-plataforma-landing/
├── plan.md              # Este ficheiro (/speckit-plan)
├── research.md          # Phase 0 (/speckit-plan)
├── data-model.md        # Phase 1 (/speckit-plan) — "conteúdo da página", não dados de DB
├── quickstart.md        # Phase 1 (/speckit-plan)
├── contracts/           # Phase 1 (/speckit-plan) — contratos de UI (rota, footer, secções)
│   ├── route.md
│   └── ui-page.md
└── tasks.md             # Phase 2 (/speckit-tasks — NÃO criado por /speckit-plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── pages/
│   │   └── public/
│   │       └── PlataformaPage.js        # NOVO — landing page da plataforma (named export)
│   ├── layouts/
│   │   └── PublicLayout.js              # EDIT — link discreto no rodapé (bloco inferior ou coluna existente)
│   └── App.js                           # EDIT — import lazy + <Route path="/plataforma">
```

**Structure Decision**: Web application, alterações confinadas ao `frontend/`. A página segue a convenção das restantes páginas públicas (named export em `pages/public/`, registada em `App.js` envolvida por `<PublicLayout>`). Nenhum diretório novo é criado. Backend, base de dados e modelos ficam **intocados**.

#### Pontos de integração reais (apurados no Phase 0)

- **Rota**: `frontend/src/App.js` — imports lazy (~linhas 13–32) e bloco de rotas públicas em `AppRoutes()` (~linhas 117–133). Padrão: `<Route path="/plataforma" element={<PublicLayout><PlataformaPage /></PublicLayout>} />`.
- **Rodapé**: `frontend/src/layouts/PublicLayout.js` (~linhas 132–172). Grelha de 4 colunas + barra inferior (copyright + "Política de Privacidade", ~linhas 167–170). O link discreto entra na barra inferior (estilo `text-white/50 hover:text-white text-xs`) **ou** numa coluna existente ("Links Rápidos" / "Área Reservada").
- **Página**: espelhar `SobrePage.js` — `PageBanner` (badge/título/subtítulo), secções `py-12 sm:py-20`, grelha `lg:grid-cols-2`, `card-technical card-hover`, `.animate-fade-up`, tokens `grafite`/`carmesim`/`floresta`, ícones `lucide-react`.

## Complexity Tracking

> Sem violações constitucionais — secção não aplicável.
