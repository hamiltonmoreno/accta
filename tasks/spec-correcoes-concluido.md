# SPEC — Correção de Problemas (Análise de Saúde 2026-05-18)

_Especificação de execução para resolver todos os achados da análise de saúde do Portal ACCTA._
_Origem: auditoria de arquitetura + segurança + qualidade (3 subagentes paralelos)._

> **Escopo**: corrigir bugs funcionais, falhas de segurança, violações de convenção e dívida arquitetural prioritária.
> **Restrição**: app ainda **não está em produção** → sem migração de dados / downtime. Mudanças de schema são índices idempotentes via `ensure_schema()`.
> **Regras do projeto**: PT em texto de usuário; Pydantic em todo body; `async/await`; audit log em toda ação admin; status só `ativo`/`inativo`/`pendente_convite`; testes `pytest` antes de "done".

---

## Decisões a confirmar antes da Fase 1

- [ ] **D1 — Ciclo de vida de enquetes**: qual é o fluxo correto? Proposta: `rascunho → aberta → encerrada`, transição via `PATCH /polls/{id}/status` (admin), abertura automática opcional por `start_date`, encerramento por `end_date` ou ação manual. _Confirmar se deve haver auto-abertura agendada ou só manual._
- [ ] **D2 — Endpoint de status legado** (`PATCH /users/{id}/status`): manter validando, ou **remover** e migrar o frontend (`usersAPI.updateStatus`) para `PATCH /users/{id}`? Proposta: validar agora (não-quebra), depreciar depois.
- [ ] **D3 — SVG em logos**: sanitizar (`defusedxml`+`bleach`) ou **rejeitar SVG** e aceitar só raster? Proposta: rejeitar SVG (mais simples, menor superfície).
- [ ] **D4 — Estratégia de PRs**: um PR por fase (recomendado) vs. um PR por item. Itens que tocam >3 arquivos ou exigem design entram em PR próprio com plano dedicado.

---

## Fase 1 — 🔴 CRÍTICO (feature quebrada)

### C1 — Ciclo de vida de enquetes inexistente
- **Problema**: enquetes nascem `status="rascunho"` e nenhum endpoint muda para `aberta`/`encerrada`. `vote()` aceita voto em rascunho sem checar status/janela; `report.py:24` e `activity.py:142` filtram `aberta`/`encerrada` → sempre 0.
- **Causa raiz**: falta endpoint de transição + falta guard em `vote()`.
- **Solução**:
  1. `PATCH /api/polls/{id}/status` (admin) — body Pydantic `PollStatusUpdate` (`status ∈ {aberta, encerrada}`); valida transição (`rascunho→aberta`, `aberta→encerrada`); `create_audit_log`.
  2. Em `vote()` (`polls.py:51`): rejeitar (`400`) se `poll.status != "aberta"` ou fora de `[start_date, end_date]`.
- **Arquivos**: `backend/routes/polls.py`, `backend/models.py`, `backend/routes/__init__.py` (se necessário), testes.
- **Aceitação**: criar enquete → `rascunho`; abrir → votável; votar em `rascunho`/`encerrada` → `400`; relatório/atividade refletem enquetes abertas; audit log gerado.
- **Testes**: `tests/test_polls.py` — transições válidas/inválidas, voto fora de janela, RBAC (só admin abre).
- **Risco/dep**: depende de **D1**. Toca model + rota → PR próprio com mini-plano.

### C2 — Voto duplicado (race condition)
- **Problema**: guard `find_one`→`insert_one` sem constraint única; requisições concorrentes inserem 2 votos.
- **Solução**: índice único parcial em `user_votes` por `(doc->>'user_id', doc->>'poll_id')` em `_INDEX_DDL` (`database.py`); capturar conflito de insert em `vote()` e retornar `400` "já votou".
- **Arquivos**: `backend/database.py` (`_INDEX_DDL`), `backend/routes/polls.py`.
- **Aceitação**: dois votos concorrentes do mesmo usuário/enquete → exatamente 1 persistido, 2º recebe `400`.
- **Testes**: teste de inserção concorrente / violação de unique tratada.
- **Risco/dep**: DDL idempotente, não-destrutivo. Verificar que não há votos duplicados pré-existentes antes de criar o índice (seed/dev sem dados → ok).

---

## Fase 2 — 🟠 ALTO

### A3 — I/O de arquivo síncrono em handler async
- **Problema**: `open().write()` de até 10 MB dentro de `async def` trava o event loop.
- **Solução**: `await asyncio.to_thread(_write_bytes, path, contents)` (ou `aiofiles`) em ambos os pontos.
- **Arquivos**: `backend/routes/upload.py:51`, `backend/routes/gallery.py:203`.
- **Aceitação**: upload grande não bloqueia requisições concorrentes; comportamento de gravação idêntico.
- **Testes**: upload OK persiste arquivo; (opcional) teste de concorrência.

