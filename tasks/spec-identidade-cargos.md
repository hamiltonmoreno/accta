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

**Invariante**: no máximo UM mandato activo (`fim=None`) por sócio.
Validado em código + opcionalmente por trigger Postgres (não para a
fase 1; código basta).

### 2. Constantes e mapeamentos (em `models.py`)

```python
ROLES_VALID = ["admin", "financeiro", "moderador", "socio"]

# Mantém-se a constante CARGOS existente.

# Hint de role default por cargo — só para preencher o modal do admin.
# Admin pode sempre sobrepor.
CARGO_DEFAULT_ROLE = {
    "Presidente": "admin",
    "Vice-Presidente": "admin",
    "Secretário-Geral": "admin",
    "Tesoureiro": "financeiro",
    "Vogal": "moderador",
    "Membro da Direção": "moderador",
    "Sócio": "socio",
}
```

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

## Endpoints novos

Todos sob `routes/admin.py` (já é o sítio dos endpoints `/admin/*`).
RBAC: apenas `admin`.

### `POST /api/admin/users/{user_id}/promote`

Promove um sócio a um cargo institucional.

**Acção**:
1. Valida `cargo ∈ CARGOS` e `role ∈ ROLES_VALID`.
2. Fecha mandato actual do sócio (se houver mandato activo no
   `cargo_history`, set `fim = effective_date`).
3. Acrescenta nova entrada ao `cargo_history` com `fim=None`.
4. Actualiza `users.doc.role` e `users.doc.cargo` para os novos.
5. `create_audit_log("cargo_promote", actor=current_user.id,
   details={target: user_id, cargo, role, mandate_id})`.
6. `notify_users([user_id], "system", f"Foi atribuído o cargo de
   {cargo}", "/perfil")`.

**Response**: `{"message": "...", "cargo_history": [...]}`

### `POST /api/admin/users/{user_id}/demote`

Despromove (fim de mandato sem substituto imediato).

**Acção**:
1. Fecha mandato activo (`fim=effective_date`).
2. `role` volta a `"socio"`, `cargo` volta a `"Sócio"`.
3. Audit log `cargo_demote`.
4. Notifica o sócio.

### `POST /api/admin/cargos/transfer`

**Operação atómica** — transição de mandato de uma pessoa para outra.
Use case: AGA elege novo presidente.

**Acção** (numa única função, dentro de um bloco try com rollback
manual em caso de falha — não há transacções no DAO Mongo-compat, mas
podemos fazer as duas updates sequencialmente e logar a discrepância
em caso de falha entre elas):

1. Valida ambos os sócios existem e `to_user.status="ativo"`.
2. **Despromove from_user**:
   - Fecha mandato activo
   - `role="socio"`, `cargo="Sócio"`
3. **Promove to_user**:
   - Fecha mandato anterior se existir (raro mas possível)
   - Acrescenta novo mandato
   - Actualiza `role`/`cargo`
4. **Dois audit logs** linkados por `transition_id` (uuid partilhado):
   - `cargo_transfer_out` em `from_user`
   - `cargo_transfer_in` em `to_user`
5. Notifica ambos.

**Response**: `{"message": "...", "transition_id": "..."}`

### `GET /api/admin/cargos`

Lista o estado actual de todos os cargos institucionais.

**Response**:
```json
{
  "cargos": [
    {"cargo": "Presidente", "user": {id, name, email, member_id}, "since": "2024-01-01"},
    {"cargo": "Tesoureiro", "user": null, "since": null},
    ...
  ]
}
```

Vacancies (sem ocupante) aparecem com `user: null`.

### `GET /api/users/{user_id}/cargo-history` (auth: próprio ou admin)

Devolve o histórico de cargos de um sócio (ordenado descendente).

---

## Frontend

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
- Para: autocomplete de utilizadores `status=ativo` (debounce 300ms)
- Role: prefilled de `CARGO_DEFAULT_ROLE[cargo]`, editável
- Data efectiva: date picker, default hoje
- "Eleito por" (texto livre): default "AGA YYYY"
- Notas (textarea)
- Submit → POST `/api/admin/cargos/transfer`

Design — `frontend-design`: botão primário Carmesim para "Confirmar
transferência", `bg-white` na tabela, badges neutros para cargos,
hover linha `bg-[#F5F5F5]`.

### Página `/admin/usuarios/[id]` — adicionar secção "Histórico de Cargos"

Timeline simples:
```
Presidente   2024-01-01 → presente
Vogal        2022-01-01 → 2023-12-31
```

Sem necessidade de UI de edição directa — apenas leitura. Mudanças
acontecem via `/admin/cargos`.

### Página `/perfil` (sócio comum) — adicionar mesma secção

Visibilidade do próprio percurso na associação.

---

## Migração das contas partilhadas existentes

Como o sistema **não está em produção**, podemos fazer migração
destrutiva controlada. Plano:

### Fase de descoberta (manual, com o utilizador)

Mapear cada conta partilhada existente para uma pessoa real:

| Conta partilhada | Pessoa real | Email pessoal |
|------------------|-------------|---------------|
| `admin@controlador.cv` | ? | ? |
| `admin@controlador.com` | ? | ? |
| `presidente@controlador.cv` | (não existe ainda) | n/a |

> **Acção requerida do utilizador**: identificar a pessoa real por
> trás de cada conta. Se ainda não houver pessoa real definida (sistema
> em teste), podemos simplesmente deletar a conta partilhada e re-criar
> uma conta admin pessoal nova.

### Estratégia A — sistema só em teste, sem dados a preservar

**Recomendada se o utilizador confirmar que não há nada de valor.**

