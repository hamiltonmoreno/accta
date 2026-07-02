# Feature Specification: Gestão de Sócios — Privilégios legíveis, Função completa, Predefinições por cargo e Departamento na inscrição

**Feature Branch**: `feature/016-privilegios-cargo-departamento`

**Created**: 2026-07-01

**Status**: Draft

**Input**: User description: "No privilégios, os três penúltimos [privilégios] estão transparentes, não dá para saber o que está escrito; o privilégio já deveria vir predefinido de acordo com a função ou cargo do utilizador; na inscrição dar a opção de lista suspensa de departamento (o utilizador fica perdido sem saber o que preencher); a função acho que está incompleta, só tem 3 elementos — a função deveria concordar com o cargo do sócio e estar ligada aos respetivos privilégios."

## Contexto de Domínio

O modelo de identidade da ACCTA tem três camadas, todas com fonte única em `backend/governance.py`:

- **Função de acesso (`role`)** — nível grosso de acesso: `admin`, `financeiro`, `moderador`, `socio`.
- **Cargo institucional (`cargo`)** — posição estatutária (ex.: Tesoureiro), atribuída **apenas** em «Cargos & Mandatos» (promoção/transferência) e por proclamação de eleição, que **registam mandato**.
- **Privilégios (`privileges`)** — 12 permissões granulares aditivas, avaliadas como «role OU privilégio».

Já existe no sistema um mapa **cargo → função + privilégios-padrão** (usado ao promover). O problema é sobretudo de **UX/apresentação**: esse conhecimento não está exposto onde o admin trabalha, três privilégios aparecem sem rótulo, o convite oferece uma lista de funções incompleta, e o campo «departamento» é texto livre sem orientação.

Esta funcionalidade **não** altera governança institucional (mandatos, eleições, categorias de sócio) nem o esquema de dados.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Privilégios sempre legíveis (Priority: P1)

Um administrador abre a ficha de um sócio para rever permissões e vê a grelha de privilégios. Hoje, três das doze permissões surgem como células vazias/«transparentes» — o admin não consegue saber o que está a ativar ou desativar.

**Why this priority**: é um defeito visível que compromete uma decisão de segurança (atribuição de permissões) e tem correção pequena e de alta confiança. Entregar isto sozinho já remove risco real.

**Independent Test**: abrir a ficha de edição de um sócio e confirmar que **todas** as doze permissões mostram um rótulo legível em Português, sem células em branco.

**Acceptance Scenarios**:

1. **Given** um admin na ficha de edição de um sócio, **When** a grelha de privilégios é apresentada, **Then** cada uma das 12 permissões mostra um rótulo legível em PT (nenhuma célula vazia).
2. **Given** que, no futuro, seja adicionada uma nova permissão sem tradução, **When** ela aparece na grelha, **Then** é mostrada a sua chave técnica como texto de recurso (nunca uma célula em branco).

---

### User Story 2 - Departamento como lista orientada na inscrição e gestão (Priority: P2)

Um candidato a sócio preenche o formulário público de inscrição e chega ao campo «Departamento». Hoje é um campo de texto livre sem pistas e a pessoa fica sem saber o que escrever. Deve passar a ser uma **lista suspensa** com os departamentos da associação, com uma opção «Outro» para casos não previstos. O mesmo campo, com a mesma lista, deve estar disponível ao admin (no convite e na edição). O sócio escolhe na inscrição; o admin pode corrigir depois.

**Why this priority**: é a principal dor de usabilidade relatada («o utilizador fica perdido») e melhora a qualidade dos dados de departamento de forma imediata.

**Independent Test**: na inscrição pública, abrir o campo «Departamento» e confirmar que apresenta a lista de departamentos + «Outro»; submeter escolhendo um valor da lista e confirmar que fica associado à conta.

**Acceptance Scenarios**:

1. **Given** um candidato no formulário de inscrição, **When** abre o campo «Departamento», **Then** vê uma lista suspensa com os departamentos da associação e uma opção «Outro».
2. **Given** que o candidato escolhe «Outro», **When** o formulário se apresenta, **Then** surge um campo de texto livre para especificar o departamento.
3. **Given** um admin a convidar ou a editar um sócio, **When** define o «Departamento», **Then** usa a mesma lista suspensa (+ «Outro») do formulário público.
4. **Given** um sócio existente cujo departamento guardado não pertence à lista (registo antigo/texto livre), **When** o admin abre a ficha, **Then** o valor atual é preservado e apresentado (via «Outro»), sem perda de dados.
5. **Given** um candidato que não preenche o departamento, **When** submete a inscrição, **Then** a submissão é aceite (campo opcional).

---

### User Story 3 - Função de acesso completa no convite (Priority: P2)

Um administrador convida um novo sócio e escolhe a «Função». Hoje o seletor só oferece três opções (Sócio, Financeiro, Moderador) e omite «Administrador», além de usar um rótulo diferente do resto do portal. Deve oferecer as **quatro** funções de acesso e usar o rótulo consistente «Função no Sistema».

