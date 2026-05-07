# Sistema de Notificacoes In-App — Portal ACCTA

## Status: 100% Implementado e Funcional

---

## Overview

Sistema completo de notificacoes para manter socios informados sobre eventos importantes da associacao.

### Componentes:
1. Backend API (5 endpoints, 100% testado)
2. NotificationContext (Provider React com polling 30s)
3. NotificationBell (Badge + Dropdown no header)
4. NotificacoesPage (Pagina completa com stats e filtros)
5. Broadcast Admin (Enviar notificacoes para todos)
6. Auto-triggers (Projetos, Financas, Galeria)

---

## Tipos de Notificacao

| Tipo | Quando e Gerada | Link |
|------|-----------------|------|
| poll_opened | Nova votacao criada pelo admin | /votacoes |
| document_new | Novo documento publicado | /documentos |
| wall_post_approved | Post do mural aprovado | /mural |
| wall_post_pending | Novo post aguarda moderacao (para admin) | /mural |
| project_update | Alteracao em projeto | /projetos |
| finance_update | Nova transacao financeira | /financeiro |
| gallery_submission | Nova foto submetida (para admin) | /galeria-admin |
| gallery_approved | Foto aprovada/rejeitada (para socio) | /galeria-admin |
| broadcast | Mensagem geral do admin | - |

---

## API Endpoints

```
GET    /api/notifications                  # Listar todas do utilizador
GET    /api/notifications/unread/count     # Contador nao lidas
PATCH  /api/notifications/{id}/read        # Marcar uma como lida
PATCH  /api/notifications/mark-all-read    # Marcar todas como lidas
POST   /api/notifications                  # Criar notificacao (admin)
POST   /api/notifications/broadcast        # Broadcast para todos (admin)
DELETE /api/notifications/{id}             # Eliminar notificacao
```

---

## Funcionalidades

### Badge Visual
- Contador no sino (header sidebar)
- Animacao pulse quando ha nao lidas

### Dropdown
- Ultimas 10 notificacoes
- Botao "Marcar todas como lidas"
- Click para navegar ao destino
- Timestamp relativo

### Pagina Completa (/notificacoes)
- Dashboard com estatisticas (total, nao lidas)
- Lista cronologica com filtros
- Cards coloridos por tipo
- Eliminacao individual

### Auto-triggers
- Nova votacao → notifica todos socios ativos
- Alteracao em projeto → notifica membros
- Nova transacao financeira → notifica admin/financeiro
- Submissao de foto → notifica admin
- Aprovacao/rejeicao de foto → notifica socio autor

---

## Teste via cURL

```bash
TOKEN=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"socio1@controlador.cv","password":"socio123"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# Contador
curl -X GET "$API_URL/api/notifications/unread/count" \
  -H "Authorization: Bearer $TOKEN"

# Listar
curl -X GET "$API_URL/api/notifications" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Ficheiros

```
Backend:
  /app/backend/routes/notifications.py
  /app/backend/models.py (Notification model)
  /app/backend/helpers.py (create_notification, notify_all_active_users)

Frontend:
  /app/frontend/src/contexts/NotificationContext.js
  /app/frontend/src/components/NotificationBell.js
  /app/frontend/src/pages/private/NotificacoesPage.js
```

---

## Seguranca

- Apenas notificacoes do proprio utilizador sao visiveis
- Token JWT obrigatorio
- Admin pode criar/broadcast notificacoes
- Nao e possivel ver notificacoes de outros utilizadores

---

Status Final: Production-Ready
