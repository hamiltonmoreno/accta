# Spec — 40 Artigos do Blog / Notícias do Portal ACCTA

> **Objetivo:** definir 40 artigos para publicar no blog/notícias do Portal
> ACCTA, redigidos **estritamente** a partir da base de conhecimento
> autoritativa (`memory/deep-research-report.md`), cobrindo **as três
> categorias** do blog (`noticia`, `institucional`, `educativo`).
>
> **Natureza deste documento:** especificação de conteúdo. **Não implementa
> nada** — define o quê, com que origem, com que regras editoriais e como
> carregar. A implementação será feita **depois de o blog estar pronto**
> (ver dependência em §3, alinhada com `tasks/spec-blog-noticias.md`).
>
> **Branch:** `claude/create-blog-articles-s3FCm`

---

## 1. Contexto

O módulo de notícias existe (`backend/routes/posts.py`, `GET/POST /api/posts`;
página pública `frontend/src/pages/public/NoticiasPage.js` com filtro por
`type`), mas é hoje **só de leitura, alimentado por seed** — sem página de
detalhe, sem CRUD de gestão (diagnóstico completo em `tasks/spec-blog-noticias.md`).

Em paralelo, a área pública já foi alinhada à base de conhecimento
(`tasks/spec-base-conhecimento.md`, executada): nomes corretos (AAC = **Agência**
de Aviação Civil), **FIR Oceânica do Sal**, remoção de números não oficiais,
sem o conceito de inadimplência. **Estes artigos herdam exatamente essas regras.**

Esta spec define o **conteúdo editorial** (os 40 artigos). A *capacidade* de os
ler por inteiro depende da página de detalhe descrita na spec do blog — daí a
dependência em §3.

---

## 2. Fonte de verdade e regras editoriais (herdadas de `spec-base-conhecimento.md`)

1. **Fonte única e exclusiva:** `memory/deep-research-report.md`. Nenhum facto
   fora do relatório. (Os "PDFs da associação" originais não estão no repositório;
   o relatório é a sua consolidação autoritativa.)
2. **PT-PT** (português europeu) em todo o texto. O relatório está em PT-BR — o
   conteúdo **nasce PT-PT** (ex.: "facto", "contacto", "registo", "equipa",
   "reformado", "planeamento").
3. **Citar a base legal** ao afirmar um requisito (CV-CAR / decreto).
4. Em **divergência regulatória** prevalece o **CV-CAR 2.3 (2026)**. Nunca
   reproduzir a info antiga da AAC (licença "5 anos" / perda após "6 meses").
