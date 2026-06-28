# Data Model — Notificações Push no Celular

**Feature**: 009-notificacoes-push-celular | **Date**: 2026-06-28

## Coleção nova: `push_subscriptions`

Tabela `(pk bigserial, doc jsonb)` (padrão do DAO Mongo-compatível). Representa a
autorização de **um dispositivo/navegador** para receber Web Push.

| Campo         | Tipo   | Notas |
|---------------|--------|-------|
| `id`          | string | `str(uuid4())`, gerado na criação |
| `user_id`     | string | sócio dono da subscrição |
| `endpoint`    | string | URL do serviço de push (**único**; chave de upsert) |
| `p256dh`      | string | chave pública do cliente (cifra do payload) |
| `auth`        | string | segredo de autenticação do cliente (cifra) |
| `user_agent`  | string | UA do dispositivo no registo (≤255, diagnóstico) |
| `created_at`  | string | ISO-8601 (na criação) |
| `updated_at`  | string | ISO-8601 (na criação e em cada re-subscrição) |

### Índices (em `ensure_schema()`)

- `ix_push_user` em `(doc->>'user_id')` — lookup das subscrições de um sócio.
- `ux_push_endpoint` **UNIQUE** em `(doc->>'endpoint')` — um registo por
  dispositivo; suporta o upsert e a poda por endpoint.

### Regras de validação

- `endpoint` tem de passar `is_safe_push_endpoint` (HTTPS + host público) **antes
  de gravar** (FR-009 / anti-SSRF).
- `p256dh`/`auth` obrigatórios (vêm de `PushSubscription.toJSON().keys`).

### Transições de estado (ciclo de vida)

```
(inexistente)
   │  subscribe (endpoint novo, válido)        → INSERT  → ATIVA
ATIVA
   │  subscribe (mesmo endpoint)               → UPDATE  → ATIVA (re-aponta user/chaves)
   │  unsubscribe (próprio user + endpoint)    → DELETE  → (inexistente)
   │  envio devolve 404/410 (Gone)             → DELETE  → (inexistente)  [poda]
```

## Entidade existente (reutilizada): `notifications`

Sem alterações de esquema. Cada documento (`user_id`, `type`, `title`,
`message`, `link`, `read`, `created_at`) que é criado passa também a ser
espelhado como push via `dispatch_push(user_id, title, message, link)`.

## Modelo Pydantic (request)

- `PushSubscriptionRequest`: `endpoint: str`, `keys: { p256dh: str, auth: str }`
  (`extra="ignore"` — aceita o objeto de `PushSubscription.toJSON()`).

## Exclusões (consistentes com a entrega in-app)

- Contas `account_type="technical"` e sócios `status != "ativo"` não recebem
  push (herdado da lógica de `notify_all_active_users`).
- Sem chaves VAPID configuradas: nenhuma subscrição é aceite (503) e nenhum
  envio ocorre (no-op).
