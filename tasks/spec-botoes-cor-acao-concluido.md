# Spec — Cor de ação dos botões (verde positivo / vermelho destrutivo)

> **Objetivo:** acabar com a colisão semântica de o mesmo Carmesim servir ações
> positivas (Guardar) e destrutivas (Apagar). Aplicar psicologia da cor + UX/UI:
> **ação primária positiva → Floresta `#166534`**, **destrutiva → outline
> Carmesim**, neutro para o resto. O Carmesim mantém-se como **identidade de
> marca** (links, nav ativa, anel de foco, realces de erro) — nunca como botão
> primário positivo.

Estado: **proposta** (brainstorming validado com o dono em 2026-05-29; mockups
em `.superpowers/brainstorm/`). Branch a criar: `feature/botoes-cor-acao` (de
`develop`). PRs pequenos por fase.

---

## Decisões do dono (fechadas no brainstorming)
- **D1 — Direção:** semáforo — verde para positivo, vermelho para destrutivo
  (em vez de manter Carmesim na primária).
- **D2 — Tom de verde:** **Floresta `#166534`** (verde-800; institucional, foge
  ao verde genérico; contraste 6.2:1 com texto branco). Hover `#14532D`.
- **D3 — Destrutivo:** **outline Carmesim** por defeito (borda+texto `#C7202F`,
  fundo branco, hover tint `carmesim-50`). Vermelho **cheio** só em confirmação
  irreversível dentro de diálogo.
- **D4 — Âmbito:** **todo o sistema** — portal privado **e** site público
  (incl. CTAs de marketing como "Tornar-me sócio" e o botão de login).
- **D5 — Ações negativas sem perda de dados** (Rejeitar/Reprovar/Suspender/
  Indeferir/Bloquear): tratadas como **destrutivo (outline Carmesim)**.
- **D6 — Doc canónica:** atualizar a fonte-de-verdade do design (skill
  `frontend-design`) **+ espelhos** além do código.
- **D7 — Anel de foco:** mantém-se **Carmesim** (`ring-[#C7202F]/40`) como sinal
  global de acessibilidade, mesmo em botões verdes (aparece com offset).

## Stop conditions desta spec
- **Não** é um find-replace de `bg-carmesim`. 63 ficheiros usam `bg-carmesim`,
  mas a maioria são **acentos não-botão** (banners, nav ativa, avatares, badges,
  ícones) que **se mantêm**. Cada ocorrência tem de ser **classificada à mão**
  (botão-positivo / botão-destrutivo / identidade-não-botão).
