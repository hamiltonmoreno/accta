# Spec — Controlos Financeiros Estatutários (Categoria 4) — CONCLUÍDA

> ## ✅ Estado actual (2026-05-28)
>
> Spec **CONCLUÍDA** no que toca a código de F0–F4 (`develop`). Pendências são
> **operacionais** (Tesouraria) ou **deliberativas** (AG), não de engenharia.
>
> **Implementado:**
> - **F0** — `permissions.is_direcao` / `is_presidente` / `is_tesoureiro` (key-based,
>   delegando em `governance.py`); aditivos em `UserBase`
>   (`cta_qualified_since`, `joia_devida`, `joia_isento`), `Transaction.ato_id`,
>   `FinanceSettings.joia_multiplier`/`joia_amount`/`coaprovacao_limiar`.
> - **F1 (4.2)** — `INCOME_CATEGORIES` alinhadas ao Art. 5; endpoint
>   `GET /api/finances/meta/categories`; `scripts/migrate_income_categories.py`
>   (`--dry-run`/`--apply`); decisão dono: `patrocinios → donativos`.
> - **F2 (4.3)** — `finance_joia.py` (compute_joia, joia_status) com isenções
>   fundador/honorário; integrado em `routes/admin.py` (`approve_registration`,
>   convite); endpoint `GET /api/finances/joia/preview`.
> - **F3 (4.1)** — `routes/atos.py` (`POST /api/atos`, `/list`, `/{id}`,
>   `/{id}/assinar`, `/{id}/executar`, `/{id}/cancelar`); regra estatutária
>   pura em `atos_rules.py`; gate de pagamentos em `finances.py`
>   (`coaprovacao_limiar`).
> - **F4 frontend** — `CoAprovacoesPage.js`, `AdminPedidosInscricaoPage` com
>   bloco de jóia, `AuthContext.isDirecao`/`isPresidente`/`isTesoureiro`,
>   `useFinanceCategories` (lê do endpoint meta, sem hard-code).
>
> **Testes:** `test_atos.py` (~33) + `test_joia.py` (~22) ✅;
> `useFinanceCategories.test.js` (4) ✅.
>
> **Pendências NÃO-código (operador/AG):**
> 1. **F5** — correr `scripts/migrate_income_categories.py --apply` em prod
>    (STOP: confirmação humana antes).
> 2. **`coaprovacao_limiar`** — definir valor inicial em `FinanceSettings`
>    (decisão de governança/Tesouraria; default `0.0` ⇒ regra inactiva).
> 3. **Alterar `quota_amount`/`joia_multiplier`** — exige deliberação de AG
>    (3/4) por desenho.
>
> **Follow-ups conhecidos (não bloqueiam o uso):**
> - Materializar `cta_qualified_since` para sócios existentes (script de
>   normalização, opcional).
> - `cargo_history` para `ato_id` no audit/UI (rastrear quem assinou actos
>   históricos por mandato).
> - Mover `CATEGORY_LABELS` de `financeiro/constants.js` para o hook (depois
>   da migração `--apply`, podem-se eliminar as keys legadas).

---

> **Status**: rascunho técnico (2026-05-21). Requer validação da Direcção/
> Tesouraria/CF nas regras com efeito estatutário (quem assina o quê, isenções de
> jóia, alinhamento de categorias). Spec de produto/engenharia, **não** parecer
> jurídico/contabilístico.
> **Objetivo**: implementar os controlos financeiros do estatuto — **dupla
> assinatura/co-aprovação** de actos que vinculam a ACCTA, **categorias de receita
> estatutárias** e **cálculo automático da jóia** (2× quota) na admissão.
> **Estado do sistema**: sem dados reais; aditivo é o padrão. Alterar categorias
> de transacções existentes e qualquer migração de dados é **stop condition**.
> **Base estatutária**: Art. 54 (dupla assinatura: 2 da Direcção incl. Presidente;
> pagamentos exigem o Tesoureiro), Art. 5 (categorias de receita), Art. 6 (jóia =
> 2× quota para CTA qualificado há >4 meses). `source_article` em cada regra.

