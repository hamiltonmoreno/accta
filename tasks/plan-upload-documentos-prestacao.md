# Upload de documentos nos diálogos de Prestação de Contas — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir o campo de texto manual de `document_id` nos diálogos de prestação de contas por um uploader in-dialog, suportado por um endpoint dedicado que faz upload + cria o registo `documents` numa só chamada, autorizado pelos atores de prestação (Direção/Tesoureiro/CF).

**Architecture:** Backend — extrair a validação/gravação de upload para `save_validated_upload` (reuso); novo `POST /prestacao-contas/documentos` (multipart) gated por `can_upload_prestacao_document`, com política `kind → (visibilidade, título)` server-side, que grava o ficheiro e cria o `Document` (rollback do ficheiro se a criação falhar). Frontend — componente reutilizável `DocumentUploadField` + grupo `prestacaoContasAPI.uploadDocumento`, ligado aos diálogos.

**Tech Stack:** FastAPI + asyncpg DAO, Pydantic v2, pytest; React 19 + shadcn/ui + Tailwind + TanStack Query.

**Spec:** `tasks/spec-upload-documentos-prestacao.md` (mesmo ramo).

**Convenções** (CLAUDE.md / `.claude/rules`): RBAC em cada endpoint; `create_audit_log` em cada escrita; datas ISO-8601; IDs `str(uuid4())`; sem SQL cru; `frontend-design` (neutro, ≤1 botão primário/vista, sem dark mode); PT-PT; `eslint` limpo.

---

## File Structure

| Ficheiro | Responsabilidade | Ação |
|---|---|---|
| `backend/routes/upload.py` | Extrair `save_validated_upload(category, contents, filename)` | Modificar |
| `backend/routes/prestacao_contas.py` | Helper RBAC + política + endpoint `/prestacao-contas/documentos` | Modificar |
| `backend/tests/test_upload_prestacao_doc.py` | Testes do endpoint | **Criar** |
| `frontend/src/utils/api.js` | Grupo `prestacaoContasAPI.uploadDocumento` | Modificar |
| `frontend/src/components/DocumentUploadField.js` | Componente uploader reutilizável | **Criar** |
| `frontend/src/pages/private/financeiro/PrestacaoContasTab.js` | Ligar o uploader aos diálogos | Modificar |

---

# FASE F0 — Backend

### Task 1: Extrair `save_validated_upload` em `upload.py`

**Files:**
- Modify: `backend/routes/upload.py`
- Test: `backend/tests/test_upload_prestacao_doc.py` (criado nesta task com o teste do helper)

- [ ] **Step 1: Write the failing test**

Criar `backend/tests/test_upload_prestacao_doc.py`:
```python
import io
import pytest
import routes.upload as upmod


@pytest.mark.asyncio
async def test_save_validated_upload_rejects_oversize(monkeypatch):
    # documents: 10MB. Passar 11MB tem de levantar 413.
    big = b"x" * (11 * 1024 * 1024)
    with pytest.raises(Exception) as ei:
        await upmod.save_validated_upload("documents", big, "x.pdf")
    assert getattr(ei.value, "status_code", None) == 413


@pytest.mark.asyncio
async def test_save_validated_upload_writes_and_returns_url(monkeypatch, tmp_path):
    # Evita validação de magic-bytes e I/O real: monkeypatch dos helpers internos.
    monkeypatch.setattr(upmod, "validate_file_content", lambda *a, **k: None)
    async def _fake_to_thread(fn, *a, **k):
        return None
    monkeypatch.setattr(upmod.asyncio, "to_thread", _fake_to_thread)
    url = await upmod.save_validated_upload("documents", b"%PDF-1.4 ...", "relatorio.pdf")
    assert url.startswith("/uploads/documents/") and url.endswith(".pdf")
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && python -m pytest tests/test_upload_prestacao_doc.py -k save_validated -v`
Expected: FAIL (`AttributeError: module 'routes.upload' has no attribute 'save_validated_upload'`).

- [ ] **Step 3: Implement the helper + refactor `upload_file` to use it**

