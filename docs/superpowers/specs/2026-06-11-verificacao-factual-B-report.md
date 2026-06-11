# Verificação factual do conteúdo público (sub-projeto B) — Relatório (Fase 1)

**Data:** 2026-06-11 · **Âmbito:** `frontend/src/content/cta/*` (o que o site público mostra)
**Método:** investigação web contra fontes oficiais/credíveis (ICAO, AAC `aac.cv`, ASA `asa.cv`,
VINCI Airports, IPIAAM, imprensa setorial). **Esta é a Fase 1** — só constata; as correções
(Fase 2) só são aplicadas após a tua aprovação.

## Legenda de veredictos
- ✅ **Confirmado** — bate com fonte oficial/credível.
- 🔧 **Corrigir/precisar** — impreciso ou incompleto; ação recomendada.
- ❓ **Não verificável online** — exige documento primário da AAC; manter com a cautela
  editorial já existente e **hiperligar à fonte** (alimenta o sub-projeto C).

---

## Achados que exigem CORREÇÃO (🔧) — prioridade

### B1. Nome oficial da ASA — **ERRO de identidade institucional**
- **Site diz** (`estruturaAts.js`, `contactosUteis.js`): "ASA — Navegação Aérea de Cabo Verde, S.A."
- **Realidade:** o nome oficial é **"ASA — Aeroportos e Segurança Aérea, S.A."** (sede no Sal;
  a navegação aérea é assegurada pela sua Direção de Navegação Aérea / Centro de Controlo
  Oceânico). "Navegação Aérea de Cabo Verde" **não** é a designação social.
- **Ação:** corrigir para "ASA — Aeroportos e Segurança Aérea, S.A." (confirmar a grafia exata
  em `asa.cv`). Manter a descrição do papel (prestador ATS). **Alta prioridade.**
- Fontes: pt.wikipedia.org/wiki/ASA · asa.cv · canso.org/member/asa

### B2. Concessão aeroportuária — incompleto
- **Site diz** (`estruturaAts.js`/`legislacao.js`): "Cabo Verde Airports, S.A. … concessionária
  … desde julho de 2023".
- **Realidade:** a concessão (7 aeroportos, **40 anos**, arranque **julho 2023**) é operada pela
  **VINCI Airports (70%) + ANA — Aeroportos de Portugal (30%)**, através da sociedade
  *Cabo Verde Airports, S.A.* A data e a entidade-veículo estão certas; falta o operador real.
- **Ação:** acrescentar "operada por VINCI Airports + ANA (concessão de 40 anos)". Completar, não corrigir erro.
- Fontes: vinci-airports newsroom · aviationweek.com · ifc.org (2023)

### B3. Códigos das qualificações (ratings) — imprecisão técnica
- **Site diz** (`profissao.js`/`qualificacoes`): "ADI · APP procedural · APP vigilância ·
  ACC procedural · ACC vigilância".
- **ICAO (Anexo 1) oficial:** os códigos são **ADI, APP (Approach Procedural), APS (Approach
  Surveillance), ACP (Area Procedural), ACS (Area Surveillance)**. As do site são descritivas mas
  não são os códigos oficiais ("APP vigilância" = APS; "ACC procedural/vigilância" = ACP/ACS).
- **Ação (baixa):** manter a descrição PT mas indicar o código ICAO oficial entre parênteses
  (ex.: "Aproximação por vigilância (APS)"). Não é erro factual, é precisão.
- Fonte: skybrary.aero/articles/atco-licensing · eurocontrol ATCO Spec

---

## Confirmados (✅)

| # | Afirmação (ficheiro) | Veredicto | Fonte |
|---|----------------------|-----------|-------|
| C1 | Idade mínima **21 anos** (`licenciamento`,`profissao`) | ✅ bate com ICAO Anexo 1 | skybrary / sassofia (Annex 1) |
| C2 | **Inglês Nível Operacional 4** ICAO (`licenciamento`,`profissao`) | ✅ | icao.int PEL FAQ · skybrary ELP |
| C3 | **Certificado Médico Classe 3** para CTA (`licenciamento`) | ✅ padrão ICAO p/ ATCO | skybrary / AESA |
| C4 | **Objetivos ATS** (6 pontos, `responsabilidades`) | ✅ correspondem ao Anexo 11 da ICAO | (norma ICAO) |
| C5 | **FIR Oceânica do Sal gerida pela ASA**; cruza Europa↔América, África↔América (`estruturaAts`,`profissao`) | ✅ | asa.cv · atc-network · CANSO · Aireon |
| C6 | FIR "uma das maiores do Atlântico" (`estruturaAts`) | ✅ defensável (**~1,3 milhões km²**) — sugiro citar o número | Indra · Aireon · atc-network |
| C7 | **DL 9/80, de 11 de fevereiro** criou a FIR (`legislacao`,`estruturaAts`) | ✅ existe — está **no site da AAC** | aac.cv/documentos/decree-law-no-980-of-february-11 |
| C8 | **7 aeroportos**: 4 internacionais (Amílcar Cabral/Sal, Nelson Mandela/Praia, Aristides Pereira/Boa Vista, Cesária Évora/São Vicente) + 3 (Preguiça/São Nicolau, Maio, São Filipe/Fogo) (`estruturaAts`) | ✅ **todos corretos** | VINCI · Wikipedia |
| C9 | **Torres**: Sal, Praia, Boa Vista, São Vicente; **FIS**: São Filipe, Maio, São Nicolau (`estruturaAts`,`profissao`) | ✅ | asa.cv/navegacao-aerea |
| C10 | **AAC** = regulador aeronáutico que emite os CV-CAR e licencia CTA (`estruturaAts`) | ✅ | aac.cv |
| C11 | **IPIAAM** investiga acidentes; **DL 6/2023** (`estruturaAts`) | ✅ (nome completo: "Instituto de Prevenção e Investigação de Acidentes **Aeronáuticos e Marítimos**"; cobre também o marítimo) | ipiaam.cv · aac.cv |

