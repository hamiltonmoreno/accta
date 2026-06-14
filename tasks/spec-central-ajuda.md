# Spec — Central de Ajuda (Manual do Utilizador no dropdown do perfil)

> **Objetivo:** acrescentar um item **"Ajuda"** ao dropdown do avatar no
> cabeçalho (`UserMenu`) que leva a uma **Central de Ajuda** — um manual de
> instruções super detalhado de como usar o Portal ACCTA, organizado por módulo
> e adaptado ao papel (role) e privilégios de quem está autenticado.
>
> **Natureza deste documento:** especificação de mudança. **Não implementa
> nada** — define o quê, onde e como construir, as decisões a tomar e os
> critérios de aceitação. A implementação é um follow-up após aprovação.

---

## 1. Contexto e motivação

- O cabeçalho privado já tem um **dropdown do avatar**
  (`frontend/src/layouts/components/UserMenu.jsx`) com: *Meu Perfil*, *Ranking*,
  *Carteira Digital*, *Mural* (só mobile) e *Sair*.
- O portal cresceu para **~40 páginas privadas** agrupadas em vários blocos de
  navegação (Início, Governança, Participação, Comunidade, Conhecimento,
  Administração) com visibilidade por **role** (`admin`/`financeiro`/`moderador`/
  `socio`) e **privilégios** aditivos. Um sócio novo não tem como saber o que
  cada módulo faz nem o fluxo correto (ex.: votar numa eleição de voto secreto,
  submeter uma proposta, acompanhar a prestação de contas).
