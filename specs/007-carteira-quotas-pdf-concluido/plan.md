# Implementation Plan: Exportar carteira de quotas em PDF

**Branch**: `feature/carteira-quotas-pdf` | **Date**: 2026-06-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/007-carteira-quotas-pdf/spec.md`

## Summary

Adicionar uma exportação **PDF da carteira de quotas do próprio sócio**, reutilizando
infra já existente no portal: o endpoint self-service `GET /api/finances/me/quotas`
(fonte de dados, já RBAC-safe por `user_id`), o gerador de PDF *branded* `fpdf`
(`_new_relatorio_pdf()` + estilo Carmesim/Grafite em `routes/finances.py`) e o idioma
de download por *blob* já presente no frontend (`CarteiraPage.js` para o QR;
`DRETab.js` para PDF). Backend: 1 endpoint novo + 1 renderer. Frontend: 1 botão
"Exportar PDF" na Carteira + 1 método de API. Zero dependências novas.

## Technical Context

**Language/Version**: Python 3.11 (backend), JavaScript/React 19 (frontend)

**Primary Dependencies**: FastAPI + `fpdf` (fpdf2, **já instalado**), `StreamingResponse`;
frontend Axios + React (já instalados). **Zero deps novas.**

**Storage**: PostgreSQL via DAO Mongo-compatible (`db.transactions`) — **leitura apenas**
(mesma query de `/me/quotas`: `type=receita`, `category ∈ {quotas, joias}`, `user_id` do
próprio). Sem schema novo, sem migração.

**Testing**: pytest unit (endpoint com `mock_db` + token forjado, asserts no
`StreamingResponse`/headers/own-data); verificação em navegador do download real.

**Target Platform**: Web (portal privado).

**Project Type**: Web app (frontend + backend).

**Performance Goals**: download em <10s (SC-001); geração de PDF de algumas centenas de
linhas é instantânea.

**Constraints**: RBAC self-service (só o próprio); marca ACCTA; texto do PDF ASCII-safe
nos rótulos (convenção dos PDF existentes); dados PT (nomes/descrições) são latin-1-safe.

**Scale/Scope**: ~3 ficheiros (`routes/finances.py`, `CarteiraPage.js`, `utils/api.js`);
carteira de um sócio = dezenas a baixas centenas de lançamentos.

## Constitution Check

*GATE: avaliado antes da Fase 0 e reconfirmado após a Fase 1.*

| Princípio | Estado | Nota |
|-----------|--------|------|
| I. Simplicity First | ✅ | Reutiliza query `/me/quotas`, helpers FPDF e idioma de download existentes. 1 endpoint + 1 renderer + 1 botão. |
| II. Root-Cause Discipline | ✅ N/A | Feature nova. |
| III. RBAC + Audit | ✅ | Endpoint usa `get_current_user` e filtra por `user_id` do próprio (sem privilégio, igual a `/me/quotas`). É **leitura dos próprios dados** → **sem audit log** (audit é para escritas de admin); sem raw SQL (DAO). `password` nunca exposto. |
| IV. Language Discipline | ✅ | Botão/filename/erros em PT; rótulos do PDF ASCII-safe (convenção dos PDF atuais); dados PT latin-1-safe. Identificadores EN. |
| V. Design System Authority | ✅ | "Exportar PDF" = ação de **exportação → botão neutro** (não Floresta/Carmesim). PDF mantém a marca ACCTA já usada (Carmesim header / Grafite texto). |
| VI. GitFlow + Confirmation | ✅ | `feature/* → develop`. Toca `backend/` → o próximo corte `develop→main` exige **Via B** (não-STOP agora; só na release). |
| VII. Verification Before Done | ✅ | Teste backend (pytest) + verificação do download em navegador (Princípio VII). |

**Resultado do gate**: PASS, sem deviations. Sem Complexity Tracking necessário.

## Project Structure

### Documentation (this feature)

```text
specs/007-carteira-quotas-pdf/
├── plan.md              # Este ficheiro
├── research.md          # Fase 0 — decisões (PDF, RBAC, encoding, download, layout)
├── data-model.md        # Fase 1 — sem schema novo (documenta a vista existente)
├── quickstart.md        # Fase 1 — guia de validação (pytest + navegador)
├── contracts/           # Fase 1 — contrato do endpoint novo
└── tasks.md             # Fase 2 (/speckit-tasks — NÃO criado aqui)
```

### Source Code (repository root)

```text
backend/
└── routes/finances.py        # + GET /me/quotas/pdf  e  _render_carteira() (reusa _new_relatorio_pdf/_fmt)

frontend/src/
├── pages/private/CarteiraPage.js   # + botão "Exportar PDF" (reusa o idioma de download por blob já presente)
└── utils/api.js                    # + financesAPI.myQuotasPdf() (GET responseType:'blob')
```

**Structure Decision**: Web app; feature toca **backend** (1 endpoint + 1 renderer em
`finances.py`) **e frontend** (botão + método de API). É a primeira linha desta release a
mexer no backend desde v0.5.37, por isso a release que a levar a prod precisará de **Via B**
(ver [[prod-backend-deployed-state]]).

## Complexity Tracking

> Sem violações do Constitution Check — secção não aplicável.
