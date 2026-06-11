# Normalização PT-PT — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir brasileirismos por português de Portugal em todo o texto visível (site público, app privada, strings do backend e relatório-fonte), sem tocar identificadores.

**Architecture:** Edições de string cirúrgicas por superfície. Não há comportamento novo a testar (TDD clássico não se aplica): a verificação é manter `eslint`/`pytest`/`craco test` verdes e atualizar os 2 únicos asserts que dependem de strings antigas (`authSchemas.test.js`). Cada tarefa = editar uma superfície → correr lint/testes → commit.

**Tech Stack:** React 19 (CRA/craco, jest), FastAPI (pytest), Markdown.

**Glossário canónico** (ref. spec `2026-06-11-normalizacao-pt-pt-design.md`):
`conosco→connosco` · `você→impessoal` · `senha→palavra-passe` · `registro→registo` ·
`arquivo→ficheiro` · `tela→ecrã` · `contato→contacto` · `deletar→eliminar`.

**Guardrails (NUNCA tocar):** rotas (`/admin/usuarios`), nomes de componentes/variáveis (`AdminUsuariosPage`, `showPassword`, `confirmPassword`), `data-testid`, inglês técnico. **Falso positivo a preservar:** `profissional.py:689` `"Arquivou …"` = verbo *arquivar* (archive), não "ficheiro".

**Termos do glossário SEM ocorrências reais** (verificado — não criar tarefa): `tela`/`ecrã` (só falsos positivos: "Ho**tela**ria", "Tu**tela**"), `equipe`, `esporte`, `planejamento`, `gerenciar`, `gerencia`, `acessar`, `aplicativo`, `celular`. O `usuário` visível também não existe (só a rota `/admin/usuarios` e o nome `AdminUsuariosPage`, ambos a preservar; os rótulos já são "Utilizadores").

---

## Task 1: Schema de auth (fonte partilhada das mensagens) + teste

**Files:**
- Modify: `frontend/src/utils/authSchemas.js`
- Test: `frontend/src/utils/__tests__/authSchemas.test.js`

- [ ] **Step 1: Editar `authSchemas.js`** — substituir nas mensagens visíveis:
  - linha 8: `'A senha deve ter pelo menos 6 caracteres'` → `'A palavra-passe deve ter pelo menos 6 caracteres'`
  - linha 9: `'A senha não pode ter mais de 72 caracteres'` → `'A palavra-passe não pode ter mais de 72 caracteres'`
  - linha 25: `'Confirme a senha'` → `'Confirme a palavra-passe'`
  - linha 29: `'As senhas não coincidem'` → `'As palavras-passe não coincidem'`

- [ ] **Step 2: Atualizar o teste** `authSchemas.test.js`:
  - linha 79: `'A senha deve ter pelo menos 6 caracteres'` → `'A palavra-passe deve ter pelo menos 6 caracteres'`
  - linha 104: `'As senhas não coincidem'` → `'As palavras-passe não coincidem'`

- [ ] **Step 3: Correr o teste**

