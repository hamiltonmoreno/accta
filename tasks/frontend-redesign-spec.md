# Spec — Migração do Frontend para o Sistema Neutral-Led

> **Fonte da verdade:** `.claude/skills/frontend-design/SKILL.md` (canônico).
> Esta spec traduz a auditoria de `frontend/src/` num plano de execução
> faseado, verificável, **um PR/commit por fase**, na branch própria
> (atual: `fix/health-audit` — usar branch dedicada por fase).
>
> **Princípio que sobrepõe o instinto:** _a maioria dos botões e superfícies é
> neutra; vermelho é um evento, não um fundo._ Carmesim `#C7202F` é o acento
> único — ≤1 instância proeminente por tela.

---

## 0. Diagnóstico estrutural (verificado no código)

O app **não é estruturalmente vermelho**. O tema shadcn está correto:

- `frontend/src/index.css:24` → `--primary: 0 0% 23%` (Grafite, não Carmesim) ✅
- `frontend/tailwind.config.js:35-38` → `primary.DEFAULT = #3A3A3A` ✅
- `frontend/src/components/ui/button.jsx` → variante default = neutra ✅

Os problemas são **camadas legadas sobrepostas a uma base correta**. Há dois
alvos sistêmicos e quatro classes de violação localizadas.

### Alvos sistêmicos

| ID | Alvo | Por que é sistêmico |
|----|------|---------------------|
| **S1** | `frontend/src/App.css` (folha de overrides globais legada) | `a { color:#C7202F }` global (L111-117) força **todo link vermelho, inclusive sobre fundo escuro** — raiz de grande parte do red-on-dark. Também: `::selection` Carmesim (L120-123), `*:focus-visible outline #C7202F` (L126-129), `input:focus border #C7202F !important` (L132-135), scrollbar Carmesim (L58-65), `:root` duplicado conflitando com `index.css` (L21-27), `.btn-primary/.btn-secondary` legadas (L90-108). `index.css` **já** define scrollbar neutro, focus-ring `grafite/40` e `.card-technical` → App.css é majoritariamente redundante **e** conflitante. |
| **S2** | Padrão "hero escuro com acento vermelho" copiado em ~8 páginas públicas + Login | `text-carmesim` sobre `bg-grafite`/gradiente escuro repetido em HomePage, Sobre, Transparência, Profissão, Contactos, BeneficiosPublico, EventosPublico, LoginPage. Ex. concreto `HomePage.js`: L92 gradiente `from-grafite`, L99/105 `text-carmesim` por cima; L143 `bg-grafite` + L154 `text-carmesim`; L366 `bg-grafite` + L376 `text-carmesim`; L384 `bg-confianca` (segundo acento ilegítimo num botão). |

### Inventário de violações (contagens reais)

| ID | Severidade | Classe | Magnitude (grep) | Raiz |
|----|-----------|--------|------------------|------|
| **V1** | 🔴 CRÍTICO | Vermelho sobre escuro/foto (ilegível) | subconjunto dos **197** `text-carmesim`/`text-[#C7202F]`/`text-red-` em 42 ficheiros — os que caem em fundo escuro | S1 + S2 |
| **V2** | 🟠 ALTO | >1 botão primário Carmesim por tela | varrer os 197 + `bg-carmesim` | padrão copiado |
| **V3** | 🟠 ALTO | Código de dark mode | `tailwind.config.js:3` `darkMode:["class"]` + `alert.jsx` (único ficheiro com `dark:` em `src/`) | scaffold shadcn |
| **V4** | 🟡 MÉDIO | Paleta de gráficos / tokens legados | `VotingResults.js:25` `['#00FF9C','#0A1F44',…]`; tokens `confianca/navy/amber/slate` e `pulse-radar` em `tailwind.config.js` | identidade "Aero-Swiss" antiga |
| **V5** | 🟡 MÉDIO | Texto muted abaixo de `#6B7280` | **161** `text-gray-400`/`text-gray-300`/`text-muted-auto` em 27 ficheiros | `index.css:53` `--text-muted:#9ca3af` + utilitário `.text-muted-auto` (L164-166) |

