# Spec — Modelo de Identidade e Cargos

> **Status**: rascunho, a aprovar antes de implementar.
> **Estado do sistema**: ainda não em produção, sem sócios reais —
> podemos migrar agressivamente sem receio de perda de dados.
> **Spec relacionado**: `tasks/spec-auto-registo.md` (compatível, não
> conflita).

---

## Contexto e princípio

O sistema actual mistura **identidade** (quem é a pessoa) com **função**
(que cargo ocupa). Contas como `admin@controlador.cv` e
`presidente@controlador.cv` (planeada) são **contas partilhadas de
papel**, o que parte:

- **pontuação dos sócios** — trabalho feito como "presidente" não
  acumula na pessoa real;
- **auditoria** — `audit_logs.user_id` aponta para o papel, não para o
  humano que fez a acção;
- **segurança** — passar passwords entre presidentes/tesoureiros é o
  ataque mais comum em PMEs e associações;
- **continuidade** — transição de mandato exige troca de credenciais e
  perde-se o histórico.

**Princípio que adoptamos**:

> Uma pessoa = uma conta para a vida. `member_id` é imutável. Cargos
> (`role` + `cargo`) são atribuídos pelo admin e mudam ao longo da
> vida do sócio. O histórico de mandatos vive na conta pessoal.

Emails institucionais (`presidente@`, `tesoureiro@`) deixam de ser
contas de login e passam a ser **aliases de email** geridos no
provedor (DNS/mailbox), fora do ACCTA.

---

## Estado actual (snapshot, 2026-05-20)

### Models (`backend/models.py`)

- `UserBase` tem já `role: str = "socio"` e `cargo: str = "Sócio"`.
- Constante `CARGOS = ["Presidente", "Vice-Presidente",
  "Secretário-Geral", "Tesoureiro", "Vogal", "Membro da Direção",
  "Sócio"]` (linha 9).
- Constante `PRIVILEGES` com 7 permissões granulares (linhas 11-19).
- `UserAdminUpdate` permite ao admin alterar `role`/`cargo`/`status`/
  `member_id`/`privileges` — base já existente.

### Contas partilhadas existentes

| Email | Onde aparece | Conta? |
|-------|--------------|--------|
| `admin@controlador.cv` | `create_admin.py`, 17 ficheiros de teste, `server.py:203` | **Sim** — `member_id="ACCTA-ADMIN"` (sentinel), `role=admin`, `cargo="Administrador"` |
| `presidente@controlador.cv` | não existe ainda no código | planeada mas não criada |
| `admin@controlador.com` | mencionada pelo utilizador na conversa | a confirmar |

`create_admin.py` cria a conta sentinel `ACCTA-ADMIN`. Há referências
hard-coded em testes integração-live (`test_*.py` com `import requests`).

### `cargo_history`

Não existe. Auditoria de mandatos é zero.

---

## Modelo proposto

### Tipo de conta — separar humanos de sistema

Distinção fundamental introduzida por este spec:

| `account_type` | Quem | Exemplo |
|----------------|------|---------|
| `"member"` | Pessoa real, sócio da associação | Todos os auto-registos, contas pessoais |
| `"technical"` | Conta de manutenção do sistema, não é um sócio | `admin@controlador.cv` |

A conta técnica:
- Tem `role="admin"` e todos os privilégios — pode tudo.
- **NÃO** aparece em listagens de sócios (`/admin/usuarios`,
  `/transparencia`, etc.) por defeito.
- **NÃO** participa em sistema de pontuação dos sócios.
- **NÃO** vota em assembleias.
- **NÃO** ocupa cargos institucionais (`cargo_history` fica vazio).
- **Pode** ser actor em `audit_logs` — todas as acções continuam
  registadas (técnico continua responsabilizável).
- **Pode** ser revelada em listagens com flag explícito
  `?include_technical=true` (utilidade: debug, suporte).

Implementação:

```python
# models.py
ACCOUNT_TYPES = ["member", "technical"]

class UserBase(BaseModel):
    # ... campos existentes ...
    account_type: Literal["member", "technical"] = "member"
```

