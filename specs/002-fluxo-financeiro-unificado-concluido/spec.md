# Feature Specification: Fluxo Financeiro Unificado (Projetos → Caixa + Relatórios Auto-Gerados)

**Feature Branch**: `feature/fluxo-financeiro-unificado`

**Created**: 2026-06-20

**Status**: Draft

**Input**: Análise do fluxo financeiro do Portal ACCTA. Duas lacunas: (1) o que se gasta num projeto não aparece no fluxo de caixa central, obrigando a relançamento manual; (2) a prestação de contas pede ao utilizador para *subir* um relatório anual em PDF, quando o sistema já tem todos os movimentos e devia ser ele a *gerar* o relatório.

## Contexto do Problema

Hoje os domínios **Projetos** e **Finanças** são silos isolados:

- O orçamento aprovado de um projeto e as suas despesas vivem apenas em `project_expenses` / `project.spent`; **nunca entram no caixa central** (`transactions`). Para o dinheiro aparecer no fluxo de caixa, alguém tem de o relançar manualmente em Finanças, criando risco de dessincronização e dupla entrada. O único elo automático existente é o *Ato de pagamento* (co-aprovação Art. 54) → transação.
- As despesas de projeto **escapam** ao gate de co-aprovação do Art. 54: hoje uma despesa de projeto de qualquer valor é registada sem dupla assinatura.
- A prestação de contas **permite subir** um PDF de "Relatório e Contas", mas o sistema **ignora o conteúdo do PDF** — calcula sempre os números (DRE, balancete) a partir das transações. O upload confunde: parece que o utilizador tem de produzir o relatório, quando o sistema já o produz.

**Esclarecimento contabilístico fundamental**: um *orçamento* é uma **previsão/dotação**, não dinheiro movimentado. O orçamento aprovado NÃO deve cair no fluxo de caixa — fazê-lo inflaria o caixa com dinheiro que não entrou nem saiu. O que deve aparecer no caixa são as **despesas reais** do projeto quando ocorrem. O orçamento serve para comparar **Orçado vs. Realizado**.

**Âmbito desta ronda**: APENAS **projetos**. Eventos (que hoje não têm modelo de custos) e multas de sanções ficam para ronda futura.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Despesa de projeto aparece no caixa automaticamente (Priority: P1)

Enquanto responsável financeiro, quando registo uma despesa num projeto, essa despesa passa a aparecer imediatamente no fluxo de caixa central, no DRE e no balancete — sem ter de a relançar manualmente em Finanças.

**Why this priority**: É a raiz da dor relatada — a dupla entrada e o risco de o caixa não refletir o que os projetos gastaram. Entregue isolada, já elimina o relançamento manual e dá um caixa fiável.

**Independent Test**: Criar um projeto, registar uma despesa abaixo do limiar de co-aprovação, e confirmar que (a) a despesa aparece em `GET /finances/transactions` filtrável por projeto, (b) o `spent` do projeto reflete a soma, (c) o DRE/resumo/balancete do período passam a incluí-la — tudo sem qualquer ação adicional em Finanças.

**Acceptance Scenarios**:

1. **Given** um projeto aprovado e o limiar de co-aprovação a 0 (ou a despesa abaixo do limiar), **When** o financeiro regista uma despesa de 5.000 CVE com categoria "eventos", **Then** é criado um movimento de despesa no caixa associado ao projeto, o `spent` do projeto aumenta 5.000 e o resumo financeiro do período passa a contar essa despesa.
2. **Given** uma despesa de projeto já registada, **When** o financeiro a apaga, **Then** o movimento correspondente desaparece do caixa, do DRE e do balancete, e o `spent` do projeto é recalculado.
3. **Given** a lista de transações em Finanças, **When** o utilizador filtra por um projeto, **Then** vê apenas os movimentos desse projeto.
4. **Given** um projeto, **When** o utilizador vê o detalhe financeiro do projeto, **Then** vê o Orçado (budget, previsão) vs. Realizado (spent, soma das despesas reais) e o desvio.

---

### User Story 2 - Despesa de projeto acima do limiar exige co-aprovação (Priority: P1)

