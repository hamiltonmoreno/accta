# Contracts — API `/api/push`

**Feature**: 009-notificacoes-push-celular | **Date**: 2026-06-28

Todos os endpoints exigem autenticação (`Authorization: Bearer …` /
cookie httpOnly) via `get_current_user`. Prefixo: `/api/push`.

Quando a funcionalidade não está configurada (sem VAPID), os endpoints que dela
dependem respondem **503** `{"detail": "Notificações push não estão configuradas."}`.

---

## GET `/api/push/vapid-public-key`

Devolve a chave pública VAPID (applicationServerKey) para o browser subscrever.

- **200** → `{ "publicKey": "<base64url>" }`
- **401** → não autenticado
- **503** → push não configurado

## POST `/api/push/subscribe`

Regista (upsert por `endpoint`) a subscrição deste dispositivo para o sócio
atual.

**Request body** (`PushSubscriptionRequest`, formato de `PushSubscription.toJSON()`):

```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/abc...",
  "keys": { "p256dh": "<base64url>", "auth": "<base64url>" }
}
```

- **200** → `{ "ok": true }` (INSERT se endpoint novo; UPDATE se já existia)
- **400** → `{ "detail": "Endpoint de push inválido." }` (endpoint não-HTTPS /
  host privado/interno — anti-SSRF)
- **401** → não autenticado
- **422** → corpo inválido (falta `endpoint`/`keys`)
- **503** → push não configurado

## POST `/api/push/unsubscribe`

Remove a subscrição deste dispositivo (apenas a do próprio sócio; filtro por
`user_id` + `endpoint`). Idempotente.

**Request body**: igual a `subscribe` (usa `endpoint`).

- **200** → `{ "ok": true }`
- **401** → não autenticado

## POST `/api/push/test`

Envia um aviso de teste ao próprio sócio (confirma a ativação ponta-a-ponta).

- **200** → `{ "ok": true, "devices": <int> }`
- **400** → `{ "detail": "Nenhum dispositivo subscrito para esta conta." }`
- **401** → não autenticado
- **503** → push não configurado

---

## Payload do Web Push (backend → service worker)

JSON entregue ao evento `push` do service worker:

```json
{ "title": "…", "body": "… (≤180 chars)", "url": "/carteira" }
```

O service worker mostra `showNotification(title, { body, icon, badge, data:{ url } })`
e, no `notificationclick`, foca/abre o portal em `url`. Sem `tag` por omissão
(cada aviso é uma entrada separada).

## Comportamento de entrega (`dispatch_push`)

- Resolve subscrições dos `user_ids` numa única query (`{$in: …}`).
- Envia cada uma em threadpool; em **404/410 (Gone)** remove a subscrição.
- No-op se VAPID não configurado; ignora (defensivamente) endpoints não seguros.