Validação de `cargo`:

- Contas `member`: `cargo` tem de estar em `CARGOS`.
- Contas `technical`: `cargo` pode ser um label técnico fora de
  `CARGOS`, por exemplo `"Técnico de Sistema"`.
- Endpoints de promoção/transferência só aceitam contas `member`, então
  a excepção técnica não entra em mandatos.

### Impacto noutras rotas

- `GET /api/users` — endpoint real usado pelo admin. Filtro default:
  mostrar só contas de sócios reais. Para retro-compatibilidade, tratar
  documentos sem `account_type` como `"member"`:
  `account_type == "member" OR account_type missing`. Query param
  `?include_technical=true` mostra também contas técnicas.
- Listagens públicas de sócios/transparência — onde existirem no
  frontend/backend, devem sempre filtrar só contas `member` e nunca
  aceitar `include_technical`.
- `GET /api/admin/cargos` — lista o quadro de cargos e ocupantes.
- `GET /api/admin/cargos/candidates` — lista apenas contas `member`
  com `status="ativo"` para promote/transfer, com busca por nome,
  email ou `member_id`.
- `POST /api/auth/register` (auto-registo) — força
  `account_type="member"` no servidor (não vem do request) e inicializa
  `cargo_history=[]`.
- Notificações `notify_admins` — continua a filtrar por `role="admin"`
  na fase 1. Se o ruído da conta técnica incomodar, ajustar depois para
  `account_type="member" AND role="admin"`.

### Imutabilidade de `member_id`

`member_id` passa a ser identificador permanente do sócio real:

- Auto-registo e convites de membros devem usar sempre `next_member_id`
  / sequência (`ACCTA-0001`, `ACCTA-0002`, ...).
- Conta técnica tem `member_id=None` e não consome sequência.
- `UserAdminUpdate` deixa de aceitar alteração de `member_id` depois da
  migração/bootstrap. O backend deve ignorar/rejeitar esse campo em
  updates normais.
- A UI de `/admin/usuarios` remove o input editável de `member_id` e
  mostra o valor como texto somente leitura.
- Alterações manuais de `member_id`, se alguma vez forem necessárias,
  ficam restritas a script de migração/administração fora da API comum.

### Estrutura de cargos por órgão social

Uma associação CV/PT típica tem três órgãos sociais eleitos +
coordenações funcionais. Cargos agrupados:

```python
CARGOS_ORGAOS_SOCIAIS = {
    "Direcção": [
        "Presidente",
        "Vice-Presidente",
        "Secretário-Geral",
        "Tesoureiro",
        "Vogal da Direcção",
    ],
    "Conselho Fiscal": [
        "Presidente do Conselho Fiscal",
        "Vogal do Conselho Fiscal",
    ],
    "Mesa da Assembleia Geral": [
        "Presidente da Mesa",
        "Vice-Presidente da Mesa",
        "Secretário da Mesa",
    ],
    "Coordenações": [
        "Coordenador de Comunicação",
        "Coordenador de Eventos",
        "Coordenador de Projectos",
    ],
    "Comissões": [
        "Membro da Comissão de Ética",
    ],
    "Base": [
        "Sócio",  # default, sem mandato institucional
    ],
}

# Lista plana usada para validação no auto-registo e endpoints
CARGOS = [c for grupo in CARGOS_ORGAOS_SOCIAIS.values() for c in grupo]
```

A constante `CARGOS` existente em `models.py` (com 7 entradas) é
substituída por esta lista de 14 cargos institucionais + Sócio.

### Privilégios — extensão necessária

A lista actual em `models.py:11-19`:

```python
PRIVILEGES = [
    "manage_users", "manage_finances", "manage_events",
    "manage_documents", "moderate_content", "manage_benefits",
    "view_audit_logs",
]
```

Está incompleta para o Conselho Fiscal (que precisa de auditar
finanças sem poder alterar). Adicionar **um** novo privilégio:

```python
PRIVILEGES.append("view_finances_readonly")
```

Total: 8 privilégios.

### Mapeamento cargo → role + privilégios (defaults sugeridos)

