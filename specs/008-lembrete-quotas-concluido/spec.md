# Feature Specification: Lembrete informativo de quotas

**Feature Branch**: `008-lembrete-quotas`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "Lembrete/resumo automático e periódico das quotas para o sócio, de caráter INFORMATIVO (não é sobre inadimplência). Cada sócio recebe um lembrete com o resumo das suas quotas (confirmação do período, valor, total acumulado). Reutiliza /me/quotas e a infra de notificações. Canal principal: notificação in-app automática; email opcional e sujeito a confirmação do dono (STOP). O sócio pode controlar a preferência (opt-out)."

## Clarifications

### Session 2026-06-27

- Q: Modelo de disparo do lembrete? → A: **Orientado a evento** — quando a quota do
  período é registada/gerada para o sócio, o sistema notifica-o nesse momento. Liga-se
  à geração de quotas existente; sem novo agendador; idempotente por lançamento/período.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Receber o lembrete informativo de quota in-app (Priority: P1)

Um sócio é mantido informado sobre as suas contribuições sem ter de ir procurar:
recebe automaticamente, no portal, uma notificação que confirma a quota do período
(valor) e mostra o total acumulado pago — de tom informativo, nunca de cobrança.

**Why this priority**: É o coração da feature e entrega valor por si só (transparência).
O canal in-app não envolve envio a utilizadores reais, por isso é o MVP seguro.

**Independent Test**: Para um sócio com quota registada no período, disparar o
processo de lembrete e confirmar que recebe uma notificação in-app com o valor do
período e o total acumulado, com texto informativo.

**Acceptance Scenarios**:

1. **Given** um sócio ativo com quota registada no período, **When** o lembrete é
   gerado, **Then** o sócio recebe uma notificação in-app com a confirmação da quota
   (valor) e o total acumulado pago.
2. **Given** a notificação, **When** o sócio a abre, **Then** o tom é informativo
   (transparência) e leva à sua Carteira/quotas; nunca sugere dívida ou atraso.
3. **Given** os valores mostrados, **When** comparados com a Carteira do sócio,
   **Then** coincidem com `/me/quotas` (mesma fonte).

---

### User Story 2 - Controlar a preferência (opt-out) (Priority: P1)

Um sócio que não quer estes lembretes pode desativá-los nas suas preferências, de
forma coerente com as preferências de comunicação já existentes; quem opta por sair
deixa de os receber.

**Why this priority**: Respeito pela preferência do utilizador e requisito de
comunicação responsável; inseparável de um envio automático recorrente.

**Independent Test**: Desativar a preferência de um sócio e confirmar que, no disparo
seguinte, esse sócio NÃO recebe o lembrete; reativar e confirmar que volta a receber.

**Acceptance Scenarios**:

1. **Given** um sócio com a preferência de lembretes desativada, **When** o lembrete é
   gerado, **Then** esse sócio não recebe nada.
2. **Given** um sócio sem preferência definida, **When** o lembrete é gerado, **Then**
   recebe-o (opt-out, não opt-in — ativo por defeito).
3. **Given** a página de preferências, **When** o sócio a abre, **Then** encontra um
   controlo claro para ativar/desativar os lembretes de quota.

---

### User Story 3 - Envio por email (opcional, gated) (Priority: P3)

A administração pode, opcionalmente, fazer o lembrete chegar também por email — mas
como é envio a utilizadores reais, só acontece com confirmação explícita do dono e
respeitando a preferência (opt-out) do sócio.

**Why this priority**: Valor adicional (alcance), mas é uma **condição STOP** (envio a
utilizadores reais) e depende de US1/US2. Fica para o fim e atrás de um gate explícito.

**Independent Test**: Com o email desativado (default), confirmar que nenhum email é
enviado. Só após ativação explícita pela administração é que sócios sem opt-out
recebem o email; sócios com opt-out nunca recebem.

**Acceptance Scenarios**:

1. **Given** a configuração por defeito, **When** o lembrete é gerado, **Then**
   nenhum email é enviado (só in-app).
2. **Given** o email ativado explicitamente pela administração, **When** o lembrete é
   gerado, **Then** os sócios sem opt-out recebem também por email; os com opt-out não.

---

### Edge Cases

- **Sócio sem quota no período**: por defeito não recebe lembrete desse período (nada
  a confirmar) — não é tratado como "atraso".
- **Contas técnicas** (`account_type="technical"`, ex.: `admin@controlador.cv`): nunca
  recebem o lembrete (não são sócios).
