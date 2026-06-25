---
description: "Task list — Ícone quadrado da marca / PWA"
---

# Tasks: Ícone quadrado da marca / PWA

**Input**: Design documents from `specs/005-icone-marca-pwa/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/brand-icon.md, quickstart.md

**Tests**: tarefas de teste de **backend (pytest)** incluídas — são convenção do projeto
(`tests/test_brand_routes.py`) e estão explícitas no contrato. A validação de **frontend
é manual no browser** (convenção do projeto + Princípio VII).

**Organization**: agrupado por user story para implementação/teste independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode correr em paralelo (ficheiros diferentes, sem dependências por concluir)
- **[Story]**: US1 / US2 / US3 (mapeia spec.md)
- Caminhos de ficheiro exatos em cada tarefa

## Path Conventions

Web app: `backend/` e `frontend/src/` na raiz do repo (git root = `accta-main/accta/`).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: baseline antes de tocar em código.

- [X] T001 Confirmar branch `feature/icone-marca-pwa` e baseline verde: `cd backend && pytest tests/test_brand_routes.py -q` (deve passar antes de qualquer alteração)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: persistir e expor o novo campo `icon_url` — base partilhada por **todas** as
user stories.

**⚠️ CRITICAL**: nenhuma user story arranca antes desta fase.

- [X] T002 [P] Acrescentar `icon_url: Optional[str] = None` a `BrandSettings` (comentário: ícone quadrado PWA/og/in-app; None → default estático) e a `BrandSettingsUpdate` (comentário: "" = repor default; None = manter) em `backend/models.py`
- [X] T003 Estender `backend/routes/brand.py`: incluir `"icon_url"` no tuplo `url_fields` (já trata PATCH `set_fields`, semântica `""`→None, limpeza de uploads órfãos e `details` do audit) e acrescentar `"icon_url": doc.get("icon_url")` ao `_public_view` (depende de T002)

**Checkpoint**: `icon_url` persiste via PATCH, aparece em `/api/brand` e `/api/brand/public`, é auditado e tem limpeza de órfãos — pronto para as stories.

---

## Phase 3: User Story 1 - Gerir o ícone quadrado da marca (Priority: P1) 🎯 MVP

**Goal**: Admin/Moderador carrega, pré-visualiza e repõe o ícone quadrado na página
Aparência → Marca; ação auditada; sem deploy.

**Independent Test**: carregar um ícone, ver a pré-visualização e a persistência; repor e
confirmar regresso ao default; financeiro/socio recebem 403.

### Tests for User Story 1

- [X] T004 [P] [US1] Em `backend/tests/test_brand_routes.py`, acrescentar testes: `PATCH /api/brand` define `icon_url` (admin e moderador); nega financeiro/socio (403); `icon_url=""` repõe `None` e apaga o upload anterior; `GET /api/brand/public` devolve `icon_url` (null quando vazio, valor quando gravado)

### Implementation for User Story 1

- [X] T005 [US1] Criar `IconSlot` em `frontend/src/pages/private/AdminMarcaPage.js` (espelha `FaviconSlot`): pré-visualização do ícone em tamanhos representativos de app, hint de formato (quadrado, transparente, ~512×512, conteúdo centrado com safe-zone), botões Substituir/Repor com `data-testid` próprios; ligado a `handleUpload('icon_url', file)` / `handleReset('icon_url')` e `busyField === 'icon_url'`. Renderizar `<IconSlot url={data?.icon_url} … />` junto do `FaviconSlot`
- [X] T006 [P] [US1] Atualizar o subtítulo em `frontend/src/pages/private/AdminAparenciaPage.js` para mencionar também o ícone da app/partilha

**Checkpoint**: US1 funcional e testável de forma independente (gestão completa do ícone pela UI).

---

## Phase 4: User Story 2 - App instalada e partilhas mostram a marca (Priority: P1)

**Goal**: o ícone carregado alimenta o ícone PWA e a imagem de partilha (og) via um URL
estável do backend, sem novo deploy.

**Independent Test**: com ícone carregado, `GET /api/brand/icon` resolve para a imagem;
`manifest`/`og` apontam para esse URL; instalar PWA / validar Open Graph mostra a marca.

### Tests for User Story 2

> Escrever T007 primeiro e confirmar que **falha** (rota inexistente → 404) antes de T008.

- [X] T007 [US2] Em `backend/tests/test_brand_routes.py`, testar `GET /api/brand/icon`: com `icon_url` definido → 302 com `Location` = esse URL; sem `icon_url` → 302 para o default (`{FRONTEND_URL}/logo512.png`)

### Implementation for User Story 2

- [X] T008 [US2] Adicionar `GET /api/brand/icon` (público) em `backend/routes/brand.py`: lê `brand_settings`; se `icon_url` → `RedirectResponse(icon_url, 302)`; senão → `RedirectResponse(f"{FRONTEND_URL}/logo512.png", 302)`; header `Cache-Control: public, max-age=3600`. Importar `FRONTEND_URL` da config/env (depende de T003; faz T007 passar)
- [X] T009 [P] [US2] Em `frontend/public/manifest.json`, substituir a entrada de ícone "grande" por `{ "src": "https://api.controlador.cv/api/brand/icon", "sizes": "any", "purpose": "any", "type": "image/png" }` (manter `favicon.ico`); atualizar também os ícones dos `shortcuts` se aplicável
- [X] T010 [P] [US2] Em `frontend/public/index.html`, apontar `og:image` e `twitter:image` para `https://api.controlador.cv/api/brand/icon`

