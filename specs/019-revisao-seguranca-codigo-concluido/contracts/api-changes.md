# API Contract Changes — Revisão de Segurança (spec 019)

A revisão é **hardening**: preserva o comportamento existente exceto onde o
comportamento é a vulnerabilidade. Nenhuma rota que o frontend chama hoje é
removida. Abaixo, apenas os **deltas** de contrato, por workstream.

## Adicionado

### `GET /api/finances/transactions/{transaction_id}/proof` (WS-A)
- **Auth**: sessão + `require_view_finances` (admin / financeiro / Conselho Fiscal
  read-only) — a MESMA gate de `GET /api/finances/transactions`.
- **200**: `FileResponse` do comprovativo + `Cache-Control: no-store`.
- **403**: sócio sem acesso a finanças.
- **404**: transação inexistente, ou sem `proof_url`, ou ficheiro ausente, ou
  `proof_url` que tenta path-traversal para fora de `UPLOAD_DIR/proofs`.
- **Autorização pelo recurso** (id da transação), nunca pelo filename → sem
  enumeração de ficheiros.
- Nota p/ futura UI de conferência CF: obter por axios autenticado; **não** construir
  o URL com `mediaUrl(proof_url)` contra o caminho estático público.

## Removido / restringido

### `GET /uploads/proofs/*` → **404** (WS-A)
- Deixa de ser servido publicamente, no mount da app **e** no nginx do VPS
  (`deploy/nginx/accta.conf`). Zero consumidores frontend hoje → sem regressão visível.
- **[STOP]** a regra nginx tem de ir no mesmo deploy do backend.

### Rate-limit passa a ser real e por-cliente (WS-D)
- `429 Too Many Requests` (handler slowapi já existente) passa a poder ocorrer em
  **qualquer** rota sob o default **200/min por cliente real** (antes: nunca aplicado).
- Atrás do edge, o 429 isola o cliente abusivo em vez de estrangular o balde partilhado.
- Endpoints de upload ganham `429` sob `30/hour` por IP (WS-F).
- SPA não envia XFF próprio (o edge NPM põe-no) → **sem alteração no frontend**.

### Uploads oversized: `413` **antes** de buffrar (WS-F/G)
- O corpo é lido em streaming; excede o limite da categoria → `413` imediato
  (semântica 413 já usada). Os limites por-categoria mantêm-se (documents 10 MB, etc.).
- **Mitigação acoplada ao bump (WS-G)**: `max_part_size≈11 MB` no arranque — sem ela,
  Starlette 0.40+ daria `400 "Part exceeded maximum size"` a **todo** upload >1 MB.

### Campos de URL: `422` em valores não-`/uploads` (WS-F)
- `Benefit.logo_url`, `Post.cover_url`, `Publicacao.capa_url` (create+update) rejeitam
  `javascript:`/`data:`/`http(s)://externo` → `422`. O frontend já submete `/uploads/…`
  do endpoint de upload → sem alteração no frontend.
- **[verificar]** que nenhum registo em prod guarda URL externo (senão o edit dá 422).

### `GET /api/brand/icon` (WS-F)
- O `302` só aponta para `icon_url` se `/uploads/…` ou host == FRONTEND_URL; caso
  contrário cai no ícone estático default (neutraliza redirect aberto). Caso comum
  (admin faz upload p/ `/uploads`) inalterado.

## Tightening de serialização (WS-B)
- `GET /api/users/{id}` e `PATCH /api/users/me/profile` passam a serializar por
  `response_model=User` (já usado por `GET /api/users` e `GET /api/auth/me`).
- Efeito: chaves jsonb não declaradas em `User`/`UserBase` são descartadas
  (password/MFA já eram removidos por projeção). PII de terceiros passa de «ausente»
  a `null`. **[verificar]** que consumidores (EditUserModal/ProfilePage) não distinguem
  ausente vs `null` para esses campos.

## Comportamento de arranque (WS-E) — não é contrato de runtime
- O backend **recusa arrancar** (fail-closed) se: `SECRET_KEY` < 32 chars; ou um deploy
  HTTPS público (FRONTEND_URL/CORS https não-local) sem `ENVIRONMENT=production`.
- Um prod corretamente configurado é indiferente. **[STOP]** verificar `/docker/accta/.env`
  no VPS antes do release da Fase 2.

## Sem alteração de contrato
- WS-C (IDOR): só testes + fix interno de destinatários de notificação em `wall.py`
  (muda quem recebe o aviso, não a API).
- H6 (CSRF): **verify-only** — o `CSRFOriginCheckMiddleware` já rejeita escrita
  cross-origin em todos os métodos inseguros; só se adiciona teste parametrizado.
- WS-G (deps): sem alteração de contrato **desde que** a mitigação `max_part_size`
  seja aplicada (o teste de upload >1 MB é o árbitro).
- FR-013 (`$regex`): interno ao DAO/helper de pesquisa; sem alteração de endpoint.