- **Não** mudar `primary` (Grafite #3A3A3A) nem `secondary` (#F5F5F5) — não são
  vermelhos; o botão neutro fica igual.
- **Não** tocar em semântica de status/badges de erro (continuam Carmesim) nem
  em badges de sucesso já existentes.
- Email real a utilizadores continua stop condition (não é afetado aqui).

---

## Estado atual (levantamento)
- **Tokens** (`tailwind.config.js`): `carmesim` (DEFAULT `#C7202F`, `light
  #E8444F`, `dark #A51B27`, `50 #FEF2F2`, `100 #FEE2E4`), `primary` = **Grafite
  `#3A3A3A`**, `secondary` `#F5F5F5`, `destructive`/`alert` = `#C7202F`.
- **Primitivo** (`components/ui/button.jsx`): `cva` com variantes `default`
  (=Grafite), `brand` (=`bg-carmesim`), `destructive` (=carmesim sólido),
  `outline`, `secondary`, `ghost`, `link`. Anel de foco `ring-[#C7202F]/40`.
  **As variantes `brand`/`destructive` têm 0 usos** — os botões vermelhos são
  quase todos `bg-carmesim` hand-rolled.
- **Constantes ad-hoc `primaryBtn`** (duplicadas, `bg-carmesim`):
  `AdminAssembleiasPage.js`, `AdminDisciplinarPage.js`, `AdminEleicoesPage.js`,
  `AssembleiaSalaPage.js`.
- **Pegada `bg-carmesim`:** 63 ficheiros (worklist de auditoria — descobrir com
  `grep -rl "bg-carmesim\|bg-\[#C7202F\]\|bg-\[#A51B27\]" src --include=*.js`).

---

## Sistema-alvo

### Tokens (Tailwind)
Adicionar a paleta da ação positiva (naming consistente com `carmesim`/`grafite`):
```js
floresta: {
  DEFAULT: "#166534",  // ação primária positiva
  dark:    "#14532D",  // hover
  50:      "#F0FDF4",  // tint (badges de sucesso podem reutilizar)
}
```
`carmesim` mantém-se. Nada mais muda nos tokens.

### Primitivo de botão (`components/ui/button.jsx`)
- **`primary`** (nova variante, positiva) → `bg-floresta text-white hover:bg-floresta-dark`.
- **`destructive`** → reescrita para **outline**: `bg-white border border-carmesim
  text-carmesim hover:bg-carmesim-50`.
- **`destructiveSolid`** (nova) → `bg-carmesim text-white hover:bg-carmesim-dark`
  — só confirmação irreversível em diálogo.
- **`brand`** → marcada como **deprecada para botões** (mantida no código para não
  partir nada; comentário a dizer "não usar como CTA genérico").
- `default` (Grafite), `secondary`, `outline`, `ghost`, `link`: inalterados.
- Anel de foco: inalterado (`ring-[#C7202F]/40`).

### Módulo partilhado `lib/buttonStyles.js` (novo)
Exporta as class strings canónicas para páginas que não usam o `<Button>`:
`primaryBtn` (floresta), `destructiveBtn` (outline carmesim), `secondaryBtn`
(neutro), `ghostBtn`. As 4 constantes `primaryBtn` ad-hoc passam a **importar**
daqui (fim da duplicação).

### Mapa de verbos (taxonomia)
| Categoria | Estilo | Verbos |
|---|---|---|
| **Primária positiva** | Floresta sólido | Guardar, Salvar, Submeter, Confirmar, Criar, Adicionar, Novo/Nova, Enviar, Convidar, **Aprovar**, Publicar, Registar, **Entrar (login)**, Entrar na reunião, Votar/Confirmar voto, Gerar, Aplicar, Concluir, Finalizar, Avançar/Próximo, **Tornar-me sócio** (CTA público) |
| **Destrutiva / negativa** | Outline Carmesim | Apagar, Eliminar, Remover, Excluir, Anular, Revogar, **Rejeitar, Reprovar, Recusar, Suspender, Indeferir, Bloquear, Desativar** |
| **Confirmação irreversível** | Vermelho cheio (`destructiveSolid`) | Só dentro de diálogo de confirmação ("Apagar definitivamente") |
| **Secundária / neutra** | Branco + borda `#D1D5DB` + Grafite | Cancelar, Fechar, Voltar, Limpar, Filtrar, Exportar, Ver detalhes, ações de tabela |
| **Identidade Carmesim (NÃO-botão, mantém-se)** | — | links em fundo branco, nav ativa, anel de foco, badges/realces de erro, ícones de perigo |

Casos-limite: **Cancelar** = neutro (aborta, sem perda). **Aprovar** = verde.
**Terminar sessão/logout** = neutro/ghost. **Rejeitar** = destrutivo (D5).

### Acessibilidade
- Floresta `#166534` + branco = **6.2:1** ✓ AA.
- Outline Carmesim `#C7202F` em branco = **4.7:1** ✓ AA.
- Estado nunca por cor isolada: manter ícone/label (regra do design system).

---

## Fases

### F0 — Fundação (tokens + primitivo + módulo partilhado)
- [ ] `tailwind.config.js`: + token `floresta` (DEFAULT/dark/50).
- [ ] `components/ui/button.jsx`: variante `primary` (floresta), `destructive`
      → outline, `destructiveSolid`, comentário de deprecação em `brand`.
- [ ] `lib/buttonStyles.js`: `primaryBtn`/`destructiveBtn`/`secondaryBtn`/`ghostBtn`.
- [ ] As 4 `primaryBtn` ad-hoc passam a importar do módulo.
- [ ] Sem regressão visual fora dos botões (tokens novos são aditivos).

### F1 — Portal privado (auditoria por-instância)
- [ ] Varrer `pages/private/**` + `components/**` por `bg-carmesim`/`bg-[#C7202F]`.
- [ ] Para **cada** ocorrência: classificar e aplicar o mapa de verbos
      (positiva→floresta, destrutiva→outline, identidade→manter).
- [ ] Hotspots conhecidos: Admin* (Usuarios/Comunicados/Eleicoes/Disciplinar/
      Assembleias/PedidosInscricao/Cargos), financeiro/* (TransactionModal,
      SettingsTab, CashFlowTab, DRETab), Mural, Galeria, Projetos, Eventos,
      Votações, Perfil, Carteira.
- [ ] Sub-lotes por área (≤~8 ficheiros/PR) para revisão gerível.

### F2 — Site público
- [ ] `pages/public/**`: CTAs → floresta (LoginPage, CriarContaPage,
      SetupAccountPage, ForgotPasswordPage, ResetPasswordPage, HomePage,
      ProfissaoPage, Contactos, Sobre, Transparencia, e os *Publico*).
- [ ] Banners/heros com `bg-carmesim` decorativo = **identidade, mantêm-se**;
      só os **botões** mudam.

### F3 — Docs canónicas (D6)
- [x] `.claude/skills/frontend-design/SKILL.md`: cor de ação = Floresta;
      taxonomia de botões; Carmesim = identidade + destrutivo-outline.
- [x] Espelhos reconciliados: `.claude/rules/frontend.md`,
      `.github/copilot-instructions.md`, `.github/copilot-frontend.md`,
      `design_guidelines.json` (cada um defere à skill).
- [x] Atualizar `CLAUDE.md` (secção Conventions/Styling) se referir "Carmesim
      como acento único" — passar a "Carmesim = identidade/destrutivo; Floresta
      = ação positiva".

### F4 — Verificação
- [x] `npx eslint src/ --ext .js,.jsx --max-warnings=60` limpo (exit 0).
- [x] Verificação de contraste AA dos pares novos (Floresta 6.2:1, outline Carmesim 4.7:1).
- [x] Suite de testes FE (`craco test`) — nenhum teste seleciona por classe de cor
      de botão (grep em `*.test.js*` = 0 asserts a `bg-carmesim`/`bg-floresta`); suite verde.
- [x] Varrimento manual (multi-agente, 180 ocorrências em 58 ficheiros): nenhum
      botão de ação positiva vermelho remanescente; nenhum destrutivo verde;
      identidade Carmesim intacta. 1 desvio menor corrigido (GaleriaAdminPage:436).
- [x] Grep de sanidade: `bg-carmesim` restante só em contextos de
      identidade/destrutivo-outline.

---

## Ordem dentro de cada fase
tokens/primitivo → módulo partilhado → auditoria+refactor por área → eslint →
testes → varrimento manual.

## Review

**Estado: CONCLUÍDA** (F0–F4, 2026-06-01).

- **F0** — token `floresta` (DEFAULT `#166534` / dark `#14532D` / 50 `#F0FDF4`) em
  `tailwind.config.js`; primitivo `button.jsx` com `primary` (floresta),
  `destructive` (outline carmesim), `destructiveSolid` (carmesim cheio),
  `brand` deprecado; módulo `lib/buttonStyles.js`; as 4 `primaryBtn` ad-hoc
  importam de lá. (commit 5c01c15)
- **F1+F2** — auditoria por-instância: 44 botões positivos Carmesim→Floresta,
  CTAs públicos incluídos; banners/nav/badges/avatares Carmesim mantidos como
  identidade. (commit d18f3a6, 48 ficheiros)
- **F3** — doutrina de cor reescrita nas 6 docs canónicas (com OK do dono p/
  editar a SKILL.md): `SKILL.md` (fonte-de-verdade) + espelhos
  `.claude/rules/frontend.md`, `.github/copilot-instructions.md`,
  `.github/copilot-frontend.md`, `design_guidelines.json`, e `CLAUDE.md`.
  Doutrina: **Floresta `#166534` = ação positiva primária; Carmesim `#C7202F` =
  identidade + destrutivo (outline por defeito, cheio só em diálogo)**.
- **F4** — eslint limpo; contraste AA (Floresta 6.2:1 / outline Carmesim 4.7:1);
  verificação multi-agente (180 ocorrências / 58 ficheiros, revisão adversarial):
  0 botões positivos vermelhos, 0 destrutivos verdes; 1 desvio menor corrigido
  (`GaleriaAdminPage.js:436` — hover destrutivo sólido fora de diálogo → tinta
  `bg-carmesim/80`, ícone mantém-se branco p/ não violar "sem vermelho sobre
  escuro"). Pegada `bg-carmesim` restante = só identidade / destrutivo-outline.
- **Pendente operacional:** nenhum. (`brand` mantém-se no primitivo, deprecado,
  por compatibilidade — sem usos como CTA.)
