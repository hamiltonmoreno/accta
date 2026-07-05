# Feature Specification: Consolidação do modelo de acessos e identidade do utilizador

**Feature Branch**: `018-consolidacao-acessos`

**Created**: 2026-07-03

**Status**: Draft — **decisões D1–D7 confirmadas pelo dono (2026-07-03)**; pronta para `/speckit-plan`

**Input**: User description: "Consolidação do modelo de acessos e identidade do utilizador — eliminar a redundância entre role, privilégios, funções personalizadas, cargos e departamentos; modelo limpo com role ∈ {admin, socio}, privilégios como única fonte de acesso granular, funções personalizadas como mecanismo canónico de empacotamento, cargo estatutário apenas sugere privilégios, departamento explicitamente organizacional; UI reorganizada em «Acesso ao sistema» vs «Identidade associativa»; unificação dos checks; migração de dados em prod."

## Contexto e diagnóstico (revisão profunda de 2026-07-03)

O portal acumulou, ao longo das specs, **seis eixos** que descrevem "o que um utilizador é",
com sobreposição real confirmada no código:

| Eixo | O que faz hoje |
|---|---|
| Função no Sistema (`role`: admin/financeiro/moderador/socio) | Nível de acesso |
| Privilégios (12 granulares) | Acesso aditivo — todos os checks são «role OU privilégio» |
| Funções personalizadas (spec 017) | Pacotes nomeados de privilégios |
| Cargo estatutário (11 cargos, 3 órgãos) | Identidade estatutária + *defaults* de role+privilégios |
| Departamento (9 + «Outro») | **Nada** — rótulo puramente declarativo |
| Categoria de membro / tipo de conta | Voto/elegibilidade; visibilidade |

Problemas concretos:

1. **Os níveis «Financeiro» e «Moderador» são pacotes de 1–2 privilégios disfarçados** —
   no código, o acesso é sempre «role em (admin, financeiro) OU `manage_finances`» e
   «role em (admin, moderador) OU `moderate_content`». Existem hoje **4 caminhos** para
   conceder o mesmo acesso (nível, privilégio manual, função personalizada, predefinições
   de cargo), o que torna a gestão repetitiva e propensa a erro.
2. **A mesma semântica vive em 4 eixos** (ex.: finanças = nível Financeiro + privilégio
   + cargo Tesoureiro + departamento «Tesouraria e Finanças»), sendo que o departamento
   *parece* conceder acesso mas não concede nada.
3. **Colisão de nomes na UI**: «Função no Sistema», «Funções personalizadas» (dentro do
   mesmo seletor) e «Cargo na Associação» são quase sinónimos em português.
4. **Entropia interna**: coexistem 3 estilos de verificação de acesso e ~28 verificações
   avulsas espalhadas pelos módulos.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Um só modelo mental para conceder acessos (Priority: P1)

Como administrador, quando quero dar a um sócio a capacidade de gerir finanças (ou eventos,
documentos, moderação…), existe **um caminho canónico e apenas um**: atribuir o privilégio
correspondente — diretamente ou através de uma função personalizada (pacote). O seletor de
nível de acesso passa a ter apenas dois níveis de base (Administrador / Sócio), e tudo o
resto é feito por privilégios/funções.

**Why this priority**: é a raiz da confusão relatada pelo dono; sem isto, cada nova feature
volta a multiplicar caminhos redundantes.

**Independent Test**: com o novo modelo, dar acesso de finanças a um sócio só é possível
via privilégio/função; o resultado (módulos visíveis, ações permitidas) é idêntico ao que
o nível «Financeiro» dava antes.

**Acceptance Scenarios**:

1. **Given** um sócio sem acessos extra, **When** o admin lhe atribui o privilégio de gestão
   financeira (direto ou via função personalizada), **Then** o sócio passa a ver e operar o
   módulo financeiro exatamente como um «Financeiro» de hoje.
