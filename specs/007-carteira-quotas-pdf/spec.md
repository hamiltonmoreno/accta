# Feature Specification: Exportar carteira de quotas em PDF

**Feature Branch**: `007-carteira-quotas-pdf`

**Created**: 2026-06-26

**Status**: Draft

**Input**: User description: "Permitir aos sócios exportar a sua carteira de quotas em PDF. O sócio acede à sua carteira/área financeira no portal e descarrega um documento PDF com o seu histórico de quotas (e jóia, se aplicável): pagamentos efetuados, valores, datas/períodos e totais. O PDF serve como comprovativo pessoal (uso interno do sócio), com a identidade visual da ACCTA. O sócio só pode exportar a SUA própria carteira."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Descarregar a minha carteira de quotas em PDF (Priority: P1)

Um sócio abre a sua Carteira (área financeira pessoal) no portal e quer guardar um
comprovativo do seu histórico de quotas. Clica em "Exportar PDF" e o navegador
descarrega um documento PDF, com a identidade visual da ACCTA, que lista os seus
pagamentos de quota (e jóia, se houver) — valores, datas e o total pago.

**Why this priority**: É o coração da feature — sem o download do PDF não há
funcionalidade. Entrega valor por si só (MVP).

**Independent Test**: Autenticado como sócio com lançamentos de quota, abrir a
Carteira, acionar "Exportar PDF" e confirmar que é descarregado um PDF legível,
com marca ACCTA, contendo os seus lançamentos e o total.

**Acceptance Scenarios**:

1. **Given** um sócio autenticado com lançamentos de quota/jóia, **When** aciona
   "Exportar PDF" na sua Carteira, **Then** é descarregado um ficheiro PDF cujo
   conteúdo lista cada pagamento (data, descrição/período, categoria quota ou jóia,
   valor) e o total pago.
2. **Given** o PDF gerado, **When** é aberto, **Then** apresenta a identidade visual
   da ACCTA (marca/cabeçalho) e identifica o sócio (nome e n.º de sócio).
3. **Given** o documento é um comprovativo de uso interno, **When** é aberto,
   **Then** inclui a data de emissão e uma nota de que é um comprovativo pessoal
   (sem valor fiscal).

---

### User Story 2 - Só a minha própria carteira (Priority: P1)

Um sócio só pode exportar a SUA carteira; ninguém consegue obter, via esta
funcionalidade, o PDF da carteira de outro sócio.

**Why this priority**: Privacidade de dados financeiros pessoais. É um requisito de
segurança inseparável da P1 — exportar dados financeiros sem este limite seria uma
fuga. Por isso também P1.

**Independent Test**: Autenticado como sócio A, confirmar que a exportação devolve
apenas os lançamentos de A; qualquer tentativa de exportar a carteira de outro
sócio (B) é recusada.

**Acceptance Scenarios**:

1. **Given** o sócio A autenticado, **When** exporta a carteira, **Then** o PDF
   contém exclusivamente os lançamentos de A.
2. **Given** uma tentativa de exportar a carteira de outro sócio, **When** é feita,
   **Then** o sistema recusa (não devolve dados de terceiros).
3. **Given** um pedido não autenticado, **When** tenta a exportação, **Then** é
   recusado.

---

### User Story 3 - Carteira vazia (Priority: P3)

Um sócio sem lançamentos de quota (ex.: admitido há pouco) aciona a exportação.
O sistema produz um PDF coerente em vez de um erro.

**Why this priority**: Robustez de um caso de fronteira comum; não bloqueia o fluxo
principal.

**Independent Test**: Como sócio sem lançamentos, exportar e confirmar um PDF válido
com indicação de que ainda não há lançamentos e total = 0.

**Acceptance Scenarios**:

1. **Given** um sócio sem lançamentos de quota/jóia, **When** exporta, **Then** o PDF
   é gerado, indica "sem lançamentos" e total 0, sem erro.

---

### Edge Cases

- **Sócio sem lançamentos**: PDF válido com total 0 e mensagem (US3).
- **Muitos lançamentos** (vários anos): o PDF pagina e mantém legibilidade; o total
  reflete todos os lançamentos.
