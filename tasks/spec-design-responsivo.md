# Spec — Design Responsivo Mobile-First do Portal ACCTA

> **Fonte da verdade de design:** `.claude/skills/frontend-design/SKILL.md`
> (canônico para cor, tipografia, espaçamento, botões). Esta spec **não
> altera tokens** — adiciona a **camada de responsividade mobile-first** por
> cima do sistema neutral-led já existente, e defere ao SKILL em qualquer
> conflito.
>
> **Princípio que sobrepõe o instinto:** _o estilo base é o do telemóvel;
> `sm:`/`md:`/`lg:`/`xl:`/`2xl:` são **melhorias progressivas**, nunca o ponto
> de partida._ Não se desenha para desktop e depois "encolhe".
>
> Execução faseada, **um PR/commit por fase**, na branch
> `claude/responsive-design-spec-0FvlF`. Marcar `[x]` ao concluir. Nenhum
> código de frontend foi alterado na criação desta spec.

---

## 0. Diagnóstico estrutural (verificado no código)

O app **não é estruturalmente não-responsivo**. A fundação mobile-first já
existe e está correta — os problemas são **localizados**, não sistêmicos.

| Fundação | Estado | Evidência |
|----------|--------|-----------|
| Breakpoints pedidos (`sm 640 / md 768 / lg 1024 / xl 1280 / 2xl 1536`) | ✅ já definidos (+ `xs:360`) | `frontend/tailwind.config.js:11-18` |
| Navegação mobile (portal) | ✅ drawer + overlay + botão hambúrguer | `layouts/PrivateLayout.js:457` (desktop `hidden md:flex`), `:468` (overlay `md:hidden`), `:476-483` (drawer `translate-x`), `:489-499` (header mobile + `Menu`) |
| Navegação mobile (público) | ✅ menu colapsável | `layouts/PublicLayout.js:39` (`hidden lg:flex`), `:67-78` (botão `lg:hidden`), `:84-115` (painel `grid-rows-[0fr]→[1fr]`) |
| Tabelas com scroll horizontal | ✅ wrapper embutido | `components/ui/table.jsx:6` (`<div className="relative w-full overflow-auto">`); 13 páginas com `overflow-x-auto` |
| Imagens responsivas | ✅ sem distorção | todos os `<img>` usam `w-full`/`object-cover`/`object-contain` (0 imgs sem `object-*`) |
| Painéis flutuantes vs viewport | ✅ protegidos | `components/NotificationBell.js:73` (`w-[400px] max-w-[90vw]`) |
| Uso de prefixos responsivos | 🟡 parcial | **71 de 129** ficheiros usam `sm:/md:/lg:/xl:` — restantes ~58 são na maioria componentes pequenos, mas há páginas densas sem grid responsivo |

### Conclusão de triagem

Isto é um **plano de conformidade e hardening mobile-first**, não um redesign.
O trabalho é: (a) padronizar containers/grids/tipografia onde ainda não há
escala; (b) eliminar as larguras fixas em `px` que arriscam overflow no
telemóvel estreito (360–390px); (c) garantir alvos de toque e formulários
confortáveis; (d) verificar nas 7 larguras de teste.

---

## 1. Inventário de achados (contagens reais — grep em `frontend/src/`)

