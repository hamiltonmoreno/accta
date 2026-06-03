# Comunicados (disparo de email + in-app) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dar ao Portal ACCTA um canal de **comunicados** — um compositor único onde admins (e órgãos com o privilégio `send_comunicados`) escrevem uma mensagem, escolhem destinatários (segmentos + seleção manual) e canais (in-app e/ou email), disparam por Resend em background com rastreio de estado/contagens; mais espelhamento automático por email dos atos oficiais de governança.

**Architecture:** Novo domínio `comunicados` (coleção + `routes/comunicados.py`). Um core reutilizável `comunicados_service.py` resolve destinatários e faz o fan-out: canal in-app via `helpers.notify_users`, canal email via `email_service.send_comunicado_batch` (Resend). O endpoint cria o comunicado (`status=a_enviar`) e agenda `dispatch_comunicado` em `BackgroundTasks`. A fase automática (F3) reusa o mesmo core via `dispatch_oficial_auto`, ligado aos endpoints de convocatória/abertura-de-votação/deliberação.

**Tech Stack:** FastAPI + asyncpg DAO (Mongo-compatible), Pydantic v2, Resend, slowapi; React 19 + shadcn/ui + Tailwind; pytest.

**Spec:** `tasks/spec-comunicados-email.md` (mesmo ramo).

**Convenções obrigatórias** (de CLAUDE.md / `.claude/rules`): RBAC em cada endpoint protegido; `create_audit_log` em cada escrita admin; datas ISO-8601 string; IDs `str(uuid4())`; sem SQL cru nas rotas (schema/índices em `ensure_schema`); nunca expor `password`; **email a sócios reais é STOP-condition — testar só com mocks/dummies**.

---

## File Structure

| Ficheiro | Responsabilidade | Ação |
|---|---|---|
| `backend/models.py` | Modelos Pydantic dos comunicados + prefs | Modificar (acrescentar perto dos `Notification*`, ~L944) |
| `backend/database.py` | `COLLECTIONS` (+`comunicados`) e `_INDEX_DDL` | Modificar (L55-111 e L749+) |
| `backend/governance.py` | `PRIVILEGES` (+`send_comunicados`) | Modificar (L189-201) |
| `backend/email_service.py` | `comunicado_email_html` + `send_comunicado_batch` | Modificar (fim do ficheiro) |
| `backend/comunicados_service.py` | Core: resolver destinatários + dispatch + auto | **Criar** |
| `backend/routes/comunicados.py` | Endpoints REST | **Criar** |
| `backend/routes/__init__.py` | Registar router | Modificar (L30 + L62) |
| `backend/routes/assembleias.py` | Gatilhos F3 (convocatória, deliberação) | Modificar (L82-138, L263-329) |
| `backend/routes/eleicoes.py` | Gatilho F3 (abertura de votação) | Modificar (L270-281) |
| `backend/tests/conftest.py` | Pré-wire `comunicados` + patch service | Modificar (L160, L204-218) |
| `backend/tests/test_comunicados_service.py` | Testes do core | **Criar** |
| `backend/tests/test_comunicados_routes.py` | Testes dos endpoints | **Criar** |
| `backend/tests/test_email_comunicado.py` | Testes de render/batch | **Criar** |
| `backend/tests/test_comunicados_auto.py` | Testes dos gatilhos F3 | **Criar** |
| `frontend/src/utils/api.js` | Grupo `comunicadosAPI` | Modificar |
| `frontend/src/pages/private/AdminComunicadosPage.js` | Compositor + histórico | **Criar** |
| `frontend/src/pages/private/PerfilPage.js` | Toggle de opt-out | Modificar |
| `frontend/src/App.js` | Lazy import + Route | Modificar (L51 e bloco de rotas privadas) |
| `frontend/src/layouts/PrivateLayout.js` | Entrada na sidebar | Modificar |
| `accta/CLAUDE.md` | Contagem de tabelas 36→37 | Modificar |

---

# FASE F0 — Fundações (modelos, schema, privilégio)

### Task 1: Modelos Pydantic dos comunicados

**Files:**
- Modify: `backend/models.py` (acrescentar a seguir a `NotificationCreate`, ~L944)
- Test: `backend/tests/test_comunicados_service.py` (criado nesta task só com o teste de modelos)

- [ ] **Step 1: Confirmar imports de validators no topo de models.py**

Verificar que o topo de `models.py` importa `field_validator` e `model_validator`. Se faltarem, acrescentar à linha de import do pydantic:
```python
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
```

- [ ] **Step 2: Write the failing test**

Criar `backend/tests/test_comunicados_service.py`:
```python
import pytest
from pydantic import ValidationError
from models import ComunicadoCreate, ComunicadoSegment


def _valid_payload(**over):
    base = dict(
        subject="Convocatória AG",
        body="Corpo do comunicado com texto suficiente.",
        tipo="informativo",
        channels=["in_app", "email"],
        segment={"kind": "all_active"},
    )
    base.update(over)
    return base


def test_comunicado_create_valid():
    c = ComunicadoCreate(**_valid_payload())
    assert c.channels == ["in_app", "email"]
    assert c.notification_type == "comunicado"


def test_comunicado_create_dedupes_channels():
    c = ComunicadoCreate(**_valid_payload(channels=["email", "email"]))
    assert c.channels == ["email"]


@pytest.mark.parametrize("over", [
    {"channels": []},
    {"channels": ["sms"]},
    {"tipo": "spam"},
    {"body": "curto"},
    {"subject": "   "},
    {"cta_url": "javascript:alert(1)"},
    {"segment": {"kind": "role"}},          # value em falta
    {"segment": {"kind": "manual"}},        # user_ids em falta
    {"segment": {"kind": "galaxia"}},       # kind inválido
])
def test_comunicado_create_invalid(over):
    with pytest.raises(ValidationError):
        ComunicadoCreate(**_valid_payload(**over))
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && pytest tests/test_comunicados_service.py -v`
Expected: FAIL com `ImportError: cannot import name 'ComunicadoCreate'`.

- [ ] **Step 4: Implement the models**

