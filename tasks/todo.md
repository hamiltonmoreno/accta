# TODO — Finanças: Fundação F0 + Categorias estatutárias

Specs: `spec-controlos-financeiros` (§4.2 categorias, §6.1 campos aditivos, §9 F0/F1)
+ `spec-ciclo-prestacao-contas` (F0: `proof_url`/`conferido`). Decisões com efeito
estatutário **alinhadas com o dono** em `memory/finance-specs-alignment` (2026-05-21):
categorias canónicas, mapa de migração (`patrocinios → extraordinarias`), e
**estender** o `GET /finances/meta/categories` existente (não criar `/categorias`).

Branch: `feature/financas-fundacao-categorias → develop` (GitFlow). PR aditivo,
sem alteração de schema/DDL, sem colecções novas. Migração `--apply` é STOP — não corre.

## F0 — Campos aditivos + helper de órgão (aditivo, zero mudança de comportamento)
- [x] `models.py` `Transaction`: + `ato_id`, `proof_url`, `conferido` (Optional)
- [x] `models.py` `FinanceSettings`: + `coaprovacao_limiar: float = 0.0`
- [x] `models.py` `UserBase`: + `cta_qualified_since`, `joia_devida`, `joia_isento` (Optional)
- [x] `permissions.py`: + `is_presidente(user)` → cargo key `dir_presidente`
- [x] `AuthContext.js`: + `isPresidente` (`cargo === 'dir_presidente'`)

## Categorias estatutárias (Art. 5) — backend + frontend em lockstep
- [x] `models.py` `INCOME_CATEGORIES` → canónicas: quotas, joias, subvencoes,
      donativos, venda_publicacoes, juros, extraordinarias
- [x] `models.py` + `INCOME_CATEGORY_LABELS` / `EXPENSE_CATEGORY_LABELS` (PT c/ acentos, p/ meta)
- [x] `models.py` + `LEGACY_INCOME_ALIASES` + `canonical_income_category()` (mapa partilhado script/testes)
- [x] `finances.py` `CATEGORY_LABELS`: + keys de receita novas (ASCII p/ CSV/DRE); manter legadas
- [x] `finances.py` `GET /finances/meta/categories`: + `labels` (NÃO criar `/categorias`)
- [x] `frontend/.../financeiro/constants.js`: `INCOME_CATEGORIES`+`CATEGORY_LABELS` → canónicas
      (refactor p/ consumir meta fica F4)
- [x] `scripts/migrate_income_categories.py`: plano puro + dry-run default + `--apply --confirm` (NÃO correr)

## Testes & gates
- [x] Atualizar `test_finances.py` / `test_finances_routes.py` (categorias legadas → canónicas)
- [x] Novos testes: campos aditivos aceites; meta devolve `labels`; create receita só aceita
      canónicas (legada → 400); `canonical_income_category` mapeia aliases (idempotente)
- [x] `pytest -m unit` (709 passed) · `ruff check`/`format` ✓ · `eslint` (meus ficheiros) ✓ · `craco build` ✓

## Review
- **Âmbito aditivo verificado**: todos os campos novos são `Optional`/com default em `doc jsonb`
  → zero DDL, zero colecções novas, zero migração de schema. Não dispara nenhum STOP.
- **Categorias em lockstep**: backend (validação + meta + CSV/DRE) e frontend (`constants.js`)
  mudaram juntos — não fica um dropdown a oferecer categorias que o backend rejeita.
- **Decisão do dono respeitada**: `patrocinios → extraordinarias` (a spec hesitava → donativos;
  `memory/finance-specs-alignment` anula). Meta estende `/categories` (sem `/categorias` paralela).
- **Migração não corrida**: `migrate_income_categories.py` fica em dry-run; `--apply` exige
  `--confirm` (STOP §11). DB dev quase vazia; sem dados reais a migrar.
- **Testes**: `test_finances_foundation.py` (25 casos) cobre campos aditivos, categorias,
  `canonical_income_category`, plano de migração (despesa "eventos" NÃO renomeada) e `is_presidente`.
- **Pendente do dono**: verificação manual no browser; correr a migração quando houver dados reais.

## STOP / fora de escopo (fases seguintes)
- `migrate_income_categories.py --apply` em `transactions` (STOP §11) — não corrido (DB dev quase vazia)
- 4.1 `atos`/dupla-assinatura · 4.3 `compute_joia`+hook de admissão · ciclo F1–F5 — PRs seguintes
- `TransactionUpdate.proof_url`/`conferido` + wiring da rota PATCH — ciclo F2