2. **Given** o seletor «Nível de acesso» na edição/convite, **When** o admin o abre,
   **Then** vê apenas «Administrador», «Sócio» e o grupo «Funções personalizadas» *(D1/D2)*.
3. **Given** um utilizador admin, **When** consulta qualquer módulo, **Then** mantém acesso
   total (o nível Administrador não muda).

---

### User Story 2 - Migração sem perda nem ganho de acesso (Priority: P1)

Como associação, os utilizadores que hoje têm nível «Financeiro» ou «Moderador» continuam
a conseguir fazer **exatamente o mesmo** depois da consolidação — nem mais, nem menos —
sem qualquer ação da parte deles.

**Why this priority**: é a condição de segurança da mudança; um erro aqui bloqueia a
tesouraria ou abre acessos indevidos em produção.

**Independent Test**: matriz de acesso (utilizador × módulo × ação) capturada antes e
depois da migração é idêntica para todos os utilizadores existentes.

**Acceptance Scenarios**:

1. **Given** um utilizador com nível «Financeiro» em produção, **When** a migração corre,
   **Then** fica Sócio com a função seed «Financeiro» *(D1)* e o seu acesso efetivo não
   muda; a migração fica registada na auditoria.
2. **Given** um convite pendente emitido com nível «Financeiro»/«Moderador» antes da
   migração, **When** o convidado ativa a conta depois dela, **Then** nasce já no modelo
   novo com acesso equivalente.
3. **Given** o histórico de auditoria anterior à migração, **When** é consultado,
   **Then** os registos antigos permanecem intactos (o histórico não é reescrito).

---

### User Story 3 - UI que separa «Acesso» de «Identidade» (Priority: P2)

Como administrador, ao editar um sócio vejo duas secções claramente separadas:
**«Acesso ao sistema»** (nível de base, função personalizada, privilégios — com a
**proveniência** de cada privilégio: manual, da função X, ou das predefinições do cargo Y)
e **«Identidade associativa»** (cargo estatutário, categoria de membro, departamento —
com a nota explícita de que **não concedem acessos**).

**Why this priority**: resolve a colisão de nomes e o "parece que dá acesso mas não dá";
depende do modelo consolidado (US1) para não expor dois paradigmas ao mesmo tempo.

**Independent Test**: um admin não-técnico consegue, olhando para o modal, dizer de onde
vem cada privilégio de um sócio e o que cada campo controla.

**Acceptance Scenarios**:

1. **Given** um sócio com função personalizada, **When** o admin abre a edição,
   **Then** os privilégios aparecem na secção «Acesso ao sistema» marcados como
   provenientes dessa função.
2. **Given** a secção «Identidade associativa», **When** o admin a consulta,
   **Then** vê cargo/categoria/departamento com a indicação «organizacional — não
   altera acessos» (D5).

---

### User Story 4 - Unificação interna das verificações de acesso (Priority: P3)

Como equipa de desenvolvimento, todas as verificações de acesso passam por **um único
helper** alimentado por uma **tabela canónica módulo→privilégio**, eliminando os 3 estilos
coexistentes e as verificações avulsas — sem qualquer mudança visível para o utilizador.

**Why this priority**: previne regressões futuras e torna as próximas specs mais baratas;
é invisível, por isso P3, mas é o alicerce técnico de US1/US2.

**Independent Test**: suíte de testes de equivalência (antes/depois) verde para todos os
módulos; zero verificações de acesso fora do helper canónico.

**Acceptance Scenarios**:

1. **Given** a suíte de testes existente, **When** a unificação é aplicada isoladamente
   (fase de higiene, D6), **Then** todos os testes continuam verdes e o comportamento de
   cada endpoint é idêntico.

---

### Edge Cases

- **Predefinições de cargo que apontam para níveis removidos** (Tesoureiro→Financeiro,
  Vogal→Moderador): têm de ser reescritas para privilégios (D3), incluindo o caso
  Secretário da Direcção → admin completo (rever se é intencional).
