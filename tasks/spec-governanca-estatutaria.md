# Spec — Governança Estatutária da ACCTA

> **Status**: rascunho, a aprovar antes de implementar.
> **Objetivo**: parametrizar os **cargos, órgãos e funções** da ACCTA para
> implementação real, alinhados aos **Estatutos** e ao **Regimento da
> Assembleia Geral** (documentos oficiais), e construir o **módulo de
> governança completo** (Assembleia, Eleições, Regime Disciplinar, Quotas/Jóias).
> **Estado do sistema**: ainda não em produção, sem sócios reais — podemos
> migrar agressivamente sem receio de perda de dados.

## Specs relacionados (ler antes de executar)

- **`tasks/spec-identidade-cargos.md`** — infra genérica de identidade/cargos
  (account_type, `member_id` imutável, `cargo_history`, promote/demote/transfer,
  `CARGO_DEFAULTS`, `CARGO_SEATS`, RBAC granular). **Este spec SUPERSEDE a parte
  de "estrutura de cargos" daquele**, corrigindo-a para a realidade estatutária
  (ver §3 e §4). A maquinaria de promote/transfer/cargo_history daquele spec é
  **reaproveitada tal-e-qual**.
- **`tasks/spec-auto-registo.md`** — fluxo de auto-registo + aprovação. Compatível;
  só muda o catálogo de cargos declaráveis e os defaults aplicados na aprovação.

> ⚠️ **Divergências a corrigir no `spec-identidade-cargos.md`** (foi escrito sem
> os estatutos): `"Secretário-Geral"` → `"Secretário"`; **adicionar `Relator` ao
> Conselho Fiscal** (Art. 35); `"Coordenações"`/`"Comissões"` **não são órgãos
> estatutários** — passam a "funções operacionais" opcionais e separadas (§3.4);
> faltam categorias de membro, mandato eleitoral, assembleia e disciplina.

---

## 1. Contexto e princípio

A ACCTA (Associação Caboverdiana dos Controladores de Tráfego Aéreo) tem uma
estrutura de governança definida nos Estatutos (vigor desde 1/Jan/2011) e no
Regimento da Assembleia Geral (Deliberação 001/AG/ACCTA/2012). O portal hoje
modela **roles técnicos** (`admin/socio/financeiro/moderador`) e um campo `cargo`
**puramente cosmético** — não há noção de **órgão social**, **categoria de
membro**, **mandato**, nem dos processos estatutários (assembleia, eleições,
disciplina).

**Princípio** (herdado do `spec-identidade-cargos.md`, mantido):

> Uma pessoa = uma conta para a vida. `member_id` imutável. `role` + `cargo` +
> `orgao` são atribuídos pelo admin e mudam ao longo do mandato. O histórico de
> mandatos vive na conta pessoal (`cargo_history`). A estrutura de governança é
> **parametrizada numa fonte única** (`backend/governance.py`) consumida pelo
> backend (validação + derivação de privilégios) e pelo frontend (dropdowns).

---

## 2. Fonte estatutária (referência autoritativa)

Estrutura extraída dos documentos oficiais. **Esta secção é a fonte de verdade**
para todas as constantes em §3.

### 2.1 Órgãos sociais (Estatutos Art. 16)

| Órgão | Natureza | Composição | Artigos |
|-------|----------|------------|---------|
| **Assembleia Geral** | Deliberativo máximo; todos os membros | Dirigida pela **Mesa da AG** | 16, 17, 18 |
| **Direcção** | Executivo/administrativo | 5 a 7 titulares | 16, 27 |
| **Conselho Fiscal** | Fiscalização económico-financeira | 3 titulares | 16, 35 |

### 2.2 Cargos por órgão

- **Mesa da Assembleia Geral** (Art. 18, 25, 26): Presidente, Vice-Presidente,
  Secretário.
- **Direcção** (Art. 27): Presidente, Vice-Presidente, Secretário, Tesoureiro,
  Vogal — *podendo ter mais 2 vogais* afetos a órgãos ATC fora da sede (→ 5 ou 7
  membros). O **Presidente da Direcção é o Presidente da ACCTA** (Art. 32).
- **Conselho Fiscal** (Art. 35): Presidente, **Relator**, Vogal.

### 2.3 Categorias de membro (Art. 8)

| Categoria | Definição | Vota? |
|-----------|-----------|-------|
| **Fundador** | CTA caboverdiano no ativo à data da fundação | Sim |
| **Ordinário** | Exerce/exerceu funções de CTA; admitido pela Direcção | Sim |
| **Honorário** | Serviços relevantes; eleito pela AG (2/3) sob proposta da Direcção | **Não** (exceto em representação de fundador/ordinário — Regimento Art. 32.3) |

Direitos (Art. 9) e deveres (Art. 10): eleger/ser eleito, propor admissões,
participar, votar; pagar quotas/jóias, exercer cargos, comparecer.

### 2.4 Mandato e eleições (Cap. V, Art. 39-52)

- Mandato de **3 anos**, sufrágio **secreto**, **listas plurinominais**, **sem
  cumulação de cargos** (Art. 39.1).
- **Suplentes**: 2 para a Direcção, 1 para cada um dos restantes órgãos (Art. 39.5).
- Titulares cessantes mantêm-se até à posse dos novos (Art. 39.9); posse nos 15
  dias seguintes à proclamação (Art. 39.2).
