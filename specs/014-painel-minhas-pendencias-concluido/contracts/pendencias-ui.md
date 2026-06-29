# Contrato de UI: página «As minhas pendências»

Feature **frontend-only**. Não há contrato de API novo — o "contrato" é o comportamento da
página e os reads existentes que a alimentam.

## Rota e navegação

- Nova rota **`/pendencias`** (lazy, dentro de `ProtectedRoute` — qualquer sócio autenticado).
- Item de menu **"As minhas pendências"** na sidebar do sócio (`PrivateLayout.js`).
- Torna-se o **destino** das ligações dos avisos das specs 010–013 (follow-up: apontar esses
  avisos a `/pendencias` em vez de `/financeiro/co-aprovacoes` — fora do âmbito mínimo, anotar).

## Reads consumidos (existentes, via TanStack Query `useQuery`)

| Secção | Endpoint | Filtro no cliente | Condição de chamada |
|--------|----------|-------------------|---------------------|
| Atos que propus | `GET /api/atos?status=pendente` | `created_by === user.id` | só se `isDirecao(user)` / admin |
| Atos à minha assinatura | `GET /api/atos?pendentes_para_mim=true` | (servidor já filtra) | só se `isDirecao(user)` |
| Votações por votar | `GET /api/polls` | `status==='aberta' && !has_voted` | só se membro votante |
| Eventos por confirmar | `GET /api/events/upcoming` | `!attendees.includes(user.id)` | qualquer sócio ativo |

- As secções de Atos **não são pedidas** a um sócio comum (evita o 403 de `_require_view`).
- Erros de um read **não** derrubam a página: cada secção degrada isoladamente (skeleton →
  vazio/erro local), as outras secções renderizam na mesma.

## Comportamento

- Cada secção mostra um **cabeçalho com contagem** e uma lista de itens; cada item tem uma
  **ligação para agir** (ver Ato / votar / confirmar presença).
- **Estado vazio global**: se **nenhuma** secção tem itens, mostrar uma mensagem clara de
  "está tudo em dia / nada pendente" (FR-006) — não secções vazias soltas.
- **Estado vazio por secção**: uma secção sem itens **não** se mostra (evita ruído), exceto
  o estado vazio global acima.
- **Design**: skill `frontend-design` — superfícies neutras, ligações em Carmesim sobre
  branco, **uma** primária positiva (Floresta) se houver CTA, sem dark mode; ícones
  lucide-react; padrão de cartão coerente com a CoAprovacoesPage/Dashboard.
- **i18n/texto**: PT; sem linguagem de inadimplência.

## Não-objetivos

- Sem endpoint agregador novo; sem mutações no painel (as ações completam-se no ecrã de
  destino); sem eleições/deliberações-secretas; sem persistência.