Estes são **defaults pré-carregados no modal de aprovação/promoção**.
O admin pode sobrepor caso a caso.

| Cargo | Role | Privilégios | Racional |
|-------|------|-------------|----------|
| **Presidente** | `admin` | TODOS os 8 | Cargo máximo, acesso total |
| **Vice-Presidente** | `admin` | TODOS os 8 | Substitui o Presidente |
| **Secretário-Geral** | `admin` | `manage_users`, `manage_events`, `manage_documents`, `moderate_content` | Secretaria, actas, comunicação |
| **Tesoureiro** | `financeiro` | `manage_finances`, `view_audit_logs` | Responsável financeiro |
| **Vogal da Direcção** | `moderador` | `moderate_content`, `manage_events` | Apoio operacional |
| **Presidente do Conselho Fiscal** | `socio` | `view_finances_readonly`, `view_audit_logs` | Audita finanças (leitura) |
| **Vogal do Conselho Fiscal** | `socio` | `view_finances_readonly`, `view_audit_logs` | Audita |
| **Presidente da Mesa** | `socio` | `manage_events` | Conduz assembleias |
| **Vice-Presidente da Mesa** | `socio` | (nenhum extra) | Apoia o Presidente da Mesa |
| **Secretário da Mesa** | `socio` | `manage_documents` | Lavra actas |
| **Coordenador de Comunicação** | `moderador` | `moderate_content`, `manage_events` | Mural, galeria, redes |
| **Coordenador de Eventos** | `socio` | `manage_events` | Organiza eventos |
| **Coordenador de Projectos** | `socio` | `manage_events`, `manage_documents` | Gestão de projectos |
| **Membro da Comissão de Ética** | `socio` | `view_audit_logs` | Verifica condutas |
| **Sócio** | `socio` | (nenhum) | Default |

Materializado em código:

```python
CARGO_DEFAULTS = {
    "Presidente": {
        "role": "admin",
        "privileges": list(PRIVILEGES),  # todos
    },
    "Vice-Presidente": {
        "role": "admin",
        "privileges": list(PRIVILEGES),
    },
    "Secretário-Geral": {
        "role": "admin",
        "privileges": ["manage_users", "manage_events",
                       "manage_documents", "moderate_content"],
    },
    "Tesoureiro": {
        "role": "financeiro",
        "privileges": ["manage_finances", "view_audit_logs"],
    },
    "Vogal da Direcção": {
        "role": "moderador",
        "privileges": ["moderate_content", "manage_events"],
    },
    "Presidente do Conselho Fiscal": {
        "role": "socio",
        "privileges": ["view_finances_readonly", "view_audit_logs"],
    },
    "Vogal do Conselho Fiscal": {
        "role": "socio",
        "privileges": ["view_finances_readonly", "view_audit_logs"],
    },
    "Presidente da Mesa": {
        "role": "socio",
        "privileges": ["manage_events"],
    },
    "Vice-Presidente da Mesa": {
        "role": "socio",
        "privileges": [],
    },
    "Secretário da Mesa": {
        "role": "socio",
        "privileges": ["manage_documents"],
    },
    "Coordenador de Comunicação": {
        "role": "moderador",
        "privileges": ["moderate_content", "manage_events"],
    },
    "Coordenador de Eventos": {
        "role": "socio",
        "privileges": ["manage_events"],
    },
    "Coordenador de Projectos": {
        "role": "socio",
        "privileges": ["manage_events", "manage_documents"],
    },
    "Membro da Comissão de Ética": {
        "role": "socio",
        "privileges": ["view_audit_logs"],
    },
    "Sócio": {
        "role": "socio",
        "privileges": [],
    },
}
```

**Importante** — `role` é o nível de acesso "grosso" (admin/financeiro/
moderador/socio). `privileges` são overlays granulares que dão acesso
extra a módulos específicos. Combinação útil:

- Conselho Fiscal tem `role=socio` (não pode editar nada), mas com
  `view_finances_readonly` ganha leitura ao módulo financeiro.
  Separação de poderes preservada.