- Listas têm de apresentar candidatos para **todos** os órgãos + suplentes
  (Art. 45.2).
- Organização: **Mesa da AG** (Art. 40) + **Comissão Eleitoral** (2 membros +
  1 por lista, não podem ser candidatos — Art. 52) + **Mesa de Voto** (≥2
  membros — Art. 41).
- Capacidade eleitoral: todos os membros no pleno gozo dos direitos (Art. 42).
- Cadernos eleitorais (Art. 44); candidaturas até 10 dias antes (Art. 45);
  convocatória eleitoral ≥20 dias (Art. 43.3).
- Votação (Art. 48): urna única na sede; **voto por correspondência** permitido
  com impedimento justificado; **sem voto por procuração nas eleições** (Art. 48.4).
- Voto branco/nulo (Art. 49). Apuramento pela Mesa de Voto; **lista vencedora =
  maioria simples** dos votos válidos (Art. 50.4); empate → nova eleição em 15
  dias (Art. 50.5). Recurso em 3 dias (Art. 51).

### 2.5 Funcionamento da Assembleia (Estatutos Art. 19-26 + Regimento)

- **Sessão ordinária**: 1×/ano no 1º trimestre — apreciar contas, eleições (se
  ano eleitoral), aprovar orçamento/plano (Art. 19.1).
- **Extraordinária**: convocação do Presidente da Mesa a requerimento da Mesa,
  Direcção, Conselho Fiscal ou ≥1/4 dos membros (Art. 19.2).
- **Convocatória** ≥10 dias, com dia/hora/local + ordem do dia (Art. 20).
- **Quórum** (Art. 21): maioria dos membros em 1ª convocatória; ½h depois, ≥1/3
  em 2ª convocatória.
- **Deliberação** (Art. 22): **maioria absoluta** dos presentes; **3/4** para
  alteração de estatutos e fixação de quota/jóia (Art. 22.4 ref. Art. 24.2 d/e);
  **3/4 do universo de membros** para dissolução (Art. 55).
- **Representação** (Art. 23): um membro representa no máximo **3 outros** (só 1
  residente no Sal); titulares da Mesa não podem representar.
- **Votação** (Regimento Art. 32): braço no ar / de pé, ou nominal/secreta;
  honorários não votam; voto de qualidade do Presidente da Mesa (Art. 33).
- **Actas** (Regimento Art. 37): assinadas por Presidente + Secretário,
  disponíveis na sede em 30 dias.

### 2.6 Regime disciplinar (Cap. III, Art. 11-15)

- **Sanções** (Art. 12): (a) advertência escrita, (b) multa ≤3× quota,
  (c) perda de direitos ≤1 ano, (d) **expulsão**.
  - a/b/c → competência da **Direcção**; (d) expulsão → competência **exclusiva
    da AG**, sob proposta da Direcção (Art. 12.2/12.3).
  - Comunicada por escrito; recurso à AG em 15 dias para b/c (Art. 12.5).
- **Processo** (Art. 13): **Comissão de Inquérito** de 3 elementos (1 da
  Direcção, 1 do averiguado, 1 por consenso); conclusões em 30 dias; poder
  disciplinar da Direcção caduca se não exercido em 30 dias.
- **Perda de qualidade** (Art. 14): demissão escrita; expulsão; **não pagamento
  de quotas 3 meses consecutivos** + após aviso, 6 meses sem regularizar.
- **Readmissão** (Art. 15): cumprir condições de admissão; expulsos só por
  deliberação da AG; pagar todas as dívidas.

> ⚠️ **Tensão com invariante do projeto**: o `CLAUDE.md` define *"No inadimplente
> status — quotas are payroll-deducted"*. O Art. 14.c (perda por não pagamento)
> existe nos estatutos mas é praticamente inaplicável (quotas descontadas em
> folha). **Decisão recomendada** (§16): modelar sanções/expulsão como workflow,
> mas **NÃO** introduzir status "inadimplente"; perda por não pagamento fica como
> processo manual de exceção, preservando o invariante.

### 2.7 Quotas e jóias (Art. 6, 7, 24.e, 34, 54)

- Valor da **quota** fixado pela AG (Art. 7, 24.2.e).
- **Jóia = 2× a quota** em vigor, devida por novos membros já qualificados como
  CTA há >4 meses (Art. 6).
- O **Tesoureiro** guarda valores, movimenta a conta, apresenta balancetes
  (Art. 34). Movimentação da conta exige assinatura do Tesoureiro (Art. 54.2).

---

## 3. Parametrização (núcleo) — `backend/governance.py` (NOVO)

Fonte única de verdade. **Sem imports de `models`** (para evitar ciclos);
`models.py` passa a **re-exportar** daqui para retro-compatibilidade
(`from models import CARGOS, PRIVILEGES, CARGOS_DECLARADOS` continua a funcionar).

### 3.1 Órgãos

