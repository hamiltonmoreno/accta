# Feature Specification: Lembrete de Ato pendente ao próprio proponente

**Feature Branch**: `feature/aviso-proponente-ato-pendente`

**Created**: 2026-06-29

**Status**: Draft

**Input**: User description: "Lembrar o próprio proponente de um Ato (Art. 54) quando o seu Ato fica pendente (a aguardar assinaturas da Direção) há mais de X dias. Hoje a spec 010 avisa a Direção dos Atos pendentes atrasados, mas o proponente que criou o Ato não recebe qualquer aviso de que está parado."

## User Scenarios & Testing *(mandatory)*

> Contexto de domínio: um **Ato** (Art. 54) é proposto por um sócio (o *proponente*)
> e fica `pendente` enquanto aguarda as assinaturas da Direção. A **spec 010** já
> avisa a **Direção** quando um Ato está pendente há mais de **X dias** (X
> admin-configurável, default 7), uma única vez por Ato. **O proponente — quem
> criou o Ato — não recebe nada**, e por isso pode não perceber que o seu pedido
> está parado à espera de ação de outros.

### User Story 1 - Proponente é avisado de que o seu Ato está parado (Priority: P1)

Quando o Ato que propus continua `pendente` há mais de X dias, recebo um aviso
(in-app, espelhado no telemóvel se tiver push ativo) a dizer que ainda aguarda
assinaturas da Direção. Assim percebo que está parado e posso agir (lembrar a
Direção, corrigir/cancelar, ou aguardar com conhecimento de causa) em vez de
assumir que já seguiu.

**Why this priority**: É o coração da feature e entrega valor sozinho — fecha o
ponto cego do proponente, que hoje não tem qualquer sinal de que o Ato encalhou.

**Independent Test**: Criar um Ato, deixá-lo pendente além do limiar X, e confirmar
que o proponente recebe um aviso que identifica o Ato, a antiguidade e uma ligação
para o ver.

**Acceptance Scenarios**:

1. **Given** um Ato que propus, ainda `pendente` há mais de X dias, **When** a
   avaliação diária corre, **Then** recebo um aviso de que o meu Ato continua a
   aguardar a Direção, com a antiguidade em dias e uma ligação para o Ato.
2. **Given** que tenho push ativo, **When** sou avisado do meu Ato parado, **Then** a
   notificação aparece também no telemóvel (espelho do aviso in-app).
3. **Given** um Ato meu que **deixou de estar pendente** (aprovado/rejeitado/
   executado/cancelado), **When** a avaliação corre, **Then** **não** recebo aviso de
   "parado" sobre esse Ato.
4. **Given** que sou eu próprio (sendo da Direção) o proponente do Ato, **When** sou
   avisado, **Then** recebo **um único** aviso por Ato e não dois (não duplicar o
   aviso ao proponente com o aviso à Direção da spec 010).

---

### Edge Cases

- **Proponente é conta inativa/técnica**: a entrega reutiliza o mecanismo de avisos
  existente; não deve gerar erro nem interromper a avaliação. (Conta `technical` não
  cria Atos no fluxo normal; defensivamente, não se avisa.)
- **Ato sem `created_at` fiável**: ignora-se com segurança (não dispara com base em
  data não fiável), tal como na spec 010.
- **Proponente sem push**: o aviso in-app é entregue na mesma (push é espelho
  best-effort, não requisito).
- **Atos já marcados pela spec 010**: um Ato cujo `overdue_notified_at` já foi gravado
  (Direção avisada antes desta feature) **não** re-dispara para avisar o proponente —
  a marca é partilhada (sem reprocessamento retroativo). Aplica-se a Atos que cruzem o
  limiar a partir da entrada em vigor.
- **Proponente == quem assina**: irrelevante para o aviso de "pendente" (o gatilho é a
  ausência de decisão final, não quem assinou).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Quando um Ato continua `pendente` há **mais de X dias** (X =
  configuração existente da spec 010, default 7), o sistema MUST avisar **o
  proponente** (quem o criou) de que o Ato ainda aguarda assinaturas da Direção.
- **FR-002**: O aviso ao proponente MUST identificar o Ato (descrição/tipo/valor), a
  **antiguidade em dias** e MUST incluir uma ligação para o ver.
- **FR-003**: O sistema MUST entregar o aviso pelo canal existente (in-app, com
  espelho push quando o proponente o tiver ativo). **Email fora do âmbito.**
- **FR-004**: O sistema MUST avisar o proponente **uma única vez por Ato** —
  espelhando a regra da spec 010 para a Direção — no **mesmo evento de avaliação** em
  que o Ato cruza o limiar X. Reutiliza a marca de idempotência existente
  (`overdue_notified_at`): o proponente entra como destinatário adicional na avaliação
  já existente, não havendo lembretes recorrentes.
- **FR-005**: O sistema MUST evitar **duplicação** quando o proponente também é membro
  da Direção: para o mesmo Ato e mesmo evento de aviso, o proponente recebe **um**
  aviso, não o aviso de proponente **e** o aviso de Direção (spec 010) em separado.
- **FR-006**: O aviso MUST aplicar-se apenas a Atos em estado `pendente`; um Ato que
  saiu de `pendente` MUST deixar de gerar avisos de "parado".
- **FR-007**: Contas `technical`/`inativo` MUST ser excluídas dos destinatários.
- **FR-008**: A avaliação MUST ser não-fatal e idempotente o suficiente para que
  reiniciar o serviço não gere avisos repetidos indevidos (reutiliza o disparo diário
  já existente da spec 010).

### Key Entities *(include if feature involves data)*

- **Ato**: o ato de co-aprovação; tem um **proponente** (quem o criou) e um estado
  (`pendente`/…). Já carrega a marca de "Direção avisada" da spec 010.
- **Aviso ao proponente**: a mensagem entregue a quem criou o Ato quando este está
  pendente além do limiar.
- **Limiar X (dias)**: configuração existente (spec 010) que define "mais de X dias".

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos Atos que estão pendentes além do limiar geram um aviso ao
  respetivo proponente (que hoje não recebe nada).
- **SC-002**: O proponente fica a saber que o seu Ato está parado **sem ter de
  perguntar a ninguém** nem abrir a área de co-aprovações por iniciativa própria.
- **SC-003**: Para um dado Ato e evento de cadência, o proponente recebe **no máximo
  um** aviso de "parado" (sem duplicação com o aviso à Direção).
- **SC-004**: A introdução do aviso ao proponente **não altera** o comportamento já
  existente do aviso à Direção (spec 010) — esta continua a ser avisada como antes.

## Assumptions

- Reutiliza a infraestrutura da spec 010: o **disparo diário** existente
  (avaliação de Atos pendentes atrasados), o **limiar X** (`ato_overdue_dias`,
  default 7) e a entrega in-app (+push). **Não** se cria novo agendador nem novo
  limiar.
- O proponente é o criador do Ato (`created_by`).
- O aviso ao proponente acontece **no mesmo evento de avaliação** em que a Direção é
  avisada (mesmo limiar X) e **uma única vez** por Ato (Q1=A, dono — partilha a marca
  `overdue_notified_at` da spec 010; sem lembretes recorrentes).
- Sem novo endpoint obrigatório; o disparo é automático (com o disparo manual de
  verificação da spec 010 a poder cobrir também este aviso).
- Email continua fora do âmbito (decisão consistente com as specs 008/010).
- Validação funcional ponta-a-ponta fica ao critério do dono (Princípio VII).
