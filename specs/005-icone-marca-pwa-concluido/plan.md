# Implementation Plan: Ícone quadrado da marca / PWA

**Branch**: `feature/icone-marca-pwa` | **Date**: 2026-06-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/005-icone-marca-pwa/spec.md`

## Summary

Acrescentar ao subsistema de marca (já com logótipos claro/escuro + favicon) um
**ícone quadrado da marca** carregável pela página Aparência → Marca, que passa a
alimentar as superfícies quadradas do portal: **marca compacta in-app** (sidebar
recolhida, runtime), **ícone da aplicação instalada (PWA)** e **imagem de
pré-visualização de partilha (og)**.

A peça nova chave é o **serviço dinâmico** (decisão Q1): em vez de o `manifest.json`
e o `og:image` apontarem para ficheiros estáticos cujo nome muda a cada upload, passam
a apontar para um **URL estável do backend** — `GET /api/brand/icon` — que serve sempre
o ícone atual (ou o default quando não há upload). Assim, trocar o ícone pela UI
reflete-se na app instalada e nas partilhas **sem novo deploy** (best-effort para
crawlers, que dependem de re-indexar). O campo é **distinto do favicon** (decisão Q2):
`icon_url` novo, `favicon_url` intocado.

Abordagem deliberadamente simples (Princípio I): **servir a imagem-mestre tal-e-qual**
(o browser/SO escala), **sem dependência de processamento de imagem** (sem Pillow);
reutiliza a categoria de upload `brand`, o documento `brand_settings`, o padrão de
PATCH+audit e o componente runtime de marca já existentes.

## Technical Context

**Language/Version**: Python 3.11 (backend) · React 19 (frontend)

**Primary Dependencies**: FastAPI + asyncpg (DAO Mongo-compatível em `database.py`);
React + TanStack Query + Tailwind + shadcn/ui. **Sem novas dependências** (em particular,
sem biblioteca de imagem — a imagem-mestre é servida sem redimensionar).

**Storage**: documento único `brand_settings` (tabela `(pk, doc jsonb)`); novo campo
`icon_url`. Ficheiro carregado em `/uploads/brand/` (já servido estaticamente por
`UploadsStaticFiles` em `server.py`).

**Testing**: pytest in-process (backend, `tests/test_brand_routes.py`); validação manual
no browser + instalação PWA (frontend, conforme convenção do projeto e Princípio VII).

**Target Platform**: web — frontend na Vercel (`controlador.cv`), backend no VPS
(`api.controlador.cv`); portal instalável como PWA.

**Project Type**: web application (frontend + backend).

**Performance Goals**: `GET /api/brand/icon` leve e cacheável (servir/redirecionar com
`Cache-Control` curto-médio); não é caminho crítico de performance.

**Constraints**: SVG bloqueado (XSS); upload ≤ 2 MB (categoria `brand`); `manifest.json`
e `index.html` são estáticos na Vercel → o URL do backend tem de ser **absoluto e fixo**
(hardcode do origin de prod `https://api.controlador.cv`, coerente com o `og:image`
atual que já hardcoda `https://controlador.cv/...`). Sem dark mode (ícone único).

**Scale/Scope**: ~poucas centenas de sócios; 1 documento de marca; delta pequeno
(1 endpoint novo + 1 campo + 1 secção de UI + 2 referências estáticas + 1 componente
in-app).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|---|---|
| **I. Simplicity First** | ✅ Servir imagem-mestre tal-e-qual; **sem** processamento de imagem nem novas deps; reutiliza upload `brand`, `brand_settings`, PATCH+audit e padrão do `FaviconManager`. Endpoint único serve PWA+og (não dois). |
| **II. Root-Cause Discipline** | ✅ Resolve a causa real (assets quadrados presos a ficheiros estáticos do template) com um URL estável servido dinamicamente — não um patch por superfície. |
| **III. RBAC + Audit (NON-NEGOTIABLE)** | ✅ Escrita (`PATCH /api/brand`, `POST /api/upload/brand`) restrita a admin+moderador; `create_audit_log` no PATCH; leitura `GET /api/brand/icon` e `/api/brand/public` públicas (a marca é pública); **sem SQL cru** (DAO); projeções mantêm-se. |
| **IV. Language Discipline** | ✅ UI/strings em PT; identificadores EN (`icon_url`, `get_brand_icon`); docstrings/comentários PT. |
| **V. Design System Authority (NON-NEGOTIABLE)** | ✅ Nova `IconSlot` na página Marca segue o padrão neutro do `FaviconSlot` (botões `border-[#D1D5DB]`, Carmesim só no focus ring, sem primário, sem red-on-dark); sem dark mode. |
| **VI. GitFlow + Confirmação** | ✅ `feature/icone-marca-pwa` → PR `develop`. Backend tocado → release + Via B com confirmação do dono. **Nenhuma** STOP condition acionada (campo aditivo opcional; sem migração destrutiva; sem CORS/JWT/email). |
| **VII. Verification Before Done (NON-NEGOTIABLE)** | ✅ pytest backend + verificação no browser (in-app) + **instalação PWA** e inspeção do `manifest`/og servidos; para prod, "teste decisivo" no runbook Via B (`GET /api/brand/icon` → 200 imagem; manifest aponta para o endpoint). |

**Resultado**: PASS — sem violações; Complexity Tracking vazio.

## Project Structure

### Documentation (this feature)

```text
specs/005-icone-marca-pwa/
├── plan.md              # Este ficheiro (/speckit-plan)
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── brand-icon.md    # Phase 1 — contrato do endpoint + PATCH estendido
├── checklists/
│   └── requirements.md  # da /speckit-specify
└── tasks.md             # /speckit-tasks (NÃO criado aqui)
```

### Source Code (repository root)

```text
backend/
├── models.py                     # + icon_url em BrandSettings / BrandSettingsUpdate
├── routes/brand.py               # + GET /api/brand/icon (público); icon_url no _public_view,
│                                 #   no PATCH (url_fields), na limpeza de órfãos e no audit
└── tests/test_brand_routes.py    # + testes: definir/limpar icon_url; /icon serve atual/default

frontend/
├── public/
│   ├── manifest.json             # icons[].src → https://api.controlador.cv/api/brand/icon
│   └── index.html                # og:image / twitter:image → .../api/brand/icon
└── src/
    ├── components/
    │   ├── BrandIcon.js           # NOVO — mark quadrado in-app (runtime; default fallback)
    │   └── FaviconManager.js      # (inalterado; favicon continua separado)
    ├── pages/private/AdminMarcaPage.js   # + <IconSlot> (preview + substituir/repor)
    ├── layouts/PrivateLayout.js   # sidebar recolhida usa <BrandIcon /> (US3, P3)
    └── utils/api.js               # (brandAPI já existe; sem alteração de contrato JS)
```

**Structure Decision**: web application (frontend + backend) — estende o subsistema de
marca existente; nenhuma estrutura nova. O único componente novo é `BrandIcon.js`
(espelha o padrão do `BrandLogo`/`FaviconManager`).

## Complexity Tracking

> Sem violações constitucionais — nada a justificar.