- **Lançamento com dados em falta/legados** (ex.: valor ausente): tolerado sem
  rebentar a geração (valor tratado como 0, coerente com a vista da carteira).
- **Jóia presente/ausente**: a jóia aparece quando existe; não é inventada quando não há.
- **Conta técnica** (não-sócio, ex.: `admin@controlador.cv`): sem lançamentos de
  quota → comporta-se como carteira vazia.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST permitir que um sócio autenticado descarregue, a partir
  da sua Carteira, um documento PDF com o seu histórico de quotas e jóia.
- **FR-002**: O PDF MUST listar, por lançamento, a data, o período/descrição, a
  categoria (quota ou jóia) e o valor, e MUST apresentar o total pago.
- **FR-003**: O PDF MUST apresentar a identidade visual da ACCTA e identificar o
  sócio (nome e n.º de sócio) e a data de emissão.
- **FR-004**: O PDF MUST incluir uma nota de que é um comprovativo pessoal de uso
  interno, sem valor fiscal.
- **FR-005**: A exportação MUST devolver exclusivamente os lançamentos do próprio
  sócio autenticado; MUST NÃO permitir exportar a carteira de outro sócio.
- **FR-006**: Um pedido não autenticado MUST ser recusado.
- **FR-007**: Para um sócio sem lançamentos, o sistema MUST gerar um PDF válido que
  indica a ausência de lançamentos e total 0 (sem erro).
- **FR-008**: O documento MUST refletir os mesmos valores e totais que o sócio vê na
  Carteira no portal (consistência entre a vista e o PDF).

### Key Entities *(include if feature involves data)*

- **Lançamento de quota/jóia**: um pagamento efetivo do sócio — data, período/
  descrição, categoria (`quota` ou `jóia`), valor. Todos os lançamentos listados são
  **efetivos** (não há estado pendente/pago — as quotas são descontadas em folha).
- **Carteira do sócio**: o conjunto dos lançamentos de quota/jóia do próprio sócio,
  com o total pago. É a fonte única do conteúdo do PDF.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um sócio consegue descarregar a sua carteira em PDF em menos de 10
  segundos a partir da Carteira, sem ajuda.
- **SC-002**: 100% dos PDFs gerados abrem corretamente e mostram marca ACCTA,
  identificação do sócio, lançamentos e total.
- **SC-003**: O total e os lançamentos do PDF coincidem a 100% com os apresentados na
  Carteira no portal.
- **SC-004**: 0% de exportações devolvem dados de outro sócio; pedidos não
  autenticados são sempre recusados.
- **SC-005**: A exportação com a carteira vazia produz um PDF válido em 100% dos
  casos (zero erros).

## Assumptions

- **Sem estado por quota**: o domínio não tem estado pendente/pago — todos os
  lançamentos da carteira são pagamentos efetivos (quotas descontadas em folha;
  alinhado com a convenção "sem `inadimplente`"). Por isso o PDF reflete pagamentos
  efetivos e datas, **não** um campo de "estado" por quota. *(Corrige o "estado de
  cada quota" do pedido original, que não existe no domínio.)*
- **Âmbito = toda a carteira** (todos os lançamentos do sócio até à data de emissão),
  ordenados por data; com subtotais por ano quando ajudar a leitura. Sem seletor de
  período no MVP.
- **Fonte de dados**: a mesma vista que alimenta a Carteira do sócio (lançamentos do
  próprio: quotas + jóia), garantindo consistência (FR-008).
- **Comprovativo de uso interno**: não é um recibo fiscal/oficial; inclui nota a
  declará-lo. Sem assinatura digital nem código de verificação no MVP.
- **Idioma e marca**: PDF em PT, com a identidade visual ACCTA (marca, Carmesim/
  Grafite), coerente com os PDF já existentes no portal.
- **Privacidade**: o documento contém dados pessoais/financeiros do próprio sócio;
  não é partilhado nem guardado pelo sistema — é descarregado pelo sócio a pedido.
