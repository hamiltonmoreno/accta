# Research: Pendências v2 — contador + avisos

Todas as NEEDS CLARIFICATION da spec estão resolvidas (FRs explícitos + decisões do dono).
Este documento fixa as decisões de desenho que o `plan.md` flagou.

## D1 — Onde vive a derivação do total (contador ≡ painel)

- **Decisão**: extrair a derivação de pendências de `PendenciasPage.js` para um hook partilhado
  `frontend/src/hooks/usePendencias.js`, consumido pela página **e** pela barra lateral.
- **Rationale**: SC-002 exige que o contador coincida **exatamente** com o que o painel lista.
  Duplicar os filtros na sidebar criaria duas cópias que divergem ao primeiro ajuste — exatamente
  o "re-implementar o que está umas linhas ao lado" que a Constituição (Princípio I) e o padrão
  de reutilização pedem para evitar. Um hook = uma definição, dois consumidores.
- **Alternativas consideradas**:
  - *Duplicar os ~6 filtros na sidebar, sem tocar em PendenciasPage*: menor raio de alteração,
    mas viola SC-002 por deriva. **Rejeitada.**
  - *Endpoint/contador no backend*: a spec proíbe (Assumptions: "sem endpoint/coleção novos para
    o contador"). **Rejeitada.**

## D2 — Partilha de cache (sem pedidos extra)

- **Decisão**: o hook usa os **mesmos `queryKeys`** já definidos em `lib/queryClient.js`
  (`polls.list()`, `events.upcoming()`, `atos.list({mine:true})`, `atos.list({status:'pendente'})`).
- **Rationale**: o TanStack Query deduplica por `queryKey`; reutilizar as chaves faz a sidebar e o
  painel lerem a **mesma** entrada de cache (`staleTime: 30s`, `gcTime: 5min`,
  `refetchOnWindowFocus`). Frescura "no carregamento/navegação" sem stream — exatamente FR-005.
- **Alternativas**: chave dedicada para o contador → cache separada, refetch duplicado. **Rejeitada.**

## D3 — Role-aware sem 403 (FR-009 / SC-005)

- **Decisão**: as 2 queries de Atos ficam com `enabled: isDir` (`isDir = isAdmin || isDirecao`,
  de `AuthContext`); o sócio comum nunca as dispara.
- **Rationale**: herda a garantia da spec 014 (achado: só Direção/admin veem/propõem Atos). Sem
  pedidos de Atos para sócio comum ⇒ sem 403. O `total` para sócio comum = votações + eventos.

## D4 — Voto secreto fora (herdado)

- **Decisão**: nenhuma exclusão nova. O contador deriva **só** de `polls` + `events` (+`atos`),
  nunca de `eleicoes`/`deliberacoes` (módulos/rotas separados).
- **Rationale**: como o painel nunca lê eleições/deliberações secretas, o contador também não —
  a invariante de voto secreto mantém-se por construção (SC-005), sem código extra.

## D5 — Formato do badge: "9+" e zero escondido

- **Decisão**: `total > 9 ? '9+' : total`; render apenas se `total > 0` (FR-003/FR-004).
- **Rationale**: o badge de «Pedidos de Inscrição» (`PrivateLayout.js:383-396`) já é a referência
  visual (bolha carmesim, `min-w-[20px] h-5 text-[11px] font-bold`); só falta o cap. Reutilizar
  as classes mantém a coerência do design system (Princípio V) sem nova decisão de cor.
- **Nota**: o cap aplica-se **só** ao badge de pendências; o de «Pedidos de Inscrição» fica como
  está (fora de âmbito).

## D6 — Re-apontamento dos avisos: 2.ª constante, não swap

- **Decisão**: introduzir `_LINK_PENDENTE = "/pendencias"` em `routes/atos.py`; aplicá-la aos 3
  call-sites de Atos **pendentes** (`create_ato`, overdue→Direção, overdue→proponente). `_LINK`
  (`/financeiro/co-aprovacoes`) mantém-se nos 2 de **decididos** (`sign_ato`, `execute_ato`).
- **Rationale**: o código partilha hoje uma única `_LINK`. Trocar a constante quebraria os avisos
  de decididos (levá-los-ia a um painel onde o Ato decidido **não** aparece). FR-007 é explícito:
  só os pendentes mudam. A 2.ª constante torna a distinção legível e à prova de regressão.
- **Alternativas**: parametrizar o link por `status` numa função → mais código para a mesma
  decisão estática de 2 valores. **Rejeitada** (Princípio I).

## D7 — Via B

- **Decisão**: como `routes/atos.py` muda, a release `develop→main` segue **Via B**
  (`docs/runbook-deploy-backend-via-b.md`). O frontend (US1) sai pela Vercel no push a `main`.
- **Teste decisivo Via B**: disparar um aviso de Ato pendente (ou inspecionar a notificação
  criada por `create_ato`) e confirmar `link == "/pendencias"`; um aviso de decidido `==
  "/financeiro/co-aprovacoes"`. (Sem rota nova ⇒ confirmação por código no container + pytest.)
