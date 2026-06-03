# Spec — Ciclo Anual de Prestação de Contas (Categoria 3)

> **Status**: rascunho técnico (2026-05-21). Requer validação da Direcção/
> Conselho Fiscal/Mesa da AG nas regras com efeito estatutário (competências de
> aprovação, prazos do 1.º trimestre, maiorias). Spec de produto/engenharia,
> **não** parecer jurídico/contabilístico.
> **Objetivo**: dar ao portal o **ciclo anual guiado** de prestação de contas —
> Relatório e Contas + Parecer do Conselho Fiscal + Orçamento + Plano à AG
> ordinária do 1.º trimestre, balancetes periódicos e balanço anual do
> Tesoureiro (com auditoria do CF aos documentos de despesa), e um repositório
> **versionado** de Regulamentos Internos com fluxo de aprovação.
> **Estado do sistema**: sem dados reais; aditivo é o padrão. Mexer em `users`/
> dados financeiros é stop condition.
> **Base estatutária**: Art. 19.1 (AG ordinária aprova contas), 31.k (Direcção
> apresenta relatório/contas/orçamento), 37 (relatório/contas e parecer do CF),
> 34 (CF fiscaliza, confere documentos), 31.j + 56 (regulamentos internos /
> Regimento). Cada regra sensível guarda `source_article`.

---

## 0. Âmbito

As **3 funcionalidades** da Categoria 3:

| # | Funcionalidade | Artigo |
|---|---|---|
| 3.1 | Relatório e Contas + Parecer do CF + Orçamento + Plano (ciclo guiado) | 19.1, 31.k, 37 |
| 3.2 | Balancetes periódicos + balanço anual (Tesoureiro publica, CF audita) | 34, 37 |
| 3.3 | Regulamentos Internos versionados (incl. o Regimento da AG) | 31.j, 56 |

**Não-objectivos**: não redefine **categorias de receita estatutárias**, **jóia**
nem **dupla assinatura** — isso é a Categoria 4 (`spec` futuro). Reusa as
categorias e o módulo financeiro **actuais** e liga-se a essas regras quando
existirem.

---

## 1. Specs relacionadas e dependências

- **`tasks/spec-governanca-estatutaria.md`** (planeado): fornece a `Assembleia`
  (§11) e a **AG ordinária** (uma vez por ano, 1.º trimestre) com deliberações.
  A **aprovação** do Relatório e Contas (3.1) é uma `AssembleiaDeliberacao` da AG
  ordinária — **dependência**. Também define `is_direcao`, `is_conselho_fiscal`,
  `is_mesa_ag` e `view_finances_readonly` (já implementado).
- **`tasks/spec-sessao-assembleia-ao-vivo.md`** (Categoria 2): o pacote do
  exercício (relatório, contas, parecer, orçamento, plano) entra como
  **documentos da sessão** (≥3 dias) e **pontos da ordem de trabalhos** da AG
  ordinária.
- **Módulo financeiro actual** (reaproveitado, ver §2): `transactions`,
  `GET /finances/summary`, `GET /finances/dre`, RBAC `can_view_finances`/
  `can_manage_finances`, documentos + Transparência pública.

---

## 2. Diagnóstico do estado actual

Verificado no código (2026-05-21):

**Existe:**
- `Transaction` (`models.py`): `type` (`receita`/`despesa`), `category`,
  `description`, `amount` (>0), `date`, `reference`, `user_id?`, `created_by`,
  `created_at`. Categorias fixas: `INCOME_CATEGORIES`, `EXPENSE_CATEGORIES`.
- `FinanceSettings` singleton (`quota_amount`, `quota_description`).
- `routes/finances.py`: CRUD de transacções; `GET /finances/summary`
  (`total_receitas/despesas/resultado_liquido` + por categoria);
  `GET /finances/dre?year` (mensal + por categoria) e `GET /finances/dre/pdf`;
  `POST /finances/generate-quotas`; export CSV. RBAC: `require_view_finances`
  (admin/financeiro/`view_finances_readonly`/`manage_finances`) nos GET;
  `require_manage_finances` (admin/financeiro/`manage_finances`; **CF não
  escreve**) nas escritas.