Em `backend/routes/upload.py`, adicionar a função (a seguir a `MAX_FILE_SIZES`, antes de `upload_file`):
```python
async def save_validated_upload(category: str, contents: bytes, filename: str) -> str:
    """Valida (tamanho/extensão/conteúdo) e grava um upload já lido em memória.
    Devolve o `file_url`. Levanta HTTPException em invalidação. Reutilizado pelo
    endpoint genérico `/upload/{category}` e pelo upload de documentos de
    prestação de contas. NÃO faz checagem de RBAC (o caller decide)."""
    max_size = MAX_FILE_SIZES.get(category, 5 * 1024 * 1024)
    if len(contents) > max_size:
        max_mb = max_size / (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"Arquivo excede o limite de {max_mb:.0f} MB")
    validate_file_content(contents, filename, ALLOWED_EXTENSIONS[category])
    file_ext = Path(filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    category_dir = UPLOAD_DIR / category
    await asyncio.to_thread(category_dir.mkdir, parents=True, exist_ok=True)
    await asyncio.to_thread((category_dir / unique_filename).write_bytes, contents)
    return f"/uploads/{category}/{unique_filename}"
```
Depois, refatorar `upload_file` para reutilizá-la (mantendo o comportamento e os gates de RBAC existentes). Substituir o bloco que lê/valida/grava por:
```python
    contents = await file.read()
    try:
        file_url = await save_validated_upload(category, contents, file.filename)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Falha ao guardar upload (categoria=%s)", category)
        raise HTTPException(status_code=500, detail="Erro interno ao processar o ficheiro")
    unique_filename = Path(file_url).name
    await create_audit_log(current_user.id, f"Upload de arquivo: {file.filename}", unique_filename)
    return {"filename": file.filename, "file_url": file_url, "size": len(contents), "category": category}
```
(As verificações de categoria/RBAC no topo de `upload_file` mantêm-se inalteradas.)

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && python -m pytest tests/test_upload_prestacao_doc.py -k save_validated -v`
Expected: PASS (2 testes).

- [ ] **Step 5: Sanity — endpoint genérico não regrediu**

Run: `cd backend && python -m pytest tests/ -k upload -v 2>&1 | tail -15` (corre os testes de upload existentes, se houver) e `python -c "import routes.upload"`.
Expected: sem novos erros; import ok.

- [ ] **Step 6: Commit**
```bash
git add backend/routes/upload.py backend/tests/test_upload_prestacao_doc.py
git commit -m "refactor(upload): extrair save_validated_upload reutilizavel"
```

---

### Task 2: Endpoint `POST /prestacao-contas/documentos`

**Files:**
- Modify: `backend/routes/prestacao_contas.py`
- Test: `backend/tests/test_upload_prestacao_doc.py` (acrescentar)

- [ ] **Step 1: Write the failing tests**

Acrescentar a `backend/tests/test_upload_prestacao_doc.py`:
```python
import io as _io
from starlette.datastructures import UploadFile, Headers
import routes.prestacao_contas as pmod


def _upload(filename="relatorio.pdf", data=b"%PDF-1.4 conteudo"):
    return UploadFile(filename=filename, file=_io.BytesIO(data),
                      headers=Headers({"content-type": "application/pdf"}))


@pytest.fixture(autouse=True)
def _no_real_io(monkeypatch):
    # O endpoint não deve tocar no disco nos unit tests.
    async def _fake_save(category, contents, filename):
        return f"/uploads/{category}/fake-{filename}"
    monkeypatch.setattr(pmod, "save_validated_upload", _fake_save)


