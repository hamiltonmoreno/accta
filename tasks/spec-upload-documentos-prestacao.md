# Spec — Upload de documentos integrado nos diálogos de Prestação de Contas

> **Status**: rascunho técnico (2026-05-24). Spec de produto/engenharia.
> **Objetivo**: eliminar o atrito de ter de **colar um `document_id` à mão** nos
> diálogos do ciclo de prestação de contas. O admin/ator passa a **escolher o
> ficheiro no próprio diálogo**; o sistema faz upload + cria o registo `documents`
> e usa o `document_id` automaticamente.
> **Estado do sistema**: o ciclo de prestação de contas (Cat 3) está em `develop`
> (F0–F5, #109). Os endpoints aceitam `document_id` validado contra a coleção
> `documents`. Aditivo — não remove nada nem migra dados.
> **Base**: item "Aberto/futuro" do `tasks/spec-ciclo-prestacao-contas.md`
> ("upload de documentos integrado nos diálogos; hoje recebem `document_id`").

---

## 0. Âmbito

Integrar o upload de documentos diretamente nos diálogos de prestação de contas,
substituindo o campo de texto manual de `document_id` por um **uploader in-dialog**.

**Decisões confirmadas com o dono** (ver §11):

1. **UX**: substituir o campo de texto por um **uploader in-dialog** (escolher
   ficheiro → upload + criação do registo `documents` → `document_id` automático).
2. **RBAC**: **endpoint dedicado atómico**, gated pela permissão das ações de
   prestação (Direção/Tesoureiro/CF), mantendo o módulo de Documentos admin-only
   intacto e sem janela de falha parcial.
3. **Visibilidade**: **default sensato por ação** — `relatorio`/`balancete`/
   `parecer` → `publico` (transparência); `orcamento`/`plano` → `socios`. Ajustável
   depois no módulo de Documentos.

---

## 1. Specs relacionadas e dependências

- **`backend/routes/prestacao_contas.py`** (implementado, em `develop`): endpoints
  que aceitam `document_id` e validam via `_validate_document` (existe em
  `db.documents`). Mapa de ações + RBAC:

  | Endpoint | Ação | RBAC (helper) | `document_id` | Visibilidade |
  |---|---|---|---|---|
  | `POST /balancetes` | publicar balancete | `_require_manage_finances` | opcional | `publico` |
  | `POST /exercicios/{ano}/relatorio` | relatório e contas | `_require_direcao` | **obrigatório** | `publico` |
  | `POST /exercicios/{ano}/orcamento` | orçamento | `_require_direcao` | opcional | `socios` |
  | `POST /exercicios/{ano}/plano` | plano de atividades | `_require_direcao` | opcional | `socios` |
  | `POST /exercicios/{ano}/parecer` | parecer do CF | `_require_cf` | opcional | `publico` |

- **`backend/routes/upload.py`** (implementado): `POST /upload/{category}` valida
  extensão/tamanho (`validate_file_content`, `MAX_FILE_SIZES`, `ALLOWED_EXTENSIONS`)
  e guarda em `/uploads/{category}/`; a categoria `documents` é **admin-only**.
  **Reusa-se a lógica de validação/gravação**, não o gate admin-only.
- **`backend/routes/documents.py`** (implementado): cria registos `documents`
  (admin-only). O novo endpoint cria o registo **em nome** do ator de prestação,
  sem alargar o gate do módulo de Documentos.
- **`backend/auth.py`** / **`backend/permissions.py`**: `can_manage_finances`,
  `is_direcao`, `can_emit_parecer_cf` — base do novo gate.
- **Frontend** `PrestacaoContasTab.js`: hoje só o diálogo do **relatório** tem o
  campo de texto `document_id` (`<input type="text"> "ID do documento (PDF
  carregado)"`); `uploadAPI`/`documentsAPI` existem em `utils/api.js`.

---

## 2. Diagnóstico do estado actual

- O ator tem de pré-criar o documento no módulo de Documentos (admin-only),
  copiar o `id`, e colá-lo no diálogo. Para um Tesoureiro/CF **não-admin**, isto
  é impossível sem ajuda de um admin (o módulo de Documentos é admin-only).
- Não existe: endpoint que faça upload+criação atómica gated por permissão de
  prestação; componente de upload reutilizável nos diálogos; exposição do
  uploader nos diálogos de balancete/orçamento/plano/parecer (só relatório tem
  campo, e é texto manual).

---

## 3. Decisões transversais (arquitetura)

1. **Endpoint dedicado** em `prestacao_contas.py` (coeso com o domínio), em vez de
   relaxar o módulo de Documentos: cria o registo `documents` em nome do ator,
   gated pela união dos atores de prestação, deixando o módulo de Documentos
   admin-only intacto.
2. **Política por `kind` é server-side** (fonte única): o mapa
   `kind → (visibilidade, prefixo de título)` vive no backend; o frontend só passa
   o `kind` (e, opcionalmente, um `title`). Evita drift de política entre diálogos.
3. **Reuso da validação de upload**: extensão/tamanho via os mesmos helpers do
   `upload.py` (sem duplicar regras).
4. **Atómico/best-effort**: o registo `documents` só nasce depois do ficheiro
   gravado; se a criação do registo falhar, o ficheiro é apagado (sem órfãos). O
   endpoint nunca deixa estado meio-feito visível.
5. **Componente frontend reutilizável** `DocumentUploadField` — uma só
   responsabilidade (escolher ficheiro → obter `document_id`), usado por todos os
   diálogos; substitui o campo de texto e adiciona-se onde faltava.
6. **Aditivo**: nenhum endpoint existente muda contrato (continuam a aceitar
   `document_id`); datas ISO-8601; IDs `str(uuid4())`; sem SQL cru; `create_audit_log`.

---

## 4. Backend — endpoint dedicado

### 4.1 `POST /prestacao-contas/documentos` (multipart/form-data)

- **Campos**: `file: UploadFile` (obrigatório); `kind: str` (form field;
  `relatorio|balancete|orcamento|plano|parecer`); `title: Optional[str]` (override).
- **RBAC**: helper novo `can_upload_prestacao_document(user)` =
  `can_manage_finances(user) or is_direcao(user) or can_emit_parecer_cf(user)`
  (admin já incluído em cada um). 403 caso contrário, 401 sem token.
- **Validação do ficheiro**: reusa `validate_file_content(contents, filename,
  ALLOWED_EXTENSIONS["documents"])` e `MAX_FILE_SIZES["documents"]` do `upload.py`
  (extrair para reutilização sem duplicar). 400 em tipo/tamanho inválido.
- **Política por `kind`** (mapa server-side, fonte única):
  ```python
  _PRESTACAO_DOC_POLICY = {
      "relatorio": ("publico", "Relatório e Contas"),
      "balancete": ("publico", "Balancete"),
      "parecer":   ("publico", "Parecer do Conselho Fiscal"),
      "orcamento": ("socios",  "Orçamento"),
      "plano":     ("socios",  "Plano de Atividades"),
  }
  ```
  `kind` inválido → 400. `visibility = policy[kind][0]`; `title = title or
  policy[kind][1]` (acrescentar o nome do ficheiro/ano quando útil).
- **Fluxo atómico**:
  1. valida ficheiro;
  2. grava em `/uploads/documents/{uuid}.{ext}` → `file_url`;
  3. cria registo `documents` (`id`, `title`, `file_url`, `visibility`,
     `category="prestacao_contas"`, `uploaded_by=current_user.id`, `created_at`,
     campos que o modelo `documents` exige);
  4. se (3) falhar → apaga o ficheiro (`delete_upload_file`) e propaga 500;
  5. `create_audit_log(user, "upload_documento_prestacao", document_id, details)`.
- **Resposta**: `{ "document_id": str, "file_url": str, "title": str,
  "visibility": str }`.
- **Modelos** (`models.py`): não é preciso um request model (multipart usa
  `Form`/`File`); resposta pode ser dict simples ou um `PrestacaoDocumentoResponse`.

### 4.2 Refactor mínimo de `upload.py`

Extrair a validação+gravação para uma função reutilizável (ex.:
`save_validated_upload(category, file_bytes, filename) -> file_url`) usada tanto
por `upload_file` como pelo novo endpoint — sem mudar o comportamento de
`/upload/{category}`.

---

## 5. Frontend

### 5.1 Componente `DocumentUploadField` (`components/`)

- Props: `kind`, `value` (document_id atual), `onChange(documentId, meta)`,
  `required`, `label`.
- UI: input de ficheiro (botão "Escolher ficheiro") + nome do ficheiro escolhido +
  estado (a carregar / carregado ✓ / erro) + ação "substituir". Ao escolher, chama
  `prestacaoContasAPI.uploadDocumento(file, { kind, title? })`; em sucesso, guarda
  `document_id` e chama `onChange`. Erros → `toast.error(detail)`.
- Design `frontend-design`: neutro; o botão de escolher ficheiro é secundário
  (não Carmesim); o único primário do diálogo continua a ser o de submeter; focus
  rings; PT-PT.

### 5.2 `utils/api.js` + `lib/queryClient.js`

- `prestacaoContasAPI.uploadDocumento(file, { kind, title })` → `POST
  /prestacao-contas/documentos` (multipart, como `uploadAPI.uploadFile`). (Se já
  existir um grupo `prestacaoContasAPI`/`exerciciosAPI`/`balancetesAPI`, acrescentar
  aí; senão criar.)

### 5.3 Ligação aos diálogos (`PrestacaoContasTab.js`, e balancete onde estiver)

- **Relatório**: substituir o `<input type="text">` do `document_id` pelo
  `DocumentUploadField kind="relatorio" required`. Submeter desativado até haver
  `document_id`.
- **Balancete / Orçamento / Plano / Parecer**: adicionar `DocumentUploadField`
  (opcional, `kind` respetivo) onde o backend já aceita documento mas a UI não
  expunha. Confirmar em que componente vive o diálogo de publicar balancete
  (`PrestacaoContasTab.js` ou `BalancetesTab.js`) e ligar aí.

---

## 6. Erros & edge cases

- Ficheiro grande / extensão inválida → 400 do backend → `toast.error`.
- Falha de gravação do registo após upload → ficheiro apagado, 500, toast; o
  campo volta ao estado vazio.
- `kind` obrigatório e válido (o frontend passa-o sempre; backend valida).
- Relatório: `document_id` obrigatório (submeter bloqueado sem upload); restantes
  opcional.
- Substituir ficheiro: novo upload cria novo `document_id` (o anterior fica no
  módulo de Documentos; sem limpeza automática do anterior no v1).

---

## 7. Segurança & RBAC

- Gate `can_upload_prestacao_document` (Direção OU Tesoureiro/`manage_finances` OU
  CF OU admin); o módulo de Documentos mantém-se admin-only.
- O endpoint de ação subsequente (relatorio/balancete/…) **revalida** a sua própria
  permissão e o `document_id` (`_validate_document`) — o upload ser ligeiramente
  permissivo não dá acesso indevido (o documento só é usado se a ação passar).
- Validação de conteúdo do ficheiro (não só extensão) via `validate_file_content`.
- `create_audit_log` em cada upload. Datas ISO-8601; sem SQL cru.
- Sem migração destrutiva; sem emails; sem mexer em `main`.

---

## 8. Testes (`backend/tests/`)

Unit/in-process com `mock_db`:
- **RBAC**: Direção, Tesoureiro (`manage_finances`), CF (`emit_cf_parecer`), admin
  → passam; sócio sem privilégio → 403.
- **Política por `kind`**: visibilidade correta por `kind`; `kind` inválido → 400;
  título default vs override.
- **Atómico**: cria registo `documents` após gravar ficheiro; em falha da criação,
  o ficheiro é apagado (mock de `delete_upload_file`) e devolve 500.
- **Validação**: extensão/tamanho inválidos → 400 (reusa helpers de `upload.py`).
- **Resposta**: devolve `document_id` utilizável (o endpoint de ação aceita-o).
- Frontend: `eslint` limpo; verificação manual do fluxo num diálogo.

---

## 9. Faseamento

- **F0 — Backend**: refactor `save_validated_upload` em `upload.py`; helper
  `can_upload_prestacao_document`; endpoint `POST /prestacao-contas/documentos` +
  política por `kind` + audit; testes.
- **F1 — Frontend**: `DocumentUploadField` + `prestacaoContasAPI.uploadDocumento`;
  ligar ao diálogo do relatório (substituir) e aos de balancete/orçamento/plano/
  parecer (adicionar); eslint.

Cada fase é entregável e testável; F1 depende do endpoint da F0.

---

## 10. Fora de âmbito (YAGNI / futuro)

- Seletor de documento existente (reutilizar PDFs já carregados) — descartado na
  decisão de UX.
- Limpeza automática do documento anterior ao substituir.
- Drag-and-drop / multi-ficheiro / barra de progresso por bytes.
- Generalizar o uploader a outros módulos (mural, eventos) — fora deste âmbito.

---

## 11. Registo das decisões (perguntas confirmadas)

| # | Pergunta | Decisão |
|---|---|---|
| 1 | Modelo UX | Substituir o campo de texto por uploader in-dialog |
| 2 | RBAC do upload | Endpoint dedicado atómico, gated pela permissão de prestação |
| 3 | Visibilidade | Default sensato por ação (relatorio/balancete/parecer → público; orcamento/plano → sócios) |
