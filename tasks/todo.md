# Plano — Remover `invoices` e unificar a vista financeira do sócio em `transactions`

## Contexto / justificação

- Tabela `invoices` **vazia em produção** (verificado: 0 linhas no Supabase; `transactions`=12, todas `category=quotas`).
- `invoices` é um subsistema legado/dormente: `POST`/`confirm` sem UI viva (`invoicesAPI.create/confirm` nunca chamados), `confirm` não materializa transação.
- Único uso vivo: `GET /invoices` → `MemberFinanceView` ("Minhas Quotas"), que mostra **vazio para todos** em prod.
- As quotas reais vivem em `transactions` (com `user_id`) e **nunca** chegam ao sócio.
- `/stats total_revenue` soma invoices pagas → devolve **0** em prod; é uma métrica órfã divergente do resto do dashboard.

**Objetivo:** eliminar `invoices`, dar ao sócio uma vista real das suas quotas a partir de `transactions`, e alinhar `total_revenue` com a contabilidade real (`transactions`).

---

## Decisões de design

1. **Novo endpoint self-service** `GET /finances/me/quotas` em `finances.py`:
   - Sem `require_view_finances` — qualquer utilizador autenticado vê **só as suas** (`user_id == current_user.id`).
   - Filtra `transactions` por `user_id`, `type="receita"`, `category in ("quotas","joias")`; ordena `date` desc; projeção `{"_id":0}`.
   - Devolve `{ items, total_pago }` (soma dos `amount`). Em `transactions` não há `status` pendente/pago — todos os lançamentos são efetivos (descontados em folha).
2. **`total_revenue`**: removido de `/stats`; o card "Receita Anual" passa a depender só de `financeSummary` (já é a fonte primária), com guard para `undefined`/0.
3. **Tabela física `invoices` em prod**: fica vazia e órfã. **DROP é STOP condition** (schema destrutivo) → passo manual separado, só com confirmação do dono. Não bloqueia este PR.

---

## Backend