- Coordenador de Eventos tem `role=socio` mas com `manage_events`
  pode criar e editar eventos. Não toca em mais nada.

### Matriz RBAC obrigatória

Antes dos endpoints de cargos entrarem, a implementação deve alinhar
as rotas existentes com `privileges`. Hoje vários módulos ainda validam
apenas `role`, então os novos defaults não teriam efeito sem este
passo.

Regras alvo:

| Módulo | Leitura | Escrita/administração |
|--------|---------|-----------------------|
| Finanças | `role in ["admin", "financeiro"]` **ou** `view_finances_readonly` | `role in ["admin", "financeiro"]` **ou** `manage_finances` |
| Eventos | público/logado conforme regra actual | `role="admin"` **ou** `manage_events` |
| Documentos | conforme regra actual | `role="admin"` **ou** `manage_documents` |
| Conteúdo/comunicação | conforme regra actual | `role in ["admin", "moderador"]` **ou** `moderate_content` |
| Benefícios | conforme regra actual | `role="admin"` **ou** `manage_benefits` |
| Auditoria | `role="admin"` **ou** `view_audit_logs` | sem escrita pela UI |
| Utilizadores/cargos | `role="admin"` **ou** `manage_users` | `role="admin"` **ou** `manage_users` |

Finanças precisa de separação explícita:

- `can_view_finances(user)` para endpoints `GET`.
- `can_manage_finances(user)` para endpoints `POST`, `PUT`, `PATCH`,
  `DELETE`, importações e reconciliações.
- Frontend mostra o módulo financeiro para quem pode ver, mas desactiva
  botões, formulários e acções destrutivas quando o utilizador tem só
  `view_finances_readonly`.

Se algum módulo ficar fora do escopo do PR inicial, deixar isso
explícito na implementação e não atribuir privilégio que sugira acesso
funcional inexistente.

### 1. Schema — campo `cargo_history` em `users`

Array opcional no `doc.cargo_history`. Cada entrada documenta um
mandato:

```python
class CargoMandate(BaseModel):
    cargo: str                         # "Presidente", "Tesoureiro", ...
    role: str                          # "admin"/"financeiro"/"moderador"/"socio"
    inicio: str                        # ISO 8601, obrigatório
    fim: Optional[str] = None          # ISO 8601; None = mandato activo
    elected_by: Optional[str] = None   # "AGA 2026", "Direcção", livre
    transitioned_by: str               # id do admin que efectuou a alteração
    notes: Optional[str] = None
```

**Invariantes**:

- No máximo UM mandato activo (`fim=None`) por sócio.
- No máximo o número de vagas permitido por cargo. Cargos singulares
  como Presidente, Tesoureiro e Secretário-Geral têm 1 vaga; cargos
  colectivos como Vogal e Comissão podem ter mais de uma.
- Conta `account_type="technical"` nunca pode receber mandato activo.

Validado em código na fase 1. Trigger/constraint em Postgres pode ficar
para uma fase posterior se o DAO suportar bem essa garantia.

### 2. Constantes e mapeamentos (em `models.py`)

```python
ROLES_VALID = ["admin", "financeiro", "moderador", "socio"]

CARGO_SEATS = {
    "Presidente": 1,
    "Vice-Presidente": 1,
    "Secretário-Geral": 1,
    "Tesoureiro": 1,
    "Vogal da Direcção": 3,
    "Presidente do Conselho Fiscal": 1,
    "Vogal do Conselho Fiscal": 2,
    "Presidente da Mesa": 1,
    "Vice-Presidente da Mesa": 1,
    "Secretário da Mesa": 1,
    "Coordenador de Comunicação": 1,
    "Coordenador de Eventos": 1,
    "Coordenador de Projectos": 1,
    "Membro da Comissão de Ética": 3,
    "Sócio": 0,
}
```

`CARGOS`, `PRIVILEGES`, `CARGO_DEFAULTS` e `CARGO_SEATS` são definidos
na secção "Estrutura de cargos por órgão social" acima.

### 3. Modelos Pydantic novos