**Why this priority**: alinha o convite com o resto da gestão de sócios (a edição já oferece as 4) e remove uma limitação que obriga o admin a um segundo passo para tornar alguém administrador.

**Independent Test**: abrir o modal de convite e confirmar que o seletor de função lista as quatro funções (Administrador, Sócio, Financeiro, Moderador) com o rótulo «Função no Sistema».

**Acceptance Scenarios**:

1. **Given** um admin no modal de convite, **When** abre o seletor de função, **Then** vê as quatro funções de acesso, incluindo «Administrador».
2. **Given** o mesmo modal, **When** olha para o rótulo do campo, **Then** lê «Função no Sistema» (consistente com a ficha de edição).

---

### User Story 4 - Aplicar as predefinições do cargo na edição (Priority: P3)

Um administrador edita um sócio que ocupa um cargo (ex.: Tesoureiro) e quer que as permissões correspondam ao cargo. Hoje tem de marcar as caixas à mão, sem saber quais correspondem ao cargo. Deve existir uma ação **«Aplicar predefinições do cargo»** que preenche, de uma vez, a função de acesso e os privilégios-padrão desse cargo, deixando o admin livre para ajustar antes de guardar. A ação **nunca** aplica nada automaticamente sem o admin a acionar.

**Why this priority**: torna visível e acionável a relação cargo → função → privilégios que já existe no sistema, reduzindo erro e esforço; é a peça mais rica e, por isso, a de menor prioridade dentro do conjunto.

**Independent Test**: editar um sócio com um cargo cujos privilégios-padrão são conhecidos, acionar «Aplicar predefinições do cargo» e confirmar que a função e os privilégios passam a corresponder ao cargo, permanecendo editáveis até guardar.

**Acceptance Scenarios**:

1. **Given** um admin a editar um sócio com um cargo definido, **When** aciona «Aplicar predefinições do cargo», **Then** a função de acesso e os privilégios são preenchidos com os valores-padrão desse cargo.
2. **Given** que o admin acionou a ação, **When** revê o formulário, **Then** pode ajustar manualmente qualquer permissão antes de guardar (a ação sugere, não tranca).
3. **Given** um admin que **não** aciona a ação, **When** edita o sócio, **Then** os privilégios existentes permanecem inalterados (nada é sobrescrito sem intenção explícita).
4. **Given** uma conta técnica de sistema (sem cargo estatutário), **When** o admin a edita, **Then** a ação «Aplicar predefinições do cargo» não é oferecida.

---

### Edge Cases

- **Cargo com predefinição vazia** (ex.: Vice-Presidente da Mesa da AG, Sócio): acionar «Aplicar predefinições do cargo» define o conjunto de privilégios como vazio de forma explícita; como nada é guardado até o admin confirmar, este pode reverter antes de guardar.
- **Nova permissão sem tradução no futuro**: a grelha mostra a chave técnica em vez de célula em branco (regra de recurso).
- **Departamento legado fora da lista**: o valor atual é preservado e apresentado através de «Outro»; guardar sem alterar não corrompe o valor.
- **Departamento vazio**: aceite em qualquer ponto (campo opcional); a lista mostra um estado inicial «Selecionar…».
- **Convite sem cargo**: um novo sócio entra sem cargo institucional (é `socio`), por isso «Aplicar predefinições do cargo» não se aplica no convite — só na edição de quem já tem cargo.
- **Inscrição pública sob proteção anti-bot**: a introdução da lista de departamentos não pode enfraquecer as proteções existentes do formulário público (limite de tentativas, verificação anti-bot, honeypot).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A grelha de privilégios na ficha de edição de sócio MUST apresentar um rótulo legível em Português para **todas** as 12 permissões, sem células vazias.
- **FR-002**: Quando uma permissão não tiver tradução definida, o sistema MUST apresentar a sua chave técnica como texto de recurso (degradação graciosa; nunca célula em branco).
- **FR-003**: Os rótulos em PT das três permissões atualmente sem tradução MUST ser: «Emitir Parecer (Conselho Fiscal)» (emit_cf_parecer), «Enviar Comunicados» (send_comunicados) e «Comunicar entre Órgãos» (comunicar_intra_orgao).
- **FR-004**: O seletor de função no convite de sócio MUST oferecer as quatro funções de acesso (Administrador, Sócio, Financeiro, Moderador) e MUST usar o rótulo «Função no Sistema», consistente com a ficha de edição.
- **FR-005**: A ficha de edição de sócio MUST oferecer uma ação «Aplicar predefinições do cargo» que preenche a função de acesso e os privilégios com os valores-padrão do cargo atual do sócio.
- **FR-006**: A ação «Aplicar predefinições do cargo» MUST ser explícita — o sistema MUST NOT alterar automaticamente função ou privilégios sem o admin a acionar, e MUST permitir ajuste manual antes de guardar.
- **FR-007**: A ação «Aplicar predefinições do cargo» MUST NOT ser oferecida para contas técnicas de sistema (sem cargo estatutário).
- **FR-008**: O campo «Departamento» MUST ser apresentado como lista suspensa a partir de uma lista canónica de departamentos da associação, na inscrição pública, no convite e na edição.
- **FR-009**: A lista de departamentos MUST conter os nove valores validados: «Formação e Certificação», «Segurança Operacional (Safety)», «Assuntos Profissionais e Laborais», «Assuntos Técnicos e Operacionais», «Relações Institucionais e Internacionais», «Comunicação e Imagem», «Assuntos Jurídicos», «Tesouraria e Finanças», «Eventos, Cultura e Ação Social».
- **FR-010**: A lista suspensa de departamento MUST incluir uma opção «Outro» que revela um campo de texto livre para especificar um departamento não listado.
- **FR-011**: O campo «Departamento» MUST permanecer opcional em todos os pontos (a inscrição/convite/edição pode ser submetida sem departamento).
- **FR-012**: A lista canónica de departamentos MUST estar disponível ao formulário público de inscrição sem exigir autenticação.
- **FR-013**: Ao editar um sócio cujo departamento guardado não pertence à lista canónica, o sistema MUST preservar e apresentar o valor atual (via «Outro»), sem o perder nem forçar troca.
- **FR-014**: O sócio MUST poder escolher o departamento na inscrição, e o admin MUST poder alterá-lo posteriormente.
- **FR-015**: O departamento MUST manter-se como etiqueta organizacional independente de função, cargo e privilégios (não participa em regras de acesso ou governança).
- **FR-016**: As alterações MUST preservar a compatibilidade com registos existentes: nenhum sócio com departamento em texto livre ou vazio pode ficar inválido ou deixar de carregar.
- **FR-017**: As proteções do formulário público de inscrição (limite de tentativas, verificação anti-bot, honeypot) MUST permanecer intactas.