```python
ASSEMBLEIA_GERAL = "assembleia_geral"
DIRECAO = "direcao"
CONSELHO_FISCAL = "conselho_fiscal"

ORGAOS = {
    ASSEMBLEIA_GERAL: {"id": ASSEMBLEIA_GERAL, "nome": "Assembleia Geral",
        "tipo": "deliberativo", "tem_mesa": True, "mandato_anos": 3,
        "suplentes": 1, "artigos": "16,17,18"},
    DIRECAO: {"id": DIRECAO, "nome": "Direcção", "tipo": "executivo",
        "tem_mesa": False, "mandato_anos": 3, "suplentes": 2, "artigos": "16,27"},
    CONSELHO_FISCAL: {"id": CONSELHO_FISCAL, "nome": "Conselho Fiscal",
        "tipo": "fiscalizacao", "tem_mesa": False, "mandato_anos": 3,
        "suplentes": 1, "artigos": "16,35"},
}
```

### 3.2 Catálogo de cargos estatutários (corrigido vs. estatutos)

Cada cargo tem `key` (estável, qualificado por órgão), `label` (display),
`orgao`, `seats`, `role`/`privileges` default, e flags.

```python
CARGOS_CATALOG = [
    # Mesa da Assembleia Geral (Art. 18, 25, 26)
    {"key": "ag_presidente",      "label": "Presidente da Mesa da AG",      "orgao": ASSEMBLEIA_GERAL, "ordem": 1, "seats": 1, "role": "socio",      "privileges": ["manage_events"]},
    {"key": "ag_vice_presidente", "label": "Vice-Presidente da Mesa da AG", "orgao": ASSEMBLEIA_GERAL, "ordem": 2, "seats": 1, "role": "socio",      "privileges": []},
    {"key": "ag_secretario",      "label": "Secretário da Mesa da AG",      "orgao": ASSEMBLEIA_GERAL, "ordem": 3, "seats": 1, "role": "socio",      "privileges": ["manage_documents"]},
    # Direcção (Art. 27, 32, 33, 34)
    {"key": "dir_presidente",     "label": "Presidente da Direcção",        "orgao": DIRECAO, "ordem": 1, "seats": 1, "role": "admin",      "privileges": "ALL", "is_president_accta": True},
    {"key": "dir_vice_presidente","label": "Vice-Presidente da Direcção",   "orgao": DIRECAO, "ordem": 2, "seats": 1, "role": "admin",      "privileges": "ALL"},
    {"key": "dir_secretario",     "label": "Secretário da Direcção",        "orgao": DIRECAO, "ordem": 3, "seats": 1, "role": "admin",      "privileges": ["manage_users","manage_events","manage_documents","moderate_content"]},
    {"key": "dir_tesoureiro",     "label": "Tesoureiro",                    "orgao": DIRECAO, "ordem": 4, "seats": 1, "role": "financeiro", "privileges": ["manage_finances","view_audit_logs"]},
    {"key": "dir_vogal",          "label": "Vogal da Direcção",             "orgao": DIRECAO, "ordem": 5, "seats": 3, "role": "moderador",  "privileges": ["moderate_content","manage_events"]},
    # Conselho Fiscal (Art. 35, 38) — NOTA: inclui Relator (faltava no spec antigo)
    {"key": "cf_presidente",      "label": "Presidente do Conselho Fiscal", "orgao": CONSELHO_FISCAL, "ordem": 1, "seats": 1, "role": "socio", "privileges": ["view_finances_readonly","view_audit_logs"]},
    {"key": "cf_relator",         "label": "Relator do Conselho Fiscal",    "orgao": CONSELHO_FISCAL, "ordem": 2, "seats": 1, "role": "socio", "privileges": ["view_finances_readonly","view_audit_logs"]},
    {"key": "cf_vogal",           "label": "Vogal do Conselho Fiscal",      "orgao": CONSELHO_FISCAL, "ordem": 3, "seats": 1, "role": "socio", "privileges": ["view_finances_readonly","view_audit_logs"]},
    # Base
    {"key": "socio",              "label": "Sócio",                         "orgao": None,    "ordem": 99, "seats": 0, "role": "socio", "privileges": []},
]
```

> **`"ALL"`** expande para a lista completa de `PRIVILEGES`. `seats` para
> `dir_vogal` = 3 (1 vogal base + até 2 vogais extra de órgãos ATC fora da sede,
> Art. 27). `seats=0` para Sócio = sem limite/sem mandato.

### 3.3 Categorias de membro, privilégios, roles, mandato

```python
MEMBER_CATEGORIES = ["fundador", "ordinario", "honorario"]
MEMBER_CATEGORY_LABELS = {"fundador": "Fundador", "ordinario": "Ordinário", "honorario": "Honorário"}
VOTING_CATEGORIES = {"fundador", "ordinario"}        # honorário não vota (Reg. Art. 32.3)
DEFAULT_MEMBER_CATEGORY = "ordinario"

PRIVILEGES = ["manage_users","manage_finances","manage_events","manage_documents",
              "moderate_content","manage_benefits","view_audit_logs",
              "view_finances_readonly"]              # +1 (Conselho Fiscal: leitura)
PRIVILEGE_LABELS = { ... }                            # PT (centraliza o que está no frontend)

ROLES = ["admin", "financeiro", "moderador", "socio"]
ROLE_LABELS = {"admin": "Administrador", "financeiro": "Financeiro", "moderador": "Moderador", "socio": "Sócio"}

MANDATO_ANOS = 3

# Cargos declaráveis no auto-registo (informativo; admin confirma na aprovação).
# Mantido simples por órgão — alinhar com CARGOS_CATALOG labels + nomes de órgão.
CARGOS_DECLARADOS = ["Sócio","Vogal","Tesoureiro","Secretário","Vice-Presidente",
                     "Presidente","Direcção","Conselho Fiscal","Mesa da Assembleia"]
```

