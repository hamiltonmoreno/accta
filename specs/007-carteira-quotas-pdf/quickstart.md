# Quickstart — Validação (Exportar carteira de quotas em PDF)

## Pré-requisitos

```bash
# Backend
cd backend && uvicorn server:app --port 8001 --env-file .env
# Frontend
cd frontend && npx craco start         # (ver memory: local-dev-run)
```

- Sócio autenticado com lançamentos de quota/jóia (a DB de dev tem sócios seed).
- Um sócio **sem** lançamentos (ex.: conta técnica) para o caso vazio.

## Teste backend (pytest — sem servidor)

Um `tests/test_me_quotas_pdf.py` cobre o endpoint com `mock_db` + token forjado:

- **Own data + headers**: GET `/api/finances/me/quotas/pdf` como sócio →
  `200`, `Content-Type: application/pdf`, `Content-Disposition: attachment; filename=…pdf`,
  e o corpo começa com `%PDF`.
- **Total coincide com `/me/quotas`**: o total no documento corresponde ao `total_pago`
  (validar via os dados injetados; opcionalmente extrair texto).
- **Carteira vazia**: sócio sem lançamentos → `200` com PDF válido (`%PDF`), sem erro.
- **Não autenticado**: sem sessão → `401`.

```bash
cd backend && pytest tests/test_me_quotas_pdf.py -q
```

## Verificação em navegador (Princípio VII)

1. Login como sócio com quotas → abrir **Carteira**.
2. Acionar **"Exportar PDF"** → confirmar o **download** de
   `Carteira_Quotas_ACCTA_<nº>.pdf`. (SC-001)
3. Abrir o PDF: marca ACCTA, nome + n.º de sócio, data de emissão, tabela de
   lançamentos, **Total**, rodapé "uso interno — sem valor fiscal". (SC-002, FR-002/3/4)
4. Confirmar que os **lançamentos e o total coincidem** com a vista da Carteira no
   portal. (SC-003)
5. (Privacidade) Confirmar que só aparecem os lançamentos **do próprio**. (SC-004)
6. (Vazio) Como sócio sem lançamentos → PDF válido "Sem lançamentos", Total 0. (SC-005)

## Lint

```bash
cd backend && ruff check routes/finances.py
cd frontend && npx eslint src/pages/private/CarteiraPage.js src/utils/api.js --ext .js,.jsx --max-warnings=60
```

## Critérios (resumo)

- SC-001…SC-005 verdes; PDF *branded* ACCTA; só dados do próprio; vazio sem erro.
- Sem deps novas; sem schema/migração. Release → **Via B** (backend tocado).
