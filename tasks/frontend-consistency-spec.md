# Spec — Consistência de Layout do Frontend (Pós-Neutral-Led)

> **Fonte da verdade:** `.claude/skills/frontend-design/SKILL.md` (canônico).
> Esta spec traduz a auditoria de consistência de `frontend/src/` (todas as
> ~30 páginas + layouts) num plano de execução faseado, verificável,
> **um PR/commit por fase**, em branch própria por fase. Não fundir em `main`
> sem OK do utilizador (stop condition do CLAUDE.md).
>
> **Princípio que sobrepõe o instinto:** _consistência > criatividade local._
> O mesmo elemento conceptual (header, card, modal, botão, status, empty
> state) deve ter **uma** implementação canônica, reutilizada — não uma
> variante ad-hoc por página.
>
> **Pré-requisito:** a migração neutral-led (Fases 0–5,
> `tasks/frontend-redesign-spec.md`) está concluída — Fases 0–2 em `main`
> (PR #42), Fases 3–5 na branch `fix/frontend-neutral-led`. Esta spec
> **não duplica** esse trabalho: trata de **dimensões novas** (estrutura,
> espaçamento, tipografia de secção, componentes partilhados, bug funcional)
> e de **resíduos conhecidos** explicitamente fora do âmbito da Fase 1
> original (ícones sobre Carmesim; o texto já foi tratado).

---

## 0. Diagnóstico estrutural (verificado no código)

A base de design está correta (tema shadcn neutro, tokens neutral-led). Os
problemas são de **consistência inter-página**: cada página reinventa
estrutura/componentes em vez de reutilizar um padrão canônico. Há **um
conflito SKILL ↔ index.css** e **um bug funcional** a resolver primeiro.

### Conflito de fonte da verdade (decisão necessária)

| Onde | SKILL.md diz | `index.css` faz | Impacto |
|------|--------------|-----------------|---------|
| Raio de card | `rounded-lg` (8px) — §Components | `.card-technical`/`.card-elevated` = `rounded-xl` (12px); override em `@media (max-width:640px)` → `rounded-lg` (8px) | Toda a app usa `.card-technical` (12px desktop / 8px mobile); o SKILL diz 8px. **Decisão tomada (default):** `.card-technical`/12px é o card canônico, reconciliado **só no código** (convergir outliers como `DashboardPage` `rounded-2xl` → `.card-technical`). O **`SKILL.md` NÃO é editado autonomamente** (canonical source-of-truth — preferência do dono, ver `tasks/lessons.md`); a frase "8px cards" do §Components fica como **nit de doc sinalizado** para o dono decidir. |

### Alvos sistêmicos

| ID | Alvo | Por que é sistêmico |
|----|------|---------------------|
| **S1** | Sem componente de **header de página** partilhado | `.page-title`/`.page-subtitle` existem (12 ficheiros usam) mas 4+ páginas hard-codam `h1 font-sans font-bold text-4xl text-grafite mb-2` (AdminLogs:25, Beneficios:65, Carteira:193 [ainda *centrado*], Documentos:32); Perfil/AdminUsuarios usam subtítulo cru. |
| **S2** | Sem componente de **modal** partilhado | 6 ficheiros hand-rolam `<div role="dialog">` (AdminUsuarios, Documentos, Eventos, TransactionModal, GaleriaAdmin, Projetos); **nenhuma página importa o shadcn `Dialog`**; raios e z-index divergentes; só os `AlertDialog` de delete usam shadcn. |
| **S3** | Sem **Empty/Loading** partilhado | `components/EmptyState.jsx` existe mas quase nenhuma página o usa; spinners ad-hoc (`border-carmesim` vs `border-primary` vs `border-3`); `Skeleton` (exigido por `.claude/rules/frontend.md`) não é usado em lado nenhum. |
| **S4** | Sem **STATUS map** partilhado | `STATUS_CONFIG` duplicado (ProjectsPage ≠ ProjectDetailPage, formatos diferentes); `getEventStyle` é um 3.º formato; 31 pares de tint Tailwind cru (`bg-blue/green/pink/purple/orange-*`) fora da paleta semântica do SKILL §4. |

### Inventário de violações (contagens reais verificadas)

| ID | Severidade | Classe | Magnitude (grep/auditoria) | Raiz |
|----|-----------|--------|----------------------------|------|
| **V1** | 🔴 CRÍTICO | **Bug funcional**: `${...}` literal em `className="..."` (string sem crase) → classes condicionais nunca aplicam | **4** ficheiros: `EventosPage.js:161`, `MuralPage.js:481`, `NotificacoesPage.js:304`, `EventosPublicoPage.js:148` | erro de digitação (crase ausente) |
| **V2** | 🔴 CRÍTICO | a11y: ausência total de `prefers-reduced-motion`/`motion-reduce` | **0** ocorrências em todo o `src/` (`animate-fade-up`/`fadeIn` correm sempre) | falha o checklist de aceitação do SKILL |
| **V3** | 🔴 ALTO | Header de página não-uniforme (S1) | ≥4 hand-rolled `h1 text-4xl` + 2 subtítulos crus vs 12 com `.page-title` | S1 |
| **V4** | 🔴 ALTO | Ícone/glifo `text-grafite` sobre `bg-carmesim` (par proibido ~1.6:1) — **resíduo da Fase 1** (só tratou texto) | confirmado `BeneficiosPublicoPage.js:192`; auditoria reporta também SobrePage ×3, Transparencia:156, AdminLogs:46, Beneficios:91/187, Votacoes:187 | Fase 1 excluiu ícones |
| **V5** | 🟠 ALTO | Cores fora do sistema (legado + Tailwind cru) | `#0A3A5A` em BeneficiosPublico:127 + Transparencia:153; "Radar Green" `rgba(0,255,156,...)` em EventosPublico:63 + Profissao:439; **31** pares de tint Tailwind cru em maps de status/categoria | resíduo Aero-Swiss + paletas ad-hoc |
| **V6** | 🟠 MÉDIO | Taxonomia de botão não unificada; focus-ring não-canônico | primário ora `.btn-primary` ora `bg-grafite font-mono uppercase` ora hand-rolled; **9** `focus:ring-primary` (cinza Grafite) vs `ring-carmesim/20|30|40` — todos ≠ canônico `ring-[#C7202F]/40 ring-offset-2` | Fase 2 só corrigiu a contagem ≤1 |
| **V7** | 🟠 MÉDIO | Status por cor de marca / cor sozinha (S4) | Validador "ativo"/válida = Carmesim (≠ success; erro≈sucesso); ProjectDetail prioridade "alta"=`text-carmesim`; Notificacoes `invoice_due:'bg-carmesim'`; MemberFinanceView status sem ícone | S4 |
| **V8** | 🟠 MÉDIO | Empty/Loading não partilhados (S3) | `EmptyState` quase não usado; spinners divergentes; 0 `Skeleton` | S3 |
| **V9** | 🟠 MÉDIO | Modais hand-rolled (S2) | 6 ficheiros; 0 importam shadcn `Dialog`; z-index `z-[60]` fora da escala | S2 |
| **V10** | 🟡 BAIXO | Ritmo de espaçamento/tipografia de secção divergente; inline `style var(--text-*)` | section-gap em 3 escalas; container em 3 convenções; `space-y-8/5/6`; headings `text-2xl..5xl` quase todos `font-bold` (SKILL: 1.5–2rem `font-semibold`); inline `style` pervasivo | sem token único |

> **Nota de triagem:** V4 são **ícones** (a Fase 1 da spec anterior tratou só
> `text-*` em **texto**, excluindo ícones explicitamente — ver
> `tasks/lessons.md`). V5 "Tailwind cru" é distinto da Fase 4 anterior (que
> removeu os *tokens* `amber/slate`; estes são classes Tailwind-default + hex
> inline que a remoção de token não apanha).

---

## Matriz de decisão — cor fora do sistema (V5)

| Uso | Veredito | Ação |
|-----|----------|------|
| `#00FF9C`/`rgba(0,255,156,…)` (Radar Green legado) em `style` inline decorativo | 🔴 proibido | remover o pattern ou trocar por `rgba(255,255,255,0.06)` sobre escuro |
| `#0A3A5A` / `from-primary to-[#0A3A5A]` (Navy legado) | 🔴 proibido | `bg-grafite` ou Navy canônico `#1e3a5f` (SKILL §3) |
| `bg-{blue,green,pink,purple,orange}-{50,100} text-…-{600,700}` em STATUS/categoria | 🟠 fora do sistema | mapear para SKILL §4: success `#15803D`/`#F0FDF4`, warning `#B45309`/`#FFFBEB`, info `#1D4ED8`/`#EFF6FF`, error `#B91C1C`/`#FEF2F2`; categorias sem semântica → neutro `bg-[#F5F5F5] text-[#3A3A3A]` |
| `text-red-{400,500,600}`/`orange-500` como dado/estado | 🟠 | erro→`#B91C1C`; aviso→`#B45309`; valor financeiro negativo→`#B91C1C` + sinal/ícone (nunca cor sozinha) |
| Ícone/glifo `text-grafite` sobre `bg-carmesim` | 🔴 V4 | `text-white` (único par permitido sobre Carmesim, SKILL §5) |

---

## Fases de execução

Cada fase: **branch própria → commit → verificação → PR**. Marcar `[x]` ao
concluir. Ordem = (impacto ÷ esforço) + dependências; globais/baixo-risco
primeiro.

### Fase 0 — Fundação global (alto alcance, baixo risco)

- [x] **Decisão do dono (resolvida — default):** `.card-technical`/`rounded-xl`
  (12px) é o card canônico. Reconciliação **só no código** (fases que tocam
  cards convergem outliers, ex. `DashboardPage` `rounded-2xl`, para
  `.card-technical`). O **`SKILL.md` NÃO é editado** (canonical
  source-of-truth — preferência do dono, `tasks/lessons.md`); a frase
  "8px cards" do §Components fica como nit de doc para o dono.
- [ ] **V1 — bug `${...}` em `className`:** trocar a `"` externa por crase
  (template literal) ou usar `cn()` em:
  `EventosPage.js:161`, `MuralPage.js:481`, `NotificacoesPage.js:304`,
  `EventosPublicoPage.js:148`. Confirmar que `border-l`/`opacity-70`
  condicionais passam a renderizar.
  - **Aceitação:** `grep -rnE 'className="[^"]*\$\{' frontend/src` → **0**.
- [ ] **V2 — `prefers-reduced-motion`:** adicionar a `index.css` um bloco
  `@media (prefers-reduced-motion: reduce){ .animate-fade-up,.animate-fade-in,
  .animate-fadeIn,*{animation:none!important;transition:none!important} }`
  (escopo conservador: anular só as animações próprias).
  - **Aceitação:** `grep -n prefers-reduced-motion frontend/src/index.css` → ≥1.
- [ ] **Verificação:** `npx eslint src/ --max-warnings=60` limpo; `yarn build`
  OK; smoke visual de 1 página com card pinned/evento (V1 visível).

### Fase 1 — Header de página uniforme (S1/V3)

- [ ] Substituir headers hand-rolled por `.page-title`/`.page-subtitle`
  (left-aligned), em `AdminLogsPage:25`, `BeneficiosPage:65`,
  `CarteiraPage:193` (remover `text-center`), `DocumentosPage:32`; e o
  subtítulo cru de `PerfilPage`/`AdminUsuariosPage:151`.
- [ ] Opcional: extrair `<PageHeader title subtitle actions>` reutilizável.
  - **Aceitação:** nenhuma página com `h1 ... text-4xl` hand-rolled
    (`grep -rnE 'h1 className="[^"]*text-4xl' frontend/src/pages` → 0);
    todas as páginas privadas usam `.page-title`.

### Fase 2 — Contraste de ícones + cores fora do sistema (V4/V5)

Aplicar a **Matriz de decisão de cor**. Triagem por subagente por grupo.

- [ ] **V4:** ícone/glifo `text-grafite` (ou `text-carmesim`) sobre
  `bg-carmesim`/gradiente escuro → `text-white`. Confirmado
  `BeneficiosPublicoPage:192`; varrer SobrePage, Transparencia:156,
  AdminLogs:46, Beneficios:91/187, Votacoes:187 e similares.
- [ ] **V5 legado:** remover `#0A3A5A` (BeneficiosPublico:127,
  Transparencia:153) → `#1e3a5f`/`bg-grafite`; remover Radar-Green
  `rgba(0,255,156,…)` (EventosPublico:63, Profissao:439).
- [ ] **V5 Tailwind cru:** mapear os 31 pares de tint em STATUS/categoria →
  SKILL §4 (ver matriz).
  - **Aceitação:** `grep -rnE "#0A3A5A|0,\s*255,\s*156" frontend/src` → 0;
    nenhum par `text-grafite`+`bg-carmesim` numa varredura fg/bg de ícones;
    maps de status só com hexes/tints do SKILL §4.

### Fase 3 — Taxonomia de botão + focus-ring canônico (V6)

- [ ] Unificar à taxonomia do SKILL §Buttons: Primary `bg-carmesim text-white
  hover:bg-carmesim-dark`; Secondary `bg-white border border-[#D1D5DB]
  text-[#3A3A3A] hover:bg-[#F5F5F5]`; Ghost. Remover `font-mono uppercase
  tracking-wider` legado dos botões (Eventos/Documentos/PublicLayout/auth).
- [ ] Focus-ring canônico: substituir `focus:ring-primary` (9×) e
  `ring-carmesim/20|30` por `focus-visible:ring-2 focus-visible:ring-[#C7202F]/40
  focus-visible:ring-offset-2` (ou usar primitivos shadcn já corretos).
  - **Aceitação:** `grep -rn "ring-primary\|font-mono.*uppercase" frontend/src`
    só devolve usos não-botão legítimos; ring de input uniforme.

### Fase 4 — Status semântico único (S4/V7)

- [ ] Criar `frontend/src/lib/statusConfig.js` (fonte única: project status,
  priority, event type, invoice/role) com tints/-700 do SKILL §4 + **ícone**
  por estado. Importar em ProjectsPage/ProjectDetailPage/EventosPage/etc.
  (eliminar `STATUS_CONFIG` duplicado e `getEventStyle`).
- [ ] Corrigir semântica: Validador "ativo"/válida → success (`#15803D`/
  `#F0FDF4`) + ícone, erro → `#B91C1C` (distinguíveis); ProjectDetail
  prioridade "alta" → warning; Notificacoes `invoice_due` → warning;
  MemberFinanceView status → ícone+label+cor.
  - **Aceitação:** sem `STATUS_CONFIG` duplicado; nenhum status comunicado
    só por cor (sempre ícone+label); Carmesim não usado como cor de estado.

### Fase 5 — Empty/Loading partilhados (S3/V8)

- [ ] Usar `<EmptyState>` (ícone centrado + mensagem + **1** ação primária,
  conforme SKILL §Patterns) em todas as listas/feeds vazios.
- [ ] Loading: usar `<Skeleton>` (shadcn) onde há grelha/lista; um único
  spinner canônico (`border-carmesim`) onde spinner fizer sentido.
  - **Aceitação:** spinners ad-hoc divergentes eliminados; `EmptyState`
    usado em ≥90% dos estados vazios; grelhas usam `Skeleton`.

### Fase 6 — Modais → shadcn `Dialog` (S2/V9) — maior risco

- [ ] Migrar os 6 modais hand-rolled (AdminUsuarios, Documentos, Eventos,
  TransactionModal, GaleriaAdmin, Projetos) para shadcn `Dialog`/`DialogContent`
  (raio canônico 12px, `z-50` da escala, header/footer consistentes,
  `aria-modal`/foco/scroll-lock geridos pelo primitivo).
  - **Stop condition:** se um modal tiver lógica não-trivial (steps, upload),
    parar e re-planear esse ficheiro isoladamente.
  - **Aceitação:** `grep -rln 'role="dialog"' frontend/src/pages` → 0;
    todos importam de `components/ui/dialog`; z-index na escala documentada.

### Fase 7 — Ritmo de espaçamento/tipografia + inline styles (V10)

- [ ] Definir e aplicar um único ritmo: container
  (`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`), section-gap (escolher 1, ex.
  `py-16 sm:py-24` público / `space-y-6` privado), heading de secção
  `font-semibold` escala única (utilitário `.section-title`).
- [ ] Substituir `style={{ color:'var(--text-*)' }}` inline por classes
  (`.text-secondary-auto`/`text-[#6B7280]`/`.text-grafite-auto`). Exceções
  documentadas: flip-3D da Carteira, largura dinâmica da sidebar.
  - **Aceitação:** `grep -rn "style={{ color: 'var(--text" frontend/src`
    só devolve exceções documentadas; section-gap/container consistentes
    numa amostra de 8 páginas.

### Fase 8 — Verificação final & QA

- [ ] `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60` limpo.
- [ ] `cd frontend && yarn build` sem erros.
- [ ] **Checklist de aceitação do SKILL** (§Acceptance) tela a tela.
- [ ] Smoke visual: 375/768/1024/1440 + `prefers-reduced-motion` ativo.
- [ ] Atualizar `tasks/lessons.md` com correções surgidas.

---

## Sequenciamento e risco

```
Fase 0 ─► 1 ─► 2 ─► 3 ─► 4 ─► 5 ─► 6 ─► 7 ─► 8
(global) (head)(cor)(btn)(stat)(empty)(modal)(rit.)(QA)
```

- **Fase 0 primeiro** (obrigatório): a decisão do raio destrava as fases que
  tocam cards; V1/V2 são correções globais de baixo risco e alto valor.
- Fases 1–5 são independentes entre si após a 0 → podem ser PRs paralelos;
  a ordem é a recomendada por (impacto ÷ esforço).
- **Risco maior:** Fase 6 (migração de 6 modais hand-rolled) — fazer um
  modal por commit, validar interação/foco/scroll-lock a cada um.
- **Stop conditions:** decisão do raio pendente; build quebrar de forma não
  óbvia; escopo de uma fase exceder >3 ficheiros não previstos; modal com
  lógica não-trivial. Em qualquer destes: parar e re-planear.
- **Sem migração de dados, sem backend, sem auth** — risco de produção baixo.

## Fora de escopo

- Reescrever o sistema de design (`SKILL.md` é canônico; só reconciliar o
  raio de card, ponto único e explícito da Fase 0).
- Backend, modelos, rotas, auth.
- Redesenhar páginas/fluxos (isto é **conformidade/consistência**, não
  redesign de UX).
- Re-fazer Fases 0–5 da `frontend-redesign-spec.md` (já concluídas; aqui só
  resíduos explicitamente fora do âmbito original + dimensões novas).

---

_Spec gerada a partir da auditoria de consistência de `frontend/src/`
(todas as ~30 páginas + 2 layouts, 5 subagentes) contra
`.claude/skills/frontend-design/SKILL.md`. Achados-chave verificados no código
(V1 4 ficheiros, V2 0 ocorrências, raio `.card-technical`=`rounded-xl`,
6 modais hand-rolled, 31 pares Tailwind cru, cores legadas `#0A3A5A`/Radar
Green). Nenhum código de frontend foi alterado na criação desta spec._
