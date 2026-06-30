# Feature Specification: Pendências v2 — contador no menu + avisos apontam ao painel

**Feature Branch**: `feature/pendencias-contador-avisos`

**Created**: 2026-06-29

**Status**: Draft

**Input**: User description: "Completar a spec 014 (painel «As minhas pendências», `/pendencias`) com (1) um contador de pendências junto ao item de menu e (2) re-apontar as ligações dos avisos de Atos PENDENTES para `/pendencias` — mantendo os avisos de Atos JÁ DECIDIDOS onde o Ato decidido é visível."

## User Scenarios & Testing *(mandatory)*

> Contexto: a **spec 014** entregou a página `/pendencias` (role-aware: o sócio comum vê
> votações por votar + eventos por confirmar; a Direção vê ainda Atos à minha assinatura +
> Atos que propus). Faltam dois remates: o sócio só sabe que tem pendências se **abrir** a
> página, e os **avisos** de Atos pendentes (specs 010/012/013) ainda levam à área de
> co-aprovações em vez do novo painel acionável.
>
> **Nuance de domínio (importante):** um Ato **já decidido** (aprovado/rejeitado) **não** é
> pendente e **não** aparece no painel. Por isso os avisos sobre Atos decididos — incluindo o
> aviso de **rejeição com motivo** (spec 011) — **não** podem apontar a `/pendencias` (levariam
> a uma página onde o Ato não está); têm de continuar a apontar para onde o Ato decidido é
> visível (co-aprovações/detalhe).

### User Story 1 - Ver quantas pendências tenho sem abrir a página (Priority: P1) 🎯 MVP

Como sócio, vejo um **contador** junto ao item de menu «As minhas pendências» que me diz
quantas coisas aguardam a minha ação. Percebo de relance que tenho (ou não) algo a tratar,
sem ter de abrir a página.

**Why this priority**: É o remate que torna o painel *descoberto* — sem o contador, o sócio
tem de abrir a página para saber se tem pendências. Entrega valor sozinho.

**Independent Test**: Com um sócio que tem N pendências (votações/eventos; +Atos se for
Direção), confirmar que o item de menu mostra o contador com N; quando resolve tudo, o
contador desaparece (ou mostra zero/sem indicador).

**Acceptance Scenarios**:

1. **Given** que tenho pendências, **When** vejo a barra lateral, **Then** o item «As minhas
   pendências» mostra um contador com o número das minhas pendências.
2. **Given** que sou da Direção, **When** vejo o contador, **Then** ele inclui também os meus
   Atos pendentes (à minha assinatura + que propus), coerente com o que o painel mostra.
3. **Given** que não tenho nada pendente, **When** vejo o item de menu, **Then** **não** há
   contador (ou mostra explicitamente zero), sem ruído.
4. **Given** que resolvo uma pendência, **When** o contador é reavaliado, **Then** reflete o
   novo total.

---

### User Story 2 - O aviso de um Ato pendente leva-me ao sítio onde ajo (Priority: P2)

Como destinatário de um aviso de **Ato pendente** (Direção avisada de um Ato a aguardar
assinatura; proponente avisado de que o seu Ato está parado — specs 010/012/013), ao clicar
no aviso aterro em **`/pendencias`**, onde vejo e ajo sobre esse Ato (e as restantes
pendências), em vez de na área genérica de co-aprovações.

**Why this priority**: Fecha o ciclo "aviso → ação" iniciado na spec 014, mas depende de o
painel já existir (014) e é incremental sobre US1.

**Independent Test**: Disparar um aviso de Ato pendente e confirmar que a ligação aponta a
`/pendencias`; disparar um aviso de Ato **decidido** (aprovação/rejeição) e confirmar que a
ligação **não** aponta a `/pendencias`.

**Acceptance Scenarios**:

1. **Given** um aviso de Ato **pendente** (novo Ato a aguardar a Direção; ou Ato atrasado),
   **When** clico no aviso, **Then** sou levado a `/pendencias`.
2. **Given** um aviso de Ato **decidido** (aprovado ou **rejeitado**, incl. o aviso de
   rejeição com motivo da spec 011), **When** clico no aviso, **Then** **não** sou levado a
   `/pendencias` — vou para onde o Ato decidido é visível (co-aprovações/detalhe).

---

### Edge Cases

- **Sócio comum vs Direção**: o contador (US1) e o destino dos avisos (US2) são role-aware —
  um sócio comum não tem pendências de Atos (não propõe/assina), por isso o contador só conta
  votações+eventos e ele não recebe avisos de Atos.
- **Voto secreto**: eleições/deliberações secretas continuam **fora** (nunca contam para o
  contador), herdado da spec 014.
- **Contador "pesado"**: o contador aparece na barra lateral, presente em todas as páginas —
  não deve degradar o carregamento das páginas (ver Assumptions).