- `Document` (`type` livre — inclui `balancete`/`plano`/`relatorio`/`financeiro`;
  `visibility` `publico|socios|direcao|privado`; `tags`); upload
  `/upload/documents` (10 MB, admin/`manage_documents`); download público
  `/api/documents/{id}/public/download`; **Transparência** filtra `balancete`/
  `plano` como "relatórios".

**Não existe (a construir):**
- Objecto de **exercício/ciclo anual** (nada amarra relatório+parecer+orçamento+
  plano+aprovação).
- **Parecer do CF** — sem modelo nem endpoint.
- **Balancete/balanço como entidade** — hoje é só um *tipo* de documento; o
  `summary`/`dre` calcula números mas não há balancete publicado/auditado.
- **`proof_url`** na transacção (o CF não tem como conferir o documento de
  despesa a partir da transacção).
- **Versionamento** — inexistente em todo o código (grep vazio). Regulamentos
  versionados são net-new.

---

## 3. Decisões transversais (arquitetura)

1. **Espinha = exercício anual**: colecção `exercicios` (um por ano) é a máquina
   de estados que **guia** 3.1. Balancetes (3.2) referenciam o `exercicio_ano`.
2. **Módulos**: `backend/routes/prestacao_contas.py` (3.1 + 3.2) e
   `backend/routes/regulamentos.py` (3.3). Esqueleto da casa (`routes/polls.py`),
   `current_user = Depends(get_current_user)`, RBAC explícito, `create_audit_log`
   em toda a escrita, datas ISO-8601 (regras em `.claude/rules/api.md`).
3. **Parecer é escrita do CF sem escrita financeira**: o CF tem
   `view_finances_readonly` (não pode mexer em transacções), mas **pode emitir
   parecer e auditar balancetes**. Novo capability gated por
   `is_conselho_fiscal(user)` (ou privilégio `emit_cf_parecer`), **separado** de
   `manage_finances` (separação de poderes mantida).
4. **Reusar os números existentes**: o Relatório e Contas e os balancetes fazem
   *snapshot* de `GET /finances/summary` / `GET /finances/dre` — não recalcular
   noutro sítio.
5. **`proof_url` aditivo** na `Transaction` (Optional) para o CF conferir
   documentos de despesa. Aditivo/opcional ⇒ não quebra documentos existentes
   (não é stop condition), mas regista-se a alteração de Pydantic.
6. **Aprovação via AG**: 3.1 (contas) e os regulamentos de competência da AG
   ligam-se a `AssembleiaDeliberacao` (governança). Interim (sem Assembleia):
   guardar `assembleia_id`/`deliberacao_id` como `Optional` e permitir registo
   manual do resultado pela Mesa/admin.
7. **Transparência**: documentos aprovados (relatório, balanço, regulamentos)
   ficam públicos pelo fluxo de documentos existente (`public/download`); o
   balancete pode expor também um *snapshot* inline (decisão em aberto).
8. **Notificações/Auditoria**: tipo `"finance"` para avisos do ciclo; auditoria
   snake_case (ex.: `relatorio_contas_submetido`).

---

## 4. Feature 3.1 — Relatório e Contas + Parecer do CF + Orçamento + Plano (Art. 19.1, 31.k, 37)

**Resumo**: ciclo anual guiado — a Direcção submete relatório e contas, o
Conselho Fiscal anexa o parecer, e tudo vai à AG ordinária do 1.º trimestre para
aprovação.

### 4.1 Modelo de dados — colecção `exercicios`