> **Nota de triagem:** os 197 hits de "texto vermelho" **não são todos
> violação**. Carmesim em texto sobre **branco** (link sublinhado, ênfase
> única, texto de erro `#B91C1C`) é **permitido** pelo SKILL. Só é defeito
> sobre fundo escuro/colorido/foto. A Fase 1 usa a matriz de decisão abaixo
> para classificar mecanicamente cada ocorrência.

---

## Matriz de decisão fg/bg (aplicar a cada ocorrência de Carmesim em texto)

| Ocorrência | Fundo | Veredito | Ação |
|------------|-------|----------|------|
| `text-carmesim` / `text-[#C7202F]` | branco `#FFFFFF` / `#F5F5F5` / `#FBEAEC`, **e** é link ou ênfase única | ✅ permitido | manter |
| `text-carmesim` | `bg-grafite` / gradiente escuro / `bg-confianca`/`navy` / foto | 🔴 defeito | trocar por `text-white` (label/heading) ou neutro claro; se for "badge", usar pílula `bg-white/10 text-white` |
| `text-red-400/500` como texto muted/secundário | qualquer | 🔴 defeito | trocar por token secundário (`#6B7280`) — não é estado de erro |
| `text-carmesim` repetido (vários por tela em branco) | branco | 🟠 excesso | manter só onde é link/ênfase real; resto → `text-grafite` |
| Erro de formulário em vermelho | branco | ✅ permitido | normalizar para `#B91C1C` (texto de erro acessível do SKILL) |

Regras de pares de contraste permitidos (do SKILL §Color System.5) são a
referência final. Qualquer par fora dela = defeito.

---

## Fases de execução

Cada fase: **branch própria → commit → verificação → PR**. Não fundir em `main`
sem OK do utilizador (stop condition do CLAUDE.md). Marcar `[x]` ao concluir.

### Fase 0 — Fundação global (alto impacto, baixo risco visual)

Remove a fonte sistêmica S1 e os interruptores globais errados. Nenhuma página
muda de layout; só param de herdar overrides legados.

- [ ] **`frontend/src/App.css`** — reduzir ao mínimo não-conflitante:
  - Remover regra global `a { color:#C7202F }` / `a:hover` (L111-117). Links
    passam a ser estilizados **por contexto** (Carmesim sublinhado só sobre
    branco; `text-white` sobre escuro).
  - Remover `::selection` Carmesim (L120-123) **ou** trocar para neutro.
  - Remover `*:focus-visible { outline:#C7202F }` (L126-129) — `index.css:80`
    já define o focus-ring canônico (`ring-grafite/40`). Conflito resolvido a
    favor do `index.css`.
  - Remover `input:focus { border #C7202F !important }` (L132-135) — o
    `!important` quebra o focus-ring dos inputs shadcn.
  - Remover scrollbar Carmesim (L48-65) — `index.css:84-96` já tem scrollbar
    neutro (cinza). Conflito → manter só o do `index.css`.
  - Remover `:root` duplicado (L21-27) e `.btn-primary/.btn-secondary`
    legadas (L90-108) — duplicam/conflitam com `index.css`.
  - **Manter** apenas: nada que não esteja já em `index.css`. Se o ficheiro
    ficar vazio de regras úteis, esvaziá-lo (deixar comentário) — **não**
    remover o `import './App.css'` sem confirmar que nada depende dele.
  - **Aceitação:** `grep -n "C7202F" frontend/src/App.css` → 0 resultados;
    app continua a renderizar; focus-ring visível nos inputs.
- [ ] **`frontend/src/index.css:53`** — `--text-muted: #9ca3af` → `#6B7280`.
  (O `--text-secondary` já é `#6b7280` ✅, não tocar.) Eleva todo o texto
  `.text-muted-auto` para o piso AA do SKILL.
  - **Aceitação:** `--text-muted` = `#6B7280`; contraste do texto muted em
    branco ≥ 4.5:1.
- [ ] **`frontend/tailwind.config.js:3`** — remover `darkMode: ["class"]`.
  - **Aceitação:** linha ausente; `yarn build` sem erro.
- [ ] **`frontend/src/components/ui/alert.jsx`** — remover classes `dark:`
  (único ficheiro com `dark:` em `src/`, ex. L13 `dark:border-destructive`).
  - **Aceitação:** `grep -rn "dark:" frontend/src/` → 0 resultados.