---

## Não verificáveis online (❓) — exigem documento primário da AAC

Mantêm-se com a cautela editorial **já presente** no conteúdo ("Confirmar sempre na fonte
oficial vigente", "prevalece o CV-CAR 2.3 (2026)"). **Ação recomendada: hiperligar à AAC**
(sub-projeto C) em vez de remover, pois são plausíveis e bem-cauteladas.

- **CV-CAR 2.3 (2026)** — conteúdos específicos (3 meses OJTI; averbamento ≤ 3 anos;
  invalidação após 90 dias). A idade 21 e o inglês N4 estão cobertos pela ICAO (✅ acima).
- **CV-CAR 2.4** — periodicidades do Médico Classe 3 (até 30: 4 anos; 30–49: 2 anos; 50+: anual).
- **Diretiva n.º 01/PEL/2024** — escalonamento de reentrada (6m–1a / 1–5a / 5a+).
- **Taxas de conversão**: 4.500$00 por prova; 9.000$00 conversão; formulários FS.PEL.09 / FS.PEL.01.
  ⚠️ Valores monetários específicos = maior risco editorial ("sem números não-oficiais") —
  confirmar na tabela de taxas da AAC ou suavizar para "taxa conforme tabela da AAC".
- **ATO**: SENASA (CV-05/ATOE, validade 31/07/2027) e NAV Portugal (CV-12/ATOE, 25/07/2027).
  Existência das ATO é plausível; os **números de certificado e datas de validade** precisam da
  lista oficial de ATO da AAC (a `notaFonte` já avisa que é pontual).
- **Programa FPEF + SENASA** (24 vagas, Madrid) — vinha citado no relatório-fonte; confirmar fonte.
- **Decretos**: Código Aeronáutico (DL-Legislativo 1/2001 + 4/2009), Lei 64/IX/2019, DL 14/2022,
  CV-CAR 17, CV-CAR 22 — plausíveis e coerentes; idealmente hiperligar ao Boletim Oficial / AAC.
- **FIR — vigilância**: "Cobertura radar (Santo Antão, Sal e Santiago) e ADS-C". As fontes
  públicas enfatizam **ADS-B espacial (Aireon)** e a digitalização (Indra); a lista de **estações
  radar** não foi confirmada — confirmar na AIP/e-AIP ou suavizar.

---

## Também encontrado (fora do âmbito estrito de B)

- **Resíduo PT-PT (gap do sub-projeto A):** `formacao.js` tem `acadêmica` (grafia BR) em 2 strings
  visíveis → **`académica`** (PT-PT). O A não passou em `content/cta/`. Trivial — corrijo na Fase 2.
- **Sub-projeto C (hiperligações):** `contactosUteis.js` já tem os URLs oficiais (aac.cv, asa.cv,
  caboverde-airports.cv, uta.cv, senasa.es, nav.pt) — base pronta para C.
- **Sub-projeto D (imagem FIR):** a FIR Oceânica do Sal (~1,3 M km²) é o candidato; fonte de
  imagem oficial/licenciada a definir em D.

---

## Proposta de ações para a Fase 2 (a tua aprovação decide o alcance)

1. **B1 (alta):** corrigir nome da ASA → "Aeroportos e Segurança Aérea, S.A." (2 ficheiros).
2. **B2:** acrescentar operador da concessão (VINCI + ANA, 40 anos) em `estruturaAts.js`.
3. **B3 (baixa):** anotar códigos ICAO oficiais (APS/ACP/ACS) junto às descrições.
4. **C6:** citar a dimensão (~1,3 M km²) para credibilizar "uma das maiores do Atlântico".
5. **❓ itens:** **não remover** (estão bem cauteladas); hiperligar à AAC/asa.cv (entra no C).
   Exceção a decidir: **suavizar as taxas em escudos** (4.500$00 / 9.000$00) se não as
   confirmarmos na tabela oficial.
6. **PT-PT:** `acadêmica → académica` em `formacao.js`.

**Decisão tua antes da Fase 2:** (a) aprovas B1–B3 + C6 + PT-PT? (b) os ❓ — hiperligar e manter,
ou queres que eu suavize já as taxas em escudos?
