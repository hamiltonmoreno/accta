# Spec — MFA (TOTP) · F2 do `spec-verificacao-seguranca-saas`

> **Origem**: F2 de `tasks/spec-verificacao-seguranca-saas.md` (§3.3, §12). Fecha a
> única lacuna de "alto valor" do checklist SaaS: **sem MFA**. Contas `admin`/
> `financeiro` gerem utilizadores, finanças e moderação — roubo de password =
> comprometimento total. MFA TOTP fecha isso.
>
> **Estado do sistema**: app ainda **não em produção**, **sem dados reais** →
> tudo aditivo; migração/drop é stop condition (não aplicável aqui).

---

## 0. Decisões fechadas com o dono (gates D1/D2/âmbito)

- **D1 — Obrigatoriedade**: MFA **obrigatório para `admin` + `financeiro`**;
  **opt-in** para `moderador` e `socio`.
- **Armazenamento do segredo TOTP**: **cifrado em repouso** (Fernet com chave
  derivada do `SECRET_KEY`).
- **Âmbito desta entrega (PR1 = backend)**: endpoints enroll/verify/disable/
  status + gate no login + sinalização de auto-enrolment + testes. **Frontend
  (QR, ecrã de códigos, passo-2 do login, forçar enrolment) fica para PR2** —
  fora do âmbito deste spec.

---

## 1. Arquitetura

- **Novo módulo `backend/mfa.py`** (mantém `auth.py` enxuto; responsabilidade
  única: criptografia + TOTP + backup codes + política de obrigatoriedade).
- **Endpoints** em `routes/auth_routes.py` sob `/api/auth/mfa/*` (autenticados
  via `Depends(get_current_user)`), + alteração mínima no `POST /auth/login`.
- **Persistência**: campos novos no `doc` jsonb da coleção `users`. Segredos
  **nunca** entram em modelos de resposta.
- **Dependências novas**: `pyotp` (TOTP) e `cryptography` (Fernet). `bcrypt`
  permanece pinado em `4.0.1` (não tocar).

---

## 2. Modelos (`models.py`) — tudo aditivo/opcional

```python
# UserBase: ÚNICO campo novo exposto (flag). Docs antigos sem a chave → False.
class UserBase(BaseModel):
    ...
    mfa_enabled: bool = False

# UserLogin: otp opcional (2.º fator no mesmo endpoint de login).
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    otp: Optional[str] = None

# Token: flag aditiva — sinaliza ao frontend que o utilizador (papel
# obrigatório) ainda não tem MFA e deve ser forçado a configurá-lo.
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User
    mfa_setup_required: bool = False

# Novos request models:
class MfaVerifyRequest(BaseModel):
    otp: str

class MfaDisableRequest(BaseModel):
    password: str
```

**Segredos vivem SÓ no doc jsonb, nunca como campos de modelo**:
`mfa_secret` (Fernet), `mfa_pending_secret` (Fernet, durante o enrolment),
`mfa_backup_codes` (lista de hashes sha256). Como `User` tem
`ConfigDict(extra="ignore")`, `User(**doc)` descarta-os automaticamente; o login
faz `pop()` explícito antes de construir o `User`, como já faz à `password`.

---

## 3. Módulo `backend/mfa.py`

```python
import base64, hashlib, secrets
from typing import Optional
import pyotp
from cryptography.fernet import Fernet, InvalidToken
from auth import SECRET_KEY

MFA_MANDATORY_ROLES = {"admin", "financeiro"}
ISSUER = "Portal ACCTA"
BACKUP_CODE_COUNT = 10

def _fernet() -> Fernet:
    # Chave Fernet determinística a partir do SECRET_KEY (32 bytes urlsafe-b64).
    key = base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())
    return Fernet(key)

def encrypt_secret(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()

def decrypt_secret(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()

def generate_totp_secret() -> str:
    return pyotp.random_base32()

def provisioning_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=ISSUER)

def verify_totp(secret: str, code: str) -> bool:
    # valid_window=1 tolera +-30s de drift de relógio.
    return pyotp.TOTP(secret).verify((code or "").strip(), valid_window=1)

def generate_backup_codes(n: int = BACKUP_CODE_COUNT) -> list[str]:
    # Códigos de alta entropia, legíveis (ex. "a1b2-c3d4").
    return [f"{secrets.token_hex(2)}-{secrets.token_hex(2)}" for _ in range(n)]

def hash_backup_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode()).hexdigest()

def is_mfa_mandatory(role: str) -> bool:
    return role in MFA_MANDATORY_ROLES
```

