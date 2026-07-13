# Feature Specification: Dashboard unificado para todos os sócios

**Feature Branch**: `feature/dashboard-unificado`

**Created**: 2026-07-13

**Status**: Draft

**Input**: User description: "Queria que pelo menos o Dashboard fosse igual para todos os sócios independente dos privilégios — por exemplo, um sócio sem cargo pode ver a evolução das finanças no dashboard, ele só não pode ter acesso à área de Finanças. Analisar também se é de bom tom colocar outros KPIs para incrementar o dashboard."

## User Scenarios & Testing *(mandatory)*

> **Contexto:** hoje o Dashboard mostra widgets **diferentes** conforme o nível de acesso.
> Em `DashboardPage.js` o gate `hasFinance = isAdmin || isFinanceiro` esconde o bloco
> financeiro inteiro (stat cards, gráfico receitas × despesas, DRE, pizza de despesas por
> categoria, banner de resumo). Um sócio comum abre o Dashboard e vê **apenas** votações,
> eventos, ranking pessoal e feed de atividade — nunca vê a **evolução da associação a que
> pertence**. Isto está trocado: a informação institucional de **estado da associação** é
> pertence colectiva do sócio (transparência é princípio do estatuto); o que **é** privilégio
> é *entrar no back-office das Finanças* (lançar, editar, ver os documentos individuais).
>
> Esta feature separa as duas coisas:
> **estado agregado da associação** = universal no Dashboard (todos vêem);
> **operar sobre as Finanças / drill-down para lançamentos** = continua gated.
> Simultaneamente, aproveita a revisão para **avaliar KPIs adicionais** que reforcem o
> Dashboard como painel institucional (não implementá-los em bloco — apresentar candidatos
> priorizáveis com o dono).
>
> **Restrições de domínio:** RBAC intocado (privilégios continuam a governar áreas e
> drill-down); nunca expor PII em widgets universais (sem nome/quantia por sócio nos widgets
> financeiros; agregados apenas); linguagem **sem inadimplência** (quotas são descontadas por
> folha); PT-PT; neutro-led; sem dark mode.

### User Story 1 - Sócio comum vê a evolução financeira agregada no Dashboard (Priority: P1) 🎯 MVP

Como sócio ativo, sem cargo nem privilégios especiais, abro o Dashboard e vejo a **evolução
financeira da associação** em modo agregado (saldo actual, gráfico mensal de receitas ×
despesas do exercício, resultado do exercício, quotas do mês) — **os mesmos widgets** que o
admin vê. Fico com uma visão institucional do estado da associação, **sem** que isso me dê
acesso à área `/financeiro` (que continua reservada a quem tem privilégio para lá operar).

**Why this priority**: é o coração da feature e entrega valor sozinho — cumpre o princípio de
transparência para com o sócio e alinha o Dashboard ao **estado da associação** (não ao papel
do utilizador). Sem isto, o resto (KPIs extra) é acessório.

**Independent Test**: Autenticar como sócio comum (role `socio`, sem privilégios de finanças
nem cargo elevado) e abrir o Dashboard. Confirmar que aparecem os widgets financeiros
agregados (mesmos que aparecem ao admin); confirmar que o menu **Finanças** e a rota
`/financeiro` **continuam inacessíveis** (item de menu escondido / rota → 403); confirmar que
os widgets **não** listam lançamentos individuais nem nomes de sócios.

**Acceptance Scenarios**:

1. **Given** que sou sócio comum (sem privilégios de finanças), **When** abro o Dashboard,
   **Then** vejo o gráfico de receitas × despesas do exercício, o saldo actual, o resultado
   do exercício e o valor total de quotas do mês — **agregados**, sem lançamentos individuais.
2. **Given** que sou sócio comum, **When** olho para o menu lateral, **Then** o item
   **Finanças** **não** aparece; **When** navego manualmente para `/financeiro`, **Then** o
   sistema devolve **acesso negado** (comportamento actual mantém-se).
3. **Given** que sou admin ou tenho privilégio de finanças, **When** abro o Dashboard,
   **Then** vejo **os mesmos widgets** que o sócio comum vê (paridade de conteúdo) — mais
   nada a mais nem a menos no Dashboard.
4. **Given** que estou no Dashboard e clico num widget financeiro agregado, **Then** o
   comportamento respeita US2 (drill-down gated).

