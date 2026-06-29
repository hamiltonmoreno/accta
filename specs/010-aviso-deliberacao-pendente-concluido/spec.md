# Feature Specification: Aviso à Direção de deliberação pendente há mais de X dias

**Feature Branch**: `feature/aviso-deliberacao-pendente`

**Created**: 2026-06-28

**Status**: Draft

**Input**: User description: "Notificar a Direção quando uma deliberação fica pendente há mais de X dias."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Direção é avisada de pendências paradas (Priority: P1)

Um membro da Direção quer ser avisado quando uma decisão/ato que requer a ação do
órgão está parada há demasiado tempo, para que nada caia no esquecimento e o órgão
possa agir a tempo — sem ter de andar a vigiar manualmente listas de pendentes.

**Why this priority**: É o coração da funcionalidade — sem o aviso automático, as
pendências continuam a depender de alguém se lembrar de as procurar. Entrega valor
imediato: a Direção passa a ser empurrada para a ação em vez de ter de a puxar.

**Independent Test**: Com uma pendência cuja "idade" ultrapassa o limiar
configurado, confirmar que os membros da Direção recebem um aviso (in-app) com
título, resumo e ligação para o item, e que abrir o aviso leva à página do item.

**Acceptance Scenarios**:

1. **Given** uma pendência que requer ação da Direção e está nesse estado há **mais**
   de X dias, **When** o sistema avalia as pendências, **Then** cada membro da
   Direção recebe um aviso com o item e a sua antiguidade, e um link para agir.
2. **Given** uma pendência com **menos** de X dias, **When** o sistema avalia,
   **Then** não é gerado nenhum aviso para esse item.
3. **Given** um aviso de pendência recebido, **When** o membro da Direção o abre,
   **Then** é levado à ficha/página do item para o tratar.
4. **Given** uma pendência que entretanto foi resolvida (aprovada/executada/
   rejeitada/concluída), **When** o sistema reavalia, **Then** já não gera avisos
   para esse item.

---

### User Story 2 - Administração define o limiar X (Priority: P2)

Quem administra quer poder definir o número de dias (X) a partir do qual uma
pendência passa a ser sinalizada, para o adaptar ao ritmo real do órgão sem
depender de um valor fixo de código.

**Why this priority**: Sem um valor adequado, os avisos ou chegam cedo demais
(ruído) ou tarde demais (já não ajudam). Não é P1 porque um valor por omissão
razoável permite a US1 funcionar desde o início; a configuração é refinamento.

**Independent Test**: Alterar o limiar nas definições e confirmar que uma pendência
que antes não disparava (idade entre o valor antigo e o novo) passa — ou deixa — de
disparar conforme o novo X.

**Acceptance Scenarios**:

1. **Given** um administrador nas definições, **When** define o limiar para um novo
   número de dias, **Then** as avaliações seguintes passam a usar esse limiar.
2. **Given** nenhum valor configurado, **When** o sistema avalia, **Then** aplica um
   valor por omissão sensato e funciona à mesma.

---

### User Story 3 - Sem spam: aviso controlado por item (Priority: P3)

A Direção quer ser avisada do que está parado **sem** receber o mesmo aviso vezes
sem conta, para que os avisos continuem a ter valor e não sejam ignorados.

**Why this priority**: A utilidade do aviso colapsa se cada pendência gerar dezenas
de notificações repetidas. É P3 porque a US1 já entrega valor; o controlo de
repetição é qualidade que evita fadiga de notificações.

**Independent Test**: Deixar uma pendência atrasada manter-se atrasada ao longo de
várias avaliações e confirmar que o número de avisos por item respeita a cadência
definida (não um aviso por avaliação).

**Acceptance Scenarios**:

1. **Given** um Ato que se mantém atrasado ao longo de várias avaliações,
   **When** o sistema reavalia, **Then** o ato **não** gera um aviso novo em cada
   avaliação — recebe **no máximo um aviso** (o do momento em que cruzou o limiar).

---

### Edge Cases

- **Nenhum membro da Direção atribuído**: o sistema não falha; simplesmente não há
  destinatários (e regista que não houve a quem avisar).
- **Várias pendências atrasadas ao mesmo tempo**: a Direção recebe avisos por todas,
  sem que uma "engula" as outras (cada item é identificável).
- **Pendência resolvida entre avaliações**: não gera mais avisos a partir do momento
  em que deixa de estar pendente.
- **Conta técnica / membro inativo**: excluídos dos destinatários, de forma
  consistente com as restantes notificações.
- **Limiar alterado para um valor menor**: pendências que já tinham essa idade
  passam a qualificar na avaliação seguinte (sem reprocessar histórico de avisos).
