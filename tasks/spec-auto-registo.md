# Spec — Auto-registo de Sócios com Aprovação do Admin

> **Relacionado**: `tasks/spec-identidade-cargos.md` (implementado). O auto-registo
> força `account_type="member"` e, ao aprovar com um cargo institucional (≠ Sócio),
> cria a 1ª entrada em `cargo_history`. O modal de aprovação pré-preenche
> `role`/`privileges` a partir de `CARGO_DEFAULTS[cargo]`.

## Objectivo

Permitir que potenciais sócios criem o seu pedido de inscrição directamente
numa página pública (sem invite prévio), e que um administrador aprove ou
rejeite o pedido. O fluxo de invite-por-admin continua a existir — esta é
uma **alternativa**, não uma substituição.

## Não-objectivos

- Não substitui o fluxo de convite existente (`/admin/invite` →
  `/setup-account?token=...`).
- Não permite que o próprio utilizador escolha o `role` — todos os
  pedidos chegam como `socio`. O candidato pode declarar um **cargo**
  (label) mas isso não promove automaticamente: a promoção a
  `financeiro`/`moderador`/`admin` continua a ser acção exclusiva do
  admin via painel.
- Não envia password no submit — a password só é definida depois de
  aprovado, **reutilizando o fluxo `SetupAccount` existente**.

---

## Fluxo

```
Visitante                Backend                   Admin
   │                        │                        │
   │ 1. abre /criar-conta   │                        │
   │ 2. preenche form ──────▶ POST /api/auth/register│
   │                        │ cria user              │
   │                        │ status=pendente_aprovacao
   │                        │ ──────────────────────▶ notify_admins
   │ 3. vê "pedido enviado" │                        │
   │                        │                        │ 4. abre painel
   │                        │                        │    Pedidos pendentes
   │                        │ ◀── GET /admin/registration-requests
   │                        │ ── lista pedidos ─────▶│
   │                        │                        │ 5a. aprova
   │                        │ ◀── POST .../approve   │
   │                        │ gera invite_token      │
   │                        │ status=pendente_convite│
   │                        │ envia email setup ────▶│
   │ 6. recebe email        │                        │
   │ 7. /setup-account ─────▶ (fluxo existente)      │
   │ 8. define password     │ status=ativo           │
   │                        │                        │
   │                        │                        │ 5b. rejeita
   │                        │ ◀── POST .../reject    │
   │                        │ status=rejeitado       │
   │                        │ email "infelizmente..."▶│
   │ 9. recebe rejeição     │                        │
```

**Decisão chave**: aprovar **não** activa a conta directamente — gera um
invite. Vantagens:
1. Reutiliza 100% do `SetupAccount` já existente (uma única forma de
   activação).
2. Confirma o email (utilizador prova posse antes de acceder).
3. A password fica nas mãos do utilizador, nunca passa pelo admin.

---

## Mudanças no modelo de dados

### `USER_STATUSES` (backend/models.py)

Adicionar dois novos estados:

```python
USER_STATUSES = [
    "ativo",
    "inativo",
    "pendente_convite",       # já existente
    "pendente_aprovacao",     # NOVO — pedido de auto-registo, aguarda admin
    "rejeitado",              # NOVO — admin rejeitou o pedido
]
```

`rejeitado` mantém o documento (auditoria + impede re-registo trivial
com o mesmo email). Pode ser limpo por job manual.

### Novos campos opcionais no documento `users`

| Campo | Tipo | Notas |
|-------|------|-------|
| `registration_request_at` | ISO 8601 | quando o pedido foi feito |
| `registration_review_at` | ISO 8601 | quando o admin reviu |
| `registration_reviewer_id` | str | `id` do admin que aprovou/rejeitou |
| `registration_rejection_reason` | str | opcional, mostrado no email |
| `cargo_declarado` | str | cargo escolhido pelo candidato (dropdown) — apenas declarativo, NÃO altera o `role` |
| `member_id` | str | já existe — agora sequencial e imutável |

Todos opcionais — utilizadores criados por invite continuam sem
`registration_*`.

### Índice + sequência

Adicionar em `ensure_schema()`:

```sql
-- Listagem rápida de pedidos pendentes para o painel admin
CREATE INDEX IF NOT EXISTS users_status_registration_idx
  ON users ((doc->>'status'))
  WHERE doc->>'status' IN ('pendente_aprovacao', 'rejeitado');

-- Sequência atómica para member_id (resolve race condition sob carga)
CREATE SEQUENCE IF NOT EXISTS member_id_seq START 1;
```