- [ ] **Verificação da fase:** `cd frontend && npx eslint src/ --ext
  .js,.jsx --max-warnings=60` limpo; `yarn build` OK; smoke visual
  (login + 1 página privada + 1 pública) sem regressão de layout.

### Fase 1 — 🔴 CRÍTICO: eliminar vermelho sobre escuro (V1)

Aplicar a **matriz de decisão fg/bg** a cada ocorrência. Triagem assistida por
subagente (1 subagente por grupo de páginas) para classificar os 197 hits;
corrigir só os classificados como 🔴.

- [ ] **Páginas públicas com hero escuro (S2):**
  `HomePage.js`, `SobrePage.js`, `TransparenciaPage.js`, `ProfissaoPage.js`,
  `ContactosPage.js`, `BeneficiosPublicoPage.js`, `EventosPublicoPage.js`,
  `LoginPage.js`. Em cada secção de fundo escuro: `text-carmesim` →
  `text-white`; badge/eyebrow vermelho → `bg-white/10 text-white`
  (não `text-carmesim`); botão de segundo-acento `bg-confianca` (ex.
  `HomePage.js:384`) → taxonomia correta da Fase 2.
- [ ] **Layouts/Componentes:** revisar hits de `text-carmesim` em
  `PublicLayout.js`, `PrivateLayout.js`, `ValidadorPage.js`,
  `SetupAccountPage.js`, `ResetPasswordPage.js`, `NotificacoesPage.js`,
  `ProjectDetailPage.js`, `MuralPage.js`, `DashboardPage.js`,
  `financeiro/CashFlowTab.js` — manter só os sobre branco que são link/ênfase.
- [ ] **Aceitação (rígida):** nenhuma combinação `text-carmesim`/`text-red-*`
  sobre `bg-grafite`/gradiente escuro/`bg-confianca`/`bg-navy`/foto no
  resultado de uma varredura final; cada par texto/fundo é um par permitido
  do SKILL e ≥ 4.5:1 (3:1 para ≥24px ou ≥18.66px bold). Verificar com leitura
  visual dos 8 heros + amostragem de contraste.

### Fase 2 — 🟠 ALTO: taxonomia de botões (≤1 primário/tela)

- [ ] Varrer botões com fill Carmesim (`bg-carmesim`, `.btn-primary`,
  `<Button>` com variante destrutiva usada como CTA comum). Em cada
  tela/secção: **no máximo 1** primário Carmesim (a ação principal real).
  Os restantes → **Secondary** (`bg-white border border-[#D1D5DB]
  text-[#3A3A3A] hover:bg-[#F5F5F5]`) ou **Tertiary/Ghost** conforme o
  SKILL §Buttons.
- [ ] Substituir botões de segundo-acento (`bg-confianca`/`bg-navy`) por
  Secondary/Primary conforme o papel — nunca como cor de botão paralela.
- [ ] **Aceitação:** inspeção tela a tela das páginas com formulários/ações
  (Login, Mural, Financeiro, Projetos, Eventos, Perfil, Admin*) → contagem
  de primários Carmesim ≤ 1 por vista.

### Fase 3 — 🟡 MÉDIO: texto muted muito claro (V5)

Pré-requisito: Fase 0 já elevou `--text-muted` para `#6B7280` (cobre
`.text-muted-auto`). Falta o uso literal de classes Tailwind cinza-claras.

- [ ] Substituir `text-gray-400` / `text-gray-300` por `text-[#6B7280]`
  (ou `text-secondary-auto` / token secundário) **quando forem texto**.
  Manter cinza-claro só em **não-texto** (ícones decorativos, divisórias) —
  o SKILL permite `#9CA3AF` apenas para decorativo não-textual.
  Ficheiros de maior densidade: `DashboardPage.js` (26), `AdminUsuariosPage.js`
  (23), `ProjectDetailPage.js` (25), `EventosPage.js` (14),
  `financeiro/CashFlowTab.js` (12) — ver lista completa de 27 ficheiros na
  auditoria.
- [ ] **Aceitação:** nenhum **texto** com `text-gray-400/300`; todo texto
  secundário/muted ≥ `#6B7280` (≥ 4.5:1 em branco).

### Fase 4 — 🟡 MÉDIO: paleta de gráficos + tokens legados