### 3.4 Funções operacionais (NÃO estatutárias, opcionais)

O `spec-identidade-cargos.md` incluía Coordenações/Comissões. Como **não são
órgãos estatutários**, ficam num catálogo separado e opcional, claramente
distinto dos cargos eleitos. Podem ser usadas para grupos de trabalho (Art. 31.e
permite à Direcção criar grupos de trabalho eventuais e designar coordenadores).

```python
FUNCOES_OPERACIONAIS = [   # opcional; NÃO entram em cargo_history estatutário
    {"key": "coord_comunicacao", "label": "Coordenador de Comunicação", "privileges": ["moderate_content","manage_events"]},
    {"key": "coord_eventos",     "label": "Coordenador de Eventos",     "privileges": ["manage_events"]},
    {"key": "coord_projetos",    "label": "Coordenador de Projectos",   "privileges": ["manage_events","manage_documents"]},
]
```

### 3.5 Helpers (assinaturas)

```python
def cargo_info(cargo_key_or_label) -> dict | None      # resolve por key OU label, com aliases legados
def normalize_cargo(value) -> str                       # legacy label -> key canónico
def privileges_for_cargo(cargo) -> list[str]            # expande "ALL"
def role_for_cargo(cargo) -> str
def orgao_of_cargo(cargo) -> str | None
def seats_for_cargo(cargo) -> int
def is_voting_member(user_doc) -> bool                  # categoria ∈ VOTING_CATEGORIES e status ativo
def governance_structure() -> dict                      # payload do endpoint /governance/structure

LEGACY_CARGO_ALIASES = {
    "Presidente": "dir_presidente", "Vice-Presidente": "dir_vice_presidente",
    "Secretário-Geral": "dir_secretario", "Secretário": "dir_secretario",
    "Tesoureiro": "dir_tesoureiro", "Vogal": "dir_vogal",
    "Membro da Direção": "dir_vogal", "Sócio": "socio",
    # "Administrador" (conta técnica) NÃO mapeia para cargo estatutário
}

# Derivado para retro-compat (models.py re-exporta):
CARGOS = [c["label"] for c in CARGOS_CATALOG]           # labels canónicos
CARGO_KEYS = [c["key"] for c in CARGOS_CATALOG]
CARGO_DEFAULTS = {c["key"]: {"role": c["role"], "privileges": privileges_for_cargo(c["key"])} for c in CARGOS_CATALOG}
CARGO_SEATS = {c["key"]: c["seats"] for c in CARGOS_CATALOG}
```

**Validação de `cargo`** (em writes): aceitar `key` canónico **ou** label
canónico **ou** alias legado; normalizar sempre para `key` ao gravar. Tolerância
durante transição evita partir dados/Testes existentes.

---

## 4. Alterações ao modelo de dados (`backend/models.py`)

Campos **aditivos e opcionais** (retro-compatíveis; `extra="ignore"` já está nos
modelos). Re-exportar constantes de `governance`.

```python
from governance import (CARGOS, CARGO_KEYS, PRIVILEGES, CARGOS_DECLARADOS,
                        MEMBER_CATEGORIES, ROLES, ORGAOS, MANDATO_ANOS,
                        CARGO_DEFAULTS, CARGO_SEATS)  # re-export

ACCOUNT_TYPES = ["member", "technical"]               # de spec-identidade-cargos

class UserBase(BaseModel):
    # ... campos existentes ...
    account_type: Literal["member","technical"] = "member"
    orgao: Optional[str] = None                       # ∈ ORGAOS keys ou None
    member_category: str = "ordinario"                # ∈ MEMBER_CATEGORIES
    cargo: str = "socio"                              # KEY canónico ("socio","dir_tesoureiro",...); label só para display. NUNCA usar o label "Sócio" como default — partiria CARGO_DEFAULTS/orgao_of_cargo/seat checks

class CargoMandate(BaseModel):                        # entrada de cargo_history
    cargo: str; role: str; orgao: Optional[str] = None
    inicio: str; fim: Optional[str] = None            # ISO 8601; None = ativo
    suplente: bool = False
    elected_by: Optional[str] = None                  # "AGE 2026", "Direcção"...
    transitioned_by: str; notes: Optional[str] = None
```

`cargo_history` (array em `users.doc`), `PromoteUserRequest`,
`TransferCargoRequest` — **conforme `spec-identidade-cargos.md` §1-3** (reusar).

**Novos modelos** para os módulos de governança em §8 (Assembleia, Eleição,
Sanção). **Datas sempre como strings ISO 8601** (regra do projeto).

---

## 5. Novas coleções (Postgres/Supabase via `database.py::ensure_schema`)

Cada coleção = tabela `(pk bigserial, doc jsonb)`. Adicionar em `ensure_schema()`
+ índices por expressão (`doc->>'campo'`), seguindo o padrão existente. **Sem SQL
cru nas rotas.**

