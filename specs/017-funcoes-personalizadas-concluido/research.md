# Research — Funções personalizadas com privilégios à medida (017)

**Date**: 2026-07-02 · Todas as NEEDS CLARIFICATION da spec foram resolvidas pelo dono (Q1 = ligação viva; Q2 = base sempre «sócio»). Este documento fixa as decisões técnicas.

## D1 — Como materializar a «ligação viva» sem tocar no hot path do RBAC

- **Decision**: denormalização com propagação. O utilizador guarda `custom_role_id` (referência) **e** `privileges` materializados a partir da função. Editar a função faz `update_many({"custom_role_id": id}, {"$set": {"privileges": [...]}})` sobre `users`. O RBAC em runtime (`auth.has_privilege`, `permissions.user_can`, todos os 32 módulos de rotas) continua a ler `user.privileges` — **zero alterações no caminho de autenticação/autorização**.
- **Rationale**: `get_current_user` já lê o doc do utilizador a cada pedido; resolver a função em runtime acrescentaria 1 leitura por pedido ou uma cache. A propagação na escrita (operação rara, escala de unidades) dá a mesma semântica «viva» com custo zero no hot path e zero risco de regressão (SC-002). O DAO já suporta `update_many` + `$set`.
- **Alternatives considered**: (a) resolver `custom_role_id` → privilégios em `get_current_user` a cada pedido — rejeitado: toca no caminho crítico de auth e obriga a cache/invalidação; (b) snapshot puro sem referência — rejeitado pelo dono (Q1).

## D2 — Onde guardar as funções personalizadas

- **Decision**: nova coleção `custom_roles` (tabela `(pk, doc jsonb)` criada em `ensure_schema()` ao acrescentar a `COLLECTIONS` em `database.py`). Doc: `{id, name, description, privileges[], created_by, created_at, updated_at}`.
- **Rationale**: padrão idêntico às 63 coleções existentes; aditivo, sem migração. Unicidade do nome validada na rota (normalização trim+casefold) — à escala esperada (unidades de funções, 1 admin) não se justifica índice único.
- **Alternatives considered**: embutir o catálogo em `finance_settings`/`brand_settings`-style singleton — rejeitado: é uma lista CRUD com contagem por função, coleção própria é mais simples de consultar.

## D3 — Semântica da atribuição (Q2: base sempre «sócio»)

- **Decision**: atribuir uma função personalizada define no utilizador `role="socio"`, `privileges=<privilégios da função>` e `custom_role_id=<id>`. Atribuir uma função fixa (ou editar privilégios manualmente) **destaca** o utilizador da função (`custom_role_id=None`). O payload com `custom_role_id` tem precedência sobre `role`/`privileges` no mesmo pedido.
- **Rationale**: mantém o invariante FR-004 («acesso = base sócio + privilégios da função, exatamente») e evita drift entre a função e os privilégios materializados. A UI reforça: checkboxes de privilégios ficam read-only enquanto uma função personalizada está selecionada.
- **Alternatives considered**: permitir privilégios individuais *além* da função — rejeitado: cria três fontes de acesso sobrepostas e torna a propagação destrutiva de ajustes manuais; a spec define acesso ≡ função.

## D4 — Superfície API

- **Decision**: novo módulo `backend/routes/custom_roles.py` com prefixo `/api/admin/custom-roles`:
  - `GET /` — lista com `user_count` por função (1 query a `users` agregada, sem N+1)
  - `POST /` — cria (nome único, ≥1 privilégio ⊆ `PRIVILEGES`)
  - `PATCH /{id}` — edita; se `privileges` mudar, propaga via `update_many` e notifica os afetados (padrão «Perfil Atualizado» existente)
  - `DELETE /{id}` — 409 com contagem se `user_count > 0`
  - Guard: `current_user.role == "admin"` (FR-009 — exclusivo de admin, sem overlay `manage_users`); `create_audit_log` em todas as escritas.
- A atribuição a utilizadores NÃO ganha endpoint novo: reutiliza `PATCH /api/users/{user_id}` (campo aditivo `custom_role_id` em `UserAdminUpdate`) e `POST /api/admin/invite` (campo aditivo em `InviteCreate`).
- **Rationale**: um domínio novo → um módulo novo (padrão do projeto); atribuição pelo endpoint existente herda auditoria before/after e notificação ao utilizador já implementadas.
- **Alternatives considered**: meter o CRUD em `admin.py` — rejeitado: o módulo já é grande e mistura convite/aprovação/cargos.

## D5 — Interação com cargos estatutários e predefinições

- **Decision**: o botão «Aplicar predefinições do cargo» (spec 016) e os fluxos `/admin/cargos` + proclamação de eleições continuam a escrever `role`/`privileges` como hoje; qualquer um deles limpa `custom_role_id` (destaque). No `EditUserModal`, se o utilizador tem função personalizada, aplicar predefinições mostra aviso prévio (FR-010).
- **Rationale**: cargos são a fonte estatutária; funções personalizadas são comodidade administrativa. Precedência clara evita estados híbridos.

## D6 — Sem dependências novas, sem alterações de schema destrutivas

- Campos novos em Pydantic são todos `Optional`/aditivos (`custom_role_id`), seguros para documentos existentes. Zero deps backend/frontend novas. Sem migração de dados.