@pytest.mark.asyncio
async def test_upload_doc_forbidden_for_socio(mock_db, socio_user):
    with pytest.raises(Exception) as ei:
        await pmod.upload_prestacao_documento(file=_upload(), kind="relatorio",
                                              title=None, current_user=socio_user)
    assert getattr(ei.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_upload_doc_invalid_kind(mock_db, financeiro_user):
    with pytest.raises(Exception) as ei:
        await pmod.upload_prestacao_documento(file=_upload(), kind="galaxia",
                                              title=None, current_user=financeiro_user)
    assert getattr(ei.value, "status_code", None) == 400


@pytest.mark.asyncio
async def test_upload_doc_relatorio_publico_creates_document(mock_db, financeiro_user):
    res = await pmod.upload_prestacao_documento(file=_upload(), kind="relatorio",
                                                title=None, current_user=financeiro_user)
    assert res["visibility"] == "publico"
    assert res["title"] == "Relatório e Contas"
    assert res["document_id"]
    mock_db.documents.insert_one.assert_awaited()
    mock_db.audit_logs.insert_one.assert_awaited()


@pytest.mark.asyncio
async def test_upload_doc_orcamento_socios(mock_db, financeiro_user):
    res = await pmod.upload_prestacao_documento(file=_upload(), kind="orcamento",
                                                title="Orçamento 2027", current_user=financeiro_user)
    assert res["visibility"] == "socios"
    assert res["title"] == "Orçamento 2027"   # override respeitado


@pytest.mark.asyncio
async def test_upload_doc_rollback_on_db_failure(mock_db, financeiro_user, monkeypatch):
    mock_db.documents.insert_one.side_effect = RuntimeError("db down")
    deleted = {}
    monkeypatch.setattr(pmod, "delete_upload_file", lambda url: deleted.update(url=url) or True)
    with pytest.raises(Exception) as ei:
        await pmod.upload_prestacao_documento(file=_upload(), kind="relatorio",
                                              title=None, current_user=financeiro_user)
    assert getattr(ei.value, "status_code", None) == 500
    assert deleted.get("url", "").startswith("/uploads/documents/")  # ficheiro limpo
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && python -m pytest tests/test_upload_prestacao_doc.py -k upload_doc -v`
Expected: FAIL (`AttributeError: ... has no attribute 'upload_prestacao_documento'`).

- [ ] **Step 3: Implement the endpoint**

Em `backend/routes/prestacao_contas.py`:
1. Acrescentar aos imports do topo:
```python
import logging
from fastapi import File, Form, UploadFile
from helpers import delete_upload_file
from models import Document
from routes.upload import save_validated_upload
```
e, a seguir a `router = APIRouter(...)`:
```python
logger = logging.getLogger(__name__)
```
2. Acrescentar o helper RBAC + a política + o endpoint (perto dos outros `_require_*`):
```python
def can_upload_prestacao_document(user: User) -> bool:
    """Atores que podem anexar documentos no ciclo: Direção, Tesoureiro
    (manage_finances) e Conselho Fiscal — admin já incluído em cada helper."""
    return can_manage_finances(user) or is_direcao(user) or can_emit_parecer_cf(user)


_PRESTACAO_DOC_POLICY = {
    "relatorio": ("publico", "Relatório e Contas"),
    "balancete": ("publico", "Balancete"),
    "parecer": ("publico", "Parecer do Conselho Fiscal"),
    "orcamento": ("socios", "Orçamento"),
    "plano": ("socios", "Plano de Atividades"),
}


@router.post("/prestacao-contas/documentos")
async def upload_prestacao_documento(
    file: UploadFile = File(...),
    kind: str = Form(...),
    title: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
):
    if not can_upload_prestacao_document(current_user):
        raise HTTPException(status_code=403, detail="Sem permissao para anexar documentos de prestacao de contas")
    if kind not in _PRESTACAO_DOC_POLICY:
        raise HTTPException(status_code=400, detail="Tipo de documento invalido")
    visibility, default_title = _PRESTACAO_DOC_POLICY[kind]
    final_title = (title or "").strip() or default_title

    contents = await file.read()
    file_url = await save_validated_upload("documents", contents, file.filename)
    try:
        doc = Document(title=final_title, file_url=file_url, type="prestacao_contas",
                       visibility=visibility, tags=[])
        await db.documents.insert_one(doc.model_dump())
    except Exception:
        delete_upload_file(file_url)  # rollback: sem ficheiros órfãos
        logger.exception("Falha ao registar documento de prestacao (kind=%s)", kind)
        raise HTTPException(status_code=500, detail="Erro ao registar o documento")

    await create_audit_log(
        current_user.id, "upload_documento_prestacao", doc.id,
        details={"kind": kind, "visibility": visibility, "title": final_title},
    )
    return {"document_id": doc.id, "file_url": file_url, "title": final_title, "visibility": visibility}
```
Notas: `Document` ignora campos extra, por isso `type="prestacao_contas"` (campo livre do modelo) e não há `uploaded_by` no doc — a autoria fica no audit log. `delete_upload_file` (em `helpers.py`) apaga o ficheiro `/uploads/...` com guard de path-traversal.

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && python -m pytest tests/test_upload_prestacao_doc.py -v`
Expected: PASS (todos — helper + endpoint).

- [ ] **Step 5: Lint + import sanity**

Run: `cd backend && python -m ruff check routes/prestacao_contas.py routes/upload.py && python -c "import routes"`
Expected: ruff limpo; `import routes` ok (sem ciclo — `upload` não importa `prestacao_contas`).

- [ ] **Step 6: Commit**
```bash
git add backend/routes/prestacao_contas.py backend/tests/test_upload_prestacao_doc.py
git commit -m "feat(upload-prestacao): F0 endpoint dedicado upload+criacao de documento (RBAC + politica por kind)"
```

---

# FASE F1 — Frontend

> Sem testes unitários de UI no projeto — verificação por `eslint` + smoke manual. Seguir `frontend-design` (o botão de escolher ficheiro é secundário; o único primário do diálogo continua a ser o de submeter).

### Task 3: Grupo de API `prestacaoContasAPI`

**Files:**
- Modify: `frontend/src/utils/api.js`

- [ ] **Step 1: Adicionar o grupo**

Junto de `exerciciosAPI`/`balancetesAPI` em `frontend/src/utils/api.js`:
```javascript
export const prestacaoContasAPI = {
  uploadDocumento: (file, { kind, title } = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('kind', kind);
    if (title) formData.append('title', title);
    return api.post('/prestacao-contas/documentos', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};
```

- [ ] **Step 2: Lint**

Run: `cd frontend && npx eslint src/utils/api.js --max-warnings=60`
Expected: limpo.

- [ ] **Step 3: Commit**
```bash
git add frontend/src/utils/api.js
git commit -m "feat(upload-prestacao): F1 prestacaoContasAPI.uploadDocumento"
```

---

### Task 4: Componente `DocumentUploadField`

**Files:**
- Create: `frontend/src/components/DocumentUploadField.js`

- [ ] **Step 1: Criar o componente**

`frontend/src/components/DocumentUploadField.js`:
```jsx
import React, { useRef, useState } from 'react';
import { Upload, FileCheck, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { prestacaoContasAPI } from '../utils/api';

/**
 * Campo de upload de documento para os diálogos de prestação de contas.
 * Faz upload + cria o registo `documents` no backend e devolve o document_id
 * via onChange. `kind` define visibilidade/título (política server-side).
 */
export function DocumentUploadField({ kind, value, onChange, required = false, label = 'Documento (PDF)' }) {
  const inputRef = useRef(null);
  const [fileName, setFileName] = useState('');
  const [uploading, setUploading] = useState(false);

  const handlePick = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const { data } = await prestacaoContasAPI.uploadDocumento(file, { kind });
      setFileName(file.name);
      onChange?.(data.document_id, data);
      toast.success('Documento carregado.');
    } catch (err) {
      onChange?.('', null);
      setFileName('');
      toast.error(err.response?.data?.detail || 'Falha ao carregar o documento.');
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  return (
    <div>
      <label className="block text-xs font-medium text-[#6B7280] mb-1">
        {label}{required ? ' *' : ''}
      </label>
      <input ref={inputRef} type="file" accept=".pdf,.doc,.docx" className="hidden" onChange={handlePick} data-testid={`doc-upload-${kind}`} />
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={uploading}
          className="inline-flex items-center gap-1.5 px-3 py-2 text-sm border border-[#D1D5DB] rounded-md text-grafite hover:bg-[#F5F5F5] focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 disabled:opacity-60"
        >
          {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
          {uploading ? 'A carregar…' : (value ? 'Substituir ficheiro' : 'Escolher ficheiro')}
        </button>
        {value && !uploading && (
          <span className="inline-flex items-center gap-1 text-xs text-[#6B7280]">
            <FileCheck className="h-4 w-4 text-grafite" /> {fileName || 'Documento carregado'}
          </span>
        )}
      </div>
    </div>
  );
}

export default DocumentUploadField;
```
(Confirmar que `sonner` e os ícones `lucide-react` são os usados no projeto — são, em `PerfilPage`/`PrestacaoContasTab`. Ajustar o caminho de import de `api` se o componente ficar noutra pasta.)

- [ ] **Step 2: Lint**

Run: `cd frontend && npx eslint src/components/DocumentUploadField.js --max-warnings=60`
Expected: limpo.

- [ ] **Step 3: Commit**
```bash
git add frontend/src/components/DocumentUploadField.js
git commit -m "feat(upload-prestacao): F1 componente DocumentUploadField"
```

---

### Task 5: Ligar o uploader aos diálogos

**Files:**
- Modify: `frontend/src/pages/private/financeiro/PrestacaoContasTab.js`

- [ ] **Step 1: Importar o componente**

No topo de `PrestacaoContasTab.js`:
```javascript
import { DocumentUploadField } from '../../../components/DocumentUploadField';
```
(Confirmar a profundidade relativa do caminho a partir de `pages/private/financeiro/`.)

- [ ] **Step 2: Substituir o campo de texto do relatório**

No diálogo `dialog === 'relatorio'` (hoje ~linhas 243–246), substituir o `<div>` com `<label>…</label><input type="text" … data-testid="relatorio-doc" />` por:
```jsx
            <DocumentUploadField
              kind="relatorio"
              required
              value={form.document_id}
              onChange={(id) => setForm({ ...form, document_id: id })}
              label="Relatório e Contas (PDF)"
            />
```
O `DialogActions … disabled={!form.document_id?.trim()}` mantém-se (continua a bloquear submeter sem documento).

- [ ] **Step 3: Adicionar o uploader aos diálogos de orçamento, plano, balancete e parecer**

Em cada diálogo correspondente (procurar `dialog === 'orcamento'`, `'plano'`, `'balancete'`, `'parecer'` neste ficheiro — e, se o diálogo de publicar balancete viver em `BalancetesTab.js`, ligar aí também), acrescentar, antes do `DialogActions`, um campo **opcional**:
```jsx
            <DocumentUploadField
              kind="orcamento"
              value={form.document_id}
              onChange={(id) => setForm({ ...form, document_id: id })}
              label="Documento de suporte (PDF, opcional)"
            />
```
Trocar `kind`/`label` por diálogo: `orcamento` → "Orçamento (PDF)"; `plano` → "Plano de Atividades (PDF)"; `balancete` → "Balancete (PDF)"; `parecer` → "Parecer do CF (PDF)". Garantir que o `payload`/`form` desses diálogos inclui `document_id` quando preenchido (estes são opcionais; o backend só valida se vier preenchido). Se um diálogo usa estado próprio (ex.: `linhas`/`atividades`) em vez de `form`, passar o `document_id` no payload da mutação respetiva.

- [ ] **Step 4: Lint + build smoke**

Run: `cd frontend && npx eslint src/pages/private/financeiro/PrestacaoContasTab.js --max-warnings=60`
Expected: limpo. (Opcional: `yarn build`.)

- [ ] **Step 5: Commit**
```bash
git add frontend/src/pages/private/financeiro/PrestacaoContasTab.js
git commit -m "feat(upload-prestacao): F1 ligar DocumentUploadField aos dialogos de prestacao"
```

---

# Fecho

### Task 6: Suite + lint + estado

- [ ] **Step 1: Backend**

Run: `cd backend && python -m pytest tests/test_upload_prestacao_doc.py -v && python -m ruff check routes/upload.py routes/prestacao_contas.py`
Expected: PASS + ruff limpo.

- [ ] **Step 2: Import sanity**

Run: `cd backend && python -c "import routes; print('ok')"`
Expected: `ok`.

- [ ] **Step 3: Frontend lint**

Run: `cd frontend && npx eslint src/components/DocumentUploadField.js src/utils/api.js src/pages/private/financeiro/PrestacaoContasTab.js --max-warnings=60`
Expected: limpo.

- [ ] **Step 4: Nota de estado na spec**

Acrescentar no topo de `tasks/spec-upload-documentos-prestacao.md` uma nota "F0–F1 implementadas".

- [ ] **Step 5: Commit**
```bash
git add -A
git commit -m "chore(upload-prestacao): fecho F0-F1 (suite verde, lint, spec atualizada)"
```

---

## Notas de implementação (gotchas verificados)

- **Modelo `Document`** tem `type` (string livre, obrigatório), `visibility` (∈ `{publico,socios,direcao,privado}`), `tags`, e `model_config extra="ignore"` → `uploaded_by` **não** persiste; usa-se `type="prestacao_contas"` e a autoria fica no `audit_log`.
- **Sem ciclo de import**: `routes.upload` não importa `routes.prestacao_contas`, por isso `from routes.upload import save_validated_upload` no topo de `prestacao_contas.py` é seguro.
- **Testes**: o `mock_db` já pré-liga `documents` e `audit_logs`; `prestacao_contas`/`upload` são patched pelo loop `routes.*` do conftest. Para não tocar no disco, os testes do endpoint fazem monkeypatch de `routes.prestacao_contas.save_validated_upload` (e de `delete_upload_file` no teste de rollback). `UploadFile` real de `starlette.datastructures` com `BytesIO`.
- **RBAC**: `can_upload_prestacao_document` = união dos atores; o endpoint de ação subsequente (relatorio/balancete/…) **revalida** a sua permissão e o `document_id`, por isso o gate de upload ser permissivo não dá acesso indevido.
- **Frontend**: confirmar a profundidade do import relativo (`pages/private/financeiro/` → `components/` são 3 níveis: `../../../components/...`). Verificar em que componente vive o diálogo de publicar balancete antes de ligar o `kind="balancete"`.