### A4 — Link de reset/convite com origem controlável
- **Problema**: sem `FRONTEND_URL`, link emailado é montado de `Origin`/`Referer` → phishing com token válido.
- **Solução**: fail-closed — exigir `FRONTEND_URL`; se ausente, validar origem contra `CORS_ORIGINS` (allowlist) antes de usar; senão erro de config (não enviar link envenenado).
- **Arquivos**: `backend/routes/auth_routes.py:243`, `backend/routes/admin.py:67`.
- **Aceitação**: `Origin` forjado nunca aparece no link; `FRONTEND_URL` setado → usado; ausente + origem não-allowlisted → falha controlada.
- **Testes**: `tests/test_auth.py`/`test_admin.py` — origem maliciosa rejeitada, origem allowlisted aceita.

### A5 — Stored XSS via upload de SVG (logos)
- **Problema**: SVG aceito pula `Pillow.verify()`, só checa prefixo; SVG com `<script>` servido site-wide.
- **Solução** (conforme **D3**): rejeitar SVG em `logos` (remover de `_MAGIC_PREFIXES`/categorias) **ou** sanitizar com `defusedxml`+`bleach`. Adicional: servir uploads com `Content-Disposition: attachment` ou `X-Content-Type-Options: nosniff` reforçado.
- **Arquivos**: `backend/routes/upload.py:15`, `backend/file_validation.py:58`.
- **Aceitação**: SVG com script → `400`; raster válido → OK.
- **Testes**: `tests/test_file_validation.py` — SVG malicioso rejeitado.
- **Risco/dep**: depende de **D3**.

### A6 — Audit log ausente em ações admin (convenção)
- **Problema**: faltam `create_audit_log` em ações admin/moderação.
- **Solução**: adicionar `await create_audit_log(...)` em: `gallery.py` linhas 103/115/129/237/264 (criar/editar/excluir álbum, aprovar/rejeitar foto), `wall.py:114` (pin), `notifications.py:126` (criar notificação).
- **Arquivos**: `backend/routes/gallery.py`, `backend/routes/wall.py`, `backend/routes/notifications.py`.
- **Aceitação**: cada ação gera registro em `audit_logs` com ator/alvo/ação.
- **Testes**: assert de audit log nos testes de gallery/wall/notifications.

### A7 — Stat de eventos ativos sempre 0
- **Problema**: `stats.py:16` filtra `status:"active"` mas `Event` não tem campo `status`.
- **Solução**: contar eventos futuros: `{"date": {"$gte": now_iso}}` (consistente com formato ISO do DAO).
- **Arquivos**: `backend/routes/stats.py:16`.
- **Aceitação**: contagem reflete eventos com data futura.
- **Testes**: `tests/test_stats.py` — evento futuro conta, passado não.

---

## Fase 3 — 🟡 MÉDIO

### M8 — Status sem validação
- **Problema**: `users.py:161` (legado) e `users.py:106` (`admin_update_user`) aceitam status arbitrário (permite `inadimplente`, proibido).
- **Solução**: validar `status ∈ {ativo, inativo, pendente_convite}` em **ambos**; legado conforme **D2**.
- **Arquivos**: `backend/routes/users.py`. **Testes**: status inválido → `400`.

### M9 — Invite token vazado no body
- **Problema**: `admin.py:80` retorna `setup_url` com token (vai p/ logs/histórico).
- **Solução**: não retornar o token no body (já foi enviado por email); retornar só o path.
- **Arquivos**: `backend/routes/admin.py:80`. **Testes**: resposta não contém token.

### M10 — Sem rate limit em `POST /contact`
- **Solução**: `@limiter.limit("5/minute")` em `submit_contact`.
- **Arquivos**: `backend/routes/contact.py:56`. **Testes**: 6ª requisição/min → `429`.

### M11 — `X-Forwarded-For` confiado incondicionalmente
- **Solução**: confiar em XFF só quando `request.client.host` for proxy conhecido; senão usar `client.host`. Documentar suposição Nginx.
- **Arquivos**: `backend/helpers.py:57`. **Testes**: XFF ignorado quando origem não-confiável.

### M12 — `KeyError → 500` em finanças
- **Solução**: trocar acesso direto `t["category"]`/`t["type"]`/`t["amount"]` por `.get()` com default em summary/dre/csv.
- **Arquivos**: `backend/routes/finances.py` (~226, 272, 508). **Testes**: doc sem `category` não quebra.

### M13 — Bodies `dict` sem Pydantic em projects
- **Solução**: criar `ProjectExpenseCreate`/`ProjectCommentCreate`/`ProjectMilestoneCreate` e tipar os endpoints.
- **Arquivos**: `backend/models.py`, `backend/routes/projects.py` (453/393/548/577). **Testes**: payload inválido → `422`.

### M14 — `notify_all_active_users` corta em 500
- **Solução**: paginar/remover cap no caminho de broadcast.
- **Arquivos**: `backend/helpers.py:125`. **Testes**: broadcast com >500 ativos atinge todos.