> Nota de rotação: como a chave Fernet deriva do `SECRET_KEY`, **rotar o
> `SECRET_KEY` invalidaria os segredos MFA** (re-enrolment necessário). Isto
> liga ao gate **D6** (rotação multi-chave) e a um stop condition — não é
> resolvido aqui.

---

## 4. Endpoints (`routes/auth_routes.py`)

Todos sob `/api/auth`. Os de MFA exigem `Depends(get_current_user)`. Cada
escrita gera audit log.

### `POST /auth/mfa/setup` (autenticado, `@limiter.limit("5/minute")`)
- Gera `secret = generate_totp_secret()`.
- `update_one({"id": user.id}, {"$set": {"mfa_pending_secret": encrypt_secret(secret)}})`
  (NÃO mexe em `mfa_secret`/`mfa_enabled` — um utilizador já com MFA pode
  re-configurar sem perder o ativo até confirmar).
- Audit `mfa_setup_initiated`.
- **Resposta 200**: `{"secret": secret, "otpauth_uri": provisioning_uri(secret, user.email)}`
  (o segredo em claro é devolvido **só aqui**, para o frontend gerar o QR; não é
  persistido em claro).

### `POST /auth/mfa/verify` (autenticado) — body `MfaVerifyRequest`
- Lê `mfa_pending_secret`; se ausente → `400 "Inicie a configuracao de MFA primeiro"`.
- `decrypt_secret` + `verify_totp(secret, otp)`; se inválido → `400 "Codigo invalido"`.
- Sucesso: `codes = generate_backup_codes()`;
  `update_one($set: {mfa_secret: <pending>, mfa_enabled: True,
  mfa_backup_codes: [hash_backup_code(c) for c in codes]}, $unset: {mfa_pending_secret: ""})`.
- Audit `mfa_enabled`.
- **Resposta 200**: `{"backup_codes": codes}` (os 10 em claro, **uma única vez**).

### `POST /auth/mfa/disable` (autenticado) — body `MfaDisableRequest`
- Re-autenticação: lê o doc completo, `verify_password(data.password, doc["password"])`;
  se falhar → `403 "Password incorreta"`.
- `update_one($set: {mfa_enabled: False}, $unset: {mfa_secret: "",
  mfa_pending_secret: "", mfa_backup_codes: ""})`.
- Audit `mfa_disabled`.
- **Resposta 200**: `{"message": "MFA desativado"}`.
- (Papéis obrigatórios podem desativar, mas no próximo login virão com
  `mfa_setup_required=True` → frontend força re-enrolment. Aceitável.)

### `GET /auth/mfa/status` (autenticado)
- **Resposta 200**: `{"enabled": bool, "mandatory": is_mfa_mandatory(user.role),
  "backup_codes_remaining": len(doc.get("mfa_backup_codes", []))}`.

---

## 5. Alteração no `POST /auth/login` (o gate — mínima e aditiva)

Inserir **depois** da verificação de password bem-sucedida e **antes** de
`reset_failed_logins`/emissão do token:

```python
# (password já validada acima; user_doc carregado)
if user_doc.get("mfa_enabled"):
    if not credentials.otp:
        await create_audit_log(user_doc["id"], "login_mfa_challenge", request=request)
        raise HTTPException(status_code=401, detail="mfa_required")
    secret = decrypt_secret(user_doc["mfa_secret"])
    code = credentials.otp.strip()
    consumed_backup = _consume_backup_code(user_doc, code)  # devolve nova lista ou None
    if not verify_totp(secret, code) and consumed_backup is None:
        await record_failed_login(credentials.email, ip=...)   # OTP conta p/ lockout
        await create_audit_log(user_doc["id"], "login_mfa_failed", request=request)
        raise HTTPException(status_code=401, detail="mfa_invalido")
    if consumed_backup is not None:
        await db.users.update_one({"id": user_doc["id"]},
                                  {"$set": {"mfa_backup_codes": consumed_backup}})

# sucesso (com ou sem MFA):
await reset_failed_logins(credentials.email)
...
mfa_setup_required = is_mfa_mandatory(user_doc["role"]) and not user_doc.get("mfa_enabled")
for k in ("password", "invite_token", "mfa_secret", "mfa_pending_secret", "mfa_backup_codes"):
    user_doc.pop(k, None)
user = User(**user_doc)
token = create_access_token({"sub": user.id})
set_session_cookie(response, token)
return Token(access_token=token, token_type="bearer", user=user,
             mfa_setup_required=mfa_setup_required)
```