```python
class Exercicio(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ano: int                                  # exercício económico
    status: Literal[
        "aberto", "relatorio_submetido", "parecer_emitido",
        "em_aprovacao_ag", "aprovado", "rejeitado", "reaberto"
    ] = "aberto"
    relatorio_contas: Optional[dict] = None   # {document_id, dre_snapshot, submitted_by, submitted_at}
    orcamento: Optional[dict] = None          # {document_id, submitted_by, submitted_at}  (ano seguinte)
    plano_atividades: Optional[dict] = None   # {document_id, submitted_by, submitted_at}
    parecer_cf: Optional[dict] = None         # ver ParecerCF
    assembleia_id: Optional[str] = None       # AG ordinária do 1.º trimestre
    deliberacao_id: Optional[str] = None      # deliberação que aprova
    aprovado_em: Optional[str] = None
    created_at: str
    source_article: str = "37"
```

`ParecerCF` (embebido em `exercicios.parecer_cf`):

```python
class ParecerCF(BaseModel):
    document_id: Optional[str] = None
    sentido: Literal["favoravel", "favoravel_com_reservas", "desfavoravel"]
    texto: str
    emitted_by: str                            # membro do CF
    emitted_at: str
```

`dre_snapshot` = resultado de `GET /finances/dre?year=<ano>` congelado no momento
da submissão (auditabilidade — os números não mudam depois).

### 4.2 Máquina de estados (ciclo guiado)

```
aberto → relatorio_submetido → parecer_emitido → em_aprovacao_ag → aprovado
                                                                  ↘ rejeitado → reaberto
```

- A Direcção abre o exercício e submete **Relatório e Contas** (+ **Orçamento** e
  **Plano** do ano seguinte) → `relatorio_submetido`.
- O CF emite **Parecer** → `parecer_emitido`.
- A Mesa liga à AG ordinária e submete a votação → `em_aprovacao_ag`.
- A deliberação da AG aprova/rejeita → `aprovado`/`rejeitado`.

**Regra do 1.º trimestre (Art. 19.1)**: a AG ordinária que aprova o exercício
`N` realiza-se no 1.º trimestre de `N+1`; o sistema **avisa** se a submissão/
aprovação ocorrer fora do prazo (não bloqueia).

### 4.3 Endpoints (`routes/prestacao_contas.py`)

- `POST /api/exercicios` (Direcção/admin) — abre o ano.
- `GET /api/exercicios` / `GET /api/exercicios/{ano}`.
- `POST /api/exercicios/{ano}/relatorio` (Direcção) — anexa `document_id` +
  congela `dre_snapshot`.
- `POST /api/exercicios/{ano}/orcamento`, `POST /api/exercicios/{ano}/plano`
  (Direcção).
- `POST /api/exercicios/{ano}/parecer` (**CF** — `is_conselho_fiscal`/`emit_cf_parecer`).
- `POST /api/exercicios/{ano}/submeter-ag` (Mesa AG/admin) — liga `assembleia_id`.
- `POST /api/exercicios/{ano}/aprovar` (Mesa AG/admin) — regista
  `deliberacao_id` + resultado.

### 4.4 RBAC, notificações, auditoria

- Abrir/relatório/orçamento/plano: Direcção/admin. Parecer: **CF**. Submeter-AG/
  aprovar: Mesa AG/admin.
- Audit: `exercicio_aberto`, `relatorio_contas_submetido`, `orcamento_submetido`,
  `plano_submetido`, `parecer_cf_emitido`, `exercicio_submetido_ag`,
  `exercicio_aprovado`/`rejeitado`.
- Notif.: CF quando o relatório é submetido (para emitir parecer); Mesa quando o
  parecer sai; sócios quando o exercício é aprovado (`"finance"`).

### 4.5 Frontend

Página `/financeiro/prestacao-contas` (ou aba no Financeiro): **dashboard do
ciclo** com os passos (Relatório&Contas → Parecer → AG → Aprovado) e o estado
atual; botões contextuais por papel (Direcção submete; CF emite parecer; Mesa
aprova). Reutiliza upload de documentos e o `dre` para pré-visualizar números.

### 4.6 Critérios de aceitação

A submissão do relatório congela o `dre_snapshot`; só o CF emite parecer (e não
consegue mexer em transacções); a aprovação exige deliberação da AG; o ciclo
avança apenas pela ordem dos estados; aviso fora do 1.º trimestre.

