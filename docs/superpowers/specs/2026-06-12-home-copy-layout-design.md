# Home — copy e layout v2 · Design

**Spec date:** 2026-06-12
**Owner:** prisidenteaccta
**Scope:** `frontend/src/pages/public/HomePage.js` (sem alteração de API ou banner config)
**Tipo:** revisão de copy + reordenação/remoção de secções; sem novas dependências.

---

## 1. Contexto

A Home actual tem 11 secções e ~644 linhas. Mistura quatro propósitos (educar o público, atrair candidatos, servir sócios, identidade institucional) com copy de tom dramático ("Guardiões Invisíveis", "elite em terra", "complexas rotas") e dois CTAs do hero que competem por audiências distintas. A consequência é uma página longa, com ruído editorial e arco narrativo interrompido.

A memória do projecto e o `deep-research-report.md` confirmam que **o site público é uma base de conhecimento educativa** sobre o sector CTA em Cabo Verde, com guardrails editoriais rigorosos (sem números não-oficiais, sem inadimplência, sem retórica de marketing).

## 2. Objectivo

Re-alinhar a Home com a prioridade **educar o público** sobre o que é o controlo de tráfego aéreo em Cabo Verde, mantendo visibilidade discreta para sócios (Área do Associado, Evento, Notícias). Atingir o objectivo via:

1. Reduzir 11 → 10 secções (remover Stats Bar; encolher a secção de Evento).
2. Reescrever copy do Hero, da intro "O que é o CTA" e do CTA final para um registo **sereno e factual**.
3. Reordenar para um arco narrativo claro: **o quê → como → quem → onde → como tornar-se → actualidade**.

Fora do escopo: imagem de fundo do hero (gerida pela `spec-padronizacao-banners`), contratos de API, design tokens, animações globais.

## 3. Decisões aprovadas durante o brainstorm

| # | Decisão | Resultado |
|---|---|---|
| D1 | Prioridade #1 da Home | Educar o público sobre CTA |
| D2 | Featured Event mantém-se? | Sim, mas em formato *slim* |
| D3 | Últimas Notícias mantêm-se? | Sim, sem alterações ao formato actual (cards com imagem) |
| D4 | Stats Bar autónoma? | **Remover**. Não há km²/voos-ano em fontes oficiais; evitar fluff ("1 Missão") |
| D5 | Fluxo de evento+notícias | **Opção C (híbrido):** evento *slim* após o Hero; notícias mantidas antes do CTA final |
| D6 | Direcção do Hero | **Opção C** (sereno, factual), depois encurtado por preferência do dono |
| D7 | H1 do Hero | "O controlo de tráfego aéreo em Cabo Verde." (versão curta) |
| D8 | Scroll indicator decorativo | **Remover** |
| D9 | CTA final ("Junte-se aos profissionais...") | **Reescrever** — registo institucional ACCTA-como-associação |

## 4. Arquitectura final da página

Ordem das secções (10 no total):

```
01  Hero                       reescrever
02  Evento em destaque (slim)   conditional render mantido
03  O que é o CTA              reescrever copy (cards mantidos)
04  Como funciona — TWR/APP/ACC intacto
05  Quem opera — 4 entidades    intacto
06  FIR Oceânica do Sal         intacto
07  Caminho para CTA — 5 etapas intacto
08  FAQ — 6 perguntas           intacto
09  Últimas notícias            intacto (cards com imagem, decisão D3)
10  CTA final                   reescrever
```

Eliminada: **Stats Bar** (antiga secção 02).

## 5. Especificação por secção

### 5.1 · Hero (reescrita)

**Mantém:** estrutura DOM (`<section>` com background image + gradient overlay), classes Tailwind de altura (`min-h-[600px] sm:min-h-[85vh] lg:min-h-[90vh]`), `animate-fade-up`, container `max-w-7xl`, alinhamento `max-w-2xl` do bloco de texto.

**Substitui:**

| Elemento | Antes | Depois |
|---|---|---|
| Pill badge | `<Radio>` + "ACCTA Cabo Verde" (uppercase, tracking-wider, font-semibold) | `● ACCTA · Cabo Verde` — sem ícone Lucide; ponto carmesim renderizado como `<span className="w-2 h-2 rounded-full bg-carmesim">` antes do texto |
| H1 | "Os Guardiões Invisíveis dos Céus de Cabo Verde" | "O controlo de tráfego aéreo em Cabo Verde." |
| Lead | "24 horas por dia, garantimos a segurança, a fluidez e a soberania do espaço aéreo no meio do Atlântico. **Nós somos a CTA.**" | "Somos os controladores de tráfego aéreo que organizam, comunicam e protegem cada voo na FIR Oceânica do Sal — uma das maiores regiões de informação de voo do Atlântico." |
| CTA primário | "Conheça a Profissão" (Floresta) → `/profissao` | "Conhecer a profissão" (Floresta) → `/profissao` |
| CTA ghost | "Área do Associado" → `/login` | "Área do associado" → `/login` |
| Scroll indicator | bolinha carmesim em rect arredondado | **Remover** |