```python
class PromoteUserRequest(BaseModel):
    cargo: str                          # tem de estar em CARGOS
    role: str                           # tem de estar em ROLES_VALID
    elected_by: Optional[str] = None
    notes: Optional[str] = None
    effective_date: Optional[str] = None  # ISO 8601, default = agora

class TransferCargoRequest(BaseModel):
    from_user_id: str
    to_user_id: str
    cargo: str
    role: str
    elected_by: Optional[str] = None
    notes: Optional[str] = None
    effective_date: Optional[str] = None
```

---

## Endpoints novos/alterados

Endpoints administrativos ficam em `routes/admin.py`. RBAC:
`role="admin"` ou privilégio `manage_users`.

### `POST /api/admin/users/{user_id}/promote`

Promove um sócio a um cargo institucional.

**Acção**:
1. Valida `cargo ∈ CARGOS`, `role ∈ ROLES_VALID` e, se vierem no
   request, `privileges ⊆ PRIVILEGES`.
2. Valida `user.account_type="member"` e `user.status="ativo"`.
3. Valida `CARGO_SEATS[cargo]`: não pode exceder o número de titulares
   activos daquele cargo.
4. Fecha mandato actual do sócio (se houver mandato activo no
   `cargo_history`, set `fim = effective_date`).
5. Acrescenta nova entrada ao `cargo_history` com `fim=None`.
6. Actualiza `users.doc.role`, `users.doc.cargo` e
   `users.doc.privileges`. Se privilégios não vierem no request, aplica
   `CARGO_DEFAULTS[cargo]`.
7. `create_audit_log("cargo_promote", actor=current_user.id,
   details={target: user_id, cargo, role, mandate_id})`.
8. `notify_users([user_id], "system", f"Foi atribuído o cargo de
   {cargo}", "/perfil")`.

**Response**: `{"message": "...", "cargo_history": [...]}`

### `POST /api/admin/users/{user_id}/demote`

Despromove (fim de mandato sem substituto imediato).

**Acção**:
1. Valida `user.account_type="member"`.
2. Fecha mandato activo (`fim=effective_date`).
3. `role` volta a `"socio"`, `cargo` volta a `"Sócio"` e
   `privileges=[]`.
4. Audit log `cargo_demote`.
5. Notifica o sócio.

### `POST /api/admin/cargos/transfer`

**Operação atómica** — transição de mandato de uma pessoa para outra.
Use case: AGA elege novo presidente.

**Acção**:
1. Executar numa transacção real do banco. Se o helper actual do DAO não
   expuser transacções, criar uma função dedicada no `Database` para
   esta operação antes de implementar a rota.
2. Valida ambos os utilizadores existem, são `account_type="member"` e
   `to_user.status="ativo"`.
3. Valida que `from_user` é titular activo do `cargo` informado.
4. Valida `CARGO_SEATS[cargo]` considerando a saída do `from_user` e a
   entrada do `to_user`.
5. **Despromove from_user**:
   - Fecha mandato activo
   - `role="socio"`, `cargo="Sócio"`, `privileges=[]`
6. **Promove to_user**:
   - Fecha mandato anterior se existir
   - Acrescenta novo mandato
   - Actualiza `role`/`cargo`/`privileges`
7. Cria dois audit logs linkados por `transition_id` (uuid partilhado):
   - `cargo_transfer_out` em `from_user`
   - `cargo_transfer_in` em `to_user`
8. Notifica ambos.

**Response**: `{"message": "...", "transition_id": "..."}`

### `GET /api/admin/cargos`

Lista o estado actual de todos os cargos institucionais, incluindo
vagas e cardinalidade.

**Response**:
```json
{
  "cargos": [
    {
      "cargo": "Presidente",
      "seats": 1,
      "holders": [
        {"id": "...", "name": "...", "email": "...", "member_id": "ACCTA-0001", "since": "2024-01-01"}
      ]
    },
    {"cargo": "Tesoureiro", "seats": 1, "holders": []}
  ]
}
```

Vagas aparecem com `holders: []` ou com menos titulares do que
`seats`.

### `GET /api/admin/cargos/candidates`

