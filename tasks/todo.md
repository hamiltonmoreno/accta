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

**Pendente (fora deste PR) — issues abertas:**

- [#281](https://github.com/hamiltonmoreno/accta/issues/281) — `chore(db)`: `DROP TABLE invoices` em prod (STOP — schema destrutivo; tabela órfã vazia).
- [#277](https://github.com/hamiltonmoreno/accta/issues/277) — `fix(finances)`: DRE/export truncam a 5000 transações silenciosamente (summary não).
- [#278](https://github.com/hamiltonmoreno/accta/issues/278) — `fix(finances)`: geração de quotas limitada a 1000 sócios (`to_list(1000)`).
- [#279](https://github.com/hamiltonmoreno/accta/issues/279) — `fix(finances)`: joia/preview aceita `cta_qualified_since` no futuro sem validação.
- [#280](https://github.com/hamiltonmoreno/accta/issues/280) — `fix(finances)`: audit logs de finanças sem IP/User-Agent (falta `request=`).
- [#282](https://github.com/hamiltonmoreno/accta/issues/282) — `cleanup(ranking)`: comentário órfão menciona invoices (detetado na revisão pós-merge).

---

## Review — spec 010 aviso-deliberacao-pendente (2026-06-28)

**Feito (14/14 tarefas, branch `feature/aviso-deliberacao-pendente`):** aviso à Direção de Ato
(Art. 54) `pendente` há > X dias (X admin-configurável, default 7), **uma única vez** por Ato.

- **Disparo**: loop in-process diário — `asyncio.create_task(overdue_atos_loop())` no
  `@app.on_event("startup")` de `server.py` (padrão non-fatal dos seeds). Decisão confirmada pelo dono.
- **Lógica** (`routes/atos.py` `notify_overdue_atos()`): lê `ato_overdue_dias`; varre Atos `pendente`
  sem `overdue_notified_at`; idade > X (`.days` trunca → dispara a X+1 completos); destinatários
  `members_of_orgao("direcao")` (exclui técnicos/inativos); `notify_users(..., "financeiro", ..., link)`;
  grava a marca. Sem Direção ⇒ no-op sem marcar. `created_at` ausente/inválido ⇒ ignorado.
- **Config** (`models.py` + `routes/finances.py`): `FinanceSettings.ato_overdue_dias` (default 7) +
  `FinanceSettingsUpdate.ato_overdue_dias`; PATCH admin existente valida `>= 1`.
- **Idempotência**: marca `Ato.overdue_notified_at` (aditivo); filtro `$exists:false`.
- **Endpoint** (verificação/disparo manual): `POST /api/atos/notify-overdue` (admin-only).
- **Testes**: `tests/test_atos_overdue.py` (8 casos, verdes); 159 testes in-process verdes; ruff limpo.
  Falhas em `test_finance_improvements.py` = integração `import requests` sem servidor (ambiental).

**Zero deps novas. Backend-only.** Campos aditivos ⇒ sem migração, sem STOP condition.

**Por fechar (fora do âmbito de codificação):** release `develop→main` exige **Via B** (toca `backend/`);
verificação prod = `POST /api/atos/notify-overdue` sem token → 401 + log de arranque do loop. Só após
RELEASED+deployed renomear `specs/010-...` para `-concluido` (convenção do projeto).