Notas de estilo:
- O H1 mantém `font-bold text-3xl sm:text-5xl lg:text-6xl xl:text-7xl text-white leading-tight`.
- Sem `<span>` decorativo no H1 — texto plano (a sobriedade é o ponto).
- O `data-testid="hero-title"` e os `data-testid` dos CTAs **mantêm-se** para os testes existentes.
- Verbos em CTA passam de imperativo formal ("Conheça") para infinitivo ("Conhecer") — uniforme com o resto do site (`/eventos`, `/profissao`).

### 5.2 · Evento em destaque — *slim* (reescrita parcial)

Render condicional **mantido** (só se `eventsAPI.getFeatured()` devolve evento).

**Encolhe:**
- `<section>` exterior: `py-12 sm:py-16` → `py-8 sm:py-10`
- Card interior: `p-6 sm:p-10 lg:p-12` → `p-5 sm:p-7 lg:p-8`
- Countdown boxes: `w-16 h-16 sm:w-20 sm:h-20` → `w-12 h-12 sm:w-14 sm:h-14`
- Countdown digits: `text-2xl sm:text-3xl` → `text-xl sm:text-2xl`
- Background pattern (dots radial) e blur orange decorativo: **removidos** (reduzem ruído e custo de pintura)
- Layout 2-col `lg:grid-cols-2` permanece; o lado esquerdo (info) ganha mais respiro.

**Mantém copy:** badge "Próximo evento" (corrigir acento — actual é "Proximo"), título do evento (vem da API), descrição truncada a 150 chars, ícones Calendar/Clock/MapPin/Users.

**Mantém testids:** `featured-event-section`, `featured-event-title`, `countdown-timer`, `countdown-dias/horas/minutos/segundos`.

### 5.3 · O que é o CTA (reescrita de copy)

**Mantém estrutura:** `<section>` com `bg-gray-50`, grid 2-col com texto à esquerda e 4 cards à direita.

**Substitui:**

| Elemento | Antes | Depois |
|---|---|---|
| Pill badge | "O que fazemos" | "O que é o CTA" |
| H2 | "Muito além da **Torre de Controlo**" | **Mantém** (funciona, é educativo) |
| Body §1 | "Quando embarca num avião, vê o piloto e a tripulação. Mas existe uma **equipa de elite em terra**, monitorizando cada metro do seu voo." | "Quando embarca num avião, vê o piloto e a tripulação. Em terra, há também uma equipa que acompanha cada fase do voo — da partida à chegada." |
| Body §2 | "O Controlador de Tráfego Aéreo (CTA) é o responsável por evitar colisões, organizar descolagens e aterragens e guiar aeronaves em segurança através das complexas rotas do Atlântico." | "O Controlador de Tráfego Aéreo (CTA) organiza descolagens e aterragens, mantém a separação entre aeronaves e guia os voos pelas rotas do Atlântico médio." |
| Link inferior | "Saiba como funciona o controlo aéreo" → `/profissao` | **Mantém** |

**Mantém intactos** os 4 cards (Vigilância 24h / Comunicação / Segurança / Coordenação) e os respectivos ícones Lucide.

### 5.4 · Como funciona — TWR / APP / ACC

**Sem alterações.** Conteúdo vem de `tiposControlo` em `content/cta`. Layout grid 3-col, cards `card-technical card-hover`.

### 5.5 · Quem opera — AAC / ASA / Cabo Verde Airports / IPIAAM

**Sem alterações.** Conteúdo vem de `camadas` em `content/cta`. Layout grid 4-col.

### 5.6 · FIR Oceânica do Sal

**Sem alterações.** A banda escura, o subtitle ("Uma das maiores regiões de informação de voo do Atlântico, operada pela ASA a partir da ilha do Sal.") e os 4 mini-cards (Cobertura / Comunicações / Vigilância / Rotas) **já estão alinhados** com as fontes oficiais (DL n.º 9/80; VHF, HF, CPDLC; radar de Santo Antão+Sal+Santiago + ADS-C). Não adicionar km² nem voos-ano (não consta em fontes oficiais).

### 5.7 · Caminho para CTA — 5 etapas

**Sem alterações.** Conteúdo vem de `caminhoCTA` em `content/cta`; resumos de 1 linha vivem em `CAMINHO_RESUMO` (local ao componente, manter).

### 5.8 · FAQ — 6 perguntas

**Sem alterações.** Conteúdo vem de `faq.slice(0, 6)` em `content/cta`. Accordion mantém-se single-collapsible.

### 5.9 · Últimas notícias

**Sem alterações** (D3). Continua com 3 cards (`postsAPI.getAll({ visibility, status, limit: 3 })`) com imagem de capa (cover_url ou fallback `NEWS_IMAGES`), título, excerpt e link "Ler mais →".

### 5.10 · CTA final (reescrita)

**Mantém:** `<section>` grafite com grid pattern, container central, 2 CTAs.

**Substitui:**