Lista candidatos elegíveis para atribuição/transferência de cargo.

Query params:
- `q`: busca por nome, email ou `member_id`
- `status`: default `"ativo"`
- `exclude_cargo`: opcional, para ocultar quem já ocupa determinado
  cargo

Sempre filtra `account_type="member"`. Nunca retorna a conta técnica.

### `GET /api/users/cargos`

Endpoint de metadata para o frontend. Deve devolver `CARGOS`,
`CARGOS_ORGAOS_SOCIAIS`, `PRIVILEGES`, `CARGO_DEFAULTS` e
`CARGO_SEATS`, evitando constantes hard-coded no React.

### `GET /api/users/{user_id}/cargo-history` (auth: próprio ou admin)

Devolve o histórico de cargos de um sócio (ordenado descendente).

---

## Frontend

### Ajustes transversais

- Substituir constantes hard-coded de cargos/privilégios por
  `GET /api/users/cargos`.
- Em `/admin/usuarios`, mostrar `member_id` como somente leitura e
  remover edição directa.
- Listagens de usuários devem ocultar `account_type="technical"` por
  defeito; a flag `include_technical` deve existir só em fluxo de
  debug/admin explícito.
- Menu e rota de Finanças passam a usar `can_view_finances`; botões e
  formulários de escrita usam `can_manage_finances`.

### Página nova: `/admin/cargos`

Layout:
- Tabela de cargos institucionais (linha por cargo de `CARGOS`).
- Para cada linha: ocupante actual (nome + member_id + badge) ou
  "Vago".
- Acções por linha:
  - **Atribuir** (se vago) → modal escolhe sócio
  - **Transferir** (se ocupado) → modal escolhe novo sócio
  - **Terminar mandato** (se ocupado) → confirma demote

Modal de transferência:
- Cargo: read-only
- De: read-only (sócio actual)
- Para: autocomplete via `GET /api/admin/cargos/candidates` (debounce
  300ms)
- Role: prefilled de `CARGO_DEFAULTS[cargo].role`, editável
- Privilégios: prefilled de `CARGO_DEFAULTS[cargo].privileges`,
  editável por checkboxes
- Data efectiva: date picker, default hoje
- "Eleito por" (texto livre): default "AGA YYYY"
- Notas (textarea)
- Submit → POST `/api/admin/cargos/transfer`

Design — `frontend-design`: botão primário Carmesim para "Confirmar
transferência", `bg-white` na tabela, badges neutros para cargos,
hover linha `bg-[#F5F5F5]`.

### `/admin/usuarios` — histórico no detalhe existente

Timeline simples:
```
Presidente   2024-01-01 → presente
Vogal        2022-01-01 → 2023-12-31
```

O app actual não tem rota `/admin/usuarios/[id]`; portanto a primeira
implementação deve adicionar a timeline no modal/detalhe existente de
`/admin/usuarios`. Criar uma rota dedicada só se isso for decidido no
redesign do admin.

Sem UI de edição directa — apenas leitura. Mudanças acontecem via
`/admin/cargos`.

### Página `/perfil` (sócio comum) — adicionar mesma secção

Visibilidade do próprio percurso na associação.

---

## Migração das contas partilhadas existentes

Como o sistema **não está em produção**, podemos fazer migração
destrutiva controlada. A decisão final é **limpar/recriar utilizadores**
e manter `admin@controlador.cv` apenas como conta técnica de bootstrap.

### Estratégia final confirmada

1. Fazer backup/export antes de qualquer limpeza, mesmo em ambiente de
   teste.
2. Limpar `users` e dados acoplados que dependem directamente de
   `user_id` de teste (`audit_logs`, `notifications`, sessões/tokens se
   existirem).
3. Adaptar `create_admin.py` para criar exclusivamente:
   - `email="admin@controlador.cv"`
   - `name="Administrador de Sistema"`
   - `account_type="technical"`
   - `member_id=None`
   - `cargo="Técnico de Sistema"` fora de `CARGOS`
   - `role="admin"`
   - todos os privilégios
   - `cargo_history=[]`
