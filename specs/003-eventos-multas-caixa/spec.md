# Feature Specification: Eventos e Multas Ligados ao Caixa (Fluxo Financeiro Unificado — Ronda 2)

**Feature Branch**: `feature/eventos-multas-caixa`

**Created**: 2026-06-21

**Status**: Draft

**Input**: Ronda 2 do modelo financeiro unificado (a ronda 1, spec 002, está em produção — v0.5.26). Ligam-se ao caixa central os dois domínios deixados de fora: **eventos** (hoje sem qualquer registo financeiro) e **multas de sanções** (têm `multa_valor` mas nunca entram no caixa).

## Contexto do Problema

A ronda 1 unificou as despesas de projeto no caixa central (despesa de projeto = movimento do caixa com vínculo ao projeto). Ficaram por ligar:

- **Eventos**: não têm qualquer dimensão financeira. O que se gasta e o que se arrecada num evento (catering, sala / inscrições, patrocínios) vive fora do sistema — não há forma de saber o resultado financeiro de um evento nem de o ver no caixa.
- **Multas**: uma sanção do tipo "multa" guarda um `multa_valor`, mas quando é aplicada esse valor **nunca entra no caixa** como receita — fica só registado no processo disciplinar.

Esta ronda aplica o **mesmo modelo unificado**: o dinheiro de cada domínio é um movimento do caixa central com um campo de vínculo (`event_id`, `sancao_id`), tal como `project_id` na ronda 1. Os números aparecem automaticamente no resumo/DRE/balancete, e a granularidade por evento/sanção vem dos vínculos (não de categorias novas).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Resultado financeiro de um evento (Priority: P1)

Enquanto gestor de eventos, registo as despesas e as receitas de um evento e vejo o seu resultado financeiro (receitas − despesas), com tudo refletido no caixa central — sem relançamentos manuais.

**Why this priority**: É o valor central da frente de eventos — hoje não existe nada. Entregue isolada, já dá visibilidade financeira por evento e alimenta o caixa.

**Independent Test**: Criar um evento, registar uma despesa e uma receita; confirmar que ambas aparecem no caixa filtráveis pelo evento, que o evento mostra `resultado_financeiro` correto, e que o resumo financeiro do período passa a incluí-las — sem ação adicional em Finanças.

**Acceptance Scenarios**:

1. **Given** um evento e o limiar de co-aprovação a 0 (ou abaixo), **When** o gestor regista uma despesa de 8.000 CVE (categoria "eventos"), **Then** é criado um movimento de despesa no caixa associado ao evento e o resumo do período passa a contar essa despesa.
2. **Given** o mesmo evento, **When** o gestor regista uma receita de 12.000 CVE (inscrições), **Then** é criado um movimento de receita associado ao evento.
3. **Given** o evento com 8.000 de despesa e 12.000 de receita, **When** o utilizador abre o detalhe do evento, **Then** vê `resultado_financeiro = {receitas: 12.000, despesas: 8.000, resultado: 4.000}`.
4. **Given** a lista de movimentos em Finanças, **When** filtra por um evento, **Then** vê apenas os movimentos desse evento.
5. **Given** uma despesa de evento já registada, **When** o gestor a apaga, **Then** o movimento desaparece do caixa e o resultado do evento é recalculado.

---

### User Story 2 - Multa aplicada entra no caixa automaticamente (Priority: P1)

Enquanto associação, quando uma sanção do tipo "multa" é aplicada, o valor da multa entra automaticamente no caixa como receita, ligado à sanção — sem qualquer lançamento manual.

**Why this priority**: Fecha a lacuna em que multas decididas não tinham reflexo financeiro. Pequena e de alto valor; independente da frente de eventos.

**Independent Test**: Levar uma sanção de multa até "aplicada" e confirmar que surge uma receita no caixa com o vínculo à sanção, com o valor da multa, e que o resumo do período aumenta nesse montante.

**Acceptance Scenarios**:

1. **Given** uma sanção do tipo "multa" com `multa_valor` 6.000 CVE no estado "decidida", **When** é aplicada, **Then** é criado **um** movimento de receita de 6.000 CVE associado à sanção, e a sanção fica "aplicada".
2. **Given** a aplicação da multa, **When** o processo de aplicação é repetido/concorre, **Then** a receita é criada **exatamente uma vez** (sem duplicação).
3. **Given** uma sanção que **não** é multa (advertência, perda de direitos), **When** é aplicada, **Then** **não** é criado qualquer movimento no caixa.
4. **Given** uma multa já aplicada que vem a ser **anulada**, **When** a anulação ocorre, **Then** é registado um movimento de estorno associado à sanção (a receita original mantém-se; corrige-se por compensação). *(Aplicável apenas se o fluxo aplicada→anulada existir; ver Assumptions.)*

