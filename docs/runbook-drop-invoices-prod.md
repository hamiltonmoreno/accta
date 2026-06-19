# Runbook — DROP da tabela órfã `invoices` em produção (issue #281)

> **Quando usar:** uma única vez, para remover a tabela física `invoices` que
> ficou **vazia e órfã** após o PR #276 (que removeu todo o subsistema:
> rotas, modelos, índices e `"invoices"` de `database.COLLECTIONS`).
>
> **Natureza:** `DROP TABLE` em produção — **schema destrutivo (STOP condition**
> da CLAUDE.md). Requer confirmação explícita do dono. A tabela está vazia
> (0 linhas verificadas no Supabase), por isso o risco de perda de dados é nulo,
> mas a operação é irreversível e fica documentada aqui.

---

## 0. Factos fixos

| Item | Valor |
|------|-------|
| Tabela alvo | `public.invoices` |
| Estado esperado | **0 linhas** (vazia, órfã) |
| Origem do código | PR #276 (`invoices` fora de `COLLECTIONS`, sem rotas/modelos) |
| DB de produção | PostgreSQL / Supabase (via `DATABASE_URL`, pooler 6543) |
| Artefactos | `scripts/sql/2026-06-19-drop-invoices.sql` · `scripts/drop_invoices_table.py` |

---

## 1. ⚠️ Pré-condição crítica (ler antes de tudo)

O backend em produção **tem de já correr a release que inclui o PR #276**
(onde `"invoices"` saiu de `database.COLLECTIONS`).

**Porquê:** `ensure_schema()` corre no arranque da app e **recria** todas as
tabelas de `COLLECTIONS` de forma idempotente. Se a versão em prod ainda tiver
`"invoices"` em `COLLECTIONS`, o próximo restart/redeploy **recria** a tabela e
o DROP não é durável.

**Verificar (no commit/imagem em prod):**

```bash
# No código que corresponde à imagem em produção:
grep -n '"invoices"' backend/database.py     # NÃO deve haver match (saiu no #276)
```

- Se ainda houver match → **PARAR**. Primeiro fazer a release develop→main com o
  #276 e fazer deploy do backend (ver `docs/runbook-deploy-backend-via-b.md`),
  só depois executar este DROP.
- Se não houver match → seguir para o passo 2.

---

## 2. Pré-checks (não destrutivos)

### 2.1 Confirmar que a tabela está vazia

No Supabase SQL Editor (ou `psql`):

```sql
SELECT to_regclass('public.invoices') AS existe;   -- esperado: "invoices"
SELECT count(*) AS linhas FROM public.invoices;     -- esperado: 0
```

- `linhas > 0` → **PARAR** e investigar a origem (não se dropa dados).

### 2.2 Confirmar ausência de dependências

O modelo é `(pk bigserial, doc jsonb)` por tabela, **sem chaves estrangeiras**
entre coleções — não há objetos dependentes. Confirmação opcional:

```sql
SELECT dependent.relname
FROM pg_depend d
JOIN pg_class dependent ON dependent.oid = d.objid
JOIN pg_class ref ON ref.oid = d.refobjid
WHERE ref.relname = 'invoices' AND d.deptype = 'n';
-- esperado: 0 linhas
```

### 2.3 Backup (defensivo)

A tabela está vazia, mas mantenha o snapshot diário do Supabase do dia da
operação como rede de segurança (Supabase → Database → Backups). Não é preciso
backup ad-hoc para uma tabela de 0 linhas.

---

## 3. Execução — escolher **um** caminho

O DROP tem um **gate de segurança**: aborta se a tabela tiver linhas. Os dois
caminhos são equivalentes; escolher conforme o acesso disponível.

### Caminho A — Supabase SQL Editor (recomendado)

> O Supabase CLI faz *crash* nesta máquina (ver memória `supabase-cli-crash`);
> usar o **web console**.

1. Abrir Supabase → projeto de produção → **SQL Editor**.
2. Colar o conteúdo de **`scripts/sql/2026-06-19-drop-invoices.sql`** e correr.
3. Saída esperada: `NOTICE: invoices vazia (0 linhas) — a remover.` seguido de
   `NOTICE: invoices removida.`
   - Se aparecer `EXCEPTION: ABORTADO: invoices tem N linha(s)…` → o gate travou;
     voltar ao passo 2.1.

### Caminho B — Script Python guardado (via `DATABASE_URL`)

Mesmo gate, corre contra o `DATABASE_URL` do `backend/.env`. Dry-run por defeito.

```bash
# 1) Verificação (não escreve nada):
python scripts/drop_invoices_table.py

#    Esperado: "DRY-RUN: tabela vazia e pronta a remover."
#    Se "ABORTADO: esperado 0 linhas, encontrado N" → PARAR e investigar.

# 2) Aplicar de facto (DROP):
python scripts/drop_invoices_table.py --apply --confirm

#    Esperado: "OK: tabela `invoices` removida."
```

> Apontar o `DATABASE_URL` ao ambiente certo. Confirmar que é a DB de **produção**
> antes de `--apply --confirm`.

---

## 4. Verificação pós-execução

```sql
SELECT to_regclass('public.invoices');   -- esperado: NULL (já não existe)
```

- Smoke da app: `GET https://api.controlador.cv/api/` → 200; abrir o portal e
  confirmar **Financeiro / Minhas Quotas** a carregar (lê `transactions`, não
  `invoices` — não deve ser afetado).
- Confirmar que o arranque do backend não recria a tabela: após o próximo
  restart, repetir a query acima — deve continuar `NULL` (garantido pela
  pré-condição do passo 1).

---

## 5. Rollback

A tabela estava **vazia**, logo não há dados a restaurar. Se por alguma razão
for preciso repor a estrutura (ex.: um backend antigo, pré-#276, foi reposto e
espera a tabela), `ensure_schema()` recria-a automaticamente no arranque **se**
`"invoices"` voltar a `COLLECTIONS`. Recriação manual mínima, se necessária:

```sql
CREATE TABLE IF NOT EXISTS public.invoices (pk bigserial PRIMARY KEY, doc jsonb NOT NULL);
```

---

## 6. Pós-tarefa (follow-up de documentação)

- `.claude/rules/database.md` ainda lista `invoices` em **Collections & Schema**
  ("invoices: user_id, amount, status, period"). É uma referência **stale**
  pós-#276 — sinalizar ao dono para remoção (não editar a fonte canónica de
  regras de forma autónoma).
- Fechar a issue **#281** referenciando este runbook e o resultado da execução.