| Coleção | Conteúdo | Índices |
|---------|----------|---------|
| `assembleias` | Sessões da AG (convocatória, ordem de trabalhos, presenças, deliberações, acta) | `(doc->>'status')`, `(doc->>'tipo')`, `(doc->>'data')` |
| `assembleia_presencas` | Presença/representação por sessão | `(doc->>'assembleia_id')`, `(doc->>'user_id')` |
| `eleicoes` | Atos eleitorais (mandato, calendário, comissão, mesa de voto, listas, resultado) | `(doc->>'status')`, `(doc->>'ano')` |
| `eleicao_listas` | Listas candidatas (letra, candidatos por cargo+suplentes, programa) | `(doc->>'eleicao_id')` |
| `eleicao_votos` | Votos (secreto: registo de *quem votou* separado do *sentido de voto*) | **UNIQUE** `(doc->>'eleicao_id', doc->>'voter_hash')` — garante **1 voto/eleitor atomicamente** sob escrita concorrente; checks só na aplicação não bastam (race) |
| `sancoes` | Processos disciplinares (tipo, comissão de inquérito, decisão, recurso) | `(doc->>'user_id')`, `(doc->>'status')` |

> **Voto secreto** (Art. 48): separar a *lista de quem votou* (para evitar voto
> duplo e conferência de assinaturas, Art. 50.1) do *boletim* (sentido de voto)
> que não pode ser ligado ao eleitor. Modelar `eleicao_votos` com `voter_hash`
> (marca que votou) e contagem agregada de boletins por lista, **sem FK
> voter→boletim**. O **índice UNIQUE `(eleicao_id, voter_hash)`** é o guard de
> unicidade do voto: o INSERT do "já votou" tem de ser a operação atómica que
> falha no 2º voto — não confiar em `find`+`insert` na aplicação (TOCTOU sob
> concorrência). `ensure_schema()` deve criar este índice como `UNIQUE`.

---

## 6. Enforcement (RBAC por cargo/privilégio)

Adotar a **matriz RBAC do `spec-identidade-cargos.md` §"Matriz RBAC obrigatória"**
(Finanças view/manage split, Eventos, Documentos, Conteúdo, Benefícios,
Auditoria, Utilizadores). Pontos-chave:

- Helper comum em `auth.py` ou novo `permissions.py`:
  `user_can(user, privilege) -> bool` = `user.role == "admin" or privilege in (user.privileges or [])`.
  Manter o `role` como gate "grosso"; `privileges` como overlay (já é o padrão em
  `documents.py:18-19`).
- **Tesoureiro** (`dir_tesoureiro`) → `manage_finances` (escrita financeira).
- **Conselho Fiscal** → `view_finances_readonly` (leitura financeira, **sem
  escrita**) + `view_audit_logs`. Separação de poderes (Art. 37: fiscaliza, não
  executa). Frontend desativa botões de escrita.
- **Mesa da AG** → `manage_events` (gere assembleias) + `manage_documents`
  (actas). Só a **Mesa** pode criar/convocar assembleias e abrir eleições.
- **Derivação automática**: ao definir/alterar `cargo` (invite, aprovação,
  promote, update), se `privileges` não vierem explícitos no request, aplicar
  `CARGO_DEFAULTS[cargo]`. Admin pode sempre sobrepor.
- **Votação estatutária**: elegibilidade de voto (assembleia e eleições) exige
  `is_voting_member(user)` → categoria ∈ {fundador, ordinário} e `status=ativo`.
  Honorário só vota em representação (assembleia), nunca nas eleições (Art. 48.4
  proíbe procuração eleitoral).

---

## 7. Endpoint de parametrização

### `GET /api/governance/structure` (NOVO — `routes/governance.py`)

Público/autenticado leve. Devolve a estrutura completa para o frontend (elimina
hard-code de cargos/privilégios no React):

```json
{
  "orgaos": [ ... ],
  "cargos": [ {"key","label","orgao","seats","role_default","privileges_default"} ],
  "funcoes_operacionais": [ ... ],
  "member_categories": [ {"key","label","vota"} ],
  "privileges": [ {"key","label"} ],
  "roles": [ {"key","label"} ],
  "mandato_anos": 3
}
```

Substitui/expande `GET /api/users/meta/cargos` e `/meta/privileges` (manter os
antigos como aliases finos para não partir `test_member_profile_crud.py`, **ou**
atualizar esses testes — ver §13).

---

## 8. Módulos de governança ("completo")

Cada módulo: coleção(ões) + rotas + RBAC + regras estatutárias + aceitação.
Reaproveitam módulos existentes onde indicado (§11).

### 8.1 Assembleia Geral — `routes/assembleias.py` (NOVO)

Modela sessões da AG. **Reaproveita** padrões de `events` (data/local) e
`documents` (acta) e `notifications` (convocatória).

**Modelo `Assembleia`**: `id, tipo (ordinaria|extraordinaria|eleitoral),
titulo, data, local, convocada_por, convocatoria_em, antecedencia_dias,
ordem_trabalhos: [{ponto, descricao}], status (convocada|em_curso|encerrada),
quorum_1a, quorum_2a, presentes, representados, deliberacoes:
[{ponto, tipo_maioria (absoluta|qualificada_3_4), a_favor, contra, abstencoes,
aprovada}], acta_document_id, created_at`.

**Regras estatutárias a aplicar**:
- Convocatória ≥10 dias (≥20 se eleitoral) — validar `antecedencia_dias` (Art. 20, 43).
- Só a **Mesa da AG** (cargo `ag_*`) ou admin convoca.
- Extraordinária exige requerente válido (Mesa/Direcção/Conselho Fiscal/≥1/4
  membros) — Art. 19.2.