| Elemento | Antes | Depois |
|---|---|---|
| H2 | "Junte-se aos profissionais que garantem a **segurança dos céus**" | "A ACCTA representa os controladores de tráfego aéreo de Cabo Verde." |
| Lead | "A ACCTA representa e valoriza os controladores de tráfego aéreo de Cabo Verde" | "Conheça quem somos, o que defendemos e como participamos no setor da navegação aérea." |
| CTA primário | "Conheça a Associação" (Floresta) → `/sobre` | "Conhecer a associação" (Floresta) → `/sobre` |
| CTA ghost | "Entre em Contacto" → `/contactos` | "Entrar em contacto" → `/contactos` |

A reescrita resolve a ambiguidade do título actual ("junte-se aos profissionais" lê-se como "candidate-se a controlador" e não como "junte-se à associação").

## 6. Impacto técnico

### 6.1 Ficheiros tocados
- `frontend/src/pages/public/HomePage.js` — único ficheiro.

### 6.2 Imports a remover
Após a remoção da Stats Bar (e o seu uso de `Globe` + `Target`) — verificar se `Globe`, `Target`, `Plane`, `Shield`, `Users`, `Clock`, `MapPin` continuam usados em outras secções (FIR usa `Globe`, `Radio`, `Navigation`, `Plane`; Evento usa `Calendar`, `Clock`, `MapPin`, `Users`; What-We-Do usa `Eye`, `Radio`, `Shield`, `Plane`). Limpar imports não usados após edição.

### 6.3 Dados e APIs
- **Nenhuma alteração** a `postsAPI`, `eventsAPI`, `bannersAPI`, `queryKeys`, `unsplashSrcSet`, `bannerDefault`.
- **Nenhum** novo endpoint, modelo Pydantic ou tabela.
- `content/cta` (`tiposControlo`, `camadas`, `fir`, `caminhoCTA`, `faq`) — **inalterado**.

### 6.4 Testes
- Testes E2E e unitários que dependam de `hero-title`, `hero-cta-primary`, `hero-cta-secondary`, `featured-event-section`, `featured-event-title`, `countdown-timer` — todos os `data-testid` **mantêm-se**.
- Testes que verifiquem o texto "Os Guardiões Invisíveis" ou "Junte-se aos profissionais" terão de ser actualizados (procurar e listar no plano).

### 6.5 Acessibilidade e responsividade
- Contraste mantido: branco sobre grafite (≥4.5:1 já cumprido).
- Hero responsivo já cobre `sm`, `lg`, `xl`. Encolhimento do Evento valida em mobile (countdown de `w-12 h-12` continua tappable).
- Sem mudanças a tabindex ou ordem visual/DOM.

## 7. Princípios editoriais aplicados

1. **Português europeu** (memória `communicate-in-portuguese`): "actual", "factual", "perceber" (não "perceber" do BR), "ficheiro", verbos no infinitivo nos CTAs.
2. **Sem números não-oficiais** (memória `public-site-knowledge-base`): nenhum km², nenhum voos-ano, nenhum "movimento por hora" — só dados confirmados no `deep-research-report`.
3. **Sem "elite", "guardiões", "soberania"** — registo institucional sereno.
4. **Sem inadimplência / sem auto-promoção** — Home é educativa, não comercial.
5. **CV-CAR 2.3 (2026)** prevalece nas referências a regime de licenciamento (já reflectido em `caminhoCTA` e FAQ).
6. **Brand tokens** (frontend-design skill): Carmesim para identidade/links/destrutivo, Floresta para o único primary positivo (já é o caso nos CTAs do hero e final).

## 8. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Testes E2E que assertam strings antigas falham | Plano de implementação lista todos os data-testid e strings substituídas; testes actualizados na mesma PR |
| Dono prefere o título dramático para fins de marca | Decisão D6 + D7 já confirmadas; reverter é trivial (1 string) |
| O slim do Evento corta utilidade | Mantém todos os campos (título, descrição, data/hora/local, atendees, countdown); só reduz padding e tamanho — não é remoção de informação |
| Imports não usados causam ESLint warnings | Verificar e limpar `lucide-react` imports não usados; ESLint config do projecto permite 60 warnings (`--max-warnings=60`) |

## 9. Critério de aceitação

- [ ] HomePage.js tem 10 secções, na ordem definida em §4.
- [ ] Hero: H1, lead, badge e CTAs reescritos conforme §5.1; scroll indicator removido.
- [ ] Stats Bar removida (incluindo o array com Globe/Clock/MapPin/Target).
- [ ] Evento *slim* aplicado conforme §5.2; conditional render mantido.
- [ ] "O que é o CTA": badge "O que é o CTA", body §1 e §2 reescritos; 4 cards intactos.
- [ ] CTA final reescrito conforme §5.10.
- [ ] Lint passa (`yarn eslint src/ --ext .js,.jsx --max-warnings=60`).
- [ ] Testes existentes passam ou foram actualizados na mesma PR.
- [ ] Visual smoke test no `yarn start` em ≥1 resolução desktop e ≥1 mobile.

## 10. Não está nesta spec

- Mudança de imagem do hero (gerida por banners config).
- Alteração de copy nas secções 4, 5, 6, 7, 8, 9.
- Reorganização da navegação ou do footer.
- Nova secção "Imprensa", "Parceiros" ou similar.
- Tradução para outras línguas.
- A/B testing de copy.