Acrescentar em `backend/models.py` após `NotificationCreate`:
```python
# ===== COMUNICADOS (spec-comunicados-email) =====

COMUNICADO_TIPOS = ["oficial", "informativo"]
COMUNICADO_CHANNELS = ["in_app", "email"]
COMUNICADO_SEGMENT_KINDS = ["all_active", "role", "orgao", "member_category", "manual"]
COMUNICADO_STATUSES = ["a_enviar", "enviando", "enviado", "parcial", "falhado"]


class ComunicadoSegment(BaseModel):
    kind: str
    value: Optional[str] = None
    user_ids: Optional[List[str]] = None


class ComunicadoCreate(BaseModel):
    subject: str
    body: str
    tipo: str = "informativo"
    channels: List[str]
    segment: ComunicadoSegment
    notification_type: str = "comunicado"
    cta_label: Optional[str] = None
    cta_url: Optional[str] = None

    @field_validator("subject")
    @classmethod
    def _v_subject(cls, v):
        v = (v or "").strip()
        if not v:
            raise ValueError("Assunto obrigatório")
        if len(v) > 200:
            raise ValueError("Assunto demasiado longo (máx. 200)")
        return v

    @field_validator("body")
    @classmethod
    def _v_body(cls, v):
        if len((v or "").strip()) < 10:
            raise ValueError("Corpo demasiado curto")
        return v

    @field_validator("tipo")
    @classmethod
    def _v_tipo(cls, v):
        if v not in COMUNICADO_TIPOS:
            raise ValueError("Tipo inválido")
        return v

    @field_validator("channels")
    @classmethod
    def _v_channels(cls, v):
        if not v:
            raise ValueError("Selecione pelo menos um canal")
        bad = [c for c in v if c not in COMUNICADO_CHANNELS]
        if bad:
            raise ValueError(f"Canal inválido: {bad}")
        return list(dict.fromkeys(v))  # dedupe preservando ordem

    @field_validator("cta_url")
    @classmethod
    def _v_cta_url(cls, v):
        if v is None:
            return v
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL do CTA deve começar por http:// ou https://")
        return v

    @model_validator(mode="after")
    def _v_segment(self):
        seg = self.segment
        if seg.kind not in COMUNICADO_SEGMENT_KINDS:
            raise ValueError("Segmento inválido")
        if seg.kind in ("role", "orgao", "member_category") and not seg.value:
            raise ValueError("Este segmento requer 'value'")
        if seg.kind == "manual" and not seg.user_ids:
            raise ValueError("Selecione pelo menos um sócio")
        return self


class RecipientsCountRequest(BaseModel):
    tipo: str = "informativo"
    channels: List[str]
    segment: ComunicadoSegment


class EmailPreferencesUpdate(BaseModel):
    email_opt_out_informativos: bool
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_comunicados_service.py -v`
Expected: PASS (8+ casos).

- [ ] **Step 6: Commit**
```bash
git add backend/models.py backend/tests/test_comunicados_service.py
git commit -m "feat(comunicados): F0 modelos Pydantic + validacoes"
```

---

### Task 2: Coleção + índices + privilégio

**Files:**
- Modify: `backend/database.py` (`COLLECTIONS` L55-111; `_INDEX_DDL` L749+)
- Modify: `backend/governance.py` (`PRIVILEGES` L189-201)
- Modify: `accta/CLAUDE.md` (contagem de tabelas)

- [ ] **Step 1: Registar a coleção**

Em `backend/database.py`, dentro da tuple `COLLECTIONS`, acrescentar após `"regulamento_versoes",` (L103):
```python
    # comunicados (spec-comunicados-email):
    "comunicados",
```
Atualizar o comentário de L54 (`# All logical collections -> tables. 29 with Pydantic models + 7 without.` → `30 with Pydantic models + 7 without.`).

- [ ] **Step 2: Acrescentar índices**

No fim da tuple `_INDEX_DDL` (a seguir aos índices de `regulamento_versoes`, ~L884), acrescentar:
```python
    # comunicados (spec-comunicados-email)
    "CREATE INDEX IF NOT EXISTS ix_comunicados_created ON \"comunicados\" ((doc->>'created_at') DESC)",
    "CREATE INDEX IF NOT EXISTS ix_comunicados_status ON \"comunicados\" ((doc->>'status'))",
    "CREATE INDEX IF NOT EXISTS ix_comunicados_created_by ON \"comunicados\" ((doc->>'created_by'))",
    'CREATE INDEX IF NOT EXISTS ix_comunicados_source ON "comunicados" '
    "((doc->>'source_kind'), (doc->>'source_ref_id'))",
```

- [ ] **Step 3: Registar o privilégio**

Em `backend/governance.py`, na lista `PRIVILEGES` (após `"emit_cf_parecer",` L200), acrescentar:
```python
    # disparo de comunicados (spec-comunicados-email) — overlay aditivo:
    # admin OU este privilégio podem compor/enviar comunicados.
    "send_comunicados",
```

- [ ] **Step 4: Atualizar a contagem de tabelas no CLAUDE.md**

Em `accta/CLAUDE.md`, na linha do Stack que diz `36 tables`, mudar para `37 tables` e acrescentar `comunicados` à enumeração das tabelas de governança/finanças.

- [ ] **Step 5: Verify import sanity**

Run: `cd backend && python -c "import database, governance; assert 'comunicados' in database.COLLECTIONS; assert 'send_comunicados' in governance.PRIVILEGES; print('ok')"`
Expected: imprime `ok` sem exceção.

- [ ] **Step 6: Commit**
```bash
git add backend/database.py backend/governance.py CLAUDE.md
git commit -m "feat(comunicados): F0 coleccao comunicados + indices + privilegio send_comunicados"
```

---

# FASE F1 — Backend manual (core, email, endpoints)

### Task 3: Test harness — pré-wire `comunicados` + patch do service

**Files:**
- Modify: `backend/tests/conftest.py` (L160 tuple; L204-218 patches)

- [ ] **Step 1: Pré-wire a coleção `comunicados` no `mock_db`**

Na tuple de coleções dentro de `mock_db` (conftest.py L160-184), acrescentar `"comunicados",` à lista.

- [ ] **Step 2: Patch do módulo de serviço**

Em `conftest.py`, na zona dos patches (após `monkeypatch.setattr(helpers, "db", fake_db)`, L210), acrescentar:
```python
    # comunicados_service faz `from database import db` no topo — patch explícito
    if "comunicados_service" in sys.modules:
        monkeypatch.setattr(sys.modules["comunicados_service"], "db", fake_db)
```

- [ ] **Step 3: Verify**

Run: `cd backend && python -c "import ast,sys; print('comunicados' in open('tests/conftest.py').read())"`
Expected: `True`. (Verificação completa corre nas tasks seguintes.)

- [ ] **Step 4: Commit**
```bash
git add backend/tests/conftest.py
git commit -m "test(comunicados): F1 pre-wire mock_db + patch comunicados_service"
```

---

### Task 4: `comunicados_service.resolve_recipients`

**Files:**
- Create: `backend/comunicados_service.py`
- Test: `backend/tests/test_comunicados_service.py` (acrescentar)

- [ ] **Step 1: Write the failing tests**

Acrescentar a `backend/tests/test_comunicados_service.py`:
```python
import comunicados_service


def _set_users(mock_db, users):
    mock_db.users.find.return_value.to_list.return_value = users


MEMBROS = [
    {"id": "u1", "name": "A", "email": "a@x.cv", "role": "socio",
     "member_category": "ordinario", "account_type": "member"},
    {"id": "u2", "name": "B", "email": "b@x.cv", "role": "socio",
     "member_category": "fundador", "account_type": "member",
     "email_opt_out_informativos": True},
    {"id": "u3", "name": "C", "email": None, "role": "financeiro",
     "member_category": "ordinario", "account_type": "member"},
    {"id": "sys", "name": "Sys", "email": "sys@x.cv", "role": "admin",
     "account_type": "technical"},
]


@pytest.mark.asyncio
async def test_resolve_all_active_excludes_technical(mock_db):
    _set_users(mock_db, MEMBROS)
    res = await comunicados_service.resolve_recipients(
        {"kind": "all_active"}, channel="in_app", tipo="informativo")
    ids = {u["id"] for u in res}
    assert ids == {"u1", "u2", "u3"}          # "sys" (technical) excluído


@pytest.mark.asyncio
async def test_resolve_email_informativo_drops_optout_and_no_email(mock_db):
    _set_users(mock_db, MEMBROS)
    res = await comunicados_service.resolve_recipients(
        {"kind": "all_active"}, channel="email", tipo="informativo")
    ids = {u["id"] for u in res}
    assert ids == {"u1"}                       # u2 opt-out, u3 sem email


@pytest.mark.asyncio
async def test_resolve_email_oficial_ignores_optout(mock_db):
    _set_users(mock_db, MEMBROS)
    res = await comunicados_service.resolve_recipients(
        {"kind": "all_active"}, channel="email", tipo="oficial")
    ids = {u["id"] for u in res}
    assert ids == {"u1", "u2"}                 # u2 incluído (oficial); u3 sem email fora


@pytest.mark.asyncio
async def test_resolve_role_and_category(mock_db):
    _set_users(mock_db, MEMBROS)
    by_role = await comunicados_service.resolve_recipients(
        {"kind": "role", "value": "financeiro"}, channel="in_app", tipo="oficial")
    assert {u["id"] for u in by_role} == {"u3"}
    by_cat = await comunicados_service.resolve_recipients(
        {"kind": "member_category", "value": "fundador"}, channel="in_app", tipo="oficial")
    assert {u["id"] for u in by_cat} == {"u2"}


@pytest.mark.asyncio
async def test_resolve_manual(mock_db):
    _set_users(mock_db, MEMBROS)
    res = await comunicados_service.resolve_recipients(
        {"kind": "manual", "user_ids": ["u2", "naoexiste"]}, channel="in_app", tipo="oficial")
    assert {u["id"] for u in res} == {"u2"}
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_comunicados_service.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'comunicados_service'`.

