# Research — Revisão do Ranking e do Perfil

Fase 0. Resolve as incógnitas técnicas e regista decisões. Tudo frontend.

---

## D1 — Causa raiz do "TV antiga sem sinal" no telemóvel (US1)

**Decision**: Tratar como **transbordo horizontal / layout partido** em larguras
estreitas e corrigir na origem; a causa exata é confirmada por reprodução em
navegador (Princípio VII) antes de fechar.

**Suspeitos a confirmar na reprodução** (≈360–414px, em `RankingPage.js`):
- Barra de ações do cabeçalho (`flex … flex-wrap`, linha ~241): para gestores tem
  PeriodToggle + 3 botões; pode amontoar/empurrar largura. Confirmar wrap correto.
- Tabela em `overflow-x-auto` (linha ~400): com `padding` `sm:px-6` e 3 colunas, o
  conteúdo deve caber; validar que nomes/cargos longos não forçam scroll feio que
  o utilizador lê como "quebrado".
- Pódio `grid-cols-1 sm:grid-cols-3` com `sm:-mt-2` no 1.º: em mobile é coluna
  única — validar que o `-mt` não vaza.

**Rationale**: O sintoma ("sem sinal") descreve distorção/garble visual, quase
sempre causado por um elemento que ultrapassa a viewport e empurra o resto.
Corrigir o elemento culpado (constrangimento responsivo correto) é a correção de
raiz; nunca mascarar com `overflow-hidden` no contentor de topo.

**Alternatives considered**: Adicionar `overflow-x-hidden` global — rejeitado
(esconde o sintoma, parte o scroll legítimo da tabela). Reescrever a página —
rejeitado (excessivo; o problema é responsividade pontual).

**Validação**: SC-001 — 100% dos blocos contidos a 360/390/414px, sem corte
indevido nem sobreposição; desktop/tablet sem regressão (SC-006).

---

## D2 — Distinção 1.º / 2.º / 3.º lugar (US2) — **decisão de design**

**Decision (default, compatível com a paleta)**: distinguir os três primeiros por
uma **escala de ênfase dentro do sistema** + **ordinal sempre visível** + ícone:
- **1.º** — ícone **Coroa**, acento **Carmesim `#C7202F`** (o acento único), com o
  realce de superfície já existente (`ring`/tint `#FBEAEC`).
- **2.º** — ícone **Medalha**, **Grafite `#3A3A3A`** (neutro forte).
- **3.º** — ícone **Award**, **muted `#6B7280`** (neutro mais leve).
- **4.º+** — número ordinal mono (como hoje).
- Cada um dos três usa um **ícone de forma distinta** (Coroa/Medalha/Award) **além**
  do tom — a distinção 2.º vs 3.º não depende só da cor (FR-005, daltonismo) — e um
  rótulo `sr-only` "N.º lugar" acompanha o ícone para leitores de ecrã.

**Rationale**: Cria uma hierarquia de três degraus percetível ao relance
(Carmesim → escuro → claro) sem sair da paleta neutral-led nem usar Carmesim como
nada além de acento. Cumpre Princípio V (NON-NEGOTIABLE) e a skill `frontend-design`
sem a editar ([[no-autonomous-skill-edits]]).

**Alternatives considered**:
- **Ouro/prata/bronze literais** — o que o dono pediu textualmente. Rejeitado por
  defeito: introduz 3 cores fora do sistema (skill proíbe "qualquer cor fora deste
  sistema") → viola Princípio V. **Fica como decisão de override do dono (ver
  abaixo).**
- Só tamanho/forma de ícone sem variação de tom — rejeitado: distinção fraca, é
  exatamente a queixa atual (2.º e 3.º indistintos).

> **DECISÃO DO DONO (D2) — RESOLVIDA (2026-06-26)**: usar o **default
> Carmesim → Grafite → muted, sem metálicos**. Ouro/prata/bronze literais ficam
> **fora de âmbito** (não se estende a paleta nem se edita a skill de design). É
> esta a decisão final para FR-003.

**Validação**: SC-002 — identificar 1/2/3 ao relance sem ler números.

---

## D3 — Fotos dos sócios no ranking (US3)

