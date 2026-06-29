# Feature Specification: Aviso de rejeição de Ato com o motivo

**Feature Branch**: `feature/aviso-rejeicao-ato`

**Created**: 2026-06-29

**Status**: Draft

**Input**: User description: "avisar proponente de Ato quando é rejeitado, com o motivo"

## User Scenarios & Testing *(mandatory)*

> Contexto de domínio: um **Ato** (Art. 54) é proposto por um sócio (o *proponente*)
> e depende de co-aprovação da Direção. Qualquer membro da Direção que decida
> **rejeitar** fecha o Ato como rejeitado (veto único). Hoje o proponente já recebe
> um aviso de que o Ato foi rejeitado, **mas sem qualquer indicação do porquê** — fica
> sem saber o que correu mal nem o que corrigir.

### User Story 1 - Proponente percebe porque o Ato foi rejeitado (Priority: P1)

Quando o Ato que propus é rejeitado por um membro da Direção, recebo um aviso
(in-app, espelhado no telemóvel se tiver push ativo) que **inclui o motivo** da
rejeição. Assim percebo a razão sem ter de perguntar a ninguém e posso agir
(corrigir e voltar a submeter, ou aceitar a decisão).

**Why this priority**: É o coração da feature e entrega valor sozinho. Sem o motivo,
o aviso atual é uma porta fechada sem explicação; com ele, o proponente fica autónomo.

**Independent Test**: Propor um Ato, ter um membro da Direção a rejeitá-lo com um
motivo, e confirmar que o proponente recebe um aviso que contém esse motivo (texto
legível) e uma ligação para ver o Ato.

**Acceptance Scenarios**:

1. **Given** um Ato `pendente` que propus, **When** um membro da Direção o rejeita
   indicando o motivo "Falta o comprovativo da despesa", **Then** recebo um aviso de
   rejeição que inclui esse motivo e uma ligação para o Ato.
2. **Given** que tenho push ativo no telemóvel, **When** o meu Ato é rejeitado com
   motivo, **Then** a notificação no telemóvel também reflete a rejeição e o motivo
   (espelho do aviso in-app).
3. **Given** que fui eu próprio (sendo da Direção) a registar a rejeição do meu Ato,
   **When** a rejeição é concluída, **Then** não recebo um aviso redundante (já conheço
   o motivo).

---

### User Story 2 - Motivo fica registado no Ato para consulta posterior (Priority: P2)

O motivo da rejeição fica **guardado no próprio Ato**, visível na vista de
co-aprovações, não apenas no aviso momentâneo. Assim o proponente (e quem possa ver
o Ato) consegue reler a razão mais tarde, mesmo depois de a notificação sair do
radar, e fica registo de responsabilidade (quem rejeitou e porquê).

**Why this priority**: Aumenta a durabilidade e a transparência da decisão, mas o
valor essencial (saber o porquê) já é entregue pela US1 via aviso.

**Independent Test**: Abrir um Ato rejeitado na vista de co-aprovações e confirmar
que mostra o motivo da rejeição e o autor da rejeição, sem depender do aviso.

**Acceptance Scenarios**:

1. **Given** um Ato que foi rejeitado com motivo, **When** abro o detalhe do Ato,
   **Then** vejo o motivo da rejeição e quem a registou.
2. **Given** um Ato ainda `pendente`, **When** abro o seu detalhe, **Then** não é
   apresentado qualquer motivo de rejeição.

---

### Edge Cases

- **Motivo vazio ou só com espaços**: a rejeição é recusada com mensagem clara — o
  motivo é obrigatório (FR-002); não existe rejeição "com motivo" mas sem conteúdo.
- **Motivo muito longo**: o sistema impõe um limite razoável de tamanho e rejeita
  acima dele com mensagem clara (sem truncar silenciosamente).
- **Proponente é conta inativa/técnica**: a entrega reutiliza o mecanismo de avisos
  existente, que já lida com estes casos; nenhum erro deve interromper a rejeição.