- [ ] **Step 3: Create the service module**

Criar `backend/comunicados_service.py`:
```python
"""Core reutilizável de comunicados (spec-comunicados-email).

Resolve destinatários a partir de um segmento e faz o fan-out por canais
(in-app via helpers.notify_users; email via email_service.send_comunicado_batch).
Usado pelo endpoint manual (routes/comunicados.py) e pelos gatilhos automáticos
de governança (F3).
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from database import db
from helpers import notify_users, members_of_orgao
# NOTA: comunicado_email_html / send_comunicado_batch são importados no topo
# na Task 6 (dispatch), depois de existirem no email_service — não importar aqui.

logger = logging.getLogger(__name__)

_MEMBER_PROJECTION = {
    "_id": 0, "id": 1, "name": 1, "email": 1, "role": 1,
    "account_type": 1, "member_category": 1, "cargo": 1,
    "email_opt_out_informativos": 1,
}


async def _base_members() -> list[dict]:
    """Sócios activos, excluindo contas técnicas."""
    users = await db.users.find({"status": "ativo"}, _MEMBER_PROJECTION).to_list(None)
    return [u for u in users if u.get("account_type") != "technical"]


async def resolve_recipients(segment: dict, *, channel: str, tipo: str) -> list[dict]:
    """Lista de destinatários `{id,name,email,...}` para um canal.

    - exclui contas técnicas (sempre);
    - canal `email` + tipo `informativo`: exclui quem fez opt-out;
    - canal `email`: exclui quem não tem email;
    - tipo `oficial`: ignora o opt-out (dever estatutário).
    """
    members = await _base_members()
    kind = segment.get("kind")
    value = segment.get("value")
    if kind == "all_active":
        sel = members
    elif kind == "role":
        sel = [u for u in members if u.get("role") == value]
    elif kind == "member_category":
        sel = [u for u in members if u.get("member_category") == value]
    elif kind == "orgao":
        ids = set(await members_of_orgao(value))
        sel = [u for u in members if u["id"] in ids]
    elif kind == "manual":
        wanted = set(segment.get("user_ids") or [])
        sel = [u for u in members if u["id"] in wanted]
    else:
        sel = []
    if channel == "email":
        if tipo == "informativo":
            sel = [u for u in sel if not u.get("email_opt_out_informativos")]
        sel = [u for u in sel if u.get("email")]
    return sel
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && pytest tests/test_comunicados_service.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add backend/comunicados_service.py backend/tests/test_comunicados_service.py
git commit -m "feat(comunicados): F1 resolve_recipients (segmentos + opt-out + tecnicas)"
```

---

### Task 5: Render de email + envio em batch

**Files:**
- Modify: `backend/email_service.py` (fim do ficheiro; import `escape` no topo)
- Test: `backend/tests/test_email_comunicado.py`

- [ ] **Step 1: Write the failing tests**

Criar `backend/tests/test_email_comunicado.py`:
```python
import pytest
import email_service
from email_service import comunicado_email_html


def test_render_escapes_and_includes_subject():
    html = comunicado_email_html("Assunto <b>", "Linha 1\n\nLinha 2", tipo="oficial")
    assert "Assunto &lt;b&gt;" in html
    assert "Linha 1" in html and "Linha 2" in html


def test_render_cta_only_when_label_and_url():
    sem = comunicado_email_html("S", "corpo longo o suficiente")
    assert "href=" not in sem.split("Cabo Verde")[0] or "Aceder" not in sem
    com = comunicado_email_html("S", "corpo longo", cta_label="Ver", cta_url="https://x.cv/a")
    assert 'href="https://x.cv/a"' in com and ">Ver<" in com


def test_render_optout_note_only_informativo():
    inf = comunicado_email_html("S", "corpo longo", tipo="informativo")
    ofi = comunicado_email_html("S", "corpo longo", tipo="oficial")
    assert "desactivar" in inf.lower()
    assert "desactivar" not in ofi.lower()


@pytest.mark.asyncio
async def test_batch_without_api_key_counts_all_failed(monkeypatch):
    monkeypatch.setattr(email_service, "RESEND_API_KEY", None)
    res = await email_service.send_comunicado_batch(["a@x.cv", "b@x.cv"], "S", "<p>x</p>")
    assert res["sent"] == 0 and res["failed"] == 2
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_email_comunicado.py -v`
Expected: FAIL com `ImportError: cannot import name 'comunicado_email_html'`.

- [ ] **Step 3: Implement render + batch**

No topo de `backend/email_service.py`, garantir o import:
```python
from html import escape
```
No fim de `backend/email_service.py`, acrescentar:
```python
def comunicado_email_html(subject: str, body: str, cta_label: str = None,
                          cta_url: str = None, *, tipo: str = "informativo") -> str:
    """Renderiza um comunicado no template ACCTA. Conteúdo escapado; \n\n →
    parágrafos, \n → <br>. CTA (Carmesim) só com label+url. Nota de opt-out
    apenas em comunicados informativos."""
    safe_subject = escape(subject, quote=True)
    paragraphs = ""
    for block in (body or "").split("\n\n"):
        block = block.strip()
        if not block:
            continue
        inner = escape(block, quote=True).replace("\n", "<br>")
        paragraphs += (
            f'<p style="margin:0 0 14px;font-size:14px;color:#6b7280;'
            f'line-height:1.7;">{inner}</p>'
        )
    cta_block = ""
    if cta_label and cta_url:
        cta_block = f"""
    <table cellpadding="0" cellspacing="0" width="100%"><tr><td align="center">
      <a href="{escape(cta_url, quote=True)}" style="display:inline-block;padding:12px 32px;background-color:#C7202F;color:#ffffff;font-size:14px;font-weight:600;text-decoration:none;border-radius:8px;">
        {escape(cta_label, quote=True)}
      </a>
    </td></tr></table>"""
    optout_note = ""
    if tipo == "informativo":
        optout_note = (
            '<p style="margin:20px 0 0;font-size:12px;color:#9ca3af;line-height:1.5;">'
            'Pode desactivar estes avisos informativos no seu perfil no Portal ACCTA.</p>'
        )
    content = f"""
    <h2 style="margin:0 0 16px;font-size:20px;color:#3A3A3A;">{safe_subject}</h2>
    {paragraphs}{cta_block}{optout_note}"""
    return _base_template(content)


async def send_comunicado_batch(recipients: list, subject: str, html: str) -> dict:
    """Envia o mesmo email a N destinatários — individualmente (sem To/CC
    partilhado). Usa Resend Batch quando disponível (chunks de 100), com
    fallback para envios individuais. Devolve {sent, failed, errors}."""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set. Comunicado a %d destinatarios nao enviado.", len(recipients))
        return {"sent": 0, "failed": len(recipients), "errors": ["resend_not_configured"]}

    sent = 0
    failed = 0
    errors: list = []
    CHUNK = 100
    use_batch = hasattr(resend, "Batch")
    for i in range(0, len(recipients), CHUNK):
        chunk = recipients[i:i + CHUNK]
        if use_batch:
            params = [
                {"from": f"{APP_NAME} <{SENDER_EMAIL}>", "to": [r], "subject": subject, "html": html}
                for r in chunk
            ]
            try:
                await asyncio.to_thread(resend.Batch.send, params)
                sent += len(chunk)
                continue
            except Exception as e:  # noqa: BLE001 — fallback per-recipient
                logger.error("Resend Batch falhou, fallback individual: %s", e)
        for r in chunk:
            res = await send_email(r, subject, html)
            if res.get("status") == "sent":
                sent += 1
            else:
                failed += 1
                errors.append(res.get("error", res.get("reason", "unknown")))
    return {"sent": sent, "failed": failed, "errors": errors[:20]}
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && pytest tests/test_email_comunicado.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add backend/email_service.py backend/tests/test_email_comunicado.py
git commit -m "feat(comunicados): F1 render de email + send_comunicado_batch"
```

