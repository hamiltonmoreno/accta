# Quickstart — Validação (Lembrete informativo de quotas)

## Pré-requisitos

```bash
cd backend && uvicorn server:app --port 8001 --env-file .env
cd frontend && npx craco start
```

- Um admin/financeiro (gera quotas) e sócios ativos seed (recebem o lembrete).
- Um sócio com `quota_reminder_opt_out=True` para o caso de exclusão.

## Testes backend (pytest — sem servidor)

`tests/test_lembrete_quotas.py` (unit, `mock_db` + token):

- **Notifica os novos**: gerar quotas de um mês → `create_notification` chamado **uma
  vez por sócio** que recebeu quota nova, com link `/carteira`, corpo com valor + total
  (sem linguagem de dívida). (FR-001/002/003)
- **Opt-out excluído**: sócio com `quota_reminder_opt_out=True` não é notificado. (FR-004/005)
- **Técnicas/inativos excluídos**: conta `technical` e sócio `inativo` não recebem. (FR-005)
- **Idempotência**: re-gerar o mesmo mês → 0 novos → 0 notificações. (FR-006)
- **Sem quota no período**: sócio sem quota nova não recebe. (FR-008)
- **Email off**: nenhum envio de email no fluxo do MVP. (FR-007/SC-005)

```bash
cd backend && pytest tests/test_lembrete_quotas.py -q
```

## Verificação em navegador (Princípio VII)

1. Como **admin/financeiro**, gerar as quotas de um mês ainda não gerado.
2. Como **sócio** que recebeu quota, abrir o sino de notificações → ver o lembrete
   informativo (valor + total), tom não-cobrança, a abrir `/carteira`. (SC-001/003)
3. Em **Perfil → preferências**, desativar "Lembretes de quota" → gerar outro mês →
   confirmar que esse sócio **não** recebe. Reativar → volta a receber. (SC-006, FR-004)
4. Confirmar que **nenhum email** é enviado (só in-app). (SC-005)

## Lint

```bash
cd backend && ruff check routes/finances.py database.py models.py
cd frontend && npx eslint src/pages/private/perfil/EmailPrefs.js src/utils/api.js --ext .js,.jsx --max-warnings=60
```

## Critérios (resumo)

- SC-001…SC-006; tom informativo (sem inadimplência); opt-out respeitado; idempotente;
  email off. Sem deps novas; 1 campo aditivo. Release → **Via B**.