- Falta um **ponto único de ajuda** dentro do sistema. O ícone de perfil é o
  local natural e descoberto por convenção (a maioria dos SaaS põe "Ajuda/
  Suporte" sob o avatar).

**Pedido do dono:** no dropdown do ícone de perfil, acrescentar **um** elemento
— *Ajuda* — que abre "onde tem tudo o que pode ajudar o usuário": um **manual
super detalhado** de instruções de uso do sistema.

> Nota de escopo: isto é o **manual do portal (ERP privado)** — como *usar a
> aplicação*. É diferente da *Base de Conhecimento pública sobre a profissão CTA*
> (`spec-base-conhecimento-concluido.md`, conteúdo regulatório em
> `frontend/src/content/cta/`). Não confundir nem misturar os dois.

---

## 2. Decisões a tomar antes de implementar (entrada do dono)

Estas escolhas alteram o tamanho da implementação. Recomendação em **negrito**.

1. **Formato do destino do item "Ajuda":**
   - **(A) Página própria `/ajuda`** (rota privada, índice + secções por módulo).
     **Recomendado** — é um "manual super detalhado", merece uma página
     navegável, pesquisável e linkável (deep-link por secção). Alinha com o
     resto do portal (páginas privadas dedicadas).
   - (B) Painel lateral/modal (Sheet) sobre a página atual — bom para ajuda
     contextual curta, mau para um manual extenso.
   - (C) Link externo (PDF/Notion) — rejeitado: sai do portal, desatualiza,
     quebra a voz/design e a adaptação por role.

2. **Fonte do conteúdo do manual:**
   - **(A) Módulo de conteúdo estático em JS/MDX** versionado no repo
     (`frontend/src/content/ajuda/`), à semelhança de `content/cta/`.
     **Recomendado** — sem dependência de backend, auditável em PR, propaga numa
     só alteração, funciona offline. O manual muda quando o produto muda → vive
     com o código.
   - (B) Conteúdo dinâmico via API/DB (coleção `help_articles`) editável por
     admin no portal — maior custo (rota + RBAC + audit + UI de edição); deixar
     para uma **fase 2 opcional** se a Direção quiser editar sem deploy.

3. **Adaptação por papel:** o manual **deve filtrar** as secções pela
   visibilidade real do utilizador (role + privilégios), reutilizando a mesma
   lógica da navegação. Um `socio` não vê instruções de "Audit Logs" nem
   "Co-aprovações". **Recomendado: sim, filtrar** (evita confundir e expor
   funcionalidades inacessíveis).

4. **Pesquisa dentro do manual:** caixa de pesquisa client-side (filtra
   títulos/conteúdo). **Recomendado para a fase 1** (barato e muito útil num
   manual longo).

> **Pressupostos desta spec (se não houver objeção):** 1-A, 2-A, 3-sim, 4-sim.

---

## 3. Mudança no dropdown (`UserMenu.jsx`)

Acrescentar **um** `DropdownMenuItem` *Ajuda*, antes do separador final / do
*Sair*. Visível para **todos os utilizadores autenticados** (não depende de
role) — toda a gente precisa de ajuda.

- **Ícone:** `HelpCircle` (lucide-react) — já é usado no projeto para
  "Esclarecimentos" (`PrivateLayout.js:83`); aqui é navegação utilitária sob o
  avatar, sem conflito semântico. (Alternativas: `LifeBuoy`, `BookOpen`.)
- **Posição:** novo bloco entre o `DropdownMenuSeparator` dos itens de perfil e
  o item *Sair*, OU logo a seguir a *Meu Perfil*. **Recomendado:** próprio
  separador + item, imediatamente **antes** do separador do *Sair* (a Ajuda é
  utilitária, não destrutiva — não deve colar-se ao *Sair* vermelho).
- **`data-testid`:** `menu-ajuda` (segue o padrão `menu-perfil`/`menu-ranking`).
- **Destino:** `<Link to="/ajuda">` (decisão 1-A).
- **Cor/estilo:** neutro (igual aos outros itens) — **nunca** Carmesim (essa cor
  é reservada ao *Sair*/destrutivo, ver `frontend-design`).

Esboço (ilustrativo, não normativo) a inserir antes do separador do *Sair*:

```jsx
<DropdownMenuSeparator />
<DropdownMenuItem asChild>
  <Link to="/ajuda" data-testid="menu-ajuda">
    <HelpCircle className="w-4 h-4 mr-2" aria-hidden="true" />
    Ajuda
  </Link>
</DropdownMenuItem>
```

> O `import` de `HelpCircle` junta-se aos ícones já importados no topo do
> ficheiro. Atualizar os testes `UserMenu.test.jsx` (ver §8).

---

## 4. Rota e página `/ajuda`

- **Rota:** privada, dentro do `PrivateLayout` (mesmo padrão das outras páginas
  privadas em `App.js`, com `lazy(() => import('./pages/private/AjudaPage'))`).
  Acessível a **qualquer utilizador autenticado** (sem gate de role).
- **Ficheiro:** `frontend/src/pages/private/AjudaPage.js`.
- **Deep-link por secção:** suportar âncoras (`/ajuda#financeiro`,
  `/ajuda#votacoes`) para que outras páginas possam ligar à ajuda do seu módulo
  (fase 2: botão "?" contextual no cabeçalho de cada página → abre a secção).
- **Sem item na sidebar** (decisão do dono é pô-lo no dropdown do perfil). A
  navegação primária para a ajuda é o avatar; opcionalmente, um link discreto no
  rodapé do `PrivateLayout`.

### 4.1 Estrutura da página (UX)

- **Cabeçalho/herói** sóbrio (neutral-led): título "Central de Ajuda",
  subtítulo "Manual de utilização do Portal ACCTA".
- **Caixa de pesquisa** (decisão 4) — filtra as secções/artigos por texto.
- **Índice (TOC)** com as secções **visíveis para o utilizador** (filtradas por
  role/privilégio). Em desktop, TOC fixo à esquerda; em mobile, acordeão no topo.
- **Conteúdo** em secções (uma por módulo), cada uma com:
  - O que é / para que serve;
  - Quem tem acesso (role/privilégio) — só informativo;
  - **Passo a passo** das ações principais (numerado);
  - Dicas / erros comuns / FAQ curta do módulo.
- **"Primeiros passos"** no topo (onboarding): login, completar perfil, foto,
  MFA, navegação, notificações.
- **Rodapé da página:** "Não encontrou o que procura?" → atalho para
  *Esclarecimentos* (`/participacao/esclarecimentos`) e/ou *Contactos*.

Aplicar o **`/frontend-design`** (neutral-led, Open Sans, shadcn/ui, sem dark
mode, ≤1 botão primário Floresta por vista, sem cores legadas). Componentes
sugeridos: `Accordion` (shadcn/ui) por secção, `Input` para pesquisa, `Card`
para "Primeiros passos". Animações discretas via Framer Motion.

---

## 5. Conteúdo do manual (mapa de secções)

Derivar **da navegação real** (`PrivateLayout.js`) e das páginas existentes.
Cada secção é filtrada pela visibilidade do utilizador (mesma regra da sidebar).
PT-PT, voz institucional, **passo a passo orientado à tarefa**.

**A. Primeiros passos (todos)**
- Entrar (login), recuperar palavra-passe, ativar conta por convite.
- Completar o *Meu Perfil* e carregar foto (workflow de aprovação de foto).
- **MFA** (ativar/usar — ver `spec-mfa-*`).
- Como ler o cabeçalho (sino de notificações SSE, avatar, atalhos) e a sidebar.

**B. O meu portal (sócio — `roles: all`)**
- **Dashboard** — o que cada cartão mostra.
- **Carteira Digital** (`/carteira`, só `socio`) — cartão de membro, estado.
- **Ranking** (`/ranking`) — como é calculado (referir `spec-ranking-socio`).
- **Notificações** — stream em tempo real + fallback 30s; gerir.

**C. Governança & voz (todos)**
- **Votações** (`/votacoes`) e **Eleições** (`/admin/eleicoes`) — incluindo
  **voto secreto** e recibo (referir `spec-voz-participacao-socio`,
  `spec-governanca-estatutaria`).
- **Assembleias** (`/admin/assembleias`, sala ao vivo `AssembleiaSalaPage`) —
  presença, deliberações (referir `spec-sessao-assembleia-ao-vivo`).
- **Regulamentos** (`/regulamentos`) — consultar versões.
- **Participação:** Patrocínios, **Petições**, **Propostas**, **Esclarecimentos**,
  **Reclamações** (`/participacao/*`) — como submeter e acompanhar estado.

**D. Comunidade & conhecimento (todos)**
- **Eventos**, **Projetos** (+ detalhe/tarefas), **Documentos**, **Mural**,
  **Galeria**, **Benefícios**, **Formações**, **Publicações**,
  **Defesa Profissional**, **Relações Externas**.

**E. Finanças (admin/financeiro + privilégios)**
- **Financeiro** (`/financeiro`) — transações, receitas/despesas, configurações.
- **Co-aprovações** (`/financeiro/co-aprovacoes`) — fluxo de dupla aprovação.
- Nota: quotas são **descontadas na folha** — **não existe inadimplência**
  (regra do projeto; não escrever o contrário).
- Distinguir `view_finances_readonly` (Conselho Fiscal, leitura) de
  `manage_finances`.

**F. Administração (admin + privilégios)**
- **Pedidos de Inscrição**, **Utilizadores**, **Cargos & Mandatos**
  (promover/exonerar/transferir; nunca editar mandato à mão — referir
  `spec-identidade-cargos`/`spec-governanca-estatutaria`), **Comunicados**
  (email), **Disciplina/Sanções**, **Honorários**, **Audit Logs**,
  **Aparência/Marca/Banners/Notícias**.
- Lembrar condições de paragem relevantes ao admin (envio de emails reais, ações
  com auditoria).

> Cada subsecção: 1 parágrafo "para que serve" + lista numerada de passos +
> (opcional) "erros comuns". Onde já existe spec de domínio, **reaproveitar** a
> terminologia canónica (não reinventar nomes).

---

## 6. Arquitetura de conteúdo (recomendada — decisão 2-A)

```
frontend/src/content/ajuda/
├── index.js          # array ordenado de secções { id, titulo, icon, visivel(user), artigos[] }
├── primeirosPassos.js
├── meuPortal.js
├── governanca.js
├── comunidade.js
├── financas.js
└── administracao.js
```

- Cada **secção**: `{ id, titulo, icon, grupo, visivel?, artigos }`.
- Cada **artigo**: `{ id, titulo, resumo, passos: string[], dicas?: string[],
  faq?: [{q,a}] , rota? }` (texto PT-PT puro, sem JSX onde possível; permitir
  ligações internas por `rota`).
- **`visivel(user)`** reutiliza a **mesma lógica de gate** da sidebar
  (role + privilégios). **Extrair** essa lógica de `PrivateLayout.js` para um
  helper partilhado (ex.: `frontend/src/lib/nav/visibility.js`) e consumi-la
  tanto na sidebar como no manual — evita duas fontes de verdade que divergem.
  (Se a extração for rejeitada, replicar a regra com cuidado e anotar o
  acoplamento.)
- `AjudaPage` apenas **consome** o módulo e renderiza; zero conteúdo hardcoded na
  página. Uma alteração de produto → uma alteração no módulo → propaga.

---

## 7. Acessibilidade & i18n

- Item do dropdown e página com `aria-label`/headings semânticos; navegação por
  teclado no TOC; foco visível (ring Carmesim/40 como no resto).
- Texto **PT-PT** (UI-facing). Identificadores em EN; termos de domínio em PT
  (`socio`, `assembleia`, `quota`, …) conforme `CLAUDE.md`.
- Pesquisa e TOC funcionam sem rato; acordeões com `aria-expanded`.

---

## 8. Testes

- **`UserMenu.test.jsx`** — novo caso: o item *Ajuda* (`data-testid="menu-ajuda"`)
  renderiza para utilizador autenticado e aponta para `/ajuda`; aparece para
  todos os roles (admin/socio/financeiro/moderador).
- **`AjudaPage`** — render básico: mostra "Primeiros passos"; **não** mostra
  secções sem permissão (ex.: `socio` não vê "Audit Logs"/"Co-aprovações");
  admin vê secção de Administração; a pesquisa filtra resultados.
- **`content/ajuda`** — teste de integridade: ids únicos, toda secção tem
  `titulo` e ≥1 artigo, `rota`s apontam para rotas existentes.
- Seguir a arquitetura de testes do projeto (unit/in-process; sem servidor).

---

## 9. Fora de escopo

- Editor de ajuda no portal / conteúdo via API (fase 2 opcional — decisão 2-B).
- Ajuda contextual "?" por página (fase 2 — usa os deep-links da §4).
- Tour interativo/walkthrough (overlay passo-a-passo) — possível fase futura.
- Conteúdo público da profissão CTA (`content/cta/`) — já coberto por outra spec.
- Tradução multilíngue — o portal é PT-PT.

---

## 10. Critérios de aceitação / verificação

1. O dropdown do avatar mostra **Ajuda** (`menu-ajuda`) para todos os roles,
   estilo neutro, e navega para `/ajuda`.
2. `/ajuda` carrega dentro do `PrivateLayout`, com índice, pesquisa e secções.
3. As secções respeitam a visibilidade por role/privilégio (mesma regra da
   sidebar) — verificado para `socio` e `admin`.
4. Conteúdo vem do módulo `content/ajuda/` (página sem texto hardcoded);
   terminologia alinhada às specs de domínio existentes.
5. Sem inadimplência/cores legadas/dark mode; `/frontend-design` respeitado.
6. `cd frontend && yarn build` passa; `npx eslint src/ --ext .js,.jsx
   --max-warnings=60` sem novos erros; testes novos verdes.
7. Revisão visual (desktop + mobile, light mode, neutral-led).

---

## 11. Faseamento sugerido (follow-up, após aprovação)

- **Fase 0** — extrair o helper de visibilidade da navegação (§6) partilhado
  entre sidebar e manual.
- **Fase 1** — item *Ajuda* no `UserMenu` + rota/`AjudaPage` + módulo
  `content/ajuda/` (Primeiros passos + B/C/D) + pesquisa + testes.
- **Fase 2** — secções E/F (finanças/admin) e deep-links contextuais "?".
- **Fase 3** (opcional) — conteúdo editável por admin via API + tour interativo.

---

_Base auditada em primeira mão: `frontend/src/layouts/components/UserMenu.jsx`,
`frontend/src/layouts/PrivateLayout.js` (grupos/roles de navegação), `App.js`
(rotas privadas), e o conjunto de specs de domínio em `tasks/spec-*-concluido.md`._
