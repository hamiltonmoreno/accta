# Spec — Atualização da Base de Conhecimento Pública (Portal ACCTA)

> **Objetivo:** alinhar todo o conteúdo informativo público do Portal ACCTA à
> base de conhecimento autoritativa em [`memory/deep-research-report.md`](../memory/deep-research-report.md),
> corrigindo erros factuais, removendo números não oficiais e adicionando o
> conteúdo regulatório/educativo hoje ausente.
>
> **Natureza deste documento:** especificação de mudança. Não implementa nada —
> define o quê, onde e como mudar, e o que precisa de decisão/dados da ACCTA.

---

## 1. Contexto e propósito do site (confirmado pelo dono)

- O site **é da própria ACCTA** (associação constituída — manter voz institucional).
- **Parte pública** = educar, divulgar e sensibilizar a população sobre o
  trabalho dos controladores de tráfego aéreo (CTA) em Cabo Verde.
  → É, na prática, uma **base de conhecimento educativa autoritativa**. É exatamente
  o que o `deep-research-report.md` foi escrito para alimentar.
- **Parte privada** = ERP de gestão da associação (fora do escopo desta spec).

Consequência: o relatório **não** deve ser usado para relativizar a existência
da ACCTA (a ressalva "associação a confirmar" do relatório era da ótica de um
pesquisador externo; o dono confirma a associação). O relatório é a **fonte de
verdade do conteúdo técnico/regulatório/educativo** da área pública.

---

## 2. Fonte de verdade e hierarquia editorial

1. `memory/deep-research-report.md` é a fonte autoritativa do conteúdo público.
2. Em divergência **regulatória**, prevalece o **CV-CAR 2.3 (2026)** e, na sua
   falta, o CV-CAR aplicável / Código Aeronáutico (como o próprio relatório
   determina). Páginas informativas antigas da AAC (ex.: validade de 5 anos /
   perda após 6 meses) **não** devem ser reproduzidas.