4. Garantir que `member_id_seq` arranca em `ACCTA-0001` para o primeiro
   sócio real, não para a conta técnica.
5. Adaptar `seed_data.py`, fixtures e testes para entenderem
   `account_type` e para continuarem usando `admin@controlador.cv` como
   bootstrap técnico quando precisarem de superuser.
6. Todos os Presidente/Tesoureiro/Secretário/etc. entram pelo
   auto-registo ou convite como contas `member` e depois recebem cargo
   via `promote`/`transfer`.

Não há migração in-place de `admin@controlador.cv` para pessoa real.
Emails institucionais como `presidente@controlador.cv` ou
`tesoureiro@controlador.cv` não viram login; são aliases fora do ACCTA.

---

## Plano de execução por fases

Implementação em ordem para minimizar quebras:

### Fase 0 — Alinhamento com o código actual (~45min)
- Confirmar endpoints reais: `GET /api/users`, `GET /api/users/cargos`,
  rotas de admin e rotas de finanças.
- Mapear todas as validações por `role` que precisam passar a aceitar
  `privileges`.
- Definir helper comum de autorização para evitar checks duplicados.

### Fase 1 — Schema + models (~1h30)
- Adicionar `account_type` e `cargo_history` ao `User` (campos
  retro-compatíveis)
- Adicionar `CargoMandate`, `PromoteUserRequest`,
  `TransferCargoRequest` aos models
- Adicionar `ROLES_VALID`, `CARGO_DEFAULTS`, `CARGO_SEATS` e novo
  privilégio `view_finances_readonly`
- Remover `member_id` de updates administrativos comuns
- Testes unitários dos models

### Fase 2 — RBAC granular (~2h)
- Separar `can_view_finances` de `can_manage_finances`
- Actualizar eventos/documentos/conteúdo/benefícios/auditoria para
  aceitar privilégios relevantes
- Ajustar frontend de Finanças para modo somente leitura quando
  aplicável

### Fase 3 — Endpoints backend (~3h)
- `routes/admin.py`: novos endpoints `promote`/`demote`/`transfer`
- `routes/admin.py`: novo endpoint `GET /admin/cargos`
- `routes/admin.py`: novo endpoint `GET /admin/cargos/candidates`
- `routes/users.py`: actualizar `GET /users` com filtro
  `account_type` e `include_technical`
- `routes/users.py`: actualizar `GET /users/cargos` para retornar
  metadata completa
- `routes/users.py`: `GET /users/{id}/cargo-history`
- Audit log + notify em cada acção
- Transacção real para `transfer`
- Testes unitários (com `mock_db`, padrão do projecto)

### Fase 4 — UI admin (~3h)
- `/admin/cargos` — tabela + modais
- Secção "Histórico de Cargos" no modal/detalhe actual de
  `/admin/usuarios`
- Secção "Os meus cargos" em `/perfil`
- Remover edição de `member_id`
- Substituir constantes hard-coded por metadata do backend
- Lighthouse / verificação design system

### Fase 5 — Migração das contas (~1h)
- Adaptar `create_admin.py`
- Executar estratégia final confirmada: conta técnica
  `admin@controlador.cv`, `member_id=None`
- Actualizar fixtures/testes para `account_type`

### Fase 6 — Documentação (~30min)
- Actualizar `CLAUDE.md` com o modelo de cargos
- Actualizar `.claude/rules/database.md` com `cargo_history`
- Actualizar `spec-auto-registo.md` para referenciar este spec

**Total estimado**: ~11h de trabalho focado, divisível em PRs por fase.

---

## Integração com `spec-auto-registo.md`

O auto-registo continua **exactamente igual** ao definido:

- Candidato preenche `cargo_declarado` (dropdown).
- Admin aprova → escolhe `role` e `cargo` no modal de aprovação.
- Backend força `account_type="member"` e usa `next_member_id`.
- Modal de aprovação deve preencher `role` e `privileges` a partir de
  `CARGO_DEFAULTS[cargo]`, mantendo override manual pelo admin.
- **Acção extra** (acrescentada por este spec): no momento da
  aprovação, se o `cargo` aprovado não for "Sócio", criar
  automaticamente a primeira entrada no `cargo_history`.
