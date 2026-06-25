# Phase 0 — Research: Landing page da plataforma

Sem `NEEDS CLARIFICATION` pendentes (resolvidos com o dono antes do plano). Esta fase consolida as decisões técnicas e o levantamento da base de código.

## Decisão 1 — Onde vive a página e como é registada

- **Decision**: Nova página `frontend/src/pages/public/PlataformaPage.js` (named export `PlataformaPage`), registada em `frontend/src/App.js` como rota **lazy** envolvida por `<PublicLayout>`, no path `/plataforma`.
- **Rationale**: replica exatamente o padrão das restantes páginas públicas (`SobrePage`, `ProfissaoPage`, etc.). O `PublicLayout` já fornece cabeçalho + rodapé partilhados, garantindo coerência e o ponto de entrada do link no rodapé.
- **Alternatives considered**:
  - *Import eager* (como `HomePage`): rejeitado — só a HomePage é eager por ser o first paint; uma landing secundária deve ser lazy (FR-010).
  - *Rota fora do `PublicLayout`* (como `/login`): rejeitado — perderia cabeçalho/rodapé e o contexto de marca.

## Decisão 2 — Local e estilo do link discreto no rodapé

- **Decision**: Adicionar o link na **barra inferior** do rodapé (`PublicLayout.js`, junto ao copyright/"Política de Privacidade"), com estilo discreto (`text-white/50 hover:text-white`, tamanho `text-xs`/`text-sm`). Label: **"A plataforma"**.
- **Rationale**: "discreto" (pedido explícito) ⇒ menor destaque visual; a barra inferior já agrega links utilitários de baixa proeminência (Política de Privacidade). Não compete com "Links Rápidos"/"Área Reservada".
- **Alternatives considered**:
  - *Coluna "Links Rápidos"*: rejeitado como primeira opção — esses links têm peso de navegação primária; menos "discreto".
  - *Nova coluna dedicada*: rejeitado — chamaria demasiada atenção para um link que deve ser sóbrio.

## Decisão 3 — Estrutura visual da página

- **Decision**: Espelhar `SobrePage.js`: `PageBanner` no topo (badge + título + subtítulo) seguido de 3–4 secções alternadas (`bg-gray-50` / `bg-white`), com grelha `lg:grid-cols-2` e cartões `card-technical card-hover` para a lista de capacidades/módulos. Animação via `.animate-fade-up`. Ícones de `lucide-react`.
- **Rationale**: reutiliza utilitários e ritmo de secções já validados em produção; zero novas dependências; coerência imediata de marca.
- **Alternatives considered**:
  - *Hero full-bleed estilo `HeroSection` da HomePage*: rejeitado — esse hero tem CTAs proeminentes (Floresta), o que colide com "sem CTA forte". `PageBanner` é mais sóbrio e é o padrão das páginas interiores.
  - *Componentes shadcn/ui novos*: desnecessário; os utilitários CSS existentes bastam.

## Decisão 4 — Tom, conteúdo e regras editoriais

- **Decision**: Copy factual e institucional; descrever capacidades reais do portal (sócios, quotas/finanças, transparência, eventos, votações/assembleias, comunicação). **Sem** números/estatísticas, **sem** preços, **sem** promessas comerciais, **sem** CTA forte.
- **Rationale**: a área pública é uma knowledge base com regras editoriais estritas (ver [[public-site-knowledge-base]]); o dono pediu tom informativo sem CTA forte.
- **Alternatives considered**: copy de vendas/SaaS com métricas e botão "Pedir demo" — rejeitado pelas clarificações e pela regra editorial.

## Decisão 5 — Dependências e performance

- **Decision**: **Zero** novas dependências npm. Usar Tailwind, `lucide-react`, react-router-dom já presentes. Preferir conteúdo estático (sem imagens pesadas); se for usada imagem de banner, seguir o mecanismo `PageBanner`/`mediaUrl()` existente.
- **Rationale**: instalar deps novas pendura nesta máquina ([[frontend-dep-install-hangs]]); lazy-load mantém o bundle inicial intacto.
- **Alternatives considered**: bibliotecas de animação/ilustração novas — rejeitado (custo de instalação + peso desnecessário).

## Levantamento da base de código (factos)

| Item | Localização | Nota |
|------|-------------|------|
| Rotas públicas | `frontend/src/App.js` ~L117–133 | Bloco de `<Route>` dentro de `AppRoutes()`; imports lazy ~L13–32 |
| Layout público | `frontend/src/layouts/PublicLayout.js` | Cabeçalho ~L35; rodapé ~L132–172 (grelha 4 col + barra inferior L167–170) |
| Páginas públicas | `frontend/src/pages/public/` | `SobrePage.js` é o melhor molde |
| Banner de página | `frontend/src/components/PageBanner.js` | Props `pageKey/badge/title/subtitle/icon`; altura `h-64 sm:h-72 lg:h-80` |
| Tokens de marca | `frontend/tailwind.config.js` (~L27–65) + `frontend/src/index.css` (~L39–56) | `carmesim`, `grafite`, `floresta`; utilitários `card-technical`, `card-hover`, `.animate-fade-up` |
| Helper de media | `frontend/src/utils/api.js` L10 `mediaUrl()` | Só necessário se a página usar media gerida/uploaded |
| SEO/título | `frontend/public/index.html` (título estático) | Sem `react-helmet`; `document.title` por `useEffect` é opcional |

**Conclusão**: a feature é inteiramente realizável com padrões e componentes existentes, sem backend, sem DB e sem novas dependências.
