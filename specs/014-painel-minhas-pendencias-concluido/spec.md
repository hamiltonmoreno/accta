# Feature Specification: Painel «As minhas pendências»

**Feature Branch**: `feature/painel-minhas-pendencias`

**Created**: 2026-06-29

**Status**: Draft

**Input**: User description: "Painel «As minhas pendências» — uma vista para o sócio que agrega, num só sítio, tudo o que aguarda AÇÃO dele, para ele resolver em vez de só ser notificado. Complementa as notificações das specs 010–013 com um destino acionável."

## User Scenarios & Testing *(mandatory)*

> Contexto: hoje o sócio é **notificado** de coisas que dependem dele (ex.: o seu Ato
> está parado — specs 012/013), mas não há **um sítio** onde veja, de uma vez, tudo o que
> aguarda a sua ação e possa resolver. As pendências estão espalhadas: votações no
> Dashboard (sem filtrar "falta-me votar"), eventos por confirmar, Atos que propôs e ainda
> aguardam a Direção. Esta feature reúne isso num **painel acionável**.
>
> **Restrição de domínio (voto secreto):** em eleições e em deliberações de modo secreto o
> sistema **não consegue** saber quem ainda não votou (os votos não estão ligados ao
> eleitor, por desenho). Essas pendências **não** entram no painel — não se contorna o
> segredo do voto.

### User Story 1 - Ver tudo o que aguarda a minha ação num só sítio (Priority: P1) 🎯 MVP

Como sócio, abro «As minhas pendências» e vejo, agrupadas e com contagem, as coisas que
dependem de mim agora — e cada item tem uma ligação direta para agir. Deixo de ter de
caçar pelo portal o que está à minha espera.

**Why this priority**: É o coração da feature e entrega valor sozinho — transforma "ser
avisado" em "ter onde resolver". Sem isto, o sócio continua a depender de notificações
soltas e de procurar manualmente.

**Independent Test**: Com um sócio que tem (a) um Ato que propôs ainda pendente, (b) uma
votação aberta por votar e (c) um evento próximo por confirmar, abrir o painel e confirmar
que as três aparecem, agrupadas, com contagem e ligação para agir; e que itens já tratados
(Ato decidido, votação já votada, evento já confirmado) **não** aparecem.

**Acceptance Scenarios**:

1. **Given** que propus um Ato que continua `pendente`, **When** abro o painel, **Then**
   vejo-o na secção dos meus Atos pendentes, com uma ligação para o ver.
2. **Given** uma votação aberta em que ainda não votei, **When** abro o painel, **Then**
   vejo-a com uma ligação para votar; **e** uma votação em que **já** votei **não** aparece.
3. **Given** um evento próximo em que ainda não me inscrevi, **When** abro o painel,
   **Then** vejo-o com uma ligação para confirmar presença; um evento já confirmado (ou
   passado) **não** aparece.
4. **Given** que resolvo um item (votar/confirmar/o Ato é decidido), **When** volto ao
   painel, **Then** esse item **deixa** de aparecer.

---

### User Story 2 - Saber, sem ruído, quando não tenho nada pendente (Priority: P2)

Quando não há nada à minha espera, o painel diz-mo claramente (estado vazio tranquilizador)
em vez de uma lista vazia confusa. E o painel é o **destino** natural das ligações dos
avisos (specs 010–013): clico no aviso e aterro aqui.

**Why this priority**: Fecha o ciclo "aviso → ação" e evita ansiedade de "será que me
falta alguma coisa?". É valor incremental sobre US1.

**Independent Test**: Com um sócio sem pendências, abrir o painel e confirmar uma mensagem
de "está tudo em dia / nada pendente"; e confirmar que a ligação de um aviso de Ato
pendente leva ao painel.

**Acceptance Scenarios**:

1. **Given** que não tenho pendências, **When** abro o painel, **Then** vejo uma mensagem
   clara de "nada pendente" (não uma lista vazia ambígua).

---

### User Story 3 - (Direção) Ver também os Atos à minha assinatura (Priority: P3)

Como membro da Direção, além dos Atos que eu próprio propus, vejo no mesmo painel os Atos
que **aguardam a minha assinatura** — para não ter de ir à área de Co-Aprovações só para
saber se há algo à minha espera.

**Why this priority**: Útil para quem é Direção, mas é um público menor e a área de
Co-Aprovações já cobre a assinatura; é conveniência, não o MVP.

**Independent Test**: Com um utilizador da Direção que tem um Ato por assinar, abrir o
painel e confirmar a secção "À minha assinatura"; com um sócio comum, essa secção **não**
aparece.

**Acceptance Scenarios**:

1. **Given** que sou da Direção e há um Ato a aguardar a minha assinatura, **When** abro o
   painel, **Then** vejo-o numa secção "À minha assinatura" com ligação para assinar.

---

### Edge Cases

- **Voto secreto**: deliberações em modo secreto e eleições **não** geram pendências no
  painel (o sistema não sabe quem não votou; não se contorna o segredo). Podem, no máximo,
  ser referidas noutro sítio como "votação a decorrer", mas **fora** do âmbito deste painel.
