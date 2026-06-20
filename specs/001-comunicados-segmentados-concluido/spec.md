# Feature Specification: Comunicados Segmentados (v2)

**Feature Branch**: `001-comunicados-segmentados`

**Created**: 2026-06-20

**Status**: Draft

**Input**: Comunicados v2 — substituir o envio "para todos os sócios activos" do
módulo existente por audiência definida pelo autor (cargo / órgão / categoria /
período de filiação / status / lista nominal), com preview antes do envio e
registo auditável da audiência efectivamente atingida.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Direcção comunica internamente (Priority: P1)

Um membro da Direcção precisa de informar os restantes membros da Direcção (e
opcionalmente o Conselho Fiscal) sobre uma decisão operacional sem mandar a
mensagem para os ~200 sócios. Hoje recorre a um canal paralelo (WhatsApp ou
e-mail manual); a feature elimina essa necessidade.

**Why this priority**: cria o uso institucional mais comum (comunicação
intra-órgão) e elimina o canal paralelo que escapa a auditoria. Maior impacto
operacional imediato. Sem isto, a feature continua a ter o mesmo problema do
v1 — só muda quem dispara.

**Independent Test**: o membro da Direcção entra em "Novo comunicado", escolhe
o filtro "Órgão: Direcção", vê preview com a contagem e os primeiros nomes,
envia. Os 5+ membros da Direcção recebem in-app + e-mail; nenhum dos sócios
fora da Direcção é notificado; existe entrada em `audit_logs` com
`action=comunicado_enviado` e o filtro persistido.

**Acceptance Scenarios**:

1. **Given** o autor tem cargo na Direcção e privilégio para comunicar,
   **When** escolhe o filtro "Órgão: Direcção" e clica enviar com preview
   confirmado, **Then** todos os sócios com cargo no órgão Direcção recebem
   notificação in-app + e-mail e ninguém mais é notificado.
2. **Given** o autor não tem privilégio para comunicar, **When** tenta abrir
   o ecrã de novo comunicado, **Then** vê mensagem "sem permissão" e a
   chamada API devolve 403.
3. **Given** o autor compõe o comunicado mas sai sem enviar, **When** volta
   ao ecrã mais tarde, **Then** o rascunho está disponível e pode ser editado
   ou cancelado.

---

### User Story 2 — Convocatória de AGA para subconjunto (Priority: P2)

Em assembleias com matéria específica (eleger Conselho Fiscal, aprovar contas
do exercício, deliberar mudança de quota) só uma fracção dos sócios vota nessa
matéria. A Mesa AG precisa de convocar apenas os elegíveis.

**Why this priority**: depende do P1 estar operacional (mesma infraestrutura
de filtros) e aborda o segundo caso de uso institucional mais frequente
(convocatórias de AGA). Impacto alto mas menos diário que P1.

**Independent Test**: a Mesa AG cria comunicado com filtros combinados
(Categoria: ordinário + Status: ativo + opcionalmente Período de filiação:
admitidos até data X), o preview mostra a contagem e amostra, envia; a
audiência resolvida fica persistida no documento para reconciliação posterior
(ex: alguém que mudou de categoria depois do envio continua a aparecer no
registo como destinatário desse comunicado).

**Acceptance Scenarios**:

1. **Given** a Mesa AG escolhe um filtro composto (categoria + status +
   período), **When** clica "Calcular audiência", **Then** o preview mostra
   contagem exacta + amostra de até 5 nomes + "...mais N" se a contagem
   excede 5.
2. **Given** o filtro resolve para 0 destinatários, **When** o autor tenta
   enviar, **Then** o sistema bloqueia o envio e exibe "Filtro não selecciona
   nenhum sócio — revê os critérios".
3. **Given** o envio é bem-sucedido, **When** alguém consulta o histórico do
   comunicado, **Then** vê a definição do filtro original + a lista de
   `member_id` que foi efectivamente notificada (snapshot), mesmo que cargos
   tenham mudado entretanto.

---

### User Story 3 — Boas-vindas em massa a sócios em onboarding (Priority: P3)

Quando há vários sócios pendentes de aprovação ou admitidos recentemente, o
admin quer mandar uma única mensagem de boas-vindas com instruções, em vez
de fazê-lo individualmente.

**Why this priority**: caso de uso útil mas pouco frequente; serve sobretudo
para validar que o filtro de `status` funciona para perfis fora do uso
quotidiano (pendentes/recém-admitidos).