- [ ] **`frontend/src/components/voting/VotingResults.js:25`** —
  `const COLORS = ['#00FF9C','#0A1F44','#6B7280','#9CA3AF']` → paleta do
  sistema (Carmesim como 1ª série de destaque + neutros/semânticos do SKILL;
  ex. `['#C7202F','#3A3A3A','#6B7280','#9CA3AF']`). Garantir séries
  distinguíveis sem depender só de cor (legenda/rótulo).
- [ ] **`frontend/tailwind.config.js`** — limpeza de tokens da identidade
  antiga, **com mapeamento de uso antes de remover** (remover token usado
  quebra build):
  - `pulse-radar` keyframe/animation (L126-129, 150) — legado "radar"; remover
    se sem uso, senão substituir o uso primeiro.
  - `confianca`/`navy` (`#1B2B4B`) — o SKILL só sanciona Navy estrutural
    `#1e3a5f` para profundidade de hero. Decidir: realinhar a `#1e3a5f` **ou**
    eliminar e migrar usos para neutro. Não deixar como segundo acento.
  - `amber` (`#D4A843`) / `slate` — fora do sistema; mapear usos → semântico
    (`warning #D97706`) / neutro, depois remover o token.
  - **Aceitação:** `grep -rn "confianca\|bg-navy\|amber\|slate-\|pulse-radar"
    frontend/src/` só devolve usos já migrados; `yarn build` OK.

### Fase 5 — Verificação final & QA

- [ ] `cd backend && ruff check .` (sanidade — não deve ser afetado).
- [ ] `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60` limpo.
- [ ] `cd frontend && yarn build` sem erros.
- [ ] **Checklist de aceitação do SKILL** (`SKILL.md` §Acceptance) tela a tela:
  - [ ] ≤1 botão Primary/Carmesim por vista; restantes neutros
  - [ ] Todo par texto/fundo é permitido e ≥ 4.5:1 (3:1 grande)
  - [ ] Zero texto vermelho sobre escuro/Navy/foto
  - [ ] Focus-visible ring visível em todos os interativos
  - [ ] Estado por ícone + texto + cor semântica (nunca só cor)
  - [ ] Open Sans, ≤2 pesos/secção; muted ≥ `#6B7280`
  - [ ] shadcn/ui; só Tailwind; copy em PT
  - [ ] Responsivo 375 / 768 / 1024 / 1440; `prefers-reduced-motion`
- [ ] Diff de comportamento vs `main` nas páginas tocadas (screenshots
  antes/depois dos 8 heros).
- [ ] Atualizar `tasks/lessons.md` com qualquer correção surgida na execução.

---

## Sequenciamento e risco

```
Fase 0 ──► Fase 1 ──► Fase 2 ──► Fase 3 ──► Fase 4 ──► Fase 5
(global)   (CRÍTICO)  (ALTO)     (MÉDIO)    (MÉDIO)    (verificar)
```

- **Fase 0 primeiro** é obrigatório: remover `a{color:#C7202F}` global e
  `--text-muted` claro elimina a raiz de muitas ocorrências das fases 1 e 3
  **antes** de as corrigir uma a uma (menos trabalho manual, menos regressão).
- Fases 1–4 são independentes entre si após a 0 → podem ser PRs paralelos se
  necessário, mas a ordem de severidade é a recomendada.
- **Risco maior:** Fase 4 remoção de tokens Tailwind usados → sempre mapear
  uso antes de remover. **Stop condition:** se o escopo de uma fase exceder o
  previsto ou um build quebrar de forma não óbvia, parar e re-planear.
- **Sem migração de dados, sem backend, sem auth** — risco de produção baixo;
  o app não está em produção com este frontend.

## Fora de escopo

- Reescrever o sistema de design (já feito — `SKILL.md` é canônico).
- Backend, modelos, rotas, auth.
- Dark mode (proibido por decisão de design — só estamos a **remover** o
  código morto dele).
- Redesenhar páginas/fluxos (isto é conformidade ao sistema, não redesign de
  UX).

---

_Spec gerada a partir da auditoria de `frontend/src/` (197 hits de
vermelho-texto em 42 ficheiros; 161 de muted-claro em 27; 1 ficheiro com
`dark:`; paleta de chart legada em `VotingResults.js:25`) contra
`.claude/skills/frontend-design/SKILL.md`. Nenhum código de frontend foi
alterado na criação desta spec._
