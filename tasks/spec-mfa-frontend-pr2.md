# Spec — MFA Frontend (PR2)

> **Origem**: PR2 do MFA TOTP. O backend (PR1, `spec-mfa-f2.md`, merged em
> `develop` via #120) está completo: endpoints, gate no login e enforcement
> server-side (claim `mfa_pending` → sessão limitada). Este spec é **só
> frontend** — dar UI ao que o backend já impõe. **Não altera o backend nem
> adiciona dependências** (`react-qr-code` e `input-otp` já instalados).

---

## 0. Decisões fechadas com o dono

- **Gestão de MFA**: secção no `PerfilPage` (não página dedicada).
- **2.º fator no login**: **inline** na `LoginPage` (revela campo OTP; a password
  fica no estado do form, não viaja entre rotas).
- **Enrolment obrigatório** (admin/financeiro sem MFA): **página `/mfa-setup`
  bloqueante** + redirect proativo; alinha com o backend que recusa (403) tudo
  fora do enrolment.

---

## 1. Contrato do backend (já em `develop` — não mexer)

- `POST /api/auth/mfa/setup` (autenticado) → `{ "secret": str, "otpauth_uri": str }`.
- `POST /api/auth/mfa/verify` (autenticado), body `{ "otp": str }` →
  `{ "backup_codes": [str×10], "access_token": str, "token_type": "bearer" }`.
  **Faz upgrade da sessão** (novo cookie completo, sem `mfa_pending`).
- `POST /api/auth/mfa/disable` (autenticado), body `{ "password": str }` →
  `{ "message": str }`. `403` se password incorreta.
- `GET /api/auth/mfa/status` (autenticado) →
  `{ "enabled": bool, "mandatory": bool, "backup_codes_remaining": int }`.
- `POST /api/auth/login` body aceita `otp?`; respostas:
  - `401 detail="mfa_required"` — password OK, falta OTP.
  - `401 detail="mfa_invalido"` — OTP/backup errado.
  - `200 Token{ access_token, token_type, user, mfa_setup_required }`.
- `GET /api/auth/me` → `User` com `mfa_enabled: bool`.
- **Enforcement**: sessão `mfa_pending` (admin/financeiro sem MFA) só acede a
  `/api/auth/mfa/{setup,verify,status}`, `/api/auth/me`, `/api/auth/logout`;
  tudo o resto → `403 detail="mfa_setup_required"`.

Regra de obrigatoriedade espelhada no frontend: `mandatory = role ∈ {admin, financeiro}`.

---

## 2. Camada API (`frontend/src/utils/api.js`)

Novo grupo `mfaAPI` (axios já tem `baseURL=.../api` + `withCredentials: true`):
```js
export const mfaAPI = {
  setup: () => api.post('/auth/mfa/setup'),
  verify: (otp) => api.post('/auth/mfa/verify', { otp }),
  disable: (password) => api.post('/auth/mfa/disable', { password }),
  status: () => api.get('/auth/mfa/status'),
};
```

---

## 3. AuthContext (`frontend/src/contexts/AuthContext.js`)

- O `user` (de `/auth/me` e do login) já traz `mfa_enabled`.
- Expor no value do contexto um derivado:
  ```js
  const mfaMandatory = ['admin', 'financeiro'].includes(user?.role);
  const mfaSetupRequired = !!user && mfaMandatory && !user.mfa_enabled;
  ```
- `login` mantém o contrato (chama `authAPI.login`, faz `setUser(res.data.user)`,
  devolve o user). O tratamento de `mfa_required` é no `LoginPage` (é um erro 401).
- Sem outras mudanças.

---

## 4. Componente partilhado `SetupMFA` (`frontend/src/components/SetupMFA.jsx`)

Wizard de 3 passos, recebe `onComplete()` (callback após ativar). Estado interno
`step ∈ {qr, confirm, backup}`.

- **Passo `qr`**: ao montar, `mfaAPI.setup()` → guarda `{secret, otpauth_uri}`.
  Renderiza `<QRCode value={otpauth_uri} />` (de `react-qr-code`) + o `secret` em
  texto monospace com botão **Copiar** (para apps que não leem QR). Botão
  **Continuar** → passo `confirm`.
- **Passo `confirm`**: `InputOTP maxLength={6}` (shadcn `input-otp`). Botão
  **Ativar** → `mfaAPI.verify(otp)`. Sucesso → guarda `backup_codes`, passo
  `backup`. Erro 400 → `toast.error('Código inválido')` (fica no passo).
- **Passo `backup`**: lista os 10 códigos (grid monospace). Botões **Copiar
  todos** e **Descarregar (.txt)**. Checkbox obrigatório **"Guardei os meus
  códigos de recuperação"** habilita o botão **Concluir** → `onComplete()`.

Notas:
- O componente é agnóstico do contentor (Dialog ou página) — quem o usa decide.
- `.txt` gerado client-side (Blob + download); nome `accta-mfa-backup-codes.txt`.
- Aplicar `frontend-design`: superfícies neutras, **≤1 botão primário Carmesim por
  passo** (o de avanço), restantes secundários; `Alert` para o aviso "guarde estes
  códigos — não voltarão a ser mostrados".

---

## 5. Secção no Perfil (`frontend/src/pages/private/PerfilPage.js`)

Nova card "Segurança / Autenticação de dois fatores", a seguir às Preferências de
Email (~linha 491). `useQuery`/efeito que chama `mfaAPI.status()` (ou usa
`user.mfa_enabled` + `mandatory` do role; usar `status()` para a contagem de
backups).

- **Estado**: badge **Ativo** (success) / **Inativo** (neutro) via `statusConfig`
  (sem cores inventadas); nota "Obrigatório para o seu cargo" se `mandatory`;
  "Códigos de recuperação restantes: N" se ativo.
- **Inativo** → botão **Ativar 2FA** abre `SetupMFA` num `Dialog`; `onComplete` →
  `refreshUser()` + fecha + `toast.success`.
- **Ativo + não-obrigatório** → botão **Desativar** abre `Dialog` com campo de
  password → `mfaAPI.disable(password)` → `refreshUser()` + toast. `403` →
  toast "Password incorreta".
- **Ativo + obrigatório** → **não** mostra "Desativar" (não o podem desligar);
  só o estado + nota.

---

## 6. Login inline (`frontend/src/pages/public/LoginPage.js`)

- Estado novo: `mfaStep` (bool), valor `otp`.
- `onSubmit`: `authAPI.login({ email, password, otp: otp || undefined })`.
  - **Sucesso**: `setUser(res.data.user)`; redirect: se
    `['admin','financeiro'].includes(user.role) && !user.mfa_enabled` →
    `/mfa-setup`; senão `/dashboard`.
  - **`401 detail="mfa_required"`**: `setMfaStep(true)` — revela `InputOTP` de 6
    dígitos; email/password ficam preenchidos/bloqueados; o utilizador insere o
    OTP e re-submete (mesmo handler).
  - **`401 detail="mfa_invalido"`**: `toast.error('Código de verificação inválido')`,
    permanece em `mfaStep`.
  - **`423`**: mantém o lockout/countdown atual.
  - Outros: `toast.error(detail || 'Erro ao fazer login')` (comportamento atual).
- UI: quando `mfaStep`, mostra o `InputOTP` + texto "Introduza o código da sua app
  de autenticação (ou um código de recuperação)"; o botão primário passa a
  "Verificar". Link/botão secundário "Voltar" repõe `mfaStep=false`.

---

## 7. Rota e guarda (`frontend/src/App.js`)

- Nova rota `/mfa-setup` → `<ProtectedRoute><MfaSetupPage /></ProtectedRoute>`
  (autenticada; a sessão `mfa_pending` já acede aos endpoints de enrolment).
- **Guarda em `ProtectedRoute`**: obter `mfaSetupRequired` do contexto; se
  `isAuthenticated && mfaSetupRequired && location.pathname !== '/mfa-setup'` →
  `<Navigate to="/mfa-setup" replace />`. (Não redirecionar quando já em
  `/mfa-setup`, para não criar loop.)

## 8. Página `MfaSetupPage` (`frontend/src/pages/MfaSetupPage.jsx`)

- Layout cheio, centrado, **sem** sidebar/navegação (não usa `PrivateLayout`):
  logótipo + título "Configure a autenticação de dois fatores" + texto curto a
  explicar que é obrigatório para o cargo.
- Renderiza `<SetupMFA onComplete={...} />`; `onComplete` → `refreshUser()` →
  `navigate('/dashboard')` (com `mfa_enabled` agora true, a guarda deixa passar).
- Botão **Sair** (logout) sempre visível (única saída sem configurar).
- **Não-dispensável**: sem links para outras rotas.

## 9. Interceptor axios (`frontend/src/utils/api.js`)

- Manter o ramo atual (401 em rota não-pública → force-logout → `/login`), mas
  **isentar** `detail ∈ {mfa_required, mfa_invalido}` (não fazer logout — são do
  fluxo de login, rota pública, já isenta; isenção explícita por robustez).
- **Acrescentar** ramo: `status === 403 && detail === 'mfa_setup_required'` em
  rota não-pública → `window.location.replace('/mfa-setup')` (rede de segurança
  caso a guarda proativa não apanhe; não faz logout).

---

## 10. Verificação (não há testes de frontend automatizados no projeto)

- `cd frontend && yarn build` → sem erros.
- `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60` → dentro do
  limite.
- **Walkthrough manual** (documentar no PR):
  1. Sócio: Perfil → Ativar 2FA → QR → confirma OTP → recebe backup codes →
     logout → login pede OTP inline → entra.
  2. Login com OTP errado → `mfa_invalido` → permanece no passo.
  3. Login com backup code → entra (e o backend consome-o).
  4. Admin sem MFA: após login → `/mfa-setup` bloqueante; tentar navegar para
     outra rota → continua bloqueado; configura → vai para dashboard.
  5. Sócio com 2FA → Perfil → Desativar (password) → desativado. Admin não vê
     "Desativar".
- Sem dark mode; Carmesim como acento único (`frontend-design`).

---

## 11. Fora de âmbito (futuro)

- Regenerar backup codes (o backend não tem endpoint dedicado; re-setup
  regenera-os).
- "Lembrar este dispositivo" / trusted devices.
- Itens menores herdados do backend para F3 (SSE não honra `mfa_pending`; audit
  sem IP/UA em verify/disable; lockout partilhado password↔OTP).

---

## 12. Review (preencher ao concluir)

- [x] `mfaAPI` + AuthContext `mfaMandatory`/`mfaSetupRequired` + `SetupMFA` +
  secção no Perfil + login inline + rota/guarda `/mfa-setup` + interceptor.
- [x] `yarn build` limpo (exit 0); eslint 0 erros / 37 warnings (limite 60),
  nenhum nos ficheiros novos/alterados.
- [ ] Walkthrough manual dos 5 cenários — **pendente** (requer servidor + DB
  com um admin; correr em staging/local antes do merge).
- **Desvio à letra do §6**: o campo de 2.º fator no login é um **input de texto**
  (não `InputOTP` de 6 slots), porque os backup codes têm o formato
  `xxxx-xxxx-xxxx-xxxx-xxxx` (24 chars) e não cabem em 6 dígitos — necessário para
  o cenário 3 do walkthrough. O `InputOTP` de 6 slots mantém-se no passo de
  confirmação do `SetupMFA` (TOTP puro).
- **Conclusão**: PR2 implementado em 8 ficheiros (3 novos: `mfaAPI` em `api.js` +
  `queryKeys.mfa`; `AuthContext`; `SetupMFA.jsx`; `MfaSetupPage.jsx`; `App.js`;
  `LoginPage.js`; `PerfilPage.js`). Sem alterações ao backend nem novas
  dependências. Dá UI completa ao MFA que o backend já impunha — ativação no
  Perfil, 2.º fator inline no login (TOTP/backup), enrolment obrigatório
  bloqueante para admin/financeiro — fechando a feature MFA de ponta a ponta.