---

## 0. Âmbito

As **3 funcionalidades** da Categoria 4:

| # | Funcionalidade | Artigo |
|---|---|---|
| 4.1 | Dupla assinatura / co-aprovação (workflow de 2 confirmações) | 54 |
| 4.2 | Categorias de receita estatutárias | 5 |
| 4.3 | Cálculo automático da jóia (2× quota) na admissão | 6 |

---

## 1. Specs relacionadas e dependências

- **`tasks/spec-governanca-estatutaria.md` §14** (planeado): já desenha a jóia —
  `FinanceSettings.joia_multiplier = 2.0`, `joia_amount`, `finance_settings_history`,
  e a regra de que **alterar quota/jóia exige deliberação de AG (3/4)**. A 4.3
  **implementa essa jóia** + a condição do Art. 6 (CTA >4 meses). **Reconciliar**,
  não duplicar.
- **`tasks/spec-identidade-cargos.md`** (implementado): `cargo` + `CARGOS_ORGAOS_SOCIAIS`
  são a fonte de verdade de órgão/cargo **hoje** (por label). A 4.1 usa-os.
- **`tasks/spec-auto-registo.md`** (implementado): a 4.3 liga-se ao
  `approve_registration` (e ao convite por admin) para assinalar a jóia devida.
- **`tasks/spec-ciclo-prestacao-contas.md`** (Categoria 3): a jóia entra como
  receita (`category="joias"`) nos balancetes/DRE; os atos de pagamento ligam-se a
  transacções de despesa.

---

## 2. Diagnóstico do estado actual

Verificado no código (2026-05-21):

- **Órgãos por label**: `CARGOS_ORGAOS_SOCIAIS["Direcção"] = ["Presidente",
  "Vice-Presidente", "Secretário-Geral", "Tesoureiro", "Vogal da Direcção"]`.
  Hoje o **Presidente** = `cargo=="Presidente"`, o **Tesoureiro** =
  `cargo=="Tesoureiro"`, **membro da Direcção** = `cargo in
  CARGOS_ORGAOS_SOCIAIS["Direcção"]`. **Não há** `is_direcao`/`is_tesoureiro` nem
  co-aprovação.
- **Categorias de receita**: `INCOME_CATEGORIES = ["quotas", "patrocinios",
  "doacoes", "eventos", "outros_receita"]` — **não alinhadas ao estatuto**.
  Validadas ao nível da rota (`finances.py`), não como `Literal` Pydantic.
- **`FinanceSettings`**: `quota_amount`, `quota_description`, `updated_at`,
  `updated_by` — **sem `joia_multiplier`/`joia_amount`**.
- **`UserBase`**: tem `admission_date`, `account_type`, `cargo`, `license_number`
  — **sem `member_category`, sem data de qualificação CTA, sem campo de jóia**.
- **Transacção**: `type/category/amount/date/reference/user_id/created_by` — sem
  `status` nem ligação a aprovação.

---

## 3. Decisões transversais (arquitetura)

1. **Módulos**: `backend/routes/atos.py` (4.1). A 4.2 e 4.3 tocam `models.py`,
   `routes/finances.py` e `routes/auth_routes.py` (hook de admissão). Esqueleto da
   casa; `create_audit_log` em toda a escrita; datas ISO-8601; sem SQL nas rotas
   (regras em `.claude/rules/`).
2. **Helpers de órgão (hoje, por label)** em `auth.py`/`permissions.py`:
   ```python
   def is_direcao(user) -> bool:      return user.cargo in CARGOS_ORGAOS_SOCIAIS["Direcção"]
   def is_presidente(user) -> bool:    return user.cargo == "Presidente"
   def is_tesoureiro(user) -> bool:    return user.cargo == "Tesoureiro"
   ```
   Migram para as **keys** da governança (`dir_presidente`, `dir_tesoureiro`,
   `orgao==direcao`) quando esse spec for implementado — encapsular para trocar num
   só sítio.