---

### User Story 2 - Drill-down permanece gated (widget é read-only para quem não tem privilégio) (Priority: P1) 🎯 MVP

Ainda como sócio comum, quando **clico** num widget financeiro do Dashboard (ex.: gráfico
mensal, categoria da pizza de despesas, saldo), o widget **não** me leva para dentro da área
de Finanças — o widget é **read-only informativo**. Para admin/financeiro, o mesmo widget
**é clicável** e abre o ecrã de detalhe / drill-down em `/financeiro`.

**Why this priority**: sem esta regra, uniformizar o Dashboard abre uma porta lateral para
a área gated e violaria o RBAC. É co-MVP com US1 (as duas juntas = a promessa da feature).

**Independent Test**: Como sócio comum, passar o rato/tocar em cada widget financeiro do
Dashboard e verificar que **não** há afordância de clique (cursor default, sem hover
"click me", sem link para `/financeiro`). Como admin, os mesmos widgets **têm** afordância
de clique e o clique abre o ecrã correspondente em `/financeiro`.

**Acceptance Scenarios**:

1. **Given** que sou sócio comum, **When** interajo com um widget financeiro no Dashboard,
   **Then** o widget não tem afordância de clique nem me leva para `/financeiro`.
2. **Given** que sou admin/financeiro, **When** clico num widget financeiro, **Then** vou
   para o ecrã correspondente em `/financeiro` (comportamento actual do "Ver detalhes"
   preservado).
3. **Given** qualquer utilizador, **When** o Dashboard renderiza, **Then** os widgets
   universais **não** expõem PII (sem nomes de sócios ligados a quantias, sem lista de
   lançamentos individuais, sem números de identificação).

---

### User Story 3 - Escolher e activar KPIs adicionais no Dashboard (Priority: P2)

Como dono do produto, quero **escolher** de uma lista curada de KPIs candidatos aqueles que
fazem sentido para a ACCTA neste momento — e vê-los aparecer no Dashboard uniformizado (para
todos os sócios), respeitando as mesmas regras de US1/US2 (agregados; drill-down gated se
aplicável; sem PII).

**Why this priority**: valor incremental sobre US1/US2. O Dashboard uniformizado é o "chassi"
que este US3 mobila. Sem US1/US2 não faz sentido activar KPIs novos porque metade dos sócios
não os veria.

**Independent Test**: Uma vez seleccionado o conjunto de KPIs para v1 (via Q1 abaixo),
verificar que cada um deles aparece no Dashboard, é o mesmo para todas as roles, não expõe
PII, e — quando faz sentido — o drill-down está gated de acordo com US2.

**Acceptance Scenarios**:

1. **Given** que os KPIs de v1 foram seleccionados, **When** um sócio comum abre o
   Dashboard, **Then** vê exactamente esses KPIs, agregados, e com o mesmo layout que o admin.
2. **Given** um KPI cujo detalhe vive numa área gated (ex.: "sanções aplicadas no ano" →
   drill-down em `/sancoes` só para quem tem privilégio de moderação), **When** um sócio
   comum vê o KPI, **Then** o número está lá mas o clique não abre a área restrita.

---

### Edge Cases

- **Widgets já-visíveis** (votações abertas, eventos próximos, ranking Top-N, feed de
  actividade, notificações não lidas, relatório pessoal): continuam iguais — a feature
  **acrescenta** widgets universais, **não altera** os que já eram universais.
- **RankingTopN — política universalizada em v1** (decisão do dono Q2): a configuração
  actual `ranking.visibility=direcao_only` (se activa) MUST ser alterada para permitir Top-N
  visível a todos os sócios. Consequência: o Top-N passa a mostrar **nomes dos sócios** no
  Top-N a todo o utilizador autenticado (mantém o comportamento actual de excluir contas
  `inativo` do Top-N do Dashboard). Nomes no Top-N **não** são considerados fuga de PII para
  efeitos de FR-005 — o consentimento implícito de participar num ranking associativo é
  domínio-padrão da associação; se houver preocupação, tratar como opt-out separado (fora
  desta feature).
- **KPI que revele PII por dedução em associação pequena** (ex.: se só um sócio faz
  aniversário no mês, "aniversariantes do mês" identifica-o): tratamento — ou o KPI é
  **opt-in** por sócio (mostrar nome só se autorizou), ou é **contagem agregada** sem nomes,
  ou fica **fora** de v1. Decidir por KPI durante Q1.