5. **Não publicar números sem fonte oficial.** Onde o relatório marca
   **"não especificado"** (UTA/UIR, salários) → formulação neutra ("não
   especificado; consultar a AIP/e-AIP vigente"), nunca inventar.
6. **AAC = Agência de Aviação Civil** (nunca "Autoridade"); **FIR Oceânica do
   Sal** (nunca "FIR de Sal" / "FIR Sal").
7. **Sem inadimplência/adimplência** em lado nenhum.
8. Voz **institucional** nos artigos da associação (a ACCTA é tratada como
   constituída — decisão do dono), **mas sem inventar** dados institucionais
   (datas de fundação, número de sócios, composição da diretoria, números de
   artigos dos estatutos). Conteúdo associativo grounded nos *modelos prontos*
   do relatório (missão, código de conduta, ficha de adesão).
9. Validades pontuais de terceiros (ex.: certificados de ATO) publicam-se sempre
   **com data/fonte e formulação que envelhece bem** ("conforme a lista da AAC à
   data de…; confirmar a versão vigente").

---

## 3. Dependência e onde os artigos vão viver

### 3.1 Dependência (porquê implementar **depois** do blog)
A `NoticiasPage` trunca o conteúdo (`line-clamp-3`) e **não há rota de detalhe**
(`/noticias/:slug`). Artigos longos só serão **lidos por inteiro** quando a
página de detalhe da `tasks/spec-blog-noticias.md` (MVP) existir. Por isso:

> **Recomendação:** carregar os 40 artigos **após** a Fase 2 da
> `spec-blog-noticias.md` (detalhe público + migração da lista). Até lá, os
> artigos aparecem como cartões com texto truncado — funcional, mas incompleto.

### 3.2 Modelo de dados alvo (coleção `posts`)
Campos que cada artigo deve preencher. O modelo atual (`backend/models.py`,
`Post`) tem `id, title, content, type, visibility, tags, created_at`. Os campos
extra abaixo (`slug`, `excerpt`, `status`, `author_name`, `published_at`) são
**desejáveis e seguros**: o `Post` usa `extra="ignore"`, portanto persistem no
`jsonb` e ficam **prontos** para o modelo estendido da `spec-blog-noticias.md`
(§4.1) sem partir o que existe.

| Campo | Valor para estes artigos |
|---|---|
| `id` | determinístico — `uuid5` do slug (idempotência; ver §4) |
| `title` | título do artigo (PT-PT) |
| `slug` | kebab-case do título, sem acentos (`unicodedata` NFKD) |
| `excerpt` | resumo de 1–2 frases (≤320 carateres) — serve de *lead* e de preview do cartão |
| `content` | corpo completo, texto simples com parágrafos separados por linha em branco (render futuro `whitespace-pre-wrap`) |
| `type` | `noticia` \| `institucional` \| `educativo` (ver catálogo §5) |
| `visibility` | `publico` (37) \| `socios` (3) (ver catálogo §5) |
| `status` | `publicado` |
| `tags` | 3–5 tags PT-PT relevantes |
| `author_name` | `"ACCTA"` |
| `created_at` / `published_at` | ISO-8601; espalhar por datas decrescentes (ver §4) |

> ⚠️ **Conteúdo em texto simples** (sem HTML/Markdown renderizável) — coerente
> com o MVP da spec do blog (sem `dangerouslySetInnerHTML`).

---

## 4. Abordagem de implementação (a executar depois)

**Decisão do dono (confirmada):** **script de seed dedicado e idempotente**,
versionado, **não destrutivo** — não a inserção direta na BD nem o
`seed_data.py` (que apaga e recria coleções).

Ficheiro a criar: **`scripts/seed_blog_articles.py`**, seguindo o padrão de
`scripts/seed_gallery.py`:

- `sys.path.insert(0, …/backend)`, `load_dotenv(backend/.env)`,
  `from database import db, ensure_schema, close_pool`; `asyncio.run(...)`.
- **Idempotência:** `id = str(uuid.uuid5(NAMESPACE_URL, "https://controlador.cv/noticias/" + slug))`.
  Para cada artigo: `find_one({"id": id})` → se existe, `update_one($set=…)`
  **preservando `created_at`/`published_at`**; senão `insert_one`. Correr N
  vezes não duplica nem reescreve a cronologia.
- **Sem `delete_many`** (nada é apagado).
- **Datas:** `published_at = created_at = BASE_DATE - (índice × 3 dias)` para uma
  ordenação determinística (mais recentes primeiro).
- **Guarda editorial offline** (`validate_articles()`, corre sem BD): assere
  `len == 40`, slugs/ids únicos, as **3 categorias presentes**, `excerpt ≤ 320`,
  e faz *scan* de **termos proibidos** (`inadimpl`, `adimplência`,
  `"Autoridade de Aviação"`, `"FIR de Sal"`).
- Execução: `python scripts/seed_blog_articles.py` (idempotente).

> Opcional na implementação: um teste leve (`backend/tests/`) que importa
> `ARTICLES` e corre `validate_articles()` — sem BD, rápido, fixa o contrato.

---

## 5. Catálogo dos 40 artigos

Distribuição: **educativo 27 · institucional 7 · notícia 6** = **40**.
Visibilidade: **publico 37 · socios 3** (os 3 `socios` são institucionais
orientados ao membro). "Fonte" remete para a secção de
`memory/deep-research-report.md` e/ou a base legal.

### 5.1 Educativo (27 · todos `publico`)

| Nº | Título | Fonte (relatório / base legal) | Âmbito (resumo) |
|---|---|---|---|
| 1 | O que faz um controlador de tráfego aéreo | Definições e escopo · Anexo 11 ICAO · CV-CAR 2.3 | Definição fiel de CTA; objetivos do ATS; o que o controlador faz no dia a dia. |
| 2 | Como se tornar CTA em Cabo Verde | Formação/licenciamento (timeline) · CV-CAR 2.3/2.4 | Caminho-padrão em 5 etapas: pré-requisitos → formação → operacional → ingresso → manutenção. |
| 3 | A estrutura de navegação aérea em quatro camadas | Estrutura organizacional · DL 47/2019, Lei 64/IX/2019, DL 14/2022, DL 6/2023 | AAC (regulação), ASA (ATS), Cabo Verde Airports (aeroportos), IPIAAM (investigação). |
| 4 | FIR Oceânica do Sal | Marco legal · DL 9/80 | Criação, integração no Aeroporto Amílcar Cabral, âmbito ICAO; UTA/UIR **não especificado**. |
| 5 | As cinco qualificações do controlador | Formação/licenciamento · CV-CAR 2.3 | ADI, APP procedural, APP vigilância, ACC procedural, ACC vigilância. |
| 6 | Certificado Médico Classe 3 | Formação/licenciamento · CV-CAR 2.4 | O que é e periodicidade escalonada por idade (ECG, ORL/audiograma, oftalmo). |
| 7 | Inglês Nível Operacional 4 | Formação/licenciamento · CV-CAR 2.3 | Proficiência para radiotelefonia; escala ICAO; exigência na conversão. |
| 8 | Averbamento de órgão de controlo | Formação/licenciamento · CV-CAR 2.3 | Validade ≤3 anos; invalida após >90 dias; revalidação. |
| 9 | ATC, FIS e serviço de alerta | Definições · Anexo 11 · CV-CAR 17 | Os três serviços de tráfego aéreo. |
| 10 | Condições de trabalho e prevenção da fadiga | Trabalho/carreira · CV-CAR 17 | 5 min/mudança de turno; ≤6h contínuas; turno ≤8h; local de descanso. |
| 11 | Onde formar: ATO aprovadas pela AAC | Formação (lista de ATO) | SENASA e NAV Portugal; escopo de cursos; validades pontuais (confirmar). |
| 12 | Conversão de licença estrangeira | Formação (fluxo AAC) | FS.PEL.09 (4.500$00) → FS.PEL.01 (9.000$00); prova de proficiência. |
| 13 | Unidades operacionais: ACC, torres e FIS | Estrutura organizacional · ASA | ACC Sal; torres Sal/Praia/Boa Vista/São Vicente; FIS São Filipe/Maio/São Nicolau. |
| 14 | Recência e revalidação | Formação/licenciamento · CV-CAR 2.3 | Horas mínimas, refrescamento, avaliação; limite dos 90 dias. |
| 15 | Controlo de área, aproximação e aeródromo | Definições · CV-CAR 17 | Os três níveis do ATC e quem presta cada um. |
| 16 | Os 3 meses sob OJTI | Formação/licenciamento · CV-CAR 2.3 | Da formação à prontidão operacional (controlo real supervisionado). |
| 17 | O quadro legal da aviação civil em Cabo Verde | Marco legal (tabela de diplomas) | Hierarquia: Código Aeronáutico (DL-Leg 1/2001, alt. 4/2009) → CV-CAR; prevalece CV-CAR 2.3. |
| 18 | As normas ICAO que enquadram o trabalho do CTA | Marco legal · Anexos 1/11/19, Doc 4444/7030 | Padrões internacionais aplicáveis ao licenciamento e ao ATS. |
| 19 | Reentrada após afastamento longo | Formação/licenciamento · Diretiva 01/PEL/2024 | Gradação >6m–1a / 1–5a / >5a (regra de reentrada, não de ingresso). |
| 20 | Requisitos de elegibilidade: idade, conhecimentos e experiência | Formação/licenciamento · CV-CAR 2.3 | ≥21 anos; áreas obrigatórias de conhecimento; experiência supervisionada. |
| 21 | Caminhos de carreira do CTA | Trabalho/carreira · CV-CAR 2.3 + vaga AAC | Instruendo → qualificações/averbamento → OJTI/STDI/avaliador → supervisão/inspeção. |
| 22 | UTA/ISAT: formação académica complementar | Formação · UTA/ISAT | Gestão e Planeamento da Aviação Civil; **não** é via de licença CTA. |
| 23 | Comunicações e vigilância na FIR do Sal | Estrutura organizacional · divulgação AAC | VHF/HF/CPDLC; radar Santo Antão/Sal/Santiago; ADS-C; UTA/UIR **não especificado**. |
| 24 | Aeródromo e aeroporto: as definições oficiais | Definições · AAC | Distinção técnica; 7 aeródromos (4 internacionais + 3 domésticos). |
| 25 | Cultura justa, SMS e sistema de qualidade | Trabalho/carreira · CV-CAR 17/22 | Sistema de qualidade, gestor de qualidade, SMS aprovado, notificação de ocorrências. |
| 26 | Da notificação de ocorrências à investigação técnica | Trabalho · CV-CAR 17/22, DL 6/2023 | Fluxo: mitigação → registo → preservação → notificação → análise → (se grave) investigação. |
| 27 | Dados não especificados: porque publicamos só o oficial | Limitações e pontos em aberto | Salários e UTA/UIR **não especificados**; consultar AIP/e-AIP; política de rigor. |

### 5.2 Institucional (7)

| Nº | Título | Vis. | Fonte (relatório) | Âmbito (resumo) |
|---|---|---|---|---|
| 28 | Missão e objetivos da ACCTA | publico | Representação coletiva (voz institucional) | Missão, objetivos e papel educativo da associação. |
| 29 | Quem é a ACCTA: a voz dos controladores | publico | Representação coletiva | Identidade; três compromissos (segurança, valorização, condições de trabalho). |
| 30 | O compromisso com a segurança e a cultura justa | publico | CV-CAR 22/17 | Cultura justa de reporte; bases regulamentares. |
| 31 | Defesa de condições de trabalho dignas e seguras | **socios** | CV-CAR 17 | Salvaguardas de fadiga como base de pauta associativa. |
| 32 | Código de conduta da ACCTA | **socios** | Conteúdo pronto (modelo de código de conduta) | Princípios, deveres, condutas vedadas, comissão de ética, sanções. |
| 33 | Transparência, prestação de contas e política editorial | **socios** | Regras editoriais (§2) | Governança + política editorial (fonte oficial; CV-CAR 2.3 prevalece; "não especificado"). |
| 34 | Quem pode aderir à ACCTA e categorias de membro | publico | Conteúdo pronto (ficha de adesão) | Situações (operacional/instruendo/reformado/inspetor) e categorias (efetivo/associado/fundador/honorário). |

### 5.3 Notícia (6 · todos `publico`)

> ⚠️ "Notícia" aqui = **desenvolvimentos factuais** presentes no relatório,
> enquadrados como informação datada — **nunca eventos inventados** (a seed atual
> tem exemplos fictícios — "10 anos", "parceria IFATCA" — que **não** devem ser
> replicados).

| Nº | Título | Fonte (relatório / base legal) | Âmbito (resumo) |
|---|---|---|---|
| 35 | CV-CAR 2.3 (2026): o novo regime de licenciamento | Marco legal · CV-CAR 2.3 | Elimina a validade da licença; foco em qualificações/averbamentos; incorpora Anexo 1. |
| 36 | Cabo Verde Airports assume a gestão dos aeroportos (desde julho 2023) | Marco legal · Lei 64/IX/2019, DL 14/2022 | Concessão em vigor; ASA mantém a prestação ATS. |
| 37 | FPEF e SENASA abrem curso inicial de controlo de tráfego aéreo | Formação patrocinada | 24 vagas, Madrid, 16 semanas, seleção em 3 fases. |
| 38 | ASA passa a apresentar-se como Navegação Aérea de Cabo Verde | Estrutura organizacional | Reposicionamento institucional; prestador ligado ao trabalho do CTA. |
| 39 | IPIAAM e o regime de investigação técnica | DL 6/2023 | Investigação de acidentes/incidentes graves, distinta de regulação e reporte. |
| 40 | AAC mantém SENASA e NAV Portugal entre as ATO aprovadas | Lista oficial de ATO | Escopo de cursos CTA; validades pontuais a confirmar. |

---

## 6. Tags (orientação)

3–5 por artigo, PT-PT, minúsculas/siglas, reutilizáveis entre artigos para
permitir agrupar por tema. Vocabulário sugerido: `CTA`, `licenciamento`,
`formação`, `CV-CAR 2.3`, `CV-CAR 17`, `CV-CAR 2.4`, `CV-CAR 22`, `AAC`, `ASA`,
`FIR`, `ATS`, `ATC`, `FIS`, `ICAO`, `segurança`, `cultura justa`,
`condições de trabalho`, `medicina aeronáutica`, `inglês`, `qualificações`,
`averbamento`, `recência`, `carreira`, `ACCTA`, `associação`, `legislação`,
`transparência`, `aeroportos`, `IPIAAM`.

---

## 7. Critérios de aceitação

1. Existem **40 artigos**, com slugs e ids (uuid5) únicos.
2. As **três categorias** estão presentes (educativo/institucional/notícia) e o
   filtro da `NoticiasPage` (`Todas/Notícias/Institucional/Educativo`) mostra
   conteúdo em cada uma.
3. **Zero termos proibidos**: `grep -ri` por `inadimpl`, `adimplência`,
   `Autoridade de Aviação`, `FIR de Sal`, e por números banidos da
   `spec-base-conhecimento.md` (`60 profissionais`, `500 voos`, `40-50 milhas`)
   → sem resultados no conteúdo.
4. Cada afirmação de **requisito** cita a sua **base legal** (CV-CAR/decreto).
5. Dados marcados "não especificado" no relatório (UTA/UIR, salários) **não** são
   inventados.
6. Texto **PT-PT**; voz institucional nos artigos da associação **sem** dados
   institucionais inventados.
7. O script de seed é **idempotente** (correr 2× não duplica) e **não destrutivo**.
8. `ruff check scripts/ && ruff format --check scripts/` sem erros no novo script.

---

## 8. Faseamento (na implementação futura)

- **Fase A** — (pré-requisito recomendado) MVP de detalhe do blog
  (`spec-blog-noticias.md`, Fases 1–2): `GET /posts/{id_or_slug}`, rota pública
  `/noticias/:slug`, cartões com link e `excerpt`.
- **Fase B** — criar `scripts/seed_blog_articles.py` com `ARTICLES` (40),
  `build_post_doc`, `validate_articles`, seed idempotente (§4).
- **Fase C** — redigir os 40 corpos (§2 + §5), revisão editorial PT-PT.
- **Fase D** — correr o seed; verificar §7 (catálogo visível, greps limpos,
  build/lint).

---

## 9. Riscos e stop conditions (CLAUDE.md)

- **Modelo Pydantic:** **não** alterar `Post` nesta entrega de conteúdo. Os
  campos extra (`slug`/`excerpt`/`status`/…) são tolerados por `extra="ignore"`;
  enums (`Literal`) e novos campos pertencem à `spec-blog-noticias.md` (decisão
  separada). Se essa spec for implementada com `Literal`, garantir que
  `type ∈ {noticia,institucional,educativo}` e `visibility ∈ {publico,socios}`
  destes artigos são válidos (são).
- **Sem migração destrutiva:** seed só insere/atualiza; nunca `delete_many`.
- **Não inventar** dados institucionais da ACCTA nem números sem fonte oficial.
- **Validades de terceiros** (ATO) e contactos são pontuais — publicar com
  data/fonte.
- Conteúdo em **texto simples** (sem HTML) enquanto o detalhe do blog não
  suportar Markdown sanitizado.

---

## 10. Ficheiros impactados (na implementação futura)

| Ficheiro | Mudança |
|---|---|
| `scripts/seed_blog_articles.py` | **novo** — 40 artigos + seed idempotente + validação offline |
| `backend/tests/test_seed_blog_articles.py` | *(opcional)* importar `ARTICLES` e correr `validate_articles()` |
| `memory/deep-research-report.md` | *(só leitura)* — fonte de verdade |
| — | **Nada** no backend de rotas/modelos nem no frontend é alterado por esta spec de conteúdo |

---

_Fonte autoritativa do conteúdo: `memory/deep-research-report.md`. Regras
editoriais herdadas de `tasks/spec-base-conhecimento.md`. Mecânica do blog e
modelo estendido: `tasks/spec-blog-noticias.md`._
