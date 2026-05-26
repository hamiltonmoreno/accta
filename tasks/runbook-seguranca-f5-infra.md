# Runbook — F5: Infra de Segurança (operador)

> **Âmbito**: a fase **F5** da `spec-verificacao-seguranca-saas` (§7, §9, §10) +
> o hand-off de infra do **F4** (§8.1). **Nada disto é código da app** — são
> passos que o **operador** aplica no Supabase / alojamento e confirma. Cada
> item: **Objetivo → Passos → Verificação → Ressalvas**.
>
> Estado: app **ainda não em produção, sem dados reais** → é o momento ideal
> para aplicar estes controlos antes do go-live.
>
> ⚠️ Itens marcados **GATE** precisam de confirmação explícita do dono antes de
> executar (são stop conditions do `CLAUDE.md`).

---

## F5.1 — Imutabilidade do audit log (hand-off do F4)

**Objetivo**: o `audit_logs` é append-only. A app já não tem rota que apague/
altere audit logs, e o F4 (#125) acrescentou tamper-evidence por HMAC que deteta
**modificação**. Falta fechar a **remoção/apagamento** ao nível da BD — a camada
correta para isso.

**Porque o HMAC sozinho não chega**: quem tem escrita direta na BD pode alterar
uma linha **e remover o `entry_hash`**; a entrada passa a "não verificável"
(`GET /api/audit-logs/verify` reflete-o e nega o `ok`, mas não consegue provar
que foi adulterada). Bloquear UPDATE/DELETE na BD elimina esse vetor.

**✅ Já AUTOMÁTICO no código** (PR do F5.1): `ensure_schema()` em `database.py`
(`_AUDIT_IMMUTABILITY_DDL`) instala, em cada arranque (idempotente), um trigger
`BEFORE UPDATE OR DELETE OR TRUNCATE` no `audit_logs` que **rejeita** qualquer
mutação. Não há SQL para o operador correr — só **verificar**. Robusto ao
owner-bypass (um trigger trava toda a gente, ao contrário de GRANT/REVOKE que
não trava o dono da tabela). Provado contra Postgres real: INSERT permitido,
UPDATE/DELETE bloqueados.

**Verificação do operador** (após o deploy que inclua o F5.1):

```sql
-- (a) triggers presentes:
SELECT tgname FROM pg_trigger WHERE tgrelid = 'public.audit_logs'::regclass
  AND tgname LIKE 'trg_audit_logs%';
-- → trg_audit_logs_immutable, trg_audit_logs_no_truncate

-- (b) mutação é rejeitada (deve dar ERRO 'audit_logs is append-only'):
UPDATE public.audit_logs SET doc = doc WHERE pk = (SELECT pk FROM public.audit_logs LIMIT 1);
DELETE FROM public.audit_logs            WHERE pk = (SELECT pk FROM public.audit_logs LIMIT 1);
```
E confirmar que a app continua a **inserir** audit logs (ação admin → nova
entrada em `GET /api/audit-logs`) e que `GET /api/audit-logs/verify` dá `ok`.

**Camada complementar (opcional, defesa em profundidade)** — só tem efeito se o
role da app **não** for o dono da tabela:
```sql
-- REVOKE UPDATE, DELETE, TRUNCATE ON public.audit_logs FROM <role_da_app>;
```

**Ressalvas**:
- O trigger **não** afeta a app: a app só faz `INSERT`+`SELECT` em `audit_logs`;
  `ensure_schema()` apenas faz `CREATE … IF NOT EXISTS`; o purge oportunista
  (`_TTL_PURGE`) **não** inclui `audit_logs`. Verificado no código.
- Um **superuser** pode contornar com `SET session_replication_role='replica'` —
  o trigger eleva muito a fasquia vs. um `DELETE` simples, mas não substitui
  limitar quem tem credenciais de superuser/`service_role`.
- Se algum dia for preciso **purga** legítima (a retenção é indefinida, F5.5),
  é uma operação deliberada de superuser (desativar o trigger, purgar, reativar)
  — registar em mudança controlada.

---

## F5.2 — TLS ≥ 1.2 + redireção (§7)

**Objetivo**: todo o tráfego em HTTPS, TLS ≥ 1.2, HTTP→HTTPS. (HSTS **já está no
código** em produção — `server.py`; CORS recusa arrancar com `*` em produção.)

**Passos**:
- Confirmar no terminador TLS (Nginx / Render / Vercel) que **TLS 1.0/1.1 estão
  desativados** e que há **redireção 80→443**.
- Confirmar as env vars de produção: `CORS_ORIGINS` (lista explícita, sem `*`),
  `FRONTEND_URL`, `SECRET_KEY`, `DATABASE_URL` (pooler Supabase 6543, transaction
  mode), `RESEND_API_KEY`, `SENDER_EMAIL`.

**Verificação**:
```bash
# Protocolos: TLS1.2 deve ligar; TLS1.0/1.1 devem ser recusados.
openssl s_client -connect <dominio>:443 -tls1_2 </dev/null 2>/dev/null | grep -i protocol
openssl s_client -connect <dominio>:443 -tls1   </dev/null    # deve falhar
# Redireção e cabeçalhos:
curl -sI http://<dominio>/        # → 301/308 para https
curl -sI https://<dominio>/api/   # → Strict-Transport-Security, X-Frame-Options: DENY,
                                  #   X-Content-Type-Options: nosniff, CSP, Referrer-Policy
# Cookie de sessão (após login): Set-Cookie com HttpOnly; Secure; SameSite
```

**Ressalvas**: HSTS só é emitido quando `ENVIRONMENT=production`; confirmar essa
env var no deploy. Não ativar HSTS com `includeSubDomains`/`preload` sem
certeza de que todos os subdomínios servem HTTPS.

---

## F5.3 — Backups e recuperação de desastres (§9)

**Objetivo**: perda de dados recuperável; restauro testado **antes** do go-live.

**Passos**:
- Confirmar no Supabase: **backups automáticos** ativos e, se o plano o
  permitir, **PITR** (Point-In-Time Recovery); registar a **janela de retenção**.
- Definir e documentar **RPO** (perda máxima aceitável, ex.: 24h sem PITR / ~min
  com PITR) e **RTO** (tempo máximo de reposição).
- **Testar um restauro** para um projeto/branch de *staging* pelo menos uma vez;
  registar o tempo real (valida o RTO) e que os dados vieram íntegros.

**Verificação**: restauro de staging concluído + `GET /api/audit-logs/verify`
no ambiente restaurado a devolver `ok:true` (prova de integridade do trilho após
o restauro — desde que o `SECRET_KEY` seja o mesmo; ver F5.4).

**Ressalvas**: o restauro tem de incluir a configuração de env vars; um restauro
de dados com `SECRET_KEY` diferente **invalida** sessões, segredos MFA e a
verificação HMAC do audit (ver F5.4).

---

## F5.4 — Rotação do `SECRET_KEY` — **GATE (D6)**

**Objetivo**: poder rodar o `SECRET_KEY` (ex.: suspeita de fuga) sem partir o
sistema. **Hoje não há suporte multi-chave** → rodar o `SECRET_KEY` é uma
operação disruptiva.

**Consequências de rodar o `SECRET_KEY` (estado atual)**:
- **Sessões**: todos os JWT ficam inválidos → todos os utilizadores re-login.
- **MFA**: os segredos TOTP estão cifrados (Fernet derivado do `SECRET_KEY`) →
  deixam de decifrar; os utilizadores com MFA têm de **re-inscrever** (admins/
  financeiro são obrigatórios). Os backup codes (hash SHA-256) continuam válidos.
- **Audit log (F4)**: a verificação HMAC das entradas **anteriores** à rotação
  passa a falhar (`/verify` marca-as como adulteradas/não-verificáveis), porque
  a chave HMAC deriva do `SECRET_KEY`.

**Procedimento (disruptivo, atual)** — só com **confirmação do dono**:
1. Anunciar janela de manutenção (re-login + re-inscrição MFA).
2. Substituir `SECRET_KEY` no ambiente; reiniciar o backend.
3. Avisar utilizadores MFA para re-inscrever; gerar baseline novo do audit
   (as entradas pré-rotação ficam como "legado não verificável").

**Opção recomendada (evita a disrupção) — requer CÓDIGO (não feito; GATE D6)**:
suportar `SECRET_KEY` + `SECRET_KEY_PREVIOUS` com janela de graça (verificar JWT/
HMAC com ambas; re-cifrar segredos MFA no próximo login). É um PR dedicado —
confirmar com o dono se querem antes de qualquer rotação.

**Ressalva**: não rodar o `SECRET_KEY` "por higiene" sem necessidade — neste
sistema o custo é alto. É um **stop condition**.

---

## F5.5 — Retenção do audit log

**Objetivo / Estado**: **retenção indefinida** (decisão do dono, 2026-05-26) —
sem purga automática; `audit_logs` **não** está em `_TTL_PURGE`. É o
comportamento atual; nada a aplicar, só **documentar** a política para o registo
de conformidade.

---

## Checklist (colar no PR de release / issue de operação)

- [ ] F5.1 Triggers de imutabilidade do `audit_logs` (automáticos via `ensure_schema`) **verificados** em prod (pg_trigger presentes; UPDATE/DELETE falham; INSERT da app OK; `/verify` dá `ok`)
- [ ] F5.2 TLS≥1.2 + redireção 80→443 + cabeçalhos de segurança confirmados; env vars de prod (CORS sem `*`, `ENVIRONMENT=production`)
- [ ] F5.3 Backups/PITR confirmados; RPO/RTO documentados; **restauro de staging testado**
- [ ] F5.4 **GATE D6** — decidir com o dono: adiar rotação OU implementar suporte multi-chave antes de rodar
- [ ] F5.5 Política de retenção (indefinida) registada

> Fecho da `spec-verificacao-seguranca-saas`: F0/F2/F3/F4 em código (MERGED em
> `develop`); F1 cancelado; **F5 = este runbook (operador)**. Ver
> `tasks/spec-verificacao-seguranca-saas.md` §14 (stop conditions) e §15 (gates).