- **Sem dados no exercício** (ex.: exercício acabado de abrir, zero lançamentos): widgets
  devem mostrar estado vazio explícito ("Ainda sem movimento neste exercício"), não valores
  a zero enganadores.
- **Utilizador em conta `technical`** (ex.: `admin@controlador.cv`): não é sócio → o
  Dashboard institucional continua a ser-lhe visível (é admin operacional), mas os widgets
  **pessoais** (relatório pessoal, ranking do próprio) já hoje são vazios/omitidos porque
  não têm `member_id` associado — comportamento actual preservado.
- **Estado `inativo` / `pendente_aprovacao` / `rejeitado`**: fora do público desta feature
  (acesso à app já está restrito por essas transições).
- **Frescura dos dados agregados**: não é preciso tempo-real. Cache dos últimos minutos é
  aceitável — os widgets financeiros do Dashboard são visão, não ferramenta de operação.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O Dashboard MUST apresentar o **mesmo conjunto de widgets** para todos os
  utilizadores autenticados, **independentemente** de `role` e `privileges[]`. Não pode haver
  widgets "só para admin" nem "só para financeiro" no Dashboard.
- **FR-002**: O Dashboard MUST incluir, para todos os utilizadores, **widgets de evolução
  financeira agregada**: (a) saldo actual da associação; (b) gráfico mensal de receitas ×
  despesas do exercício em curso; (c) resultado do exercício (receitas − despesas); (d)
  total de quotas do mês. **Sem PII**, **sem lançamentos individuais**, **sem drill-down
  para quem não tem privilégio**.
- **FR-003**: O acesso à **área** de Finanças (`/financeiro` e sub-rotas), ao **menu**
  Finanças e às operações de **escrita** MUST manter-se governado pelos privilégios
  existentes — a uniformização do Dashboard **não** altera o RBAC das áreas nem o item de
  menu.
- **FR-004**: Widgets do Dashboard MUST ser **read-only para quem não tem privilégio para o
  drill-down correspondente**. Concretamente: para utilizadores sem privilégio de finanças,
  os widgets financeiros do Dashboard **não** têm afordância de clique nem hyperlink para
  `/financeiro`. Para quem tem privilégio, a afordância de clique é preservada.
- **FR-005**: Os widgets universais MUST expor **apenas dados agregados** — contagens,
  totais, distribuições por categoria — nunca lançamentos individuais, nomes de sócios
  ligados a quantias, ou qualquer identificador pessoal.
- **FR-006**: O RankingTopN MUST tornar-se **universal** — visível a todos os sócios
  autenticados no Dashboard, com o mesmo Top-N para todos. A política actual
  `ranking.visibility=direcao_only` (se configurada) MUST ser alterada em v1 para permitir
  visibilidade universal. **Decisão do dono (Q2, 2026-07-13): universalizar.**
- **FR-007**: Os KPIs adicionais **activados em v1** (decisão do dono Q1, 2026-07-13) são
  o **sweet-spot: Grupo B (Finanças agregadas) + Grupo A curado (Vida associativa)**,
  concretamente:
  - **B.8** Saldo actual da associação
  - **B.9** Receitas × Despesas do mês corrente (comparação com mês anterior)
  - **B.10** Resultado do exercício em curso
  - **B.11** Total de quotas do mês
  - **B.12** Distribuição de despesas por categoria (pizza)
  - **A.1** Nº de sócios activos
  - **A.2** Novos sócios nos últimos 90 dias
  - **A.3** Próximas AGA / assembleias marcadas
  - **A.5** Atos pendentes agregados (por estado)
  - **A.7** Participação em votações (percentagem na última votação fechada)

  Ficam **fora de v1**: A.4 taxa de comparência AGA; B.13 balancete link; C.14/C.15/C.16
  comunidade; D.17–D.19 pessoais (D.17 já existe como spec 015; D.18/D.19 mantêm-se como
  estão). Podem voltar em ronda futura.
- **FR-008**: Cada KPI activado MUST cumprir simultaneamente as regras universais: (a) o
  mesmo para todos os utilizadores; (b) agregado, sem PII (ou opt-in explícito, ver
  FR-011); (c) drill-down gated se aplicável.
