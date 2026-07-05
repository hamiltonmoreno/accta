# Feature Specification: Funções personalizadas com privilégios à medida

**Feature Branch**: `017-funcoes-personalizadas`

**Created**: 2026-07-02

**Status**: Draft

**Input**: User description: "Funções personalizadas com privilégios à medida: o admin quer poder criar 'funções' novas (para além das 4 fixas: admin, financeiro, moderador, socio) e atribuir-lhes um conjunto personalizado de privilégios, para depois aplicar essas funções a sócios. Hoje a 'Função no Sistema' só tem 4 opções e o ajuste fino é feito privilégio a privilégio por utilizador; o dono quer poder definir uma vez uma função nomeada (ex.: 'Coordenador de Eventos' = manage_events + manage_documents) e reutilizá-la em vários sócios."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Criar e gerir funções personalizadas (Priority: P1)

O administrador acede a uma área de «Funções personalizadas» na gestão de utilizadores, cria uma função com um nome próprio (ex.: «Coordenador de Eventos»), uma descrição opcional e um conjunto de privilégios escolhidos do catálogo existente. Pode depois listar, editar e eliminar funções personalizadas. As 4 funções fixas (Administração, Financeiro, Moderador, Sócio) continuam a existir e não são editáveis nem elimináveis.

**Why this priority**: é a fundação — sem o catálogo de funções personalizadas não há nada para aplicar aos sócios.

**Independent Test**: criar uma função «Coordenador de Eventos» com 2 privilégios, vê-la na listagem com os privilégios legíveis, editar-lhe o nome, e confirmar que as 4 funções fixas aparecem separadas e sem ações de edição/eliminação.

**Acceptance Scenarios**:

1. **Given** um admin autenticado, **When** cria uma função com nome único e ≥1 privilégio do catálogo, **Then** a função fica disponível na listagem com nome, descrição e privilégios legíveis (rótulos PT).
2. **Given** uma função personalizada existente, **When** o admin tenta criar outra com o mesmo nome, **Then** o sistema recusa com mensagem clara de nome duplicado.
3. **Given** uma função personalizada, **When** o admin a edita (nome, descrição, privilégios), **Then** as alterações ficam gravadas e auditadas.
4. **Given** as 4 funções fixas, **When** o admin abre a gestão de funções, **Then** não existe qualquer ação de editar/eliminar sobre elas.

---

### User Story 2 - Aplicar uma função personalizada a um sócio (Priority: P1)

Ao editar um sócio (e ao convidar um novo utilizador), o campo «Função no Sistema» passa a oferecer, além das 4 funções fixas, as funções personalizadas criadas pelo admin. Ao selecionar uma função personalizada, o sócio passa a ter exatamente o acesso definido por essa função.

**Why this priority**: é o valor visível da feature — definir uma vez, reutilizar em vários sócios sem marcar privilégios um a um.

**Independent Test**: aplicar a função «Coordenador de Eventos» a um sócio e verificar que ele passa a conseguir gerir eventos e documentos, e nada mais além do acesso base de sócio.

**Acceptance Scenarios**:

1. **Given** uma função personalizada criada, **When** o admin edita um sócio, **Then** a função aparece na lista de «Função no Sistema» junto às 4 fixas, claramente distinguível.
2. **Given** um sócio com a função «Coordenador de Eventos» aplicada, **When** o sócio inicia sessão, **Then** tem acesso aos módulos concedidos pelos privilégios da função e não perde o acesso base de sócio.
3. **Given** um sócio com função personalizada, **When** o admin lhe volta a atribuir uma das 4 funções fixas, **Then** o acesso reverte para o comportamento atual (função fixa + privilégios individuais).
4. **Given** a atribuição de uma função personalizada, **When** ela acontece, **Then** fica registada na auditoria (quem, a quem, que função).

---

### User Story 3 - Ciclo de vida: edição e eliminação com sócios afetados (Priority: P2)

O admin precisa de perceber o impacto de alterar ou eliminar uma função que já está aplicada a sócios: a listagem mostra quantos sócios têm cada função, e a eliminação é protegida quando a função está em uso.

**Why this priority**: evita estados incoerentes (sócios a apontar para funções inexistentes) mas só é relevante depois de US1+US2 existirem.

**Independent Test**: aplicar uma função a 2 sócios, confirmar a contagem «2 sócios» na listagem, tentar eliminá-la e receber recusa com indicação de uso; retirar a função aos 2 sócios e eliminar com sucesso.

**Acceptance Scenarios**:

1. **Given** uma função aplicada a 2 sócios, **When** o admin abre a listagem de funções, **Then** vê a contagem de sócios com essa função.
2. **Given** uma função aplicada a ≥1 sócio, **When** o admin tenta eliminá-la, **Then** o sistema recusa e indica quantos sócios a têm.
3. **Given** uma função sem sócios atribuídos, **When** o admin a elimina, **Then** a função desaparece da listagem e do seletor «Função no Sistema», com registo em auditoria.

---

### Edge Cases

