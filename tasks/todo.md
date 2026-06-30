# Task — Integração Cloudflare Turnstile (anti-bot) nos formulários públicos

## Contexto
Widget Turnstile criado no Cloudflare (modo Gerenciado). Integrar nos
formulários sensíveis: **login, registo, recuperação de password e contacto**.

- Site Key (pública, vai no frontend): `0x4AAAAAAADs8kZrozSpCdz7g`
- Secret Key (confidencial): **NUNCA committada** — só no env do backend.

## Decisão de desenho — degradação graciosa (igual ao Web Push)
`TURNSTILE_SECRET` ainda **não está configurada em produção**. Fazer
*fail-closed* (503 sem secret) **partiria o login de todos** ao fazer deploy.
Por isso: **sem secret → verificação é no-op** (feature desligada); uma vez
configurada a secret, passa a exigir/validar o token. Sem alterações de
frontend para ligar. Na validação real (secret presente) é fail-closed:
403 token ausente/inválido, 502 se a Cloudflare estiver indisponível.

## Plano
### Backend
- [x] `backend/turnstile.py` — helper `verify_turnstile` + `turnstile_enabled`
- [x] `models.py` — `turnstile_token: str = ""` em UserLogin / RegistrationRequest / PasswordResetRequest
- [x] `routes/auth_routes.py` — `verify_turnstile` como 1.ª linha de login/register/forgot-password
- [x] `routes/contact.py` — `turnstile_token` no ContactRequest + verify no submit
- [x] `tests/test_turnstile.py` — unitários do helper + wiring das rotas (16 testes)

### Frontend
- [x] `components/Turnstile.js` — widget reutilizável (render explícito, reset via ref)
- [x] `pages/public/LoginPage.js` — widget + `turnstile_token` no payload
- [x] `pages/public/CriarContaPage.js` — idem
- [x] `pages/public/ForgotPasswordPage.js` — idem
- [x] `pages/public/ContactosPage.js` — idem

### Docs / env
- [x] `backend/.env.example` — `TURNSTILE_SECRET=` (placeholder, sem valor)
- [x] `CLAUDE.md` — tabela de env vars + nota Turnstile

## Verificação
- [x] `pytest tests/test_turnstile.py` → 16 passed
- [x] suite unit completa: **1363 passed** (falhas só em test_invite_auth.py = live/integration sem servidor, documentado)
- [x] `ruff check` + `ruff format` limpos nos ficheiros backend
- [ ] `eslint` / `build` frontend — bloqueado por flakiness de rede do proxy ao instalar devDeps; diffs revistos manualmente

## Review
- **Decisão central**: degradação graciosa (sem `TURNSTILE_SECRET` → no-op).
  Evita partir o login no deploy antes de a secret estar configurada; alinhado
  com o precedente do Web Push (VAPID). Quando ligada: 403 token ausente/inválido,
  502 Cloudflare indisponível. IP real via `cf-connecting-ip` (fallback client.host).
- **Segurança**: secret key NUNCA committada — só placeholder no `.env.example`.
  Site key é pública (frontend), com fallback embutido.
- **Token de uso único**: cada form reseta o widget no `catch` (novo token).
- Verify corre como 1.ª linha de cada handler (testes provam que corta antes de DB/email).
