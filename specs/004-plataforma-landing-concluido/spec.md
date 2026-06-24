# Feature Specification: Landing page da plataforma de gestão de associações

**Feature Branch**: `feature/landing-plataforma` (spec dir `004-plataforma-landing`)

**Created**: 2026-06-22

**Status**: Draft

**Input**: User description: "landing page sobre sistema de gestao de associacao, coloca um link discreto no roda pe"

**Clarificações do dono (2026-06-22)**:
- **Propósito**: marketing do *software* — apresentar o Portal ACCTA como um **sistema/plataforma de gestão de associações** reutilizável por outras entidades (capacidades, módulos, benefícios).
- **Localização**: **nova rota pública** no `PublicLayout` (ex. `/plataforma`), com um **link discreto no rodapé** existente a apontar para ela.
- **CTA**: **sem CTA forte** — página informativa, em registo sóbrio, coerente com a knowledge base educacional do site.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conhecer a plataforma a partir do rodapé (Priority: P1)

Um visitante do site público da ACCTA repara num link discreto no rodapé (ex. "A plataforma" / "Sistema de gestão"). Ao clicar, chega a uma página que explica, de forma factual e sóbria, o que é o sistema de gestão de associações que está por trás do portal — que problemas resolve e que módulos oferece.

**Why this priority**: é o coração da funcionalidade — sem a página e o seu ponto de entrada discreto, não há nada a entregar. É a fatia mínima que já entrega valor.

**Independent Test**: navegar para a nova rota (ex. `/plataforma`) diretamente e a partir do link do rodapé; confirmar que a página carrega, descreve a plataforma e mantém cabeçalho/rodapé do `PublicLayout`.

**Acceptance Scenarios**:

1. **Given** o site público carregado em qualquer página, **When** o visitante olha para o rodapé, **Then** vê um link discreto (não proeminente, estilo de link de rodapé existente) para a página da plataforma.
2. **Given** o visitante no rodapé, **When** clica no link da plataforma, **Then** é levado para a nova rota pública e vê a landing page da plataforma com o cabeçalho e rodapé do `PublicLayout`.
3. **Given** a landing page aberta, **When** o visitante a lê, **Then** encontra: uma secção de abertura (o que é a plataforma), uma secção de capacidades/módulos e uma secção de fecho — toda em PT-PT e em tom factual.

---

### User Story 2 - Compreender as capacidades/módulos do sistema (Priority: P2)

Um responsável de outra associação quer perceber, ao ler a página, que funcionalidades o sistema oferece (gestão de sócios, quotas, transparência financeira, eventos, votações/assembleias, comunicação) para avaliar se serve a sua organização.

**Why this priority**: é o conteúdo que dá substância à página de produto; sem isto a página é uma casca. Depende da estrutura criada na US1.

**Independent Test**: confirmar que a página apresenta um conjunto claro de capacidades/módulos com título + descrição curta cada, em cartões ou grelha consistentes com as páginas públicas existentes.

**Acceptance Scenarios**:

1. **Given** a landing page, **When** o visitante percorre a secção de capacidades, **Then** vê pelo menos os módulos centrais do portal descritos de forma sucinta (ex. sócios, quotas/finanças, transparência, eventos, votações/assembleias, comunicação).
2. **Given** cada capacidade listada, **When** o visitante a lê, **Then** a descrição é factual e não inclui números inventados, preços, nem promessas comerciais não suportadas.

---

### User Story 3 - Experiência responsiva e de marca (Priority: P3)

Qualquer visitante, em telemóvel ou desktop, vê uma página alinhada com a identidade visual da ACCTA (neutral-led, Floresta para ação positiva pontual, Carmesim como identidade, Open Sans, sem dark mode) e totalmente responsiva.

**Why this priority**: qualidade e coerência de marca; a página funciona sem isto, mas não estaria pronta para produção.

**Independent Test**: abrir a página em larguras mobile e desktop; confirmar layout responsivo, tokens de marca corretos e ausência de dark mode/inline styles.

**Acceptance Scenarios**:

1. **Given** a página em ecrã ≤ 640px, **When** é renderizada, **Then** as secções empilham e o texto permanece legível sem overflow horizontal.
2. **Given** a página em desktop, **When** é renderizada, **Then** usa larguras de contentor e ritmo de secções consistentes com as outras páginas públicas.

---

### Edge Cases

