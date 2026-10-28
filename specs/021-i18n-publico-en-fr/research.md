# Research — Spec 021: Site público em EN e FR

Fundamentado no código real (`frontend/src/App.js`, `layouts/PublicLayout.js`,
`pages/public/**`, `public/index.html`, `public/sw.js`, `vercel.json`), 2026-07-14.

## Inventário (estado atual)

- **Sem biblioteca de i18n** nem de `<head>` (sem i18next, sem react-helmet). Títulos são
  definidos à mão: só `PlataformaPage.js:68` mexe em `document.title` no público.
- **Rotas públicas** declaradas uma a uma em `App.js:123-139`. 12 dentro de `PublicLayout`;
  **`/login`, `/forgot-password`, `/reset-password`, `/setup-account` NÃO usam
  `PublicLayout`** (layout próprio) → precisam de seletor de idioma à parte.
- **Fallback** `App.js:453`: `<Route path="*" element={<Navigate to="/" replace />} />` —
  **não existe página 404**; hoje qualquer rota desconhecida redireciona para a Home.
- **Volume**: 17 ficheiros de página (3 964 linhas) + `pages/public/home/*` (611 linhas) +
  `PublicLayout.js` (177 linhas, 13 links internos) + `content/cta` (constantes partilhadas).
  ~45 links internos (`to="/…"`) nas páginas públicas.
- **Datas**: `date-fns` + `ptBR` em `EventosPublicoPage`, `home/FeaturedEvent`,
  `home/NewsSection`, `NoticiaDetailPage`, `NoticiasPage`.
- **Turnstile** (`components/Turnstile.js:57`) usado em Login, CriarConta, ForgotPassword,
  Contactos — o widget aceita a opção `language`.
- **`index.html`**: `<html lang="pt-CV">`, `og:locale=pt_CV`.
- **Vercel**: rewrite catch-all `/(.*) → /index.html` ⇒ `/en/*` e `/fr/*` já são servidos
  sem alterar `vercel.json`.
- **Service worker**: navegações são network-first (`sw.js:54`) ⇒ nada a mudar.
- **Testes frontend**: `craco test` (Jest + Testing Library), 16 ficheiros `__tests__/`.

## Decisões

### R1 — Biblioteca de i18n → **módulo próprio mínimo, zero dependências**

- **Decision**: `src/i18n/` com `I18nProvider` (contexto), hook `useI18n()` → `{ locale, t,
  lp, formatDate }`, dicionários JS por locale. `t(key, vars)` com interpolação `{nome}`;
  sem pluralização (o conteúdo estático não a exige).
- **Rationale**: Princípio I; a necessidade é chave→string + interpolação. Memória
  `frontend-dep-install-hangs` (instalar deps pendura nesta máquina). ~80 linhas.
- **Alternatives**: `i18next` + `react-i18next` (padrão da indústria, ~40 KB, detetor de
  idioma, plurais) — rejeitado por excesso de funcionalidade e risco de install;
  `react-intl` — idem, API mais pesada (ICU).

### R2 — Locale vem do URL (fonte de verdade em runtime)

- **Decision**: `locale` derivado do 1.º segmento de `location.pathname` (`en`/`fr`, senão
  `pt`). As rotas públicas são declaradas **uma vez** num array e montadas para os prefixos
  `''`, `/en`, `/fr` (React Router v7 não suporta regex em params). `lp(path)` prefixa
  caminhos internos com o locale ativo.
- **Rationale**: FR-015/FR-018 (URL prevalece); determinístico p/ crawlers; sem estado
  duplicado entre storage e URL.
- **Alternatives**: `/:lang/*` com validação manual — aceita `/xx/…` e obriga a filtrar;
  estado em contexto sem URL — viola D1.

### R3 — Detecção na 1.ª visita + persistência