- **Sócio `inativo`**: não recebe o lembrete (alinhado com a exclusão das comunicações
  dirigidas a membros ativos).
- **Disparo repetido no mesmo período**: o sócio não recebe lembretes duplicados para
  o mesmo período (idempotência).
- **Sócio em opt-out**: nunca recebe, nem in-app nem email.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST gerar, de forma automática e periódica, um lembrete
  informativo de quota para cada sócio elegível, com o valor da quota do período e o
  total acumulado pago.
- **FR-002**: O lembrete MUST ser entregue **in-app** (notificação) por defeito, com
  tom informativo (transparência) e ligação à Carteira/quotas — **nunca** linguagem de
  dívida, atraso ou inadimplência.
- **FR-003**: Os valores do lembrete MUST coincidir com a vista da carteira do sócio
  (`/me/quotas`): mesmos lançamentos e total.
- **FR-004**: O sócio MUST poder desativar/ativar a receção destes lembretes numa
  preferência clara, coerente com as preferências de comunicação existentes (opt-out;
  ativo por defeito).
- **FR-005**: Sócios com opt-out, contas técnicas e sócios `inativo` MUST ser excluídos
  do envio.
- **FR-006**: O sistema MUST evitar lembretes duplicados para o mesmo sócio e período
  (idempotência num disparo repetido).
- **FR-007**: O envio por **email** MUST estar **desativado por defeito** e só ocorrer
  após ativação explícita pela administração (condição STOP — envio a utilizadores
  reais); quando ativo, MUST respeitar o opt-out do sócio.
- **FR-008**: Um sócio sem quota registada no período MUST NÃO receber lembrete desse
  período (sem "atraso").
- **FR-009**: O lembrete MUST ser **orientado a evento**: quando a quota do período é
  registada/gerada para o sócio, o sistema notifica-o nesse momento (ligado ao fluxo de
  geração de quotas existente). Não há processo de lote agendado nem novo agendador na
  app. A idempotência (FR-006) é por lançamento/período. *(Decisão Q1, 2026-06-27.)*

### Key Entities *(include if feature involves data)*

- **Lembrete de quota**: um aviso informativo dirigido a um sócio para um período —
  referencia o(s) lançamento(s) de quota do período e o total acumulado. Marca de
  período para garantir idempotência (um por sócio/período).
- **Preferência de lembretes do sócio**: opção do sócio para receber/não receber estes
  lembretes (opt-out; ativa por defeito), coerente com as preferências de comunicação.
- **Lançamento de quota** (existente): pagamento efetivo de quota/jóia do sócio —
  fonte do valor e do total (mesma de `/me/quotas`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos sócios elegíveis (ativos, sem opt-out, com quota no período)
  recebem exatamente um lembrete in-app por período.
- **SC-002**: 0% de lembretes enviados a sócios com opt-out, contas técnicas ou sócios
  inativos.
- **SC-003**: Os valores do lembrete coincidem a 100% com a Carteira do sócio.
- **SC-004**: 0 lembretes duplicados por sócio/período num disparo repetido.
- **SC-005**: Nenhum email é enviado enquanto o email não for explicitamente ativado
  pela administração.
- **SC-006**: Um sócio consegue ativar/desativar a preferência e o efeito reflete-se no
  disparo seguinte.

## Assumptions

- **Sem inadimplência**: as quotas são descontadas em folha e o sistema não tem estado
  de atraso; o lembrete é **puramente informativo** (transparência). Linguagem de
  cobrança é proibida (alinhado com a convenção "sem `inadimplente`").
- **Periodicidade**: mensal por defeito (as quotas são mensais).
- **Fonte de dados**: a mesma vista que alimenta a Carteira (`/me/quotas`) — valor do
  período + total acumulado.
- **Canal in-app reutiliza a infra de notificações existente** (criação de notificação
  por sócio, com exclusão de contas técnicas), sem novo sistema.
- **Opt-out reutiliza/estende as preferências de comunicação do sócio** já existentes
  na página de Perfil.
- **"Automático" = orientado a evento** (Decisão Q1): o lembrete dispara ao registar a
  quota do período (ligado à geração de quotas existente), não por um agendador na app.
  A periodicidade resulta de as quotas serem mensais. Sem processo de lote.
- **Email é STOP**: qualquer envio real por email exige confirmação explícita do dono.
- **Elegível** = sócio `ativo`, `account_type` membro, sem opt-out, com quota no período.