3. **Categorias**: alinhar `INCOME_CATEGORIES` ao Art. 5 + mapa de **alias legado**
   + **script de migração** (confirmar antes de `--apply`). Expor as categorias +
   labels por endpoint meta (o frontend não hard-codeia).
4. **Jóia**: estender `FinanceSettings` com `joia_multiplier` (=2.0, alinhado à
   governança §14) e adicionar `cta_qualified_since` (aditivo) a `UserBase`. A jóia
   é **assinalada na admissão** e **cobrada** como receita no financeiro.
5. **Co-aprovação liga-se a pagamentos**: pagamentos acima de um limiar
   configurável exigem um **ato aprovado** antes de a despesa ser registada;
   campo aditivo `ato_id` na `Transaction` para rastreio.
6. **Aditivos/opcionais**: todas as alterações de Pydantic (`joia_multiplier`,
   `cta_qualified_since`, `ato_id`) são aditivas/opcionais → não quebram
   documentos existentes.

---

## 4. Feature 4.1 — Dupla assinatura / co-aprovação (Art. 54)

**Resumo**: actos que vinculam a ACCTA exigem **2 membros da Direcção (um deles o
Presidente)** e os **pagamentos exigem a assinatura do Tesoureiro**; vira um
workflow de aprovação com 2 confirmações.

### 4.1.1 Modelo de dados — colecção `atos`

```python
class Ato(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tipo: Literal["vinculativo", "pagamento"]
    descricao: str
    valor: Optional[float] = None
    beneficiario: Optional[str] = None
    requisitos: dict                 # snapshot da regra no momento da criação
    assinaturas: list[dict] = []      # {user_id, cargo, decisao: "aprovado"|"rejeitado", signed_at}
    status: Literal["pendente", "aprovado", "rejeitado", "executado", "cancelado"] = "pendente"
    transaction_id: Optional[str] = None   # despesa criada ao executar (pagamento)
    created_by: str
    created_at: str
    source_article: str = "54"
```

`requisitos` (computado de `tipo`, configurável):

```python
# vinculativo
{"min_direcao": 2, "exige_presidente": True, "exige_tesoureiro": False}
# pagamento (vincula + sai dinheiro): default estatutário
{"min_direcao": 2, "exige_presidente": True, "exige_tesoureiro": True}
```

### 4.1.2 Regra de aprovação

`status="aprovado"` quando as `assinaturas` com `decisao="aprovado"` satisfazem
**todos** os `requisitos`:
- `≥ min_direcao` assinantes com `is_direcao`,
- pelo menos um com `is_presidente` (se `exige_presidente`),
- o Tesoureiro assinou (se `exige_tesoureiro`).

Qualquer `decisao="rejeitado"` ⇒ `status="rejeitado"`. Um utilizador não assina
duas vezes (índice/validação). **O Presidente conta também como 1 dos 2 da
Direcção.**

### 4.1.3 Endpoints (`routes/atos.py`)

- `POST /api/atos` (Direcção/Tesoureiro/admin) — cria (`pendente`), congela
  `requisitos`.
- `GET /api/atos` (com filtro `?pendentes_para_mim`), `GET /api/atos/{id}`.
- `POST /api/atos/{id}/assinar` `{decisao}` — assina; recalcula `status`.
- `POST /api/atos/{id}/executar` (Tesoureiro/admin, só se `aprovado` e
  `tipo=pagamento`) — cria a despesa (`Transaction` `type="despesa"`,
  `ato_id=<id>`), marca `executado`.
- `POST /api/atos/{id}/cancelar` (proponente/admin, se `pendente`).