**Independent Test**: o admin cria comunicado com filtro "Status:
pendente_aprovacao", o preview lista os candidatos, envia. Todos recebem
notificação in-app + e-mail; os sócios `ativo` não recebem.

**Acceptance Scenarios**:

1. **Given** existem 3 sócios em `pendente_aprovacao`, **When** o admin
   filtra por esse status e envia, **Then** os 3 recebem a notificação.
2. **Given** o filtro inclui status `pendente_aprovacao`, **When** o preview
   é calculado, **Then** a contagem aparece com aviso visual (ex: ícone)
   indicando que o envio atinge contas ainda não aprovadas.

---

### User Story 4 — Conselho Fiscal dirige-se à Direcção (Priority: P3)

O Conselho Fiscal precisa, no exercício da sua função, de enviar
recomendações ou perguntas formais à Direcção sem passar pelo plenário.

**Why this priority**: caso institucionalmente importante mas pouco
frequente; valida que utilizadores fora da Direcção/Admin podem também
emitir comunicados se tiverem o privilégio (RBAC granular).

**Independent Test**: um membro do Conselho Fiscal entra no ecrã de novo
comunicado (autorizado pelo privilégio), escolhe filtro "Órgão: Direcção",
envia. Os membros da Direcção recebem; outros sócios não.

**Acceptance Scenarios**:

1. **Given** o autor tem cargo no Conselho Fiscal e privilégio para
   comunicar, **When** envia para "Órgão: Direcção", **Then** o comunicado
   chega à Direcção e o audit log identifica o autor pelo cargo (CF) + a
   audiência (Direcção).

---

### Edge Cases

- **Filtro resolve a 0 destinatários** → bloquear envio com mensagem clara
  "Filtro não selecciona nenhum sócio — revê os critérios".
- **Cargos mudam entre criação e envio** (admin promove/demote outro membro
  entre o preview e o submit) → o filtro é re-resolvido no momento do envio;
  a lista efectivamente notificada é a do envio, não a do preview, e fica
  persistida no documento.
- **Lista nominal contém `member_id` inexistente** → ignorar os inválidos,
  prosseguir com os válidos, mostrar warning no preview com a lista dos não
  encontrados.
- **`account_type=technical` selecionada via lista nominal** → excluir
  silenciosamente do envio (sócios reais apenas, conforme o sistema já filtra
  noutros listings); mostrar aviso no preview.
- **Filtros que se cruzam num conjunto vazio** (ex: categoria fundador +
  status pendente_aprovacao quando não há nenhum) → mesma resposta que "0
  destinatários".
- **`recipients_sample` muito longo para audit log** → o snapshot da lista
  resolvida (member_ids) fica no documento do comunicado; o audit log
  guarda apenas contagem + amostra (até 5 nomes); ambos são consultáveis
  separadamente.
- **Sócio adicionado ao sistema depois do envio mas que casaria o filtro**
  → NÃO é notificado retroactivamente. O envio é one-shot.
- **Resend API timeout / falha parcial** → o estado do comunicado fica
  `enviado_parcial`; o autor vê quais `member_id` falharam no e-mail (a
  notificação in-app pode ter passado mesmo assim) e pode re-tentar só esses
  numa fase seguinte (re-tentativa fora do escopo desta spec).
- **Dois autores enviam comunicados idênticos em concorrência** → cada um
  cria o seu documento independente; não há de-duplicação automática
  (responsabilidade humana).
