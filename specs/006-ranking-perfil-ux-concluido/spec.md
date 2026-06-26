# Feature Specification: Revisão do Ranking e do Perfil

**Feature Branch**: `006-ranking-perfil-ux`

**Created**: 2026-06-26

**Status**: Draft

**Input**: User description: "Revisão do Ranking de sócios e do Perfil de utilizador. Problemas: (1) página de Ranking quebrada no telemóvel ('tipo TV antiga sem sinal'); (2) todas as categorias do ranking com o mesmo ícone de medalha, sem distinção clara de 1.º/2.º/3.º lugar; (3) ranking sem fotos dos associados; (4) dropdown de notificações cortado à esquerda, sem margem; (5) no Perfil o utilizador não consegue editar todas as informações — melhorar o perfil."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver o Ranking corretamente no telemóvel (Priority: P1)

Um sócio abre a página de Ranking no telemóvel para ver a sua posição e a dos
colegas. Hoje o conteúdo aparece distorcido/quebrado em ecrãs estreitos ("tipo
TV antiga sem sinal"). O sócio precisa de uma página legível e bem composta em
qualquer largura de ecrã.

**Why this priority**: A maioria dos sócios acede pelo telemóvel; uma página
ilegível torna a funcionalidade inutilizável para o público principal. É o
defeito mais grave (bloqueia o uso), por isso P1.

**Independent Test**: Abrir `/ranking` numa viewport de telemóvel (≈360–414px)
e confirmar que pódio, tabela e a caixa "A minha posição" se compõem sem
sobreposição, sem corte horizontal indevido e sem distorção, mantendo o texto
legível.

**Acceptance Scenarios**:

1. **Given** a página de Ranking com dados, **When** é vista numa largura de
   telemóvel, **Then** todos os blocos (pódio Top-3, "A minha posição", tabela,
   paginação) ficam contidos na largura do ecrã sem partir o layout.
2. **Given** a tabela de membros com nomes longos e cargos, **When** vista no
   telemóvel, **Then** o conteúdo de cada linha permanece legível (truncado ou
   reflowed de forma intencional), sem empurrar colunas para fora do ecrã.
3. **Given** larguras de desktop e tablet, **When** a página é vista, **Then** o
   aspeto atual nessas larguras é preservado (a correção não regride o desktop).

---

### User Story 2 - Distinguir claramente 1.º, 2.º e 3.º lugar (Priority: P2)

Um sócio olha para o ranking e quer perceber de imediato quem está em 1.º, 2.º e
3.º. Hoje o 2.º e o 3.º partilham o mesmo ícone/cor de medalha neutra, sem
hierarquia visual clara entre os três primeiros.

**Why this priority**: É o coração do reconhecimento — a razão de existir do
ranking. Sem distinção dos três primeiros, a página perde o seu propósito
motivacional. P2 porque depende de a página já ser legível (US1).

**Independent Test**: Com pelo menos três membros no ranking, confirmar que 1.º,
2.º e 3.º têm um destaque visual distinto entre si (ouro/prata/bronze ou
equivalente claramente diferenciado) tanto no pódio como na tabela.

**Acceptance Scenarios**:

1. **Given** um ranking com 3+ membros, **When** o pódio é apresentado, **Then**
   1.º, 2.º e 3.º exibem destaques visuais distintos uns dos outros.
2. **Given** a tabela completa, **When** as três primeiras posições são
   apresentadas, **Then** cada uma tem um indicador de posição distinto entre si;
   a partir do 4.º lugar é mostrado o número da posição.
3. **Given** a distinção é feita por cor, **When** apresentada, **Then** a
   posição é também comunicada por outro meio além da cor (número e/ou ícone),
   para acessibilidade.

---

### User Story 3 - Reconhecer os sócios pela foto no ranking (Priority: P2)

Um sócio percorre o ranking e quer reconhecer os colegas visualmente, não só
pelo nome. Hoje não há fotos. O sócio espera ver o avatar de cada associado ao
lado do nome.

**Why this priority**: Personaliza e humaniza o reconhecimento, aumentando o
envolvimento. P2: melhora significativa mas não bloqueante.

**Independent Test**: Confirmar que cada entrada do ranking (pódio e tabela)
mostra a foto de perfil do sócio, com um substituto consistente (ex.: iniciais)
quando não há foto.

**Acceptance Scenarios**:

1. **Given** um sócio com foto de perfil definida, **When** aparece no ranking,
   **Then** a sua foto é apresentada junto ao nome no pódio e na tabela.
2. **Given** um sócio sem foto de perfil, **When** aparece no ranking, **Then** é
   mostrado um substituto consistente (ex.: iniciais ou ícone neutro) em vez de
   um espaço vazio ou imagem quebrada.

---

### User Story 4 - Abrir as notificações sem corte no telemóvel (Priority: P2)

Um utilizador toca no sino de notificações no telemóvel. Hoje o painel
("dropdown") aparece cortado à esquerda, sem margem suficiente do bordo do ecrã.
O utilizador precisa de ver o painel inteiro, com respiro nas duas margens.

**Why this priority**: Afeta uma interação frequente em todas as páginas e em
todos os perfis. P2: incomodativo e visível, mas não bloqueia tarefas críticas.

**Independent Test**: Numa viewport de telemóvel, abrir o painel de notificações
e confirmar que não fica colado nem cortado em nenhum dos bordos, mantendo uma
margem mínima de ambos os lados.

**Acceptance Scenarios**:

1. **Given** uma largura de telemóvel, **When** o painel de notificações abre,
   **Then** mantém uma margem mínima em relação aos bordos esquerdo e direito do
   ecrã e nenhum conteúdo é cortado.
2. **Given** larguras de desktop, **When** o painel abre, **Then** continua
   alinhado ao sino como hoje, sem regressão.

---

### User Story 5 - Editar e melhorar o Perfil (Priority: P3)

Um sócio abre o seu Perfil para manter os dados atualizados. Hoje a página
mostra muita informação só de leitura e o sócio sente que "não consegue editar
todas as informações". O sócio precisa de perceber claramente o que pode editar,
conseguir editar tudo o que lhe compete, e ter uma página de perfil mais clara e
agradável.

**Why this priority**: Importante para a qualidade dos dados associativos, mas os
campos de autosserviço já são, na prática, editáveis — trata-se sobretudo de
clareza e UX. P3.

**Independent Test**: Como sócio, entrar em modo de edição e confirmar que todos
os campos que o sócio pode gerir estão acessíveis e gravam corretamente; os
campos que o sócio não pode editar estão claramente identificados como tal.

**Acceptance Scenarios**:

1. **Given** o sócio em modo de edição, **When** percorre o formulário, **Then**
   todos os campos de autosserviço (dados pessoais, contacto, morada, contacto de
   emergência, dados profissionais/licença, foto, biografia) estão presentes e
   gravam.
2. **Given** campos geridos pela associação (n.º de sócio, cargo, função, estado,
   categoria, data de admissão), **When** o sócio vê o perfil, **Then** estão
   visíveis mas claramente marcados como não-editáveis, com indicação de como
   alterá-los (contactar a administração).
3. **Given** o email (identidade, gerido por admin), **When** o sócio vê o
   perfil, **Then** o email aparece como não-editável, com indicação de que a
   alteração é feita pela administração.

---

### Edge Cases

- **Ranking com menos de 3 membros**: o pódio adapta-se (mostra 1 ou 2 destaques)
  sem partir o layout.
- **Empate de pontuação**: a ordem/posição é determinística e a distinção visual
  segue a posição atribuída.
- **Membro em opt-out do ranking público**: continua excluído das listas
  públicas; a introdução de fotos não o reexpõe.
- **Foto de perfil em falta, removida ou inacessível**: substituto consistente,
  nunca imagem quebrada.
- **Sino de notificações junto ao bordo do ecrã**: o painel reposiciona-se para
  não ultrapassar nenhuma margem.
- **Nomes muito longos / cargos longos** no telemóvel: truncagem intencional sem
  quebrar a grelha.

## Requirements *(mandatory)*

### Functional Requirements

**Ranking — responsividade (US1)**

- **FR-001**: A página de Ranking MUST apresentar-se sem layout quebrado,
  sobreposição ou distorção em larguras de telemóvel (≈360–414px), incluindo
  pódio Top-3, caixa "A minha posição", tabela e paginação.
- **FR-002**: A correção responsiva MUST preservar a apresentação atual em
  larguras de tablet e desktop (sem regressão).

**Ranking — distinção de posição (US2)**

- **FR-003**: O 1.º, 2.º e 3.º lugar MUST ter destaques visuais distintos entre
  si, tanto no pódio como na tabela, usando uma escala de ênfase dentro da paleta
  ACCTA — **1.º Carmesim, 2.º Grafite, 3.º muted** — com ícone (coroa/medalha) e
  número ordinal. Sem cores metálicas fora da paleta. *(Decisão D2, 2026-06-26.)*
- **FR-004**: A partir do 4.º lugar, a posição MUST ser indicada pelo **número de
  posição contínuo a negrito** (1, 2, 3, 4, 5, 6…), refletindo a posição do sócio
  na lista ordenada — **não** o rank com empates do servidor (que repetiria "4, 4,
  4" para pontuações iguais). *(Correção do dono, 2026-06-26.)*
- **FR-005**: A posição MUST ser percetível por outro meio além da cor (número
  e/ou forma de ícone), cumprindo o requisito de acessibilidade do projeto
  (estado/posição nunca só por cor).

**Ranking — fotos (US3)**

- **FR-006**: Cada entrada do ranking (pódio e tabela) MUST apresentar a foto de
  perfil do sócio junto ao nome.
- **FR-007**: Quando o sócio não tem foto, o sistema MUST apresentar um
  substituto consistente (ex.: iniciais ou ícone neutro), nunca um espaço vazio
  ou imagem quebrada.
- **FR-008**: A apresentação de fotos MUST respeitar o opt-out do ranking público
  (um membro oculto não é reexposto através da foto).

**Notificações (US4)**

- **FR-009**: O painel de notificações MUST manter uma margem mínima de **16px**
  em relação aos bordos esquerdo e direito do ecrã em larguras de telemóvel, sem
  cortar conteúdo.
- **FR-010**: Em larguras de desktop, o painel MUST manter o alinhamento atual ao
  sino, sem regressão.

**Perfil (US5)**

- **FR-011**: O sócio MUST conseguir editar, em autosserviço, todos os campos de
  perfil que lhe competem (dados pessoais, contacto, morada, contacto de
  emergência, dados profissionais/licença, foto, biografia) e essas alterações
  MUST persistir.
- **FR-012**: Os campos geridos pela associação (n.º de sócio, cargo, função,
  estado, categoria, data de admissão) MUST ser apresentados como não-editáveis e
  identificados claramente como tal, com indicação de como alterá-los.
- **FR-013**: A página de Perfil MUST tornar visualmente óbvia a fronteira entre
  "o que posso editar" e "o que é gerido pela associação".
- **FR-014**: O email MUST permanecer fora do autosserviço (identidade gerida só
  por admin); na página de Perfil é apresentado como não-editável, com indicação
  de que a alteração é feita pela administração. *(Decisão Q1, 2026-06-26.)*

### Key Entities *(include if feature involves data)*

- **Entrada de Ranking**: representa a posição de um sócio num período —
  posição, pontuação, nome, cargo, estado, e (novo) referência à foto de perfil
  do sócio. Respeita a preferência de opt-out público.
- **Perfil do Sócio**: dados pessoais, de contacto, morada, emergência,
  profissionais/licença, foto e biografia (autosserviço) vs. dados de
  identidade/associação geridos pela administração.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos blocos da página de Ranking ficam contidos na largura do
  ecrã, sem corte horizontal indevido nem sobreposição, em viewports de 360px,
  390px e 414px.
- **SC-002**: Um sócio identifica corretamente quem está em 1.º, 2.º e 3.º num
  relance, sem ler números, porque os três têm destaques distintos.
- **SC-003**: 100% das entradas do ranking mostram foto ou substituto
  consistente; zero imagens quebradas.
- **SC-004**: O painel de notificações mantém margem ≥ 16px em ambos os bordos em
  viewports de telemóvel; zero conteúdo cortado.
- **SC-005**: Um sócio consegue editar e gravar com sucesso qualquer campo de
  autosserviço numa única sessão de edição; os campos não-editáveis estão
  rotulados como tal.
- **SC-006**: Nenhuma regressão visual em desktop/tablet no Ranking, nas
  Notificações e no Perfil.

## Assumptions

- **Sem alterações ao algoritmo de pontuação**: esta revisão é de apresentação e
  edição; os pesos, sinais e regras de cálculo do ranking mantêm-se.
- **Fotos reutilizam o avatar existente do perfil**: usa-se a foto de perfil já
  gerida pelo sócio; não há novo fluxo de upload no ranking.
- **Substituto sem foto**: iniciais do nome sobre superfície neutra (consistente
  com o resto do portal).
- **Distinção de posição**: escala de ênfase da paleta ACCTA (1.º Carmesim, 2.º
  Grafite, 3.º muted) + ícone + número ordinal; **sem metálicos** (Decisão D2). A
  posição é sempre legível por número/ícone, não só por cor (acessibilidade).
- **Identidade mantém-se admin-only por defeito**: email, n.º de sócio, cargo,
  função, estado, categoria e data de admissão continuam fora do autosserviço,
  salvo decisão em contrário em Q1.
- **Âmbito = frontend**, exceto se a US3 exigir que a fonte de dados do ranking
  passe a incluir a referência da foto do sócio (ajuste mínimo na leitura do
  ranking), e exceto eventual decisão de Q1.
- **Sem dark mode** e respeito integral pelo sistema de design ACCTA
  (neutral-led, Carmesim como acento de marca/destrutivo, Floresta para ação
  positiva).
