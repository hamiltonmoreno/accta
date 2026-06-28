# Contracts — N/A

Esta feature **não altera nenhum contrato de API**. Não há endpoints novos,
alterados ou removidos; nenhuma mudança de request/response.

O frontend consome contratos **já existentes**, sem os modificar:

- `GET /api/ranking/leaderboard` — já devolve `entries[].photo_url` e `me.photo_url`
  (US3 usa-os; nada muda no contrato).
- `GET /api/ranking/me` — inalterado.
- Sessão do utilizador autenticado (perfil) — inalterado; US5 é apresentação.

Por isso não existem ficheiros de contrato neste diretório. Qualquer alteração de
API exigiria reabrir o plano e reavaliar o Constitution Check (RBAC + Audit).
