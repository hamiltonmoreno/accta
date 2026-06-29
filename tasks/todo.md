# Spec 011 — Aviso de rejeição de Ato com o motivo (Revisão)

**Feita** (branch `feature/aviso-rejeicao-ato`): avisar o proponente de um Ato (Art. 54)
quando é rejeitado, **com o motivo** (Q1=A, obrigatório). Desenho mínimo: o motivo vive
**na assinatura de rejeição** em `Ato.assinaturas[]` (**sem schema/migração/DAO**); reutiliza
o aviso de rejeição existente (in-app + push) + a auditoria.

- T002 `backend/models.py`: `AtoSign.motivo: Optional[str] = None` (aditivo).
- T003/T004 `backend/routes/atos.py` (`sign_ato`): exige motivo não-vazio ≤500 ao rejeitar
  (400 PT); põe `motivo` na assinatura; enriquece o aviso ao proponente e o `details` da
  auditoria com o motivo. Aprovar inalterado (ignora motivo).
- T005 `frontend/utils/api.js`: `atos.assinar(id, decisao, motivo)`.
- T006 `frontend/CoAprovacoesPage.js`: diálogo de rejeição com textarea obrigatória
  (contador ≤500, confirmar desativado se vazio; botão Carmesim sólido no confirm irreversível).
- T008 `frontend/CoAprovacoesPage.js`: mostra o motivo + cargo de quem rejeitou nos Atos rejeitados.
- T007 `backend/tests/test_atos_rejeicao_motivo.py` (7 casos) + ajuste de
  `test_atos.py::test_rejeicao_fecha` (passou a exigir motivo).

**Verificação**: 42 testes de Atos verdes (7 novos + 35 existentes); suite unit completa
**1346 passed**; ruff / ruff-format / eslint limpos.

**Nota (pré-existente, fora do âmbito):**
`tests/test_idor.py::test_delete_expense_non_manager_forbidden` falha com
`delete_expense() missing 'request'` — drift de assinatura num teste de despesas de projeto,
**não tocado por esta spec** (confirmado por stash: falha na base, sem as minhas mudanças).
Candidato a follow-up isolado (passar `request` no teste).

**Por fechar (fora do âmbito de codificação):** PR → `develop`; release `develop→main` exige
**Via B** (toca `backend/`); verificação prod = `POST /api/atos/<id>/assinar {"decisao":"rejeitado"}`
sem motivo → 400 (e sem token → 401). Só após RELEASED+deployed renomear `specs/011-...` para
`-concluido`. Validação funcional ponta-a-ponta (Cenário B, navegador) = Princípio VII (dono).
