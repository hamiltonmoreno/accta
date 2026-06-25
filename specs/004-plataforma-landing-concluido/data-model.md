# Phase 1 — "Data Model": conteúdo da página

> Esta feature **não** introduz entidades de dados, tabelas, nem modelos Pydantic. Não há persistência. O "modelo" abaixo descreve apenas a **estrutura de conteúdo estático** da página (constantes no componente), para guiar a implementação.

## Estrutura de conteúdo (estática, no componente)

### `PageMeta`
| Campo | Tipo | Valor / regra |
|-------|------|---------------|
| `route` | string | `/plataforma` |
| `badge` | string (PT-PT) | ex. "A plataforma" |
| `title` | string (PT-PT) | ex. "Um sistema feito para gerir associações" |
| `subtitle` | string (PT-PT) | frase factual de enquadramento |

### `Capacidade` (lista, ≥ 5 itens — SC-002)
| Campo | Tipo | Regra |
|-------|------|-------|
| `icon` | componente `lucide-react` | ícone ilustrativo (ex. `Users`, `Wallet`, `BarChart3`, `CalendarDays`, `Vote`, `Megaphone`) |
| `title` | string (PT-PT) | nome do módulo/capacidade |
| `desc` | string (PT-PT) | descrição curta, factual, sem números/promessas |

**Conjunto inicial sugerido** (mapeado aos módulos reais do portal):
1. **Gestão de sócios** — registo, perfis, estados (`ativo`/`inativo`/`pendente`), cargos e órgãos sociais.
2. **Quotas e finanças** — quotas, jóia, transações e fluxo financeiro central.
3. **Transparência** — prestação de contas, balancetes e exercícios acessíveis aos sócios.
4. **Eventos** — divulgação, inscrições e ligação ao caixa (custos/receitas).
5. **Votações e assembleias** — deliberações, eleições com voto secreto e participação.
6. **Comunicação** — comunicados segmentados (in-app + email) e notificações em tempo real.

> A copy final deve descrever capacidades sem inventar métricas (regra editorial — [[public-site-knowledge-base]]).

### `Seccao` (estrutura da página)
| Secção | Propósito | Componente/estilo |
|--------|-----------|-------------------|
| Banner | enquadrar "o que é a plataforma" | `PageBanner` |
| Introdução | parágrafo de abertura + contexto | secção `lg:grid-cols-2`, `.animate-fade-up` |
| Capacidades | grelha de `Capacidade` | grelha de `card-technical card-hover` |
| Fecho | nota institucional sóbria | secção neutra; **sem** botão de ação proeminente |

## Validações / invariantes (de conteúdo)

- **INV-1**: Todo o texto em PT-PT (FR-006).
- **INV-2**: ≥ 5 capacidades (SC-002).
- **INV-3**: Nenhum CTA primário comercial proeminente (FR-005, SC-004).
- **INV-4**: Nenhum número/estatística não oficial nem preço (FR-009).
- **INV-5**: Apenas classes Tailwind + tokens de marca; sem inline styles, sem dark mode (FR-007).