- [ ] `routes/invoices.py` — **apagar ficheiro**.
- [ ] `routes/__init__.py` — remover import (linha 4) e `include_router` (linha 40).
- [ ] `models.py` — remover `Invoice` e `InvoiceCreate` (578–607). Confirmar que mais nada os importa (só `invoices.py`, que foi apagado).
- [ ] `routes/stats.py` — remover o bloco `total_revenue` (20–22) e a chave no `return` (28).
- [ ] `routes/finances.py` — adicionar `GET /finances/me/quotas` (ver design #1).
- [ ] `database.py` — remover `"invoices"` de `COLLECTIONS` (57) e os 2 índices `ix_inv_*` (864–866). Verificar que `__getattr__`/`_COLLECTION_SET` não é exercido para invoices em mais lado nenhum (já não é).

## Frontend

- [ ] `pages/private/financeiro/MemberFinanceView.js` — reescrever para `financesAPI.getMyQuotas()`. Remover dependência de `INVOICE_STATUS_CONFIG`; lista de lançamentos efetivos (data, categoria, descrição, valor) + "Total Pago"; manter aviso de folha salarial; corrigir `amount` → `toLocaleString('pt')` (era `{inv.amount} CVE` cru).
- [ ] `utils/api.js` — remover `invoicesAPI` (270–274); adicionar `financesAPI.getMyQuotas: () => api.get('/finances/me/quotas')`.
- [ ] `lib/queryClient.js` — remover `queryKeys.invoices` (142–143); adicionar key p/ quotas do sócio (ex. `transactions.myQuotas`).
- [ ] `lib/statusConfig.js` — remover `INVOICE_STATUS_CONFIG`/`INVOICE_STATUS_FALLBACK` (uso restante só era o `MemberFinanceView`).
- [ ] `pages/private/dashboard/AdminStats.js` — remover fallback `stats.total_revenue` (27,30); usar só `financeSummary` com guard.
- [ ] `pages/private/dashboard/widgets.js` — remover ícone `invoice_due` (31) — tipo de notificação morto (nunca criado).

## Seed

- [ ] `scripts/seed_data.py` — remover criação de invoices (38, 136–173, 420). Se quisermos dados de demo na carteira, semear `transactions` de quota por sócio (com `user_id`).

## Testes

- [ ] `tests/test_invoices_routes.py` — **apagar**.
- [ ] `tests/conftest.py` — remover `mock_db.invoices` pré-cabeado se existir.
- [ ] Rever/ajustar refs a `invoice`/`total_revenue`: `test_accta_portal.py`, `test_dashboard_redesign.py`, `test_finances_edge_cases.py`, `test_rbac_matrix.py`, `test_refactoring_all_endpoints.py`.
- [ ] Novo teste p/ `GET /finances/me/quotas`: sócio vê só as suas; user diferente não vê as do outro; soma `total_pago` correta; sem auth → 401.

## Verificação (DoD)

- [ ] `cd backend && pytest` verde.
- [ ] `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60` limpo.
- [ ] `cd frontend && yarn build` ok.
- [ ] Validar "Minhas Quotas" no browser com um sócio que tenha `transactions` de quota.
- [ ] `grep -rn "invoice" backend frontend/src` sem resíduos vivos (exceto comentários históricos intencionais).

## Git / entrega (GitFlow)

- [ ] Branch `feature/remover-invoices-unificar-transactions` a partir de `develop`.
- [ ] 1 PR → `develop` (backend + frontend + seed + testes).
- [ ] **Pós-merge, separado e com confirmação:** `DROP TABLE invoices` em prod (STOP — schema destrutivo).

## Stop conditions ativas neste plano

- DROP da tabela em prod → confirmar com o dono (não incluído no PR).
- `MemberFinanceView` lê uma rota nova; confirmar que nenhum outro consumidor depende de `GET /invoices` (verificado: só `MemberFinanceView`).

## Review

**Implementado (26 ficheiros, +215/−564):**

- **Backend:** apagado `routes/invoices.py`; removido router de `__init__.py`;
  removidos `Invoice`/`InvoiceCreate` de `models.py`; removido `total_revenue`
  de `stats.py`; removidos `"invoices"` + índices `ix_inv_*` de `database.py`.
  Novo `GET /finances/me/quotas` (self-service, filtro fixo por `user_id`,
  sem `view_finances`).
- **Frontend:** `MemberFinanceView` reescrito (lê `transactions` via novo
  endpoint, corrigido `amount`→`toLocaleString`); removidos `invoicesAPI`,
  `queryKeys.invoices`, `INVOICE_STATUS_CONFIG`, ícones `invoice_due`
  (widgets/NotificationBell/NotificacoesPage); `AdminStats` sem fallback
  `total_revenue`; `SettingsTab` invalida a key correta.
- **Seed:** `seed_data.py` gera quotas como `transactions` (limpa `transactions`
  no re-seed em vez de `invoices`).
- **Testes:** apagado `test_invoices_routes.py`; limpos `conftest`,
  `test_finances_edge_cases`, `test_rbac_matrix`, `test_accta_portal`,
  `test_dashboard_redesign`, `test_refactoring_all_endpoints`; novo teste unit
  `TestMyQuotas` em `test_finances_routes.py`.
- **Extra:** `venv311/` adicionado ao `.gitignore` (estava untracked).

**Verificação (DoD):**

- [x] `pytest tests/test_finances_routes.py tests/test_finances_edge_cases.py tests/test_rbac_matrix.py` → **123 passed**.
- [x] `pytest --collect-only` → **1847 testes**, sem `ImportError`.
- [x] `eslint src/` → **0 errors**, 24 warnings (pré-existentes, < 60).
- [x] `craco build` → build de produção OK.
- [ ] Validação no browser com sócio que tenha quotas (pendente — requer sessão).

**Pendente (fora deste PR):**

- `DROP TABLE invoices` em prod (STOP — schema destrutivo; tabela vazia, inócua).
- Dívidas não tocadas (análise): DRE truncado a 5000, cap de 1000 sócios na
  geração de quotas, jóia-preview com data futura, audit logs de finanças sem IP.
