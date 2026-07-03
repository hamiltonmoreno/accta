# Contratos de API — Consolidação do modelo de acessos (spec 018)

Sem endpoints novos. Mudanças de contrato em superfícies existentes, por fase.

## Fase 1 (higiene) — ZERO mudança de contrato

Nenhum endpoint muda de comportamento; a matriz de testes (R10) é a prova.

## Fase 2 (modelo + migração)

### `PATCH /api/users/{id}` (admin)

- `role` aceita `admin | socio`. **Release de transição**: `financeiro`/`moderador` são
  aceites e traduzidos → `role="socio"` + `custom_role_id=<seed>` + privilégios da seed;
  audit `details.legacy_role_translated: true`. Release seguinte: 400 «Nível de acesso
  inválido: use admin ou socio».
- Resto do contrato (custom_role_id da 017, destaque, sensitive audit) inalterado.

### `POST /api/admin/invite` (admin)

- Idem: `role ∈ {admin, socio}` + tradução de legados na release de transição (o contrato
  422 da spec 016 mantém-se para roles desconhecidas; a mensagem passa a listar só os
  níveis novos na release pós-transição).
- `custom_role_id` (017) inalterado — e passa a ser o caminho recomendado para «convidar
  um financeiro» (função seed «Financeiro»).

### `GET /api/governance/structure` e `GET /api/users/meta/cargos`

- `cargos[].role_default` reflete R7/D3 (presidente/vice = admin; restantes = socio).
  Formato inalterado — consumidores (botão «Aplicar predefinições», promote) já leem daqui.

### `GET /api/admin/custom-roles`

- Passa a incluir as funções seed «Financeiro»/«Moderador» (funções normais). Nomes
  `financeiro`/`moderador` saem da lista de reservados (R5) — a unicidade normal protege.

### Alerta de escalada (interno, `helpers.py`)

- `notify_role_change`: dispara para `new_role == "admin"` OU novos privilégios sensíveis
  ({manage_users, manage_finances, view_audit_logs}), incl. via função personalizada (R8).
  Canal e formato da notificação inalterados.

### Sem mudança

- Login/refresh/me (role continua no payload do utilizador; valores novos apenas).
- Registo público/auto-registo (nunca aceitou role).
- Eleições/cargos: promote/demote/transfer/proclamação continuam a escrever role+privileges
  — passam a fazê-lo a partir dos defaults novos (R7); contrato HTTP inalterado.