Helper (em `auth_routes.py` ou `mfa.py`):
```python
def _consume_backup_code(user_doc: dict, code: str) -> Optional[list[str]]:
    """Se `code` casa um hash em mfa_backup_codes, devolve a lista SEM esse
    hash (uso único). Caso contrário, None."""
    h = hash_backup_code(code)
    codes = user_doc.get("mfa_backup_codes") or []
    return [c for c in codes if c != h] if h in codes else None
```

**Semântica de erros (todos 401, distinguíveis pelo `detail`)**:
- `Credenciais invalidas` — password errada (inalterado, anti-enumeração).
- `mfa_required` — password OK, falta OTP (frontend mostra o campo OTP).
- `mfa_invalido` — password OK, OTP/backup errado (conta p/ lockout).

---

## 6. Auto-enrolment (papéis obrigatórios)

- O login **não bloqueia** quem é obrigatório mas ainda não inscreveu (não pode
  inscrever sem entrar — chicken-and-egg). Sinaliza com `Token.mfa_setup_required`.
- O **frontend (PR2)** usa essa flag para forçar o ecrã de configuração antes de
  qualquer outra ação. Backend não impõe bloqueio por-rota nesta fase (app
  pré-produção; a flag + gate-no-login-quando-inscrito é suficiente para F2).

---

## 7. Segurança e armazenamento

- Segredo TOTP **cifrado** (Fernet) em repouso → BD comprometida não revela o
  segredo. Backup codes guardados como **hash sha256** (alta entropia → hash
  rápido chega; sem necessidade de bcrypt).
- Segredos **nunca** em respostas: não são campos de `User` (`extra="ignore"`) +
  `pop()` explícito no login. `GET /auth/me`, `get_current_user` e
  `get_user_from_token` constroem `User(**doc)` → descartados.
- OTP/backup errados **contam para o lockout** existente (`record_failed_login`)
  → trava brute-force de OTP (6 dígitos).
- `valid_window=1` tolera drift de relógio (±30s).

---

## 8. Plano de testes — `backend/tests/test_mfa.py` (unit, `mock_db`)

- **Cripto**: `encrypt_secret`/`decrypt_secret` round-trip; chave determinística
  do `SECRET_KEY`; `decrypt` de token adulterado levanta erro tratado.
- **setup**: guarda `mfa_pending_secret` cifrado; devolve `secret` + `otpauth_uri`
  (formato `otpauth://totp/...issuer=Portal%20ACCTA`); não ativa.
- **verify**: OTP correto (gerado via `pyotp.TOTP(secret).now()`) → `mfa_enabled=True`,
  promove segredo, devolve 10 backup codes; OTP errado → 400; sem pending → 400.
- **disable**: password correta → limpa campos; password errada → 403.
- **status**: reflete enabled/mandatory/contagem de backups.
- **login (4 ramos)**: `mfa_enabled` sem otp → 401 `mfa_required`; otp errado →
  401 `mfa_invalido` + `record_failed_login` chamado; TOTP correto → `Token`;
  backup code válido → `Token` + código consumido (lista encolhe, persistida).
- **mfa_setup_required**: admin não-inscrito → `Token.mfa_setup_required is True`;
  sócio não-inscrito → `False`; qualquer um inscrito → `False`.
- **não-exposição**: resposta de login e `GET /auth/me` **não** contêm
  `mfa_secret`/`mfa_pending_secret`/`mfa_backup_codes`.

> Arquitetura de testes (CLAUDE.md): chamadas diretas às funções de rota com
> `mock_db` + `pytest.raises(HTTPException)`; para o login (decorado com
> `@limiter.limit`) desativar `auth_routes.limiter.enabled` e passar `Request`
> real, como em `test_lockout_integration.py`. `mock_db` não pré-liga campos
> novos — usar `find_one`/`update_one` AsyncMock por teste.

---

## 9. Stop conditions (confirmadas — nenhuma disparada)

- **Algoritmo/`SECRET_KEY`**: inalterados (Fernet deriva, não altera). ✅
- **Pydantic**: só campos aditivos/opcionais (não quebra docs existentes). ✅
- **Migração/drop de dados**: nenhuma (campos aditivos; ausência → default). ✅
- **CORS / remover rota**: não. ✅
- **Emails reais**: nenhum (enrolment é in-app via QR; backup codes no ecrã). ✅
- **Dependências novas**: `pyotp`, `cryptography` — realçado, não é stop condition.