---

## Fase 4 — 🟢 BAIXO / Higiene

- **B15** — Senha mínima 8 (Pydantic `Field(min_length=8)`) — `auth_routes.py:151,263`, `models.py`.
- **B16** — Header CSP em `SecurityHeadersMiddleware` — `server.py:24`.
- **B17** — Parar de retornar JWT no body após depreciar Bearer legado — `auth_routes.py:96,193` (decisão futura, não-quebra agora).
- **B18** — Email de boas-vindas realmente não-bloqueante (`BackgroundTasks`) — `auth_routes.py:184`.
- **B19** — Limpar mortos: `pop("_id")` (DAO nunca cria), retorno de `record_failed_login` descartado.

---

## Fase 5 — 🏗️ Dívida arquitetural (track separado, não bloqueia Fases 1–4)

> Mudanças amplas; cada uma é um épico com plano próprio. **Não** misturar com correções de bug.

- **AR1** — Empurrar `$group/$sum/$sort/$limit` para SQL no `_aggregate` (`database.py:591`). Maior ganho de escala.
- **AR2** — Congelar contrato suportado do DAO + matriz de testes do tradutor query/aggregation contra Postgres real.
- **AR3** — Dependency central `require_roles(...)` + teste que garante guard de auth em todo router (substitui ~66 checks inline).
- **AR4** — Centralizar (de)serialização datetime ISO↔datetime no `_rehydrate` do DAO; remover ~40 helpers duplicados.
- **AR5** — Guard de consistência: varredura de validação de documentos por coleção no startup/CI + runner de migração versionada junto a `ensure_schema()`.

---

## Estratégia de PRs (recomendada)

| PR | Conteúdo | Risco |
|----|----------|-------|
| PR-1 | C1 (ciclo de enquetes) — plano próprio | Médio (model+rota) |
| PR-2 | C2 (voto duplicado + índice) | Baixo |
| PR-3 | A3, A4, A5, A6, A7 (segurança/convenção alto) | Médio |
| PR-4 | M8–M14 (médios) | Baixo |
| PR-5 | B15–B19 (higiene) | Baixo |
| Épicos | AR1–AR5 — um plano/PR cada | Alto |

**Ordem de execução**: Fase 1 → 2 → 3 → 4. Fase 5 em paralelo por outro track.

## Gates de verificação (toda fase)

- [ ] `cd backend && ruff check . && ruff format --check .`
- [ ] `cd backend && pytest` (verde, incluindo testes novos do item)
- [ ] `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60` (se tocar frontend)
- [ ] Nenhuma violação de Stop Condition do CLAUDE.md sem confirmação do usuário
- [ ] Diff revisado: só toca o necessário, sem efeitos colaterais

## Stop Conditions aplicáveis (confirmar com usuário)

- C1 toca model Pydantic (`Poll`/novo request) → confirmar que não quebra documentos existentes.
- C2 adiciona índice único → confirmar ausência de duplicados pré-existentes.
- Qualquer push para `main` → confirmar antes.
- Se um "item simples" passar a tocar >3 arquivos → parar e replanejar.

---

## Execução (registo)

> Auditado item-a-item contra o código em 2026-05-21. As correções (Fases 1–4)
> já estavam implementadas — em larga medida pela track paralela
> `spec-correcoes-2-codex` (concluída) e por trabalho subsequente.

- **Fase 1** — ✅ C1 (`PATCH /api/polls/{id}/status` + guard de janela/status no
  `vote()`), C2 (índice único `ux_votes_user_poll` em `database.py`).
- **Fase 2** — ✅ A3 (`asyncio.to_thread` na escrita de upload/galeria), A4
  (`resolve_link_base` fail-closed contra `CORS_ORIGINS`), A5 (SVG rejeitado em
  `logos` — raster-only), A6 (audit logs em galeria/mural/notificações), A7
  (eventos futuros por `date >= now`).
- **Fase 3** — ✅ M8 (`status not in USER_STATUSES`), M9 (token fora do body),
  M10 (`@limiter.limit("5/minute")` em contacto), M11 (XFF só atrás de proxy),
  M12 (`.get()` em finanças), M13 (`Project*Create` Pydantic), M14 (broadcast
  sem cap).
- **Fase 4** — ✅ B16 (CSP), B18 (email de boas-vindas em `BackgroundTasks`).
  **B15 (password 6→8) — CANCELADO** por decisão do dono: o mínimo fica em **6**.
  B17 (parar de devolver JWT no body) — adiado por design (depende de depreciar
  o Bearer legado), B19 — higiene menor.
- **Fase 5 (AR1–AR5, dívida arquitetural)** — **NÃO feita**; track separado de
  épicos (cada um com plano/PR próprio), explicitamente não-bloqueante.
- **Decisões**: D1 = ciclo manual (sem scheduler) ✅; D2 = endpoint legado
  `/users/{id}/status` mantido e a validar ✅; D3 = rejeitar SVG ✅.