- Função criada com 0 privilégios: recusada — uma função sem privilégios é equivalente a «Sócio» e só gera confusão.
- Nome de função personalizada igual a uma das 4 fixas (ex.: «Financeiro»): recusado como duplicado.
- Sócio com cargo estatutário (ex.: Tesoureiro) **e** função personalizada: o botão «Aplicar predefinições do cargo» continua a funcionar e, se usado, substitui a função personalizada pelos defaults do cargo — o admin é avisado antes.
- Edição de uma função personalizada em uso: propaga a todos os sócios que a têm (ligação viva — decisão Q1); a UI mostra quantos sócios serão afetados antes de guardar.
- Conta técnica (ex.: admin@controlador.cv): fora do âmbito — funções personalizadas aplicam-se a contas de membro geridas pelo admin.
- Privilégio que deixe de existir no catálogo no futuro: a função continua válida ignorando o privilégio desconhecido (sem quebrar o acesso restante).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST permitir ao admin criar funções personalizadas com nome único (após normalização de maiúsculas/espaços), descrição opcional e um conjunto de ≥1 privilégios escolhidos exclusivamente do catálogo canónico de privilégios existente.
- **FR-002**: As 4 funções fixas (admin, financeiro, moderador, socio) MUST permanecer intactas: não são editáveis, não são elimináveis e o seu comportamento de acesso não muda.
- **FR-003**: O sistema MUST permitir aplicar uma função personalizada a um utilizador nos mesmos pontos onde hoje se define a «Função no Sistema» (edição de utilizador e convite), com as funções personalizadas claramente distinguíveis das fixas no seletor.
- **FR-004**: Um sócio com função personalizada MUST ter acesso equivalente a: acesso base de sócio + os privilégios da função. Funções personalizadas NÃO concedem níveis de acesso base elevados (Financeiro/Moderador/Admin) — todo o acesso adicional vem exclusivamente dos privilégios. *(Decisão do dono Q2, 2026-07-02.)*
- **FR-005**: Quando o admin edita os privilégios de uma função personalizada já aplicada a sócios, a alteração MUST propagar automaticamente a todos os sócios que a têm (ligação viva) — o acesso efetivo de cada um reflete sempre a definição atual da função. *(Decisão do dono Q1, 2026-07-02.)*
- **FR-006**: O sistema MUST recusar a eliminação de uma função personalizada enquanto estiver atribuída a ≥1 utilizador, indicando a contagem; sem utilizadores, a eliminação MUST ser possível.
- **FR-007**: Todas as operações de criar/editar/eliminar função e de atribuir/retirar função a um utilizador MUST ficar registadas na auditoria.
- **FR-008**: A listagem de funções personalizadas MUST mostrar, por função, o número de utilizadores que a têm atribuída.
- **FR-009**: A gestão de funções personalizadas MUST ser exclusiva do admin (nem financeiro, nem moderador, nem detentores de privilégios avulsos).
- **FR-010**: O fluxo existente de predefinições por cargo estatutário MUST continuar a funcionar sem alterações de comportamento; quando aplicado a um sócio com função personalizada, substitui-a pelos defaults do cargo com aviso prévio ao admin.
- **FR-011**: Os privilégios de uma função personalizada MUST ser apresentados sempre com rótulos legíveis em PT (nunca chaves técnicas), consistente com o padrão existente.

### Key Entities

- **Função personalizada**: nome único, descrição opcional, conjunto de privilégios (do catálogo canónico), quem criou, datas de criação/edição. Distinta das 4 funções fixas e dos cargos estatutários.
- **Atribuição a utilizador**: a relação viva entre um utilizador e a função personalizada que lhe foi aplicada — o acesso do utilizador segue sempre a definição atual da função (decisão Q1).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O admin consegue definir uma função uma única vez e aplicá-la a 5 sócios em menos de 2 minutos, sem selecionar privilégios individualmente em nenhum deles.
- **SC-002**: Zero regressões de acesso para utilizadores das 4 funções fixas: todos os módulos acessíveis antes continuam acessíveis, e nenhum acesso novo aparece sem ação do admin.
- **SC-003**: 100% das operações de gestão de funções (criar/editar/eliminar/atribuir/retirar) ficam visíveis no registo de auditoria com autor, alvo e conteúdo.
- **SC-004**: Um sócio com função personalizada vê no portal exatamente os módulos concedidos — verificável comparando o menu antes e depois da atribuição.
- **SC-005**: A eliminação de uma função em uso é impossível de concretizar por engano (recusa com contagem em 100% das tentativas).

## Assumptions

- O catálogo de privilégios existente (12 privilégios) é suficiente; esta feature NÃO cria privilégios novos nem altera o significado dos existentes.
- Funções personalizadas não interferem com cargos estatutários nem com órgãos sociais — são apenas uma comodidade de gestão de acessos; mandatos e eleições ficam intocados.
- Contas técnicas ficam fora do âmbito (as funções personalizadas destinam-se a contas de membro).
- A ordenação/apresentação no seletor «Função no Sistema» agrupa fixas primeiro e personalizadas depois, com separador visual.
- Não há limite máximo imposto ao número de funções personalizadas (espera-se uso na ordem das unidades).