3. Dados marcados no relatório como **"não especificado"** (ex.: UTA/UIR,
   salários) **não são publicados** — usar formulação neutra ("não especificado;
   consultar a AIP/e-AIP vigente") em vez de inventar.
4. **Decisão do dono:** **remover todos os números sem fonte oficial** do site.
5. **Regra do projeto (CLAUDE.md):** não existe conceito de
   inadimplência/"adimplência" — quotas são descontadas na folha. Remover.
6. Texto público em **PT** (PT-PT, como o resto do site). Ao afirmar um
   requisito, citar a base legal (CV-CAR / decreto).
7. Design: respeitar o sistema **neutral-led** (skill `/frontend-design`).
   Não introduzir cores legadas. (Ver bug adjacente em §8.)

---

## 3. Arquitetura de conteúdo (recomendação habilitadora)

**Estado atual:** todo o conhecimento institucional/factual está **hardcoded em
JSX** espalhado por `frontend/src/pages/public/*` (strings inline e arrays de
objetos dentro do `return`). Não há módulo de conteúdo único; conteúdo dinâmico
(notícias, eventos, documentos, benefícios) já vem da API.

**Problema:** atualizar a base de conhecimento exige editar JSX em vários
ficheiros; fácil divergir do relatório e difícil auditar.

**Recomendação (fase 0 da implementação):** extrair a base de conhecimento para
um módulo único derivado do relatório, ex.:

```
frontend/src/content/cta/
├── index.js          # re-export
├── profissao.js      # definição CTA, tipos de controlo, responsabilidades
├── licenciamento.js  # requisitos, idade, médico, inglês, recência, conversão
├── formacao.js       # ATO aprovadas, caminhos de ingresso
├── estruturaAts.js   # 4 camadas: AAC / ASA / Cabo Verde Airports / IPIAAM
├── legislacao.js     # tabela hierárquica de diplomas
├── faq.js            # perguntas frequentes
└── contactosUteis.js # tabela de referência (AAC, ASA, ATO…)
```

As páginas públicas passam a **consumir** esse módulo. Benefício: uma alteração
no relatório → uma alteração no módulo → propaga a todas as páginas; auditável
contra o relatório num só lugar.

> Esta refatoração é **recomendada mas não obrigatória** para o conteúdo correto.
> Se for rejeitada, as mudanças das §6–§7 aplicam-se diretamente no JSX.

---

## 4. Matriz de auditoria — afirmações atuais vs. relatório

Legenda: ✅ correto · ✏️ refinar · ❌ erro factual · 🔢 número não oficial (remover) ·
➕ ausente (adicionar) · 📋 precisa de dado/decisão da ACCTA

| # | Afirmação atual no site | Local (ficheiro:linha) | Veredito | Fato autoritativo / ação |
|---|---|---|---|---|
| 1 | "validada pela **Autoridade** de Aviação Civil (AAC)" | `ProfissaoPage.js:200-202` | ❌ | AAC = **Agência** de Aviação Civil (Decreto-Lei n.º 47/2019). Corrigir nome; regulação técnica via CV-CAR. |
| 2 | "+ 60 Profissionais" | `HomePage.js:147` | 🔢 | Remover o número; manter mensagem qualitativa (ex.: "Profissionais que velam pelo céu de CV"). |
| 3 | "4 Aeroportos Internacionais" | `HomePage.js:149` | ✅ | Relatório: 4 internacionais + 3 aeródromos domésticos (7 no total). Manter; opção de enriquecer noutra secção. |
| 4 | "24/7 Operação Ininterrupta/contínua" | `HomePage.js:148`, `ProfissaoPage.js:314` | ✅ | Operação H24 consistente com estrutura ATS/FIR. Manter (qualitativo). |
| 5 | "500+ Voos/dia em média" | `ProfissaoPage.js:310` | 🔢 | Sem fonte oficial → **remover** o número; substituir por frase qualitativa. |
| 6 | "geralmente até 40-50 milhas" (APP) | `ProfissaoPage.js:152` | 🔢/✏️ | Figura não confirmada; relatório diz limites "não especificado". Reformular sem número ("uma área alargada em torno do aeroporto"). |
| 7 | "Apenas uma pequena percentagem dos candidatos consegue concluir" | `ProfissaoPage.js:211-213` | ✏️ | Sem estatística no relatório. Reformular para qualitativo ("processo seletivo e exigente"). |
| 8 | "FIR Sal" / "Flight Information Region (FIR) de Sal" | `SobrePage.js:80-87`, `ProfissaoPage.js:174,301` | ✏️ | Nome oficial: **FIR Oceânica do Sal** (criada pelo Decreto-Lei n.º 9/80, de 11 de fevereiro). Padronizar + citar base legal. |
| 9 | TWR "Sal, Praia, São Vicente, Boa Vista" | `ProfissaoPage.js:135` | ✅ | Confere (torres: Sal, Praia, Boa Vista, São Vicente). |
| 10 | Tipos de controlo TWR/APP/ACC | `ProfissaoPage.js:117-183` | ✏️/➕ | Base correta; alinhar à taxonomia do CV-CAR 2.3: ADI, APP procedural, APP vigilância, ACC procedural, ACC vigilância. Acrescentar ACC no Sal e FIS (São Filipe, Maio, São Nicolau). |
| 11 | "Proficiência mínima nível 4 ICAO" (inglês) | `ProfissaoPage.js:232` | ✅/✏️ | Correto. Refinar: "**Nível Operacional 4** (ICAO) em inglês para radiotelefonia" + base CV-CAR 2.3 (2026). |
| 12 | "Exames médicos classe 3 (ICAO) periódicos" | `ProfissaoPage.js:244` | ✅/✏️ | Correto. Refinar: **Certificado Médico Classe 3** (CV-CAR 2.4), periodicidade escalonada por idade. |
| 13 | "instituição certificada, com simuladores e estágios" | `ProfissaoPage.js:226` | ➕ | Acrescentar: ATO **aprovadas pela AAC** (ex.: SENASA, NAV Portugal) + **≥3 meses** de serviço com tráfego real sob **OJTI**. |
| 14 | Idade mínima | — (ausente) | ➕ | **Pelo menos 21 anos** (CV-CAR 2.3). Adicionar aos requisitos. |
| 15 | Validade da licença / recência | — (ausente) | ➕ | CV-CAR 2.3 (2026) **eliminou a validade da licença**; o que conta é o **averbamento de órgão** (validade ≤ 3 anos; **inválido após >90 dias** sem exercício). Adicionar secção. |
| 16 | Conversão de licença estrangeira | — (ausente) | ➕ | Fluxo da AAC (FS.PEL.09 / FS.PEL.01, taxas, proficiência). Adicionar (subsecção). |
| 17 | Estrutura ATS / quem presta o serviço | — (ausente) | ➕ | 4 camadas: **AAC** (regulador) · **ASA – Navegação Aérea de Cabo Verde** (prestador ATS) · **Cabo Verde Airports** (gestão aeroportuária concessionada desde 2023) · **IPIAAM** (investigação técnica, DL n.º 6/2023). Adicionar. |
| 18 | Legislação / regulamentos | — (ausente) | ➕ | Tabela hierárquica: Código Aeronáutico (DL-Leg. 1/2001, alt. 4/2009), DL 9/80, DL 47/2019, Lei 64/IX/2019, DL 14/2022, CV-CAR 17, CV-CAR 2.3 (2026), CV-CAR 2.4, Diretiva 01/PEL/2024, CV-CAR 22. Adicionar. |
| 19 | FAQ / Perguntas frequentes | — (ausente) | ➕ | Relatório traz FAQ pronta. Criar página/secção `/faq`. |
| 20 | "90% Taxa de Adimplência" | `TransparenciaPage.js:198` | 🔢/❌ | Remover: número não oficial **e** conceito proibido pelo projeto (sem inadimplência). |
| 21 | "60+ Sócios Ativos" | `TransparenciaPage.js:197` | 🔢 | Remover número (ou usar dado real só se vier da API/ERP). |
| 22 | "100% Assembleias Realizadas" | `TransparenciaPage.js:199` | 🔢 | Remover número; substituir por afirmação qualitativa de governança. |
| 23 | "4 Relatórios Anuais" | `TransparenciaPage.js:200` | 🔢 | Remover número fixo; a lista real já vem de `documentsAPI.getPublic()`. |
| 24 | Endereço "Aeroporto Internacional Nelson Mandela, Praia" | `ContactosPage.js:113-114,164` | 📋 | Confirmar **sede real da ACCTA** (relatório associa AAC à Achada Grande Frente/Praia e ASA a Espargos/Sal; sede da associação não consta). Não inventar. |
| 25 | E-mails `secretariado@`/`comunicacao@controlador.cv` | `ContactosPage.js:126,139` | 📋 | Confirmar e-mails reais (domínio `controlador.cv` é o do projeto). |
| 26 | Telefone "(+238) 999 99 99" | `ContactosPage.js:152-153` | 📋/❌ | **Placeholder evidente.** Substituir por número real — dado a fornecer pela ACCTA. **Não inventar.** |
| 27 | Nome por extenso "Associação dos Controladores de Tráfego Aéreo de Cabo Verde (ACCTA)" | `SobrePage.js:61` | 📋 | **Sigla resolvida: ACCTA** (decisão do dono; `ACTACV` substituído nas documentações). Resta confirmar só o **nome por extenso**: relatório usa "Associação **Cabo-verdiana** dos Controladores de Tráfego Aéreo" vs. site "…de Cabo Verde". |
| 28 | Corpos sociais "A nomear" (×4) | `SobrePage.js:207,227,234,254` | 📋 | Preencher com os corpos sociais reais (dado da ACCTA). |
| 29 | Contactos úteis de referência (AAC, ASA, ATO…) | — (ausente) | ➕ | Relatório traz tabela pronta — adicionar como recurso educativo (em Contactos ou Legislação). |

---

## 5. Itens que dependem de dados/decisões da ACCTA (bloqueiam só estes itens)

Estes **não podem ser resolvidos a partir do código nem do relatório** e não
devem ser inventados (condição de paragem — dados institucionais/contacto):

- **#26 Telefone real** (atual é placeholder `999 99 99`).
- **#24 Sede/morada real** da associação (e pin do mapa correspondente).
- **#25 E-mails** institucionais reais.
- **#27 Nome por extenso**: sigla **ACCTA** já decidida (canónica). Falta só
  decidir o extenso ("Associação **Cabo-verdiana**…" vs "…**de Cabo Verde**")
  → aplicar consistentemente em todo o site.
- **#28 Composição dos corpos sociais** (ou manter "A nomear" se ainda em
  processo — decisão do dono).