**Integração com pagamentos**: uma despesa `> coaprovacao_limiar` (config em
`FinanceSettings`) só é registada via `executar` de um ato aprovado; abaixo do
limiar segue o fluxo directo de `finances.py`. `ato_id` aditivo na `Transaction`.

### 4.1.4 RBAC, notificações, auditoria

- Criar: Direcção/Tesoureiro/admin. Assinar: quem cumpre um requisito
  (`is_direcao`/`is_presidente`/`is_tesoureiro`). Executar: Tesoureiro/admin.
- Audit: `ato_criado`, `ato_assinado`, `ato_aprovado`, `ato_rejeitado`,
  `ato_executado`, `ato_cancelado`.
- Notif. (`"finance"`): aos assinantes requeridos quando criado; ao proponente
  quando aprovado/rejeitado.

### 4.1.5 Frontend

Página/aba `/financeiro/co-aprovacoes`: lista de atos **à minha assinatura** +
todos; criar ato (tipo, descrição, valor, beneficiário); cartão de assinaturas com
estado ("Direcção 1/2 · Presidente em falta · Tesoureiro ✓"); botões Assinar
(Aprovar/Rejeitar) e Executar. `utils/api.js`: `atosAPI`.

### 4.1.6 Critérios de aceitação

Ato vinculativo só aprova com 2 da Direcção incl. Presidente; pagamento exige
também o Tesoureiro; assinante duplicado bloqueado; despesa acima do limiar exige
ato aprovado; `executar` cria a despesa ligada só após `aprovado`.

---

## 5. Feature 4.2 — Categorias de receita estatutárias (Art. 5)

**Resumo**: alinhar as categorias de receita às do estatuto — quotas, jóias,
subvenções, donativos, venda de publicações, juros e extraordinárias.

### 5.1 Constantes (models.py)

```python
INCOME_CATEGORIES = [
    "quotas", "joias", "subvencoes", "donativos",
    "venda_publicacoes", "juros", "extraordinarias",
]
INCOME_CATEGORY_LABELS = {
    "quotas": "Quotas", "joias": "Jóias", "subvencoes": "Subvenções",
    "donativos": "Donativos", "venda_publicacoes": "Venda de Publicações",
    "juros": "Juros", "extraordinarias": "Receitas Extraordinárias",
}
```

`EXPENSE_CATEGORIES` mantém-se (o Art. 5 trata de receitas).

### 5.2 Migração de categorias legadas

Mapa de alias (recomendado; `patrocinios` é decisão em aberto):

```python
LEGACY_INCOME_ALIASES = {
    "doacoes": "donativos",
    "eventos": "extraordinarias",
    "outros_receita": "extraordinarias",
    "patrocinios": "donativos",   # ou "extraordinarias" — confirmar
}
```

Script `scripts/migrate_income_categories.py` (`--dry-run`/`--apply`): renomeia
`transactions.doc.category` legadas para estatutárias. **Confirmar antes de
`--apply`** (altera dados). `GET /finances/summary` e `/dre` agrupam por categoria
dinamicamente ⇒ toleram a transição. `generate-quotas` continua `category="quotas"`.

### 5.3 Endpoints e validação

- A validação de `category` em `finances.py` passa a usar as novas
  `INCOME_CATEGORIES`.
- Novo `GET /api/finances/meta/categorias` (autenticado) → `{income: [...],
  expense: [...], labels: {...}}` para o frontend não hard-codear (padrão dos
  endpoints `/meta`).

### 5.4 Frontend e critérios

O dropdown de categoria de receita usa o endpoint meta + labels. Critérios: criar
receita só aceita categorias estatutárias; legadas migradas; DRE/summary agrupam
pelas novas; frontend sem hard-code de categorias.

---

## 6. Feature 4.3 — Cálculo automático da jóia (Art. 6)