---

## 5. Feature 3.2 — Balancetes e balanço anual (Art. 34, 37)

**Resumo**: o Tesoureiro publica balancetes periódicos e o balanço anual; o
Conselho Fiscal audita e confere os documentos de despesa.

### 5.1 Modelo de dados — colecção `balancetes`

```python
class Balancete(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tipo: Literal["periodico", "balanco_anual"] = "periodico"
    periodo: str                               # "2026-03" | "2026-Q1" | "2026"
    exercicio_ano: int
    snapshot: dict                             # de GET /finances/summary (totais + por categoria)
    document_id: Optional[str] = None          # PDF opcional
    published: bool = False
    published_by: Optional[str] = None         # Tesoureiro
    published_at: Optional[str] = None
    cf_audit: Optional[dict] = None            # {audited_by, audited_at, conferido: bool, observacoes}
    visibility: Literal["socios", "publico", "direcao"] = "socios"
    created_at: str
    source_article: str = "34"
```

### 5.2 Conferência de documentos de despesa (CF)

- Adicionar **`proof_url: Optional[str]`** à `Transaction` (comprovativo de
  despesa). O Tesoureiro anexa; o CF confere.
- Conferência ao **nível do balancete** (`cf_audit`): o CF marca o período como
  conferido com observações. Opcionalmente, marca por transacção via campo
  aditivo `conferido: Optional[bool]` na `Transaction` (sem colecção nova).

### 5.3 Endpoints (`routes/prestacao_contas.py`)

- `POST /api/balancetes` (**Tesoureiro**/`manage_finances`) — cria/publica um
  período, congelando `snapshot` de `GET /finances/summary`.
- `GET /api/balancetes` / `GET /api/balancetes/{id}` (`can_view_finances`;
  publicados → Transparência).
- `POST /api/balancetes/{id}/auditar` (**CF**) — `cf_audit` (conferido +
  observações).
- `PATCH /api/finances/transactions/{id}` (Tesoureiro) — passa a aceitar
  `proof_url`.

### 5.4 RBAC, notificações, auditoria

- Publicar balancete: Tesoureiro (`manage_finances`). Auditar: **CF**
  (`is_conselho_fiscal`). Ver: `can_view_finances`; publicados → público.
- Audit: `balancete_publicado`, `balancete_auditado`.
- Notif.: CF quando um balancete é publicado; Tesoureiro quando o CF audita.

### 5.5 Frontend

Aba "Balancetes" no Financeiro: lista por período com `snapshot` (cards de
receitas/despesas/resultado), estado de auditoria do CF (badge "Conferido"/
"Com observações") e download do PDF. Vista CF: botão "Auditar" + campo de
observações; conferência dos comprovativos (`proof_url`) por transacção.

### 5.6 Critérios de aceitação

O balancete congela o snapshot no momento da publicação; só o Tesoureiro publica
e só o CF audita; `proof_url` aceite na transacção; balancete publicado aparece
na Transparência conforme `visibility`.

---

## 6. Feature 3.3 — Regulamentos Internos versionados (Art. 31.j, 56)

**Resumo**: repositório versionado de regulamentos com fluxo de aprovação
(incluindo o próprio Regimento da AG).

### 6.1 Modelo de dados — `regulamentos` + `regulamento_versoes`

```python
class Regulamento(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slug: str                                   # "regimento-ag", "regulamento-eleitoral"
    titulo: str
    descricao: Optional[str] = None
    competencia_aprovacao: Literal["direcao", "assembleia_geral"] = "direcao"
    current_version_id: Optional[str] = None
    created_at: str
    source_article: str = "56"

class RegulamentoVersao(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    regulamento_id: str
    versao: int                                 # 1, 2, 3...
    document_id: str
    status: Literal["rascunho", "em_aprovacao", "aprovado", "revogado"] = "rascunho"
    changelog: Optional[str] = None
    created_by: str
    approved_by: Optional[str] = None
    assembleia_id: Optional[str] = None         # se competência = AG (ex.: Regimento)
    deliberacao_id: Optional[str] = None
    effective_from: Optional[str] = None
    created_at: str
```

