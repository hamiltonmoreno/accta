# Plano — F3: Alertas de anomalia (+ itens herdados do F2)

Spec: `tasks/spec-verificacao-seguranca-saas.md` §8.2 + §12 (F3). Branch
`feature/seguranca-f3-alertas` (de `develop`). PR → `develop` (GitFlow).

## Decisões do dono (gates confirmados 2026-05-26)
- **Eventos**: só **(a) lockout** + **(c) escalada de role/privileges**. Diferir
  (b) IPs distintos e (d) picos 4xx/429 (precisam de agregação stateful).
- **Canal**: **só in-app/SSE** via `notify_admins` (sem email — evita a stop
  condition de emails reais; sem fadiga). Reutiliza infra existente.
- **Itens herdados do F2**: **incluir os 3** neste PR.

## Achado durante o planeamento
- Item herdado #3 ("lockout partilhado password↔OTP") **JÁ ESTÁ FEITO**:
  `auth_routes.py:121` já chama `record_failed_login` no ramo `mfa_invalido`.
  Memória/L13 estava stale nesse ponto — nada a fazer (verificado).

## Trabalho

### Alertas (§8.2 a + c)
- [ ] `helpers.py`: `record_failed_login` passa a **devolver `bool`** = "esta
  falha cruzou o threshold agora" (count == LOCKOUT_THRESHOLD). Aditivo —
  callers que ignoram o retorno não quebram. Alerta dispara **uma vez** (na
  transição), não em cada falha subsequente já-trancada.
- [ ] `helpers.py`: `alert_admins_account_locked(email)` → `notify_admins(
  "system", …)`. `alert_admins_privilege_escalation(actor_id, target_name,
  old_role, new_role, old_privs, new_privs)` → alerta (excl. ator) quando role
  sobe para {admin,financeiro,moderador} OU ganha privilégios.
- [ ] `auth_routes.py::login`: nos 2 ramos de falha (password L84, OTP L121),
  capturar o bool e, se transição, `await alert_admins_account_locked(email)`
  antes do `raise`.
- [ ] `admin.py::promote_user` e lado `to` do `transfer`: chamar
  `alert_admins_privilege_escalation` após o update+audit. (Proclamação
  eleitoral em `eleicoes.py` **fica de fora** — fluxo democrático normal, já
  notificado, não é anomalia.)

### Itens herdados do F2 (#1, #2)
- [ ] `auth.py::get_user_from_token`: honrar `mfa_pending` → `return None` (SSE
  e get_optional_user negam sessão limitada; enrolment não precisa de SSE).
- [ ] `auth_routes.py::mfa_verify` e `mfa_disable`: adicionar `request: Request`
  à assinatura e passar `request=request` ao `create_audit_log` (IP/UA).

### Testes — `tests/test_anomaly_alerts.py` (unit, mock_db)
- [ ] 5.ª falha de login dispara `notify_admins` (lockout); 4.ª não.
- [ ] falha de OTP que cruza o threshold dispara o alerta.
- [ ] `promote_user` p/ role elevada / +privilégios dispara escalada (excl. ator).
- [ ] `get_user_from_token` com token `mfa_pending` → `None`; sem pending → User.
- [ ] `mfa_verify`/`mfa_disable` chamam `create_audit_log` com `request` (IP/UA).

## Verificação
- [ ] `ruff check .` limpo; `pytest tests/test_anomaly_alerts.py tests/test_mfa.py
  tests/test_auth_routes.py tests/test_auth_hardening.py tests/test_admin*.py` verde.
- [ ] Sem regressões; sem email; sem mudança Pydantic não-aditiva; sem tocar `main`.

## Stop conditions
Emails reais (não disparar); push a `main` (nunca). `notify_admins` é in-app — OK.