- **Item sem data de referência fiável**: é ignorado com segurança (não dispara com
  base em data ausente/inválida).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST identificar os **Atos (Art. 54) em estado `pendente`** —
  actos administrativos que requerem ação dos órgãos (assinaturas/aprovação) e ainda
  não foram aprovados, executados, rejeitados nem cancelados. (Decisão: o âmbito do
  MVP é o **Ato pendente**, a única entidade com um estado `pendente` explícito e uma
  ação clara da Direção; deliberações de assembleia aprovadas sem seguimento ficam
  fora deste MVP.)
- **FR-002**: O sistema MUST tratar um Ato pendente como **atrasado** quando está em
  `pendente` há **mais** de X dias, contados a partir da sua data de criação
  (data de referência).
- **FR-003**: Quando um Ato fica atrasado, o sistema MUST avisar os **membros da
  Direção** com um aviso que inclui um título legível, a identificação do ato
  (descrição/tipo/valor), a sua antiguidade e uma ligação que leva à página para agir.
- **FR-004**: O valor de X MUST ser **configurável por administração** (definições),
  com um **valor por omissão de 7 dias** quando não foi alterado.
- **FR-005**: O sistema MUST avisar **uma única vez** por Ato, no momento em que este
  cruza o limiar — não repete o aviso em avaliações seguintes enquanto o ato
  continuar pendente.
- **FR-006**: O sistema MUST deixar de considerar um Ato assim que este deixa de
  estar `pendente` (aprovado, executado, rejeitado ou cancelado) — não gera (nem
  re-gera) avisos para ele.
- **FR-007**: O sistema MUST excluir contas técnicas e membros inativos dos
  destinatários, de forma consistente com a entrega de notificações existente.
- **FR-008**: Todo o texto ao utilizador MUST estar em português e o aviso MUST
  ligar à página relevante do item.
- **FR-009**: O sistema MUST comportar-se corretamente quando não há membros da
  Direção atribuídos (sem destinatários ⇒ sem erro; o resto do sistema continua).
- **FR-010**: O canal de entrega MUST ser o de **notificações in-app existente**
  (que, por desenho atual, é também espelhado no telemóvel via push para quem
  optou). Envio de **email fica fora do MVP** (condição de paragem: emails a sócios
  reais).

### Key Entities *(include if feature involves data)*

- **Ato** (entidade existente, Art. 54): o acto administrativo que requer ação dos
  órgãos; tem uma data de criação (referência da idade) e um estado (`pendente` →
  aprovado/executado/rejeitado/cancelado). Só interessa enquanto `pendente`.
- **Aviso/Notificação** (existente): a mensagem interna (título, resumo, ligação)
  entregue a cada membro da Direção; reutiliza o sistema de notificações do portal.
- **Limiar (X dias)**: o número de dias a partir do qual um Ato pendente é
  sinalizado; **definido por administração**, default 7 dias (ver FR-004).
- **Marca de "já avisado"**: registo de que um Ato já gerou o seu aviso, para
  garantir o "uma única vez" do FR-005 (sem re-avisar em avaliações seguintes).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das pendências que ultrapassam o limiar geram aviso à Direção,
  em até 24 horas após cruzarem o limiar.
- **SC-002**: Um membro da Direção consegue, a partir do aviso, abrir o item a
  tratar num único toque/clique.
- **SC-003**: Cada Ato atrasado gera **no máximo um aviso** (não um aviso por
  avaliação) — fadiga de notificações controlada.
- **SC-004**: 0 avisos gerados para itens já resolvidos.
- **SC-005**: O tempo médio entre uma pendência ultrapassar o limiar e receber a
  primeira ação da Direção diminui face ao período sem a funcionalidade.

## Assumptions

- "Direção" = os membros do órgão **Direção** (helpers de elegibilidade já existentes
  no portal, p. ex. `is_direcao`); não inclui automaticamente outros órgãos.
- A **data de referência** para a idade do Ato é a sua data de criação (`created_at`);
  um Ato nasce `pendente`, pelo que "pendente desde" coincide com a criação.
- O **canal é in-app** (espelhado para push pelo mecanismo existente); **email fora
  do MVP** por decisão de negócio e pela condição de paragem em emails a sócios.
- A funcionalidade **reutiliza** o sistema de notificações e as regras de exclusão
  (contas técnicas/inativos) já existentes.
- A avaliação periódica das pendências assenta num mecanismo de disparo recorrente
  (a definir no plano técnico); o âmbito desta spec é o **comportamento**, não o
  agendador concreto.
