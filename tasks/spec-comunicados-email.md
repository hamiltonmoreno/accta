# Spec — Comunicados (disparo de email + in-app)

> **Status**: **F0–F3 IMPLEMENTADAS** (2026-05-24) no ramo `feature/comunicados-email`
> (backend manual + frontend + gatilhos automáticos de governança; suite verde, TDD).
> Falta apenas integrar: PR para `develop` após rebase (o ramo foi criado a partir
> de uma `develop` local 21 commits atrás de `origin/develop`). Fora de âmbito (futuro):
> webhooks Resend, editor rich-text, anexos, agendamento — ver §14.
> **Objetivo**: dar ao portal um canal de **comunicados** para a ACCTA comunicar
> com os sócios — um compositor único onde admins (e órgãos autorizados) escrevem
> uma mensagem, escolhem os destinatários e os canais (in-app e/ou email), e
> disparam; mais o espelhamento **automático** por email dos atos oficiais de
> governança.
> **Estado do sistema**: existe email transacional individual (Resend) e
> broadcast in-app; **não** existe envio de email em massa nem histórico de
> comunicados. Aditivo — não remove nada.
> **Base estatutária**: a convocatória de Assembleia Geral e as deliberações têm
> dever de chegar a todos os sócios → tipo `oficial` (sem opt-out). Avisos gerais
> → tipo `informativo` (com opt-out).

---

## 0. Âmbito

Um **comunicado** é um objeto composto que se "abre em leque" para um ou mais
canais. Cobre dois casos de uso:

| Caso | Origem | Canais | Tipo |
|---|---|---|---|
| **Manual** | admin / privilégio `send_comunicados` compõe | in-app e/ou email | `oficial` ou `informativo` |
| **Automático** (fase 2) | gatilhos de governança | in-app + email | `oficial` |

**Decisões confirmadas com o dono** (ver §13 para o registo completo):

1. Âmbito: **manual + automático**, faseado.
2. Canal: **comunicado unificado**, canais à escolha por envio (o
   `/notifications/broadcast` atual passa a ser, na prática, o canal in-app — mas
   **mantém-se** como rota, é aditivo).
3. Opt-out: **só para `informativo`**; `oficial` chega sempre a todos.
4. Quem envia: **admin OU privilégio `send_comunicados`** (overlay aditivo).
5. Destinatários: **segmentos predefinidos + seleção individual**.
6. Envio: **background + registo de Comunicado com estado/contagens** (Resend
   batch); webhooks de opens/bounces ficam fora de âmbito.
7. Conteúdo: **texto simples + CTA opcional** no template ACCTA; **sem anexos** no
   v1 (linka-se a documentos do portal).
8. Gatilhos automáticos: **só os oficiais de governança** — convocatória de AG,
   abertura de eleição/votação, publicação de deliberação/ata.

---

## 1. Specs relacionadas e dependências

- **`backend/email_service.py`** (implementado): `send_email(to, subject, html)`
  individual via Resend; `_base_template(content)` branded (cabeçalho Grafite +
  faixa Carmesim, rodapé); skip gracioso se `RESEND_API_KEY` ausente. **Reusa-se**
  o template; acrescenta-se rendering de comunicado + envio em batch.
- **`backend/helpers.py`** (implementado): `notify_users(ids, type, title,
  message, link)`, `notify_all_active_users(...)`, `create_audit_log(...)`,
  `members_of_orgao(orgao)`, `voting_member_ids()`. O **canal in-app reusa
  `notify_users`** com os ids resolvidos pelo segmento.
- **`backend/routes/notifications.py`** (implementado): `POST
  /notifications/broadcast` (admin-only, in-app, todos os ativos) — **mantém-se**;
  o novo domínio é o caminho rico. `GET /notifications/types` define os tipos
  in-app vivos: `geral|financeiro|evento|projeto|mural|votacao|documento|sistema`
  (acrescenta-se **`comunicado`** à lista).
- **`backend/governance.py` / `backend/permissions.py`** (implementado): fonte de
  verdade de órgãos/cargos/categorias e dos `privileges`. Acrescenta-se o
  privilégio `send_comunicados`. RBAC via `has_role_or_privilege(user,
  ("admin",), "send_comunicados")` (mesmo padrão de `view_audit_logs`).
- **`backend/routes/assembleias.py` / `eleicoes.py`** (implementado): os gatilhos
  automáticos da fase 2 ligam-se aqui (convocatória, abertura, publicação de
  deliberação/ata).
- **`backend/routes/contact.py`** (implementado): bom precedente de escape de HTML
  (`html.escape`) em conteúdo que vai para email — segue-se o mesmo no corpo do
  comunicado.