---

### Task 6: `dispatch_comunicado` (fan-out + estados/contagens)

**Files:**
- Modify: `backend/comunicados_service.py`
- Test: `backend/tests/test_comunicados_service.py` (acrescentar)

- [ ] **Step 1: Write the failing tests**

Acrescentar a `backend/tests/test_comunicados_service.py`:
```python
def _doc(**over):
    d = dict(
        id="c1", subject="S", body="corpo longo o suficiente",
        cta_label=None, cta_url=None, tipo="informativo",
        channels=["in_app", "email"], segment={"kind": "all_active"},
        notification_type="comunicado", status="a_enviar",
    )
    d.update(over)
    return d


@pytest.mark.asyncio
async def test_dispatch_skips_if_not_a_enviar(mock_db):
    mock_db.comunicados.find_one.return_value = _doc(status="enviado")
    res = await comunicados_service.dispatch_comunicado("c1")
    assert res == {"skipped": True}


@pytest.mark.asyncio
async def test_dispatch_both_channels_counts(mock_db, monkeypatch):
    mock_db.comunicados.find_one.return_value = _doc()
    _set_users(mock_db, MEMBROS)
    async def fake_batch(emails, subject, html):
        return {"sent": len(emails), "failed": 0, "errors": []}
    monkeypatch.setattr(comunicados_service, "send_comunicado_batch", fake_batch)
    res = await comunicados_service.dispatch_comunicado("c1")
    assert res["status"] == "enviado"
    assert res["inapp_created"] == 3      # u1,u2,u3 (technical fora)
    assert res["email_sent"] == 1         # só u1 (informativo: u2 opt-out, u3 sem email)
    mock_db.comunicados.update_one.assert_awaited()


@pytest.mark.asyncio
async def test_dispatch_partial_when_some_email_fail(mock_db, monkeypatch):
    mock_db.comunicados.find_one.return_value = _doc(tipo="oficial")
    _set_users(mock_db, MEMBROS)
    async def fake_batch(emails, subject, html):
        return {"sent": 1, "failed": 1, "errors": ["x"]}
    monkeypatch.setattr(comunicados_service, "send_comunicado_batch", fake_batch)
    res = await comunicados_service.dispatch_comunicado("c1")
    assert res["status"] == "parcial"
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_comunicados_service.py -k dispatch -v`
Expected: FAIL com `AttributeError: module 'comunicados_service' has no attribute 'dispatch_comunicado'`.

- [ ] **Step 3: Implement `dispatch_comunicado`**

No topo de `backend/comunicados_service.py` (agora que as funções já existem no `email_service`), acrescentar o import:
```python
from email_service import comunicado_email_html, send_comunicado_batch
```
Depois, acrescentar a função:
```python
async def dispatch_comunicado(comunicado_id: str) -> dict:
    """Fan-out de um comunicado em `a_enviar`. Idempotente: só corre uma vez
    (transição a_enviar→enviando). Nunca rebenta — falhas viram estado."""
    doc = await db.comunicados.find_one({"id": comunicado_id}, {"_id": 0})
    if not doc or doc.get("status") != "a_enviar":
        return {"skipped": True}
    await db.comunicados.update_one({"id": comunicado_id}, {"$set": {"status": "enviando"}})

    channels = doc.get("channels", [])
    tipo = doc.get("tipo", "informativo")
    segment = doc.get("segment", {})
    inapp_created = email_sent = email_failed = 0
    error = None
    try:
        if "in_app" in channels:
            recips = await resolve_recipients(segment, channel="in_app", tipo=tipo)
            ids = [u["id"] for u in recips]
            if ids:
                await notify_users(
                    ids, type=doc.get("notification_type", "comunicado"),
                    title=doc["subject"], message=(doc.get("body") or "")[:280],
                    link=doc.get("cta_url"),
                )
                inapp_created = len(ids)
        if "email" in channels:
            recips = await resolve_recipients(segment, channel="email", tipo=tipo)
            emails = [u["email"] for u in recips]
            if emails:
                html = comunicado_email_html(
                    doc["subject"], doc.get("body") or "",
                    doc.get("cta_label"), doc.get("cta_url"), tipo=tipo,
                )
                res = await send_comunicado_batch(emails, doc["subject"], html)
                email_sent = res.get("sent", 0)
                email_failed = res.get("failed", 0)
        if "email" in channels and email_failed and not email_sent:
            status = "falhado"
        elif email_failed:
            status = "parcial"
        else:
            status = "enviado"
    except Exception as e:  # noqa: BLE001 — falha de envio nunca propaga
        logger.exception("dispatch_comunicado %s falhou", comunicado_id)
        status = "falhado"
        error = str(e)

    total = max(inapp_created, email_sent + email_failed)
    await db.comunicados.update_one({"id": comunicado_id}, {"$set": {
        "status": status,
        "inapp_created": inapp_created,
        "email_sent": email_sent,
        "email_failed": email_failed,
        "recipients_total": total,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "error": error,
    }})
    return {"status": status, "inapp_created": inapp_created,
            "email_sent": email_sent, "email_failed": email_failed}
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && pytest tests/test_comunicados_service.py -v`
Expected: PASS (todos).

- [ ] **Step 5: Commit**
```bash
git add backend/comunicados_service.py backend/tests/test_comunicados_service.py
git commit -m "feat(comunicados): F1 dispatch_comunicado (fan-out + estados/contagens)"
```

---

### Task 7: `dispatch_oficial_auto` (base para F3, com anti-duplicado)

**Files:**
- Modify: `backend/comunicados_service.py`
- Test: `backend/tests/test_comunicados_service.py` (acrescentar)