- **Sem CTA forte**: a página não deve apresentar um botão de ação primário proeminente (sem "Pedir demonstração", sem "Comprar"). Qualquer ligação (ex. discreta para o login dos sócios) é secundária e de baixo destaque visual, ou inexistente.
- **Conteúdo estático**: a página não depende de dados do backend; se algum elemento dinâmico (ex. imagem de banner gerida) falhar, a página continua a renderizar com conteúdo estático.
- **Editorial**: nenhum número não oficial, estatística inventada ou afirmação não verificável (regra da knowledge base do site público).
- **Link do rodapé em todas as páginas**: como o rodapé é partilhado pelo `PublicLayout`, o link aparece em todas as páginas públicas — deve permanecer discreto e não competir com os links existentes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST disponibilizar uma nova rota pública (ex. `/plataforma`) renderizada dentro do `PublicLayout` (cabeçalho + rodapé partilhados).
- **FR-002**: A página MUST apresentar o Portal ACCTA como um sistema/plataforma de gestão de associações reutilizável, com pelo menos: secção de abertura (o que é), secção de capacidades/módulos, secção de fecho.
- **FR-003**: A página MUST descrever as capacidades centrais do sistema (gestão de sócios, quotas/finanças, transparência, eventos, votações/assembleias, comunicação) de forma factual e sucinta.
- **FR-004**: O sistema MUST adicionar um link **discreto** no rodapé do `PublicLayout` que aponta para a nova rota.
- **FR-005**: A página MUST NOT incluir um CTA primário forte/comercial (sem "pedir demonstração", "comprar", "subscrever" proeminentes); o tom é informativo.
- **FR-006**: Todo o texto visível ao utilizador MUST estar em Português europeu (PT-PT).
- **FR-007**: A página MUST seguir o sistema de design ACCTA (neutral-led; Floresta `#166534` apenas para uma eventual ação positiva pontual; Carmesim `#C7202F` como identidade/links; Open Sans; sem dark mode; só Tailwind, sem inline styles).
- **FR-008**: A página MUST ser totalmente responsiva (mobile-first), reutilizando padrões e componentes das páginas públicas existentes (ex. `PageBanner`, secções, `card-technical`, `.animate-fade-up`).
- **FR-009**: O conteúdo MUST respeitar as regras editoriais da área pública (sem números/estatísticas não oficiais, sem promessas não suportadas).
- **FR-010**: A página MUST ser carregada de forma lazy (consistente com as restantes páginas públicas, exceto a HomePage), sem regressão de performance percetível na navegação.

### Key Entities

*(N/A — funcionalidade puramente de frontend, conteúdo estático; sem novas entidades de dados nem alterações ao backend/DB.)*

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A partir de qualquer página pública, um visitante alcança a landing da plataforma em **1 clique** no rodapé.
- **SC-002**: A landing apresenta **≥ 5 capacidades/módulos** descritos (título + descrição curta cada).
- **SC-003**: A página renderiza sem erros e sem overflow horizontal em larguras de **360px a 1440px**.
- **SC-004**: **0** botões de ação primários proeminentes de natureza comercial na página (verificação visual + revisão de código).
- **SC-005**: Lint do frontend passa sem novos avisos acima do limite (`npx eslint src/ --max-warnings=60`) e o `yarn build` conclui com sucesso.
- **SC-006**: Revisão de marca: tokens corretos (Carmesim/Grafite/Floresta), Open Sans, sem dark mode, sem inline styles — confirmado em revisão de código contra a skill `frontend-design`.

## Assumptions

- A rota escolhida é `/plataforma` (ajustável; alternativa `/sistema`). O label do link no rodapé será discreto (ex. "A plataforma").
- O link discreto será colocado no bloco de baixo do rodapé (junto ao copyright / "Política de Privacidade") ou numa coluna existente, com o estilo de link de rodapé menos proeminente — decisão final no plano/implementação.
- Não há necessidade de novas dependências npm (evitar `yarn add` — instalações novas penduram nesta máquina). Reutilizar `lucide-react`, Tailwind e componentes existentes.
- O conteúdo (copy + lista de capacidades) é redigido com base nos módulos reais do portal; sem dados dinâmicos do backend.
- SEO por-página é best-effort: o site não usa `react-helmet` hoje; um `document.title` por `useEffect` é aceitável se desejado, mas não é requisito de release.

## Out of Scope

- Qualquer formulário de contacto, captura de leads, integração de email ou fluxo de "pedir demonstração".
- Páginas de preços, planos ou comparativos.
- Alterações ao backend, à base de dados ou a modelos Pydantic.
- Multi-idioma / i18n.
- `sitemap.xml` (pode ser follow-up opcional, não bloqueia o release).