**Resumo**: ao admitir um membro já qualificado como CTA há **mais de 4 meses**, o
sistema calcula a jóia como **2× a quota em vigor**.

### 6.1 Modelo de dados

- Estender `FinanceSettings` (aditivo, alinhado à governança §14):
  ```python
  joia_multiplier: float = 2.0
  joia_amount: Optional[float] = None    # se definido, sobrepõe o múltiplo
  coaprovacao_limiar: float = 0.0         # 4.1: pagamentos acima exigem ato
  ```
- Adicionar a `UserBase` (aditivo, opcional):
  ```python
  cta_qualified_since: Optional[str] = None   # ISO date; quando se qualificou como CTA
  joia_devida: Optional[float] = None          # assinalada na admissão
  joia_isento: Optional[bool] = None           # fundador/honorário/decisão
  ```

### 6.2 Regra (Art. 6)

```python
def compute_joia(user_doc, settings) -> Optional[float]:
    if user_doc.get("joia_isento"):                      return None
    if user_doc.get("member_category") == "fundador":    return None   # (governança)
    since = user_doc.get("cta_qualified_since")
    if not since:                                         return None   # flag manual
    if (now - parse(since)) <= 4 meses:                   return None
    return settings.joia_amount or settings.joia_multiplier * settings.quota_amount
```

Usa **sempre a quota em vigor** (`quota_amount`). Fundadores e quem não tiver
`cta_qualified_since` ficam isentos/marcados para decisão manual.

### 6.3 Hook na admissão + cobrança

- No `approve_registration` (auto-registo) e no convite por admin: calcular
  `compute_joia` e gravar `joia_devida` no utilizador (assinalar, não cobrar).
- `GET /api/finances/joia/preview?user_id=...` (admin) — calcula sem gravar, para
  pré-visualizar no modal de aprovação.
- **Cobrança**: o Tesoureiro lança a receita da jóia (`Transaction`
  `type="receita"`, `category="joias"`, `user_id=<membro>`). A jóia em si pode ser
  paga em folha (como as quotas) — sem `inadimplente` (invariante do projecto).

### 6.4 RBAC, notificações, auditoria, frontend

- Cálculo no fluxo de admissão (admin). Lançar receita: Tesoureiro/`manage_finances`.
- Audit: `joia_calculada`, `joia_lancada`.
- Frontend: no modal de aprovação (`AdminPedidosInscricaoPage`) mostrar "Jóia
  devida: X CVE (2× quota)" quando aplicável; campo para `cta_qualified_since`.
- Critérios: jóia = 2× quota para CTA >4 meses não-fundador; fundador/sem-dados →
  isento/manual; usa a quota vigente; alterar `joia_multiplier`/`quota_amount`
  exige deliberação de AG (governança §14).

---

## 7. Colecções e índices

| Colecção | Índices mínimos |
|---|---|
| `atos` (4.1) | `status`; `(status, created_at)`; `tipo` |

Sem colecção nova para 4.2/4.3. Campos aditivos: `Transaction.ato_id`;
`FinanceSettings.joia_multiplier`/`joia_amount`/`coaprovacao_limiar`;
`UserBase.cta_qualified_since`/`joia_devida`/`joia_isento`. A receita de jóia é uma
`transactions` normal (`category="joias"`).

---

## 8. Frontend (consolidado)

- **Co-aprovações** (`/financeiro/co-aprovacoes`): atos pendentes à minha
  assinatura, criar/assinar/executar, cartão de estado das assinaturas.
- **Categorias** (4.2): dropdowns de receita via `GET /finances/meta/categorias`
  + labels; sem hard-code.
- **Jóia** (4.3): bloco no modal de aprovação de pedido + campo
  `cta_qualified_since`; receita de jóia visível no Financeiro.
- `AuthContext`: `isDirecao`, `isPresidente`, `isTesoureiro` (espelho do backend).
- Design neutral-led + Carmesim, sem dark mode; estados de assinatura com badges
  claros. `utils/api.js`: `atosAPI`, extensão de `financasAPI` (joia preview, meta).

