# Data Model — Exportar carteira de quotas em PDF

**Sem schema novo, sem migração.** A feature **lê** dados existentes; não cria nem
altera tabelas, modelos Pydantic ou índices. Documenta-se a vista usada.

## Fonte de dados (existente — `db.transactions`)

A carteira do sócio = lançamentos em `transactions` com (igual a `GET /me/quotas`):

```
{ "user_id": <id do próprio>, "type": "receita", "category": {"$in": ["quotas","joias"]} }
```
ordenados por `date` desc. Campos relevantes por lançamento (jsonb):

| Campo | Tipo | Uso no PDF |
|-------|------|------------|
| `date` | string ISO-8601 | coluna Data (e agrupamento por ano) |
| `description` | string | coluna Período/Descrição |
| `category` | string (`quotas`/`joias`) | coluna Categoria (rótulo Quota/Joia) |
| `amount` | number | coluna Valor; somatório → Total |

- **Sem estado por lançamento**: todos são pagamentos **efetivos** (não há pendente/
  pago; quotas por folha). Coerção defensiva de `amount` ausente/mal-formado → 0
  (igual a `/me/quotas`).
- **Identidade do sócio** (do `current_user`): `name`, `member_id` — para o bloco de
  identificação do PDF. `password` nunca lido/exposto.

## Saída (novo) — documento PDF

Não é uma entidade persistida: é um **artefacto gerado on-the-fly** e devolvido como
`application/pdf` (download). Não é guardado pelo sistema (privacidade — D2/Assumptions).

| Elemento | Conteúdo |
|----------|----------|
| Cabeçalho | Marca ACCTA + "Carteira de Quotas" |
| Identificação | nome, n.º de sócio, data de emissão (UTC) |
| Tabela | Data · Período/Descrição · Categoria · Valor (CVE) |
| Total | soma de `amount` (= `total_pago` de `/me/quotas`) |
| Rodapé | "Comprovativo pessoal de uso interno — sem valor fiscal." |

## State transitions

N/A — sem máquina de estados.
