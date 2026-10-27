# Feature Specification: Site Público em EN e FR (i18n)

**Feature Branch**: `feature/021-i18n-publico-en-fr`

**Created**: 2026-07-14

**Status**: Ready for `/speckit-plan` (3 gates fechados pelo dono 2026-07-14)

**Input**: User description: "quero que toda pagina publica seja em ingles e frances tambem"

---

## Contexto & Motivação

O Portal ACCTA representa uma associação profissional cabo-verdiana cujo público-alvo primário são sócios em Cabo Verde, mas cuja **área pública** (marketing/knowledge-base) é acedida também por:

- Parceiros e instituições internacionais (IFATCA, ICAO, entes reguladores da região);
- Diáspora profissional lusófona e não-lusófona (interlocutores em Portugal, Brasil, mas também França/Bélgica/Suíça — francófonos — e mercados anglófonos);
- Recrutadores e candidatos internacionais que chegam pela página **Profissão**;
- Imprensa e a comunidade da CV-CAR (2.3/2026).

Hoje **todo o site público é em português europeu**. Este trabalho passa a oferecê-lo também em **inglês** e **francês**, com o **PT como fonte canónica** (o que se traduz é a versão PT em uso). A área privada dos sócios (`/dashboard`, `/carteira`, `/financeiro`, `/assembleias`, etc.) **permanece exclusivamente em PT**.

> ⚠️ **Nota constitucional (v1.1.0)**: o Princípio IV da constituição afirma "user-facing text MUST be in European Portuguese". Esta feature exige uma **emenda MINOR (v1.2.0)** que restrinja o âmbito do princípio a **áreas autenticadas** e permita EN/FR no site público. A emenda é pré-requisito da entrega (parte da fase F0). Se rejeitada pelo dono, o spec não avança.

---

## Clarifications

### Session 2026-07-14

- Q: Slugs por idioma — traduzir cada slug (`/en/about`) ou manter os slugs PT em todos os prefixos (`/en/sobre`)? → A: **Slugs PT mantidos.** Estrutura única de URL para todas as locales; SEO por idioma garantido via `hreflang` + prefixo + `<html lang>`, sem depender do slug. Slugs traduzidos podem ser reconsiderados numa spec futura se houver procura real.
- Q: Ao trocar de idioma via seletor numa página específica (ex.: `/en/sobre` → clicar FR), a app volta à Home do novo locale ou preserva a página? → A: **Preserva a página** — troca só o prefixo de locale (`/en/sobre` → `/fr/sobre`). Se a rota-alvo não existir na locale de destino (improvável na v1, uma vez que o shell traduz todas), fallback para `/{locale}/` (Home).
- Q: Regra do aviso «Content in Portuguese» sobre conteúdo dinâmico (notícia detalhe, publicação, comunicado, artigo Ajuda, corpos sociais Sobre, descrição de álbum) — quando aparece? → A: **Sempre visível** quando shell é EN/FR **e** a página é de conteúdo dinâmico (regra binária por rota, não por conteúdo). Banner discreto (fundo cinza claro, texto pequeno), textos EN «This content is in Portuguese» / FR «Ce contenu est en portugais». Não é aplicado à Home nem a outras páginas puramente estáticas.
- Q: Rota inexistente sob `/en/…` ou `/fr/…` — como responde? → A: **404 traduzida no locale** — página 404 com shell no idioma ativo (título EN «Page not found» / FR «Page introuvable»), ligação de recuperação para `/{locale}/` (Home) e seletor de idioma visível. Coerente com SC-006 (0 strings PT quando shell é EN/FR).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Visitante escolhe idioma e navega o site em EN/FR (Prioridade: P1)

Um visitante entra na Home e o site apresenta-se automaticamente no idioma detectado do navegador (`Accept-Language`), com um seletor de idioma visível para trocar manualmente. Depois de escolher (ou aceitar a detecção), navega Home → Sobre → Profissão → Contactos e todo o conteúdo estático (títulos, subtítulos, corpo, botões, rodapé, formulário de contacto) aparece coerentemente no idioma escolhido. A escolha persiste na próxima visita (sem obrigar a re-selecionar).