- **Modelo `users`** (implementado): segmentação via `role`, `status`,
  `account_type` (member|technical), `member_category`, `orgao`, `cargo`. O campo
  de opt-out é aditivo neste documento.

---

## 2. Diagnóstico do estado actual

- **Email**: só transacional individual (convite/reset/welcome/rejeição). Não há
  envio em massa, batch, nem histórico de envios.
- **In-app**: `notify_*` cobrem bem o canal interno; o broadcast é "todos os
  ativos" sem segmentação fina.
- **Não existe**: domínio de comunicados, segmentação de destinatários para envio,
  rastreio de estado/contagens, preferência de opt-out do sócio, página admin de
  comunicados, espelhamento de governança por email.
- **Resend**: envio é `asyncio.to_thread(resend.Emails.send, ...)` (síncrono na
  lib, off-thread). Para batch usa-se `resend.Batch.send` (até 100/chamada) com
  chunking; fallback para loop de `send_email` se a API de batch não estiver
  disponível.

---

## 3. Decisões transversais (arquitetura)

1. **Novo domínio `comunicados`** (coleção + `routes/comunicados.py`, prefixo
   `/api`), em vez de esticar `notifications`: as notificações são uma linha por
   sócio; um comunicado é **um** objeto que fan-out para N notificações in-app e N
   emails. Mantém o histórico limpo e o modelo per-utilizador intacto.
2. **Core de envio reutilizável**: a lógica de "resolver destinatários → criar
   in-app → disparar email em batch → fechar estado/contagens" vive numa função de
   serviço (`dispatch_comunicado(doc)`), chamada tanto pelo endpoint manual como
   pelos gatilhos automáticos da fase 2. Evita duplicação.
3. **Privacidade**: emails enviados **individualmente** (cada destinatário no seu
   próprio `to`) — nunca `To`/`CC` partilhado que exponha emails entre sócios.
4. **Segurança de conteúdo**: todo o conteúdo fornecido pelo utilizador é escapado
   no HTML (`html.escape`); o `\n` do corpo converte-se em parágrafos no servidor;
   a URL do CTA é validada (só `http`/`https`).
5. **Audit em toda a escrita** (`create_audit_log`); RBAC = `admin OR
   send_comunicados` em todos os endpoints de gestão.
6. **Aditivo e tolerante a falhas**: Resend ausente/falhado → email `skipped`/
   `failed` reflectido nas contagens, **o in-app é entregue na mesma**; o
   comunicado nunca "desaparece".
7. **Datas ISO-8601 string**; IDs `str(uuid4())`; sem SQL cru nas rotas; schema +
   índices em `ensure_schema()` (`database.py`).

---

## 4. Modelo de dados

### 4.1 Coleção nova `comunicados` (+1; esquema integrado atual: 51 tabelas)

```jsonc
{
  "id": "uuid",
  "subject": "Convocatória da Assembleia Geral Ordinária",
  "body": "Texto em parágrafos…",        // texto simples; \n → <p>
  "cta_label": "Ver convocatória",         // opcional
  "cta_url": "https://portal…/assembleias/123",  // opcional, http(s)
  "tipo": "oficial",                        // "oficial" | "informativo"
  "channels": ["in_app", "email"],          // 1+; subconjunto de {in_app,email}
  "segment": {
    "kind": "all_active",                   // all_active|role|orgao|member_category|manual
    "value": null,                          // ex.: "direcao" (orgao), "ordinario" (categoria), "socio" (role)
    "user_ids": null                        // [str] quando kind == "manual"
  },
  "notification_type": "comunicado",        // categoria do canal in-app
  "status": "enviado",                      // a_enviar|enviando|enviado|parcial|falhado
  "recipients_total": 42,
  "inapp_created": 42,
  "email_sent": 40,
  "email_failed": 2,
  "created_by": "uuid-do-autor",
  "created_at": "2026-05-24T10:00:00+00:00",
  "sent_at": "2026-05-24T10:00:07+00:00",   // null até concluir
  "error": null                             // mensagem se status=falhado
}
```

- **Estados**: `a_enviar` (criado, antes de a background task arrancar) →
  `enviando` → `enviado` (tudo ok) | `parcial` (alguns emails falharam) |
  `falhado` (erro geral, ex.: 0 destinatários resolvidos ou exceção).
- **Índices** (`ensure_schema`): `(doc->>'created_at')` desc, `(doc->>'created_by')`,
  `(doc->>'status')`.
- **`source`** (opcional): para comunicados automáticos, guardar
  `"source": {"kind":"assembleia_convocatoria","ref_id":"…"}` para rastreabilidade
  e para evitar duplo-disparo do mesmo gatilho.