Enquanto associação, quando uma despesa de projeto ultrapassa o limiar estatutário, ela passa a exigir um *Ato* de co-aprovação (Art. 54), tal como qualquer outra despesa do mesmo valor — fechando o atalho que hoje permite gastar sem dupla assinatura através do módulo de projetos.

**Why this priority**: É um buraco de governança ativo. Unificar despesas ao caixa sem fechar este atalho seria incoerente e auditável negativamente. Anda de mãos dadas com a US1 (mesmo ponto de criação de despesa).

**Independent Test**: Com o limiar de co-aprovação a um valor positivo, tentar registar diretamente uma despesa de projeto acima do limiar e confirmar que é recusada com indicação de criar um Ato; depois criar e executar um Ato ligado ao projeto e confirmar que o movimento resultante fica associado tanto ao Ato como ao projeto.

**Acceptance Scenarios**:

1. **Given** o limiar de co-aprovação definido em 50.000 CVE, **When** o financeiro tenta registar diretamente uma despesa de projeto de 80.000 CVE, **Then** a operação é recusada com uma mensagem em português que explica que é necessário um Ato de co-aprovação, indicando o projeto.
2. **Given** um Ato de pagamento aprovado associado a um projeto, **When** o tesoureiro o executa, **Then** o movimento de despesa criado fica associado **ao Ato e ao projeto** e conta para o `spent` do projeto e para o caixa.
3. **Given** o limiar a 0 (sem co-aprovação obrigatória), **When** o financeiro regista uma despesa de projeto de qualquer valor, **Then** é permitida diretamente (comportamento de US1).

---

### User Story 3 - Sistema gera o Relatório e Contas anual (Priority: P2)

Enquanto direção/tesoureiro, quando preciso do relatório anual de contas, o sistema gera-o por mim em PDF a partir dos dados já registados — em vez de eu ter de produzir e subir um ficheiro.

**Why this priority**: Resolve a confusão relatada e o desperdício de trabalho. Depende dos dados que as US1/US2 tornam fiáveis (despesas de projeto agora no caixa), por isso vem depois, mas é independentemente testável sobre os dados existentes.

**Independent Test**: Para um exercício com transações, pedir o Relatório e Contas anual e confirmar que o sistema devolve um PDF completo (capa, DRE, balancete anual, orçado vs. realizado, folha de assinaturas) com números coincidentes com o resumo financeiro do ano — sem ter sido subido qualquer ficheiro.

**Acceptance Scenarios**:

1. **Given** um exercício com movimentos registados, **When** um utilizador autorizado pede o Relatório e Contas anual, **Then** o sistema devolve um PDF gerado com capa, DRE, balancete anual, orçado vs. realizado e folha de assinaturas, com totais coincidentes com o resumo financeiro do ano.
2. **Given** o ecrã de submissão do Relatório e Contas, **When** o utilizador submete o exercício, **Then** a submissão é aceite **sem exigir** o upload de um ficheiro, e o snapshot financeiro fica congelado para auditoria.
3. **Given** a submissão do relatório, **When** o utilizador opta por anexar uma versão assinada à mão, **Then** o upload é aceite e fica claramente identificado como **anexo opcional**, não como fonte dos números.

---

### User Story 4 - Relatórios gerados em destaque na prestação de contas (Priority: P3)

Enquanto utilizador do módulo financeiro, vejo numa secção em destaque os relatórios que o sistema gera (DRE, balancete, Relatório e Contas anual, fluxo de caixa) com download direto, e o upload de ficheiros aparece claramente como anexo opcional.

**Why this priority**: Polimento de UX que torna o novo modelo legível. Depende da US3 existir, mas é separável e não bloqueia o valor financeiro central.

**Independent Test**: Abrir a página de Finanças / Prestação de Contas e confirmar que existe uma secção "Relatórios gerados pelo sistema" com downloads funcionais e que o upload está numa zona rotulada como "anexos (opcional)".

**Acceptance Scenarios**:

1. **Given** a página de prestação de contas, **When** o utilizador a abre, **Then** vê uma secção destacada "Relatórios gerados pelo sistema" com download de DRE, balancete, Relatório e Contas anual e fluxo de caixa.
2. **Given** a mesma página, **When** o utilizador procura o upload de PDF, **Then** encontra-o numa zona claramente rotulada "anexos (opcional)", separada dos relatórios gerados.