- [ ] **Step 1: Write the failing tests**
```python
@pytest.mark.asyncio
async def test_oficial_auto_creates_when_absent(mock_db, monkeypatch):
    mock_db.comunicados.find_one.return_value = None
    captured = {}
    async def fake_dispatch(cid):
        captured["cid"] = cid
        return {"status": "enviado"}
    monkeypatch.setattr(comunicados_service, "dispatch_comunicado", fake_dispatch)
    cid = await comunicados_service.dispatch_oficial_auto(
        subject="Convocatória", body="corpo longo", source_kind="assembleia_convocatoria", ref_id="a1")
    assert cid is not None
    mock_db.comunicados.insert_one.assert_awaited()
    assert captured["cid"] == cid


@pytest.mark.asyncio
async def test_oficial_auto_skips_when_duplicate(mock_db, monkeypatch):
    mock_db.comunicados.find_one.return_value = {"id": "existente"}
    monkeypatch.setattr(comunicados_service, "dispatch_comunicado",
                        AsyncMock(side_effect=AssertionError("não deve disparar")))
    cid = await comunicados_service.dispatch_oficial_auto(
        subject="X", body="corpo longo", source_kind="assembleia_convocatoria", ref_id="a1")
    assert cid is None
    mock_db.comunicados.insert_one.assert_not_awaited()
```
(Acrescentar `from unittest.mock import AsyncMock` ao topo do ficheiro de teste, se ainda não estiver.)

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_comunicados_service.py -k oficial_auto -v`
Expected: FAIL (`has no attribute 'dispatch_oficial_auto'`).

- [ ] **Step 3: Implement**

Acrescentar a `backend/comunicados_service.py`:
```python
async def dispatch_oficial_auto(*, subject: str, body: str, cta_label: str = None,
                                cta_url: str = None, source_kind: str,
                                ref_id: str) -> Optional[str]:
    """Cria e dispara um comunicado OFICIAL (in-app + email, todos os activos),
    a partir de um gatilho de governança. Anti-duplicado por (source_kind,
    source_ref_id). Devolve o id criado, ou None se já existia."""
    existing = await db.comunicados.find_one(
        {"source_kind": source_kind, "source_ref_id": ref_id}, {"_id": 0, "id": 1})
    if existing:
        return None
    cid = str(uuid.uuid4())
    doc = {
        "id": cid, "subject": subject, "body": body,
        "cta_label": cta_label, "cta_url": cta_url,
        "tipo": "oficial", "channels": ["in_app", "email"],
        "segment": {"kind": "all_active", "value": None, "user_ids": None},
        "notification_type": "comunicado", "status": "a_enviar",
        "recipients_total": 0, "inapp_created": 0, "email_sent": 0, "email_failed": 0,
        "source_kind": source_kind, "source_ref_id": ref_id,
        "created_by": "system",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sent_at": None, "error": None,
    }
    await db.comunicados.insert_one(doc)
    await dispatch_comunicado(cid)
    return cid
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && pytest tests/test_comunicados_service.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add backend/comunicados_service.py backend/tests/test_comunicados_service.py
git commit -m "feat(comunicados): F1 dispatch_oficial_auto + anti-duplicado"
```

---

### Task 8: Endpoints REST (`routes/comunicados.py`) + registo

**Files:**
- Create: `backend/routes/comunicados.py`
- Modify: `backend/routes/__init__.py` (L30 import; L62 include)
- Test: `backend/tests/test_comunicados_routes.py`

- [ ] **Step 1: Write the failing tests**

Criar `backend/tests/test_comunicados_routes.py`:
```python
import pytest
from fastapi import BackgroundTasks
from starlette.requests import Request
import routes.comunicados as cmod


def _req():
    return Request({"type": "http", "headers": [], "method": "POST",
                    "path": "/api/comunicados", "query_string": b"", "client": ("test", 0)})


@pytest.fixture(autouse=True)
def _no_limit(monkeypatch):
    monkeypatch.setattr(cmod.limiter, "enabled", False)


def _payload(**over):
    base = dict(subject="Aviso", body="corpo longo o suficiente",
                tipo="informativo", channels=["in_app"], segment={"kind": "all_active"})
    base.update(over)
    return base


@pytest.mark.asyncio
async def test_create_forbidden_for_socio(mock_db, socio_user):
    from models import ComunicadoCreate
    with pytest.raises(Exception) as ei:
        await cmod.create_comunicado(_req(), ComunicadoCreate(**_payload()),
                                     BackgroundTasks(), current_user=socio_user)
    assert getattr(ei.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_create_admin_schedules_and_audits(mock_db, admin_user, monkeypatch):
    from models import ComunicadoCreate
    mock_db.users.find.return_value.to_list.return_value = [
        {"id": "u1", "email": "u1@x.cv", "role": "socio", "account_type": "member",
         "member_category": "ordinario"},
    ]
    bt = BackgroundTasks()
    res = await cmod.create_comunicado(_req(), ComunicadoCreate(**_payload()),
                                       bt, current_user=admin_user)
    assert res["status"] == "a_enviar"
    assert res["recipients_total"] == 1
    mock_db.comunicados.insert_one.assert_awaited()
    mock_db.audit_logs.insert_one.assert_awaited()
    assert len(bt.tasks) == 1                      # dispatch agendado


@pytest.mark.asyncio
async def test_email_preferences_updates_self(mock_db, socio_user):
    from models import EmailPreferencesUpdate
    res = await cmod.update_email_preferences(
        EmailPreferencesUpdate(email_opt_out_informativos=True), current_user=socio_user)
    assert res["email_opt_out_informativos"] is True
    mock_db.users.update_one.assert_awaited()
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_comunicados_routes.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'routes.comunicados'`.

- [ ] **Step 3: Create the route module**

Criar `backend/routes/comunicados.py`:
```python
import uuid
from datetime import datetime, timezone
from collections import Counter

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from models import User, ComunicadoCreate, RecipientsCountRequest, EmailPreferencesUpdate
from database import db
from auth import get_current_user, has_role_or_privilege
from helpers import create_audit_log, members_of_orgao
import comunicados_service

router = APIRouter(tags=["comunicados"])
limiter = Limiter(key_func=get_remote_address)


def _can_send(user: User) -> bool:
    return has_role_or_privilege(user, ("admin",), "send_comunicados")


def _guard(user: User):
    if not _can_send(user):
        raise HTTPException(status_code=403, detail="Sem permissão")


# --- rotas estáticas ANTES de /comunicados/{id} (ordem importa no FastAPI) ---

@router.post("/comunicados/recipients/count")
async def count_recipients(payload: RecipientsCountRequest,
                           current_user: User = Depends(get_current_user)):
    _guard(current_user)
    seg = payload.segment.model_dump()
    inapp = (await comunicados_service.resolve_recipients(seg, channel="in_app", tipo=payload.tipo)
             if "in_app" in payload.channels else [])
    email = (await comunicados_service.resolve_recipients(seg, channel="email", tipo=payload.tipo)
             if "email" in payload.channels else [])
    return {"in_app": len(inapp), "email": len(email)}


@router.get("/comunicados/segments")
async def comunicado_segments(current_user: User = Depends(get_current_user)):
    _guard(current_user)
    members = await comunicados_service._base_members()
    roles = Counter(u.get("role") for u in members)
    cats = Counter(u.get("member_category") for u in members)
    orgaos = {}
    for o in ("mesa_ag", "direcao", "conselho_fiscal"):
        orgaos[o] = len(await members_of_orgao(o))
    return {
        "all_active": len(members),
        "roles": dict(roles),
        "member_categories": dict(cats),
        "orgaos": orgaos,
    }


@router.patch("/me/email-preferences")
async def update_email_preferences(payload: EmailPreferencesUpdate,
                                   current_user: User = Depends(get_current_user)):
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"email_opt_out_informativos": payload.email_opt_out_informativos}},
    )
    return {"email_opt_out_informativos": payload.email_opt_out_informativos}