Run: `cd frontend && CI=true npx craco test src/utils/__tests__/authSchemas.test.js --watchAll=false`
Expected: PASS (todos verdes).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/utils/authSchemas.js frontend/src/utils/__tests__/authSchemas.test.js
git commit -m "i18n(pt-pt): authSchemas usa 'palavra-passe' (+ teste)"
```

---

## Task 2: Páginas públicas

**Files (Modify):**
- `frontend/src/pages/public/ContactosPage.js`
- `frontend/src/pages/public/SobrePage.js`
- `frontend/src/pages/public/TransparenciaPage.js`
- `frontend/src/pages/public/HomePage.js`
- `frontend/src/pages/public/LoginPage.js`
- `frontend/src/pages/public/ForgotPasswordPage.js`
- `frontend/src/pages/public/ResetPasswordPage.js`
- `frontend/src/pages/public/SetupAccountPage.js`

- [ ] **Step 1: "Conosco" → "Connosco"** (3 ficheiros)
  - `ContactosPage.js:67` `title="Fale Conosco"` → `title="Fale Connosco"`
  - `SobrePage.js:261` `Fale Conosco` → `Fale Connosco`
  - `TransparenciaPage.js:239` `Fale Conosco` → `Fale Connosco`

- [ ] **Step 2: "você" → impessoal** em `HomePage.js:289`
  - De: `Quando você embarca num avião, vê o piloto e a tripulação. Mas existe uma{' '}`
  - Para: `Quando embarca num avião, vê o piloto e a tripulação. Mas existe uma{' '}`

- [ ] **Step 3: "senha" → "palavra-passe"** nas páginas de auth. Em CADA ficheiro abaixo, todas as ocorrências do token visível `senha`/`Senha` passam a `palavra-passe`/`Palavra-passe` (os identificadores `showPassword`/`confirmPassword` são inglês — não são afetados):
  - `LoginPage.js:189` `Senha` → `Palavra-passe`; `:196` `Esqueceu a senha?` → `Esqueceu a palavra-passe?`
  - `ForgotPasswordPage.js:66` `Recuperar senha` → `Recuperar palavra-passe`; `:156` `Redefinir senha agora` → `Redefinir palavra-passe agora`
  - `ResetPasswordPage.js`: `:28` `'Senha alterada com sucesso!'` → `'Palavra-passe alterada com sucesso!'`; `:30` `'Erro ao redefinir senha'` → `'Erro ao redefinir palavra-passe'`; `:73` `Nova senha` → `Nova palavra-passe`; `:76` `Defina a sua nova senha de acesso ao portal.` → `Defina a sua nova palavra-passe de acesso ao portal.`; `:84` `Nova senha` → `Nova palavra-passe`; `:102` `'Esconder senha' : 'Mostrar senha'` → `'Esconder palavra-passe' : 'Mostrar palavra-passe'`; `:114` `Confirmar senha` → `Confirmar palavra-passe`; `:123` `placeholder="Repita a senha"` → `placeholder="Repita a palavra-passe"`; `:142` `Redefinir senha` → `Redefinir palavra-passe`; `:155` `Senha alterada!` → `Palavra-passe alterada!`; `:158` `A sua senha foi redefinida com sucesso. Já pode fazer login com a nova senha.` → `A sua palavra-passe foi redefinida com sucesso. Já pode fazer login com a nova palavra-passe.`
  - `SetupAccountPage.js:116` `defina a sua senha para ativar a conta.` → `defina a sua palavra-passe para ativar a conta.`; `:140` `'Ocultar senha' : 'Mostrar senha'` → `'Ocultar palavra-passe' : 'Mostrar palavra-passe'`; `:160` `placeholder="Repetir a senha"` → `placeholder="Repetir a palavra-passe"`

- [ ] **Step 4: Lint + testes das páginas**

Run: `cd frontend && npx eslint src/pages/public/ --ext .js,.jsx --max-warnings=60 && CI=true npx craco test src/pages/public --watchAll=false`
Expected: eslint sem erros; testes (se existirem) PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/public/
git commit -m "i18n(pt-pt): normaliza paginas publicas (Connosco, palavra-passe, impessoal)"
```

---

## Task 3: App privada

**Files (Modify):**
- `frontend/src/pages/private/AdminLogsPage.js`
- `frontend/src/pages/private/DashboardPage.js`
- `frontend/src/pages/private/RankingPage.js`
- `frontend/src/pages/private/DocumentosPage.js`
- `frontend/src/pages/private/financeiro/MemberFinanceView.js`
- `frontend/src/pages/private/VotacoesPage.js`

- [ ] **Step 1: "registro" → "registo"**
  - `AdminLogsPage.js:41` `Registro de todas as ações administrativas no sistema` → `Registo de todas as ações administrativas no sistema`; `:53` `Registros nesta página` → `Registos nesta página`; `:79` `Nenhum registro de auditoria` → `Nenhum registo de auditoria`; `:108` `Registros {skip + 1}` → `Registos {skip + 1}`
  - `MemberFinanceView.js:50` `label="Registros"` → `label="Registos"`; `:70` `Nenhum registro encontrado` → `Nenhum registo encontrado`