- **FR-009**: O Dashboard MUST seguir o **design system ACCTA** (neutro-led; Floresta como
  única primária positiva; Carmesim identidade/destrutivo; sem dark mode) e ter todo o
  texto em **PT-PT**, **sem linguagem de inadimplência**.
- **FR-010**: Nenhuma alteração desta feature MUST introduzir escrita não auditada — nada
  na feature grava; se algum KPI de v1 exigir gravação (ex.: preferência de opt-in do
  aniversário, no futuro), essa escrita **passa por audit-log** (princípio III da
  constituição).
- **FR-011**: Qualquer KPI que possa **identificar um sócio por dedução em associação
  pequena** (aniversariantes do mês; ranking a-mostrar-nomes; presenças em AGA por sócio)
  MUST ser tratado de uma das seguintes formas: (i) **agregado apenas** (contagem, sem
  nomes); (ii) **opt-in** por sócio (só aparece nome de quem autorizou); (iii) **fora de v1**.
  A escolha por KPI é feita no plano, dentro das opções listadas na secção "Candidatos".

### Key Entities *(include if feature involves data)*

- **Dashboard**: página do sócio autenticado que agrega widgets de estado institucional +
  contexto pessoal. É **vista derivada**; não persiste estado próprio.
- **Widget universal**: um cartão/gráfico do Dashboard que respeita FR-001 (o mesmo para
  todos), FR-005 (agregado, sem PII) e FR-004 (drill-down gated).
- **Objetos de domínio já existentes** que os widgets lêem: transacções (agregadas),
  quotas, exercícios, atos, votações, eventos, sócios, sanções, presenças de AGA, ranking.
  Nenhum objecto novo é introduzido por esta feature.

### Candidatos a KPI (a priorizar com o dono — input de Q1)

Lista curada, agrupada por dimensão. Cada candidato inclui **valor**, **risco de PII em
associação pequena** e **drill-down actual** (se existir). O dono selecciona os que activa em
v1 (Q1 abaixo).

**A. Vida associativa (institucional)**

1. **Nº de sócios activos** (contagem, exclui `technical`/`inativo`/`pendente_*`) — PII: **∅**;
   drill-down: `/socios` (admin).
2. **Novos sócios nos últimos 90 dias** (contagem) — PII: **∅**; drill-down: `/socios` filtrado.
3. **Próximas AGA / assembleias marcadas** (data + agenda, sem lista de presenças) — PII:
   **∅**; drill-down: `/assembleias`.
4. **Taxa de comparência à última AGA** (percentagem agregada) — PII: **∅**; drill-down:
   `/assembleias/{id}` (Mesa da AGA).
5. **Atos pendentes agregados** (contagem por estado: aguarda proposta / aguarda Direcção)
   — PII: **∅**; drill-down: `/atos` (só se tiver privilégio); universal como número.
6. **Votações abertas** (já existe hoje — manter) — PII: **∅**.
7. **Participação em votações** (percentagem de sócios votantes na última votação fechada)
   — PII: **∅**; drill-down: `/votacoes` (leitura já pública).

**B. Finanças (agregadas — cumprem FR-005)**

8. **Saldo actual da associação** — PII: **∅**; drill-down: `/financeiro` (gated).
9. **Receitas × Despesas do mês corrente** (comparação com mês anterior, %) — PII: **∅**;
   drill-down: `/financeiro`.
10. **Resultado do exercício em curso** (receitas − despesas do ano) — PII: **∅**;
    drill-down: `/financeiro`.
11. **Total de quotas do mês** (agregado, sem lista de sócios) — PII: **∅**; drill-down:
    `/financeiro/quotas`.
12. **Distribuição de despesas por categoria** (pizza) — PII: **∅**; drill-down: `/financeiro`.
13. **Balancete disponível** (link para o mais recente publicado, se público) — PII: **∅**;
    já existe em `/prestacao-contas`.

**C. Comunidade (potencial risco de PII em associação pequena)**

14. **Aniversariantes do mês** — PII: **alto** se por nome. Opções: (i) fora de v1;
    (ii) contagem sem nomes; (iii) **opt-in** por sócio (só aparece quem autorizou no perfil).
15. **Ranking Top-3 do ano** — **universal em v1** (Q2 respondido). Mostra Top-3 com nomes
    a todos os sócios, exclui contas `inativo` do Top-N do Dashboard. Já em v1 por FR-006 —
    **não** entra na escolha do Q1.