@router.post("/comunicados")
@limiter.limit("10/minute")
async def create_comunicado(request: Request, payload: ComunicadoCreate,
                            background_tasks: BackgroundTasks,
                            current_user: User = Depends(get_current_user)):
    _guard(current_user)
    seg = payload.segment.model_dump()
    ids = set()
    for ch in payload.channels:
        recips = await comunicados_service.resolve_recipients(seg, channel=ch, tipo=payload.tipo)
        ids.update(u["id"] for u in recips)
    cid = str(uuid.uuid4())
    doc = {
        "id": cid, "subject": payload.subject, "body": payload.body,
        "cta_label": payload.cta_label, "cta_url": payload.cta_url,
        "tipo": payload.tipo, "channels": payload.channels, "segment": seg,
        "notification_type": payload.notification_type, "status": "a_enviar",
        "recipients_total": len(ids), "inapp_created": 0, "email_sent": 0, "email_failed": 0,
        "source_kind": None, "source_ref_id": None,
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sent_at": None, "error": None,
    }
    await db.comunicados.insert_one(doc)
    await create_audit_log(
        current_user.id, "enviar_comunicado", cid, request=request,
        details={"tipo": payload.tipo, "channels": payload.channels,
                 "segment": seg, "recipients_total": len(ids)},
    )
    background_tasks.add_task(comunicados_service.dispatch_comunicado, cid)
    return {"id": cid, "status": "a_enviar", "recipients_total": len(ids)}


@router.get("/comunicados")
async def list_comunicados(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                           current_user: User = Depends(get_current_user)):
    _guard(current_user)
    total = await db.comunicados.count_documents({})
    items = (await db.comunicados.find({}, {"_id": 0}).sort("created_at", -1)
             .skip(skip).limit(limit).to_list(limit))
    return {"items": items, "total": total}