---

### Edge Cases

- **Despesa com categoria omitida**: se quem regista a despesa de projeto não escolher categoria, o sistema assume `operacional` por defeito.
- **Migração com duplicados**: se uma despesa de projeto histórica já tiver sido relançada manualmente no caixa, a migração não deve contá-la duas vezes — o dry-run sinaliza candidatos a duplicado para revisão humana antes de aplicar.
- **Apagar despesa criada via Ato**: uma despesa de projeto que resultou de um Ato executado não deve poder ser apagada pela via simples de despesa de projeto (mantém o rasto de co-aprovação); a remoção segue as regras do Ato.
- **Projeto sem orçamento (budget 0)**: o "Orçado vs. Realizado" mostra realizado e desvio relativo a 0 sem erro.
- **Relatório anual de exercício sem movimentos**: o PDF é gerado na mesma, com totais a zero, sem falhar.
- **Correção de uma despesa**: não existe edição in-place de despesa de projeto (só criar/remover); uma correção faz-se removendo e voltando a registar. Como o `spent` é derivado, fica sempre coerente sem somas em duplicado.

## Requirements *(mandatory)*

### Functional Requirements

**Frente A — Projetos ligados ao caixa**

- **FR-001**: Uma despesa de projeto MUST ser persistida como um movimento de despesa no caixa central, associado ao projeto que a originou (fonte única de verdade, sem registo paralelo).
- **FR-002**: O valor "gasto" de um projeto (`spent`) MUST ser derivado da soma das despesas reais do projeto no caixa, não mantido como contador independente sujeito a divergência.
- **FR-003**: O orçamento de um projeto (`budget`) MUST permanecer uma previsão e NÃO MUST gerar qualquer movimento no caixa.
- **FR-004**: O sistema MUST oferecer uma visão "Orçado vs. Realizado" por projeto (previsão vs. soma das despesas reais, com desvio).
- **FR-005**: Ao registar uma despesa de projeto, o utilizador MUST poder indicar uma categoria de despesa de entre as categorias oficiais (`operacional`, `eventos`, `juridico`, `comunicacao`, `viagens`, `outros_despesa`); na ausência, o sistema MUST assumir `operacional`.
- **FR-006**: Uma despesa de projeto cujo montante ultrapasse o limiar de co-aprovação MUST exigir um Ato de co-aprovação (Art. 54) e MUST ser recusada se registada diretamente, com mensagem em português a orientar para a criação do Ato, identificando o projeto.
- **FR-007**: A execução de um Ato de pagamento associado a um projeto MUST produzir um movimento de despesa associado simultaneamente ao Ato e ao projeto.
- **FR-008**: As despesas de projeto, sendo movimentos do caixa, MUST aparecer automaticamente no resumo financeiro, no DRE, no balancete e na exportação de fluxo de caixa do período, sem ação adicional.
- **FR-009**: A listagem de movimentos financeiros MUST poder ser filtrada por projeto.
- **FR-010**: A remoção de uma despesa de projeto MUST remover o respetivo movimento do caixa e recalcular o realizado do projeto; despesas originadas por um Ato executado MUST seguir as regras de remoção do Ato (não removíveis pela via simples).
- **FR-011**: Toda criação, alteração e remoção de despesa de projeto MUST registar entrada de auditoria, e todos os endpoints envolvidos MUST aplicar verificação de acesso por papel.

**Migração de dados (STOP — requer confirmação explícita do dono)**

- **FR-012**: As despesas de projeto históricas MUST ser convertidas em movimentos do caixa, preservando data, descrição, autor e associação ao projeto, com categoria por defeito `operacional`.
- **FR-013**: A conversão MUST correr primeiro em modo simulação (dry-run), produzindo um relatório de reconciliação que sinaliza possíveis duplicados (despesas já relançadas manualmente no caixa); a aplicação efetiva só MUST ocorrer após confirmação explícita do dono.
- **FR-014**: Após a conversão confirmada, o registo paralelo de despesas de projeto MUST deixar de existir como fonte de dados própria.

**Frente B — Relatórios auto-gerados**