### 6.2 Fluxo de aprovação e versionamento

- Nova **versão** parte sempre de um `rascunho` → `em_aprovacao` → `aprovado`
  (ou `revogado`). Ao aprovar, `versao` torna-se a `current_version_id`; a
  anterior fica `revogado`/histórico (mantém-se — repositório versionado).
- **Competência**: `competencia_aprovacao="direcao"` (maioria dos regulamentos,
  Art. 31.j) aprova internamente; `"assembleia_geral"` (ex.: **Regimento da AG**)
  exige `deliberacao_id` de uma AG.
- O **Regimento da AG** é semeado como `regulamento` (`slug="regimento-ag"`,
  competência AG).

### 6.3 Endpoints (`routes/regulamentos.py`)

- `POST /api/regulamentos` (Direcção/admin) — cria o regulamento.
- `GET /api/regulamentos` / `GET /api/regulamentos/{id}` (+ histórico de versões).
- `POST /api/regulamentos/{id}/versoes` (Direcção) — nova versão (rascunho +
  `document_id`).
- `POST /api/regulamentos/{id}/versoes/{vid}/submeter` (Direcção) →
  `em_aprovacao`.
- `POST /api/regulamentos/{id}/versoes/{vid}/aprovar` — Direcção (se competência
  Direcção) ou Mesa AG/admin com `deliberacao_id` (se competência AG).
- `POST /api/regulamentos/{id}/versoes/{vid}/revogar`.

### 6.4 RBAC, notificações, auditoria

- Gerir/versionar: Direcção/admin (`manage_documents`). Aprovar competência-AG:
  Mesa AG/admin (com deliberação). Ver: sócios; aprovados → Transparência.
- Audit: `regulamento_criado`, `regulamento_versao_criada`,
  `regulamento_versao_submetida`, `regulamento_versao_aprovada`/`revogada`.
- Notif.: sócios quando um regulamento entra em vigor (`"system"`).

### 6.5 Frontend

Página `/regulamentos`: lista de regulamentos com a versão em vigor + badge de
estado; detalhe com **histórico de versões** (download por versão, changelog,
quem/quando aprovou). Vista Direcção/Mesa para criar versão e aprovar. Aprovados
ficam na Transparência pública.

### 6.6 Critérios de aceitação

Aprovar uma versão substitui a `current_version` e arquiva a anterior; o Regimento
da AG exige deliberação de AG para aprovar; o histórico mantém todas as versões;
versões aprovadas ficam públicas.

---

## 7. Colecções e índices

Acrescentar ao tuplo `COLLECTIONS` (`database.py`) e DDL a `_INDEX_DDL`:

| Colecção | Índices mínimos |
|---|---|
| `exercicios` | unique `(ano)`; `status` |
| `balancetes` | `exercicio_ano`; `(tipo, periodo)`; `published` |
| `regulamentos` | unique `(slug)` |
| `regulamento_versoes` | `regulamento_id`; `(regulamento_id, versao)`; `status` |

Sem colecção nova para auditoria de despesa nem parecer (embebidos). Campos
aditivos na `Transaction`: `proof_url`, `conferido` (opcionais).

---

## 8. Frontend (consolidado)

- Secção/abas no **Financeiro**: "Prestação de Contas" (dashboard do ciclo 3.1) e
  "Balancetes" (3.2), gated por `can_view_finances`; acções por papel (Direcção/
  Tesoureiro/CF/Mesa). Página **`/regulamentos`** (3.3) na sidebar (secção
  Documentos/Governança).
- `AuthContext`: usar `isConselhoFiscal`, `isDirecao`, `isTesoureiro`,
  `canManageFinances`, `canViewFinances` (espelho do backend) para gating.
- Reutilizar: upload de documentos, `dre`/`summary` para snapshots e
  pré-visualização, Transparência pública (`public/download`), TanStack Query.
- Design neutral-led + Carmesim, sem dark mode (skill `frontend-design`); estados
  de aprovação com badges claros.