**Bootstrap da sequência**: na primeira execução em produção, ajustar
o `START` para `MAX(member_id_numerico_extraído) + 1` se houver
utilizadores existentes com formato `ACCTA-NNNN`. Caso contrário, os
novos pedidos colidiriam com IDs já atribuídos. Script:

```sql
SELECT setval('member_id_seq', COALESCE(MAX(...), 0) + 1)
```

Idempotente, executado uma vez via migration script ou `ensure_schema`
com guard.

---

## Backend — novos endpoints

### `POST /api/auth/register` (público, **sem auth**)

**Rate limit**: `3/hour` por IP (anti-spam, mais restrito que
`forgot-password` porque cria um registo persistente).

**Request** (`RegistrationRequest` em `models.py`):

```python
CARGOS_DECLARADOS = [
    "Sócio",
    "Vogal",
    "Tesoureiro",
    "Secretário",
    "Vice-Presidente",
    "Presidente",
    "Direcção",
    "Conselho Fiscal",
]

class RegistrationRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = Field(default=None, max_length=30)
    department: Optional[str] = Field(default=None, max_length=80)
    cargo_declarado: str = Field(default="Sócio")  # validação: tem de estar em CARGOS_DECLARADOS
    consent_data: bool   # tem de ser True (GDPR/RGPD)
    website: Optional[str] = Field(default=None, max_length=200)  # HONEYPOT — sempre rejeitar se preenchido
```

> **Importante**: `member_id` **não vem** do request. É atribuído pelo
> servidor via `nextval('member_id_seq')` na criação do registo, no
> formato `ACCTA-{n:04d}` (zero-padded, expande para 5+ dígitos quando
> ultrapassar 9999). Imutável depois de atribuído.
>
> `role` é sempre `socio` neste fluxo — `cargo_declarado` é só um label
> que o admin vê no painel para decidir o role final.

**Validações**:
- `consent_data` obrigatoriamente `True` → senão 400.
- `cargo_declarado` tem de estar em `CARGOS_DECLARADOS` → senão 422.
- `website` (honeypot) preenchido → devolver 201 falso, descartar
  silenciosamente, **não criar registo** (anti-bot).
- Email duplicado:
  - Já `ativo`/`inativo`/`pendente_convite` → 409 "Já existe uma conta
    com este email."
  - Já `pendente_aprovacao` → 409 "Já existe um pedido em análise para
    este email."
  - `rejeitado` → 409 "Não foi possível processar este pedido." (não
    revela que foi rejeitado, evita enumeração).
- Mensagens de erro em PT, neutras (sem leak de existência).

**Acção**:
1. Atribui `member_id` via `nextval('member_id_seq')` →
   `f"ACCTA-{n:04d}"`.
2. Cria documento `users` com:
   - `status="pendente_aprovacao"`
   - `role="socio"` (sempre, ignora qualquer hint do candidato)
   - `cargo_declarado=<dropdown>` (label informativo)
   - `cargo=cargo_declarado` (também copia para o campo legado, admin
     pode editar depois)
   - `member_id=<sequencial>`
   - `password=""`, sem `invite_token`
   - `registration_request_at=now`
3. `notify_admins("system", f"Novo pedido de inscrição: {name}
   ({cargo_declarado})", "/admin/pedidos-inscricao")`.
4. `create_audit_log(user_id, "registration_requested",
   details={"cargo_declarado": ..., "member_id": ...})` — o `user_id`
   é o do próprio candidato (não há admin actor; manter convenção:
   actor pode ser o próprio).

**Response 201**:
```json
{
  "message": "Pedido recebido. Receberá um email quando for analisado.",
  "request_id": "<uuid>"
}
```

Não devolver dados sensíveis. Não confirmar/desmentir existência de
emails (anti-enumeração).

---

### `GET /api/admin/registration-requests` (admin)

**Query params**: `status` (default `pendente_aprovacao`; aceita
`rejeitado`), `limit`/`skip` para paginação.

**Response**: lista de pedidos com campos não-sensíveis (sem `password`,
sem `invite_token`).

---

### `POST /api/admin/registration-requests/{user_id}/approve` (admin)

**Request body** (`RegistrationApprove`):
```python
class RegistrationApprove(BaseModel):
    role: str = "socio"  # validação: tem de estar em ["socio", "financeiro", "moderador", "admin"]
    cargo: Optional[str] = None  # se None, mantém o cargo_declarado
```

**Acção**:
1. Verifica `status == "pendente_aprovacao"`.
2. Gera `invite_token` (mesma rotina de `admin.invite_user`).
3. Actualiza:
   - `status="pendente_convite"`
   - `role=<aprovado>` (admin escolhe — só agora pode escalar para
     `admin`/`financeiro`/`moderador`)
   - `cargo=<aprovado ou cargo_declarado>`
   - `invite_token`, `invite_token_expires_at`
   - `registration_review_at=now`,
     `registration_reviewer_id=current_user.id`