- [ ] **Step 2: "arquivo" → "ficheiro"** em `DocumentosPage.js`
  - `:193` `'Tipo de arquivo não permitido. Use PDF, DOC ou DOCX.'` → `'Tipo de ficheiro não permitido. Use PDF, DOC ou DOCX.'`
  - `:197` `'Arquivo muito grande. Máximo 10MB.'` → `'Ficheiro muito grande. Máximo 10MB.'`
  - `:291` `Arquivo *` → `Ficheiro *`

- [ ] **Step 3: "(você)"/"(voce)" → "(eu)"** (marca a linha do próprio na tabela)
  - `DashboardPage.js:669` `isMe && ' (voce)'` → `isMe && ' (eu)'`
  - `RankingPage.js:361` `isMe && ' (você)'` → `isMe && ' (eu)'`; `:425` idem → `isMe && ' (eu)'`

- [ ] **Step 4: "Você será notificado" → "Será notificado"** em `VotacoesPage.js`
  - `:120` `description="Você será notificado quando novas votações forem criadas"` → `description="Será notificado quando novas votações forem criadas"`
  - `:217` `<span>Você será notificado quando novas votações forem abertas</span>` → `<span>Será notificado quando novas votações forem abertas</span>`

- [ ] **Step 5: Lint + testes**

Run: `cd frontend && npx eslint src/pages/private/ --ext .js,.jsx --max-warnings=60 && CI=true npx craco test src/pages/private --watchAll=false`
Expected: eslint sem erros; testes PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/private/
git commit -m "i18n(pt-pt): normaliza app privada (registo, ficheiro, impessoal)"
```

---

## Task 4: Backend (strings ao utilizador)

**Files (Modify):**
- `backend/routes/auth_routes.py`
- `backend/routes/documents.py`
- `backend/routes/gallery.py`
- `backend/routes/polls.py`
- `backend/routes/upload.py`
- `backend/email_service.py`

⚠️ **NÃO tocar** `backend/routes/profissional.py:689` (`"Arquivou …"` = verbo arquivar).

- [ ] **Step 1: auth_routes.py — "senha" → "palavra-passe"** (texto visível)
  - `:96` `detail="Conta pendente de ativacao. Use o link de convite para definir a sua senha."` → `…para definir a sua palavra-passe."`
  - `:298` `detail="A senha deve ter pelo menos 6 caracteres"` → `detail="A palavra-passe deve ter pelo menos 6 caracteres"`
  - `:407` igual a :298 → `"A palavra-passe deve ter pelo menos 6 caracteres"`
  - `:424` `return {"message": "Senha alterada com sucesso. Pode fazer login com a nova senha."}` → `{"message": "Palavra-passe alterada com sucesso. Pode fazer login com a nova palavra-passe."}`

- [ ] **Step 2: "Arquivo" → "Ficheiro" / "Deletou/deletado" → "Eliminou/eliminado"**
  - `documents.py:58` e `:66` `detail="Arquivo do documento nao encontrado"` → `detail="Ficheiro do documento nao encontrado"`
  - `gallery.py:204` `detail="Arquivo excede o limite de 10 MB"` → `detail="Ficheiro excede o limite de 10 MB"`
  - `upload.py:45` `detail=f"Arquivo excede o limite de {max_mb:.0f} MB"` → `detail=f"Ficheiro excede o limite de {max_mb:.0f} MB"`
  - `upload.py:86` `f"Upload de arquivo: {file.filename}"` → `f"Upload de ficheiro: {file.filename}"`
  - `upload.py:105` `detail="Arquivo não encontrado"` → `detail="Ficheiro não encontrado"`
  - `upload.py:109` `f"Deletou arquivo: {filename}"` → `f"Eliminou ficheiro: {filename}"`
  - `upload.py:110` `return {"message": "Arquivo deletado com sucesso"}` → `{"message": "Ficheiro eliminado com sucesso"}`

- [ ] **Step 3: polls.py — "Você já votou" → "Já votou"**
  - `:142` e `:152` `detail="Você já votou nesta votação"` → `detail="Já votou nesta votação"`