| ID | Severidade | Classe | Magnitude / localização | Risco |
|----|-----------|--------|--------------------------|-------|
| **R1** | ✅ VERIFICADO (sem defeito) | Larguras fixas em `px` | Só **5** `w-[…px]` reais, todos legítimos: `NotificationBell.js:73` (`w-[400px] max-w-[90vw]` já protegido), `drawer.jsx:38`/`separator.jsx:16` (primitivos shadcn), `PrivateLayout.js:367/439` (`w-[18px]/[20px]` ícones). Os `max-w-[…px]` em `EventosPage:191`, `CashFlowTab:259`, `AdminMarcaPage:21`, `BrandLogo:38` são **tetos** + `truncate`/`object-contain` = padrão correto | nenhum — **não mexer** (ver nota de revisão abaixo) |
| **R2** | 🟡 MÉDIO | Grids que saltam 1→3/4 sem passo `sm:`/`md:` | `CarteiraPage.js:335` `grid-cols-1 md:grid-cols-3`; `AdminComunicadosPage.js:458` `grid-cols-1 xl:grid-cols-3` | salto brusco; tablet (768/1024) subaproveitado |
| **R3** | 🟡 MÉDIO | Páginas densas sem escala responsiva | ~58 ficheiros sem prefixos `sm:/md:/lg:`; priorizar **páginas** (não átomos UI): varrer `pages/private/*` e `pages/public/*` | conteúdo apertado ou esticado em larguras intermédias |
| **R4** | ✅ VERIFICADO (sem defeito) | `min-w-[…px]` (**não são colunas de tabela**) | Dois grupos, ambos corretos: **(a) alvos de toque** `min-w-[44px]/[48px]` (`AdminNoticiasPage:170/179`, `NotificacoesPage:326`, `MuralPage:522/532`, `PrivateLayout:293/365/438`) → desejável, suporta a Fase 5; **(b) filtros/campos em `flex flex-wrap`** com `flex-1`/`max-w-xs` (`ProjectsPage:321`, `CashFlowTab:160`, `AdminDisciplinarPage:262/274`, `ProjectDetailPage:101/333/441/592`, `AssembleiaSalaPage:272/850`) → padrão de wrapping correto | nenhum — só **verificar** fallback fluido (ver nota abaixo) |
| **R5** | 🟢 BAIXO | `style={{…}}` inline (convenção: só Tailwind) | **37** ocorrências; maioria **legítima e fora de escopo** (flip 3D do cartão `CarteiraPage.js:213-280`, cor de série de gráfico `FinanceCharts.jsx:17`, tamanho dinâmico do logo `ACCTALogo.js:18`, largura dinâmica da sidebar `PrivateLayout.js:458`) | só migrar para Tailwind os que forem **espaçamento/largura estáticos** |