- **Convites pendentes** emitidos com role antigo no momento da migração (ver US2-2).
- **Clientes/integrações que enviam role antigo** ao PATCH/convite (D4): aceitar e
  traduzir vs rejeitar com erro claro.
- **Alerta de escalada de privilégios** (segurança §8.2.c): a noção interna de "role
  elevado" {admin, financeiro, moderador} tem de ser redefinida (admin + privilégios
  sensíveis), sem silenciar os alertas.
- **Filtros e rótulos no frontend** (lista de utilizadores filtra por role; rótulos PT):
  precisam de acompanhar o enum sobrevivente sem partir pesquisas guardadas.
- **Funções personalizadas seed** («Financeiro», «Moderador», se D1 optar por elas):
  colidem com os nomes reservados da spec 017 — a reserva tem de ser levantada de forma
  controlada para os seeds e mantida para criações manuais.
- **Utilizador simultaneamente com role antigo e privilégios manuais** já atribuídos:
  a migração tem de unir (OR) e não duplicar.
- **Rollback**: se a migração falhar a meio, o estado tem de ser recuperável (mapa de
  migração auditado por utilizador).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST reduzir os níveis de acesso de base a **Administrador e
  Sócio** *(D1)*, passando todo o acesso granular a ser expresso exclusivamente por
  privilégios — diretos ou empacotados em funções personalizadas.
- **FR-002**: A migração MUST preservar o acesso efetivo de todos os utilizadores
  existentes de forma **exatamente equivalente** (nem mais, nem menos), de forma auditada
  e com mapa de reversão por utilizador.
- **FR-003**: As funções personalizadas (spec 017) MUST tornar-se o mecanismo canónico de
  empacotamento de privilégios; os antigos níveis Financeiro/Moderador MUST ser recriados
  como **funções seed** com os privilégios equivalentes *(D1)*, e os utilizadores
  existentes migrados para elas.
- **FR-004**: As predefinições de cargo MUST passar a exprimir-se em privilégios; apenas
  Presidente e Vice-Presidente da Direcção mantêm o nível admin *(D3)*. Continuam a ser
  *sugestões* aplicadas explicitamente — nunca escritas automáticas fora de
  promoção/eleição.
- **FR-005**: O departamento MUST permanecer um atributo organizacional sem efeito em
  acessos, e a UI MUST dizê-lo explicitamente (**D5**).
- **FR-006**: A edição/convite de utilizadores MUST separar visualmente «Acesso ao
  sistema» (com proveniência de cada privilégio) de «Identidade associativa».
- **FR-007**: A API MUST aceitar e traduzir valores de nível antigos
  (financeiro/moderador) para o modelo novo durante uma release de transição, e
  rejeitá-los com mensagem clara na release seguinte *(D4)* — de forma consistente nas
  superfícies que aceitam nível (edição e convite; o registo público nunca aceita nível).
- **FR-008**: Todas as verificações de acesso MUST passar por um único ponto canónico
  alimentado por uma tabela módulo→privilégio; verificações avulsas ficam proibidas e
  guardadas por teste.
- **FR-009**: A mudança MUST ser coberta por testes de equivalência de acesso
  (antes/depois) por módulo e por perfil de utilizador, executados antes da migração real.
- **FR-010**: O histórico (auditoria, mandatos) MUST permanecer intacto — registos antigos
  que mencionem níveis removidos não são reescritos.
- **FR-011**: O alerta de segurança de escalada de acessos MUST continuar funcional no
  modelo novo (redefinido para admin + privilégios sensíveis).

### Key Entities

- **Utilizador**: nível de base (pós-D1), privilégios efetivos, referência a função
  personalizada, cargo estatutário, categoria de membro, departamento, tipo de conta.
- **Função personalizada**: pacote nomeado de privilégios (spec 017), incluindo possíveis
  funções seed de migração (D1).