---

### User Story 3 - Despesa de evento acima do limiar exige co-aprovação (Priority: P2)

Enquanto associação, uma despesa de evento que ultrapasse o limiar estatutário exige um Ato de co-aprovação (Art. 54), tal como qualquer outra despesa — sem atalhos pela via dos eventos.

**Why this priority**: Coerência de governança com projetos (ronda 1). Anda com a US1 (mesmo ponto de criação de despesa), mas é separável.

**Independent Test**: Com o limiar positivo, tentar registar diretamente uma despesa de evento acima do limiar e confirmar a recusa com indicação de criar um Ato; criar e executar um Ato ligado ao evento e confirmar que o movimento fica associado ao Ato e ao evento.

**Acceptance Scenarios**:

1. **Given** o limiar de co-aprovação em 50.000 CVE, **When** o gestor tenta registar diretamente uma despesa de evento de 70.000 CVE, **Then** a operação é recusada (mensagem PT a orientar para criar um Ato, identificando o evento).
2. **Given** um Ato de pagamento aprovado associado a um evento, **When** o tesoureiro o executa, **Then** o movimento de despesa criado fica associado **ao Ato e ao evento**.
3. **Given** uma despesa de evento originada por um Ato executado, **When** se tenta apagá-la pela via de despesas de evento, **Then** é recusada (reverter pelo fluxo do Ato).

---

### User Story 4 - Resultado do evento na interface (Priority: P3)

Enquanto gestor de eventos, no detalhe do evento registo despesas (com categoria) e receitas e vejo o resultado financeiro do evento de forma clara.

**Why this priority**: Polimento de UX que torna a frente de eventos utilizável. Depende das US1/US3.

**Independent Test**: Abrir o detalhe de um evento no browser e confirmar a secção financeira (registar despesa/receita, listas, resultado) e a mensagem amigável quando o gate Art. 54 recusa.

**Acceptance Scenarios**:

1. **Given** o detalhe de um evento, **When** o gestor o abre, **Then** vê uma secção financeira com despesas, receitas e o resultado (receitas/despesas/resultado).
2. **Given** o formulário de despesa de evento, **When** o gestor regista uma despesa, **Then** pode escolher a categoria de despesa; sem escolha, assume "eventos".
3. **Given** uma despesa acima do limiar, **When** o gestor tenta registá-la, **Then** recebe uma mensagem clara a orientar para o Ato de co-aprovação.

---

### Edge Cases

- **Despesa de evento sem categoria**: assume "eventos" por defeito.
- **Apagar despesa de evento originada por Ato**: recusada (mantém o rasto do Ato; reverter pelo Ato).
- **Apagar um evento com movimentos no caixa**: bloqueado (não se apagam registos financeiros nem se deixam órfãos); o gestor remove primeiro os movimentos (os originados por um Ato seguem as regras do Ato).
- **Aplicar multa com `multa_valor` em falta/zero**: não cria movimento (não há valor a cobrar); a aplicação da sanção segue o seu curso normal.
- **Reaplicar/concorrência na aplicação de multa**: a receita é criada exatamente uma vez (garantido pelo mecanismo de aplicação já existente).
- **Multa anulada após aplicada**: estorno por compensação, se o fluxo existir; caso não exista transição aplicada→anulada, fica fora de âmbito.
- **Correção de uma despesa/receita de evento**: não há edição in-place; corrige-se removendo e voltando a registar (o resultado é derivado, mantém-se coerente).

## Requirements *(mandatory)*

### Functional Requirements

**Cross-cutting**

- **FR-001**: Um movimento do caixa MUST poder estar associado a um **evento** e a uma **sanção** (além das associações já existentes a projeto, Ato e sócio).
- **FR-002**: A listagem de movimentos financeiros MUST poder ser filtrada por evento e por sanção.
- **FR-003**: Movimentos associados a eventos/multas MUST aparecer automaticamente no resumo financeiro, no DRE e no balancete do período, sem ação adicional.

**Frente A — Eventos**

- **FR-004**: O sistema MUST permitir registar **despesas** de um evento, que ficam como movimentos de despesa no caixa associados ao evento, com categoria de despesa (default "eventos") e auditoria.
- **FR-005**: O sistema MUST permitir registar **receitas** de um evento (ex.: inscrições, patrocínios), que ficam como movimentos de receita no caixa associados ao evento, com auditoria.
- **FR-006**: O sistema MUST apresentar o **resultado financeiro** de um evento (receitas, despesas e resultado = receitas − despesas), derivado dos movimentos do evento.
- **FR-007**: Uma despesa de evento cujo montante ultrapasse o limiar de co-aprovação MUST exigir um Ato (Art. 54) e MUST ser recusada se registada diretamente, com mensagem em português a orientar para o Ato (identificando o evento).
- **FR-008**: A execução de um Ato de pagamento associado a um evento MUST produzir um movimento de despesa associado ao Ato e ao evento.
- **FR-009**: A remoção de uma despesa/receita de evento MUST remover o respetivo movimento e recalcular o resultado; movimentos originados por um Ato executado MUST seguir as regras de remoção do Ato (não removíveis pela via simples).
- **FR-010**: Os endpoints financeiros de evento MUST exigir a mesma permissão de gestão de eventos (admin ou privilégio de gestão de eventos) e registar auditoria nas escritas.
- **FR-011**: A eliminação de um evento MUST ser bloqueada enquanto existirem movimentos no caixa associados a esse evento.