16. **Sócios que fazem "X" anos de casa este mês** (contagem, sem nomes) — PII: **baixo**
    (agregado); ou opt-in para revelar nomes.

**D. Utilidade individual (widgets que só o próprio vê — não são "universais" no sentido de
FR-001, são **pessoais**; incluídos aqui só para o dono decidir se os promove)**

17. **As minhas pendências (contagem)** — já existe (spec 015); confirmar posição no
    Dashboard.
18. **Próximos lembretes de quotas** — já é notificação (spec 008); confirmar se se traduz
    também num tile.
19. **Meu ranking pessoal** — já existe; manter.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: **100%** dos utilizadores autenticados (admin, financeiro, moderador, sócio
  comum) vêem **o mesmo conjunto de widgets** no Dashboard após a feature — verificável
  abrindo o Dashboard com uma conta de cada tipo e comparando as listas de widgets
  renderizados.
- **SC-002**: **0 fugas de PII** em widgets universais — auditar cada widget: nenhum
  contém nome de sócio ligado a quantia, nenhum lista lançamentos individuais, nenhum
  identificador pessoal.
- **SC-003**: **0 regressões de RBAC** — sócio comum continua sem menu Finanças, `/financeiro`
  continua a devolver acesso negado a quem não tem privilégio, escritas continuam auditadas.
- **SC-004**: Sócio comum **consegue** identificar o estado financeiro agregado da
  associação (saldo, resultado do exercício, quotas do mês) **directamente** no Dashboard,
  sem ter de sair da página nem pedir privilégios.
- **SC-005**: KPIs adicionais activados em v1 (Q1) aparecem no Dashboard e cumprem SC-001 +
  SC-002 + SC-003.

## Assumptions

- **Reutiliza os endpoints de leitura já existentes** (`financesAPI.getSummary`,
  `financesAPI.getDRE`, `statsAPI.get`, etc.) removendo o `enabled: hasFinance` que hoje
  os desliga para sócios comuns. Se algum desses endpoints tiver actualmente RBAC no
  backend a bloquear sócios comuns, é preciso **um ajuste mínimo** para os tornar
  read-only-universais **preservando** a política de "sem PII"; nesse caso a release requer
  **Via B**. Confirmar no plano.
- Se os endpoints existentes já retornam apenas dados agregados sem PII (o que é
  provável, dado que são queries de resumo), a entrega pode ser **frontend-only** —
  remover o gate de UI e mostrar os widgets a todos. Vercel-only, sem Via B.
- Design system ACCTA (neutro-led, Floresta positivo, Carmesim identidade/destrutivo, sem
  dark mode) mantém-se; nenhuma alteração de tokens.
- Nenhuma nova entidade, nenhuma migração de dados, nenhum campo novo no `users`
  document (excepto se o dono escolher activar KPIs opt-in em v1, ex.: aniversários — nesse
  caso é campo aditivo simples, tratado no plano).
- A política actual do RankingTopN (`visibility=direcao_only` quando configurado) é
  respeitada, **não** alterada por esta feature.
- Validação funcional ponta-a-ponta (navegador) fica ao critério do dono (Princípio VII),
  com contas dos vários roles (admin, financeiro seed, moderador seed, sócio comum) — o
  dev isolado montado para a spec 017/018 pode ser reutilizado.

## Clarifications

## Question 1: Selecção de KPIs para v1 — **RESPONDIDO 2026-07-13: Sweet-spot (Opção B)**

FR-007 reflecte a lista final: **B.8/B.9/B.10/B.11/B.12** (Finanças agregadas) + **A.1/A.2/
A.3/A.5/A.7** (Vida associativa). Zero PII, endpoints de leitura já existem; a release
tende a ser **frontend-only (Vercel)** salvo se algum endpoint estiver hoje bloqueado a
sócios comuns por RBAC no backend — a verificar no plano.

---

## Question 2: Política do RankingTopN — **RESPONDIDO 2026-07-13: universalizar (Opção B)**

FR-006 e Edge Cases reflectem esta decisão. O RankingTopN passa a mostrar Top-N com nomes a
todos os sócios; a configuração `ranking.visibility` MUST ser alterada em v1 (aditivo, sem
migração de dados).