1. Drop completo da tabela `users` (ou `delete_many({})`) e
   re-criação via `create_admin.py` adaptado:
   ```bash
   python scripts/create_admin.py \
       --email <email-pessoal-do-developer> \
       --password <senha> \
       --name "Nome Real"
   ```
2. `create_admin.py` é modificado para:
   - Receber também `--cargo` (default "Presidente")
   - Receber também `--role` (default "admin")
   - **Não usar `ACCTA-ADMIN` como sentinel**; usar `member_id` do
     contador sequencial (`ACCTA-0001`)
   - Criar a primeira entrada no `cargo_history`
3. Limpar audit_logs, notifications, etc. (estão acoplados a user_ids
   que vão desaparecer).
4. Re-correr `seed_data.py` (também adaptado para usar emails pessoais
   fictícios em vez de `admin@controlador.cv`).

### Estratégia B — preservar a conta admin actual

Se houver algum dado de teste a preservar, migrar in-place:

1. Renomear `admin@controlador.cv` para o email pessoal do
   developer/admin.
2. Actualizar `name`, atribuir `member_id="ACCTA-0001"` (via sequência).
3. Acrescentar primeira entrada em `cargo_history`.
4. Manter audit_logs e referências (já apontam para o mesmo `id` UUID,
   só o email mudou).
5. Actualizar os 17 ficheiros de teste para usar uma fixture
   centralizada — `ADMIN_EMAIL` em `tests/conftest_integration.py`.

### Decisão a tomar

Pergunta para o utilizador antes de implementar:
- Estratégia A (limpar tudo) ou B (preservar e migrar)?
- Que email(s) reais usar para a(s) conta(s) admin?

---

## Plano de execução por fases

Implementação em ordem para minimizar quebras:

### Fase 1 — Schema + models (~1h)
- Adicionar `cargo_history` ao `User` (campo opcional, retro-compatível)
- Adicionar `CargoMandate`, `PromoteUserRequest`,
  `TransferCargoRequest` aos models
- Adicionar `ROLES_VALID` e `CARGO_DEFAULT_ROLE` aos models
- Testes unitários dos models

### Fase 2 — Endpoints backend (~3h)
- `routes/admin.py`: novos endpoints `promote`/`demote`/`transfer`
- `routes/admin.py`: novo endpoint `GET /admin/cargos`
- `routes/users.py`: `GET /users/{id}/cargo-history`
- Audit log + notify em cada acção
- Testes unitários (com `mock_db`, padrão do projecto)

### Fase 3 — UI admin (~3h)
- `/admin/cargos` — tabela + modais
- Secção "Histórico de Cargos" em `/admin/usuarios/[id]`
- Secção "Os meus cargos" em `/perfil`
- Lighthouse / verificação design system

### Fase 4 — Migração das contas (~1h, depende da estratégia)
- Adaptar `create_admin.py`
- Executar plano de migração (A ou B)
- Actualizar ficheiros de teste para usar a nova conta admin

### Fase 5 — Documentação (~30min)
- Actualizar `CLAUDE.md` com o modelo de cargos
- Actualizar `.claude/rules/database.md` com `cargo_history`
- Actualizar `spec-auto-registo.md` para referenciar este spec

**Total estimado**: ~8-9h de trabalho focado, divisível em PRs por fase.

---

## Integração com `spec-auto-registo.md`

O auto-registo continua **exactamente igual** ao definido:

- Candidato preenche `cargo_declarado` (dropdown).
- Admin aprova → escolhe `role` e `cargo` no modal de aprovação.
- **Acção extra** (acrescentada por este spec): no momento da
  aprovação, se o `cargo` aprovado não for "Sócio", criar
  automaticamente a primeira entrada no `cargo_history`.

Mínimo de fricção entre as duas specs — ambas tocam o mesmo modal de
aprovação, mas em campos diferentes.

---

## Implicações para outras features

- **Pontuação dos sócios** (a desenhar): regista actividades na conta
  pessoal. Trabalho administrativo conta normalmente. Nenhuma feature
  da pontuação precisa de tratar "papéis" de forma especial — sempre
  pessoa.
- **Auditoria**: `audit_logs.user_id` sempre humano. Nunca um "papel".
- **Notificações**: `notify_admins` (em `helpers.py`) — não muda,
  continua a filtrar por `role="admin"`. Funciona porque o role da
  conta pessoal é actualizado dinamicamente quando alguém é promovido.

---

## Stop conditions (CLAUDE.md)

Este spec **atinge uma stop condition**:

> "A task requires dropping or migrating data in PostgreSQL/Supabase"

A Fase 4 envolve migração/limpeza da tabela `users`. **Requer
confirmação explícita do utilizador** antes de executar — em
particular, a escolha entre Estratégia A (drop + recriar) e B (migrar
in-place), e os emails pessoais a usar.

Não toca em:
- JWT secret
- CORS
- Routes removidas (todas as routes existentes continuam a funcionar)
- Emails para utilizadores reais (sistema em teste; emails apenas para
  o utilizador/developer)

---

## Decisões a confirmar antes de implementar

1. **Estratégia de migração**: A (limpar tudo + recriar) ou B
   (preservar e migrar in-place)?
2. **Email pessoal do admin actual** a usar como conta principal?
3. **Outras contas partilhadas a migrar** além das listadas
   (`admin@controlador.cv`, `admin@controlador.com`)?
4. **Privilégios granulares** (`PRIVILEGES` array): mantemos como
   estão (overlay opcional ao `role`) ou simplificamos para "role
   chega"? Sugestão: deixar como está, fora do scope deste spec.
5. **Ordem de implementação das fases**: tudo num PR, ou um PR por
   fase (recomendado: um PR por fase 1-2-3, fase 4 como PR
   separado com revisão extra, fase 5 junto da última)?
