# Feature Specification: Ícone quadrado da marca / PWA

**Feature Branch**: `feature/icone-marca-pwa`

**Created**: 2026-06-25

**Status**: Draft

**Input**: User description: "O ícone quadrado da marca / PWA"

## Contexto

A gestão da marca pela UI já cobre os **logótipos horizontais** (fundo claro/escuro —
`spec-gestao-logo-marca`) e o **favicon do separador** (`spec-favicon-aparencia`,
em prod na v0.5.34). Falta a peça **quadrada** da marca.

Hoje, todas as superfícies quadradas do portal apontam para ficheiros estáticos do
template (CRA): o **ícone da aplicação instalada** (quando um sócio adiciona o portal
ao ecrã inicial do telemóvel — PWA), a **imagem de pré-visualização ao partilhar uma
ligação** (redes sociais / chat) e qualquer **marca compacta dentro da app**. Um gestor
que carregue o logótipo da ACCTA continua a ver um ícone genérico nestes contextos,
porque nada disto é gerível pela interface.

Esta feature dá ao gestor um **único ícone quadrado da marca**, carregável pela mesma
página de Aparência, que passa a alimentar essas superfícies — de forma
**não-destrutiva**: sem carregamento, o portal mantém exatamente o aspeto atual.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gerir o ícone quadrado da marca (Priority: P1)

Um Admin ou Moderador abre **Aparência do Site → Marca** e encontra, ao lado dos
logótipos e do favicon, um espaço para o **ícone quadrado da marca**. Carrega uma
imagem quadrada, vê a pré-visualização em vários tamanhos, e pode repor o ícone por
defeito a qualquer momento. A alteração fica registada (auditoria) e aplica-se sem
necessidade de deploy.

**Why this priority**: é a base de tudo — sem a capacidade de gerir o ícone pela UI,
nenhuma das superfícies quadradas pode refletir a marca. Entrega valor por si só (o
gestor passa a controlar a identidade visual quadrada num único sítio) e é
independentemente testável.

**Independent Test**: carregar um ícone quadrado, confirmar que persiste e aparece na
pré-visualização; repor e confirmar o regresso ao default. Verificável só nesta página.

**Acceptance Scenarios**:

1. **Given** sou Admin/Moderador na página Marca, **When** carrego um ficheiro de
   imagem quadrado para o ícone da marca, **Then** o ícone é guardado, a
   pré-visualização atualiza e a ação fica auditada.
2. **Given** existe um ícone carregado, **When** carrego "Repor", **Then** volta-se ao
   ícone por defeito e o ficheiro carregado anterior deixa de ser referenciado.
3. **Given** sou Financeiro ou Sócio, **When** tento aceder à gestão do ícone, **Then**
   o acesso é negado.
4. **Given** nenhum ícone foi carregado, **When** abro a página, **Then** vejo o ícone
   por defeito identificado como tal (sem erro nem espaço vazio).

---

### User Story 2 - App instalada e ligações partilhadas mostram a marca ACCTA (Priority: P1)

Quando um sócio **instala o portal no ecrã inicial** do telemóvel (PWA) ou quando
**alguém partilha uma ligação** do portal numa rede social ou aplicação de mensagens, o
ícone da aplicação e a imagem de pré-visualização passam a ser o **ícone quadrado da
marca** carregado pelo gestor — em vez do ícone genérico do template.

**Why this priority**: é o motivo principal da feature — a marca chegar aos contextos
externos (ecrã inicial, partilhas) onde hoje aparece um ícone errado. É o que distingue
esta feature de uma simples melhoria estética interna.

**Independent Test**: com um ícone carregado, instalar o portal como PWA num dispositivo
(ou simular a instalação) e confirmar que o ícone do atalho é o da marca; partilhar uma
ligação e confirmar que a pré-visualização usa o ícone da marca.

**Acceptance Scenarios**:

1. **Given** um ícone da marca carregado, **When** um sócio instala o portal no ecrã
   inicial, **Then** o atalho usa o ícone da marca (não o genérico).
2. **Given** um ícone da marca carregado, **When** uma ligação do portal é partilhada,
   **Then** a pré-visualização mostra o ícone/imagem da marca.
3. **Given** nenhum ícone carregado, **When** se instala ou partilha, **Then** mantém-se
   o ícone estático por defeito atual (comportamento idêntico a hoje).

