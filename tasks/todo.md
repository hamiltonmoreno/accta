# Tarefa: Remover autenticação de dois fatores (2FA/MFA)

Objetivo: remover por completo a funcionalidade de 2FA/MFA do Portal ACCTA e não
a reimplementar. Ramo: `feature/remove-mfa` (a partir de `develop`).

## Backend
- [x] Apagar `backend/mfa.py`
- [x] Apagar `backend/tests/test_mfa.py`
- [x] `models.py` — remover `UserBase.mfa_enabled`, `UserLogin.otp`,
  `Token.mfa_setup_required`, `MfaVerifyRequest`, `MfaDisableRequest`
- [x] `models.py` — MANTER `MFA_SECRET_FIELDS` (projeção defensiva de campos
  legados ainda presentes em docs de utilizador antigos; comentário atualizado)
- [x] `auth.py` — remover `MFA_PENDING_ALLOWED_PATHS` e os dois gates
  `mfa_pending` (`get_current_user` + `get_user_from_token`)
- [x] `routes/auth_routes.py` — remover import de `mfa`, o desafio MFA no login,
  os 4 endpoints `/auth/mfa/*`, e a lógica `mfa_setup_required` em
  `login` + `setup-account`
- [x] `requirements.txt` — remover `pyotp` e `qrcode` (não usados fora do MFA;
  o QR da carteira é frontend `react-qr-code`)
- [x] `tests/test_anomaly_alerts.py` — remover testes específicos de MFA e
  parâmetros MFA do helper `_user_doc`

## Frontend
- [x] Apagar `pages/MfaSetupPage.jsx`, `components/SetupMFA.jsx`,
  `components/ui/input-otp.jsx`
- [x] `utils/api.js` — remover `mfaAPI` e os ramos do interceptor
- [x] `contexts/AuthContext.js` — remover `mfaMandatory`/`mfaSetupRequired`
- [x] `App.js` — remover lazy import + rota `/mfa-setup` + guarda no `ProtectedRoute`
- [x] `pages/public/LoginPage.js` — remover o passo do 2.º fator
- [x] `pages/private/PerfilPage.js` — remover `SecuritySection` e órfãos
- [x] `lib/queryClient.js` — remover `queryKeys.mfa`
- [x] `CarteiraPage.js` usa `react-qr-code` (carteira) → MANTÉM no package.json

## Verificação
- [x] `ruff check .` — limpo
- [x] AST parse dos ficheiros editados — OK
- [x] `pytest tests/test_anomaly_alerts.py` — 7 passed
- [x] `pytest tests/test_auth_routes.py tests/test_auth_hardening.py` — 17 passed
- [ ] `pytest -m unit` — a correr
- [ ] `eslint` frontend

## Follow-ups (operacional, não bloqueiam o PR)
- `input-otp` fica como dependência não usada no `package.json` (removê-la
  exigiria atualizar o `yarn.lock`; fazer `yarn remove input-otp` quando
  conveniente, para não arriscar `--frozen-lockfile` no Vercel).
- Dados legados: docs de admin/financeiro (MFA era obrigatório) ainda contêm
  `mfa_secret`/`mfa_pending_secret`/`mfa_backup_codes`. A projeção
  `MFA_SECRET_FIELDS` impede a fuga; opcionalmente purgar com `$unset` em massa
  (migração de dados → STOP condition, requer OK do dono).
