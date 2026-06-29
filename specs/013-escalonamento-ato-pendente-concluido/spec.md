# Feature Specification: Escalonamento de lembretes de Ato (Art. 54) pendente

**Feature Branch**: `feature/escalonamento-ato-pendente`

**Created**: 2026-06-29

**Status**: Draft

**Input**: User description: "Escalonamento de Atos (Art. 54) que continuam pendentes muito além do limiar X. Hoje a spec 010 avisa a Direção uma única vez e a spec 012 avisa também o proponente, uma única vez (marca partilhada `overdue_notified_at`); depois disso não acontece mais nada e o Ato pode ficar esquecido. Esta feature acrescenta follow-up recorrente/escalonado enquanto o Ato permanecer parado."

## User Scenarios & Testing *(mandatory)*

> Contexto de domínio: um **Ato** (Art. 54) é proposto por um sócio (o *proponente*) e
> fica `pendente` enquanto aguarda as assinaturas da Direção. A **spec 010** avisa a
> **Direção** quando um Ato está pendente há mais de **X dias** (X admin-configurável,
> default 7) e a **spec 012** avisa também o **proponente** — em ambos os casos **uma
> única vez** por Ato. Hoje, passado esse primeiro aviso, **o sistema cala-se**: se a
> Direção nunca assinar, o Ato pode arrastar-se indefinidamente sem que ninguém volte a
> ser lembrado. Esta feature fecha esse buraco: **continuar a lembrar** (e, conforme o
> tempo parado, **aumentar a pressão**) enquanto o Ato continuar encalhado.

### User Story 1 - O Ato encalhado continua a ser lembrado (Priority: P1) 🎯 MVP

Enquanto um Ato que aguarda a Direção permanecer `pendente` muito além do limiar X, os
responsáveis (Direção, e o proponente que o criou) **voltam a ser lembrados
periodicamente** — não apenas uma vez. Assim um Ato verdadeiramente parado não cai no
esquecimento depois do primeiro aviso.

**Why this priority**: É o coração da feature e entrega valor sozinho — transforma o
aviso único (010/012) num follow-up que persiste até o Ato ser decidido. Sem isto, o
ponto cego ("avisou uma vez e esqueceu") continua aberto.

**Independent Test**: Criar um Ato, deixá-lo pendente além do limiar (primeiro aviso
disparado) e continuar a deixá-lo parado; confirmar que, na cadência definida, os
responsáveis recebem **novos** lembretes (com a antiguidade atualizada), e que um Ato
que é decidido deixa imediatamente de gerar lembretes.

**Acceptance Scenarios**:

1. **Given** um Ato pendente já avisado uma vez (010/012) e ainda parado, **When** passa
   o intervalo de recorrência e a avaliação corre, **Then** os responsáveis recebem um
   **novo** lembrete que reflete a antiguidade atual do Ato.
2. **Given** o mesmo Ato dentro do intervalo de recorrência (ainda não venceu o próximo
   lembrete), **When** a avaliação corre, **Then** **não** é enviado lembrete repetido
   (evita spam diário).
3. **Given** um Ato que **deixou de estar pendente** (aprovado/rejeitado/executado/
   cancelado), **When** a avaliação corre, **Then** **nenhum** lembrete adicional é
   enviado sobre esse Ato.
4. **Given** push ativo no destinatário, **When** recebe um lembrete recorrente, **Then**
   a notificação aparece também no telemóvel (espelho do in-app, como nas specs 010/012).

---

### User Story 2 - A pressão aumenta com o tempo parado (Priority: P2)

Quanto mais tempo um Ato fica parado, **maior a urgência** do lembrete: a mensagem
sinaliza-o como cada vez mais atrasado (a antiguidade em dias, sempre atualizada, comunica
o agravamento). Os **destinatários mantêm-se** sempre a Direção + o proponente (decisão do
dono: **sem** alargar a outros órgãos — mantém o desenho mínimo e não acopla a governança).

