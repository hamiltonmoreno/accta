# Quickstart — Validação Spec 016

Guia de validação ponta-a-ponta. Backend `uvicorn` + frontend `craco` (ver memória `local-dev-run`). Cada história é testável isoladamente.

## Pré-requisitos

```bash
cd backend && uvicorn server:app --reload --port 8001    # backend
cd frontend && yarn start                                # frontend (proxy mesma-origem)
```

Login admin de dev conforme `local-dev-run`.

## US1 — Privilégios legíveis (P1)

1. Entrar como admin → Utilizadores → abrir a ficha de um sócio.
2. **Esperado**: na secção «Privilégios», as **12** caixas têm rótulo legível — em particular «Emitir Parecer (Conselho Fiscal)», «Enviar Comunicados», «Comunicar entre Órgãos». Nenhuma célula em branco.

## US2 — Departamento como lista suspensa (P2)

**Inscrição pública:**
1. Abrir `/criar-conta` (sem sessão).
2. Campo «Departamento» é uma **lista suspensa** com 9 opções + «Outro».
3. Escolher um valor → submeter (com Turnstile) → pedido aceite. Sem departamento também é aceite (opcional).
4. Escolher «Outro» → aparece campo de texto → o texto é guardado como departamento.

**Admin (convite + edição):**
5. Utilizadores → «Convidar Sócio» → «Departamento» é a mesma dropdown + «Outro».
6. Editar um sócio cujo `department` legado NÃO está na lista → abre com «Outro» selecionado e o valor preservado no campo de texto (verificar SC-005: registo não se corrompe ao guardar).

**Backend:**
```bash
curl -s http://localhost:8001/api/auth/registration-options | jq '.departamentos'
# → array com os 9 departamentos
```

## US3 — Função completa no convite (P2)

1. Utilizadores → «Convidar Sócio».
2. **Esperado**: o seletor mostra **4** opções incluindo «Administrador», sob o rótulo «Função no Sistema».

## US4 — Aplicar predefinições do cargo (P3)

1. Utilizadores → editar um sócio **com cargo** (ex.: Tesoureiro / `dir_tesoureiro`).
2. Clicar «Aplicar predefinições do cargo».
3. **Esperado**: «Função no Sistema» passa a «Financeiro» e os privilégios passam a `manage_finances` + `view_audit_logs` (defaults do cargo). Ajustar manualmente e «Guardar» funciona.
4. Editar sem clicar → privilégios existentes inalterados.
5. Editar a conta técnica (`admin@controlador.cv`) → botão **não** aparece.

## Testes automatizados

```bash
cd backend && pytest tests/test_auth_routes.py -k registration_options
cd backend && pytest tests/test_identidade_cargos_models.py -k departamentos
cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60
cd frontend && yarn build   # craco build limpo
```

## Critério de pronto (Princípio VII)

- Backend: pytest verde (`registration-options` inclui `departamentos`; `DEPARTAMENTOS` estável).
- Frontend: as 4 histórias validadas no navegador pelo dono; `craco build` OK.
- Release com backend tocado ⇒ **Via B** + teste decisivo (`curl registration-options` no servidor).