---

## 9. Plano de execução faseado

PRs pequenos, `feature/* → develop`.

| Fase | Entrega | Depende |
|---|---|---|
| F0 | Helpers `is_direcao`/`is_presidente`/`is_tesoureiro`; aditivos de `FinanceSettings`/`UserBase`/`Transaction` | — |
| F1 | **4.2** Categorias estatutárias + endpoint meta + script de migração (dry-run) | F0 |
| F2 | **4.3** Jóia (FinanceSettings + compute_joia + hook de admissão + preview) | F0 |
| F3 | **4.1** Co-aprovação (`atos`, assinar, executar, gate de pagamentos) | F0 |
| F4 | Frontend (co-aprovações, dropdowns por meta, bloco de jóia) | F1–F3 |
| F5 | Migração real das categorias (`--apply`) + reconciliação com governança §14 (deliberação 3/4 p/ quota/jóia) | F1 + confirmação |

### Ordem dentro de cada fase

Models/campos → schema/índices (`ensure_schema`) → endpoints + RBAC + audit →
testes backend → frontend → testes frontend → verificação manual (criar e assinar
um ato; aprovar um pedido com jóia; criar receita nas categorias novas).

---

## 10. Testes obrigatórios

- 4.1: ato vinculativo aprova só com 2 Direcção incl. Presidente; pagamento exige
  Tesoureiro; rejeição fecha; assinante duplicado bloqueado; despesa > limiar sem
  ato aprovado é recusada; `executar` cria a despesa ligada.
- 4.2: criar receita só aceita categorias estatutárias; alias legado migra
  (dry-run reporta); DRE/summary agrupam pelas novas; meta endpoint devolve labels.
- 4.3: jóia = 2× quota p/ CTA >4 meses; fundador/sem `cta_qualified_since`
  isento/manual; usa `quota_amount` vigente; `joia_amount` sobrepõe o múltiplo;
  preview não grava.
- RBAC: matriz Direcção/Presidente/Tesoureiro/CF/admin por endpoint.

Frontend: cartão de assinaturas (estados parciais); dropdown de categorias por
meta; bloco de jóia no modal de aprovação; gating por `isTesoureiro`/`isDirecao`.

---

## 11. Stop conditions (CLAUDE.md)

Confirmar com o utilizador antes de:

- Executar a **migração de categorias** (`--apply`) em `transactions` (altera
  dados existentes).
- Alterar `quota_amount`/`joia_multiplier` (exige deliberação de AG — governança §14).
- Alterar Pydantic para além de campos aditivos/opcionais.
- Enviar emails reais; remover rotas que o frontend chama.

---

## 12. Decisões em aberto

1. **`patrocinios` (legado)** mapeia para `donativos` (recomendado) ou
   `extraordinarias`?
2. **Limiar de co-aprovação** (`coaprovacao_limiar`): todos os pagamentos exigem
   ato, ou só acima de um valor? Qual o default?
3. **Pagamento que não vincula** existe? Ou todo o pagamento implica a regra
   vinculativa (2 Direcção incl. Presidente) **e** o Tesoureiro (default
   estatutário aplicado)?
4. **Pode o proponente do ato** ser também um dos assinantes/aprovadores?
5. **Qualificação CTA**: campo dedicado `cta_qualified_since` (recomendado) ou
   derivar de `license_number`/`admission_date`?
6. **Isenções de jóia** além de fundador: honorários (Categoria 1) também isentos?
7. **Cobrança da jóia**: lançada automaticamente como receita pendente na
   aprovação, ou só assinalada e lançada manualmente pelo Tesoureiro (recomendado)?
8. **`atos` vs. integração directa**: actos vinculativos não-pagamento (contratos)
   ficam só registados, ou geram também documento/anexo?