**Why this priority**: é o coração da feature; sem isto, nada da entrega tem valor.

**Independent Test**: numa janela anónima, abrir o site com `Accept-Language: fr`; a Home carrega em FR; abrir o menu de idiomas e trocar para EN; navegar 3 páginas e confirmar que todas mostram EN; fechar o browser, reabrir, confirmar que a escolha EN persistiu.

**Acceptance Scenarios**:

1. **Given** um visitante primeira-vez com `Accept-Language: fr-FR`, **When** abre a Home, **Then** a página carrega em francês, com o seletor a mostrar «FR» ativo.
2. **Given** um visitante primeira-vez com `Accept-Language: en-US`, **When** abre a Home, **Then** a página carrega em inglês.
3. **Given** um visitante primeira-vez com `Accept-Language: pt-PT` ou qualquer idioma não suportado, **When** abre a Home, **Then** a página carrega em português (fallback).
4. **Given** um visitante já em EN, **When** clica no seletor e escolhe FR, **Then** todas as páginas públicas mostram FR e a escolha persiste na sessão e após fechar/reabrir o navegador.
5. **Given** um visitante em `/en/sobre`, **When** troca para FR via seletor, **Then** navega para `/fr/sobre` (mesma página no novo idioma) — não volta à Home.
6. **Given** um visitante em FR na Home, **When** navega para Sobre, Profissão, Contactos, Notícias, Galeria, Publicações, Eventos Públicos, Benefícios, Plataforma, Validador, Login, Criar Conta, Recuperar Palavra-passe, Redefinir Palavra-passe, Configurar Conta, Notícia (detalhe), **Then** todas apresentam interface e cópia em FR.

---

### User Story 2 — Traduções refletem o significado, tom e vocabulário da fonte PT (Prioridade: P1)

O conteúdo em EN e FR não pode ser tradução mecânica: mantém o tom institucional/factual do site (memory: [[public-site-knowledge-base]]), respeita PT-PT europeu como origem, e preserva os **termos de domínio** que não têm equivalente limpo (nomes próprios da associação, «CV-CAR», «ACCTA», «Portal», nomes de eventos, títulos de leis). Os textos legais/institucionais (ex.: cabeçalho da Missão, descrição da profissão) são revistos por quem faz a tradução, não gerados automaticamente sem verificação.

**Why this priority**: uma tradução má é pior do que ausência de tradução — projeta amadorismo perante parceiros internacionais.

**Independent Test**: comparar lado-a-lado um bloco de texto na Home em PT/EN/FR e confirmar que (i) preserva o significado, (ii) preserva termos próprios, (iii) soa natural (não literal).

**Acceptance Scenarios**:

1. **Given** o texto PT «A ACCTA é a associação profissional dos controladores de tráfego aéreo de Cabo Verde», **When** consulto a versão EN, **Then** aparece uma tradução profissional (ex.: «ACCTA is the professional association of Cape Verde's air traffic controllers») que **mantém** «ACCTA» como sigla e «Cape Verde» como topónimo oficial em inglês.
2. **Given** a página Profissão em PT com o marco «CV-CAR 2.3/2026», **When** consulto FR, **Then** o marco surge como «CV-CAR 2.3/2026» inalterado (regulamento próprio; não se traduz o código).
3. **Given** o rodapé com o slogan/tagline da marca, **When** consulto EN/FR, **Then** o slogan tem tradução aprovada (não deixa em PT nem inventa).

---

### User Story 3 — Seletor de idioma é descoberto facilmente e não confunde (Prioridade: P2)

O seletor de idioma está visível em todas as páginas públicas, no mesmo sítio (cabeçalho, junto aos links de navegação/login), usando **rótulos nativos** («Português», «English», «Français») em vez de bandeiras (bandeiras são ambíguas — a bandeira do Reino Unido não representa todos os anglófonos). O seletor mostra claramente qual o idioma ativo e é acessível por teclado (foco visível, aria-labels).

**Why this priority**: uma vez que a máquina traduz certo, a UX do seletor é o que decide se as pessoas o usam.

**Independent Test**: percorrer 5 páginas públicas com Tab e confirmar (i) que o seletor é focável, (ii) que anuncia o idioma ativo, (iii) que trocar por teclado funciona.

**Acceptance Scenarios**:

1. **Given** qualquer página pública, **When** olho para o cabeçalho, **Then** vejo um seletor de idioma consistente com rótulos «Português / English / Français».
2. **Given** navegação por teclado, **When** Tab chega ao seletor, **Then** foco visível surge e Enter/Espaço abre o menu.
3. **Given** o seletor aberto, **When** um leitor de ecrã lê o item ativo, **Then** ouve-se claramente «Português, ativo» / «English, active» / «Français, actif».

---

### User Story 4 — SEO: cada idioma é indexável e partilhável (Prioridade: P2)

Cada página pública tem uma URL própria por idioma via prefixo de locale (`/sobre`, `/en/sobre`, `/fr/sobre` — slugs PT mantidos em todos os prefixos, clarify Q1) com marcações `hreflang` corretas apontando para as outras variantes. Partilhar um link em EN abre a página em EN mesmo para um utilizador com PT persistido. O `<title>` e `<meta description>` refletem o idioma da página.

**Why this priority**: sem URLs por idioma o site não é descoberto por motores de busca internacionais — o valor da tradução perde metade.

**Independent Test**: partilhar por WhatsApp um link `/en/sobre`; abrir num telefone com PT persistido; confirmar que a página abre em EN.

**Acceptance Scenarios**:

1. **Given** a página Sobre em EN (`/en/sobre`), **When** vejo o HTML, **Then** existem `<link rel="alternate" hreflang="pt-PT" href="/sobre">`, `hreflang="en" href="/en/sobre"` e `hreflang="fr" href="/fr/sobre"` + `x-default` a apontar para `/sobre`.
2. **Given** um link partilhado `/fr/contactos`, **When** abro num navegador com preferência PT, **Then** a página abre em FR (URL prevalece sobre preferência guardada).
3. **Given** qualquer página traduzida, **When** inspecciono `<title>` e `<meta name="description">`, **Then** ambos estão no idioma da página.

---

### User Story 5 — Emails, PDFs e conteúdos dinâmicos ficam em PT (limite explícito de âmbito) (Prioridade: P3)

Emails transacionais (convite, reset, comunicados), PDFs gerados (carteira de quotas, relatórios, atas), notificações in-app, mensagens de erro do backend (HTTPException `detail`), e conteúdos administrados via backoffice (notícias, publicações, «Sobre» corpos sociais, artigos da Central de Ajuda, comunicados, mural, brand strings) **permanecem em PT**. Um visitante em EN/FR que preenche o formulário público de recuperação de palavra-passe recebe o email em PT (v1). Fica explicitamente **fora do âmbito** desta feature.

**Why this priority**: define o **teto de scope** que impede a feature de virar um projeto de 6 meses.

**Independent Test**: em EN, no formulário «Recuperar Palavra-passe», submeter e receber o email → confirmar que o email chega em PT com nota explícita/aceitação implícita.

**Acceptance Scenarios**:

1. **Given** um visitante em FR na página «Criar Conta», **When** completa o formulário e submete, **Then** o convite/boas-vindas por email chega em PT.
2. **Given** um visitante em EN em «Notícias», **When** entra no detalhe de uma notícia, **Then** o **shell** da página (menu, cabeçalho, rodapé, botões) está em EN, aparece o aviso «This content is in Portuguese» num banner discreto acima do corpo, e o **corpo** da notícia (título e conteúdo escritos pelo admin) fica no idioma em que foi publicado (PT, por regra).
3. **Given** um visitante em EN, **When** falha um pedido e vê uma mensagem de erro do backend, **Then** a mensagem pode aparecer em PT (a tradução das mensagens do backend é out-of-scope v1).

---

### Edge Cases

- **URL antiga sem prefixo de idioma partilhada por terceiros** (`/sobre` bookmarked antes desta release): deve continuar a funcionar; abre no idioma persistido, ou PT se não houver persistência.
- **Idioma persistido para EN mas página em causa não traduzida** (imagina uma notícia interna com corpo só em PT): shell em EN, aviso ligeiro «Content in Portuguese» acima do corpo — a página não parte.
- **Formulário submetido com validação a falhar**: mensagens de validação inline (frontend) traduzem-se; mensagens do backend (`HTTPException.detail`) mantêm-se em PT — o campo aceita esse mismatch v1.
- **Utilizador autenticado que chega a uma página pública** (ex.: `/plataforma`): a área pública mostra o idioma escolhido; ao entrar em `/dashboard` o idioma da app volta a ser PT (área privada é PT-only).
- **Motor de busca (Googlebot) sem cookie/localStorage**: cada URL serve o idioma que o seu prefixo indica (`/`→PT, `/en/…`→EN, `/fr/…`→FR); sem cookies em jogo, é o prefixo que decide.
- **Idioma persistido mas eliminado localStorage** (janela anónima ou limpar dados): volta à detecção `Accept-Language`.
- **RTL/right-to-left**: não aplicável (EN, FR e PT são LTR).
- **Formatação de números/datas**: números e datas nas páginas públicas são raros (é um site de conteúdo) mas quando existem (ex.: datas de notícias) devem seguir a convenção do idioma («14 de julho de 2026» / «July 14, 2026» / «14 juillet 2026»).
- **Rota inexistente sob `/en/…` ou `/fr/…`**: resolve para 404 traduzida no locale (FR-019a) — utilizador vê a 404 no idioma que estava a usar, com ligação para `/{locale}/`.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Âmbito & Conteúdo

- **FR-001**: O site DEVE oferecer 3 idiomas para a **área pública**: Português (fonte, canónica), Inglês, Francês.
- **FR-002**: A **área privada** (rotas atrás de `PrivateLayout`) DEVE permanecer exclusivamente em PT nesta release — sem seletor de idioma dentro do portal do sócio.
- **FR-003**: As **16 páginas públicas** DEVEM ser totalmente traduzidas: Home, Sobre, Profissão, Plataforma, Notícias (lista + detalhe), Galeria, Publicações Público, Eventos Público, Benefícios Público, Contactos, Validador, Login, Criar Conta, Recuperar Palavra-passe, Redefinir Palavra-passe, Configurar Conta.
- **FR-004**: Todos os elementos do `PublicLayout` — cabeçalho, navegação pública, rodapé, links legais, botões — DEVEM ser traduzidos.
- **FR-005**: **Conteúdos dinâmicos** (corpos de notícias, publicações, comunicados, galerias, brand strings, corpos sociais na página Sobre, artigos da Central de Ajuda) DEVEM permanecer no idioma em que foram criados (PT, por regra) nesta release. Apenas o **shell** (envolvente) traduz.
- **FR-005a**: Em páginas de conteúdo dinâmico (notícia detalhe, publicação detalhe, comunicado, artigo da Central de Ajuda, secção corpos sociais da página Sobre, descrição de álbum) com shell em EN ou FR, o sistema DEVE mostrar um **aviso discreto acima do corpo** com o texto correspondente: EN «This content is in Portuguese», FR «Ce contenu est en portugais». O aviso é uma regra **por rota**, não depende de detecção do idioma do conteúdo. Estilo: fundo cinza claro, texto pequeno, não bloqueia a leitura — clarify 2026-07-14.
- **FR-006**: **Emails transacionais, PDFs, notificações e mensagens de erro do backend** DEVEM permanecer em PT nesta release (STOP de scope explícito).
- **FR-007**: Páginas legais (Termos, Privacidade se existirem, avisos de cookies) **NÃO** são traduzidas nesta release (Q2 = A). Ficam em PT; se um visitante em EN/FR aceder, a página abre em PT com aviso ligeiro «Content in Portuguese» acima.

#### Seleção & Persistência

- **FR-008**: Na primeira visita, o sistema DEVE detetar o idioma preferido do visitante via cabeçalho `Accept-Language` do navegador (Q3 = A).
- **FR-009**: Se o idioma detetado não for PT/EN/FR, o sistema DEVE usar **PT como fallback**.
- **FR-010**: A escolha do visitante DEVE persistir no browser (localStorage) por, no mínimo, 12 meses ou até o visitante limpar dados.
- **FR-011**: O seletor de idioma DEVE estar disponível em **todas** as páginas públicas, na mesma posição do cabeçalho.
- **FR-012**: O seletor DEVE mostrar **rótulos nativos** («Português», «English», «Français»), **não bandeiras**.
- **FR-013**: O seletor DEVE indicar claramente o idioma ativo (visualmente + `aria-current`).
- **FR-014**: O seletor DEVE ser acessível por teclado e leitor de ecrã (foco visível, `aria-label`, item ativo anunciado).

#### URL & SEO

- **FR-015**: Cada página pública DEVE ter uma URL própria por idioma via **prefixo de locale** (D1): PT em `/…` (sem prefixo, canónico), EN em `/en/…`, FR em `/fr/…`. **Os slugs mantêm-se em PT** em todos os prefixos (esclarecimento 2026-07-14): ex. `/sobre`, `/en/sobre`, `/fr/sobre`. Não há tradução de path segments nesta release.
- **FR-016**: Cada página pública traduzida DEVE incluir marcações `<link rel="alternate" hreflang="…">` para as três variantes (pt-PT, en, fr) + `x-default` apontando para PT.
- **FR-017**: `<title>` e `<meta name="description">` de cada página DEVEM refletir o idioma da página.
- **FR-018**: A URL partilhada de uma variante linguística DEVE prevalecer sobre o idioma persistido (partilhar `/en/sobre` abre EN mesmo para PT persistido).
- **FR-018a**: Quando o utilizador troca de idioma via seletor, o sistema DEVE **preservar a página atual** permutando apenas o prefixo de locale (ex.: `/en/sobre` → `/fr/sobre`). Se a rota-alvo não existir na locale de destino (não deve ocorrer na v1 porque o shell traduz todas as 16 páginas), fallback para `/{locale}/` (Home) — clarify 2026-07-14.
- **FR-019**: URLs pré-existentes sem prefixo (ex.: `/sobre`) DEVEM continuar a funcionar (compatibilidade retroativa) — abrem no idioma persistido / detetado / PT.
- **FR-019a**: Rota inexistente sob um prefixo de locale (`/en/rota-x`, `/fr/typo`) DEVE resolver para uma **página 404 traduzida no locale**: shell no idioma ativo, título «Page not found» (EN) / «Page introuvable» (FR), ligação para `/{locale}/` (Home) e seletor de idioma visível. Rota inexistente sem prefixo (`/rota-x`) resolve para a 404 canónica em PT — clarify 2026-07-14.

#### Qualidade da Tradução

- **FR-020**: As traduções EN e FR DEVEM ser revistas por humanos (interna ou por serviço profissional) antes do go-live; **não é aceitável** publicar tradução automática sem revisão.
- **FR-021**: Termos próprios da associação e códigos regulamentares (ACCTA, CV-CAR, IFATCA, ICAO) NÃO devem ser traduzidos.
- **FR-022**: A tabela «tone-of-voice» PT (factual, institucional, sem cobrança/marketing agressivo — ver memory `public-site-knowledge-base`) DEVE ser mantida em EN e FR.
- **FR-023**: Datas e números que aparecem no conteúdo público DEVEM seguir a convenção local do idioma exibido.

#### Manutenção & Governança de Traduções

- **FR-024**: Quando um texto PT de uma página pública mudar, deve haver um mecanismo claro para **sinalizar que a versão EN/FR está desatualizada** (ex.: um marcador `pending_translation` no ficheiro de traduções, revisão manual, ou ferramenta que compare chaves).
- **FR-025**: Quando uma **chave** de tradução for adicionada, o sistema DEVE ter fallback para PT enquanto EN/FR estão em falta (a página não parte, apenas mostra o PT com um aviso interno em ambiente dev).
- **FR-026**: A **fonte de verdade** das strings é PT (o texto PT canónico); EN e FR são projeções.

#### Acessibilidade

- **FR-027**: O atributo `<html lang="…">` DEVE mudar dinamicamente para `pt-PT`, `en` ou `fr` conforme o idioma ativo, para leitores de ecrã e ferramentas de acessibilidade.
- **FR-028**: Nenhum texto crítico de UI pode estar hardcoded numa imagem ou SVG que não possa ser traduzido.

---

## Key Entities *(include if feature involves data)*

- **Locale**: identificador do idioma (`pt-PT`, `en`, `fr`); PT é o canónico e default.
- **TranslationKey**: chave estável (ex.: `home.hero.title`) que mapeia para 3 strings — uma por locale. As chaves são estruturadas por página/secção.
- **TranslationBundle**: coleção de todas as chaves de um idioma; carregada pelo frontend em runtime (ou embutida em build).
- **PublicRoute**: uma rota pública mapeada para uma variante por idioma (ex.: `home` → `/`, `/en`, `/fr`).
- **LanguagePreference**: a escolha do visitante, persistida no browser (localStorage), com prevalência sobre `Accept-Language`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das 16 páginas públicas apresentam shell (navegação, cabeçalho, rodapé, botões) e cópia principal traduzidos em PT, EN e FR — validado por inspeção manual + snapshot automatizado das chaves esperadas.
- **SC-002**: Um visitante primeira-vez com `Accept-Language: fr` chega à Home e vê **100% do shell** e **95%+ da cópia principal** em francês, em menos de 3 segundos (percepcionalmente ao mesmo tempo que a página carrega, sem «flash» em PT).
- **SC-003**: O seletor de idioma é descoberto em ≤ 2 segundos por 80%+ de utilizadores em teste de usabilidade (5 utilizadores, cronometrando «encontre como mudar para inglês»).
- **SC-004**: Cada página traduzida tem marcações `hreflang` corretas para todas as variantes; validador do Google Search Console reporta 0 erros de idioma alternativo.
- **SC-005**: Um visitante que escolhe EN e volta à página 24 h depois vê EN sem re-selecionar (persistência ≥ 24 h em ≥ 99% dos casos, exceto se limpar dados).
- **SC-006**: 0 (zero) strings de UI em PT visíveis quando o idioma ativo é EN ou FR, exceto (i) conteúdo dinâmico administrado (notícias, publicações, comunicados) e (ii) mensagens do backend — ambos declarados explicitamente fora de âmbito.
- **SC-007**: Nenhuma página parte, engasga ou fica em branco quando uma chave EN/FR está em falta (fallback para PT + aviso em dev).
- **SC-008**: 0 regressões na área privada — todas as rotas privadas continuam PT-only e não mostram seletor de idioma.

---

## Assumptions

- **A-01**: O público-alvo do site público em EN/FR é qualitativo (parceiros institucionais e diáspora), não escala massiva de tráfego; não é necessário CDN dedicado por idioma.
- **A-02**: PT é sempre a fonte canónica; qualquer alteração de conteúdo começa em PT e propaga para EN/FR num segundo passo (não simultâneo).
- **A-03**: Textos oficiais da associação (nomes, siglas, códigos regulamentares) não se traduzem.
- **A-04**: **Emenda constitucional MINOR v1.1.0 → v1.2.0** é pré-requisito: restringir Princípio IV a áreas autenticadas.
- **A-05**: A tradução profissional inicial (PT→EN, PT→FR) das strings **estáticas** é um **entregável fora do trabalho de engenharia** (interna, tradutor humano ou serviço externo revisto). A engenharia entrega a infraestrutura + integração + placeholders «TODO EN/FR» prontos a preencher; a fase de aceitação inclui as strings reais.
- **A-06**: Não há suporte a mais idiomas nesta release; adicionar (ex.: espanhol) fica para spec futura reutilizando a mesma infraestrutura.
- **A-07**: Não se altera o formato de armazenamento de conteúdo dinâmico (notícias/publicações) para multi-idioma nesta release — é out-of-scope.
- **A-08**: A biblioteca de i18n a usar no frontend é uma decisão do plan (`speckit-plan`), não deste spec; assumimos uma solução standard React + i18next-like ou equivalente já usada na indústria.
- **A-09**: A URL do backend (`api.controlador.cv`) e as suas respostas continuam em PT; o frontend público pode adaptar rótulos genéricos, mas conteúdo dinâmico não é retraduzido.

---

## Dependencies & Out-of-Scope

### Dependencies

- **D-01**: Emenda MINOR à constituição (v1.1.0 → v1.2.0) — Princípio IV.
- **D-02**: Textos traduzidos revistos (interno ou externo) prontos antes do go-live.
- **D-03**: `frontend-design` skill — nenhum novo token de cor/tipografia é introduzido; a feature reutiliza o sistema atual.

### Out-of-Scope (v1 explícito)

- Tradução da **área privada** (dashboard/carteira/financeiro/assembleias/etc.).
- Tradução de **emails transacionais** (Resend templates).
- Tradução de **PDFs gerados** (carteira de quotas, atas, relatórios).
- Tradução de **notificações in-app** (schedule).
- Tradução de **mensagens de erro do backend** (`HTTPException.detail`).
- Tradução de **conteúdo dinâmico** administrado (notícias, publicações, comunicados, mural, corpos sociais, artigos da Central de Ajuda, brand strings).
- Ferramenta de gestão de traduções (TMS) — v1 usa ficheiros na fonte.
- Suporte a mais idiomas além de PT/EN/FR.
- Traduções regionais (ex.: EN-GB vs EN-US, FR-FR vs FR-CA) — cada idioma tem uma variante única.

---

## Decisões do Dono *(3 gates fechados — 2026-07-14)*

Registo das respostas do dono às perguntas críticas antes do planeamento. Recomendações do assistente aceites.

### D1 — Modelo de URL por idioma → **A: prefixo `/en/`, `/fr/` + `hreflang`**

PT em `/…` (canónico, sem prefixo), EN em `/en/…`, FR em `/fr/…`. Cada URL é indexável pelo Google e partilhável por locale. **Sub-decisão de slugs fechada em 2026-07-14 (clarify Q1 = B): slugs mantêm-se em PT em todos os prefixos** (`/sobre`, `/en/sobre`, `/fr/sobre`). Uma só estrutura de URL a manter; SEO por idioma via `hreflang` + `<html lang>` + prefixo.

### D2 — Âmbito de conteúdo → **A: só shell + cópia estática das 16 páginas**

Conteúdo dinâmico (notícias, publicações, comunicados, corpos sociais, artigos da Central de Ajuda, brand strings) e páginas legais (Termos, Privacidade) mantêm-se em PT. Emails, PDFs, notificações e mensagens do backend também PT. Aviso ligeiro «Content in Portuguese» acima nos blocos onde a envolvente EN/FR mostra corpo em PT.

### D3 — Detecção de idioma na primeira visita → **A: `Accept-Language` + fallback PT**

Detecção automática via cabeçalho do navegador (PT/EN/FR reconhecidos, restantes → PT). Seletor sempre visível para override. Escolha manual persiste (localStorage, ≥ 12 meses).

---

**Status**: Ready for `/speckit-plan`.