- **Cargo estatutário**: identidade de governança com predefinições de acesso *sugeridas*.
- **Tabela canónica módulo→privilégio**: fonte única que define que privilégio governa
  cada módulo/ação (nova entidade conceptual, base de FR-008).
- **Mapa de migração**: registo auditável utilizador→(estado antes, estado depois).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos utilizadores existentes mantêm acesso efetivo idêntico após a
  migração (matriz utilizador×módulo×ação antes = depois; zero pedidos de suporte por
  perda de acesso).
- **SC-002**: Existe exatamente **1 caminho canónico** para conceder cada acesso granular
  (privilégio direto ou função personalizada) — contra os 4 atuais.
- **SC-003**: Zero verificações de acesso fora do ponto canónico no fim da consolidação
  (hoje: 3 estilos + ~28 verificações avulsas).
- **SC-004**: Um administrador consegue identificar a origem de cada privilégio de um
  sócio apenas olhando para o modal de edição (teste de usabilidade com o dono).
- **SC-005**: A suíte de testes completa continua verde e os testes de equivalência
  cobrem todos os módulos com verificação de acesso.

## Assumptions

- O nível «Administrador» mantém-se intocado (acesso total, bypass de privilégios).
- A mecânica da spec 017 (funções personalizadas, ligação viva, destaque) é o alicerce
  desta consolidação e não é redesenhada — é promovida a mecanismo canónico.
- Cargos, mandatos, eleições e órgãos (spec-governanca) não mudam de semântica; só as
  suas *predefinições de acesso* são reexpressas.
- Categoria de membro e tipo de conta estão fora do âmbito (já são claros).
- A migração corre uma única vez em produção, dentro de uma janela de manutenção curta,
  com backup prévio (procedimento padrão Via B).

## Decisões do dono (confirmadas 2026-07-03 — «aceito todas as recomendações D1 a D7»)

- **D1 — Níveis sobreviventes e migração** ✅ DECIDIDO: o enum de níveis de base passa a
  **{Administrador, Sócio}**. Os utilizadores com nível financeiro/moderador em produção
  migram para **funções personalizadas seed «Financeiro» e «Moderador»** (visíveis,
  editáveis e reutilizáveis pelo admin), com os privilégios equivalentes — o mecanismo da
  spec 017 torna-se o caminho único de empacotamento.

- **D2 — Seletor** ✅ DECIDIDO: o seletor é **renomeado para «Nível de acesso»** e mostra
  apenas Administrador, Sócio e o grupo «Funções personalizadas» — elimina a colisão
  função/cargo.

- **D3 — Predefinições de cargo** ✅ DECIDIDO: **Presidente e Vice-Presidente da Direcção
  mantêm nível admin**; **Secretário da Direcção desce para privilégios granulares**
  (lista exata a rever com o dono no plano); Tesoureiro e Vogais passam a privilégios
  (consequência de D1).

- **D4 — Compatibilidade da API** ✅ DECIDIDO: pedidos com nível antigo
  (financeiro/moderador) são **aceites e traduzidos** automaticamente para o equivalente
  novo durante **uma release de transição**; na release seguinte passam a ser
  **rejeitados com erro claro**.

- **D5 — Departamento** ✅ DECIDIDO: **declarativo para sempre** — nunca concede acessos e
  a UI di-lo explicitamente. Se um dia servir para segmentar comunicados, isso é
  audiência, não acesso.

- **D6 — Faseamento** ✅ DECIDIDO: **duas fases**. Fase 1 = higiene invisível (helper
  único + tabela canónica módulo→privilégio + testes de equivalência, sem mudança de
  modelo nem de UI). Fase 2 = consolidação do modelo + migração + UI. A Fase 1 é gate da
  Fase 2.

- **D7 — Release da spec 017** ✅ DECIDIDO: a release **v0.5.54 fica suspensa** até a
  consolidação estar decidida/entregue; o T018 da 017 valida-se no ambiente local
  isolado. A 017 permanece merged em develop, não released.