---

## 10. Em aberto (fora do âmbito de F2/PR1)

- **PR2 — Frontend**: ecrã de setup (QR + segredo manual), ecrã de backup codes,
  campo OTP no login (orquestrado por `detail` `mfa_required`), forçar enrolment
  quando `mfa_setup_required`.
- **D6 — rotação de `SECRET_KEY`**: invalidaria segredos MFA (stop condition;
  multi-chave futura).
- **Bloqueio por-rota** para papéis obrigatórios não-inscritos (reforço; adiado —
  a flag + frontend chega para pré-produção).

---

## 11. Review (preencher ao concluir)

- [x] Modelos aditivos + `mfa.py` + endpoints + gate no login implementados.
- [x] `test_mfa.py` verde (25 testes); sem regressão em `test_auth_*`/`test_rate_limit`/`test_lockout_integration` (suite de segurança: 137 passed).
- [x] `pyotp==2.9.0` em `requirements.txt`; `cryptography` transitivo via `python-jose[cryptography]`; `ruff` limpo (`mfa.py`, `models.py`, `routes/auth_routes.py`, `tests/test_mfa.py`).
- [x] Segredos comprovadamente não-expostos (`test_user_drops_mfa_secret_fields` + `test_login_response_hides_mfa_secret`).
- **Conclusão**: F2 (backend) concluído via TDD em 5 tarefas. Implementado o módulo
  `backend/mfa.py` (Fernet com chave derivada do `SECRET_KEY` + TOTP via `pyotp` +
  backup codes hash-sha256 + política de obrigatoriedade), campos aditivos em
  `models.py` (`UserBase.mfa_enabled`, `UserLogin.otp`, `Token.mfa_setup_required`,
  `MfaVerifyRequest`, `MfaDisableRequest`), 4 endpoints `/api/auth/mfa/{setup,verify,
  disable,status}` e o gate no `POST /auth/login` (2.º fator TOTP **ou** backup code
  de uso único, OTP errado conta para o lockout existente, `detail` distinguível:
  `mfa_required`/`mfa_invalido`). `mfa_setup_required` sinaliza papéis obrigatórios
  ainda não inscritos. Cobertura: 26 testes em `tests/test_mfa.py` (cripto/primitivas,
  modelos, endpoints, 7 ramos de login). Sem regressão na suite de segurança
  (137 passed). Nenhuma stop condition disparada (tudo aditivo, sem migração/drop,
  sem alteração do `SECRET_KEY`/algoritmo, sem CORS, sem emails).

  **Divergências plano↔código resolvidas**: a assinatura real de `create_audit_log`
  em `helpers.py` é `(user_id, action, target_id=None, *, request=None, details=None, ...)`
  — `request` é keyword-only, logo as chamadas do plano (`create_audit_log(uid, "...",
  request=request|None)`) funcionam sem ajuste. O import de `mfa.consume_backup_code`
  em `auth_routes.py` só é adicionado na Task 4 (onde é usado), para cada commit ficar
  ruff-limpo.

  **Pós-revisão (opus, APROVADA)**: corrigida a lacuna *Importante* — `decrypt_secret`
  não tratava `InvalidToken` (segredo corrompido / `SECRET_KEY` rodado → 500 no login).
  Novo helper `mfa.verify_totp_encrypted(encrypted, code)` falha **fechado** (False),
  usado no gate do login e no `mfa_verify` (+ teste dedicado). **Diferido para F3**
  (Menor, não-bloqueante): (a) `mfa_verify`/`mfa_disable` registam audit sem IP/UA
  (`request=None`) — acrescentar `request: Request` para contexto de origem;
  (b) OTP errado partilha o contador de lockout da password — um atacante que conheça
  a password pode trancar a conta (DoS) — candidato a alerta de anomalia no F3.

  **Handoff PR2 (frontend)**: falta o ecrã de setup (QR a partir de `otpauth_uri` +
  segredo manual), o ecrã de backup codes (mostrados 1x na resposta de
  `/mfa/verify`), o campo OTP no login orquestrado pelo `detail` `mfa_required`, e
  forçar o enrolment quando `Token.mfa_setup_required is True`. Backend não impõe
  bloqueio por-rota nesta fase (pré-produção; flag + gate-no-login chegam).