### 4.2 Campo novo em `users` (aditivo, sem migração)

- `email_opt_out_informativos: bool` — `false`/ausente = **recebe** informativos.
  Ausente trata-se como `false` (compat com docs existentes).

### 4.3 Privilégio novo

- `send_comunicados` registado em `backend/governance.py` (lista de privileges) e
  reconhecido por `has_role_or_privilege`. Atribuível via gestão de utilizadores
  como qualquer outro overlay (ex.: à Mesa da AG / Direção).

---

## 5. Resolução de destinatários

Helper testável `async def resolve_recipients(segment, *, channel, tipo) ->
list[dict]` (devolve `{id, name, email}`):

1. **Base**: sócios com `status == "ativo"` e `account_type != "technical"`
   (contas técnicas como `admin@controlador.cv` nunca recebem comunicados).
2. **Filtro por `segment.kind`**:
   - `all_active` — todos os da base.
   - `role` — `role == segment.value`.
   - `orgao` — reusa `members_of_orgao(segment.value)` (`direcao`/`mesa_ag`/
     `conselho_fiscal`).
   - `member_category` — `member_category == segment.value`
     (`fundador|ordinario|honorario`).
   - `manual` — `id ∈ segment.user_ids` (intersectado com a base).
3. **Opt-out (só canal `email`)**: se `tipo == "informativo"`, **excluir** quem
   tem `email_opt_out_informativos == true`. Se `tipo == "oficial"`, **não**
   filtrar (dever estatutário).
4. **Email válido**: para o canal `email`, descartar (e contar à parte) quem não
   tem `email`.
5. O canal **in-app** ignora opt-out e email — todo o sócio elegível recebe
   notificação interna.

`recipients_total` = nº de destinatários únicos resolvidos (união dos canais
ativos). A contagem por canal é registada separadamente (`inapp_created`,
`email_sent`+`email_failed`).

---

## 6. Envio (background + contagens)

`async def dispatch_comunicado(comunicado_doc)` — core reutilizável:

1. Marca `status="enviando"`.
2. **Canal in-app** (se em `channels`): `notify_users(ids, type=notification_type,
   title=subject, message=<resumo do corpo>, link=cta_url)`; `inapp_created = len(ids)`.
3. **Canal email** (se em `channels`): renderiza HTML uma vez
   (`comunicado_email_html`), envia em **chunks de 100** via `send_comunicado_batch`
   (Resend `Batch.send`; fallback loop). Acumula `email_sent`/`email_failed`. Entre
   chunks, micro-pausa para respeitar rate-limits do Resend.
4. Fecha: `status` = `enviado` (sem falhas) | `parcial` (≥1 email falhou) |
   `falhado` (exceção/0 destinatários); grava `sent_at`, contagens e `error`.

- Disparo via **`fastapi.BackgroundTasks`** agendado pelo endpoint `POST
  /comunicados`, para o request responder de imediato com o comunicado em
  `a_enviar` e `recipients_total`.
- **Guarda de duplo-envio**: `dispatch_comunicado` só corre se `status ==
  "a_enviar"` (transição atómica para `enviando`).
- **Resend ausente**: `send_email` já devolve `{"status":"skipped"}` → contam-se
  como `email_failed` com `error="resend_not_configured"` mas o comunicado fica
  `parcial`/`enviado` conforme o in-app; nunca rebenta.

---

## 7. Endpoints (`backend/routes/comunicados.py`)

Todos exigem `has_role_or_privilege(user, ("admin",), "send_comunicados")` exceto
`PATCH /me/email-preferences` (qualquer sócio autenticado). Rate-limit apertado no
`POST /comunicados` (sugestão: `10/minute`).

| Método | Rota | Função |
|---|---|---|
| `POST` | `/comunicados` | Valida, resolve destinatários, cria doc (`a_enviar`), `create_audit_log`, agenda `dispatch_comunicado` em background; devolve o comunicado + `recipients_total`. |
| `POST` | `/comunicados/recipients/count` | Dry-run: dado um `segment` + `tipo` + `channels`, devolve as contagens previstas (in-app, email elegível, opt-out excluídos) — alimenta a "contagem viva" do compositor. |
| `GET` | `/comunicados` | Histórico paginado (`skip`/`limit`), ordenado por `created_at` desc; estado + contagens. |
| `GET` | `/comunicados/{id}` | Detalhe de um comunicado. |
| `GET` | `/comunicados/segments` | Metadados p/ o compositor: lista de segmentos disponíveis + contagem por cada (reusa `governance`/contagens de `users`). |
| `PATCH` | `/me/email-preferences` | Sócio liga/desliga `email_opt_out_informativos`. |

