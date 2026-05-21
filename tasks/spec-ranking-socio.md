# Spec — Ranking de Atuação do Sócio

> **Status**: rascunho técnico (2026-05-21). Spec de produto/engenharia, **não**
> parecer jurídico. Requer validação da Direcção/Mesa da AG nas regras com efeito
> social/reputacional (pesos da pontuação, visibilidade pública do ranking,
> opt-out) antes de implementar.
> **Objetivo**: dar à associação uma forma de **(1) registar**, **(2) ranquear**
> e **(3) mostrar** — no dashboard geral e no dashboard pessoal — a **atuação**
> (participação efectiva) dos sócios na vida associativa. Reconhece positivamente
> quem participa; nunca expõe quem não participa.
> **Estado do sistema**: ainda sem sócios reais em produção; **aditivo é o
> padrão**. Nenhuma migração destrutiva. A pontuação é **derivada** de sinais já
> registados (assiduidade a eventos, voto, mural, projectos, galeria, governança)
> — não inventa uma nova fonte de verdade.
> **Fundação já existente**: `GET /api/report/personal`
> (`backend/routes/report.py`) já agrega 8+ dimensões de participação de **um**
> utilizador, e o `DashboardPage.js` já as mostra no cartão "A Minha
> Participação" (linhas 460-544). Esta spec **generaliza** esse cálculo a todos
> os membros, pondera-o num *score* e ordena-o num ranking.

---

## 0. Âmbito e o que isto NÃO é

Esta spec cobre **três verbos**, na ordem do pedido:

| # | Verbo | Núcleo |
|---|---|---|
| 1 | **Registar** a atuação | derivar a pontuação de sinais já gravados + permitir **ajustes manuais** auditáveis (o que o sistema não "vê") |
| 2 | **Ranquear** os sócios | calcular um *score* ponderado por período e ordenar num leaderboard materializado |
| 3 | **Mostrar** | widget Top-N no dashboard geral, posição+breakdown no dashboard pessoal, página dedicada `/ranking` |

**O que isto NÃO é:**

- **Não é gamificação competitiva agressiva.** Enquadramento **positivo**:
  celebra os mais activos (Top-N, pódio, medalhas), não envergonha os menos
  activos. A pontuação detalhada (breakdown) é privada do próprio + admin.
- **Não mede mérito profissional nem disciplina.** Não toca `sancoes` nem
  `rights_suspended_until` como entrada de pontuação (a suspensão de direitos
  afecta voto, não atuação histórica).
- **Não usa quotas como pontuação.** Quotas são por desconto em folha (não há
  `inadimplente` — `spec-governanca-estatutaria` §14); pagar quota não é "atuação"
  meritória e **fica de fora do score** por princípio.
- **Não quebra o voto secreto.** Da eleição usa-se apenas a **comparência**
  (votou / não votou), nunca o sentido de voto (ver §3.3).
- **Não substitui** `report.personal` nem `stats`/`activity` — estende e reusa.

---

## 1. Specs e código relacionados (contrato de integração)

- **`backend/routes/report.py`** (`GET /api/report/personal`, implementado): a
  função de referência. Conta, para o utilizador actual: `events_attended`,
  `polls_voted`, `wall_posts`, `likes_received`, `wall_comments`,
  `projects_member`, `benefits_used`, `photos_approved/submitted`, documentos.
  **Esta spec extrai a lógica para um helper parametrizável por `user_id` e
  período** e adiciona pesos. `report.personal` passa a poder reusar o mesmo
  helper (sem regressão de contrato — os mesmos campos continuam a sair).
- **`backend/routes/stats.py`** (`GET /api/stats`, admin/financeiro): agregados
  globais do dashboard. O ranking vive ao lado, **não** dentro deste.
- **`backend/routes/activity.py`** (`GET /api/activity/recent`): feed de
  actividade recente — fonte de inspiração para iterar várias colecções e
  fundir/ordenar; **não** é pontuação.
- **`spec-identidade-cargos` / `governance.py`** (implementado): `account_type`
  (`member`/`technical`), `member_id`, `member_category`, `status`. O filtro
  canónico de membros reais já existe e **deve ser reusado**:
  `{"$or": [{"account_type": "member"}, {"account_type": {"$exists": False}}]}`
  (ver `routes/users.py:76`, `routes/assembleias.py:38`). Técnicos são excluídos
  do ranking (alinhado com CLAUDE.md: técnicos "excluded from … scoring").