- `utils/api.js`: grupos `exerciciosAPI`, `balancetesAPI`, `regulamentosAPI`.

---

## 9. Plano de execução faseado

PRs pequenos, `feature/* → develop`. Não misturar com migração destrutiva.

| Fase | Entrega | Depende |
|---|---|---|
| F0 | `proof_url`/`conferido` aditivos na `Transaction`; capability CF de parecer/auditoria; módulos `prestacao_contas.py`/`regulamentos.py` registados | — |
| F1 | **3.3 Regulamentos versionados** (independente das finanças) | F0 |
| F2 | **3.2 Balancetes** (Tesoureiro publica snapshot; CF audita; `proof_url`) | F0 |
| F3 | **3.1 Ciclo do exercício** (relatório/orçamento/plano + parecer CF) | F0, F2 |
| F4 | Integração de aprovação na AG ordinária (deliberação) | governança §11 |
| F5 | Frontend (dashboard do ciclo, balancetes, regulamentos) | F1–F3 |

### Ordem dentro de cada fase

Models/campos → schema/índices (`ensure_schema`) → endpoints + RBAC + audit →
testes backend → frontend → testes frontend → verificação manual (submeter
relatório, emitir parecer como CF, publicar balancete, criar/aprovar versão de
regulamento).

---

## 10. Testes obrigatórios

Colecções novas **não** estão pré-cabladas no `mock_db` — cablar em-teste.

- 3.1: estados avançam por ordem; `dre_snapshot` congelado na submissão; só CF
  emite parecer; CF **não** consegue criar/editar transacção (403); aprovar exige
  deliberação; aviso fora do 1.º trimestre.
- 3.2: balancete congela `summary` snapshot; só Tesoureiro publica; só CF audita;
  `proof_url` aceite no PATCH de transacção; `view_finances_readonly` lê mas não
  publica.
- 3.3: aprovar versão troca `current_version` e revoga a anterior; Regimento (AG)
  exige `deliberacao_id`; histórico preservado; `slug` único.
- RBAC: matriz Direcção/Tesoureiro/CF/Mesa por endpoint.

Frontend: dashboard do ciclo por papel; badges de auditoria; histórico de
versões; gating por `isConselhoFiscal`/`isTesoureiro`.

---

## 11. Stop conditions (CLAUDE.md)

Confirmar com o utilizador antes de:

- Alterar a `Transaction` para além de campos **aditivos/opcionais**
  (`proof_url`, `conferido`) — qualquer mudança incompatível é stop condition.
- Migrar/limpar dados financeiros.
- Enviar emails reais.
- Remover rotas que o frontend chama.
- Tratar a aprovação digital de contas como vinculativa sem a deliberação da AG
  (a aprovação **é** da AG — Art. 19.1/37).

---

## 12. Decisões em aberto

1. **Aprovação de contas**: sempre via AG ordinária (Art. 37 — recomendado) ou
   admite-se aprovação interina pela Direcção até à AG?
2. **Granularidade do balancete**: mensal, trimestral ou ambos? (`periodo`
   suporta os três; confirmar a cadência esperada.)
3. **Conferência de despesa**: ao nível do balancete (recomendado, simples) ou
   por-transacção (`conferido` + colecção de auditoria dedicada)?
4. **`proof_url`**: campo na `Transaction` (recomendado) ou anexos numa colecção
   separada `transacao_anexos`?
5. **Competência de aprovação dos regulamentos**: confirmar quais são da Direcção
   (Art. 31.j) e quais exigem AG (ex.: Regimento, Art. 56) — semear a lista.
6. **Exposição pública do balancete**: só PDF (como hoje na Transparência) ou
   também *snapshot* inline (números) na página pública?
7. **Parecer do CF**: capability dedicada (`emit_cf_parecer`) vs. usar
   `is_conselho_fiscal` por cargo/órgão.
8. **Orçamento/Plano**: documentos anexos (recomendado) ou também dados
   estruturados (linhas de orçamento) para comparar com o realizado?