4. **NÃO altera `member_id`** — já foi atribuído no submit, é imutável.
5. Envia `send_invite_email` com link `/setup-account?token=...`.
6. `create_audit_log("registration_approved",
   details={"role": ..., "cargo": ..., "member_id": ...})`.

**Response**: `{"message": "Pedido aprovado. Email de activação
enviado.", "email_sent": true|false}`.

A partir daqui o utilizador segue o fluxo `setup-account` existente
sem qualquer alteração no frontend ou backend desse caminho.

---

### `POST /api/admin/registration-requests/{user_id}/reject` (admin)

**Request body**: `{"reason": Optional[str]}`.

**Acção**:
1. Verifica `status == "pendente_aprovacao"`.
2. Actualiza `status="rejeitado"`,
   `registration_rejection_reason=reason`,
   `registration_review_at=now`, `registration_reviewer_id=current_user.id`.
3. Envia email de rejeição (template novo,
   `send_registration_rejected_email`). Inclui `reason` se fornecido.
4. `create_audit_log("registration_rejected", ...)`.

**Response**: `{"message": "Pedido rejeitado."}`.

---

## Email — novo template

`email_service.py`:

```python
async def send_registration_rejected_email(
    name: str, email: str, reason: Optional[str] = None,
) -> dict: ...
```

Template HTML neutro, em PT, com cores ACCTA (Carmesim como acento
único), mensagem cordial. Inclui `reason` se truthy, senão omite o
bloco.

A função de aprovação **não** precisa de template novo — reutiliza
`send_invite_email` que já existe.

---

## Frontend

### Nova página: `frontend/src/pages/public/CriarContaPage.js`

- Rota pública: `/criar-conta`
- Layout: `PublicLayout` (header marketing + footer).
- Form (react-hook-form + zod):
  - Nome (obrigatório, 2-100 chars)
  - Email (obrigatório, válido)
  - Telefone (opcional)
  - Departamento / função (opcional, free text)
  - **Cargo na associação** (dropdown, default "Sócio") — usa shadcn/ui
    `<Select>`, opções vindas de `CARGOS_DECLARADOS` (idealmente um
    endpoint público `GET /api/auth/registration-options` para evitar
    hardcode no frontend; ou constante partilhada via build).
  - Checkbox consentimento RGPD (obrigatório, link para política)
  - Campo escondido `website` (honeypot, `tabIndex=-1`,
    `autoComplete=off`, `aria-hidden=true`)
  - **Nota visível**: "O nº de associado será atribuído automaticamente
    após aprovação."
- Botão "Enviar pedido" → primário Carmesim (único acento da página).
- Após sucesso: card neutro "Pedido enviado. Vamos enviar email quando
  for revisto." + CTA secundário "Voltar à página inicial".
- Erros: toast (sonner) com `error.response?.data?.detail`.
- Schema partilhado em `frontend/src/utils/authSchemas.js` →
  `registrationSchema`.

### Link a partir da `LoginPage`

Adicionar abaixo do botão "Entrar":

> Ainda não é sócio? **Criar conta**

Tipografia neutra, "Criar conta" como link Carmesim (link-on-white já
permitido pelo design system).

### Painel admin: `frontend/src/pages/private/AdminPedidosInscricaoPage.js`

- Rota protegida `/admin/pedidos-inscricao`, `allowedRoles=["admin"]`.
- Adicionar entrada no `PrivateLayout` sidebar (secção Administração)
  com badge contando pedidos pendentes.
- Tabela: nome, email, **cargo declarado**, **member_id**, telefone,
  departamento, data do pedido. Cargo declarado destacado (badge
  neutro) para o admin perceber rapidamente se é candidato a órgão
  social vs. sócio simples.
- Acções por linha:
  - **Aprovar** (botão primário Carmesim) → modal com:
    - role final (dropdown: `socio` default, ou `financeiro` /
      `moderador` / `admin` — admin decide com base no
      `cargo_declarado`).
    - `cargo` final (editável, prefilled com `cargo_declarado`).
    - confirma → POST approve com `{role, cargo}` → toast sucesso →
      invalidar query → user vai para lista "pendente_convite".
  - **Rejeitar** (botão Secondary `border-[#D1D5DB]`, ícone destrutivo)
    → modal com motivo opcional → POST reject → toast → invalidar.
- Filtro por status (default: pendentes; tab para "Rejeitados").
- Loading: `Skeleton` linhas.
- Empty state: "Sem pedidos pendentes."

### `utils/api.js`