> **Decisão de âmbito (Q1)**: estas superfícies externas são entregues por **serviço
> dinâmico** — o ícone carregado é servido nos URLs fixos do manifest (ícones PWA) e da
> imagem social (og), de modo a refletirem a marca **sem novo deploy**. Para a app
> instalada e o separador, a atualização é imediata após reinstalação/limpeza de cache do
> SO/navegador; para a pré-visualização de partilha, é **best-effort** (depende de o
> crawler externo voltar a indexar a ligação).

---

### User Story 3 - Marca compacta dentro da app (Priority: P3)

Em contextos internos onde um logótipo horizontal não cabe bem — **sidebar recolhida** e
**ecrãs estreitos / mobile** — o portal mostra o **ícone quadrado da marca** como mark
compacto, em vez de não mostrar marca nenhuma.

**Why this priority**: melhoria de coerência visual de baixo risco; agradável mas não
essencial. A sidebar recolhida atual não mostra qualquer marca, pelo que isto é um ganho
incremental, não a correção de um defeito visível.

**Independent Test**: recolher a sidebar e confirmar que aparece o mark da marca (ou o
default) no topo; com ícone carregado, confirmar que é o da marca.

**Acceptance Scenarios**:

1. **Given** um ícone da marca carregado, **When** recolho a sidebar, **Then** vejo o
   ícone quadrado da marca como mark compacto.
2. **Given** nenhum ícone carregado, **When** recolho a sidebar, **Then** vejo o mark
   por defeito (sem espaço vazio nem erro).

---

### Edge Cases

- **Ficheiro não-quadrado**: o gestor carrega uma imagem com proporção não-quadrada — o
  sistema deve avisar e/ou enquadrar de forma previsível (sem distorcer), recomendando
  imagem quadrada.
- **Imagem pequena / baixa resolução**: carregar uma imagem demasiado pequena para os
  tamanhos maiores (ex.: 512px) — o sistema recomenda uma resolução mínima e mostra o
  resultado escalado sem partir o layout.
- **Transparência e "safe zone"**: ícones de app em Android adaptam-se a máscaras
  (círculo/quadrado arredondado) e podem cortar as bordas — a UI deve orientar para
  conteúdo centrado com margem de segurança.
- **Cache de ícones**: navegadores e sistemas operativos mantêm o ícone instalado em
  cache agressiva — após trocar o ícone, o contexto externo pode só atualizar após
  reinstalar/limpar cache. Tem de ser comunicado ao gestor, não tratado como falha.
- **Reposição**: ao repor o default, todas as superfícies voltam ao ícone estático sem
  resíduos do ficheiro carregado anterior.
- **Relação com o favicon**: o favicon (separador) e o ícone de app são **geridos em
  separado** (campos distintos) e podem ser imagens diferentes — trocar um não afeta o
  outro.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST permitir que Admin e Moderador carreguem um **ícone quadrado
  da marca** a partir da página de Aparência, na secção Marca.
- **FR-002**: O sistema MUST negar a gestão do ícone (carregar/repor) a Financeiro e
  Sócio, e a utilizadores não autenticados.
- **FR-003**: O sistema MUST registar em **auditoria** cada alteração ao ícone da marca
  (quem, quando, valor).
- **FR-004**: O sistema MUST oferecer uma ação de **repor o ícone por defeito**, que
  remove a referência ao ficheiro carregado e regressa ao ícone estático.
- **FR-005**: O sistema MUST apresentar uma **pré-visualização** do ícone em pelo menos
  um tamanho representativo de app/atalho antes de confirmar.
- **FR-006**: O sistema MUST tratar a ausência de ícone carregado como **estado válido
  por defeito**, mantendo o aspeto atual do portal (rollout não-destrutivo).
- **FR-007**: O sistema MUST disponibilizar o ícone da marca às superfícies de consumo
  através do mesmo canal público já usado pela restante marca (sem exigir autenticação
  para leitura).
- **FR-008**: O sistema MUST aplicar o ícone da marca às **superfícies quadradas dentro
  da aplicação** (ex.: marca compacta da sidebar recolhida) em tempo real após a
  alteração, sem deploy.