**Frente B — Multas**

- **FR-012**: Ao aplicar uma sanção do tipo "multa" com valor positivo, o sistema MUST criar **automaticamente** um movimento de receita no caixa associado à sanção, com o valor da multa.
- **FR-013**: A criação desse movimento MUST ocorrer **exatamente uma vez** por sanção (idempotente face a repetição/concorrência da aplicação).
- **FR-014**: Sanções que não sejam multa (ou multas sem valor) MUST NOT gerar qualquer movimento no caixa.
- **FR-015**: A multa MUST ser tratada como cobrada no momento da aplicação (sem conceito de dívida/inadimplência, coerente com as quotas descontadas em folha).
- **FR-016**: Se uma multa já aplicada for anulada e o fluxo de anulação existir, o sistema MUST registar um movimento de estorno associado à sanção (correção por compensação, sem apagar o movimento original).

**Categorias**

- **FR-017**: As receitas de evento e de multa MUST usar a categoria de receita existente "extraordinarias"; o sistema MUST NOT introduzir categorias de receita novas (a granularidade vem dos vínculos evento/sanção).

**Migração**

- **FR-018**: Para multas **já aplicadas** antes desta funcionalidade, MUST existir um procedimento opcional de backfill (criar o movimento de receita em falta, associado à sanção) que corre primeiro em simulação (dry-run) com reconciliação e só aplica após confirmação explícita do dono. Eventos não têm dados a migrar.

### Key Entities *(include if feature involves data)*

- **Movimento financeiro (transação)**: entrada/saída real do caixa; passa a poder estar associado a um **evento** e a uma **sanção** (além de projeto/Ato/sócio). Fonte única dos valores.
- **Evento**: ganha uma dimensão financeira derivada — despesas e receitas reais associadas e um **resultado** (receitas − despesas). Não tem orçamento previsto.
- **Despesa/Receita de evento**: movimentos do caixa associados a um evento (não entidades separadas).
- **Sanção (multa)**: ao ser aplicada, gera um movimento de receita associado; uma anulação posterior gera um estorno (se o fluxo existir).
- **Ato de co-aprovação (Art. 54)**: pode estar associado a um evento; ao ser executado produz o movimento associado ao Ato e ao evento.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma despesa ou receita registada num evento fica refletida no caixa central sem qualquer relançamento manual adicional.
- **SC-002**: O resultado financeiro de um evento coincide sempre com a soma dos seus movimentos no caixa (receitas − despesas), sem divergência entre as duas vistas.
- **SC-003**: O total do caixa de um período passa a incluir 100% das despesas/receitas de evento e das multas aplicadas desse período (antes: 0%).
- **SC-004**: Nenhuma despesa acima do limiar de co-aprovação pode ser registada por qualquer via (incluindo eventos) sem passar por um Ato.
- **SC-005**: Ao aplicar uma multa, o valor entra no caixa automaticamente e exatamente uma vez.
- **SC-006**: A migração de multas históricas não introduz duplicados no caixa (todos os candidatos a duplicado são revistos antes da aplicação).

## Assumptions

- O modelo unificado e o caixa central da ronda 1 (spec 002) estão em produção e são a base desta ronda.
- Eventos são geridos por admin ou por quem tenha o privilégio de gestão de eventos; as finanças do evento seguem o mesmo controlo de acesso.
- O ciclo de sanções termina em "aplicada" e esse é o ponto natural de cobrança da multa. A existência (ou não) de uma transição "aplicada → anulada" é confirmada na fase de planeamento; se não existir, o estorno (FR-016) fica fora de âmbito.
- As categorias de receita existentes são suficientes; receitas de evento e multas entram em "extraordinarias" (decisão de consolidação do dono, 2026-05-21).
- Eventos não terão orçamento previsto nesta ronda (apenas custos, receitas e resultado realizado).
- O limiar de co-aprovação e as regras de Atos (Art. 54) mantêm-se inalterados; esta ronda apenas encaminha despesas de evento acima do limiar por esse fluxo já existente.
- Em produção há provavelmente 0 sanções, pelo que o backfill de multas será no-op (a confirmar no dry-run).
