# Data Model: Dashboard unificado

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-07-13

## Escopo

**Nenhuma nova coleção. Nenhum campo novo. Nenhuma migração.** Esta feature introduz
apenas um **modelo de resposta** (Pydantic `response_model`) que define o contrato
público do agregador `GET /api/dashboard/overview`.

Todo o payload é **derivado** em tempo real de dados que já existem: `transactions`,
`users`, `atos`, `polls`, `assembleias`.

## Modelo de resposta: `DashboardOverview`

Adicionar a `backend/models.py` (secção de modelos de resposta):

```python
class MonthlyPoint(BaseModel):
    """Ponto mensal do gráfico receitas × despesas."""
    month: int  # 1..12
    receitas: float
    despesas: float

class FinanceOverview(BaseModel):
    """Bloco financeiro agregado — sem PII, sem lançamentos individuais."""
    saldo_atual: float  # saldo total actual da associação
    receitas_ano: float
    despesas_ano: float
    resultado_ano: float
    quotas_mes: float  # total de quotas do mês corrente
    monthly: List[MonthlyPoint]  # 12 pontos do ano em curso
    despesas_por_categoria: Dict[str, float]  # {"joia": 0, "material": ...}
    mes_atual: Dict[str, float]  # {"receitas": ..., "despesas": ...}
    mes_anterior: Dict[str, float]  # idem — para % de variação

class SociosOverview(BaseModel):
    ativos: int
    novos_90d: int

class AtosOverview(BaseModel):
    pendentes: int
    aguarda_direcao: int  # subset de pendentes: falta assinatura da Direcção
    aguarda_proposta: int  # subset de pendentes: aguarda que o proponente submeta

class UltimaVotacao(BaseModel):
    id: str  # id da votação (público)
    titulo: str
    participacao_pct: int  # 0..100
    fechada_em: str  # ISO-8601

class VotacoesOverview(BaseModel):
    abertas: int
    ultima_fechada: Optional[UltimaVotacao] = None

class ProximaAssembleia(BaseModel):
    id: str
    titulo: str
    data: str  # ISO-8601 (só data, hora opcional)
    tipo: str  # "ordinaria" | "extraordinaria"

class AssembleiasOverview(BaseModel):
    proximas: List[ProximaAssembleia]  # até 3

class DashboardOverview(BaseModel):
    """Contrato do payload do Dashboard. Zero PII (tripwire garante)."""
    finance: FinanceOverview
    socios: SociosOverview
    atos: AtosOverview
    votacoes: VotacoesOverview
    assembleias: AssembleiasOverview
```

## Derivações (fonte dos números)

| Campo | Fonte | Observação |
|-------|-------|------------|
| `finance.saldo_atual` | soma de `transactions` de sempre: receitas − despesas | reutiliza padrão de `compute_financial_summary` sem `year` |
| `finance.receitas_ano` / `despesas_ano` / `resultado_ano` | `compute_financial_summary(year=currentYear)` | reuso directo |
| `finance.quotas_mes` | soma de `transactions.category=="quota", date=[mes_atual)` | query simples |
| `finance.monthly` | `compute_dre_report(currentYear).monthly` (12 pontos) | reuso directo |
| `finance.despesas_por_categoria` | `compute_dre_report(currentYear).despesas_por_categoria` | reuso |
| `finance.mes_atual` / `mes_anterior` | `compute_financial_summary(year, month)` para os 2 meses | 2 chamadas |
| `socios.ativos` | `db.users.count_documents({"status":"ativo", **_MEMBER_FILTER})` | `_MEMBER_FILTER` já em `routes/stats.py` |
| `socios.novos_90d` | `db.users.count_documents({"created_at":{"$gte": today-90d.isoformat()}, **_MEMBER_FILTER})` | `created_at` é ISO string |
| `atos.pendentes` | `db.atos.count_documents({"status":"pendente"})` | |
| `atos.aguarda_direcao` / `aguarda_proposta` | pipeline de agregação simples sobre `atos.assinaturas` | contagem, sem detalhes |
| `votacoes.abertas` | `db.polls.count_documents({"status":"aberta"})` | |
| `votacoes.ultima_fechada` | `db.polls.find({"status":"fechada"}).sort("closed_at",-1).limit(1)` + `db.votes.count_documents({"poll_id": id})` + count de `is_voting_member` sócios activos | 3 queries pequenas |
| `assembleias.proximas` | `db.assembleias.find({"status":"marcada","data":{"$gte":today}}).sort("data",1).limit(3)` | detalhes mínimos |

## Não expor (tripwire)

Payload **não** contém:
- `email`, `phone`, `member_id`, `name`, `cpf`, `password`, `photo_url`, `address`
- listas de `transactions` individuais
- listas de `users` (só contagens)
- listas de `atos` (só contagens)
- detalhes de deliberações / votos

## Contract test

`backend/tests/test_dashboard_routes.py::test_overview_no_pii` — walker recursivo do
payload que falha se encontrar qualquer chave da lista `FORBIDDEN_KEYS`
(`email`/`phone`/`member_id`/`name`/`cpf`/`password`/`photo_url`/`address`).
