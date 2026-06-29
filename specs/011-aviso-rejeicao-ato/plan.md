# Implementation Plan: Aviso de rejeição de Ato com o motivo

**Branch**: `feature/aviso-rejeicao-ato` | **Date**: 2026-06-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/011-aviso-rejeicao-ato/spec.md`

## Summary

Quando um membro da Direção **rejeita** um Ato (Art. 54), passa a indicar um **motivo
obrigatório**. Esse motivo é (1) entregue ao proponente no aviso de rejeição já
existente (in-app + espelho push), e (2) persistido **na própria assinatura de
rejeição** dentro de `Ato.assinaturas[]`, ficando visível na vista de detalhe das
co-aprovações. Abordagem deliberadamente mínima: **sem schema novo, sem migração, sem
tocar no DAO** — o motivo viaja no dict da assinatura que a rota já constrói e o
`sign_ato_atomic` já persiste. Backend (validação + aviso + auditoria) e um toque de
frontend (campo de motivo no diálogo de rejeição + mostrar o motivo no Ato rejeitado).

## Technical Context

**Language/Version**: Python 3.11 (backend), React 19 (frontend)

**Primary Dependencies**: FastAPI + Pydantic; helpers `notify_users`/`create_audit_log`;
`atos_rules.evaluate_status` (veto único); shadcn/ui + Tailwind no frontend. **Zero deps novas.**

**Storage**: PostgreSQL via DAO Mongo-compatível. O motivo é gravado **na assinatura
de rejeição** (`Ato.assinaturas[]`, jsonb) — **sem coluna/coleção/índice novos**.

**Testing**: pytest (unit, in-process com `mock_db` + fixtures de role); validação
funcional de frontend em navegador (Princípio VII, dono).

**Target Platform**: Backend Linux/Docker (prod Via B); frontend Vercel.

**Project Type**: Web app (backend FastAPI + frontend React).

**Performance Goals**: N/A (caminho de assinatura, baixa frequência; +1 campo no doc).

**Constraints**: Reutiliza o aviso de rejeição existente (não duplicar); motivo
obrigatório e não-vazio ao rejeitar (Q1=A); limite máximo de tamanho (ver research).

**Scale/Scope**: Atos de co-aprovação da Direção; volume baixo.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Simplicity First** ✅ — motivo na assinatura existente; sem schema/migração/DAO;
  reaproveita aviso e auditoria. Nenhum endpoint novo.
- **II. Root-Cause Discipline** ✅ — corrige a lacuna na origem (a rota de assinatura),
  não um remendo a jusante.
- **III. RBAC + Audit (NON-NEGOTIABLE)** ✅ — mantém `_require_sign` (Direção) na rota;
  o motivo entra no `create_audit_log` já emitido na assinatura. Sem SQL em rotas.
- **IV. Language Discipline** ✅ — texto ao utilizador em PT; identificadores em EN
  com termo de domínio PT (`motivo`, `rejeitado`). Sem renomeações em massa.
- **V. Design System Authority (NON-NEGOTIABLE)** ✅ — diálogo de rejeição segue
  `frontend-design`: ação destrutiva = Carmesim (sólido só dentro do confirm
  irreversível), neutro no resto, sem dark mode. Campo de motivo = textarea shadcn/ui.
- **VI. GitFlow + Confirmation** ✅ — `feature/aviso-rejeicao-ato` → PR para `develop`;
  release `develop→main` exigirá **Via B** (toca `backend/`).
- **VII. Verification Before Done (NON-NEGOTIABLE)** ✅ — testes unit backend verdes +
  validação funcional do dono (rejeitar com/sem motivo, proponente vê o motivo).

**Sem violações — sem entradas em Complexity Tracking.**

## Project Structure

### Documentation (this feature)

```text
specs/011-aviso-rejeicao-ato/
├── plan.md              # Este ficheiro
├── research.md          # Phase 0 (decisões: onde guardar o motivo, limite, formato do aviso)
├── data-model.md        # Phase 1 (AtoSign.motivo; assinatura.motivo em Ato.assinaturas[])
├── quickstart.md        # Phase 1 (cenários de validação ponta-a-ponta)
├── contracts/           # Phase 1 (contrato do POST /atos/{id}/assinar + aviso)
└── checklists/requirements.md
```

### Source Code (repository root)

```text
backend/
├── models.py                      # AtoSign: +motivo (Optional[str]); sem mudança em Ato
├── routes/atos.py                 # sign_ato: exigir motivo ao rejeitar, validar tamanho,
│                                   #   pôr motivo na assinatura, no aviso e na auditoria
└── tests/test_atos_rejeicao_motivo.py   # NOVO — unit do fluxo de rejeição com motivo

frontend/src/
├── pages/private/CoAprovacoesPage.js    # diálogo de rejeição com textarea de motivo;
│                                         #   mostrar motivo nos Atos rejeitados
└── utils/api.js                          # atos.assinar(...) passa o motivo
```

**Structure Decision**: Web app existente. Nada de novo estrutural — só campos e lógica
aditiva nos ficheiros já donos do fluxo de Atos. `database.py` **não muda** (a assinatura
com o motivo é persistida pelo `sign_ato_atomic` tal como hoje).

## Complexity Tracking

> Sem violações da Constituição — secção não aplicável.
