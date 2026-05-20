# Spec — Governança Estatutária da ACCTA

> **Status**: rascunho técnico revisto em 2026-05-20; requer validação da
> Direcção/Mesa da AG antes de implementar regras que tenham efeito jurídico.
> **Objetivo**: substituir a grelha genérica de cargos por uma modelação
> estatutária da ACCTA: órgãos sociais, cargos, categorias de membro, mandatos,
> assembleias, eleições, disciplina, quotas e jóias.
> **Estado do sistema**: ainda não em produção, sem sócios reais; migração
> agressiva é aceitável, mas qualquer limpeza/migração em `users` continua a
> exigir confirmação explícita.

## 0. Fontes, precedência e limites

Esta spec é uma especificação de produto/engenharia. Não é parecer jurídico.
Quando houver conflito, aplicar esta ordem:

1. **Estatutos da ACCTA** e **Regimento da Assembleia Geral** fornecidos pela
   associação.
2. Legislação cabo-verdiana aplicável a associações e pessoas colectivas.
3. Invariantes do projecto em `CLAUDE.md`.
4. Esta spec e specs relacionadas.
5. Implementação actual.

Fontes verificadas em 2026-05-20:

- Código Civil de Cabo Verde, secção de associações: arts. 171.º a 184.º
  tratam acto de constituição/estatutos, órgãos, assembleia, voto e efeitos da
  exclusão/extinção. Referência pública: [WIPO Lex — Civil Code, Cabo Verde](https://www.wipo.int/wipolex/en/legislation/details/8231).
- Boletim Oficial electrónico da INCV publica estatutos/extractos de
  associações, confirmando o padrão de publicidade legal. Exemplo: BOE,
  [Estatuto da Associação n.º 47/2024](https://boe.incv.cv/Bulletins/View/3688).
- A existência pública da ACCTA é mencionada pela Inforpress em 2025, mas a
  pesquisa pública não localizou os Estatutos da ACCTA no BOE. Para esta
  implementação, os documentos oficiais internos continuam a ser a fonte
  autoritativa. Referência: [Inforpress, 03/12/2025](https://www.inforpress.cv/en/article-6380).

**Pré-condição documental**: antes de codificar fases com efeito estatutário
real, anexar ao repositório privado ou ao gestor documental interno:
`Estatutos_ACCTA_2011.pdf` e `Regimento_AG_ACCTA_2012.pdf`, ou equivalente
assinado/digitalizado. A implementação deve manter o artigo de origem em cada
regra sensível (`source_article`).

---

## 1. Specs relacionados

- `tasks/spec-identidade-cargos.md`: já introduz `account_type`, `member_id`
  imutável, `cargo_history`, promote/demote/transfer, RBAC granular e
  endpoints administrativos. Esta spec **supercede a taxonomia de cargos**
  desse documento, mas reaproveita a maquinaria de identidade/mandatos.
- `tasks/spec-auto-registo.md`: compatível; o candidato continua a declarar um
  cargo informativo, mas a aprovação deve normalizar para o catálogo
  estatutário definido aqui.

**Divergências a corrigir no spec/código de identidade**:

- `"Secretário-Geral"` passa a ser `"Secretário"` nos órgãos estatutários.
- Conselho Fiscal inclui **Relator**.
- `"Coordenações"` e `"Comissões"` não são órgãos sociais estatutários; passam
  a funções operacionais opcionais.
- Falta `member_category`, `orgao`, mandato eleitoral, assembleia, disciplina,
  quotas/jóias e regras de voto.
- O código actual guarda `cargo` como label humano; a forma final deve guardar
  **key canónica**.

---

## 2. Diagnóstico do estado actual

Snapshot do código em 2026-05-20:

- `backend/models.py` concentra `CARGOS_ORGAOS_SOCIAIS`, `CARGOS`,
  `CARGO_DEFAULTS`, `CARGO_SEATS` e `PRIVILEGES`.
- A taxonomia actual ainda é a genérica do spec anterior: inclui
  Coordenações/Comissões, não inclui Relator, usa `"Secretário-Geral"` e mistura
  cargos estatutários com funções operacionais.
- `UserBase` já tem `account_type`, `cargo`, `privileges` e `cargo_history`, mas
  não tem `orgao`, `member_category`, suspensão de direitos nem campos
  eleitorais.
- `/api/users/meta/cargos`, `/api/admin/cargos`, `/promote`, `/demote` e
  `/transfer` já existem e trabalham com labels.
- `auth.py` e `routes/finances.py` já separam leitura financeira
  (`view_finances_readonly`) de escrita (`manage_finances`).
- Ainda não existem `backend/governance.py`, `routes/governance.py`,
  assembleias, eleições, disciplina, jóia nem histórico de deliberações.

Implicação: a primeira entrega não deve "adicionar mais listas"; deve migrar a
fonte de verdade para `backend/governance.py` e fazer `models.py` re-exportar
as constantes para preservar imports e testes existentes.

---

## 3. Fonte estatutária da ACCTA

### 3.1 Órgãos sociais

| Órgão | Natureza | Composição | Base |
|---|---|---:|---|
| Assembleia Geral | Deliberativo máximo; todos os membros | Mesa da AG | Estatutos arts. 16-18 |
| Direcção | Executivo/administrativo | 5 a 7 titulares | Estatutos arts. 16, 27 |
| Conselho Fiscal | Fiscalização económico-financeira | 3 titulares | Estatutos arts. 16, 35 |

### 3.2 Cargos

- **Mesa da Assembleia Geral**: Presidente, Vice-Presidente, Secretário.
- **Direcção**: Presidente, Vice-Presidente, Secretário, Tesoureiro, Vogal,
  podendo haver até 2 vogais adicionais afectos a órgãos ATC fora da sede. O
  Presidente da Direcção é o Presidente da ACCTA.
- **Conselho Fiscal**: Presidente, Relator, Vogal.

### 3.3 Categorias de membro

| Categoria | Definição operacional | Vota? |
|---|---|---|
| Fundador | CTA cabo-verdiano no activo à data da fundação | Sim |
| Ordinário | Exerce/exerceu funções de CTA; admitido pela Direcção | Sim |
| Honorário | Serviços relevantes; eleito pela AG por maioria qualificada | Não, salvo representação admitida no Regimento |

Direitos/deveres a reflectir no sistema: votar, eleger/ser eleito, participar,
propor admissões, pagar quotas/jóias, exercer cargos e comparecer.

### 3.4 Regras de mandato e eleições

- Mandato de 3 anos.
- Sufrágio secreto, listas plurinominais, sem cumulação de cargos.
- Suplentes: 2 para a Direcção, 1 para cada um dos restantes órgãos.
- Titulares cessantes mantêm-se até à posse dos novos; posse até 15 dias após
  proclamação.
- Listas devem apresentar candidatos para todos os cargos e suplentes.
- Comissão Eleitoral: 2 membros + 1 por lista; membros não podem ser candidatos.
- Mesa de Voto: pelo menos 2 membros.
- Convocatória eleitoral: antecedência mínima de 20 dias.
- Candidaturas: até 10 dias antes.
- Voto por correspondência permitido com impedimento justificado.
- Voto por procuração não é permitido em eleições.
- Lista vencedora: maioria simples dos votos válidos; empate implica nova
  eleição em 15 dias.
- Recurso: 3 dias.

### 3.5 Assembleia Geral

- Sessão ordinária: uma vez por ano, no 1.º trimestre.
- Sessão extraordinária: requerida pela Mesa, Direcção, Conselho Fiscal ou pelo
  mínimo estatutário de membros.
- Convocatória geral: pelo menos 10 dias, com dia/hora/local e ordem de
  trabalhos.
- Quórum: maioria dos membros em 1.ª convocatória; 30 minutos depois, pelo
  menos 1/3 em 2.ª convocatória.
- Deliberações: maioria absoluta dos presentes; 3/4 para alteração de estatutos
  e fixação de quota/jóia; dissolução exige 3/4 do universo de membros.
- Representação: um membro representa no máximo 3 outros; titulares da Mesa não
  representam.
- Actas: assinadas por Presidente e Secretário da Mesa; disponibilizadas em 30
  dias.

### 3.6 Disciplina

- Sanções: advertência escrita, multa até 3x quota, perda de direitos até 1 ano,
  expulsão.
- Advertência/multa/perda de direitos: competência da Direcção.
- Expulsão: competência exclusiva da AG, sob proposta da Direcção.
- Comissão de Inquérito: 3 elementos; conclusões em 30 dias.
- Recurso à AG em 15 dias para multa/perda de direitos.
- Perda de qualidade: demissão escrita, expulsão ou incumprimento de quotas nos
  termos estatutários.

**Decisão do produto**: não criar status `"inadimplente"`. Quotas são
descontadas em folha. A perda por não pagamento fica como workflow disciplinar
manual de excepção, sem novo estado de conta.

---

## 4. Decisões técnicas finais

1. **Fonte única**: criar `backend/governance.py`; `models.py` re-exporta as
   constantes para compatibilidade.
2. **Cargo persistido como key**: `users.doc.cargo = "dir_tesoureiro"`, nunca o
   label `"Tesoureiro"`. Labels só para UI.
3. **Compatibilidade de escrita**: endpoints aceitam key, label canónico ou alias
   legado, mas gravam sempre key.
4. **Órgão derivado e denormalizado**: `orgao` é calculado a partir do cargo e
   também guardado em `users.doc.orgao` para filtros/relatórios.
5. **Categorias de membro**: `member_category` define voto base; sanções podem
   suspender direitos sem alterar categoria.
6. **Conta técnica fora do modelo estatutário**:
   `admin@controlador.cv` mantém `account_type="technical"`, `member_id=None`,
   `cargo="tecnico_sistema"` ou label livre, `cargo_history=[]`, e não vota.
7. **Funções operacionais separadas**: coordenadores/grupos de trabalho vivem em
   `funcoes_operacionais` ou `operational_assignments`; não ocupam assentos de
   órgãos sociais nem entram em `cargo_history` estatutário.
8. **Sem cumulação estatutária**: um membro não pode ter mais de um mandato
   estatutário activo. Funções operacionais podem coexistir.
9. **Voto secreto**: nunca guardar `user_id` e sentido de voto no mesmo
   documento. A unicidade do eleitor é separada do boletim.
10. **Voto digital com cautela**: se os Estatutos/Regimento não autorizarem voto
    electrónico, o portal deve operar como registo/apoio administrativo e não
    como urna juridicamente vinculativa.

---

## 5. `backend/governance.py` — núcleo

Sem imports de `models`. Todos os módulos importam daqui, ou de `models.py` por
re-export temporário.

```python
ASSEMBLEIA_GERAL = "assembleia_geral"
DIRECAO = "direcao"
CONSELHO_FISCAL = "conselho_fiscal"

ORGAOS = {
    ASSEMBLEIA_GERAL: {
        "id": ASSEMBLEIA_GERAL,
        "nome": "Assembleia Geral",
        "tipo": "deliberativo",
        "tem_mesa": True,
        "mandato_anos": 3,
        "suplentes": 1,
        "artigos": ["16", "17", "18"],
    },
    DIRECAO: {
        "id": DIRECAO,
        "nome": "Direcção",
        "tipo": "executivo",
        "tem_mesa": False,
        "mandato_anos": 3,
        "suplentes": 2,
        "artigos": ["16", "27"],
    },
    CONSELHO_FISCAL: {
        "id": CONSELHO_FISCAL,
        "nome": "Conselho Fiscal",
        "tipo": "fiscalizacao",
        "tem_mesa": False,
        "mandato_anos": 3,
        "suplentes": 1,
        "artigos": ["16", "35"],
    },
}
```

### 5.1 Catálogo de cargos

```python
CARGOS_CATALOG = [
    {"key": "ag_presidente", "label": "Presidente da Mesa da AG",
     "orgao": ASSEMBLEIA_GERAL, "ordem": 1, "seats": 1,
     "role": "socio", "privileges": ["manage_events"]},
    {"key": "ag_vice_presidente", "label": "Vice-Presidente da Mesa da AG",
     "orgao": ASSEMBLEIA_GERAL, "ordem": 2, "seats": 1,
     "role": "socio", "privileges": []},
    {"key": "ag_secretario", "label": "Secretário da Mesa da AG",
     "orgao": ASSEMBLEIA_GERAL, "ordem": 3, "seats": 1,
     "role": "socio", "privileges": ["manage_documents"]},

    {"key": "dir_presidente", "label": "Presidente da Direcção",
     "orgao": DIRECAO, "ordem": 1, "seats": 1,
     "role": "admin", "privileges": "ALL", "is_president_accta": True},
    {"key": "dir_vice_presidente", "label": "Vice-Presidente da Direcção",
     "orgao": DIRECAO, "ordem": 2, "seats": 1,
     "role": "admin", "privileges": "ALL"},
    {"key": "dir_secretario", "label": "Secretário da Direcção",
     "orgao": DIRECAO, "ordem": 3, "seats": 1,
     "role": "admin",
     "privileges": ["manage_users", "manage_events", "manage_documents", "moderate_content"]},
    {"key": "dir_tesoureiro", "label": "Tesoureiro",
     "orgao": DIRECAO, "ordem": 4, "seats": 1,
     "role": "financeiro", "privileges": ["manage_finances", "view_audit_logs"]},
    {"key": "dir_vogal", "label": "Vogal da Direcção",
     "orgao": DIRECAO, "ordem": 5, "seats": 3,
     "role": "moderador", "privileges": ["moderate_content", "manage_events"]},

    {"key": "cf_presidente", "label": "Presidente do Conselho Fiscal",
     "orgao": CONSELHO_FISCAL, "ordem": 1, "seats": 1,
     "role": "socio", "privileges": ["view_finances_readonly", "view_audit_logs"]},
    {"key": "cf_relator", "label": "Relator do Conselho Fiscal",
     "orgao": CONSELHO_FISCAL, "ordem": 2, "seats": 1,
     "role": "socio", "privileges": ["view_finances_readonly", "view_audit_logs"]},
    {"key": "cf_vogal", "label": "Vogal do Conselho Fiscal",
     "orgao": CONSELHO_FISCAL, "ordem": 3, "seats": 1,
     "role": "socio", "privileges": ["view_finances_readonly", "view_audit_logs"]},

    {"key": "socio", "label": "Sócio",
     "orgao": None, "ordem": 99, "seats": 0,
     "role": "socio", "privileges": []},
]
```

`dir_vogal.seats = 3`: 1 vogal base + até 2 vogais extra fora da sede.
`socio.seats = 0`: sem limite e sem mandato.

### 5.2 Categorias, privilégios e roles

```python
MEMBER_CATEGORIES = ["fundador", "ordinario", "honorario"]
MEMBER_CATEGORY_LABELS = {
    "fundador": "Fundador",
    "ordinario": "Ordinário",
    "honorario": "Honorário",
}
VOTING_CATEGORIES = {"fundador", "ordinario"}
DEFAULT_MEMBER_CATEGORY = "ordinario"

PRIVILEGES = [
    "manage_users",
    "manage_finances",
    "manage_events",
    "manage_documents",
    "moderate_content",
    "manage_benefits",
    "view_audit_logs",
    "view_finances_readonly",
]

ROLES = ["admin", "financeiro", "moderador", "socio"]
MANDATO_ANOS = 3
```

### 5.3 Aliases legados

```python
LEGACY_CARGO_ALIASES = {
    "Presidente": "dir_presidente",
    "Vice-Presidente": "dir_vice_presidente",
    "Secretário-Geral": "dir_secretario",
    "Secretário": "dir_secretario",
    "Tesoureiro": "dir_tesoureiro",
    "Vogal": "dir_vogal",
    "Vogal da Direcção": "dir_vogal",
    "Vogal da Direção": "dir_vogal",
    "Membro da Direcção": "dir_vogal",
    "Membro da Direção": "dir_vogal",
    "Presidente do Conselho Fiscal": "cf_presidente",
    "Relator do Conselho Fiscal": "cf_relator",
    "Vogal do Conselho Fiscal": "cf_vogal",
    "Presidente da Mesa": "ag_presidente",
    "Presidente da Mesa da AG": "ag_presidente",
    "Vice-Presidente da Mesa": "ag_vice_presidente",
    "Secretário da Mesa": "ag_secretario",
    "Sócio": "socio",
    "Socio": "socio",
}
```

`"Administrador"` e `"Técnico de Sistema"` **não** mapeiam para cargo
estatutário; são labels técnicos.

### 5.4 Helpers obrigatórios

```python
def cargo_info(cargo_key_or_label: str) -> dict | None: ...
def normalize_cargo(value: str) -> str: ...
def cargo_label(cargo: str) -> str: ...
def privileges_for_cargo(cargo: str) -> list[str]: ...
def role_for_cargo(cargo: str) -> str: ...
def orgao_of_cargo(cargo: str) -> str | None: ...
def seats_for_cargo(cargo: str) -> int: ...
def is_estatutary_cargo(cargo: str) -> bool: ...
def is_voting_member(user_doc: dict, as_of: str | None = None) -> bool: ...
def is_eligible_for_office(user_doc: dict, as_of: str | None = None) -> bool: ...
def required_quorum(total_voters: int, chamada: int) -> int: ...
def required_absolute_majority(voting_power_present: int) -> int: ...
def required_three_quarters(base: int) -> int: ...
def election_slots() -> list[dict]: ...
def governance_structure() -> dict: ...
```

Derivados para re-export:

```python
CARGOS = [c["label"] for c in CARGOS_CATALOG]
CARGO_KEYS = [c["key"] for c in CARGOS_CATALOG]
CARGO_DEFAULTS = {
    c["key"]: {"role": c["role"], "privileges": privileges_for_cargo(c["key"])}
    for c in CARGOS_CATALOG
}
CARGO_SEATS = {c["key"]: c["seats"] for c in CARGOS_CATALOG}
```

Durante transição, `CARGO_DEFAULTS` pode expor também aliases por label, mas a
forma canónica é sempre por key.

---

## 6. Modelos de dados

### 6.1 `UserBase`

Campos novos/adaptados:

```python
class UserBase(BaseModel):
    account_type: Literal["member", "technical"] = "member"
    member_category: str = "ordinario"
    orgao: Optional[str] = None
    cargo: str = "socio"
    privileges: list[str] = []
    cargo_history: list[dict] = []
    rights_suspended_until: Optional[str] = None
    rights_suspension_reason: Optional[str] = None
    residence_island: Optional[str] = None
```

Notas:

- `rights_suspended_until` afecta voto e elegibilidade, mas não transforma o
  utilizador em inactivo.
- `residence_island` é necessário para validar representação em AG quando a regra
  do Sal for automatizada.
- Pydantic continua aditivo/opcional; documentos antigos são válidos.

### 6.2 `CargoMandate`

```python
class CargoMandate(BaseModel):
    id: str
    cargo: str                    # key canónica
    label: Optional[str] = None    # snapshot para auditoria/display antigo
    role: str
    orgao: Optional[str] = None
    inicio: str
    fim: Optional[str] = None
    posse_em: Optional[str] = None
    mandato_inicio: Optional[str] = None
    mandato_fim: Optional[str] = None
    suplente: bool = False
    seat_index: Optional[int] = None
    elected_by: Optional[str] = None
    eleicao_id: Optional[str] = None
    assembleia_id: Optional[str] = None
    transitioned_by: str
    transition_id: Optional[str] = None
    notes: Optional[str] = None
```

Invariantes:

- No máximo um mandato estatutário activo por membro.
- No máximo `CARGO_SEATS[cargo]` titulares activos por cargo.
- Conta `technical` nunca recebe mandato.
- `cargo_history` não é editado directamente via UI; só por promote/demote,
  transfer ou proclamação eleitoral.

### 6.3 Modelos de governança

Criar modelos Pydantic para:

- `Assembleia`, `AssembleiaPresenca`, `AssembleiaDeliberacao`
- `Eleicao`, `EleicaoLista`, `EleicaoVoterReceipt`, `EleicaoBallot`
- `Sancao`
- `FinanceSettings` estendido

Datas sempre ISO 8601 string quando armazenadas em `doc`.

---

## 7. Colecções e índices

Adicionar em `database.py::ensure_schema()`.

| Colecção | Conteúdo | Índices mínimos |
|---|---|---|
| `assembleias` | sessões da AG | `status`, `tipo`, `data` |
| `assembleia_presencas` | presença/representação | `assembleia_id`, `user_id`, `representante_id` |
| `eleicoes` | acto eleitoral | `status`, `ano`, `assembleia_id` |
| `eleicao_listas` | listas candidatas | `eleicao_id`, `letra`, unique `(eleicao_id, letra)` |
| `eleicao_voter_receipts` | marca anónima de eleitor que votou | unique `(eleicao_id, voter_hash)` |
| `eleicao_ballots` | boletins sem `user_id`/`voter_hash` | `eleicao_id`, `ballot_box_id` |
| `sancoes` | processos disciplinares | `user_id`, `status`, `tipo` |
| `finance_settings_history` | histórico de quota/jóia | `effective_from`, `assembleia_id` |

**Voto secreto**:

- `eleicao_voter_receipts` prova que um eleitor votou uma vez.
- `eleicao_ballots` guarda o boletim sem ligação ao eleitor.
- A operação de voto deve inserir receipt e ballot numa transacção. Se o DAO não
  suportar bem esta transacção, criar função dedicada em `database.py`.
- `voter_hash = HMAC(secret, f"{eleicao_id}:{user_id}")`, nunca hash simples.
- A API nunca devolve receipts com timestamps finos em conjunto com boletins.
- Se a eleição for presencial/offline, permitir modo `apuramento_manual`, onde o
  portal regista apenas contagens agregadas e acta.

---

## 8. RBAC e elegibilidade

Helpers comuns em `auth.py`/`permissions.py`:

```python
def user_can(user, privilege: str) -> bool:
    return user.role == "admin" or privilege in (user.privileges or [])

def is_mesa_ag(user) -> bool:
    return normalize_cargo(user.cargo).startswith("ag_")

def is_direcao(user) -> bool:
    return orgao_of_cargo(user.cargo) == DIRECAO

def is_conselho_fiscal(user) -> bool:
    return orgao_of_cargo(user.cargo) == CONSELHO_FISCAL
```

Matriz:

| Área | Leitura | Escrita |
|---|---|---|
| Utilizadores/cargos | `admin` ou `manage_users` | `admin` ou `manage_users` |
| Finanças | `admin`, `financeiro`, `manage_finances` ou `view_finances_readonly` | `admin`, `financeiro` ou `manage_finances` |
| Assembleias | membros autenticados conforme visibilidade | Mesa AG, `admin` ou privilégio dedicado |
| Eleições | membros votantes/Comissão/Mesa | Mesa AG, Comissão Eleitoral, `admin` |
| Disciplina | próprio vê o seu processo; Direcção/admin gerem | Direcção/admin; expulsão exige AG |
| Documentos/actas | conforme visibilidade | `manage_documents` ou Mesa AG |

`is_voting_member(user)` exige:

- `account_type == "member"`
- `status == "ativo"`
- `member_category in {"fundador", "ordinario"}`
- sem `rights_suspended_until` vigente

Honorário só pode votar quando representando membro votante em AG, se o
Regimento o admitir; nunca vota em eleições por procuração.

---

## 9. Endpoint de estrutura

### `GET /api/governance/structure`

Autenticado leve. Devolve tudo que o frontend precisa:

```json
{
  "orgaos": [],
  "cargos": [
    {
      "key": "dir_tesoureiro",
      "label": "Tesoureiro",
      "orgao": "direcao",
      "seats": 1,
      "role_default": "financeiro",
      "privileges_default": ["manage_finances", "view_audit_logs"]
    }
  ],
  "funcoes_operacionais": [],
  "member_categories": [],
  "privileges": [],
  "roles": [],
  "mandato_anos": 3,
  "election_slots": []
}
```

Manter `/api/users/meta/cargos` e `/api/users/meta/privileges` como aliases
temporários que chamam `governance_structure()`. Marcar como deprecated no
payload.

---

## 10. Cargos e mandatos

Actualizar endpoints já existentes:

- `POST /api/admin/users/{id}/promote`
- `POST /api/admin/users/{id}/demote`
- `POST /api/admin/cargos/transfer`
- `GET /api/admin/cargos`
- `GET /api/admin/cargos/candidates`
- `GET /api/users/{id}/cargo-history`

Mudanças obrigatórias:

- Requests aceitam `cargo` key/label/alias; gravam key.
- Se `role`/`privileges` não vierem no request, derivar de `CARGO_DEFAULTS`.
- Setar `orgao` em simultâneo com `cargo`.
- Validar sem cumulação estatutária.
- `GET /admin/cargos` retorna linhas por cargo key e `holders` por assento.
- UI mostra `label`, nunca key crua, excepto em debug.

---

## 11. Assembleia Geral

### Modelo

```python
class Assembleia(BaseModel):
    id: str
    tipo: Literal["ordinaria", "extraordinaria", "eleitoral"]
    titulo: str
    data: str
    local: str
    convocada_por: str
    convocatoria_em: str
    antecedencia_dias: int
    requerente_tipo: Optional[str] = None
    requerentes: list[str] = []
    ordem_trabalhos: list[dict] = []
    status: Literal["rascunho", "convocada", "em_curso", "encerrada", "anulada"]
    eligible_voters_count: int
    chamada_actual: Literal[1, 2] = 1
    quorum_required: int
    quorum_met: bool = False
    acta_document_id: Optional[str] = None
    created_at: str
```

`AssembleiaPresenca` deve distinguir:

- presença própria
- representação
- poder de voto (`voting_power`)
- documentos de procuração/representação, se houver

`AssembleiaDeliberacao`:

- ponto da ordem de trabalhos
- tipo de maioria: `absoluta`, `qualificada_3_4_presentes`,
  `qualificada_3_4_universo`
- base de cálculo
- votos a favor/contra/abstenções
- aprovado
- `source_article`

### Regras

- Convocatória: `>=10` dias; se `tipo="eleitoral"`, `>=20` dias.
- Convocação escrita: Mesa AG/admin.
- Extraordinária exige `requerente_tipo` válido e evidência.
- Quórum:
  - 1.ª chamada: `floor(total_votantes / 2) + 1`
  - 2.ª chamada: `ceil(total_votantes / 3)`
- Maioria absoluta: `floor(voting_power_present / 2) + 1`
- 3/4: `ceil(base * 3 / 4)`
- Titulares da Mesa não podem representar outros membros.
- Um representante não pode acumular mais de 3 representados.
- Validação "só 1 residente no Sal" depende de `residence_island`; enquanto o
  dado não estiver completo, o sistema deve assinalar validação manual.
- Acta deve ser anexada até 30 dias após encerramento.

### Endpoints

- `POST /api/assembleias`
- `GET /api/assembleias`
- `GET /api/assembleias/{id}`
- `POST /api/assembleias/{id}/presencas`
- `POST /api/assembleias/{id}/deliberacoes`
- `POST /api/assembleias/{id}/encerrar`
- `GET /api/assembleias/{id}/quorum`

---

## 12. Eleições

### Slots eleitorais

Não usar `dict[cargo_key] = user_id`, porque há múltiplos vogais e suplentes.
Usar lista de slots:

```python
[
  {"slot_key": "dir_vogal_1", "cargo": "dir_vogal", "orgao": "direcao", "suplente": false, "seat_index": 1},
  {"slot_key": "dir_suplente_1", "cargo": "dir_vogal", "orgao": "direcao", "suplente": true, "seat_index": 1}
]
```

`election_slots()` gera:

- Mesa AG: 3 titulares + 1 suplente.
- Direcção: 5 ou 7 titulares conforme configuração da eleição + 2 suplentes.
- Conselho Fiscal: 3 titulares + 1 suplente.

### Modelos

```python
class Eleicao(BaseModel):
    id: str
    ano: int
    mandato_inicio: str
    mandato_fim: str
    status: Literal[
        "preparacao", "candidaturas", "campanha", "votacao",
        "apurada", "recurso", "proclamada", "anulada"
    ]
    calendario: dict
    assembleia_id: Optional[str]
    comissao_eleitoral: list[str]
    mesa_voto: list[str]
    modo_votacao: Literal["presencial", "correspondencia", "digital", "hibrido"]
    resultado: Optional[dict] = None
```

```python
class EleicaoLista(BaseModel):
    id: str
    eleicao_id: str
    letra: str
    nome: Optional[str] = None
    candidatos: list[dict]  # slot_key, cargo, user_id, suplente, seat_index
    programa_document_id: Optional[str]
    estado: Literal["submetida", "aceite", "rejeitada"]
    rejeicao_motivo: Optional[str] = None
```

### Regras

- Votantes: `is_voting_member`.
- Candidatos: `is_eligible_for_office`; sem direitos suspensos.
- Uma pessoa não pode aparecer em mais de um slot na mesma lista.
- Comissão Eleitoral e Mesa de Voto não podem ser candidatos.
- Lista incompleta é rejeitada.
- Candidatura fora do prazo é rejeitada.
- Sem procuração eleitoral.
- Voto por correspondência exige `justificacao` e registo administrativo.
- Apuramento exclui brancos/nulos de `total_validos`.
- Maioria simples: maior número de votos válidos.
- Empate: status/flag `nova_eleicao_ate`.
- Proclamação cria mandatos via serviço interno comum, com `eleicao_id`,
  `assembleia_id`, `mandato_inicio`, `mandato_fim` e `posse_em`.
- Cessantes só são encerrados na posse, não no apuramento.

### Endpoints

- `POST /api/eleicoes`
- `GET /api/eleicoes`
- `GET /api/eleicoes/{id}`
- `POST /api/eleicoes/{id}/listas`
- `POST /api/eleicoes/{id}/listas/{lista_id}/validar`
- `POST /api/eleicoes/{id}/abrir-votacao`
- `POST /api/eleicoes/{id}/votar`
- `POST /api/eleicoes/{id}/voto-correspondencia`
- `POST /api/eleicoes/{id}/apurar`
- `POST /api/eleicoes/{id}/proclamar`

---

## 13. Regime disciplinar

### Modelo

```python
class Sancao(BaseModel):
    id: str
    user_id: str
    tipo: Literal["advertencia", "multa", "perda_direitos", "expulsao"]
    motivo: str
    artigo_violado: Optional[str]
    status: Literal[
        "proposta", "inquerito", "decidida", "recurso",
        "aplicada", "arquivada", "anulada"
    ]
    proposta_por: str
    comissao_inquerito: list[dict]
    inquerito_prazo: str
    conclusoes_document_id: Optional[str]
    decisao: Optional[dict]
    multa_valor: Optional[float]
    perda_direitos_ate: Optional[str]
    assembleia_id: Optional[str]
    deliberacao_id: Optional[str]
    recurso: Optional[dict]
    created_at: str
```

### Regras

- Advertência/multa/perda: Direcção/admin.
- Expulsão: proposta pela Direcção, decisão por AG, com deliberação ligada.
- Comissão de Inquérito: 3 elementos e prazo de 30 dias.
- Multa: `<= 3 * finance_settings.quota_amount`.
- Perda de direitos:
  - setar `rights_suspended_until`
  - impedir voto e candidatura enquanto vigente
  - manter `status="ativo"`
- Expulsão aplicada:
  - encerrar mandato activo
  - setar `status="inativo"`
  - manter histórico e auditoria
- Recurso em 15 dias para multa/perda.
- Dados disciplinares são sensíveis: respostas devem ocultar detalhes para
  utilizadores sem permissão.

### Endpoints

- `POST /api/sancoes`
- `GET /api/sancoes`
- `GET /api/sancoes/{id}`
- `GET /api/users/{id}/sancoes`
- `POST /api/sancoes/{id}/comissao`
- `POST /api/sancoes/{id}/decidir`
- `POST /api/sancoes/{id}/recurso`
- `POST /api/sancoes/{id}/aplicar`

---

## 14. Quotas e jóias

Estender `FinanceSettings`:

```python
class FinanceSettings(BaseModel):
    quota_amount: float = 2000.0
    quota_description: str = "Quota Mensal"
    joia_multiplier: float = 2.0
    joia_amount: Optional[float] = None
    quota_fixed_by_assembleia_id: Optional[str] = None
    quota_fixed_by_deliberacao_id: Optional[str] = None
    effective_from: Optional[str] = None
```

Regras:

- `joia_amount` default = `2 * quota_amount`, salvo deliberação em contrário se
  permitida pelos Estatutos.
- Alterar quota/jóia exige referência a deliberação de AG com maioria 3/4.
- Registar versão anterior em `finance_settings_history`.
- Auto-registo/convite deve assinalar jóia devida quando aplicável, mas a
  cobrança continua no módulo financeiro/folha.
- Não criar `inadimplente`; eventual perda por não pagamento é processo
  disciplinar/manual.

---

## 15. Frontend

### Transversal

- Substituir hard-code por `GET /api/governance/structure`.
- Guardar key nos forms; mostrar label.
- Criar `frontend/src/lib/governanceLabels.js` ou equivalente para fallbacks
  leves, nunca como fonte de verdade.
- `AuthContext.js`: adicionar `can(privilege)`, `isMesaAG`, `isDirecao`,
  `isConselhoFiscal`, `isTesoureiro`, `isVotingMember`.
- `PrivateLayout.js`: menus por permissão/cargo:
  Cargos, Assembleias, Eleições, Disciplina.

### Páginas

- `/admin/cargos`: adaptar para keys e órgão.
- `/admin/assembleias`: convocar, presenças, representações, quórum,
  deliberações, acta.
- `/admin/eleicoes`: calendário, listas, validação, votação/apuramento,
  proclamação.
- `/admin/disciplinar`: processos, prazos, decisão, recurso.
- `/perfil`: "Os meus cargos/mandatos" e, se aplicável, suspensão de direitos.

Design: seguir o sistema existente neutral-led + Carmesim; sem dark mode; sem
landing page para módulos administrativos.

---

## 16. Migração

### Fase M0 — Preparação

- Adicionar `backend/governance.py` com testes unitários.
- `models.py` re-exporta constantes; sem quebrar imports.
- `GET /api/governance/structure` criado.
- `/users/meta/cargos` vira alias temporário.

### Fase M1 — Normalização compatível

- Endpoints aceitam labels antigos e gravam key.
- Adicionar campos opcionais: `orgao`, `member_category`,
  `rights_suspended_until`, `residence_island`.
- Ajustar promote/demote/transfer para key.

### Fase M2 — Script de migração

Criar `scripts/migrate_governance_cargos.py` com:

- `--dry-run`: relatório de cargos actuais e destino.
- `--apply`: normaliza `users.doc.cargo`, preenche `orgao`,
  `member_category="ordinario"`, `account_type="member"` onde ausente.
- conta técnica permanece fora do catálogo.
- normaliza `cargo_history[].cargo` para key e guarda `label`.

Confirmar com o utilizador antes de `--apply`.

### Fase M3 — Remoção de compatibilidade

Só depois de testes e migração:

- frontend deixa de enviar labels.
- testes antigos actualizados.
- aliases ficam apenas para leitura/migração.

---

## 17. Plano de execução

| Fase | Entrega | Depende |
|---|---|---|
| 0 | `governance.py`, helpers, endpoint structure, aliases | — |
| 1 | modelos/user fields, normalização key, cargos/mandatos adaptados | 0 |
| 2 | RBAC/elegibilidade, voto e suspensão de direitos | 1 |
| 3 | Assembleia Geral | 1, 2 |
| 4 | Eleições e proclamação de mandatos | 1, 2, 3 |
| 5 | Disciplina | 2, 3 |
| 6 | Quotas/jóias com deliberação | 3 |
| 7 | Frontend completo e docs | todas |
| 8 | Migração real dos dados | 0-2 + confirmação |

Recomendação: PRs por fase. Não misturar migração destrutiva com UI.

---

## 18. Testes obrigatórios

### Unitários

- `normalize_cargo`: labels/aliases antigos → keys.
- `cargo_info`: inclui Relator e Secretário sem "-Geral".
- `privileges_for_cargo("dir_presidente")` expande `ALL`.
- `orgao_of_cargo`, `seats_for_cargo`.
- `is_voting_member`: honorário, inactivo, técnico e suspenso não votam.
- cálculo de quórum/maiorias com arredondamentos.
- `election_slots`: cargos repetidos e suplentes correctos.

### Rotas

- `/governance/structure`: shape completo e sem labels duplicados.
- `/users/meta/cargos`: alias temporário compatível.
- promote/transfer gravam key, `orgao`, privilégios default e histórico.
- Conselho Fiscal lê finanças, mas recebe 403 na escrita.
- Mesa AG convoca assembleia; sócio comum recebe 403.
- quórum 1.ª/2.ª chamada.
- representação: max 3, Mesa não representa.
- lista eleitoral incompleta rejeitada.
- candidato duplicado na lista rejeitado.
- Comissão Eleitoral candidata rejeitada.
- voto duplo bloqueado por índice único/transacção.
- boletim não contém `user_id` nem `voter_hash`.
- expulsão sem assembleia/deliberação rejeitada.
- multa > 3x quota rejeitada.
- perda de direitos bloqueia voto/candidatura.
- alteração de quota sem deliberação 3/4 rejeitada.

### Frontend

- forms enviam keys e exibem labels.
- menus respeitam privilégios/cargos.
- fiscal vê financeiro em modo leitura.
- UI de assembleia mostra quórum e maioria correcta.
- UI de eleição não expõe dados que liguem eleitor a voto.

---

## 19. Critérios de aceitação

- `backend/governance.py` é a fonte única de governança.
- `models.py` não contém listas hard-coded divergentes; só re-exporta.
- Cargos estatutários reflectem 3 órgãos, Relator e Secretário correcto.
- Coordenações/comissões não aparecem como órgãos/cargos estatutários.
- `users.doc.cargo` e `cargo_history[].cargo` usam keys canónicas.
- Honorário, técnico, inactivo e suspenso não votam.
- Quórum, maiorias e deliberações são calculados por helpers testados.
- Voto secreto não liga eleitor ao boletim.
- Proclamação eleitoral cria mandatos e respeita posse/cessantes.
- Expulsão exige deliberação de AG.
- Quota/jóia exigem deliberação qualificada.
- Testes verdes e frontend sem hard-code de cargos/privilégios.

---

## 20. Stop conditions

Confirmar com o utilizador antes de:

- Executar migração `--apply` em `users` ou `cargo_history`.
- Limpar/recriar dados.
- Enviar emails reais.
- Alterar Pydantic de forma incompatível com documentos existentes.
- Remover rotas que o frontend ainda chama.
- Tratar voto digital como juridicamente vinculativo sem validação expressa da
  Direcção/Mesa/Regimento.

---

## 21. Decisões em aberto

1. **Documentos oficiais**: onde ficam anexados/guardados para auditoria da
   implementação?
2. **Voto digital**: juridicamente vinculativo ou apenas apoio administrativo?
3. **Direcção com 5 ou 7 titulares**: valor default por mandato e quando activar
   os 2 vogais extra.
4. **Representação de honorário**: confirmar regra exacta e como comprovar no
   sistema.
5. **Residência no Sal**: campo obrigatório no perfil ou validação manual?
6. **Funções operacionais**: criar já `operational_assignments` ou adiar?
7. **Terminologia**: manter labels em português cabo-verdiano tradicional
   (`Direcção`, `Acta`) ou uniformizar para nova ortografia (`Direção`, `Ata`) na
   UI, preservando labels estatutários no backend?