### Key Entities *(include if feature involves data)*

- **Sócio (Utilizador)**: pessoa com conta no portal. Atributos relevantes: função de acesso (`role`), cargo institucional (`cargo`), privilégios (`privileges[]`), departamento (`department`), tipo de conta (member/technical).
- **Departamento**: etiqueta organizacional da associação. Conjunto canónico de nove valores + a opção «Outro» (texto livre). Independente da governança.
- **Permissão (Privilégio)**: uma das 12 permissões granulares; cada uma tem uma chave técnica estável e um rótulo de apresentação em PT.
- **Predefinição de cargo**: associação, já existente no sistema, entre um cargo e a sua função de acesso + conjunto de privilégios-padrão.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das 12 permissões apresentam um rótulo legível na ficha de edição (zero células em branco).
- **SC-002**: Um admin consegue atribuir qualquer uma das quatro funções de acesso — incluindo «Administrador» — no ato de convite, num único formulário.
- **SC-003**: Ao editar um sócio com cargo, o admin passa a conseguir aplicar a função e os privilégios corretos do cargo com **uma** ação, em vez de marcar manualmente até 12 caixas.
- **SC-004**: Na inscrição, o departamento é escolhido a partir de uma lista orientada (com saída «Outro»), eliminando o campo de texto livre sem pistas.
- **SC-005**: 100% dos sócios existentes continuam a carregar corretamente após a alteração (nenhum departamento legado ou vazio invalida um registo).
- **SC-006**: Zero regressões nos fluxos de inscrição pública — as proteções anti-abuso mantêm o mesmo comportamento.

## Fora de Âmbito

- Atribuir o **cargo institucional** no convite ou na inscrição — o cargo continua a ser atribuído exclusivamente em «Cargos & Mandatos» e por eleição (que registam mandato).
- Renomear chaves de privilégios, valores de função ou chaves de cargo (estão ligadas a dados persistidos, à API e ao frontend).
- Qualquer migração de esquema de dados ou tornar o departamento obrigatório.
- Introduzir «departamentos» como novo conceito de governança (órgãos/comissões) — o departamento é apenas uma etiqueta organizacional.

## Assumptions

- A lista dos nove departamentos foi validada com o dono e representa departamentos internos da associação (coerentes com uma associação profissional de controladores de tráfego aéreo), não locais de trabalho/aeroportos nem órgãos sociais.
- O sistema já expõe, por cargo, a função de acesso e os privilégios-padrão — a ação «Aplicar predefinições do cargo» consome esse conhecimento existente, sem novo modelo de dados.
- Um novo sócio entra sem cargo institucional (é `socio`), pelo que «predefinições do cargo» só faz sentido na edição de quem já tem cargo — não no convite/inscrição.
- O departamento continua armazenado como valor de texto livre (validação só de apresentação), garantindo compatibilidade com registos anteriores.
- As contas técnicas de sistema estão fora da lógica de predefinições de cargo (não têm cargo estatutário).