- **Lista nominal combinada com outro filtro reduz em vez de adicionar**
  (consequência da regra AND em FR-014) → ex: filtro "Categoria: ordinário"
  + lista nominal `[ACCTA-0042, ACCTA-0099]` resolve a "ordinários que ALÉM
  DISSO estão na lista nominal", o que tipicamente dá 0 ou pouco
  destinatários. O preview MUST mostrar uma mensagem explícita ("Filtros
  combinados por AND — só sócios que cumprem todos os critérios são
  incluídos") quando a contagem após intersecção cai abaixo da contagem do
  filtro mais restritivo, para o autor reconhecer o efeito.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema MUST permitir ao autor compor o filtro de audiência
  combinando, em qualquer ordem, critérios de: cargo institucional, órgão
  social, categoria de membro, status, período de filiação (intervalo de
  datas), e lista nominal (por `member_id` ou e-mail).
- **FR-002**: Sistema MUST mostrar preview da audiência antes do submit,
  contendo (a) contagem total de destinatários reais, (b) amostra com até
  5 nomes, e (c) indicação "...mais N" se a contagem excede a amostra.
- **FR-003**: Sistema MUST excluir do preview e do envio qualquer conta com
  `account_type=technical`, mesmo que apareça resolvida por outro critério
  (a exclusão é incondicional para `technical`); a UI MUST mostrar aviso
  no preview se a lista nominal incluiu contas que ficaram excluídas por
  esta regra.
- **FR-004**: Sistema MUST persistir no documento do comunicado: (a) a
  definição original do filtro (`audience_filter`), e (b) a lista resolvida
  de `member_id` no momento do envio (`audience_resolved`), independente de
  alterações posteriores aos cargos/status.
- **FR-005**: Sistema MUST registar no log de auditoria com a acção
  `comunicado_enviado` em cada envio, incluindo `audience_filter`,
  `recipients_count`, e amostra dos primeiros nomes (`recipients_sample`) —
  nunca a lista completa no audit log (a lista completa vive no documento
  do comunicado).
- **FR-006**: Sistema MUST bloquear o submit quando a audiência resolvida
  tem 0 destinatários, devolvendo erro de validação.
- **FR-007**: Sistema MUST exibir no e-mail o critério legível em vez de
  listar e-mails ("Para: Direcção" / "Para: Conselho Fiscal e Mesa AG" /
  "Para: 12 sócios — Categoria ordinário admitidos antes de 2024").
- **FR-008**: Sistema MUST validar à entrada do endpoint que o autor tem
  privilégio para criar comunicados (a matriz concreta de privilégios é
  parte do sistema RBAC existente); ausência do privilégio devolve 403.
- **FR-009**: Sistema MUST suportar modo "dry-run" em ambientes não-produção:
  o submit calcula audiência, persiste o documento, regista audit log com
  flag `dry_run=true`, mas NÃO envia o e-mail e NÃO cria notificações
  in-app. A UI MUST indicar visualmente que o envio está em dry-run.
- **FR-010**: Sistema MUST resolver a audiência no momento do envio (não
  no momento da criação do rascunho). Cargos / categorias / status que
  mudem entre criação e envio reflectem-se no envio.
- **FR-011**: Sistema MUST permitir cancelar (eliminar) um comunicado em
  estado `rascunho`; comunicados em estado `enviado` ou `enviado_parcial`
  MUST permanecer imutáveis no histórico.
- **FR-012**: Sistema MUST mostrar atalhos de "Órgão" (Assembleia Geral /
  Direcção / Conselho Fiscal) que se expandem internamente para o conjunto
  de cargos do órgão, resolvido server-side a partir do registo canónico
  de governança (sem hard-code no frontend).
- **FR-013**: Sistema MUST permitir consultar o histórico do comunicado e
  ver: estado, autor, data, filtro original, audiência resolvida, contagem
  efectiva, e quais membros falharam no envio (se aplicável).
- **FR-014**: Sistema MUST aplicar a regra de composição da seguinte forma:
  (a) **dentro do mesmo tipo** (ex: dois cargos seleccionados, ou duas
  categorias) — **OR** (qualquer dos valores seleccionados casa);
  (b) **entre tipos diferentes** (ex: cargo + categoria + período + status
  + lista nominal) — **AND** (intersecção: só sócios que cumprem TODOS os
  tipos de critério preenchidos são incluídos). A lista nominal, sendo um
  tipo de critério, NÃO funciona como escape hatch aditivo: se o autor
  quiser adicionar pessoas específicas a uma audiência existente, MUST
  ou (i) usar SÓ a lista nominal (sem outros critérios), ou (ii) alargar
  os outros filtros para incluir essas pessoas. A UI MUST tornar isto
  evidente — ex: mostrar contagem por tipo de filtro + contagem após
  intersecção, para o autor compreender a redução.

### Key Entities

- **Comunicado**: documento com `id`, `titulo`, `corpo` (markdown / texto
  simples), `autor_id`, `created_at`, `sent_at`, `status` (rascunho /
  enviado / enviado_parcial / cancelado), `audience_filter` (definição),
  `audience_resolved` (snapshot da lista de `member_id`), `recipients_count`,
  `failed_member_ids` (se houve falhas), `dry_run` (boolean).
- **AudienceFilter**: estrutura tipada com sub-conjuntos: `cargos[]`,
  `orgaos[]`, `categorias[]`, `statuses[]`, `joined_after` / `joined_before`
  (datas ISO), `nominal_member_ids[]`, `nominal_emails[]`. Cada sub-conjunto
  é opcional; pelo menos um MUST estar preenchido. A regra de composição
  entre sub-conjuntos é definida em FR-014.
- **Destinatário** (não persistido como entidade própria — é uma vista
  derivada da `users` excluindo `account_type=technical`): qualquer sócio
  real que (no momento da resolução) casa com o `AudienceFilter`.
- **AuditLog `comunicado_enviado`**: entrada já coberta pela tabela
  `audit_logs` existente; `details` inclui `comunicado_id`, `audience_filter`,
  `recipients_count`, `recipients_sample` (≤ 5 nomes), `dry_run`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um autor consegue compor um filtro de audiência composto
  (≥2 tipos de critério), ver o preview e clicar enviar em menos de
  30 segundos.
- **SC-002**: No mês seguinte ao deploy, ≥80% dos comunicados enviados em
  produção têm um filtro definido (não o atalho "todos os sócios" — que
  passa a ser uma escolha consciente, não o default).
- **SC-003**: 100% dos comunicados enviados em produção têm registo
  auditável com `audience_filter` + `recipients_count` + amostra (verificável
  via consulta a `audit_logs` filtrada por `action=comunicado_enviado`).
- **SC-004**: 0 comunicados enviados a contas com `account_type=technical`
  em produção (verificável por log inspection após o primeiro mês).
- **SC-005**: Após 3 meses, a Direcção e o Conselho Fiscal usam o sistema
  oficial em ≥90% das suas comunicações institucionais (medido por
  inquérito qualitativo a ambos os órgãos).
- **SC-006**: Reclamações em formato "recebi um comunicado que não me
  era dirigido" caem para ≤1 por trimestre (medido pelo canal de feedback
  e tickets de suporte; pode subir temporariamente em períodos de AGA).