- **FR-015**: O sistema MUST gerar, a pedido, um "Relatório e Contas" anual completo em PDF a partir dos dados registados, contendo: capa identificativa, DRE do exercício, balancete anual, orçado vs. realizado e folha de assinaturas (Direção / Conselho Fiscal).
- **FR-016**: A submissão do Relatório e Contas de um exercício MUST ser possível sem upload de ficheiro, congelando o snapshot financeiro do exercício para auditoria.
- **FR-017**: O upload de um PDF na prestação de contas MUST passar a ser opcional e identificado como anexo (ex.: versão assinada à mão), nunca como fonte dos números apresentados.
- **FR-018**: A página de prestação de contas / finanças MUST apresentar em destaque os relatórios gerados pelo sistema (DRE, balancete, Relatório e Contas anual, fluxo de caixa) com download direto, e separar visualmente os anexos opcionais.
- **FR-019**: Os números de qualquer relatório gerado MUST derivar exclusivamente das transações do sistema e coincidir com o resumo financeiro do mesmo período.

### Key Entities *(include if feature involves data)*

- **Movimento financeiro (transação)**: representa uma entrada ou saída real de dinheiro do caixa. Passa a poder estar associado a um **projeto** (além da já existente associação a um Ato de co-aprovação e a um sócio). É a fonte única de verdade dos valores.
- **Projeto**: iniciativa com um **orçamento** (previsão) e um **realizado** (soma das despesas reais associadas). O realizado deixa de ser um contador próprio e passa a derivar dos movimentos do caixa.
- **Despesa de projeto**: deixa de ser uma entidade separada e passa a ser um movimento de despesa do caixa associado a um projeto.
- **Ato de co-aprovação (Art. 54)**: mecanismo de dupla assinatura para despesas acima do limiar; ao ser executado para um projeto, produz o movimento associado ao Ato e ao projeto.
- **Exercício / Relatório e Contas**: ciclo anual de prestação de contas; o relatório passa a ser gerado pelo sistema, com o upload como anexo opcional e o snapshot financeiro congelado para auditoria.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma despesa registada num projeto fica refletida no fluxo de caixa central sem qualquer relançamento manual adicional (zero passos extra em Finanças).
- **SC-002**: O total de despesas apresentado no caixa de um período passa a incluir 100% das despesas de projeto desse período (antes: 0%).
- **SC-003**: O valor "realizado" de um projeto coincide sempre com a soma dos seus movimentos de despesa no caixa (sem divergência possível entre as duas vistas).
- **SC-004**: Nenhuma despesa acima do limiar de co-aprovação pode ser registada por qualquer via (incluindo projetos) sem passar por um Ato — o atalho atual é eliminado.
- **SC-005**: A submissão do Relatório e Contas anual pode ser concluída sem o utilizador produzir ou subir qualquer ficheiro.
- **SC-006**: O Relatório e Contas anual gerado pelo sistema apresenta números idênticos ao resumo financeiro do mesmo exercício.
- **SC-007**: A migração de despesas históricas não introduz duplicados no caixa (todos os candidatos a duplicado são revistos antes da aplicação).

## Assumptions

- A DB de desenvolvimento está praticamente vazia; o volume de `project_expenses` históricas a migrar é baixo, o que torna a revisão de reconciliação tratável.
- O orçamento de projeto e o orçamento anual do exercício (`Exercicio.orcamento.linhas`) são conceitos distintos e permanecem separados; esta ronda não os funde.
- As categorias de despesa oficiais existentes (`operacional`, `eventos`, `juridico`, `comunicacao`, `viagens`, `outros_despesa`) são suficientes para classificar despesas de projeto; não se criam categorias novas.
- O gerador de PDF existente para o DRE é reutilizável como base do Relatório e Contas anual completo.
- As regras de assinatura e execução de Atos (Art. 54) mantêm-se inalteradas; esta ronda apenas passa a encaminhar despesas de projeto acima do limiar por esse fluxo já existente.
- A visibilidade/permissões do Relatório e Contas gerado seguem as regras já existentes da prestação de contas (financeiro/direção/CF para gerir; visibilidade pública/sócios conforme já definido).
- Eventos e multas de sanções ficam explicitamente fora de âmbito nesta ronda.