- **Proponente sem push**: o aviso in-app é entregue na mesma (push é espelho
  best-effort, não um requisito).
- **Atos já rejeitados antes desta feature**: não têm motivo associado e mantêm-se
  como estão (sem preenchimento retroativo).
- **Aprovação**: não é abrangida — aprovar não exige motivo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Quando um Ato transita para `rejeitado` por decisão de um membro da
  Direção, o sistema MUST entregar ao proponente um aviso de rejeição que **inclui o
  motivo** indicado por quem rejeitou.
- **FR-002**: O motivo de rejeição MUST ser **obrigatório**: o sistema recusa, com
  mensagem clara, uma rejeição sem motivo. Um motivo só com espaços é tratado como
  vazio e também é recusado. (Garante que o aviso ao proponente nunca sai sem razão —
  SC-001.)
- **FR-003**: O aviso ao proponente MUST conter o motivo em texto legível, a
  identificação do Ato em causa e uma ligação para o ver.
- **FR-004**: O motivo da rejeição MUST ficar **persistido associado ao Ato** (com a
  identificação de quem rejeitou), visível na vista de detalhe do Ato a quem tem
  permissão para o ver.
- **FR-005**: O sistema MUST impor um limite máximo de tamanho ao motivo e recusar,
  com mensagem clara, um motivo acima desse limite (sem truncar silenciosamente).
- **FR-006**: O sistema MUST reutilizar o canal de avisos existente (in-app, com
  espelho push quando o proponente o tiver ativo), sem criar um segundo aviso de
  rejeição duplicado.
- **FR-007**: O sistema MUST registar a rejeição e o seu motivo no histórico de
  auditoria, como já faz para a decisão sobre o Ato.
- **FR-008**: A feature MUST aplicar-se apenas a rejeições a partir da sua entrada em
  vigor; Atos rejeitados anteriormente mantêm-se sem motivo (sem preenchimento
  retroativo).
- **FR-009**: Aprovar um Ato MUST permanecer inalterado (não exige motivo).

### Key Entities *(include if feature involves data)*

- **Ato**: o ato de co-aprovação proposto por um sócio; passa a poder ter associado
  um **motivo de rejeição** e a identificação de quem rejeitou.
- **Decisão de rejeição** (assinatura de um membro da Direção sobre o Ato): passa a
  poder transportar o **motivo** indicado por quem rejeita.
- **Aviso ao proponente**: a mensagem entregue ao proponente quando o Ato é
  rejeitado; passa a carregar o motivo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos avisos de rejeição entregues ao proponente passam a conter a
  razão da rejeição (deixa de existir o aviso "foi rejeitado" sem o porquê).
- **SC-002**: O proponente consegue identificar o motivo da rejeição **sem contactar
  ninguém** — disponível no aviso e na vista do Ato.
- **SC-003**: O tempo para o proponente saber porque o Ato foi rejeitado passa de
  "depende de perguntar a um membro da Direção" para **imediato** (no momento da
  rejeição).
- **SC-004**: Numa validação com o dono, em ≥ 90% dos casos de teste o motivo
  apresentado é suficiente para o proponente decidir a ação corretiva, sem
  esclarecimentos adicionais.

## Assumptions

- Reutiliza a entrega de avisos existente (in-app + espelho push da spec 009); não há
  novo canal nem email no âmbito desta feature.
- Modelo de rejeição = **veto único** (qualquer membro da Direção que rejeite fecha o
  Ato); o motivo registado é o desse membro.
- O motivo é texto livre em português, com um limite de tamanho razoável (ordem de
  algumas centenas de carateres).
- A feature melhora o aviso de rejeição **já existente** (que hoje sai sem motivo),
  não cria um fluxo paralelo.
- **Decisão (Q1): motivo obrigatório** ao rejeitar — confirmado pelo dono 2026-06-29.
- Validação funcional ponta-a-ponta fica ao critério do dono (Princípio VII), após
  deploy.