- **Modelos Pydantic** (`models.py`): `ComunicadoCreate` (subject, body, cta_label?,
  cta_url?, tipo, channels, segment, notification_type), `ComunicadoSegment`,
  `Comunicado` (resposta, sem expor nada sensível), `RecipientsCountRequest`,
  `EmailPreferencesUpdate`. Validações: `subject` não vazio (cap, ex.: 200),
  `body` ≥ 10 chars, `channels` ⊆ {in_app,email} e não vazio, `tipo` ∈
  {oficial,informativo}, `cta_url` http(s) se presente, `segment.kind` no enum e
  coerência (`value` obrigatório p/ role/orgao/member_category; `user_ids` p/
  manual).

---

## 8. Email rendering (`email_service.py`)

- `comunicado_email_html(subject, body_html, cta_label, cta_url) -> str` — usa
  `_base_template`; título = `subject`; corpo = parágrafos a partir do texto
  escapado (`html.escape` + `\n\n`→`<p>`, `\n`→`<br>`); botão CTA (Carmesim
  `#C7202F`) só se `cta_label` e `cta_url` presentes. Rodapé já indica envio
  automático; acrescentar nota de opt-out **apenas** em `informativo` ("Pode
  desativar estes avisos no seu perfil.").
- `async def send_comunicado_batch(recipients, subject, html) -> dict` — envia em
  chunks via Resend Batch (envios individuais), devolve `{"sent": n, "failed": m,
  "errors": [...]}`. Reusa `SENDER_EMAIL`/`APP_NAME`.

---

## 9. Frontend

- **`pages/private/AdminComunicadosPage.js`** (nova) — duas zonas:
  - **Compositor**: assunto; corpo (textarea); seletor de **tipo** (oficial/
    informativo) com nota do efeito no opt-out; seletor de **canais** (in-app /
    email / ambos); seletor de **segmento** (todos / role / órgão / categoria /
    manual) com multi-seleção de sócios quando `manual`; CTA opcional (label +
    URL); **contagem viva** de destinatários (chama `recipients/count`);
    **pré-visualização** do email; confirmação antes de disparar.
  - **Histórico**: tabela dos comunicados enviados (assunto, tipo, canais,
    segmento, estado, contagens, data, autor) com paginação.
- **Toggle de opt-out** no perfil/definições do sócio: "Receber comunicados
  informativos por email" (`PATCH /me/email-preferences`). Deixa claro que os
  comunicados oficiais chegam sempre.
- **`utils/api.js`**: novo grupo `comunicados` (`create`, `list`, `get`,
  `recipientsCount`, `segments`, `updateEmailPreferences`).
- **Sidebar admin**: entrada "Comunicados" (visível a admin **ou** quem tem
  `send_comunicados`).
- **Design**: segue o skill `frontend-design` (neutro, Carmesim como acento único,
  ≤1 botão primário por vista, sem dark mode). O botão de **disparar** é o primário
  da vista.

---

## 10. Fase automática — governança oficial (F3)

Reusa `dispatch_comunicado`. Gatilhos (cada um cria um comunicado `oficial`,
`channels=[in_app,email]`, `segment=all_active`, com `source` para rastreio e
guarda anti-duplicado):

| Gatilho | Onde | Comunicado |
|---|---|---|
| Convocatória de AG publicada | `routes/assembleias.py` | "Convocatória — {assembleia}", CTA p/ a página da assembleia |
| Eleição/votação aberta | `routes/eleicoes.py` (e abertura de poll relevante) | "Abertura de votação — {título}", CTA p/ votar |
| Deliberação/ata publicada | `routes/assembleias.py` | "Deliberações da AG de {data}", CTA p/ a ata |

- O disparo automático **não** depende de o admin fazer nada; respeita a mesma
  resolução de destinatários (mas como é `oficial`, ignora opt-out).
- **Anti-duplicado**: antes de disparar, verificar se já existe comunicado com o
  mesmo `source.kind`+`ref_id`; se sim, não reenviar.
- Falha do email **não** bloqueia a ação de governança (o disparo é
  best-effort/background; a publicação da convocatória/ata conclui na mesma).

---

## 11. Segurança & RBAC

- **RBAC**: `admin OR send_comunicados` em toda a gestão; 403 caso contrário; 401
  sem token. `PATCH /me/email-preferences` é self-service (qualquer autenticado, só
  o próprio).
- **Audit**: `create_audit_log` em cada criação/disparo (ação `enviar_comunicado`,
  detalhes: tipo, canais, segmento, `recipients_total`).
- **XSS/HTML**: escape de `subject`/`body`/CTA no rendering; nada de HTML cru do
  utilizador (o v1 é texto simples por decisão).
- **Validação de URL** do CTA (só http/https) — evita `javascript:` etc.
- **Privacidade**: envios individuais (sem To/CC partilhado).
- **Rate-limit** no `POST /comunicados` (endpoint poderoso).
- **Contas técnicas** nunca são destinatárias.
- **Não-stop-conditions**: a coleção nova e o campo opt-out são **aditivos** (não
  migram nem dropam dados); o `/notifications/broadcast` **não** é removido. O
  envio de email em massa a sócios reais é uma ação sensível — confirmar com o dono
  antes de qualquer teste contra endereços reais (usar emails dummy em dev).

---

## 12. Testes (`backend/tests/`)

Unit/in-process (sem servidor/DB), com `mock_db` e fixtures de role/token:

- **Resolução de destinatários**: cada `kind`; exclusão de `technical`; exclusão
  de opt-out só em `informativo`; `oficial` ignora opt-out; descarte de sem-email
  no canal email.
- **RBAC**: admin e `send_comunicados` passam; `socio` sem privilégio → 403; sem
  token → 401.
- **Rendering**: escape de conteúdo malicioso no corpo/assunto; CTA só aparece com
  label+URL; rejeição de `cta_url` não-http(s).
- **Dispatch/contagens** (mock Resend): `enviado` vs `parcial` vs `falhado`;
  contagens in-app/email; Resend ausente → não rebenta, in-app entregue.
- **Guarda de duplo-envio**: 2.º `dispatch` no mesmo doc é no-op.
- **Opt-out endpoint**: liga/desliga e reflete-se na resolução.
- **F3**: gatilho de governança cria comunicado `oficial` e a guarda
  anti-duplicado impede reenvio.
- **Validações Pydantic**: channels vazio, tipo inválido, segment incoerente → 422.

---

## 13. Faseamento

- **F0 — Fundações**: `models.py` (modelos de comunicado/segmento/prefs); tabela
  `comunicados` + índices em `ensure_schema`; campo `email_opt_out_informativos`
  (aditivo); privilégio `send_comunicados` em `governance.py`. Atualizar a
  contagem integrada de tabelas no CLAUDE.md.
- **F1 — Backend manual**: `resolve_recipients`, `comunicado_email_html` +
  `send_comunicado_batch` no `email_service.py`, `dispatch_comunicado` (core),
  `routes/comunicados.py` (POST/GET/count/segments) + `PATCH /me/email-preferences`,
  audit, rate-limit. Acrescentar `comunicado` aos tipos in-app. **Testes F1.**
- **F2 — Frontend manual**: `AdminComunicadosPage` (compositor + histórico), toggle
  de opt-out no perfil, grupo `comunicados` em `api.js`, entrada na sidebar.
- **F3 — Automático (governança)**: refactor já feito em F1 (core reutilizável);
  ligar gatilhos em `assembleias.py`/`eleicoes.py` com `source` + anti-duplicado.
  **Testes F3.**

Cada fase é uma unidade entregável e testável independentemente; F1 já deixa o
core pronto para F3.

---

## 14. Fora de âmbito (YAGNI / futuro)

- Webhooks do Resend (opens/bounces) e **estado por-destinatário**.
- **Editor rich-text** (HTML WYSIWYG) e **anexos** (v1 é texto + link a documentos).
- **Mapa de gatilhos configurável** por admin (F3 tem o conjunto fixo de
  governança).
- **Rascunhos e agendamento** (compor agora, enviar depois).
- **Preferências por categoria** (v1 tem um único opt-out de informativos).
- Conjunto alargado de gatilhos automáticos (eventos/documentos/financeiro).

---

## 15. Registo das decisões (perguntas confirmadas)

| # | Pergunta | Decisão |
|---|---|---|
| 1 | Âmbito | Manual + automático (faseado) |
| 2 | Modelo de canal | Comunicado unificado, canais à escolha |
| 3 | Opt-out | Só informativos; oficiais sempre |
| 4 | Quem envia | Admin + privilégio `send_comunicados` |
| 5 | Destinatários | Segmentos predefinidos + seleção individual |
| 6 | Envio & rastreio | Background + registo c/ estado/contagens (Resend batch) |
| 7 | Conteúdo | Texto simples + CTA opcional no template ACCTA; sem anexos |
| 8 | Gatilhos automáticos | Só governança oficial (convocatória AG, abertura eleição/votação, deliberações/atas) |