- [ ] **Step 4: email_service.py — "senha"/"Senha" → "palavra-passe"** (template, nada é enviado)
  - `:68` `Para ativar a sua conta, clique no botao abaixo e defina a sua senha:` → `…e defina a sua palavra-passe:`
  - `:88` `Recuperacao de Senha` → `Recuperacao de palavra-passe`
  - `:90` `recebemos um pedido para redefinir a sua senha no Portal ACCTA.` → `…para redefinir a sua palavra-passe no Portal ACCTA.`
  - `:176` `f"Recuperacao de Senha — {APP_NAME}"` → `f"Recuperacao de palavra-passe — {APP_NAME}"`

- [ ] **Step 5: Correr testes backend tocados**

Run: `cd backend && ./venv311/Scripts/python.exe -m pytest tests/test_auth_routes.py tests/test_documents*.py tests/test_polls*.py tests/test_gallery*.py tests/test_upload*.py -q`
Expected: sem regressões (os testes que existirem passam; ficheiros `import requests` falham por falta de servidor — ambiental, não regressão). Nenhum teste afirma estas strings (verificado).

- [ ] **Step 6: Commit**

```bash
git add backend/routes/auth_routes.py backend/routes/documents.py backend/routes/gallery.py backend/routes/polls.py backend/routes/upload.py backend/email_service.py
git commit -m "i18n(pt-pt): normaliza strings do backend (palavra-passe, ficheiro, impessoal)"
```

---

## Task 5: Relatório-fonte (`memory/deep-research-report.md`)

**Files (Modify):** `memory/deep-research-report.md`

- [ ] **Step 1: Edições conhecidas**
  - `:101` `há registro oficial de que` → `há registo oficial de que`
  - `:167` `estatutos ou registro público` → `estatutos ou registo público`
  - `:237` `└── Contatos úteis` → `└── Contactos úteis`
  - `:244` `**Contatos úteis**` → `**Contactos úteis**`
  - `:246` tabela: `| Contato principal |` → `| Contacto principal |`

- [ ] **Step 2: Varredura de confirmação** — correr o detetor no relatório e tratar qualquer resto:

Run: `cd .. && grep -nEi "usu[áa]rio|registro|arquivo|conosco|\bvoc[êe]\b|\btela\b|contato|equipe|esporte|planejamento|gerenciar|acessar|deletar|aplicativo|celular" accta/memory/deep-research-report.md`
Expected: vazio após as edições do Step 1 (se aparecer algo novo, aplicar o glossário em contexto).

- [ ] **Step 3: Commit**

```bash
git add memory/deep-research-report.md
git commit -m "i18n(pt-pt): normaliza relatorio-fonte (registo, contacto)"
```

---

## Task 6: Varredura final + PR

- [ ] **Step 1: Varredura global de confirmação** (texto visível, excluindo identificadores e o falso positivo `Arquivou`)

Run:
```bash
cd frontend && grep -rEn "Conosco|\bvoc[êe]\b|\bsenha\b|\bSenha\b|registro|Registro|\barquivo\b|\bArquivo\b" src/pages src/components src/layouts --include="*.js" --include="*.jsx" | grep -viE "showPassword|confirmPassword|data-testid|AdminUsuariosPage|/admin/usuarios"
```
Expected: vazio (ou só ocorrências justificadas). Corrigir o que sobrar.

- [ ] **Step 2: Suite frontend relevante + lint global**

Run: `cd frontend && CI=true npx craco test --watchAll=false && npx eslint src/ --ext .js,.jsx --max-warnings=60`
Expected: testes PASS; eslint dentro do limite.

- [ ] **Step 3: Push + PR para develop**

```bash
git push -u origin feature/normalizacao-pt-pt
gh pr create --base develop --head feature/normalizacao-pt-pt \
  --title "i18n(pt-pt): normalizacao para portugues de Portugal (sub-projeto A)" \
  --body "Substitui brasileirismos por PT-PT em texto visivel (publico + privado + backend + relatorio-fonte). Glossario e guardrails na spec docs/superpowers/specs/2026-06-11-normalizacao-pt-pt-design.md. Sem alteracao de identificadores/rotas. Unico teste atualizado: authSchemas.test.js. B/C/D (factual/links/FIR) ficam para a 2a ronda."
```

- [ ] **Step 4:** Confirmar checks (billing-lock: Backend/Frontend/claude-review falham em ~3s; Vercel passa — não bloqueia).