**Decision**: Renderizar `<UserAvatar name={e.member_name} photoUrl={e.photo_url} />`
em cada entrada do pódio e da tabela (RankingPage) e no widget `RankingTopN`.
Tamanho `xs`/`sm` na tabela/lista; maior no pódio.

**Rationale**: `photo_url` **já vem** em cada entrada de `leaderboard` (denormalizado
no rebuild, `backend/ranking.py:270`; a projeção do endpoint só exclui `breakdown`).
`UserAvatar` já é a fonte única de avatar com fallback de iniciais (Carmesim sobre
branco) e já aplica `mediaUrl()` — resolvendo o risco conhecido de imagens de
`/uploads` partirem em prod ([[uploaded-media-needs-mediaurl]]). Zero backend, zero
deps, reutilização total. Opt-out continua filtrado no servidor (a foto não reexpõe
ninguém — FR-008).

**Alternatives considered**: Join de `photo_url` no read do endpoint — rejeitado,
desnecessário (já está no payload). Nova caixa de iniciais — rejeitado, duplicaria
`UserAvatar`.

**Validação**: SC-003 — 100% das entradas com foto ou iniciais; zero imagens
quebradas (o `AvatarFallback` do Radix trata 404/ausência/loading).

---

## D4 — Painel de notificações cortado à esquerda (US4)

**Decision**: Garantir que o painel respeita ambas as margens da viewport em
ecrãs estreitos. O painel está `absolute right-0 … w-[400px] max-w-[90vw]`
(NotificationBell.js ~72). Em mobile, ancorado a `right-0` junto ao bordo direito,
`max-w-[90vw]` ainda pode encostar/cortar à esquerda conforme a posição do sino.
Corrigir com um constrangimento que assegure **margem mínima de 16px em cada lado**
(largura/posição responsiva que nunca ultrapasse a viewport), validado em navegador.

**Margem mínima (decisão A1)**: **16px** por bordo no telemóvel — alinha com o
espaçamento base do sistema (unidade de 8px × 2) e torna o SC-004 objetivamente
testável (passa/falha).

**Rationale**: Correção de raiz no posicionamento do painel, sem mexer no padrão
de montagem/animação existente (delayed-unmount) nem no backdrop.

**Alternatives considered**: Mover para um `Dialog`/`Sheet` shadcn em mobile —
rejeitado por agora (excessivo; o padrão atual funciona, falta só conter as margens).

**Validação**: SC-004 — margem ≥ mínima em ambos os bordos a 360/390/414px; zero
corte. Desktop mantém alinhamento ao sino (SC-006).

---

## D5 — Perfil: editável vs. gerido pela associação (US5)

**Decision**: A revisão é de **clareza/UX**, não de novos campos. O `EditForm` já
expõe **todos** os campos de autosserviço (e o backend já os aceita —
`_EditableProfileFields`). Ação: no `DetailsGrid`, marcar visualmente os campos
geridos pela associação (Email, N.º Sócio, Cargo, Função, Estado, Categoria, Data
de Admissão) como **não-editáveis**, com indicação de que a alteração é feita pela
administração; e tornar óbvia a fronteira entre os dois grupos (FR-012/FR-013).
Email permanece admin-only (**Decisão Q1**).

**Rationale**: O "não consigo editar tudo" é percepção: faltava sinalizar o que é
identidade/governança (imutável por design — `member_id` imutável, `cargo` via
`/admin/cargos`, email = identidade). Adicionar campos editáveis violaria as regras
de identidade (Princípio III / governança). A correção certa é comunicação visual.

**Alternatives considered**: Tornar email/identidade editáveis — rejeitado (Q1 +
regras de identidade). Reescrever a página de Perfil — rejeitado (já cobre os
campos; é polish, não reconstrução).

**Validação**: SC-005 — sócio edita e grava qualquer campo de autosserviço; campos
não-editáveis rotulados como tal.

---

## Resumo de impacto

- **Backend**: nenhum. (Sem Via B; o delta não toca `backend/`.)
- **Frontend**: `RankingPage.js`, `dashboard/RankingTopN.js`, `NotificationBell.js`,
  `perfil/DetailsGrid.js` (e talvez `perfil/PerfilPage.js`).
- **Deps**: zero novas.
- **Dados/Modelos/API**: sem alterações.
- **Decisão aberta**: D2-override (metálicos reais) — aguarda o dono; default já
  funciona e é mergeável.