- Quórum (Art. 21): 1ª = maioria; 2ª (½h depois) = ≥1/3. Calcular base = nº de
  membros votantes ativos.
- Deliberação: maioria absoluta dos presentes; **3/4** para alteração de
  estatutos e fixação de quota/jóia (Art. 22.4); registar `tipo_maioria` por ponto.
- Representação: máx. 3 por membro, só 1 residente no Sal (Art. 23); Mesa não
  representa. Honorário não vota salvo em representação.
- Acta gerada/anexada (documento) e disponível em 30 dias (Regimento Art. 37).

**Endpoints**: `POST /assembleias` (convocar), `GET /assembleias`,
`GET /assembleias/{id}`, `POST /assembleias/{id}/presencas` (check-in +
representações), `POST /assembleias/{id}/deliberacoes` (registar votação de um
ponto), `POST /assembleias/{id}/encerrar` (anexa acta), `GET
/assembleias/{id}/quorum` (estado em tempo real).

### 8.2 Eleições — `routes/eleicoes.py` (NOVO)

**Reaproveita** `polls` (mecânica de votação) mas com regras eleitorais.

**Modelo `Eleicao`**: `id, ano, mandato_inicio, mandato_fim (inicio+3 anos),
status (preparacao|candidaturas|campanha|votacao|apurada|recurso|proclamada),
calendario: {convocatoria, fim_candidaturas, inicio_campanha, dia_votacao},
comissao_eleitoral: [user_id], mesa_voto: [user_id], assembleia_id, resultado:
{lista_vencedora, votos_por_lista, brancos, nulos, total_validos}`.

**Modelo `EleicaoLista`**: `id, eleicao_id, letra (A,B,...), candidatos:
{cargo_key: user_id, ...} (todos os órgãos + suplentes — Art. 45.2),
programa_document_id, aceitacao: bool, estado (submetida|aceite|rejeitada)`.

**Regras estatutárias**:
- Capacidade eleitoral = `is_voting_member` (Art. 42).
- Listas têm de preencher **todos** os cargos eleitos + suplentes (2 Direcção, 1
  por órgão) — validar contra `CARGOS_CATALOG`/`ORGAOS.suplentes` (Art. 45.2, 39.5).
- Comissão Eleitoral: membros não podem ser candidatos (Art. 52.3).
- Voto **secreto** (modelo de §5): permitir **voto por correspondência** com
  justificação (Art. 48.5); **sem procuração** (Art. 48.4).
- Apuramento: maioria simples dos válidos (Art. 50.4); empate → flag para nova
  eleição em 15 dias (Art. 50.5).
- **Proclamação** → criar mandatos: para cada cargo da lista vencedora, chamar a
  maquinaria `promote`/`transfer` (spec-identidade-cargos) e abrir entrada em
  `cargo_history` com `inicio=mandato_inicio`, `elected_by="AGE {ano}"`,
  `fim=mandato_fim`. Cessantes mantêm-se até à posse (Art. 39.9).

**Endpoints**: `POST /eleicoes`, `GET /eleicoes`, `POST /eleicoes/{id}/listas`,
`POST /eleicoes/{id}/listas/{lid}/validar`, `POST /eleicoes/{id}/abrir-votacao`,
`POST /eleicoes/{id}/votar` (1 voto/eleitor, marca `voter_hash`),
`POST /eleicoes/{id}/voto-correspondencia`, `POST /eleicoes/{id}/apurar`,
`POST /eleicoes/{id}/proclamar` (gera mandatos).

### 8.3 Regime disciplinar — `routes/disciplinar.py` (NOVO)

**Reaproveita** `audit_logs` (rasto) + `notifications`.

**Modelo `Sancao`**: `id, user_id, tipo (advertencia|multa|perda_direitos|
expulsao), motivo, artigo_violado, status (proposta|inquerito|decidida|recurso|
aplicada|arquivada), comissao_inquerito: [{nomeado_por, user_id}] (3 elementos),
inquerito_prazo (30d), decisao: {por (direcao|assembleia), data, resultado},
multa_valor, perda_direitos_ate (data), recurso: {interposto_em, decidido_em,
resultado}, created_at`.

**Regras estatutárias**:
- a/b/c (advertência/multa/perda) → competência **Direcção** (cargos `dir_*` ou
  admin). (d) **expulsão** → exige deliberação da **AG** (ligar a uma
  `assembleia` + deliberação) sob proposta da Direcção (Art. 12.2/12.3).
- Comissão de Inquérito: 3 elementos (1 Direcção, 1 averiguado, 1 consenso),
  conclusões em 30 dias; caducidade do poder disciplinar em 30 dias (Art. 13).
- Multa ≤ 3× quota (validar contra `finance_settings.quota_amount`) (Art. 12.1.b).
- Recurso à AG em 15 dias para b/c (Art. 12.5).
- **Perda de qualidade** (Art. 14): expulsão aplicada → `status="inativo"` (NÃO
  "inadimplente"). Readmissão (Art. 15) → fluxo manual com quitação de dívidas.