**Checkpoint**: US1 + US2 funcionais; trocar o ícone pela UI reflete-se no PWA/partilhas sem deploy.

---

## Phase 5: User Story 3 - Marca compacta dentro da app (Priority: P3)

**Goal**: a sidebar recolhida (e contextos estreitos) mostram o ícone quadrado da marca
como mark compacto, em runtime.

**Independent Test**: recolher a sidebar com ícone carregado → mostra o ícone da marca;
sem ícone → mark por defeito (sem espaço vazio).

### Implementation for User Story 3

- [X] T011 [P] [US3] Criar `frontend/src/components/BrandIcon.js` (espelha `BrandLogo`/`FaviconManager`): lê a marca pública via TanStack Query (`queryKeys.brand.public()`, `staleTime` alto); renderiza `icon_url` (via `mediaUrl`) quadrado, ou um mark por defeito (`ACCTALogo variant="icon"` ou mark neutro com iniciais) quando ausente; aceita `className`/tamanho
- [X] T012 [US3] Em `frontend/src/layouts/PrivateLayout.js`, mostrar `<BrandIcon />` no topo da sidebar quando recolhida (`collapsed && !isMobile`), sem partir o layout expandido (depende de T011)

**Checkpoint**: as 3 user stories independentemente funcionais.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T013 [P] Correr a validação `specs/005-icone-marca-pwa/quickstart.md` (C1–C6) e registar resultados — **C1** verde (`pytest tests/test_brand_routes.py` = 20 passed, 2026-06-25); **C3** verificado server-side em **prod** (`GET /api/brand/icon` via `-L` → 200; `/api/brand/public` inclui `icon_url`, ver [[prod-backend-deployed-state]]). **C2/C4/C5/C6 (UI/PWA/iOS) NÃO exercitados** — exigem browser/dispositivo real; por Princípio VII declara-se explicitamente em vez de afirmar sucesso (residual de validação manual do dono).
- [X] T014 [P] Atualizar `docs/runbook-deploy-backend-via-b.md` com o "teste decisivo" desta release (`GET /api/brand/icon` → 200 imagem via -L; `/api/brand/public` inclui `icon_url`) — runbook atualizado para v0.5.35 (`sha-b16773a08b8a`, rollback `sha-4a78080aec1e`): valores §1, comandos §2, teste decisivo na verificação, rollback §3, histórico §6.
- [X] T015 Verificação final: `cd backend && pytest tests/test_brand_routes.py -q` verde; `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60` limpo; `cd frontend && npx craco build` OK

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências.
- **Foundational (Phase 2)**: depende do Setup — **BLOQUEIA** todas as user stories.
- **User Stories (Phase 3–5)**: dependem da Phase 2.
  - US1 e US2 são ambas P1; US2 (endpoint) depende do campo (T003) mas é independente da UI de US1.
  - US3 (P3) independente; só depende da Phase 2.
- **Polish (Phase 6)**: depois das stories desejadas.

### User Story Dependencies

- **US1 (P1)**: após Phase 2. Sem dependência de US2/US3.
- **US2 (P1)**: após Phase 2 (T008 depende de T003). Independente da UI de US1.
- **US3 (P3)**: após Phase 2. Independente.

### Within Each User Story

- Teste do endpoint primeiro (T007, falha), depois implementação (T008, faz passar).
- Endpoint (T008) antes das referências estáticas que o consomem (T009/T010 podem editar em paralelo).
- `BrandIcon` (T011) antes da integração na sidebar (T012).

### Parallel Opportunities

- T002 [P] (models) pode iniciar enquanto se prepara T003.
- US1 e US3 podem ser feitas em paralelo por pessoas diferentes após a Phase 2.
- Dentro de US2: T009 e T010 [P] (manifest + index.html, ficheiros diferentes).
- T006 [P] (AdminAparenciaPage) paralela ao resto de US1.
- Polish: T013 e T014 [P].

---

## Parallel Example: User Story 2

```bash
# Após T008 (endpoint) estar feito, editar em paralelo as referências estáticas:
Task: "manifest.json icons[].src → https://api.controlador.cv/api/brand/icon"   # T009
Task: "index.html og:image/twitter:image → https://api.controlador.cv/api/brand/icon"  # T010
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 (Setup) → 2. Phase 2 (Foundational, CRÍTICA) → 3. Phase 3 (US1).
4. **PARAR e VALIDAR**: gerir o ícone pela UI (carregar/repor) ponta-a-ponta.
5. US1 já entrega valor (o gestor controla o ícone quadrado num único sítio).

### Incremental Delivery

1. Setup + Foundational → base pronta.
2. US1 → testar → demo (MVP: gestão pela UI).
3. US2 → testar (PWA/og dinâmicos) → demo — **o porquê principal**.
4. US3 → testar (mark in-app) → demo.

### Release (após US desejadas)

- Backend tocado (`models.py`, `brand.py`) → release `release/v0.5.x` → PR `main` (STOP,
  confirmar) → tag → back-merge → **deploy Via B** (build no VPS, compose, teste decisivo
  `GET /api/brand/icon`) + Vercel para o frontend.

---

## Notes

- [P] = ficheiros diferentes, sem dependências por concluir.
- Reutiliza ao máximo a infraestrutura da feature do favicon (categoria de upload `brand`,
  `url_fields`, `_public_view`, padrão `FaviconSlot`/`FaviconManager`).
- `favicon_url` permanece **intocado** (Q2 = campos distintos).
- Commit por tarefa ou grupo lógico; parar nos checkpoints para validar cada story.
- Sem migração de dados, sem índice novo, sem nova dependência (sem Pillow).
