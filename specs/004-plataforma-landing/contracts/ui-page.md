# Contrato — UI da página `PlataformaPage`

## Composição (de cima para baixo)

1. **Banner** — `<PageBanner pageKey="plataforma" badge="A plataforma" title="…" subtitle="…" icon={…} />`
   - Mantém o padrão de altura/gradiente das páginas interiores.
2. **Introdução** — secção `py-12 sm:py-20 lg:py-24`, grelha `lg:grid-cols-2 gap-16 items-center`, `.animate-fade-up`. Parágrafo factual: o que é o sistema, para que serve.
3. **Capacidades/Módulos** — secção `bg-white`/`bg-gray-50` (alternada), grelha de cartões `card-technical card-hover p-4 sm:p-6`, ≥ 5 itens (ver `data-model.md`). Cada cartão: ícone `lucide-react` em caixa `bg-grafite`, título `text-grafite`, descrição `text-gray-600`.
4. **Fecho** — secção neutra, nota institucional sóbria. **Sem** botão de ação primário proeminente.

## Regras de marca/UI (gate de revisão)

| Regra | Fonte | Verificação |
|-------|-------|-------------|
| Neutral-led (white/`#F5F5F5`, texto Grafite) | Constituição V / `frontend-design` | revisão de código |
| Carmesim só como identidade/links; **nunca** primário positivo | Constituição V | revisão de código |
| Floresta só para ação positiva pontual (aqui, idealmente nenhuma) | Constituição V | revisão de código |
| Sem dark mode | Constituição V | revisão de código |
| Só Tailwind, sem inline styles | Constituição V | `grep` por `style={{` na página = 0 |
| Open Sans (herdado do layout) | `frontend-design` | revisão de código |
| Sem CTA comercial forte | FR-005 / SC-004 | revisão visual |

## Responsividade (SC-003)

- Largura testada: **360px → 1440px**.
- Secções empilham em mobile (`grid-cols-1`), passam a `lg:grid-cols-2` em desktop.
- Sem overflow horizontal; texto legível; toques/links com área adequada.

## Acessibilidade (best-effort)

- Hierarquia de headings coerente (`h1` no banner via `PageBanner`, `h2` por secção, `h3` por cartão).
- Ícones decorativos não anunciados (ou `aria-hidden`); texto não depende só de cor.
- Contraste conforme pares permitidos pela skill `frontend-design`.

## Não-objetivos (recordatório)

- Sem formulário de contacto / lead capture.
- Sem dados dinâmicos do backend (conteúdo estático).
- Sem novas dependências npm.