**Endpoints**: `POST /sancoes` (instaurar), `POST /sancoes/{id}/comissao`,
`POST /sancoes/{id}/decidir`, `POST /sancoes/{id}/recurso`,
`GET /sancoes` (admin/direção), `GET /users/{id}/sancoes` (próprio/admin).

### 8.4 Quotas e jóias — estender `routes/finances.py` + `finance_settings`

- `FinanceSettings`: adicionar `joia_amount` (default = `2 × quota_amount`,
  Art. 6) e `quota_fixed_by` (ref. à deliberação da AG que fixou — Art. 24.2.e).
- Alteração de quota/jóia deve referenciar uma **deliberação de assembleia** com
  maioria qualificada 3/4 (Art. 22.4) — registar `assembleia_id` na auditoria.
- Jóia aplicada no auto-registo/convite de membro qualificado há >4 meses
  (campo informativo; cobrança real via `invoices`/folha).

---

## 9. Resumo de endpoints (novos + alterados)

| Método | Rota | Módulo | RBAC |
|--------|------|--------|------|
| GET | `/api/governance/structure` | §7 | autenticado |
| GET | `/api/users/{id}/cargo-history` | identidade | próprio/admin |
| POST | `/api/admin/users/{id}/promote` `/demote` | identidade | admin/`manage_users` |
| POST | `/api/admin/cargos/transfer` | identidade | admin/`manage_users` |
| GET | `/api/admin/cargos` `/cargos/candidates` | identidade | admin/`manage_users` |
| POST/GET | `/api/assembleias…` | §8.1 | Mesa AG/admin (escrita) |
| POST/GET | `/api/eleicoes…` | §8.2 | Mesa AG/Comissão/admin |
| POST/GET | `/api/sancoes…` | §8.3 | Direcção/admin; expulsão→AG |
| PATCH | `/api/finances/settings` (quota+jóia) | §8.4 | admin/`manage_finances` |

Registar todos os routers novos em `backend/routes/__init__.py`.

---

## 10. Frontend (`frontend/src/`)

- **Substituir hard-code** de cargos/privilégios por `GET /api/governance/structure`
  em: `pages/private/AdminUsuariosPage.js` (constantes linhas ~39-45),
  `pages/public/CriarContaPage.js` (CARGOS_FALLBACK linhas ~11-14),
  `pages/private/AdminPedidosInscricaoPage.js`.
- `AuthContext.js` (linhas 82-84): adicionar derivados de cargo/órgão
  (`isMesaAG`, `isDirecao`, `isConselhoFiscal`, `isTesoureiro`) e helper
  `can(privilege)`.
- `App.js` (ProtectedRoute) + `PrivateLayout.js` (sidebar): novos itens de menu
  por privilégio/cargo (Cargos, Assembleias, Eleições, Disciplinar).
- **Páginas novas**: `/admin/cargos` (quadro de cargos + promote/transfer — ver
  `spec-identidade-cargos.md` §Frontend), `/admin/assembleias`, `/admin/eleicoes`,
  `/admin/disciplinar`. Secção "Os meus cargos/mandatos" em `/perfil`.
- Design: seguir **`.claude/skills/frontend-design`** (neutro + Carmesim como
  único acento; ≤1 botão primário/vista; sem dark mode).
- `utils/api.js`: novos grupos de API (`governanceApi`, `assembleiasApi`,
  `eleicoesApi`, `sancoesApi`, `cargosApi`).

---

## 11. O que aproveitar (reuso explícito)

| Existente | Reuso para |
|-----------|------------|
| `polls` + `user_votes` | Mecânica base de votação das **eleições** (§8.2) e deliberações da AG |
| `events` | Sessões de **assembleia** (data/local/convocatória) (§8.1) |
| `documents` | **Actas**, relatório e contas, regulamentos, convocatórias, programas de lista |
| `invoices` + `finance_settings` | **Quotas e jóias** (§8.4) |
| `audit_logs` | Rasto de **promote/transfer/disciplinar/eleições** |
| `notifications` | Convocatórias, prazos eleitorais, resultados, decisões disciplinares |
| `users.cargo/role/privileges` | **Alvo da parametrização** (§3-4) |
| Maquinaria promote/transfer/`cargo_history` (`spec-identidade-cargos`) | Criação de mandatos na **proclamação** eleitoral (§8.2) |

---

## 12. Migração & retro-compatibilidade

- Sistema sem produção → migração agressiva permitida (mas `cargo` muda de label
  para **key**: correr script único que normaliza `users.doc.cargo` legados via
  `LEGACY_CARGO_ALIASES`, e define `member_category="ordinario"`,
  `account_type="member"` onde ausente; conta técnica → `account_type="technical"`,
  `member_id=None`, `cargo` técnico fora do catálogo — ver `spec-identidade-cargos`
  §"Migração").
- `bootstrap_admin` (`server.py:195-223`) e `scripts/create_admin.py`: marcar
  como `account_type="technical"`, `member_category` irrelevante, `privileges`
  = todos os 8 (incl. `view_finances_readonly`).
- Campos aditivos/opcionais → documentos antigos continuam válidos (`extra="ignore"`).

---

## 13. Testes (padrão `backend/tests/`, `mock_db`, asyncio)

- **`governance.py`**: helpers (`privileges_for_cargo("ALL")`, `normalize_cargo`
  de aliases legados, `is_voting_member` honorário=False).
