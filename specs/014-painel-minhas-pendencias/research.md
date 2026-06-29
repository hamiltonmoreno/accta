# Research: Painel «As minhas pendências»

Fase 0. As clarificações de scope foram resolvidas no `spec.md`. Aqui resolvem-se as
incógnitas **técnicas** (RBAC dos reads, quem propõe Atos, filtros por-utilizador) que
determinam se a feature é frontend-only ou precisa de backend.

## Decisão 1 — Atos: NÃO precisa de filtro novo nem de RBAC novo (quem propõe é Direção/admin)

- **Achado**: `routes/atos.py` — `_require_create` exige `role == "admin" or is_direcao(user)`
  (linha ~ "Apenas a Direccao ou admin pode criar actos"); `_require_view` exige
  `can_view_finances(user) or is_direcao(user)`. `list_atos` (`GET /atos`) aceita `status`,
  `tipo`, `pendentes_para_mim` — **não** tem filtro `created_by`.
- **Conclusão**: o **proponente de um Ato é sempre admin/Direção** (um sócio comum nem cria
  Atos, nem os pode listar — `GET /atos` → 403). Logo:
  - "**Atos que propus**" = `GET /atos?status=pendente` filtrado no cliente por
    `created_by == eu` — disponível a quem pode chamar (Direção/admin), que é exatamente quem
    pode ter proposto. **Sem filtro novo no backend.**
  - "**Atos à minha assinatura**" = `GET /atos?pendentes_para_mim=true` (já existe, já usado
    na CoAprovacoesPage). **Sem mudança.**
- **Decisão**: **zero backend** para os Atos. O painel só mostra as secções de Atos a quem é
  **Direção/admin** (o frontend condiciona a chamada ao papel — evita o 403 ao sócio comum).
- **Alternativa rejeitada**: adicionar `?proposto_por_mim=true` ao backend — desnecessário
  (os únicos proponentes já podem listar) e tornaria a release Via B sem ganho.

## Decisão 2 — Votações e Eventos: reads existentes + filtro no cliente (acessíveis ao sócio)

- **Achado** (do mapeamento): `GET /polls` devolve, por votação, `has_voted` (por-utilizador)
  e `status`; `GET /events/upcoming` devolve `attendees[]`. Ambos são **member-facing**
  (um sócio ativo pode chamá-los).
- **Decisão**:
  - Votações por votar = `polls.filter(p => p.status === 'aberta' && !p.has_voted)`, **e só**
    se o utilizador for **membro votante** (FR-007 — não mostrar votações a quem não pode
    votar; a elegibilidade segue `is_voting_member`, validada no servidor no POST do voto).
  - Eventos por confirmar = `events.filter(e => !e.attendees?.includes(eu) && futuro)`.
- **Rationale**: filtragem trivial no cliente; sem endpoint novo; consistente com o que o
  Dashboard já consome.

## Decisão 3 — Excluir eleições e deliberações secretas (segredo do voto)

- **Achado**: `eleicao_ballots` **não tem `user_id`** (recibo HMAC em `eleicao_voter_receipts`,
  não reversível); deliberações em modo secreto idem. É **impossível** ao servidor dizer "este
  utilizador ainda não votou".
- **Decisão**: estes tipos **não** entram no painel (FR-008/SC-004). Não se inventa forma de
  contornar o segredo. (Uma referência neutra "votação a decorrer" poderia viver noutro sítio,
  fora do âmbito desta feature.)

## Decisão 4 — Dados no cliente via TanStack Query (sem agregador)

- **Decisão**: cada secção usa `useQuery` sobre o read existente (chaves em
  `lib/queryClient.js`), correndo em paralelo; a derivação "falta-me agir" é `select`/filtro
  no cliente. **Sem** endpoint agregador `/pendencias/minhas` (decisão do dono).
- **Rationale**: zero backend ⇒ entrega só pela Vercel (sem Via B); reaproveita caching/
  invalidations já existentes; a lógica de "pendente para mim" é leve e local.
- **Alternativa rejeitada**: agregador backend — tocaria `backend/` (Via B) e duplicaria a
  filtragem que já é trivial no cliente.

## Implicação de âmbito (capturada também no plan.md)

Como só Direção/admin propõem/veem Atos, **o painel é role-aware**: sócio comum vê
votações+eventos; Direção/admin vê adicionalmente as 2 secções de Atos. Não muda a intenção
do dono nem exige backend.