**Why this priority**: Distingue "escalonamento" de mera "repetição": um Ato parado há 60
dias merece sinal mais forte do que um parado há 14. Entrega valor incremental sobre US1
mas US1 sozinha já é um MVP utilizável.

**Independent Test**: Deixar um Ato parado além do(s) marco(s) de escalonamento e
confirmar que o lembrete reflete a urgência acrescida (e, se aplicável, atinge os
destinatários alargados) sem afetar o comportamento de US1 para Atos pouco atrasados.

**Acceptance Scenarios**:

1. **Given** um Ato parado além do marco de escalonamento, **When** o lembrete é gerado,
   **Then** a sua urgência/alcance reflete o maior atraso (vs. um Ato apenas ligeiramente
   atrasado).

---

### User Story 3 - O follow-up não vira spam (Priority: P3)

O sistema **não** inunda os responsáveis: a cadência de X dias garante **no máximo um
lembrete por Ato por janela de X dias** — nunca diário —, equilibrando "não esquecer" com
"não incomodar". (Não há teto de lembretes: a paragem é a **decisão** do Ato, não um limite
artificial.)

**Why this priority**: Salvaguarda de qualidade — sem ela, US1 corre o risco de gerar
ruído e ser silenciada pelos utilizadores, anulando o valor. É refinamento, não MVP.

**Independent Test**: Deixar um Ato parado por muito tempo e confirmar que o número/cadência
de lembretes respeita o limite definido (não há lembrete diário nem indefinido sem regra).

**Acceptance Scenarios**:

1. **Given** um Ato parado por um período prolongado, **When** as avaliações diárias
   correm, **Then** há no máximo um lembrete por janela de X dias (nunca dois no mesmo dia,
   nunca diário).

---

### Edge Cases

- **Atos já avisados pelas specs 010/012 antes desta feature**: continuam a entrar na
  recorrência a partir da entrada em vigor (o primeiro aviso já dado conta como o
  lembrete 1; o próximo segue a cadência), sem reprocessamento retroativo em massa.
- **Conta destinatária inativa/técnica**: excluída dos lembretes (consistente com
  010/012); não gera erro nem interrompe a avaliação.
- **Proponente que é membro da Direção**: continua a receber **um** lembrete por ciclo
  (sem duplicar o lembrete de proponente com o da Direção — dedup da spec 012 mantém-se).
- **Limiar X alterado pelo admin** a meio da vida de um Ato: a antiguidade é sempre
  recalculada contra a data de criação do Ato e o X corrente; a recorrência não "perde"
  nem "duplica" por causa da mudança.
- **Reinício do serviço**: a avaliação é idempotente o suficiente para que reiniciar não
  gere uma rajada de lembretes repetidos (reutiliza o disparo diário existente).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Enquanto um Ato permanecer `pendente` para além do limiar X, o sistema MUST
  voltar a lembrar os responsáveis **mais do que uma vez**, em vez de avisar só uma vez
  (comportamento atual das specs 010/012).
- **FR-002**: A cadência da recorrência MUST ser **a cada X dias**, reutilizando o mesmo
  limiar X (`ato_overdue_dias`, default 7): enquanto o Ato continuar pendente, há um novo
  lembrete sempre que passam X dias desde o anterior (1.º aviso a > X dias, o seguinte a
  > 2X, depois > 3X, …). **Sem novo limiar nem configuração** própria.
- **FR-003**: Cada lembrete recorrente MUST identificar o Ato (descrição/tipo/valor) e a
  **antiguidade atual em dias**, e MUST incluir uma ligação para o ver/agir (paridade com
  o conteúdo dos avisos 010/012).
- **FR-004**: Os destinatários-base do lembrete recorrente MUST ser os mesmos das specs
  010/012 — a **Direção** e o **proponente** (`created_by`) — com a mesma deduplicação
  (quem é proponente E Direção recebe um único lembrete por ciclo).
- **FR-005**: A "pressão crescente" MUST manifestar-se **apenas no conteúdo/urgência da
  mensagem** — a antiguidade em dias, sempre atualizada, comunica o agravamento. Os
  **destinatários NÃO se alargam** para além da Direção + proponente (decisão do dono —
  evita acoplar a governança/`permissions.py`).
