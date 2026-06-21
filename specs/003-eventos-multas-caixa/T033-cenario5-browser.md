# T033 — Cenário 5 (UI / browser) — checklist de validação

Os Cenários 1–4 do `quickstart.md` estão **automatizados e verdes** em
`backend/tests/test_eventos_multas_caixa_quickstart.py` (validação executável
ponta-a-ponta, sem servidor/DB). Falta o **Cenário 5 (US4)**, que é UI e exige
browser com a app a correr — segue o checklist abaixo.

## Pré-requisitos
- Backend: `cd backend && uvicorn server:app --reload --port 8001` (Postgres acessível).
- Frontend: `cd frontend && yarn start` (proxy mesma-origem via `setupProxy.js`).
- Login com conta `admin` ou com privilégio `manage_events`.
- Ter (ou criar) pelo menos um evento.

## Passos
1. Abrir o detalhe de um evento (página de Eventos → abrir um evento).
2. Abrir **"Finanças do evento"** (`EventFinanceDialog`).
3. **Registar despesa** com categoria (ex.: `Sala`, 8000, categoria *eventos*) → aparece na lista de despesas.
4. **Registar receita** (ex.: `Inscrições`, 12000) → aparece na lista de receitas.
5. Confirmar o **resultado** apresentado: receitas 12000 − despesas 8000 = **4000**.
6. **Gate Art. 54**: com `coaprovacao_limiar > 0` em finanças, tentar registar uma
   despesa acima do limiar → deve surgir **mensagem amigável em PT** a pedir um
   Acto de pagamento (não um erro cru / stack trace).

## Critérios de aceitação (Princípio VII)
- [ ] Secção financeira do evento funcional: registar despesa (com categoria), registar receita, listas e resultado visíveis.
- [ ] Mensagem amigável (PT) quando o gate Art. 54 recusa a despesa.
- [ ] **Design `frontend-design`**: botões neutros/**Floresta `#166534`** para ação positiva (Guardar/Registar); **sem vermelho sobre fundo escuro/colorido**; ≤1 botão primário por vista; sem dark mode.
- [ ] **Screenshot** do diálogo de finanças do evento (com despesa+receita+resultado) anexado ao registo da tarefa.

## Notas
- Componente: `frontend/src/.../EventFinanceDialog` (botão "Finanças do evento" na `EventosPage`, visível a admin/`manage_events`).
- Endpoints exercitados: `POST/GET/DELETE /api/events/{id}/expenses` e `/receitas`, `GET /api/events/{id}` (`resultado_financeiro`).