- **`permissions.py`**: `user_can(user, priv)`, `is_direcao(user)` para o RBAC de
  configuração/ajustes. **Não** se usa `is_voting_member` para elegibilidade ao
  ranking (atuação ≠ direito de voto; honorário também atua — ver §2.3).
- **`helpers.py`**: `create_audit_log`, `create_notification`, `notify_users`,
  `notify_admins`. Toda a escrita audita.

**Princípio**: o ranking é **shippable de forma incremental** e degrada com
elegância — sem snapshot, o pessoal calcula-se ao vivo; o leaderboard só precisa
do snapshot quando houver muitos membros (ver §2.4).

---

## 2. Decisões transversais (arquitetura)

### 2.1 Pontuação **derivada**, não event-sourcing

A pontuação **não** grava um evento por cada acção (anti-padrão pesado e
duplicador — os sinais já estão nas colecções de origem). O *score* é a **soma
ponderada de contagens** sobre colecções existentes, calculada on-demand:

```
score(membro, período) = Σ_sinal (contagem_sinal × peso_sinal) + Σ ajustes_manuais
```

A única persistência nova de "registo" é:
1. **`ranking_ajustes`** — deltas manuais auditáveis (o "registar" do que o
   sistema não consegue inferir: "organizou a festa anual", "representou a ACCTA
   no congresso"). Positivos ou negativos, sempre com motivo e período.
2. **`member_scores`** — *cache materializada* do leaderboard (score+rank+breakdown
   por membro e período), reconstruída por um *rebuild* (§2.4). É **derivada e
   descartável** — pode ser apagada e reconstruída sem perda (não é fonte de
   verdade).
3. **`ranking_settings`** — doc único de configuração (pesos, visibilidade,
   ativação), editável por admin sem deploy (espelha o padrão de
   `brand_settings`/`finance_settings`).

### 2.2 Períodos

Atuação é **periodizada**. `period_key` é uma string simples:

- `"<ano>"` (ex.: `"2026"`) — ano civil; default do leaderboard (o dashboard já
  usa `currentYear`).
- `"all"` — desde sempre (sem filtro de data).

O filtro de período é um `$match` no carimbo temporal de cada sinal
(`created_at`/`date`). Membros novos só pontuam a partir da sua atividade.

### 2.3 Elegibilidade (quem é ranqueado)

Entram no ranking os utilizadores com **`account_type` membro** (ou ausente) —
**técnicos excluídos** (filtro canónico §1). Por `status`:

- `ativo` → ranqueado.
- `inativo` → **decisão em aberto** (default: incluído mas marcado "inativo"; não
  aparece no Top-N do dashboard).
- `pendente_*` / `rejeitado` → **excluídos** (ainda não são sócios de pleno).

**Categoria de membro é irrelevante** para entrar no ranking: honorário/fundador/
ordinário atuam todos. (Contraste com voto, onde `is_voting_member` exclui
honorário — aqui **não** se aplica.)

### 2.4 Estratégia de cálculo (frescura vs. custo)

| Vista | Fonte | Frescura |
|---|---|---|
| **Pessoal** (`GET /api/ranking/me`) | calculado **ao vivo** (1 membro, barato — reusa o helper de `report.personal`) | sempre fresco; rank lido do snapshot mais recente |
| **Leaderboard** (`GET /api/ranking/leaderboard`) | lê o snapshot `member_scores` | mostra `computed_at`; reconstruído por *rebuild* |

**Rebuild** (`POST /api/ranking/rebuild`, admin): recalcula `member_scores` para
um período. Corre **fora do request path** dos sócios. Mecanismo de agendamento
recomendado: um **script** `scripts/rebuild_ranking.py` invocável por cron
(coerente com `scripts/` existente; **não** introduzir scheduler in-process novo
agora). MVP pode ser só manual (botão admin) — ver fases (§10).

> **Nota de performance (DAO):** o `aggregate` do DAO faz `$match` em SQL e
> `$group/$count/$sort/$limit/$project` em Python sobre conjuntos limitados
> (`database.py`). Não há `$unwind`. Logo, sinais escalares (`user_votes.user_id`,
> `wall_comments.user_id`, `projects.created_by`, `gallery_photos.uploaded_by`,
> `assembleia_presencas.user_id`, `ranking_ajustes.user_id`) agregam-se com **um
> `$group` por colecção**; sinais de **pertença a array** (`events.attendees`,
> `wall_posts.likes`) tallam-se iterando os docs do período em Python (bounded).
> O rebuild é O(atividade), em lote — aceitável.

### 2.5 Privacidade e enquadramento (decisão sensível)

Um ranking público de atividade tem risco reputacional. Mitigações no design:

- **Dashboard geral**: só **Top-N** (default 5/10) — enquadramento positivo.
- **Página `/ranking`**: lista completa **ordenada por score** com `visibility`
  configurável em `ranking_settings`: `all_members` (default) | `direcao_only`.
- **Breakdown detalhado** (pontos por dimensão): só o **próprio** + admin.
- **Opt-out por membro** (`ranking_opt_out` em `users`, aditivo, default
  `false`): quem opta sai das listas públicas mas continua a ver a sua própria
  posição. **Decisão em aberto** (ver §13).
- O leaderboard mostra **nome + cargo + score + medalha**; nunca dados sensíveis.

### 2.6 Convenções comuns

- `created_at` ISO-8601 string; `created_by` em toda a escrita.
- Auditoria com `action` em snake_case: `ranking_settings_updated`,
  `ranking_adjustment_added`, `ranking_rebuilt`.
- Sem SQL cru nas rotas; índices em `ensure_schema()` (`database.py`).
- Datas sempre ISO-8601 string no `doc` (regra do projecto).

---

## 3. Modelo de pontuação (sinais e pesos)

### 3.1 Sinais e pesos default

Pesos **configuráveis** em `ranking_settings.weights` (defaults em
`backend/ranking.py`). Valores iniciais propostos (a validar pela Direcção):

| Chave (`weights`) | Sinal | Fonte | Peso |
|---|---|---|---|
| `assembleia_presenca` | presença em AGA | `assembleia_presencas` (`user_id`) | **10** |
| `eleicao_turnout` | votou numa eleição (só comparência) | `eleicao_voter_receipts` (via hash, §3.3) | **8** |
| `projeto_participacao` | criou / é responsável / tem tarefa | `projects` + `project_tasks` | **6** |
| `tarefa_concluida` | tarefa de projecto concluída | `project_tasks` (`assignee_id`, `status=concluido`) | **4** |
| `votacao_voto` | votou numa votação | `user_votes` (`user_id`) | **5** |
| `evento_presenca` | presente/RSVP em evento | `events.attendees` | **4** |
| `mural_post` | publicação aprovada | `wall_posts` (`approved=True`) | **3** |
| `galeria_foto` | foto aprovada | `gallery_photos` (`status=approved`) | **2** |
| `mural_comentario` | comentário | `wall_comments` | **1** |
| `mural_like_recebido` | like recebido (cap por período, §3.2) | `wall_posts.likes` | **0.5** |

**Excluído por decisão**: quotas/invoices (desconto em folha; §0). Documentos
acedidos (`document_accesses`) são **opt-in** e ficam fora do default (consumo
passivo ≠ atuação; ver §13).

### 3.2 Anti-gaming

- `mural_like_recebido` tem **cap por período** (`max_like_points_per_period`,
  default 50 pts) — evita farmar likes.
- `mural_post`/`mural_comentario` contam só **aprovados** (`approved=True`) —
  moderação já filtra spam.
- Ajustes manuais exigem `reason` e ficam auditados (não anónimos).
- Pesos e caps centralizados em `ranking_settings` → afinável sem deploy.

### 3.3 Comparência eleitoral **sem quebrar o voto secreto**

`eleicao_ballots` é anónimo; `eleicao_voter_receipts` guarda só
`voter_hash = HMAC-SHA256(SECRET_KEY, "{eleicao_id}:{user_id}")`
(`routes/eleicoes.py:64-67`). Como o hash é **determinístico a partir de
`(eleicao_id, user_id)`**, o rebuild pode confirmar **se** um membro votou numa
eleição (recomputa o hash e procura o recibo) **sem nunca** aceder ao boletim nem
ao sentido de voto. **Invariante a respeitar**: nunca cruzar `receipts` com
`ballots`; só se conta a comparência. (Implementação: por eleição do período,
carregar o conjunto de `voter_hash`; por membro, computar o seu hash e testar
pertença — N_membros × N_eleições hashes, barato.)

### 3.4 Fórmula (helper)

```python
# backend/ranking.py
DEFAULT_WEIGHTS = {  # ver tabela §3.1
    "assembleia_presenca": 10, "eleicao_turnout": 8, "projeto_participacao": 6,
    "tarefa_concluida": 4, "votacao_voto": 5, "evento_presenca": 4,
    "mural_post": 3, "galeria_foto": 2, "mural_comentario": 1,
    "mural_like_recebido": 0.5,
}
MAX_LIKE_POINTS = 50

async def compute_member_score(uid: str, period_key: str, weights: dict) -> dict:
    """Devolve {score: float, breakdown: {chave: {count, points}}}.
    Reusa as contagens de report.personal, parametrizadas por uid + período."""
    # counts = {sinal: contagem}  (com $match de data por period_key)
    # points_sinal = counts[sinal] * weights[sinal]  (like com cap)
    # ajustes = Σ ranking_ajustes(uid, period_key).delta
    # score = round(Σ points + ajustes, 1)
    ...
```

`compute_member_score` é a **única** fonte da pontuação; tanto o pessoal (ao
vivo) como o rebuild (em lote) a chamam — sem lógica duplicada.

---

## 4. Modelo de dados

Modelos novos em `backend/models.py` (ou `backend/ranking.py` co-localizado com
os pesos — decisão de arrumação; seguir o padrão de `governance.py` que
concentra domínio + constantes).

```python
class RankingAjuste(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str                 # membro pontuado
    period_key: str              # "2026" | "all"
    delta: float                 # +/-; pode ser negativo
    reason: str                  # obrigatório, auditável
    created_by: str              # admin/Direcção que registou
    created_at: str

class MemberScore(BaseModel):          # cache materializada (derivada)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    period_key: str
    score: float
    rank: int                          # 1 = topo (dentro do período)
    breakdown: dict                    # {chave: {"count": int, "points": float}}
    # snapshot de display (evita join no leaderboard)
    member_name: str
    member_id: Optional[str] = None
    cargo: Optional[str] = None
    photo_url: Optional[str] = None
    status: str                        # ativo/inativo
    computed_at: str

class RankingSettings(BaseModel):      # doc único
    weights: dict = Field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    max_like_points_per_period: int = 50
    visibility: Literal["all_members", "direcao_only"] = "all_members"
    top_n_dashboard: int = 5
    enabled: bool = True
    last_rebuild_at: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None
```

Aditivo em `UserBase` (`models.py`), default seguro:

```python
ranking_opt_out: bool = False   # NOVO — membro fora das listas públicas (§2.5)
```

> Alteração de Pydantic é **aditiva/opcional** → compatível com documentos
> existentes (não é stop condition). Backfill **não** necessário (default cobre).

---

## 5. Cálculo e rebuild

- **`compute_member_score(uid, period_key, weights)`** (§3.4): ao vivo para o
  pessoal; chamado em lote pelo rebuild.
- **`rebuild_scores(period_key)`** (em `backend/ranking.py`):
  1. Carrega membros elegíveis (filtro canónico §2.3).
  2. Pré-agrega sinais escalares com **um `$group` por colecção** (mapa
     `user_id → count`); tally em Python para `events.attendees`/`wall_posts.likes`;
     conjunto de `voter_hash` por eleição (§3.3).
  3. Por membro: `score`+`breakdown` (reusando os mapas pré-agregados).
  4. Ordena desc por score, atribui `rank` (empate → mesma `rank`, próxima salta).
  5. **Substitui** o snapshot do período (`delete_many(period_key)` →
     `insert_many`). Operação idempotente.
  6. Escreve `ranking_settings.last_rebuild_at`; `create_audit_log(..., "ranking_rebuilt", details={"period": period_key, "members": n})`.

---

## 6. Endpoints (`backend/routes/ranking.py`)

Novo módulo, `router = APIRouter(tags=["ranking"])`, `Depends(get_current_user)`,
RBAC explícito, auditoria nas escritas. Registar em `routes/__init__.py`
(`api_router.include_router(ranking_router)`) — fica sob `/api`.

| Método | Rota | Quem | Faz |
|---|---|---|---|
| GET | `/api/ranking/leaderboard?period=2026&limit=&offset=` | membro autenticado (respeita `visibility`) | lê `member_scores` do período; pagina; inclui `computed_at`, `total`, e a **linha do próprio** mesmo fora da página |
| GET | `/api/ranking/me?period=2026` | o próprio | score+rank+breakdown **ao vivo** (§2.4); inclui `total_members` p/ "#7 de 142" |
| GET | `/api/ranking/users/{user_id}?period=2026` | o próprio **ou** admin/Direcção | breakdown de um membro (privado — §2.5) |
| GET | `/api/ranking/settings` | admin/Direcção | devolve `ranking_settings` |
| PUT | `/api/ranking/settings` | admin (ou `manage_ranking`) | edita pesos/visibilidade/top_n; audita `ranking_settings_updated` |
| POST | `/api/ranking/adjustments` | admin/Direcção | regista `RankingAjuste`; audita `ranking_adjustment_added`; notifica o membro |
| GET | `/api/ranking/adjustments?user_id=&period=` | admin/Direcção (ou o próprio, só os seus) | lista ajustes |
| POST | `/api/ranking/rebuild?period=2026` | admin (ou `manage_ranking`) | corre `rebuild_scores`; audita `ranking_rebuilt` |

**Regras de visibilidade**: se `visibility=direcao_only`, `GET /leaderboard`
devolve 403 a quem não for Direcção/admin (o `GET /me` mantém-se sempre acessível
ao próprio). Membros com `ranking_opt_out=True` são omitidos das respostas
públicas (mas vêem o seu `/me`).

---

## 7. RBAC, auditoria, notificações

- **Ler leaderboard / me**: qualquer membro autenticado (sujeito a `visibility` e
  `opt_out`). Técnicos não aparecem (nem pontuam).
- **Configurar (settings/rebuild)**: `admin` ou privilégio aditivo novo
  **`manage_ranking`** (concedível à Direcção sem lhe dar admin). Adicionar
  `manage_ranking` à lista de privilégios em `governance.py`/permissões.
- **Ajustes manuais**: `admin` ou `is_direcao(user)` ou `manage_ranking`.
- **Auditoria** (snake_case): `ranking_settings_updated` (com diff de pesos),
  `ranking_adjustment_added` (`{user_id, delta, reason, period}`),
  `ranking_rebuilt` (`{period, members}`).
- **Notificações** (parcimoniosas, tipo reutilizado `"system"`):
  - membro recebe notificação quando lhe é registado um **ajuste manual**
    (transparência: "A Direcção registou +N pontos: <motivo>").
  - **Opcional/aberto**: avisar quem entra no Top-3 após um rebuild. Default
    **off** (evitar ruído) — ver §13.

---

## 8. Frontend

### 8.1 Dashboard geral — widget Top-N (`DashboardPage.js`)

Novo cartão **"Ranking de Atuação"** (visível a todos; enquadramento positivo),
ao lado de "A Minha Participação"/"Atividade Recente". Mostra **Top-N**
(`ranking_settings.top_n_dashboard`) com **medalha** para os 3 primeiros
(🥇/🥈/🥉 via ícone Lucide `Medal`/`Trophy`, **não** emoji — cor neutra + Carmesim
só no #1), nome, cargo, score e uma mini-barra proporcional. Linha do próprio
realçada se estiver no Top-N. Footer "Atualizado <computed_at>" + link "Ver
ranking completo →" para `/ranking`.

- Reusa o padrão de cartão branco (`bg-white border rounded-2xl`) e
  `StatCard`/`ChartCard` existentes; `Skeleton` no loading; `EmptyState`
  ("Ranking ainda não calculado") quando vazio.
- Query: `useQuery({ queryKey: queryKeys.ranking.leaderboard(period), queryFn })`,
  `enabled: rankingEnabled`.

### 8.2 Dashboard pessoal — posição + breakdown (estende "A Minha Participação")

O cartão "A Minha Participação" (linhas 460-544) ganha um **cabeçalho de
pontuação**: **score total**, **posição** ("#7 de 142") e **medalha** se Top-3.
Cada tile de dimensão passa a mostrar também os **pontos** que contribuiu
(`count × peso`), tornando o score **transparente** (o sócio percebe como
pontua). Dados de `GET /api/ranking/me` (ao vivo). Sem nova página — extensão do
que já existe.

### 8.3 Página dedicada `/ranking` (nova, `pages/private/RankingPage.js`)

- **Pódio** Top-3 + **tabela** completa: rank, nome, cargo, score, (badge
  inativo). Linha do próprio fixada/realçada. Pesquisa por nome. Paginação.
- **Filtro de período**: "Este ano" (`<ano>`) / "Sempre" (`all`).
- **Vista admin/Direcção** (gated por `isAdmin || isDirecao || hasPrivilege('manage_ranking')`):
  botão **"Recalcular"** (`POST /rebuild` + `toast` + `invalidateQueries`),
  **definições** (editar pesos/visibilidade/Top-N) e **registar ajuste** (modal:
  membro + delta + motivo).
- Respeita `visibility` (se `direcao_only`, a página redireciona sócios comuns
  para `/dashboard`, à semelhança do `ProtectedRoute`).

### 8.4 `utils/api.js`, `queryKeys`, rota, sidebar

```js
export const rankingAPI = {
  leaderboard: (params) => api.get('/ranking/leaderboard', { params }),
  me: (period) => api.get('/ranking/me', { params: { period } }),
  getUser: (userId, period) => api.get(`/ranking/users/${userId}`, { params: { period } }),
  getSettings: () => api.get('/ranking/settings'),
  updateSettings: (data) => api.put('/ranking/settings', data),
  addAdjustment: (data) => api.post('/ranking/adjustments', data),
  listAdjustments: (params) => api.get('/ranking/adjustments', { params }),
  rebuild: (period) => api.post('/ranking/rebuild', null, { params: { period } }),
};
```

- `lib/queryClient.js`: grupo novo `ranking` →
  `leaderboard(period)`, `me(period)`, `settings()`. Nunca chaves à mão.
- `App.js`: rota `/ranking` envolta em `<ProtectedRoute>` + `<PrivateLayout>`.
- `layouts/PrivateLayout.js` `menuSections`: item
  `{ label: 'Ranking', path: '/ranking', icon: Trophy, roles: ['all'] }`
  (secção "Painel" ou "Gestão").
- **Design**: sistema neutral-led; Carmesim como **único** acento (no #1,
  realce do próprio, botão primário ≤1 por vista); medalhas a neutro+Carmesim,
  nunca vermelho sobre fundo escuro/colorido; Open Sans; sem dark mode; seguir o
  skill `frontend-design`. `Skeleton` no loading, `EmptyState` em PT.
- **AuthContext** já expõe `isAdmin`, `isDirecao`, `hasPrivilege` para o gating.

---

## 9. Colecções e índices (consolidado)

Adicionar ao tuplo `COLLECTIONS` em `backend/database.py` e o DDL a `_INDEX_DDL`:

| Colecção | Índices mínimos |
|---|---|
| `member_scores` | unique `(user_id, period_key)`; `(period_key, rank)` (leaderboard ordenado/paginado) |
| `ranking_ajustes` | `(user_id, period_key)`; `created_at` DESC |
| `ranking_settings` | (doc único; sem índice além do default) |

Padrão DDL (ver `_INDEX_DDL` existente):
`CREATE [UNIQUE] INDEX IF NOT EXISTS ix_<t>_<f> ON "<t>" ((doc->>'<f>'))`. Para
ordenar o leaderboard: índice composto
`((doc->>'period_key'), (doc->>'rank'))`.

Nenhuma colecção de sinais é nova — todas já existem.

---

## 10. Plano de execução faseado

PRs pequenos, `feature/ranking-socio → develop` (GitFlow). Sem migração
destrutiva.

| Fase | Entrega | Depende |
|---|---|---|
| F0 | `backend/ranking.py` (pesos default + `compute_member_score`); refactor de `report.personal` para reusar o helper (sem mudar o contrato) + testes | — |
| F1 | `GET /api/ranking/me` (ao vivo) + extensão do cartão "A Minha Participação" (score+posição+pontos por tile) | F0 |
| F2 | Colecções (`member_scores`/`ranking_ajustes`/`ranking_settings`) + `rebuild_scores` + `POST /rebuild` + `GET /leaderboard` + widget Top-N no dashboard geral | F0 |
| F3 | Página `/ranking` (pódio, tabela, filtro de período, pesquisa) + sidebar + rota | F2 |
| F4 | Config admin/Direcção: `settings` (pesos/visibilidade), `adjustments` (registar ±), privilégio `manage_ranking` | F2 |
| F5 | Privacidade: `ranking_opt_out`, `visibility=direcao_only`; agendamento do rebuild (`scripts/rebuild_ranking.py` + cron) | F2 |

**Ordem dentro de cada fase**: models/constantes → schema/índices em
`ensure_schema()` → endpoints + RBAC + audit → testes backend → frontend
(página + api.js + queryKeys + sidebar) → testes frontend → verificação manual no
browser (golden path + edge cases).

---

## 11. Testes obrigatórios

**Backend (unit/in-process, `conftest.py`):** as colecções novas
(`member_scores`, `ranking_ajustes`, `ranking_settings`) e sinais como
`assembleia_presencas` **não estão pré-cabladas** no `mock_db` — cablar em-teste
(`mock_db.member_scores = MagicMock(...)` com `AsyncMock`s). Casos-chave:

- `compute_member_score`: soma ponderada correcta; cap de likes aplicado;
  ajustes (±) somados; período filtra por data (atividade fora do ano não conta);
  técnico devolve/é excluído.
- Comparência eleitoral: hash recomputado bate o recibo → conta; **nunca** toca
  `ballots`; sem recibo → não conta.
- `rebuild_scores`: ranks atribuídos desc; empates partilham rank; idempotente
  (correr 2× dá o mesmo snapshot); exclui `pendente_*`/`rejeitado`/técnicos.
- RBAC: `PUT /settings`, `/rebuild`, `/adjustments` exigem admin/Direcção/
  `manage_ranking` (403 ao sócio comum); `GET /users/{id}` 403 a terceiro
  não-admin; `visibility=direcao_only` ⇒ 403 no `/leaderboard` ao sócio.
- `opt_out`: membro com `ranking_opt_out=True` ausente do leaderboard mas o seu
  `/me` responde.
- **Não-regressão**: `GET /report/personal` mantém exactamente os mesmos campos.

**Frontend:** render+loading (Skeleton) do widget Top-N e da página `/ranking`;
empty state quando sem snapshot; medalhas no Top-3; realce da linha do próprio;
filtro de período troca a query; gating do menu/admin por role/privilégio; modal
de ajuste valida `reason` obrigatório.

---

## 12. Stop conditions (CLAUDE.md)

Confirmar com o utilizador antes de:

- **Tornar o ranking público** com efeito reputacional sem validação da Direcção
  (default seguro: Top-N positivo + breakdown privado + opt-out).
- Alterar Pydantic de forma **incompatível** com documentos existentes (tudo aqui
  é aditivo/opcional — `ranking_opt_out` tem default).
- **Migrar/limpar `users`** (não é preciso; default cobre o backfill).
- Remover/alterar o contrato de `GET /report/personal` (o frontend usa-o no
  dashboard) — o refactor F0 **mantém** o contrato.
- Enviar emails reais (esta spec **não** envia email; usa só notificações
  in-app).
- Tratar a pontuação como tendo qualquer efeito estatutário/eleitoral — é
  **reconhecimento informal**, não confere direitos.

---

## 13. Decisões em aberto

1. **Visibilidade pública**: leaderboard completo visível a todos os membros
   (recomendado, transparência) ou só Direcção/admin (`direcao_only`)?
2. **Opt-out por membro** (`ranking_opt_out`): existe (recomendado, respeita
   privacidade) ou ranking é sempre completo?
3. **`status=inativo`**: incluído marcado (recomendado) ou excluído do ranking?
4. **Pesos**: a tabela §3.1 são valores iniciais — a Direcção valida/ajusta.
   Em particular o peso alto de AGA/eleição vs. mural.
5. **Documentos acedidos** como sinal opt-in (consumo passivo) — incluir com peso
   baixo ou manter fora (recomendado: fora)?
6. **Agendamento do rebuild**: manual (botão) só, ou cron nightly via
   `scripts/rebuild_ranking.py` (recomendado quando houver volume)?
7. **Notificação de Top-3** após rebuild: ligar (gamificação) ou manter off
   (recomendado, evitar ruído)?
8. **Períodos**: só ano civil + "sempre" (recomendado) ou também trimestral/
   mensal?
9. **Arrumação**: `member_scores` como cache materializada (recomendado, escala)
   ou cálculo 100% ao vivo também no leaderboard (mais simples, só viável com
   poucos membros)?