- **Decision**: só em **rotas públicas sem prefixo** e **se não houver escolha guardada**:
  ler `navigator.languages` (espelha o `Accept-Language`; o JS não lê o cabeçalho) →
  1.º match `en*`/`fr*`/`pt*` → se ≠ pt, `Navigate replace` para `/{locale}{path}`.
  Se houver escolha guardada (`localStorage['accta.locale']`) ≠ pt, idem. A escolha só é
  **gravada pelo seletor** (visitar um link `/en/…` partilhado não sobrescreve a
  preferência). `localStorage` envolvido em try/catch (janela privada).
  **Crawlers** (UA `/bot|crawl|spider|slurp|facebookexternalhit|whatsapp/i`) **nunca são
  redirecionados** — `/sobre` tem de ser indexado como PT canónico (hreflang x-default).
- **Rationale**: FR-008/009/010/019; o Google desaconselha redirect automático por idioma
  porque o Googlebot renderiza com `en-US` → sem a exceção, o PT canónico deixaria de ser
  indexado. 12 meses de persistência = `localStorage` (sem expiração).
- **Alternatives**: detecção no edge (Vercel middleware) — exige Next/Edge Functions, fora
  da stack CRA; banner "Ver em English?" sem redirect — mais amigável a SEO mas contraria
  D3=A.

### R4 — `<head>`: título, descrição, `lang`, `hreflang`

- **Decision**: hook `usePageMeta({ title, description })` chamado por cada página
  pública: define `document.title`, `meta[name=description]`, `document.documentElement.lang`
  e gere 4 `<link rel="alternate" hreflang>` (pt-PT, en, fr, x-default → URL sem prefixo),
  removendo-os no unmount. Áreas privadas: `lang` volta a `pt-CV` no unmount.
- **Rationale**: FR-016/017/027; o Googlebot executa JS; evita dependência (react-helmet).
- **Valor `lang` PT**: o spec pede `pt-PT`; o `index.html` usa `pt-CV`. Decisão: **hreflang
  `pt-PT`** (conforme FR-016) e **`<html lang>` mantém `pt-CV`** na variante PT
  (zero regressão p/ leitores de ecrã já configurados; ambos são "Português" para AT).
  ⚠️ Divergência menor do FR-027 — sinalizar ao dono no gate de tasks.

### R5 — Carregamento dos dicionários e "sem flash" (SC-002)

- **Decision**: `pt.js` importado estaticamente (PT nunca espera); `en.js`/`fr.js` via
  `import()` dinâmico. O provider não renderiza o conteúdo da rota até o dicionário do
  locale estar pronto (mostra o `RouteSpinner` já existente). Como o locale vem do URL no
  1.º render, nunca há render PT seguido de EN.
- **Rationale**: SC-002 ("sem flash em PT"); a área privada não paga os bytes EN/FR.
- **Alternatives**: tudo estático (+2 dicionários no bundle principal de todos os sócios) —
  rejeitado; tudo lazy (incl. PT) — spinner extra na Home canónica.

### R6 — Chaves em falta e manutenção (FR-024/025, SC-007)

- **Decision**: `t()` faz fallback **EN/FR → PT → a própria chave**, com `console.warn`
  só em `NODE_ENV !== 'production'`. Teste Jest `i18n/__tests__/parity.test.js` falha se
  (a) uma chave PT não existir em EN/FR, (b) EN/FR tiverem chaves órfãs, (c) placeholders
  `{x}` divergirem. Convenção de PR (no `quickstart` + checklist): **alterar texto PT ⇒
  atualizar EN/FR no mesmo PR** ou listar a chave em `i18n/pending.js` (o teste aceita
  chaves pendentes e imprime-as).
- **Rationale**: "ferramenta que compare chaves" (FR-024) sem TMS; impede deploy de chaves
  em falta sem bloquear o PT.

### R7 — Organização das chaves

- **Decision**: um ficheiro por locale (`src/i18n/locales/{pt,en,fr}.js`), objeto com
  namespaces por página/secção (`layout.*`, `home.hero.*`, `sobre.*`, `notFound.*`,
  `common.*`). Arrays de conteúdo (ex.: FAQ, cartões) ficam como arrays no dicionário.
