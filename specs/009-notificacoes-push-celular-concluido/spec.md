# Feature Specification: Notificações Push no Celular (Web Push / PWA)

**Feature Branch**: `claude/mobile-push-notifications-i2qx2k`

**Created**: 2026-06-28

**Status**: Implementada (documentação retroativa — PR #362)

**Input**: User description: "Notificações push no celular (Web Push / PWA). Espelhar todas as notificações in-app no dispositivo do sócio, entregues à tela mesmo com a app fechada (Android e desktop via navegador; iPhone a partir do iOS 16.4 apenas com o PWA adicionado à Tela de Início). Ativação por opt-in explícito, por dispositivo, num toggle 'Notificações no Celular' no Perfil, ao lado das preferências de email. No iPhone antes de instalar o PWA, mostrar uma instrução 'Adicionar à Tela de Início'. Degradar graciosamente sem chaves VAPID. Validar o endpoint (anti-SSRF). Podar subscrições mortas. Sem email no MVP."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Receber avisos no celular com a app fechada (Priority: P1)

Um sócio que hoje só vê as notificações quando tem o portal aberto quer ser
avisado no telemóvel — na bandeja do sistema — quando algo relevante acontece
(um comunicado, um lançamento financeiro, um evento, uma votação), mesmo sem
ter o portal aberto.

**Why this priority**: É o coração da funcionalidade — sem entrega com a app
fechada, não há "push no celular", apenas o que já existia (in-app/SSE). Entrega
valor imediato: o sócio deixa de perder avisos por não ter o portal aberto.

**Independent Test**: Com a feature ativada num dispositivo, gerar qualquer
notificação interna (ex.: um comunicado) e confirmar que aparece na bandeja do
sistema com a app fechada, e que tocar nela abre o portal no ecrã relevante.

**Acceptance Scenarios**:

1. **Given** um sócio com notificações no celular ativadas e a app fechada,
   **When** o sistema cria uma notificação interna para ele,
   **Then** o aviso aparece na bandeja do telemóvel com título e resumo.
2. **Given** uma notificação push recebida na bandeja,
   **When** o sócio toca nela,
   **Then** o portal abre (ou foca) na página associada ao aviso.
3. **Given** vários avisos enquanto a app está fechada (ex.: um comunicado e
   depois um evento),
   **When** o sócio olha para a bandeja,
   **Then** vê os avisos como entradas separadas (um não substitui o outro).

### User Story 2 - Ativar/desativar por dispositivo no Perfil (Priority: P1)

O sócio quer controlar, por dispositivo, se recebe notificações no celular,
ligando ou desligando explicitamente — porque o navegador só pede permissão
após um gesto seu e a decisão é pessoal.

**Why this priority**: Sem um ponto de ativação claro e consentido, ninguém
recebe push (o opt-in do navegador é obrigatório). É a porta de entrada para a
US1 e respeita privacidade/consentimento.

**Independent Test**: No Perfil, ligar o interruptor "Notificações no Celular",
conceder a permissão do navegador, e confirmar que o estado fica "ligado";
desligar e confirmar que deixa de receber.

**Acceptance Scenarios**:

1. **Given** um sócio no Perfil num dispositivo suportado,
   **When** liga o interruptor e concede a permissão,
   **Then** o dispositivo fica registado e o interruptor mostra-se ligado.
2. **Given** a permissão de notificações negada pelo sócio,
   **When** tenta ligar,
   **Then** recebe uma mensagem clara de que a permissão é necessária e o
   interruptor permanece desligado.
3. **Given** um dispositivo com notificações ativadas,
   **When** o sócio desliga o interruptor,
   **Then** o dispositivo deixa de receber push e o registo é removido.

### User Story 3 - Orientação no iPhone antes de instalar o PWA (Priority: P2)

Um sócio em iPhone, no Safari, antes de adicionar o portal à Tela de Início,
precisa de saber por que não consegue ativar e o que fazer — em vez de ver um
interruptor que não funciona ou nada.

**Why this priority**: Sem isto, a maior base de utilizadores móveis (iOS) fica
confusa ou excluída. Não é P1 porque não bloqueia Android/desktop, mas é
essencial para a adoção em iPhone.

**Independent Test**: Abrir o portal num iPhone via Safari (sem PWA instalado) e
confirmar que, em vez do interruptor, aparece a instrução para "Adicionar à Tela
de Início".

**Acceptance Scenarios**:

1. **Given** um sócio em iPhone/Safari sem o PWA instalado,
   **When** abre a secção de notificações no Perfil,
   **Then** vê uma instrução curta para adicionar o portal à Tela de Início.
2. **Given** o mesmo sócio depois de instalar o PWA (iOS 16.4+) e abrir pelo
   ícone,
   **When** volta ao Perfil,
   **Then** vê o interruptor normal e consegue ativar.

### Edge Cases

- **Sem suporte do dispositivo** (navegador antigo de desktop sem push): a
  secção de notificações no celular não é mostrada (nada a oferecer).
- **Feature não configurada pela organização** (sem chaves de assinatura): a
  ativação não está disponível e o sistema continua a funcionar normalmente,
  sem erros — as notificações in-app mantêm-se intactas.
- **Subscrição expirada/revogada** (o sócio limpou dados, desinstalou o PWA, ou
  o serviço de push invalidou): o envio falha graciosamente e o registo morto é
  removido automaticamente, sem afetar os restantes dispositivos.
- **Mesmo dispositivo, troca de conta**: re-ativar substitui o registo anterior
  e passa a apontar para a conta atual (um registo por dispositivo/navegador).
- **Endpoint de subscrição inválido/malicioso**: um pedido com um destino que
  não seja um serviço público de push é recusado e nunca é guardado.
- **Conta técnica/inativa**: contas de sistema e sócios inativos não recebem
  push (consistente com a entrega in-app existente).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST entregar, no dispositivo do sócio e na bandeja do
  sistema operativo, um aviso correspondente a **cada** notificação interna
  criada para esse sócio, mesmo com a aplicação fechada (nos dispositivos e
  navegadores que o suportam).
- **FR-002**: O aviso MUST conter um título e um resumo legíveis e MUST permitir
  que, ao ser tocado, o portal abra (ou foque) na página associada ao aviso.
- **FR-003**: O sócio MUST poder ativar e desativar as notificações no celular
  **por dispositivo**, a partir de um controlo no Perfil, junto das preferências
  de email.
- **FR-004**: A ativação MUST exigir o consentimento explícito do sócio (gesto +
  permissão do navegador); o sistema MUST NOT tentar ativar sem essa ação.
- **FR-005**: Quando a permissão for negada, o sistema MUST informar o sócio de
  forma clara e manter o estado desativado.
- **FR-006**: Em iPhone antes de o portal estar instalado como PWA, o sistema
  MUST apresentar uma instrução para "Adicionar à Tela de Início" em vez de um
  controlo de ativação não funcional.
- **FR-007**: Em dispositivos sem suporte real a push, o sistema MUST omitir o
  controlo, sem erros.
- **FR-008**: O sistema MUST degradar graciosamente quando a funcionalidade não
  estiver configurada pela organização: a ativação fica indisponível e todo o
  resto (notificações in-app) continua a funcionar.
- **FR-009**: O sistema MUST recusar e não guardar subscrições cujo destino não
  seja um serviço público de push (proteção contra abuso/SSRF).
- **FR-010**: O sistema MUST remover automaticamente subscrições mortas
  (expiradas/revogadas) detetadas no envio, sem afetar outros dispositivos do
  mesmo sócio nem outros sócios.
- **FR-011**: O sistema MUST excluir contas técnicas e sócios inativos da
  entrega de push, de forma consistente com a entrega in-app.
- **FR-012**: O sócio MUST poder confirmar que a ativação funcionou através de um
  aviso de teste enviado ao próprio dispositivo.
- **FR-013**: A funcionalidade MUST NOT enviar email no MVP (canal exclusivamente
  push/in-app).

### Key Entities *(include if feature involves data)*

- **Subscrição de Push**: representa a autorização de um dispositivo/navegador
  específico para receber avisos. Pertence a um sócio, é única por dispositivo,
  e guarda o destino de entrega e as credenciais necessárias para cifrar o
  aviso. É criada na ativação, atualizada na re-ativação e removida na
  desativação ou quando se torna inválida.
- **Notificação** (existente): o aviso interno do portal (tipo, título, resumo,
  ligação) que passa a ser também espelhado como push.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um sócio consegue ativar as notificações no celular em menos de 30
  segundos, num único ecrã (Perfil), sem ajuda externa.
- **SC-002**: Após ativar, um aviso de teste chega à bandeja do dispositivo em
  poucos segundos, com a aplicação fechada.
- **SC-003**: 100% das notificações internas criadas para um sócio com a feature
  ativada geram um push no(s) seu(s) dispositivo(s) registado(s) válido(s).
- **SC-004**: Quando a organização não configura a funcionalidade, 0 erros são
  visíveis ao utilizador e a experiência in-app permanece inalterada.
- **SC-005**: Subscrições inválidas detetadas no envio são removidas
  automaticamente, mantendo a taxa de falhas de envio repetidas perto de 0.
- **SC-006**: Sócios em iPhone sem o PWA instalado recebem orientação acionável
  (instrução de instalação) em 100% dos casos, em vez de um controlo inoperante.

## Assumptions

- O portal já é instalável como PWA e tem um service worker ativo em produção
  (base sobre a qual o push assenta).
- A entrega assenta no mecanismo de Web Push dos navegadores; no iPhone só
  funciona a partir do iOS 16.4 e apenas com o PWA na Tela de Início (limitação
  da plataforma, não do portal).
- O âmbito do MVP é "espelhar todas as notificações in-app" com um opt-in
  **global por dispositivo**; preferências por tipo de notificação ficam fora do
  âmbito.
- A organização gera e configura as credenciais de assinatura (VAPID) no
  ambiente de produção antes de a funcionalidade ficar disponível aos sócios.
- A entrega por email continua fora de âmbito (decisão do dono), mantendo-se a
  stop condition de emails a sócios reais.
- A taxonomia de notificações e as regras de exclusão (contas técnicas/inativos)
  reutilizam o sistema de notificações existente.