Novo grupo:

```js
export const registrationAPI = {
  submit: (payload) => apiClient.post('/auth/register', payload),
  listPending: (params) => apiClient.get('/admin/registration-requests', { params }),
  approve: (id) => apiClient.post(`/admin/registration-requests/${id}/approve`),
  reject: (id, reason) => apiClient.post(`/admin/registration-requests/${id}/reject`, { reason }),
};
```

---

## Notificações

- `notify_admins` no submit (`type="system"`, link
  `/admin/pedidos-inscricao`).
- Notificação ao candidato **não se aplica** — ainda não tem conta no
  sistema; o canal é só o email.

---

## Auditoria

Todas as acções relevantes têm `create_audit_log`:

| Acção | Actor | Target |
|-------|-------|--------|
| `registration_requested` | candidato (próprio) | candidato |
| `registration_approved` | admin | candidato |
| `registration_rejected` | admin | candidato |

---

## Segurança e abuso

- Endpoint público sem auth → atractor para spam/bots.
- **Rate limit** `3/hour` por IP em `/api/auth/register` (slowapi).
- **Captcha**: não nesta primeira fase; se houver ondas de spam, adicionar
  hCaptcha invisível (campo `captcha_token` no payload, verificação
  server-side). Fora de scope desta spec.
- **Honeypot**: campo `website` hidden no form — se preenchido, devolver
  201 falso e descartar silenciosamente.
- **Anti-enumeração**: mensagens de erro idênticas para "email já
  registado" e "email rejeitado" se isso vier a ser um vector.
- Validações duras de tamanho/regex em todos os campos (já no Pydantic
  via `Field(min_length=..., max_length=...)`).

---

## Plano de implementação (ordem sugerida)

1. **Models + status** — adicionar `pendente_aprovacao`/`rejeitado` a
   `USER_STATUSES`, modelo `RegistrationRequest`. Schema/índice em
   `ensure_schema()`.
2. **Email** — template `send_registration_rejected_email`.
3. **Routes** — `POST /api/auth/register` em `auth_routes.py`; novos
   endpoints `registration-requests` em `admin.py`.
4. **Tests backend**:
   - duplicado nas 3 variantes (ativo, pendente, rejeitado)
   - `consent_data=False` rejeita
   - approve gera invite_token e altera status correctamente
   - reject seta status e dispara email
   - rate limit (smoke)
5. **Frontend** — `CriarContaPage`, link no `LoginPage`,
   `AdminPedidosInscricaoPage`, badge no sidebar, `registrationAPI`,
   schema zod.
6. **Tests frontend** — render + submit happy/erro de
   `CriarContaPage`; render + aprovar/rejeitar no painel admin
   (mocking).
7. **Manual** — abrir `/criar-conta`, submeter, confirmar no painel
   admin, aprovar, abrir link do email no inbox de dev, definir
   password, confirmar `ativo`.

---

## Riscos / decisões em aberto

- **Email obrigatório verificado?** O fluxo actual já implica que o
  email é verificado (o invite-link só funciona se o utilizador receber
  o email após aprovação). Não precisa de double opt-in adicional.
- **Bootstrap da sequência `member_id_seq` em produção** —
  imperativo: se houver utilizadores existentes com IDs
  `ACCTA-XXXX`, o `setval` tem de correr antes do primeiro pedido de
  auto-registo, senão colide. Script de migration manual no deploy.
- **Notificar admin por email** além do sino? Fora de scope (sino +
  badge no sidebar é suficiente para piloto).
- **Limite total de pedidos pendentes**? Não para fase 1. Monitorizar.
- **Trocar `member_id` aleatórios antigos por sequenciais?** Não — só
  novos. Mantém ID imutável e estável para sócios actuais.

---

## Stop conditions (CLAUDE.md)

Esta spec NÃO atinge nenhuma stop condition:
- Não altera JWT secret.
- Não muda CORS.
- Não envia emails para utilizadores reais (envia apenas para o email
  que o próprio candidato submeteu — fluxo legítimo opt-in).
- Adiciona estados a `USER_STATUSES` e uma sequence — aditivo, sem
  migração destrutiva.

**Decisões já confirmadas com o utilizador**:
1. ✅ Aprovação gera invite (reusa `SetupAccount`).
2. ✅ Sem captcha na fase 1 — só rate-limit + honeypot.
3. ✅ Form: Nome + Email + RGPD + Telefone + Departamento + dropdown
   de cargo + member_id auto-sequencial.
4. ✅ Cargo é declarativo — admin decide o role no momento de aprovar.
5. ✅ Formato `member_id`: `ACCTA-0001` zero-padded.

**Pronto para implementar.**