- **FR-009**: O sistema MUST orientar o gestor quanto ao **formato recomendado** (imagem
  quadrada, transparente, resolução mínima e conteúdo centrado com margem de segurança).
- **FR-010**: O sistema MUST **servir o ícone carregado nos URLs fixos** usados pelo
  ícone da aplicação instalada (PWA) e pela imagem de pré-visualização de partilha (og),
  de modo a refletirem a marca **sem novo deploy** quando exista um ícone carregado;
  sem ícone, esses URLs MUST continuar a devolver o ícone estático por defeito atual.
- **FR-011**: O sistema MUST aceitar formatos de imagem rasterizada seguros e **rejeitar
  SVG** (consistente com a política de upload da marca, por risco de XSS).
- **FR-012**: O sistema MUST guardar o ícone quadrado da marca como **campo distinto do
  favicon existente** (`favicon_url` permanece separado); os dois são geridos de forma
  independente e podem ser imagens diferentes.

### Key Entities *(include if data involved)*

- **Definições da Marca (Brand Settings)**: documento único já existente que guarda as
  referências dos logótipos (claro/escuro), do favicon e do texto alternativo. Esta
  feature acrescenta uma **nova referência distinta** para o ícone quadrado da marca
  (separada de `favicon_url`). Sem valor → defaults estáticos.
- **Ficheiro de imagem do ícone**: imagem quadrada carregada pelo gestor, servida
  publicamente; substituível e reponível, com limpeza do ficheiro anterior quando deixa
  de ser referenciado.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um gestor consegue carregar e ver aplicado um novo ícone quadrado da marca
  nas superfícies internas em **menos de 2 minutos**, sem ajuda técnica e sem deploy.
- **SC-002**: Com um ícone carregado, **100%** das superfícies internas no âmbito (marca
  compacta) mostram o ícone da marca; sem ícone, **100%** mostram o default — sem espaços
  vazios nem erros.
- **SC-003**: Após instalar o portal no ecrã inicial com um ícone carregado, o atalho
  apresenta o ícone da marca em **pelo menos um dispositivo de cada plataforma principal**
  (Android e iOS), sem necessidade de novo deploy.
- **SC-004**: Ao partilhar uma ligação do portal com um ícone carregado, a
  pré-visualização apresenta o ícone/imagem da marca — best-effort, dependente de o
  serviço externo voltar a indexar a ligação.
- **SC-005**: Repor o ícone devolve **todas** as superfícies ao default e não deixa
  ficheiros órfãos referenciados.
- **SC-006**: A funcionalidade não introduz qualquer regressão visual quando nenhum ícone
  está carregado (o portal fica idêntico ao estado anterior à feature).

## Assumptions

- **Reutiliza a infraestrutura de marca existente**: a gestão integra-se na página
  Aparência → Marca e no documento único de definições da marca; o ícone é carregado pelo
  mesmo mecanismo de upload da marca (Admin+Moderador, 2 MB, SVG bloqueado).
- **Uma única imagem-mestre**: o gestor carrega **um** ícone quadrado; os vários tamanhos
  necessários derivam dessa imagem (servida/escalada conforme o contexto), sem o gestor
  ter de produzir múltiplos ficheiros. A geração de variantes maskable/multi-tamanho, se
  necessária, é detalhe de implementação a decidir no plano.
- **Superfícies internas são tempo-real; externas têm latência de cache**: as superfícies
  dentro da app aplicam-se imediatamente; o ícone de app instalada e as pré-visualizações
  de partilha dependem de cache do SO/navegador/crawler e podem exigir reinstalação ou
  reindexação — comunicado ao gestor, não é defeito.
- **Sem dark mode**: o ícone é único (não há variante para tema escuro), coerente com a
  decisão de não haver dark mode.
- **Idioma**: todo o texto de interface em Português (europeu).
- **Não-objetivos**: editor de recorte/corte de imagem; aceitação de SVG; variantes de
  ícone por idioma/tema; gestão de ícones de parceiros (categoria existente, intocada).

## Dependências

- Funcionalidades de marca já em produção: logótipos (`spec-gestao-logo-marca`) e favicon
  (`spec-favicon-aparencia`, v0.5.34). Esta feature estende o mesmo subsistema.
- Documento único de definições da marca e o respetivo canal de leitura pública.