@router.get("/comunicados/{comunicado_id}")
async def get_comunicado(comunicado_id: str, current_user: User = Depends(get_current_user)):
    _guard(current_user)
    doc = await db.comunicados.find_one({"id": comunicado_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Comunicado não encontrado")
    return doc
```

- [ ] **Step 4: Register the router**

Em `backend/routes/__init__.py`: após a linha L30 (`from routes.prestacao_contas import router as prestacao_contas_router`), acrescentar:
```python
from routes.comunicados import router as comunicados_router
```
E após L62 (`api_router.include_router(prestacao_contas_router)`), acrescentar:
```python
api_router.include_router(comunicados_router)
```

- [ ] **Step 5: Run to verify it passes**

Run: `cd backend && pytest tests/test_comunicados_routes.py -v`
Expected: PASS (4 testes).

- [ ] **Step 6: Run full backend suite for the feature + lint**

Run: `cd backend && pytest tests/test_comunicados_service.py tests/test_comunicados_routes.py tests/test_email_comunicado.py -v && ruff check comunicados_service.py routes/comunicados.py`
Expected: PASS + sem erros de lint.

- [ ] **Step 7: Commit**
```bash
git add backend/routes/comunicados.py backend/routes/__init__.py backend/tests/test_comunicados_routes.py
git commit -m "feat(comunicados): F1 endpoints REST (criar/listar/contar/segmentos/prefs) + registo"
```

---

# FASE F2 — Frontend manual (compositor + histórico + opt-out)

> Seguir o skill **frontend-design** (neutro; Carmesim como acento único; ≤1 botão primário por vista — aqui o botão **Disparar**; sem dark mode; shadcn/ui New York). Sem testes unitários de UI no projeto — a verificação é `eslint` + smoke manual.

### Task 9: Grupo de API no frontend

**Files:**
- Modify: `frontend/src/utils/api.js`

- [ ] **Step 1: Acrescentar o grupo `comunicadosAPI`**

Junto dos outros grupos `export const xAPI = {...}` em `frontend/src/utils/api.js`:
```javascript
export const comunicadosAPI = {
  list: (params) => api.get('/comunicados', { params }),
  get: (id) => api.get(`/comunicados/${id}`),
  create: (data) => api.post('/comunicados', data),
  recipientsCount: (data) => api.post('/comunicados/recipients/count', data),
  segments: () => api.get('/comunicados/segments'),
  updateEmailPreferences: (data) => api.patch('/me/email-preferences', data),
};
```

- [ ] **Step 2: Lint**

Run: `cd frontend && npx eslint src/utils/api.js --max-warnings=60`
Expected: sem erros.

- [ ] **Step 3: Commit**
```bash
git add frontend/src/utils/api.js
git commit -m "feat(comunicados): F2 grupo comunicadosAPI no api.js"
```

---

### Task 10: Página de admin — compositor + histórico

**Files:**
- Create: `frontend/src/pages/private/AdminComunicadosPage.js`

- [ ] **Step 1: Criar a página** (esqueleto a completar seguindo o frontend-design e o padrão das outras `Admin*Page.js`)

`frontend/src/pages/private/AdminComunicadosPage.js`, com:
- `export function AdminComunicadosPage()` (named export — padrão do App.js).
- Estado: `subject, body, tipo ('informativo'|'oficial'), channels ({in_app:true,email:false}), segmentKind, segmentValue, selectedUserIds, ctaLabel, ctaUrl, counts, history, loading, sending`.
- `useEffect` inicial: `comunicadosAPI.segments()` (para popular contagens/opções de segmento) e `comunicadosAPI.list()` (histórico).
- **Contagem viva**: ao mudar `tipo/channels/segment`, `comunicadosAPI.recipientsCount({tipo, channels: activeChannels, segment})` (debounce ~400ms) → mostrar "Vai para N in-app · M email".
- **Seleção manual**: quando `segmentKind === 'manual'`, mostrar um seletor de sócios (reutilizar o padrão de seleção de utilizadores de `AdminCargosPage`/`AdminUsuariosPage`); guardar ids em `selectedUserIds`.
- **Pré-visualização**: card que mostra assunto + corpo formatado + botão CTA (se preenchido), com os tokens da marca.
- **Disparar** (único botão primário Carmesim): valida no cliente, confirma ("Vai enviar a N destinatários"), chama `comunicadosAPI.create({subject, body, tipo, channels: activeChannels, segment: {kind, value, user_ids}, cta_label, cta_url})`; em sucesso, toast + refresca `history`.
- **Histórico**: tabela (assunto · tipo · canais · segmento · estado · enviados/falhados · data) ordenada desc, com paginação simples via `skip/limit`. Badges de estado neutros (Carmesim só em `falhado`).
- Estados de loading/empty/erro coerentes com as outras páginas.

Construir com primitivos `shadcn/ui` já no projeto (`Card`, `Button`, `Input`, `Textarea`, `Select`, `Badge`, `Table`, `Switch`/`Checkbox`, `useToast`). Texto em PT-PT.

- [ ] **Step 2: Lint**

Run: `cd frontend && npx eslint src/pages/private/AdminComunicadosPage.js --max-warnings=60`
Expected: sem erros.

- [ ] **Step 3: Commit**
```bash
git add frontend/src/pages/private/AdminComunicadosPage.js
git commit -m "feat(comunicados): F2 pagina AdminComunicados (compositor + historico)"
```

---

### Task 11: Rota + entrada na sidebar (gated)

**Files:**
- Modify: `frontend/src/App.js` (lazy import junto de L51; `<Route>` no bloco privado)
- Modify: `frontend/src/layouts/PrivateLayout.js` (nav)

- [ ] **Step 1: Lazy import + rota**

Em `App.js`, junto dos outros lazy imports de páginas admin (ex.: a seguir a `AdminLogsPage`, L51):
```javascript
const AdminComunicadosPage = lazy(() => import('./pages/private/AdminComunicadosPage').then((m) => ({ default: m.AdminComunicadosPage })));
```
No bloco de rotas privadas (junto das outras rotas `admin/*` dentro do `PrivateLayout`), acrescentar:
```jsx
<Route path="admin/comunicados" element={<AdminComunicadosPage />} />
```
(Confirmar o prefixo exacto das rotas admin vizinhas — ex.: `admin/logs` — e seguir o mesmo.)

- [ ] **Step 2: Entrada na sidebar (gated)**

Em `PrivateLayout.js`, junto das entradas admin (ex.: "Logs", "Pedidos de inscrição"), acrescentar uma entrada "Comunicados" → `/admin/comunicados`, visível quando `user.role === 'admin'` **OU** `user.privileges?.includes('send_comunicados')`. Reutilizar o helper/condição de gating já usado para as outras entradas admin (seguir o padrão local de `hasPrivilege`/checagem de role). Ícone coerente (ex.: `Megaphone`/`Send` do lucide-react já em uso).

- [ ] **Step 3: Lint + build smoke**

Run: `cd frontend && npx eslint src/App.js src/layouts/PrivateLayout.js --max-warnings=60`
Expected: sem erros. (Opcional: `yarn build` para confirmar que compila.)

- [ ] **Step 4: Commit**
```bash
git add frontend/src/App.js frontend/src/layouts/PrivateLayout.js
git commit -m "feat(comunicados): F2 rota admin/comunicados + entrada sidebar (gated)"
```

---

### Task 12: Toggle de opt-out no perfil do sócio

**Files:**
- Modify: `frontend/src/pages/private/PerfilPage.js`

- [ ] **Step 1: Acrescentar a preferência**

Numa secção "Preferências de email" em `PerfilPage.js`, um toggle (`Switch`) "Receber comunicados informativos por email", inicializado a partir de `!user.email_opt_out_informativos` (default ligado). Ao alternar, chamar `comunicadosAPI.updateEmailPreferences({ email_opt_out_informativos: !checked })` e refrescar o utilizador (`getMe`/contexto). Nota informativa: "Os comunicados oficiais (convocatórias, deliberações) chegam sempre." Importar `comunicadosAPI` de `../../utils/api`.

- [ ] **Step 2: Lint**

Run: `cd frontend && npx eslint src/pages/private/PerfilPage.js --max-warnings=60`
Expected: sem erros.

- [ ] **Step 3: Commit**
```bash
git add frontend/src/pages/private/PerfilPage.js
git commit -m "feat(comunicados): F2 toggle de opt-out de informativos no perfil"
```

---

# FASE F3 — Automático (gatilhos de governança oficial)

> Reusa `comunicados_service.dispatch_oficial_auto` (Task 7). Cada gatilho agenda em `BackgroundTasks` para **não bloquear** a ação de governança; falha de email nunca quebra a publicação. `tipo=oficial` ⇒ chega a todos (ignora opt-out).

### Task 13: Gatilho — convocatória de AG

**Files:**
- Modify: `backend/routes/assembleias.py` (`create_assembleia`, L82-138; já chama `notify_all_active_users` em L130)
- Test: `backend/tests/test_comunicados_auto.py`

- [ ] **Step 1: Write the failing test**

Criar `backend/tests/test_comunicados_auto.py`:
```python
import pytest
from fastapi import BackgroundTasks
from starlette.requests import Request
import comunicados_service


def _req():
    return Request({"type": "http", "headers": [], "method": "POST",
                    "path": "/api/assembleias", "query_string": b"", "client": ("t", 0)})


@pytest.mark.asyncio
async def test_create_assembleia_schedules_oficial_comunicado(mock_db, admin_user, monkeypatch):
    import routes.assembleias as amod
    from models import AssembleiaCreate
    # campos mínimos válidos — ajustar aos exigidos por AssembleiaCreate
    data = AssembleiaCreate(tipo="ordinaria", titulo="AG Ordinária 2026",
                            data="2026-06-30T10:00:00+00:00")
    bt = BackgroundTasks()
    await amod.create_assembleia(_req(), data, bt, current_user=admin_user)
    # o agendamento do comunicado oficial tem de estar entre as tasks
    assert any(t.func is comunicados_service.dispatch_oficial_auto for t in bt.tasks)
```
(Ajustar os campos de `AssembleiaCreate` aos realmente obrigatórios — abrir `models.py`/`routes/assembleias.py` para confirmar.)

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_comunicados_auto.py -k assembleia -v`
Expected: FAIL — a função ainda não aceita `BackgroundTasks` nem agenda o comunicado.

- [ ] **Step 3: Wire the trigger**

Em `backend/routes/assembleias.py`:
1. Topo: `import comunicados_service` e `from fastapi import BackgroundTasks` (juntar ao import de fastapi existente).
2. Assinatura de `create_assembleia` — acrescentar o parâmetro `background_tasks: BackgroundTasks` (a seguir a `data`):
   ```python
   async def create_assembleia(request: Request, data: AssembleiaCreate,
                               background_tasks: BackgroundTasks,
                               current_user: User = Depends(get_current_user)):
   ```
3. A seguir ao bloco `await notify_all_active_users(...)` (~L130), antes do `return`, agendar:
   ```python
   background_tasks.add_task(
       comunicados_service.dispatch_oficial_auto,
       subject=f"Convocatória — {doc['titulo']}",
       body=(f"Fica convocada a {doc['titulo']}.\n\n"
             f"Data: {doc.get('data', '')}\n"
             "Consulte a convocatória e a ordem de trabalhos no Portal ACCTA."),
       cta_label="Ver convocatória",
       cta_url=f"/assembleias/{doc['id']}",
       source_kind="assembleia_convocatoria",
       ref_id=doc["id"],
   )
   ```
   (Ajustar `doc['titulo']`/`doc['id']`/`doc['data']` aos nomes reais das chaves do documento inserido nesta função.)

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && pytest tests/test_comunicados_auto.py -k assembleia -v`
Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add backend/routes/assembleias.py backend/tests/test_comunicados_auto.py
git commit -m "feat(comunicados): F3 convocatoria de AG dispara comunicado oficial"
```

---

### Task 14: Gatilho — abertura de votação (eleição)

**Files:**
- Modify: `backend/routes/eleicoes.py` (`abrir_votacao`, L270-281)
- Test: `backend/tests/test_comunicados_auto.py` (acrescentar)

- [ ] **Step 1: Write the failing test**
```python
@pytest.mark.asyncio
async def test_abrir_votacao_schedules_oficial_comunicado(mock_db, admin_user, monkeypatch):
    import routes.eleicoes as emod
    mock_db.eleicoes.find_one.return_value = {
        "id": "e1", "status": "candidaturas", "titulo": "Eleições da Direcção 2026"}
    # _get_eleicao usa find_one; estado tem de permitir abrir votação
    bt = BackgroundTasks()
    req = Request({"type": "http", "headers": [], "method": "POST",
                   "path": "/api/eleicoes/e1/abrir-votacao", "query_string": b"", "client": ("t", 0)})
    await emod.abrir_votacao("e1", req, bt, current_user=admin_user)
    assert any(t.func is comunicados_service.dispatch_oficial_auto for t in bt.tasks)
```
(Confirmar em `eleicoes.py` qual o `status` que permite abrir votação — ajustar o `find_one.return_value` em conformidade.)

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_comunicados_auto.py -k abrir_votacao -v`
Expected: FAIL.

- [ ] **Step 3: Wire the trigger**

Em `backend/routes/eleicoes.py`:
1. Topo: `import comunicados_service` e `from fastapi import BackgroundTasks`.
2. Assinatura de `abrir_votacao` — acrescentar `background_tasks: BackgroundTasks`:
   ```python
   async def abrir_votacao(eleicao_id: str, request: Request,
                           background_tasks: BackgroundTasks,
                           current_user: User = Depends(get_current_user)):
   ```
3. A seguir ao `await create_audit_log(... "eleicao_votacao_aberta" ...)` (~L280), antes do `return`:
   ```python
   background_tasks.add_task(
       comunicados_service.dispatch_oficial_auto,
       subject=f"Abertura de votação — {eleicao.get('titulo', 'Eleições')}",
       body=("A votação está aberta. A sua participação é importante.\n\n"
             "Aceda ao Portal ACCTA para votar dentro do prazo."),
       cta_label="Votar agora",
       cta_url=f"/eleicoes/{eleicao_id}",
       source_kind="eleicao_abertura",
       ref_id=eleicao_id,
   )
   ```
   (`eleicao` é o doc devolvido por `_get_eleicao`/`find_one` no início da função; usar a chave real do título.)

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && pytest tests/test_comunicados_auto.py -k abrir_votacao -v`
Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add backend/routes/eleicoes.py backend/tests/test_comunicados_auto.py
git commit -m "feat(comunicados): F3 abertura de votacao dispara comunicado oficial"
```

---

### Task 15: Gatilho — publicação de deliberação/ata

**Files:**
- Modify: `backend/routes/assembleias.py` (`register_deliberacao`, L263-329; insere em L318)
- Test: `backend/tests/test_comunicados_auto.py` (acrescentar)

- [ ] **Step 1: Write the failing test**
```python
@pytest.mark.asyncio
async def test_register_deliberacao_schedules_oficial_comunicado(mock_db, admin_user, monkeypatch):
    import routes.assembleias as amod
    from models import DeliberacaoCreate  # ajustar ao nome real do modelo do body
    mock_db.assembleias.find_one.return_value = {"id": "a1", "titulo": "AG Ordinária", "data": "2026-06-30"}
    bt = BackgroundTasks()
    req = Request({"type": "http", "headers": [], "method": "POST",
                   "path": "/api/assembleias/a1/deliberacoes", "query_string": b"", "client": ("t", 0)})
    data = DeliberacaoCreate(titulo="Aprovação das contas", texto="…", resultado="aprovada")
    await amod.register_deliberacao("a1", req, data, bt, current_user=admin_user)
    assert any(t.func is comunicados_service.dispatch_oficial_auto for t in bt.tasks)
```
(Abrir `register_deliberacao` em `assembleias.py` para confirmar o nome/forma do modelo do body e os campos obrigatórios; ajustar.)

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_comunicados_auto.py -k deliberacao -v`
Expected: FAIL.

- [ ] **Step 3: Wire the trigger**

Em `register_deliberacao` (`assembleias.py`): acrescentar `background_tasks: BackgroundTasks` à assinatura e, após `await db.assembleia_deliberacoes.insert_one(doc)` (~L318), agendar:
```python
background_tasks.add_task(
    comunicados_service.dispatch_oficial_auto,
    subject=f"Deliberações — {assembleia.get('titulo', 'Assembleia Geral')}",
    body=("Foram publicadas novas deliberações da Assembleia Geral.\n\n"
          "Consulte o detalhe e a ata no Portal ACCTA."),
    cta_label="Ver deliberações",
    cta_url=f"/assembleias/{assembleia_id}",
    source_kind="assembleia_deliberacao",
    ref_id=doc["id"],
)
```
(`assembleia` é o doc da assembleia carregado na função; `doc` é a deliberação inserida — usar `ref_id=doc["id"]` para que cada deliberação dispare o seu comunicado; confirmar nomes das variáveis reais.)

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && pytest tests/test_comunicados_auto.py -v`
Expected: PASS (3 gatilhos).

- [ ] **Step 5: Commit**
```bash
git add backend/routes/assembleias.py backend/tests/test_comunicados_auto.py
git commit -m "feat(comunicados): F3 publicacao de deliberacao dispara comunicado oficial"
```

---

# Fecho

### Task 16: Suite completa + lint + revisão final

- [ ] **Step 1: Backend**

Run: `cd backend && pytest tests/test_comunicados_service.py tests/test_comunicados_routes.py tests/test_email_comunicado.py tests/test_comunicados_auto.py -v && ruff check comunicados_service.py routes/comunicados.py routes/assembleias.py routes/eleicoes.py`
Expected: tudo PASS, sem erros de lint.

- [ ] **Step 2: Sanidade de import da app**

Run: `cd backend && python -c "import routes; print('routes ok')"`
Expected: `routes ok` (router de comunicados regista sem erro de import).

- [ ] **Step 3: Frontend lint**

Run: `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60`
Expected: sem erros.

- [ ] **Step 4: Atualizar a spec como concluída**

Acrescentar uma nota de estado no topo de `tasks/spec-comunicados-email.md` ("F0–F3 implementadas") e (se aplicável) renomear/registar conforme a convenção `-concluido` do projeto.

- [ ] **Step 5: Commit final**
```bash
git add -A
git commit -m "chore(comunicados): fecho F0-F3 (suite verde, lint, spec atualizada)"
```

---

## Notas de implementação (gotchas verificados)

- **Ordem das rotas**: `/comunicados/recipients/count`, `/comunicados/segments` e `/me/email-preferences` são definidas **antes** de `/comunicados/{comunicado_id}` para o `{id}` não capturar paths estáticos.
- **slowapi em testes**: `monkeypatch.setattr(routes.comunicados.limiter, "enabled", False)` e passar uma `starlette.requests.Request` real (a fixture `_no_limit` já o faz).
- **conftest não pré-liga `comunicados`** por omissão — Task 3 adiciona-o à tuple e faz `monkeypatch.setattr(comunicados_service, "db", fake_db)` (o módulo faz `from database import db` no topo).
- **Consultas ao DAO não suportam paths com ponto** (`source.kind`) → guardam-se campos **planos** `source_kind`/`source_ref_id` (o índice e o anti-duplicado dependem disto).
- **Privacidade**: `send_comunicado_batch` envia **um `to` por destinatário** — nunca To/CC partilhado.
- **STOP-condition**: nenhum test toca emails reais (Resend é mockado/`RESEND_API_KEY` ausente). Antes de enviar a sócios reais em produção, confirmar com o dono.
- **`has_role_or_privilege(user, ("admin",), "send_comunicados")`** — mesma assinatura usada para `view_audit_logs` em `routes/notifications.py`.
- **`AssembleiaCreate`/`DeliberacaoCreate`/`EleicaoCreate`**: confirmar os campos obrigatórios reais ao escrever os testes de F3 (os exemplos são indicativos).