- **Rationale**: 3 ficheiros a rever lado a lado pelo tradutor; o teste de paridade é
  trivial.

### R8 — Ligações internas

- **Decision**: todas as `Link to="/…"` / `navigate('/…')` de páginas públicas passam por
  `lp()`. Ligações para a área privada (`/dashboard`, etc.) e os links de email
  (`/reset-password?token=…`, `/setup-account?…`) **não** levam prefixo.
- **Rationale**: FR-018a (navegar dentro do locale); FR-002 (privado PT).

### R9 — Seletor de idioma (US3)

- **Decision**: componente `LanguageSwitcher` (shadcn `DropdownMenu` existente; rótulos
  nativos; `aria-current="true"` + `lang` em cada item; troca o prefixo preservando
  `pathname` + `search` + `hash`; grava `localStorage`). Montado em `PublicLayout`
  (desktop + menu mobile) e no cabeçalho das 4 páginas de autenticação.
- **Rationale**: FR-011–014, FR-018a; reutiliza primitivas existentes (Princípio V).

### R10 — 404 (FR-019a)

- **Decision**: nova `NotFoundPage` (dentro de `PublicLayout`) montada como `*` **sob
  `/en` e `/fr`**. O fallback global sem prefixo **mantém o `Navigate to="/"`** atual.
- **Rationale**: o spec assume uma "404 canónica PT" que não existe; trocar o catch-all
  global mudaria o comportamento de URLs privadas mal escritas (SC-008: 0 regressões).
  ⚠️ Desvio consciente da última frase do FR-019a — sinalizar ao dono.

### R11 — Datas (FR-023)

- **Decision**: `formatDate(date, pattern)` no hook escolhe o locale date-fns:
  `pt→ptBR` (mantém o atual, zero regressão), `en→enUS`, `fr→fr`. Formatos PT com literais
  (`"dd 'de' MMMM yyyy"`) passam a vir do dicionário (`common.dateLong`).

### R12 — Aviso «conteúdo em português» (FR-005a, FR-007)

- **Decision**: componente `PortugueseContentNotice` que só renderiza com locale ≠ pt;
  incluído por rota em `NoticiaDetailPage`, secção de corpos sociais do `SobrePage`, e
  detalhes de publicação/álbum onde existam. Estilo: `bg-[#F5F5F5] text-xs text-grafite`
  (tokens do `frontend-design`).

### R13 — Strings vindas do backend em páginas públicas

- **Decision**: rótulos devolvidos pela API (ex.: `departamentos` de
  `/auth/registration-options`, `detail` de erros, conteúdos de notícias) **não** se
  traduzem (FR-005/006, A-09). Contam como exceção (ii) do SC-006.
- **Turnstile**: passar `language: locale` ao `turnstile.render` (o widget passa a falar a
  língua da página) — mudança de 1 linha.

### R14 — Tradução do conteúdo (FR-020, A-05)

- **Decision**: a engenharia produz **rascunhos EN/FR completos** (gerados pelo assistente,
  respeitando FR-021/022), sinalizados no cabeçalho de `en.js`/`fr.js`
  (`// REVISÃO HUMANA PENDENTE`). **Gate de go-live (STOP)**: o dono/tradutor revê e
  aprova; só então se retira a marca e se corta release.
- **Rationale**: evita placeholders "TODO" a estragarem as páginas na validação em navegador e
  dá ao revisor um texto real para corrigir em vez de traduzir do zero.

### R15 — Constituição (Princípio IV)

- **Decision**: emenda **MINOR v1.1.0 → v1.2.0** como 1.ª tarefa (PR
  `docs(constitution): amend to v1.2.0`): "User-facing text in **authenticated areas**,
  emails, notifications, PDFs and HTTPException `detail` MUST be PT; the **public site**
  MAY additionally offer EN/FR, with PT canonical." + reconciliar `CLAUDE.md §Conventions`.