- **FR-006**: A recorrência MUST continuar **até o Ato sair de `pendente`** (ser decidido)
  — **sem teto** de número de lembretes. A cadência de X dias (FR-002) é o único regulador
  (evita spam); não há limite artificial que faça o sistema "desistir" de um Ato encalhado.
- **FR-007**: O lembrete recorrente MUST aplicar-se apenas a Atos em estado `pendente`; um
  Ato que sai de `pendente` MUST deixar imediatamente de gerar lembretes.
- **FR-008**: Contas `technical`/`inativo` MUST ser excluídas dos destinatários.
- **FR-009**: A entrega MUST usar o canal existente (in-app, com espelho push quando
  ativo). **Email continua fora do âmbito** (consistente com 008/010/012).
- **FR-010**: A avaliação MUST ser não-fatal e idempotente o suficiente para que reiniciar
  o serviço, ou correr a avaliação mais do que uma vez no mesmo dia, não gere lembretes
  repetidos indevidos (reutiliza o disparo diário existente da spec 010).

### Key Entities *(include if feature involves data)*

- **Ato**: o ato de co-aprovação; tem proponente (`created_by`), estado (`pendente`/…) e
  data de criação. Já carrega a marca de "primeiro aviso dado" das specs 010/012.
- **Lembrete recorrente**: cada nova mensagem entregue aos responsáveis enquanto o Ato
  continua parado; difere do "primeiro aviso" por ser repetível e refletir a antiguidade
  crescente.
- **Estado de recorrência por Ato**: o que o sistema regista por Ato para saber **quando**
  enviar o próximo lembrete e **quantos** já enviou (sem isto não há cadência nem paragem).
- **Limiar X (dias)** e **cadência/marcos**: configuração que define "muito além de X" e
  o ritmo do follow-up.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos Atos que permanecem pendentes além do limiar recebem **mais do que
  um** lembrete enquanto não forem decididos (hoje recebem exatamente um).
- **SC-002**: Para um Ato parado, o intervalo entre lembretes sucessivos respeita a
  cadência definida — **nunca há dois lembretes do mesmo Ato no mesmo dia** nem lembretes
  fora do ritmo combinado.
- **SC-003**: Assim que um Ato deixa de estar `pendente`, **zero** lembretes adicionais
  são enviados sobre ele.
- **SC-004**: A introdução da recorrência **não altera** o primeiro aviso já existente das
  specs 010/012 (Direção e proponente continuam a ser avisados a primeira vez como antes).
- **SC-005**: Os lembretes de um Ato só cessam quando ele deixa de estar `pendente`;
  enquanto pendente, há **no máximo um lembrete por janela de X dias** (sem lembrete diário,
  sem desistência antes da decisão).

## Assumptions

- Reutiliza a infraestrutura das specs 010/012: o **disparo diário** in-process existente,
  o **limiar X** (`ato_overdue_dias`, default 7), os destinatários **Direção**
  (`members_of_orgao('direcao')`) + **proponente** (`created_by`), e a entrega in-app
  (+push). **Não** se cria novo agendador.
- O **estado de recorrência** por Ato reaproveita a marca existente `overdue_notified_at`
  (specs 010/012) como **timestamp do último lembrete**, em vez de marca single-shot: a
  condição de varrimento passa de "nunca avisado" para "nunca avisado **OU** já passaram X
  dias desde o último lembrete". **Sem campo novo, sem migração, sem nova coleção** — só
  muda a lógica do varrimento diário; cada lembrete atualiza a marca para "agora".
- O primeiro aviso (specs 010/012) conta como o **lembrete nº 1**; a recorrência começa a
  partir daí (passado mais X dias).
- **Backend-only**, zero dependências novas, sem frontend. Email fora do âmbito.
- Toca em `backend/` ⇒ a release `develop→main` exigirá **Via B**.
- Validação funcional ponta-a-ponta fica ao critério do dono (Princípio VII).