- **`/governance/structure`**: shape do payload; cargos incluem Relator;
  privilégios incluem `view_finances_readonly`.
- **Atualizar `test_member_profile_crud.py`**: hoje espera `len(cargos)==7` e
  cargos antigos (linhas 69-72) — passa a 12 cargos canónicos. Decidir: atualizar
  asserts (recomendado) ou manter `/meta/cargos` como alias legado de 7 itens
  (não recomendado — esconde a parametrização).
- **`test_auto_registo.py`**: cargo declarado `"Tesoureiro"` continua válido (é
  alias → `dir_tesoureiro`); adicionar caso de derivação de privilégios na
  aprovação.
- **Enforcement**: Tesoureiro escreve finanças; Conselho Fiscal lê mas 403 na
  escrita; Mesa AG cria assembleia, Sócio recebe 403.
- **Módulos**: quórum (1ª/2ª convocatória), maioria 3/4 em alteração de
  estatutos, lista eleitoral incompleta rejeitada, voto duplo bloqueado,
  expulsão exige assembleia, multa > 3× quota rejeitada.
- **bcrypt** fixado em `4.0.1` (regra do projeto) ao criar venv.

---

## 14. Plano de execução por fases (PRs separáveis)

| Fase | Conteúdo | Dependências | Estimativa |
|------|----------|--------------|-----------|
| **0** | Alinhamento: confirmar rotas reais, mapear checks por `role`, definir `user_can` | — | ~45min |
| **1 — Fundação** | `governance.py`; re-export em `models.py`; campos `orgao`/`member_category`/`account_type`/`cargo`(key); `GET /governance/structure`; reconciliar listas; frontend lê do endpoint | — | ~3h |
| **2 — Enforcement** | `user_can`; split finanças view/manage; aplicar privilégios em eventos/docs/conteúdo/benefícios/auditoria; derivação cargo→privilégios | 1 | ~3h |
| **3 — Cargos/Mandatos** | `cargo_history`; promote/demote/transfer; `/admin/cargos` (+candidates); `cargo-history`; UI `/admin/cargos` (de `spec-identidade-cargos`) | 1,2 | ~5h |
| **4 — Assembleia** | coleções `assembleias`/`presencas`; rotas; quórum/maioria/representação; actas; UI `/admin/assembleias` | 1,2 | ~5h |
| **5 — Eleições** | coleções `eleicoes`/`listas`/`votos`; voto secreto + correspondência; apuramento; proclamação→mandatos; UI `/admin/eleicoes` | 3,4 | ~7h |
| **6 — Disciplinar** | coleção `sancoes`; comissão de inquérito; competência Direcção vs AG; recurso; UI `/admin/disciplinar` | 2,4 | ~4h |
| **7 — Quotas/Jóias** | `joia_amount`; vínculo a deliberação da AG; cobrança | 4 | ~2h |
| **8 — Docs** | atualizar `CLAUDE.md`, `.claude/rules/*`, reconciliar `spec-identidade-cargos.md` e `spec-auto-registo.md` | todas | ~1h |

**Total estimado**: ~30h, faseável. Cada fase é entregável e testável de forma
independente. Recomenda-se 1 PR por fase.

### Critérios de aceitação (alto nível)

- A estrutura de governança vem **toda** de `governance.py` (zero hard-code de
  cargos/privilégios no backend e no frontend).
- Cargos refletem os estatutos: 3 órgãos, **Relator** presente, "Secretário" (não
  "-Geral"), Tesoureiro→finanças, Conselho Fiscal→leitura.
- Honorário não vota; quórum e maiorias estatutárias aplicados.
- Eleição proclamada cria mandatos em `cargo_history`.
- Expulsão exige deliberação de assembleia.
- Testes verdes; design system respeitado; sem regressões nas rotas existentes.

---

## 15. Stop conditions (CLAUDE.md)

- **Migração de dados** em `users` (Fase 1/3) → confirmar com o utilizador antes
  de comandos destrutivos.
- **Pydantic models** alterados — só de forma **aditiva/opcional** (não parte
  documentos existentes). A mudança de `cargo` (label→key) requer script de
  normalização (Fase 1) — confirmar.
- **Emails a utilizadores reais** (convite/aprovação) → STOP em sócios reais.
- Não toca em JWT secret, CORS, nem remove rotas usadas pelo frontend.

---

## 16. Decisões em aberto (a confirmar antes da execução)

1. **Não pagamento de quotas** (Art. 14.c) vs. invariante "sem inadimplente":
   recomendação = **não** criar status "inadimplente"; perda por não pagamento é
   processo manual de exceção. **Confirmar.**
2. `cargo` passa a guardar **key** (`dir_tesoureiro`) em vez de label. Alternativa
   menos disruptiva: manter label canónico + campo `orgao`. Recomendação = **key**
   (mais limpo, qualifica o órgão). **Confirmar.**
3. **Funções operacionais** (coordenadores) — manter como catálogo opcional
   separado (§3.4) ou descartar? Recomendação = manter opcional. **Confirmar.**
4. Granularidade do **voto secreto**: pseudonimização por `voter_hash` vs. urna
   totalmente anónima com conferência de cadernos à parte. **Confirmar nível.**
5. Alcance do frontend na 1ª entrega (todas as páginas vs. só `/admin/cargos`).
   **Confirmar.**