- **Elegibilidade de voto**: um sócio que **não** é membro votante (ex.: honorário,
  direitos suspensos) não deve ver votações como pendência sua (não pode votar).
- **Conta inativa/técnica**: não se aplica (o painel é do próprio sócio autenticado e
  ativo).
- **Sem dados fiáveis** (ex.: evento sem data): trata-se com segurança (não aparece como
  pendência se não der para agir).
- **Item resolvido por outro caminho**: se o sócio votar/confirmar noutro ecrã, ao reabrir
  o painel o item já não aparece (a vista reflete o estado atual).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST apresentar ao sócio autenticado uma vista que **agrega** as
  suas pendências de ação, **agrupadas por tipo**, cada grupo com uma **contagem**.
- **FR-002**: O âmbito de tipos do MVP MUST ser **três**: (a) **Atos que o sócio propôs**
  (`created_by == eu`) e continuam `pendente`; (b) **votações abertas que ainda não votou**;
  (c) **eventos próximos por confirmar**. Deliberações secretas e **eleições** ficam
  **excluídas** (voto secreto, FR-008).
- **FR-003**: Para membros da **Direção**, a vista MUST incluir também uma secção **"Atos à
  minha assinatura"** (Atos a aguardar a assinatura do próprio), além de "Atos que propus".
  Para um sócio comum, essa secção **não** aparece. (Reutiliza o filtro `pendentes_para_mim`
  já existente.)
- **FR-004**: Cada item de pendência MUST ter uma **ligação para agir** (ver o Ato, votar,
  confirmar presença), levando ao ecrã onde a ação se completa.
- **FR-005**: A vista MUST refletir o **estado atual**: um item resolvido (Ato decidido,
  votação já votada, evento já confirmado, item fora do prazo) **não** aparece.
- **FR-006**: Quando o sócio **não** tem pendências, a vista MUST mostrar um **estado vazio
  claro** ("nada pendente"), não uma lista vazia ambígua.
- **FR-007**: O sistema MUST respeitar a **elegibilidade**: só apresenta como pendência uma
  ação que o sócio pode realmente realizar (ex.: não mostrar votações a quem não é membro
  votante).
- **FR-008**: O sistema MUST **não** expor pendências que violem o **segredo do voto**
  (eleições; deliberações secretas) — não há forma legítima de listar "quem não votou".
- **FR-009**: A vista MUST viver numa **página dedicada** (ex.: `/pendencias`), com um item
  no **menu do sócio**, tornando-se o **destino** natural das ligações dos avisos das specs
  010–013.
- **FR-010**: A vista MUST seguir o **design system ACCTA** (neutral-led; Floresta como
  única primária positiva; Carmesim identidade/destrutivo; sem dark mode) e ter o texto em
  **PT**, sem linguagem de inadimplência.

### Key Entities *(include if feature involves data)*

- **Pendência**: um item que aguarda a ação do sócio. Tem um **tipo** (Ato-que-propus /
  votação / evento / Ato-à-minha-assinatura), uma **referência** ao objeto (Ato, votação,
  evento), e uma **ligação para agir**. É **derivada** do estado atual desses objetos, não
  uma entidade armazenada.
- **Atos / Votações / Eventos**: objetos de domínio já existentes; o painel lê o seu estado
  para derivar as pendências (não os altera).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A partir do painel, o sócio identifica **tudo** o que aguarda a sua ação
  **num só ecrã**, sem ter de visitar áreas separadas (co-aprovações, votações, eventos).
- **SC-002**: Cada pendência listada permite **agir em ≤ 1 clique** (ligação direta para o
  ecrã da ação).
- **SC-003**: 0% de **falsos pendentes**: itens já resolvidos (votados/confirmados/
  decididos/expirados) **não** aparecem.
- **SC-004**: 0 pendências que **violem o segredo do voto** (eleições/deliberações secretas
  nunca aparecem como "falta-me votar").
- **SC-005**: Quando não há pendências, 100% das vezes o sócio vê um **estado vazio
  explícito** (e não uma vista ambígua).

## Assumptions

- Reaproveita o estado dos objetos existentes (Atos, votações, eventos) — a pendência é
  **derivada**, **sem** nova coleção/entidade armazenada nem schema novo.
- **Abordagem de dados (decidida, dono):** **reutilizar os endpoints de leitura já
  existentes** e filtrar "falta-me agir" no cliente — zero/mínimo backend, **sem** endpoint
  agregador novo. Se os reads existentes chegarem, a entrega é **só frontend** (Vercel, sem
  Via B).
- **A verificar no plano** (não é clarificação): se um sócio comum consegue listar via
  `GET /atos` os Atos que **propôs** (RBAC + filtro por proponente); se não houver filtro,
  pode ser preciso um pequeno ajuste de backend (e então a release exige **Via B**).
- Frontend-led; se a entrega for só frontend, vai pela Vercel (sem Via B).
- Mantém-se a coerência com a CoAprovacoesPage (padrão de referência para a secção "À minha
  assinatura").
- Validação funcional ponta-a-ponta (navegador) fica ao critério do dono (Princípio VII).
