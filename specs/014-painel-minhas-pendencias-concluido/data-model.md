# Data Model: Painel «As minhas pendências»

**Sem entidade/coleção/schema novos.** A "pendência" é **derivada** em tempo de leitura do
estado de objetos existentes. Nada é persistido por esta feature.

## Conceito derivado: Pendência (apenas no cliente)

| Campo | De onde vem | Notas |
|-------|-------------|-------|
| `tipo` | secção | `ato_proposto` \| `ato_assinatura` \| `votacao` \| `evento` |
| `titulo` | objeto-fonte | descrição do Ato / título da votação / título do evento |
| `referencia` | objeto-fonte | `id` do Ato/votação/evento |
| `link_para_agir` | rota frontend | ver Ato / votar / confirmar presença |
| `meta` | objeto-fonte | ex.: antiguidade do Ato, data do evento, nº de opções |

## Fontes e regra de inclusão (derivação)

| Secção (tipo) | Fonte (read existente) | Incluído quando | Visível a |
|---------------|------------------------|-----------------|-----------|
| Atos que propus | `GET /atos?status=pendente` | `created_by == eu` | Direção/admin |
| Atos à minha assinatura | `GET /atos?pendentes_para_mim=true` | (já filtrado pelo servidor) | Direção |
| Votações por votar | `GET /polls` | `status=='aberta' && !has_voted` **e** sou membro votante | Sócio votante |
| Eventos por confirmar | `GET /events/upcoming` | `!attendees.includes(eu) && futuro` | Qualquer sócio ativo |

## Invariantes

- **Derivado, não armazenado**: reabrir o painel reflete sempre o estado atual; um item
  resolvido (votado/confirmado/Ato decidido/evento passado) **deixa** de aparecer (FR-005).
- **Segredo do voto**: eleições e deliberações secretas **nunca** produzem pendências
  (FR-008/SC-004) — não há `user_id` nos ballots.
- **Role-aware**: as secções de Atos só são pedidas/mostradas a quem é Direção/admin (um
  sócio comum levaria 403 em `GET /atos`; o frontend nem chama).
- **Elegibilidade**: votações só contam como pendência para **membros votantes** (FR-007).
- **Sem escrita**: o painel só lê; nenhuma mutação, nenhum campo novo, nenhum audit.
