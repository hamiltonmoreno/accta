# Tarefa: Gestão de contas bloqueadas + fix do reset de senha

Origem: conta `kisoliveira@gmail.com` bloqueada (5 falhas/15 min); admin sem forma de
desbloquear ou reenviar reset; link do email de reset "não abre".

## Diagnóstico (confirmado no código)

- **Bug A — email de reset sem link.** `email_service.password_reset_email_html` recebe
  `reset_url` mas ignora-o; só mostra o token como "código a copiar". A página
  `/reset-password` só aceita `?token=` no URL, sem campo para colar código →
  o sócio não tem link para clicar. Sistemático (afeta todos os resets).
- **Bug B — fica bloqueado após redefinir.** `reset_password` não limpa `login_attempts`;
  o login verifica o bloqueio antes da senha (`auth_routes.py:59`) → 423 nos 15 min
  seguintes mesmo com a nova senha.
- **Feature ausente.** Sem endpoint/UI para admin desbloquear ou reenviar reset.

## Plano

### Backend
- [x] `email_service.py` — `password_reset_email_html`: botão "Redefinir palavra-passe"
      com `href=reset_url` (Floresta) + URL em texto como fallback; removido o "código".
- [x] `auth_routes.py` — extraído `issue_password_reset(email, name, request)`;
      `forgot_password` passa a usá-lo.
- [x] `auth_routes.py` — `reset_password`: `await reset_failed_logins(email)` no fim (limpa lockout).
- [x] `routes/admin.py` — `POST /admin/users/{id}/unlock` (limpa `login_attempts` + audit).
- [x] `routes/admin.py` — `POST /admin/users/{id}/send-reset` (usa `issue_password_reset` + audit).

### Frontend
- [x] `utils/api.js` — `adminAPI.unlockUser` + `adminAPI.sendPasswordReset`.
- [x] `AdminUsuariosPage.js` — 2 mutations + AlertDialog de confirmação no envio de email.
- [x] `usuarios/EditUserModal.js` — secção "Acesso à conta": botões Desbloquear + Enviar reset.

### Testes
- [x] `password_reset_email_html` contém o link (bug A) + degrada sem URL.
- [x] `reset_password` limpa `login_attempts` (bug B).
- [x] `unlock` limpa `login_attempts` + audit; 404 se não existir; 403 se não-admin.
- [x] `send-reset` cria `password_resets` + envia email (mock); 400 se não-ativo; 404; 403.
- [x] `test_idor_coverage` — classificadas as 2 rotas novas (`role` / `_require_manage_users`).

### Verificação
- [x] `ruff` limpo; `pytest -m unit` = 1683 passed (incl. 10 novos); `craco build` exit 0; eslint 0 erros.
- STOP: envio de email real a sócios só após confirmação do dono; deploy backend = Via B.

## Review
- 3 bugs+feature entregues na branch `feature/admin-desbloqueio-reset-senha` (a partir de develop).
- Descoberta-chave: bug A (link em falta) era sistemático — o template ignorava `reset_url`.
- Revisão adversarial `code-reviewer` em curso; commit após incorporar findings.
- Toca `backend/` → release develop→main precisa de **Via B**. Envio de email real = STOP do dono.