- **Aviso antigo já entregue**: re-apontar os links altera apenas avisos **novos**; avisos já
  entregues mantêm o link com que foram criados (sem reprocessamento retroativo).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O item de menu «As minhas pendências» MUST apresentar um **contador** com o
  número de pendências do sócio autenticado.
- **FR-002**: O contador MUST refletir o **mesmo total role-aware** que o painel `/pendencias`
  mostraria (sócio comum: votações por votar + eventos por confirmar; Direção: + Atos à minha
  assinatura + Atos que propus). Não conta eleições/deliberações secretas.
- **FR-003**: O **formato** do contador MUST ser um **número exato** (ex.: "3"), com **cap
  "9+"** acima de 9 (para não alargar o item de menu).
- **FR-004**: Quando o sócio **não** tem pendências, o item de menu MUST **não** mostrar
  contador (ou mostrar explicitamente zero), sem ruído visual.
- **FR-005**: O contador MUST refletir o estado atual — ao resolver uma pendência, é
  reavaliado e o número desce. A **frescura** é **no carregamento/navegação** (recalcula ao
  navegar entre páginas, como os outros contadores da barra lateral, reutilizando a cache);
  **sem** stream/polling dedicado.
- **FR-006**: As ligações dos avisos sobre **Atos pendentes** (novo Ato a aguardar assinatura
  da Direção; avisos do varrimento de Atos atrasados — specs 010/012/013) MUST passar a apontar
  para **`/pendencias`**.
- **FR-007**: As ligações dos avisos sobre **Atos já decididos** (aprovação/**rejeição**,
  incluindo o aviso de rejeição com motivo da spec 011) MUST **NÃO** apontar para `/pendencias`
  — mantêm-se a apontar para onde o Ato decidido é visível (co-aprovações/detalhe). (Regra
  confirmada pelo dono: só os avisos de Atos **pendentes** mudam de destino; os de **decididos**
  ficam.)
- **FR-008**: O contador e o destino dos avisos MUST seguir o **design system ACCTA** (badge
  no padrão existente da barra lateral) e o texto em **PT**, sem linguagem de inadimplência.
- **FR-009**: O sistema MUST manter as garantias da spec 014 — não chamar dados de Atos para um
  sócio comum (role-aware; sem 403) e não expor pendências de voto secreto.

### Key Entities *(include if feature involves data)*

- **Contador de pendências**: número **derivado** do total de pendências do sócio (mesma
  derivação da spec 014); não é armazenado.
- **Aviso de Ato**: notificação existente sobre um Ato; tem uma **ligação**. Distingue-se
  entre avisos de Ato **pendente** (link → painel) e de Ato **decidido** (link → onde o Ato
  decidido é visível).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O sócio sabe se tem pendências (e quantas) **sem abrir** a página — a informação
  está no item de menu.
- **SC-002**: O contador coincide **exatamente** com o número de itens que o painel
  `/pendencias` lista para o mesmo utilizador (sem discrepância role-aware).
- **SC-003**: 100% dos avisos de Atos **pendentes** levam a `/pendencias`; **0%** dos avisos de
  Atos **decididos** (incl. rejeição) levam a `/pendencias`.
- **SC-004**: A introdução do contador **não** degrada percetível­mente o carregamento das
  páginas (a barra lateral continua a abrir sem atraso notável).
- **SC-005**: Mantêm-se as invariantes da spec 014 — zero pendências de voto secreto, zero 403
  para o sócio comum.

## Assumptions

- Reaproveita a derivação de pendências da spec 014 (mesmos reads; sem endpoint/coleção novos
  para o contador). O contador deriva dos **mesmos dados** do painel.
- **Perf do contador** (decisão de implementação, a fixar no plano): o contador vive na barra
  lateral (presente em todas as páginas); deve reutilizar a **cache** das leituras já feitas
  (sem multiplicar pedidos por página) e respeitar a regra role-aware (não pedir Atos ao sócio
  comum). Default de frescura = **no carregamento/navegação**, como os outros contadores.
- **Backend**: o re-apontamento dos avisos de Atos pendentes toca `backend/routes/atos.py`
  (a ligação usada por esses avisos) ⇒ a release **exige Via B**. Não é um swap cego da
  constante de link — só os avisos de **pendentes** mudam; os de **decididos** ficam.
- **Frontend**: o contador toca a barra lateral (`PrivateLayout.js`) e reutiliza o mecanismo de
  badge já existente (ex.: o badge de "Pedidos de Inscrição").
- Não há reprocessamento de avisos antigos; só os avisos **novos** usam os links atualizados.
- Validação funcional ponta-a-ponta (navegador) fica ao critério do dono (Princípio VII).
