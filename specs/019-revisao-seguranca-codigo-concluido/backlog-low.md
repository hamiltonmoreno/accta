# Backlog LOW + decisões de oráculos — Revisão de Segurança (spec 019, US5/T046)

Achados **LOW** (adiados por decisão do dono 2026-07-05: remediar HIGH+MEDIUM neste
ciclo, LOW registados) + as **decisões explícitas** exigidas pela FR-012 (oráculos de
enumeração/timing) e pela análise (bloqueio-de-conta-como-DoS). Cada item tem uma
**condição de reabertura** — o gatilho que o promove a um ciclo de trabalho.

## Decisões explícitas (FR-012 / U2) — não são "esquecimentos", são escolhas registadas

| # | Tópico | Decisão | Porquê | Reabrir se… |
|---|--------|---------|--------|-------------|
| O1 | **Oráculo de timing no login** (bcrypt só corre p/ utilizador existente → resposta mais rápida p/ email inexistente) | **Aceitar** | O `forgot-password` já é anti-enumeração (200 genérico); o rate-limit por-cliente (H3, corrigido) + lockout por-email limitam a exploração; um `dummy_verify` constante acrescenta custo a todo o login por um sinal fraco | Auditoria/Po exigir const-time; ou surgir enumeração observada |
| O2 | **Mensagens distintas no registo** (email já usado vs novo) | **Aceitar** | O registo é `pendente_aprovacao` (admin), não self-service instantâneo; a distinção é UX legítima (dizer "já tens conta"); o valor de enumeração é baixo num universo fechado de sócios | O registo passar a público/aberto |
| O3 | **Bloqueio-de-conta-como-DoS** (5 falhas/15 min trancam a conta → um atacante pode trancar a conta de um sócio conhecido) | **Aceitar (ceiling conhecido)** | Trade-off clássico lockout vs DoS-de-conta; a janela é curta (15 min) e auto-expira; alternativas (CAPTCHA-após-N, desbloqueio por email) são desproporcionadas para a base de utilizadores | Abuso observado; ou base de utilizadores crescer muito |

## Backlog LOW (adiado — remediar em ciclo futuro se a condição disparar)

| # | Achado | Condição de reabertura |
|---|--------|------------------------|
| L1 | Tokens (invite/reset) guardados em claro at-rest no jsonb | Migração de segurança de tokens; ou requisito de conformidade |
| L2 | `python-jose`/`passlib` são libs menos mantidas (alternativas: `pyjwt`/`argon2`) | `python-jose` ganhar CVE sem fix; ou reescrita de auth |
| L3 | COOP/CORP headers ausentes (isolamento de processo do browser) | Endurecimento de headers; ou uso de SharedArrayBuffer |
| L4 | `/api/health` sem rate-limit dedicado (agora sob o default 200/min global — já não é totalmente unthrottled) | Abuso do endpoint; hoje mitigado pelo default de US2 |
| L5 | Ficheiros de galeria pendente/rejeitada acessíveis por UUID direto (não-enumerável, mas não gated) | Requisito de privacidade de fotos não-aprovadas |
| L6 | `helpers.notify_admins`/varreduras usam `{"role":"admin"}` (gap análogo ao wall.py corrigido — só admins reais, sem privilégio) | Se um privilégio passar a conceder acesso admin sem o role |
| L7 | Tabnabbing (`target=_blank` sem `rel=noopener`) | **Já não aplicável** — verificado (T046): 0 casos, todos têm `rel="noopener noreferrer"` |
| L8 | Retenção/redação de `audit_logs.details` (PII acumula sem TTL) — M-AUDIT parte adiada | Política de retenção de dados; RGPD/pedido de eliminação |
| L9 | CSP em `Report-Only` — falta o **enforce** (M-CSP parte adiada) | Ação do dono após validar 0 violações no browser (promover a `Content-Security-Policy`) |
| L10 | `react-scripts` (CRA) EOL — árvore transitiva vulnerável só em build-time (M-CRA) | Migração para Vite; ou CVE runtime-alcançável (não build-only) |

> ~30 LOW no levantamento original: os acima são os materiais. Os restantes são
> observações de defesa-em-profundidade sem exploração prática (ex.: verbosidade de
> mensagens de erro internas, headers informativos) — cobertos pela postura geral.

## Infra (recomendação com STOP — parte no VPS, confirmada com o dono)

| # | Achado | Ação no repo | Ação no VPS (dono) |
|---|--------|--------------|--------------------|
| I1 | M-UPL-hdr — nginx serve `/uploads` sem os security headers da app | `deploy/nginx/accta.conf` documenta | Aplicar headers no bloco `/uploads` do edge |
| I2 | M-PROXY — confiança em `cf-connecting-ip`/XFF a validar no VPS | `rate_limit_key` já valida o peer contra `_TRUSTED_PROXY_NETS` | Confirmar que o edge (NPM) liga de um IP em `172.16/12` e põe XFF |
