# Data Model — Consolidação do modelo de acessos (spec 018)

## Entidades alteradas

### Utilizador (`users`, campo a campo)

| Campo | Antes | Depois (F2) |
|---|---|---|
| `role` | admin \| financeiro \| moderador \| socio | **admin \| socio** (legados aceites e traduzidos 1 release — R6) |
| `privileges[]` | overlays aditivos | **única fonte de acesso granular** (inalterado no formato) |
| `custom_role_id` | ref. viva a funções (017) | inalterado; passa a incluir as seeds |
| `cargo`/`orgao`/`cargo_history` | estatutário | inalterado (defaults reescritos — R7) |
| `department` | rótulo livre/canónico | inalterado; UI marca «organizacional — não altera acessos» |

Sem migração de schema (jsonb); a migração é **de dados** (valores de `role`).

### Função personalizada (`custom_roles`) — sem mudança de forma

Novos registos **seed** criados pela migração (R4/R5):

| name | privileges (provisório — output da matriz F1) |
|---|---|
| Financeiro | `manage_finances`, `manage_users` |
| Moderador | `moderate_content` |

`description` regista a origem («migração spec 018»). São funções normais: editáveis,
elimináveis (409 se em uso), ligação viva.

### Defaults de cargo (`governance.py` CARGOS — R7/D3)

| cargo | role antes → depois | privileges (inalterados) |
|---|---|---|
| dir_presidente / dir_vice_presidente | admin → **admin** | ALL |
| dir_secretario | admin → **socio** | manage_users, manage_events, manage_documents, moderate_content |
| dir_tesoureiro | financeiro → **socio** | manage_finances, view_audit_logs |
| dir_vogal | moderador → **socio** | moderate_content, manage_events |
| ag_*, cf_*, socio | socio (já era) | inalterados |

### Tabela canónica módulo→privilégio (nova, F1 — `governance.py`)

`MODULE_ACCESS: dict[str, dict]` — por módulo: `privilege` (o granular que governa),
`legacy_roles` (roles que passavam no gate antes da F2; documental, alimenta a matriz de
testes). Módulos: finances(view/manage), users, events, documents, benefits, moderation
(gallery+wall), comunicados, audit, ranking, regulamentos, atos/governança (por cargo —
fora da tabela, continuam em `permissions.py`).

### Mapa de migração (`audit_logs` + ficheiro de backup)

Por utilizador migrado: `{"user_id", "before": {role, privileges, custom_role_id},
"after": {...}, "regra": "seed"|"privilegios_diretos"}` — gravado como audit log
(`role_model_migrated`) + JSON de backup pré-migração no VPS (padrão do reset de 2026-06-30).

## Invariantes (pós-F2)

1. `role ∈ {admin, socio}` em todos os docs `users` (migração + validação de escrita).
2. Holder de função personalizada: `privileges == função.privileges` (invariante 017,
   preservado pela regra R3 — quem tinha extras não recebe função).
3. Acesso efetivo pré == pós migração para todos os utilizadores (SC-001, matriz R10).
4. Nenhum escritor de `role` produz valores legados (defaults R7 + tradução R6).