## Assumptions

- O módulo de comunicados existente (`comunicados-email-spec-state`, PR #113)
  está deployed em prod e funcional; esta feature ESTENDE o módulo
  existente, não reescreve. O pipeline de envio (Resend + notificações
  in-app) é reutilizado.
- A escala de envio (≤200 sócios) está dentro dos limites do plano Resend
  actual e não exige nova arquitectura de filas.
- A lista canónica de cargos / órgãos / categorias em
  `backend/governance.py` é estável e cobre todos os filtros precisados;
  alterações futuras à estrutura de cargos são tratadas como migração
  separada (o `audience_resolved` snapshot continua a apontar para
  `member_id` que são estáveis).
- A audiência é resolvida server-side; o preview é uma chamada API
  separada (ex: `POST /api/comunicados/preview-audience`) que partilha a
  mesma lógica de resolução que o envio real, garantindo paridade.
- O design system (Floresta `#166534` para "Enviar comunicado"; Carmesim
  `#C7202F` apenas para "Eliminar rascunho") é aplicado sem desvios.
- A flag de ambiente para dry-run é a `ENVIRONMENT` existente — não há
  nova variável dedicada.
- Não há requisito de versionamento da definição do filtro: o documento do
  comunicado guarda um snapshot único da definição (o que existia no
  momento do envio); edições posteriores ao filtro durante a fase
  "rascunho" sobrescrevem o snapshot até o envio acontecer.
- O comunicado em estado `enviado_parcial` (falha em alguns destinatários)
  permite re-tentativa apenas dos `failed_member_ids` numa fase seguinte;
  a implementação concreta da re-tentativa é fora de escopo desta spec.
- Quem pode emitir um comunicado é controlado por privilégio existente em
  `backend/permissions.py` (`comunicar_geral` para admins / Direcção;
  pode haver `comunicar_intra_orgao` para Conselho Fiscal); o detalhe
  fino da matriz de permissões é uma decisão a confirmar pelo dono e
  ajustar em `backend/permissions.py` durante o planeamento.
- Os filtros de tipo `cargo`, `orgao` e `categoria` aceitam selecções
  múltiplas dentro do mesmo tipo (ex: "cargo: Tesoureiro OR Secretário");
  a composição é sempre OR dentro do mesmo tipo. Entre tipos diferentes
  a composição é AND (intersecção) — ver FR-014.
- Períodos de filiação são intervalos por data (`joined_after` /
  `joined_before`); não há suporte (nesta versão) para janelas relativas
  como "admitidos no último ano" — o autor introduz datas absolutas.
