# Sistema de Notificações In-App — Portal ACCTA

## Visão Geral

Sistema de notificações para manter os sócios informados sobre eventos importantes da associação, com entrega **em tempo real via SSE** e *fallback* de polling.

### Componentes
1. **Backend API** — endpoints REST + stream SSE (`routes/notifications.py`)
2. **NotificationContext** — Provider React (SSE com `EventSource`, *fallback* polling 30s)
3. **NotificationBell** — Badge + dropdown no header
4. **NotificacoesPage** (`/notificacoes`) — página completa com estatísticas e filtros
5. **Broadcast admin** — enviar notificações para todos os sócios
6. **Auto-triggers** — geração automática a partir de ações no sistema

---

## Categorias de Notificação

A categoria é usada para filtros e ícones. Listadas em `GET /api/notifications/types`:

| Categoria | Exemplos de origem |
|-----------|--------------------|
| `geral` | Mensagens genéricas |
| `comunicado` | Comunicados oficiais (email + in-app) |
| `financeiro` | Transações, quotas, prestação de contas |
| `evento` | Novos eventos / inscrições |
| `projeto` | Alterações em projetos |
| `mural` | Posts do mural (aprovação / moderação) |
| `votacao` | Votações e deliberações |
| `documento` | Novos documentos |
| `sistema` | Avisos do sistema |

---

## API Endpoints

```
GET    /api/notifications                  # Listar as do utilizador
GET    /api/notifications/unread/count     # Contador de não lidas
GET    /api/notifications/stream           # SSE: count de não lidas em tempo real
GET    /api/notifications/types            # Categorias disponíveis
PATCH  /api/notifications/{id}/read        # Marcar uma como lida
PATCH  /api/notifications/mark-all-read    # Marcar todas como lidas
DELETE /api/notifications/{id}             # Eliminar uma notificação
DELETE /api/notifications/clear/all        # Limpar todas
POST   /api/notifications                  # Criar notificação (admin)
POST   /api/notifications/broadcast        # Broadcast para todos (admin)
```

---

## Stream em Tempo Real (SSE)

`GET /api/notifications/stream` (`media_type: text/event-stream`):

- **Auth**: cookie httpOnly **ou** `Authorization: Bearer` — o browser usa `EventSource` com `withCredentials: true`. O *fallback* `?token=` foi **removido** (o token aparecia em logs do proxy).
- **Payload**: emite `data: {"count": N}` sempre que o número de não lidas muda; *poll* interno a cada **5s** com *heartbeat*.
- **Limite**: máximo de **3 ligações em simultâneo por utilizador** (`429` se exceder — fechar outras abas). Slots geridos por TTL para libertar ligações órfãs.
- **Fallback**: o `NotificationContext` recorre a **polling 30s** quando o SSE não está disponível.

---

## Auto-triggers (helpers.py)

Geração automática via `create_notification`, `notify_users`, `notify_all_active_users`, `notify_admins`:

- Nova votação / deliberação → notifica sócios elegíveis
- Alteração em projeto → notifica membros do projeto
- Nova transação financeira / movimento → notifica admin/financeiro
- Submissão de foto → notifica admin; aprovação/rejeição → notifica o autor
- Novo documento / comunicado → notifica os destinatários
- Eventos de governança (assembleias, prestação de contas) → notificações dedicadas

---

## Segurança

- Apenas as notificações do próprio utilizador são visíveis
- Auth obrigatória (cookie httpOnly ou Bearer) em todos os endpoints, incluindo o SSE
- Apenas admin pode criar/broadcast notificações
- Não é possível ver notificações de outros utilizadores

---

## Ficheiros

```
Backend:
  backend/routes/notifications.py     # endpoints REST + stream SSE
  backend/models.py                   # modelo Notification
  backend/helpers.py                  # create_notification, notify_users, notify_all_active_users, notify_admins

Frontend:
  frontend/src/contexts/NotificationContext.js   # EventSource + fallback polling 30s
  frontend/src/components/NotificationBell.js     # badge + dropdown
  frontend/src/pages/private/NotificacoesPage.js  # página completa
```