- **#21** "Sócios ativos": só publicar número se vier do ERP/API com dado real;
  caso contrário, remover.

Tudo o resto nas §6–§7 é executável só com o relatório.

---

## 6. Mudanças por página existente

### 6.1 `HomePage.js`
- **L147** remover o valor `"+ 60"`; manter o item com label qualitativo
  (ex.: `{ icon: Users, value: '', label: 'Controladores de Tráfego Aéreo' }`)
  ou substituir o card por mensagem sem número. (#2)
- **L149** manter "4 Aeroportos Internacionais" (correto). (#3)
- Restante hero/slogan/secção "O que fazemos": manter (editorial alinhado).

### 6.2 `SobrePage.js`
- **L61** aplicar o **nome legal canónico** decidido (#27).
- **L80-87** "FIR Sal" → "**FIR Oceânica do Sal**"; acrescentar nota de que foi
  criada pelo Decreto-Lei n.º 9/80 e que a prestação ATS é operada pela ASA. (#8, #17)
- **L207/227/234/254** corpos sociais: preencher dado real ou manter "A nomear"
  conforme decisão (#28).
- Manter voz institucional (associação constituída).

### 6.3 `ProfissaoPage.js`  *(página central da base de conhecimento)*
- **L200-202** corrigir "Autoridade" → "**Agência** de Aviação Civil (AAC)";
  acrescentar base legal (DL 47/2019) e que a disciplina técnica vem dos CV-CAR. (#1)
- **L152** remover "40-50 milhas"; reformular qualitativamente. (#6)
- **L211-213** reformular sem percentagem implícita. (#7)
- **L222-246 (array `Requisitos`)** acrescentar/expandir cards:
  - Idade mínima **21 anos** (#14)
  - Formação em **ATO aprovada pela AAC** + **≥3 meses sob OJTI** (#13)
  - Inglês **Nível Operacional 4 (ICAO)** — base CV-CAR 2.3 (#11)
  - **Certificado Médico Classe 3** (CV-CAR 2.4), periodicidade por idade (#12)
- **Nova secção "Licenciamento, recência e validade"** (após "Como se tornar"):
  - CV-CAR 2.3 (2026) eliminou a validade da licença; o que conta é o
    **averbamento de órgão** (≤3 anos; inválido após **>90 dias** sem exercício). (#15)
  - 5 qualificações (ADI, APP proc., APP vig., ACC proc., ACC vig.). (#10)
  - Conversão de licença estrangeira (fluxo AAC). (#16)
  - Reentrada após afastamento longo (Diretiva 01/PEL/2024). 
- **L135** manter; acrescentar **ACC (Sal)** e **FIS (São Filipe, Maio, São
  Nicolau)** à descrição das unidades. (#10)
- **L174,301** "FIR Sal" → "**FIR Oceânica do Sal**" + DL 9/80. (#8)
- **L310** remover "500+"; frase qualitativa. (#5)
- **L270** ver §8 (bug de design adjacente — fora do escopo de conteúdo).

### 6.4 `TransparenciaPage.js`
- **L196-201 (array de stats)** remover os 4 números:
  - **L198 "90% Taxa de Adimplência"** — remover totalmente (número não oficial
    + conceito proibido pelo projeto). (#20)
  - **L197/199/200** remover números; substituir o bloco por afirmações
    qualitativas de governança (compromisso de transparência, prestação de
    contas, assembleias regulares) **sem percentagens/contagens fixas**. (#21-23)
- Manter a secção dinâmica de documentos (`documentsAPI.getPublic()`) — correta.

### 6.5 `ContactosPage.js`
- **L113-114, L152-153, L126, L139, L164-165** — substituir por dados reais da
  ACCTA (§5 #24-26). Enquanto não houver telefone real, **não** exibir um número
  inventado (preferir omitir o campo telefone a publicar placeholder).
- Adicionar bloco "Contactos úteis" de referência (AAC, ASA, ATO) do relatório. (#29)

---

## 7. Conteúdo novo a criar (do relatório)

Recomendado adicionar como **novas secções/páginas públicas** (decidir rota vs.
secção na implementação; navegação sugerida no relatório, §"Estrutura de
navegação"):

1. **Estrutura ATS de Cabo Verde** — 4 camadas (AAC / ASA / Cabo Verde Airports
   / IPIAAM) + FIR Oceânica do Sal + lista de órgãos (ACC Sal; TWR Sal, Praia,
   Boa Vista, São Vicente; FIS São Filipe, Maio, São Nicolau). (#17)
2. **Licenciamento CTA** — requisitos, idade, médico, inglês, qualificações,
   averbamento/recência, conversão de licença, reentrada. (#14-16)
3. **Formação** — ATO aprovadas pela AAC (SENASA, NAV Portugal — com a ressalva
   de que validades de certificado são pontuais e devem citar a fonte/data),
   caminhos de ingresso (incl. formação patrocinada FPEF/SENASA),
   formação acadêmica complementar (UTA/ISAT — **não** é via de licença). (#13)
4. **Legislação e regulamentos** — tabela hierárquica de diplomas (#18); pode
   viver sob Transparência/Documentos.
5. **FAQ** — adaptar a FAQ pronta do relatório para PT-PT (#19).
6. **Linha do tempo "Como se tornar CTA"** — usar o fluxo do relatório
   (pré-requisitos → formação inicial → operacional → ingresso em unidade →
   manutenção).

Todo o conteúdo novo deve seguir as regras editoriais da §2 (citar base legal;
"não especificado" onde o relatório assim o marca — ex.: UTA/UIR, salários).

---

## 8. Achado adjacente (fora do escopo, registar e não tocar aqui)

`ProfissaoPage.js:269-271` usa `rgba(0,255,156,0.3)` (verde "Radar Green"
**legado**, já removido do sistema de design reconciliado) num gradiente de
fundo. É uma violação do design system neutral-led, **não** um problema de
conteúdo/conhecimento. Registado para tratamento separado (não misturar com
esta spec de conteúdo).

---

## 9. Fora de escopo

- Parte privada / ERP da associação.
- Conteúdo dinâmico já servido por API (notícias, eventos, documentos,
  benefícios, galeria) — exceto onde a spec remove números hardcoded à volta.
- Refatoração de design/UX além da correção de conteúdo (incl. §8).
- Tradução PT-BR → PT-PT de massa (o site já é PT-PT; conteúdo novo nasce PT-PT).

---

## 10. Riscos e condições de paragem

- **Não inventar** telefone, morada, e-mails, nome legal ou corpos sociais
  (§5) — são dados institucionais; parar e pedir à ACCTA.
- Validades de certificados de ATO (SENASA 31/07/2027, NAV 25/07/2027) e
  contactos de terceiros são **pontuais**: publicar sempre com "fonte/data" e
  formulação que envelhece bem ("conforme lista da AAC à data de…").
- Não reintroduzir a info antiga da AAC (licença 5 anos / 6 meses) — CV-CAR 2.3
  (2026) prevalece.
- Manter o sistema de design neutral-led; não introduzir cores legadas.

---

## 11. Critérios de aceitação / verificação

1. Nenhuma das afirmações ❌/🔢 da §4 permanece no site (grep pelos números
   `60`, `500`, `40-50`, `90%`, `100%`, `4 Relatórios`, `Autoridade de Aviação`).
2. "Adimplência/inadimplência" não aparece em nenhum ficheiro público.
3. "FIR Oceânica do Sal" usado consistentemente; "Agência de Aviação Civil"
   correto em todas as ocorrências.
4. Conteúdo novo (§7) presente e cada requisito legal cita a sua base
   (CV-CAR/decreto), conforme o relatório.
5. Itens 📋 (§5) ou estão preenchidos com dado real fornecido pela ACCTA, ou
   omitidos — nunca placeholders.
6. `cd frontend && yarn build` passa; `npx eslint src/ --ext .js,.jsx
   --max-warnings=60` sem novos erros.
7. Revisão visual das páginas públicas alteradas (light mode, neutral-led).

---

## 12. Faseamento sugerido da implementação (follow-up, após aprovação desta spec)

- **Fase 0** — (opcional, recomendado) extrair base de conhecimento para
  `frontend/src/content/cta/` derivado do relatório (§3).
- **Fase 1** — correções factuais e remoção de números (§6: #1,2,5,6,7,8,20-23).
- **Fase 2** — conteúdo novo: estrutura ATS, licenciamento, formação,
  legislação, FAQ, timeline (§7).
- **Fase 3** — itens 📋 (§5) quando a ACCTA fornecer os dados.
- **Fase 4** — verificação (§11) + build/lint + revisão visual.

---

_Fonte autoritativa: `memory/deep-research-report.md`. Conteúdo atual auditado
em `frontend/src/pages/public/*` (HomePage, SobrePage, ProfissaoPage,
TransparenciaPage, ContactosPage) — linhas verificadas em primeira mão._

---

## 13. Execução (registo)

> Implementado em 2026-05-19. Decisões do dono nesta execução: **Fase 0 SIM**
> (módulo de conteúdo) e **nome por extenso = "Associação Cabo-verdiana dos
> Controladores de Tráfego Aéreo"**.

**Fase 0 — feito.** Criado `frontend/src/content/cta/` (pure data, PT-PT,
citando base legal): `profissao.js`, `estruturaAts.js`, `licenciamento.js`,
`formacao.js`, `legislacao.js`, `faq.js`, `contactosUteis.js`, `index.js`
(+ constantes `ASSOCIACAO_NOME/_SIGLA/_NOME_COMPLETO`). Páginas consomem o módulo.

**Fase 1 — feito.**

- #1 "Autoridade"→**Agência de Aviação Civil (AAC)** + DL 47/2019 (ProfissaoPage).
- #2 HomePage: removido "+ 60"; card agora `Globe / FIR / Oceânica do Sal`.
- #5 removido "500+ Voos/dia"; #6 removido "40-50 milhas"; #7 reformulado sem
  percentagem implícita.
- #8 "FIR Sal"/"FIR de Sal"/"Flight Information Region" → **FIR Oceânica do
  Sal** + DL 9/80, consistente (SobrePage, ProfissaoPage).
- #20-23 TransparenciaPage: removidos os 4 números; bloco substituído por
  "Compromissos de Governança" (qualitativo). "Adimplência" eliminada.
- #27 nome canónico aplicado via `ASSOCIACAO_NOME*` (SobrePage + footer
  PublicLayout, site-wide).

**Fase 2 — feito.** ProfissaoPage reescrita como base de conhecimento:
definição fiel CV-CAR 2.3, responsabilidades (Anexo 11), 5 qualificações,
estrutura ATS (4 camadas + órgãos + FIR), timeline "Como se tornar",
requisitos com base legal, licenciamento/recência/reentrada/conversão.
Legislação (#18) → secção em TransparenciaPage. FAQ (#19) → acordeão nativo
em ContactosPage. Contactos úteis (#29) → ContactosPage.

**Fase 3 (bloqueados §5) — tratados sem inventar.** #26 telefone placeholder
**removido**; #24 sede fictícia (Nelson Mandela) + iframe do mapa **removidos**;
corpos sociais (#28) mantidos "A nomear". **Decisão a confirmar pelo dono:** os
e-mails `secretariado@`/`comunicacao@controlador.cv` foram **mantidos** (domínio
real do projeto, não têm padrão de placeholder) — remover se a ACCTA assim
decidir.

**Fase 4 — verificação.** `yarn build` ✅ (140s, build pronto). ESLint local
(v9.23.0, flat config) ✅ **0 erros / 44 warnings** (limite 60); nenhuma das
páginas reescritas/novas aparece nos warnings (todos pré-existentes). Greps
§11.1-11.3 limpos nas páginas públicas (restam só `100%` de CSS e a frase de
*negação* "socio inadimplente" no ERP privado, fora de escopo §9).

Achado §8 (Radar Green `rgba(0,255,156,0.3)` em ProfissaoPage) **não tocado**
por decisão da spec — bloco de estilo preservado intacto, só o conteúdo textual
à volta foi atualizado. Registado para tratamento separado.