> **Nota de revisão (correção à v1 desta spec):** a auditoria inicial reportou
> "29 larguras fixas em px" e tratou os `min-w-[…px]` como colunas de tabela —
> ambos **incorretos** (artefacto de grep que apanhou o `w-[…px]` interno de
> `max-w-[…px]`; revisão do Codex na PR #139). Verificado linha-a-linha:
> **não há larguras fixas problemáticas** (R1) e **nenhum `min-w-[…px]` é
> coluna de tabela** (R4) — os maiores são filtros em `flex flex-wrap`
> (já responsivos) e os de 44/48px são alvos de toque (desejáveis). **Não
> envolver estes controlos em `overflow-x-auto` nem trocar `max-w-` por
> `w-full`** — mudaria comportamento sem reduzir risco. O trabalho real
> concentra-se em R2 (grids) e R3 (escala de páginas).

---

## 2. Matriz de breakpoints (referência única)

Usar **sempre** os prefixos Tailwind já configurados — nunca media queries CSS
soltas nem `px` mágicos:

| Prefixo | Largura | Dispositivo-alvo | Papel |
|---------|---------|------------------|-------|
| _(base)_ | `< 640px` | telemóvel (360 / 390) | **ponto de partida** — 1 coluna, `w-full`, empilhado |
| `sm:` | `≥ 640px` | telemóvel grande / landscape | 1ª melhoria progressiva |
| `md:` | `≥ 768px` | tablet | 2 colunas, campos lado-a-lado |
| `lg:` | `≥ 1024px` | laptop | sidebar fixa visível, 3 colunas |
| `xl:` | `≥ 1280px` | desktop | 3–4 colunas |
| `2xl:` | `≥ 1536px` | desktop grande | densidade máxima, `max-w` trava a leitura |

`xs:360px` (extra do projeto) existe para casos pontuais — **não** torná-lo o
default; o base (sem prefixo) deve já funcionar a 360px.

---

## 3. Padrões reutilizáveis (aplicar em toda correção)

Padronizar para estes idiomas — coerentes com o SKILL §Spacing & Layout
(`max-w-7xl`, padding 24–32px, gap 32–48px). Reutilizar, não reinventar.

### Container de página
```jsx
<div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">…</div>
```

### Grid de cards/listas/métricas (progressivo, sem saltos)
```jsx
{/* mobile 1 → tablet 2 → laptop 3 → desktop 4 */}
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">…</div>
```
Para blocos repetidos de largura mínima conhecida, preferir grid automático:
```jsx
<div className="grid [grid-template-columns:repeat(auto-fit,minmax(16rem,1fr))] gap-4">…</div>
```

### Flex que quebra
```jsx
<div className="flex flex-wrap items-center gap-3">…</div>
```
Usar `gap-*` para espaçamento — **não** margens manuais entre filhos.

### Tipografia fluida (mobile legível → cresce no desktop)
```jsx
<h1 className="text-2xl md:text-4xl lg:text-5xl font-bold">…</h1>
<p  className="text-base md:text-lg leading-relaxed max-w-prose">…</p>
```
Corpo nunca abaixo de 16px no mobile (SKILL §Typography); blocos de texto com
`max-w-prose`/`max-w-[65ch]` para não esticar no desktop.

### Imagem
```jsx
<img className="w-full h-auto object-cover aspect-video" alt="…" loading="lazy" />
```
Sempre `alt`; `object-cover` para preencher sem distorcer; `aspect-*` para
proporção estável.

### Espaçamento de secção (progressivo)
```jsx
<section className="px-4 py-8 md:px-8 md:py-12 lg:px-16 lg:py-20">…</section>
```

### Botão (toque confortável no mobile, auto no desktop)
```jsx
<button className="w-full sm:w-auto min-h-11 px-5 py-3 rounded-md …">Continuar</button>
```
Alvo de toque ≥ 44px (`min-h-11`); primário full-width no mobile, `sm:w-auto`
no desktop. Taxonomia de cor/variante = SKILL §Buttons (≤1 Primary/Carmesim
por vista).

### Formulário (empilhado no mobile, lado-a-lado no tablet+)
```jsx
<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
  <Input className="w-full" /> <Input className="w-full" />
</div>
```
`<label>` visível e associado; `Input` shadcn `w-full`; espaçamento vertical
confortável.

### Tabela (scroll horizontal controlado)
```jsx
<div className="overflow-x-auto">
  <table className="min-w-full">…</table>
</div>
```
Já é o comportamento de `components/ui/table.jsx`. Para tabelas críticas no
portal, considerar **cards no mobile** (`md:hidden` lista de cards + `hidden
md:block` tabela) onde a leitura célula-a-célula for essencial.

---

## 4. Fases de execução

Cada fase: **commit na branch → verificação → atualizar checkbox**. Não fundir
em `main` sem OK (stop condition do CLAUDE.md). Lint/build limpos por fase.

### Fase 0 — Fundação & guarda anti-regressão (baixo risco)
Antes de tocar páginas, instalar a rede de segurança contra overflow horizontal.

- [ ] Confirmar guarda global contra scroll-x indesejado em `index.css`
  (ex.: `html, body { overflow-x: hidden; }` **só** se não houver `position:
  sticky/fixed` dependente — verificar antes; senão aplicar `overflow-x-clip`
  no contentor raiz `#root`). Documentar a escolha.
- [ ] **Aceitação:** a 360px, nenhuma página tem barra de scroll horizontal;
  `yarn build` OK.

### Fase 1 — ✅ R1: larguras fixas (verificação, sem alteração esperada)
A v1 sobre-reportou `w-[…px]` (artefacto de grep sobre `max-w-[…px]`).
Verificado: não há larguras fixas problemáticas. Esta fase **guarda contra
regressão**, não altera código.

- [ ] Confirmar que os 5 `w-[…px]` reais permanecem legítimos: `NotificationBell.js:73`
  (`max-w-[90vw]`), `drawer.jsx`/`separator.jsx` (primitivos), `PrivateLayout.js:367/439`
  (ícones). **Não alterar.**
- [ ] Confirmar que os `max-w-[…px]` (tetos + `truncate`/`object-contain`) permanecem
  como caps. **Não trocar por `w-full`** — removeria o teto.
- [ ] **Aceitação:** nenhum `w-[…px]` **novo** sem `max-w`/fallback fluido
  introduzido; 360px sem overflow.

### Fase 2 — ✅ R4: `min-w-[…px]` (verificação, sem alteração esperada)
Verificado: **nenhum** é coluna de tabela. (a) touch-targets 44/48px → manter
(suportam a Fase 5); (b) filtros/campos em `flex flex-wrap` → padrão correto.

- [ ] Para cada filtro/campo com `min-w-[…px]` em `flex-wrap` (`ProjectsPage:321`,
  `CashFlowTab:160`, `AdminDisciplinarPage:262/274`, `ProjectDetailPage:101/333/441/592`,
  `AssembleiaSalaPage:272/850`), confirmar que tem `flex-1` ou `w-full` para
  embrulhar limpo a 360px; só ajustar **se faltar** o fallback fluido. **Não**
  envolver em `overflow-x-auto`.
- [ ] **Aceitação:** filtros embrulham (não cortam nem causam overflow) a
  360–768px; alvos de toque ≥44px preservados.

### Fase 3 — 🟡 R2: suavizar grids com salto
- [ ] `CarteiraPage.js:335` `grid-cols-1 md:grid-cols-3` →
  `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3` (passo intermédio no tablet).
- [ ] `AdminComunicadosPage.js:458` `grid-cols-1 xl:grid-cols-3` →
  `grid-cols-1 md:grid-cols-2 xl:grid-cols-3`.
- [ ] **Aceitação:** nenhum grid de cards salta de 1 direto para ≥3 sem passo
  intermédio; cada largura de teste mostra contagem de colunas sensata.

### Fase 4 — 🟡 R3: escala responsiva nas páginas densas
Varrer **páginas** sem prefixos responsivos (priorizar privadas de alta
densidade: dashboards, listas admin, financeiro) e aplicar os padrões da §3:
container, grid progressivo, tipografia fluida, secções com espaçamento
progressivo. Triagem assistida por subagente (1 por grupo de páginas) para
listar ficheiros sem `sm:/md:/lg:` e propor o diff mínimo.

- [ ] Páginas privadas de lista/dashboard sem escala → aplicar grid + container
  padrão.
- [ ] Páginas públicas (`pages/public/*`) → tipografia fluida nos heros +
  espaçamento progressivo de secção.
- [ ] Formulários longos → `grid-cols-1 md:grid-cols-2` para campos pareáveis;
  empilhados no mobile.
- [ ] **Aceitação:** páginas tocadas legíveis e bem distribuídas em 360 / 768 /
  1024 / 1440; sem conteúdo colado às bordas no mobile nem esticado no desktop.

### Fase 5 — Acessibilidade & toque (transversal)
- [ ] Alvos de toque interativos ≥ 44px no mobile (`min-h-11`/`p-*`), sobretudo
  ícones-botão de navegação e ações em linha.
- [ ] HTML semântico onde faltar (`<nav>`, `<main>`, `<section>`, `<button>` vs
  `<div onClick>`); `<label>` associado a todo input.
- [ ] Foco visível preservado (SKILL: `focus-visible:ring-2 ring-[#C7202F]/40`)
  — nunca `outline-none` sem substituto.
- [ ] `loading="lazy"` em imagens abaixo da dobra (galeria, cards, banners).
- [ ] **Aceitação:** navegação por teclado completa; foco visível; estados não
  dependem só de cor (SKILL §Semantic — ícone + texto + cor).

### Fase 6 — Verificação final & QA responsivo
- [ ] `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60` limpo.
- [ ] `cd frontend && yarn build` sem erros.
- [ ] **Teste visual nas 7 larguras** (critério explícito do pedido):
  **360 / 390 / 640 / 768 / 1024 / 1280 / 1536px** — em ≥1 página de cada tipo:
  dashboard, lista admin com tabela, formulário, página pública (hero),
  galeria, financeiro.
- [ ] Checklist de aceitação abaixo, tela a tela.
- [ ] Atualizar `tasks/lessons.md` com qualquer padrão novo descoberto.

---

## 5. Critérios de aceitação (do pedido + SKILL)

- [ ] **Zero scroll horizontal** indesejado em qualquer largura de 360→1536px.
- [ ] Layout funcional e equilibrado em mobile, tablet, laptop e desktop.
- [ ] Imagens responsivas, sem distorção, dentro do contentor (`object-cover` +
  `aspect-*`).
- [ ] Tipografia escalável e legível; corpo ≥16px no mobile; linhas não
  excessivamente longas no desktop (`max-w-prose`).
- [ ] Cards organizam-se em grid progressivo (1→2→3→4) sem saltos.
- [ ] Menus funcionam no mobile (drawer/hambúrguer já existentes preservados).
- [ ] Formulários confortáveis: campos empilhados no mobile, pareados em `md:`.
- [ ] Alvos de toque ≥44px; foco visível; semântica e `alt`/`label` presentes.
- [ ] Design permanece **neutral-led** e conforme ao `frontend-design`
  (tokens, ≤1 Primary/Carmesim por vista, sem red-on-dark, `prefers-reduced-motion`).
- [ ] Código limpo: padrões reutilizáveis da §3, **só Tailwind** (sem novos
  `style={{}}` de layout), PT na copy.

---

## 6. Sequenciamento e risco

```
Fase 0 ─► Fase 1 ─► Fase 2 ─► Fase 3 ─► Fase 4 ─► Fase 5 ─► Fase 6
(guarda)  (R1 ✅verif)(R4 ✅verif)(R2 grid)(R3 esc.) (a11y)    (QA 7w)
```

- **Fase 0 primeiro** (guarda anti-overflow) torna qualquer regressão de scroll-x
  imediatamente visível nas fases seguintes.
- **Fases 1–2 são apenas verificação** (R1/R4 confirmados como não-defeito) — o
  trabalho real de remediação está em **R2 (Fase 3)** e **R3 (Fase 4)**.
- Fases 1–5 são largamente independentes após a 0 → podem ser PRs paralelos,
  mas a ordem é a recomendada.
- **Risco baixo**: nenhuma mudança de backend, dados, auth ou tokens de design.
  O risco a evitar é **introduzir** alterações onde não há defeito (trocar
  `max-w-` por `w-full`, ou embrulhar filtros em `overflow-x-auto`) — Fases 1–2
  existem para travar isso.
- **Stop condition:** se uma fase exceder 3 ficheiros não previstos, ou um build
  quebrar de forma não óbvia, parar e re-planear (CLAUDE.md).

## 7. Fora de escopo

- Reescrever o sistema de design ou alterar tokens (SKILL é canônico).
- Backend, modelos, rotas, auth, dados.
- Dark mode (proibido por decisão de design).
- Redesenhar fluxos/UX (isto é responsividade + conformidade, não redesign).
- Migrar `style={{}}` legítimos não-de-layout (flip 3D, cor de gráfico, tamanho
  dinâmico de logo/sidebar) — permanecem.

---

_Spec gerada a partir de auditoria de `frontend/src/` (129 ficheiros de
página/componente; 71 já com prefixos responsivos; breakpoints já alinhados em
`tailwind.config.js:11-18`; nav mobile presente em ambos os layouts; `<img>`
todas com `object-*`) contra `.claude/skills/frontend-design/SKILL.md` e as
diretrizes mobile-first do pedido. Revista após o code-review do Codex na PR
#139: confirmado que **não há larguras fixas em px problemáticas** (R1) e que
**nenhum `min-w-[…px]` é coluna de tabela** (R4) — o trabalho real concentra-se
em 2 grids com salto (R2) e na escala responsiva de páginas densas (R3).
Nenhum código de frontend foi alterado na criação/revisão desta spec._