- Se o cargo aprovado for "Sócio", `cargo_history` fica vazio.

Mínimo de fricção entre as duas specs — ambas tocam o mesmo modal de
aprovação, mas em campos diferentes.

---

## Implicações para outras features

- **Pontuação dos sócios** (a desenhar): regista actividades na conta
  pessoal. Trabalho administrativo conta normalmente. Nenhuma feature
  da pontuação precisa de tratar "papéis" de forma especial — sempre
  pessoa.
- **Auditoria**: `audit_logs.user_id` sempre humano. Nunca um "papel".
  Excepção aceitável: acções de manutenção feitas pela conta técnica
  `admin@controlador.cv`, que ficam marcadas como actor técnico.
- **Notificações**: `notify_admins` (em `helpers.py`) — não muda,
  continua a filtrar por `role="admin"`. Funciona porque o role da
  conta pessoal é actualizado dinamicamente quando alguém é promovido.

---

## Stop conditions (CLAUDE.md)

Este spec **atinge uma stop condition**:

> "A task requires dropping or migrating data in PostgreSQL/Supabase"

A Fase 5 envolve migração/limpeza da tabela `users`. **Requer
confirmação explícita do utilizador** antes de executar comandos
destrutivos, mesmo com a estratégia final já definida.

Não toca em:
- JWT secret
- CORS
- Routes removidas (todas as routes existentes continuam a funcionar)
- Emails para utilizadores reais (sistema em teste; emails apenas para
  o utilizador/developer)

---

## Decisões já confirmadas

- ✅ **Estratégia de migração**: A — limpar tabela `users` + recriar
  via `create_admin.py` adaptado.
- ✅ **Cargos**: lista completa por órgão social (15 entradas, ver
  secção "Estrutura de cargos").
- ✅ **Privilégios**: alinhados por função, com `view_finances_readonly`
  adicionado para o Conselho Fiscal.
- ✅ **RBAC**: privilégios precisam ser aplicados nas rotas existentes;
  `view_finances_readonly` é leitura apenas e não concede escrita.
- ✅ **`member_id`**: imutável para sócios reais; conta técnica usa
  `member_id=None`.
- ✅ **Ordem de implementação**: pode ser PR único, mas o plano está
  separado em fases para facilitar revisão.
- ✅ **Conta de bootstrap**: apenas `admin@controlador.cv` é criada
  pelo script. É a conta técnica de superuser do sistema — todas as
  outras pessoas (incluindo Presidente, Tesoureiro, etc.) entram pelo
  auto-registo e ganham cargo via os endpoints `promote`/`transfer`.
- ✅ **Sem outras contas partilhadas**: `presidente@controlador.com`
  e similares NÃO são criadas como contas de login. Se forem
  necessárias como endereços institucionais, são aliases de email
  fora do sistema.

## Forma final da conta `admin@controlador.cv`

Depois do `create_admin.py` adaptado correr:

```python
{
    "id": "<uuid>",
    "name": "Administrador de Sistema",
    "email": "admin@controlador.cv",
    "account_type": "technical",          # ← chave: não é um sócio
    "role": "admin",
    "status": "ativo",
    "member_id": None,                    # técnicas não têm member_id
    "cargo": "Técnico de Sistema",        # label informativo, fora de CARGOS
    "privileges": [                       # todos os 8
        "manage_users", "manage_finances", "manage_events",
        "manage_documents", "moderate_content", "manage_benefits",
        "view_audit_logs", "view_finances_readonly",
    ],
    "cargo_history": [],                  # vazio — não é cargo eleito
    "consent_data": True,
    "created_at": "...",
}
```

Notas:
- `account_type="technical"` é o que retira esta conta de
  listagens/pontuação/AGAs.
- `member_id` fica `None` (a sequência `member_id_seq` arranca em
  ACCTA-0001 para o primeiro sócio real, não para a técnica).
- `cargo` é um label livre, NÃO está em `CARGOS` institucionais — a
  conta nunca participa em mandatos eleitos.
