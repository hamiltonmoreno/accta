# TODO — Sessão da Assembleia "ao vivo" (Categoria 2)

Spec: `tasks/spec-sessao-assembleia-ao-vivo.md`. Branch a criar:
`feature/assembleia-ao-vivo` (de `develop`). PRs pequenos por fase.

## Reconciliação com o código (a spec está stale no §1/F0)
A spec diz que o núcleo da governança "ainda não está implementado". **Está** —
governança F0–F7 merged. Logo o pré-requisito da F0 **já está satisfeito**:
- ✅ `governance.py`/`permissions.py`: `required_quorum`, `is_mesa_ag`,
  `is_voting_member`, `required_three_quarters/two_thirds/absolute_majority`.
- ✅ `routes/assembleias.py` (404 l.): create/list/get, `GET /quorum` (1ª/2ª),
  `POST /presencas` (representação ≤3, Mesa-não-representa, anti-dup,
  `voting_power`), `POST/GET /deliberacoes` (maioria + **comunicado oficial auto**),
  `POST /encerrar`.
- ✅ Colecções `assembleias`, `assembleia_presencas`, `assembleia_deliberacoes`.
- ✅ FE: `AdminAssembleiasPage.js`, sidebar, grupo `assembleiasAPI`.

**Natureza do que existe:** batch conduzido pela Mesa (folha de presenças + ata
agregada). A Cat 2 acrescenta a camada **participativa em tempo real** por cima —
sem partir o que existe (tudo aditivo).

## Decisões do dono (gates §15, fechadas 2026-05-27)
- **D1 — prova de presença online**: **clique/QR autenticado basta** (atribuível +
  datado = assinar a folha; fonte de verdade do quórum). Código de sessão = reforço
  anti-proxy opcional. **Sem** integração Meet/Zoom (scope próprio, fora).
- **D6 — voto secreto/nominal online**: **apoio administrativo** (não vinculativo
  por si; valor segue Regimento/ata). Não exige alteração estatutária.
- **D4 — limite 30 min (Art. 14)**: **aviso soft**; a Mesa encerra/estende com nota.
  Sem auto-fecho.
- **D7 — tempo real**: **polling SSE ~3s** (padrão do `notifications/stream`); zero
  deps novas; ok ~50–150 presentes. Redis = futuro (aberto).
- Defaults assumidos: **D2** só guardar/abrir `meeting_link` (iframe bloqueado);
  **D3** durações 180/60/120/120s **a confirmar com o Regimento**; **D5** braço-no-ar
  por contagem manual da Mesa; **D8** estender `routes/assembleias.py` (não novo
  módulo); **D9** representação online por registo manual da Mesa.

## Stop conditions desta spec
- Tratar voto secreto/nominal online como vinculativo → **não** (D6 fechou em apoio
  administrativo). Reabrir só com validação do Regimento.
- Email real a convidados com o `meeting_link` → fora de scope (stop em users reais).
- A 2.5 estende `AssembleiaDeliberacao`; o endpoint one-shot actual **já dispara
  comunicado oficial + email a todos os activos** (`dispatch_oficial_auto`). O novo
  ciclo abrir→votar→apurar tem de disparar **só no apurar/encerrar** — não duplicar.

---

## F0 — Infra de sessão + SSE por-assembleia ✅ (backend; aditivo, não depende dos gates)
- [x] `models.py`: + 10 campos de sessão em `Assembleia` (aditivos, `extra=ignore`):
      `modo` (default `online`), `meeting_link`, `meeting_provider`, `meeting_notes`,
      `session_phase` (default `fechada`), `current_item_id`, `check_in_code`,
      `check_in_code_expires_at`, `session_version=0`, `antes_ot_aberto_em`.
      + config de reunião em `AssembleiaCreate` + modelo `AssembleiaFaseUpdate`.
- [x] `routes/assembleias.py`: `_bump_session(id, extra)` (read-modify-write do
      `session_version`, aplica `extra` na mesma escrita) + `_session_snapshot(id)`
      (snapshot mínimo: version/phase/status/chamada/current_item_id/quorum).
- [x] `create_assembleia`: passa `modo`/`meeting_*` para o doc.
- [x] `GET /assembleias/{id}/stream` (SSE): `StreamingResponse` text/event-stream,
      loop `is_disconnected()` + `asyncio.sleep(3)`, emite snapshot quando
      `session_version` muda. **Auth `_extract_token` (cookie/header), NÃO `?token=`**
      (removido do `notifications/stream` por segurança). Headers anti-buffering.
      Subscrição: qualquer membro autenticado.
- [x] `POST /assembleias/{id}/fase`: transição só pela Mesa (`_require_convene`),
      ordem linear sem recuar; entra em `em_curso` a partir do check-in; regista
      `antes_ot_aberto_em` ao entrar em `antes_ot`; bump + audit `assembleia_fase`.
- [x] Testes (12 novos, 29/29 verdes): `_bump_session` incrementa+aplica extra;
      snapshot reflete fase/quórum; fase só Mesa, não recua, marca em_curso,
      regista abertura do antes_ot, bloqueia em encerrada; SSE 401 sem token /
      404 inexistente / emite snapshot uma vez. ruff check limpo.
- [ ] _(movido p/ F7)_ FE: hook `useAssembleiaStream(id)` — feito quando houver a
      sala que o consome (não entregar hook sem página que o renderize/verifique).

## F1 — 2.1 Check-in ao vivo + quórum em tempo real (Art. 5, 21) ✅ (backend) — dep: F0
- [x] `models.py`: `AssembleiaPresenca` + `method`/`can_vote`/`checked_in_at`/
      `source_article="21"` (defaults retro-compat: `method="mesa_manual"`);
      request models `AssembleiaCheckinRequest` + `AssembleiaCheckinScan`.
- [x] `POST /{id}/checkin` (membro autenticado): self check-in (`join_click`/
      `qr_meeting`/`self_code`); valida janela aberta (`_checkin_open`), é membro,
      código (se enviado) válido+não-expirado (`_code_valid`), anti-duplicado
      (`_existing_present_ids`), `voting_power`=1 se votante senão 0. **Representação
      NÃO entra aqui** — fica no `POST /presencas` da Mesa (decisão D9).
- [x] `POST /{id}/checkin/scan` (Mesa): `{qr_hash}` → `db.users.find_one(
      {qr_code_hash})` (igual a `/stats/validate`); regista `method=qr_scan`.
- [x] `POST /{id}/checkin/abrir|fechar` (Mesa): abrir gera/roda `check_in_code`
      (TTL 30 min) + entra em `checkin`/`em_curso`; fechar invalida o código.
- [x] `POST /{id}/segunda-convocatoria` (Mesa): `chamada_actual=2`,
      `quorum_required=required_quorum(n,2)`, recalcula `quorum_met`.
- [x] `GET /{id}/presencas` (Mesa). (`GET /quorum` reutilizado.)
- [x] `POST /presencas` actual = caminho `mesa_manual` (+ `can_vote`/`checked_in_at`);
      passou a usar `_finalize_checkin` → faz bump de sessão (SSE).
- [x] Audit: `assembleia_checkin`/`_scan`/`_abrir`/`_fechar`/`_segunda_convocatoria`.
      Notif `event` ao abrir check-in. Todas as mutações fazem bump de `session_version`.
- [x] Testes (19 novos, 48/48 verdes): self ok / honorário power 0 / código
      inválido / código expirado / já presente 409 / conta técnica / fora-de-janela;
      scan resolve por qr / 404 / 403 / fora-de-janela; abrir gera código+em_curso /
      403 / fechar invalida; 2ª convocatória recalcula 1/3 / já-em-2ª / 403; listar
      presenças Mesa / 403. ruff check limpo.
- _Nota D9:_ representação online via Mesa; self check-in regista só presença própria.

## F2 — 2.2 Fila de uso da palavra + cronómetros (Art. 21/27/28/29) ✅ (backend) — dep: F0, F1
- [x] `database.py`: + colecção `assembleia_palavra`; índices `assembleia_id` e
      `(assembleia_id, status)`.
- [x] `models.py`: `PalavraRequest` + `PalavraCreate`/`PalavraOrdenar`/`PalavraIniciar`;
      const `PALAVRA_DURACOES` = 180/60/120/120 (**a confirmar c/ Regimento — D3**).
- [x] Endpoints: `POST /{id}/palavra` (membro presente, 1 pedido activo), `DELETE
      /{id}/palavra/{qid}` (próprio ou Mesa), `POST /{id}/palavra/{qid}/ordenar|
      iniciar|terminar` (Mesa), `GET /{id}/palavra` (qualquer membro, ordenado por
      `ordem`→`requested_at`). `iniciar` arranca/estende cronómetro (`ends_at`); bump
      em cada mutação.
- [x] `_session_snapshot` estendido com bloco `speaking` (orador atual + `queue_len`)
      → o SSE da F0 propaga a fila em tempo real.
- [x] Testes (19 novos, 67/67 verdes): presente pede / protesto 60s / não-presente
      403 / sessão-não-em-curso 400 / pedido duplicado 409; retirar próprio / outro
      403 / Mesa qualquer / já-concluído 400; ordenar Mesa / socio 403; iniciar
      arranca cronómetro / override duração / já-concluído 400 / socio 403; terminar
      Mesa / não-a-falar 400 / socio 403; listar ordenado. ruff check limpo.

## F3 — 2.5 Modos de voto + conflito + voto separado (Art. 32) ✅ (backend) — dep: F0, F1
- [x] `database.py`: + `assembleia_votos` (unique `(deliberacao_id,user_id)`),
      `assembleia_voto_receipts` (unique `(deliberacao_id,voter_hash)`),
      `assembleia_voto_ballots` (`deliberacao_id`, **sem** `user_id`). Refactor:
      `_cast_secret_ballot` partilhado por `cast_ballot` (eleições) e
      `cast_assembleia_ballot`.
- [x] `models.py`: `AssembleiaDeliberacao` ganhou `voting_mode`/`item_id`/`subitem`/
      `conflitos_excluidos[]`/`status`/`apurado_em` (contagens passam a opcionais
      default 0 p/ permitir abertura sem votos). Novos request models:
      `AssembleiaDeliberacaoAbrir`, `AssembleiaVotoCast`, `AssembleiaContagem`;
      armazenamento: `AssembleiaVoto` (nominal), `AssembleiaVotoBallot` (secreto, sem
      user_id), `AssembleiaVotoReceipt` (secreto, voter_hash HMAC).
- [x] Ciclo novo **aditivo** (não parte o one-shot — frontend mantém-no): rotas em
      sub-paths distintos. **`POST .../deliberacoes/abrir`** (Mesa: mode/maioria/
      item/subitem/conflitos → `status=aberta`, **sem** comunicado),
      **`POST .../{did}/votar`** (votante presente não-excluído; nominal/secreto;
      braço-no-ar dá 400), **`POST .../{did}/registar-contagem`** (Mesa; só braço-no-ar),
      **`POST .../{did}/apurar`** (Mesa fecha + calcula + **só aqui** dispara
      comunicado oficial), **`GET .../{did}`** (Mesa vê lista nominal; secreto
      expõe só `votes_cast`). _Decisão da spec dizia reutilizar `POST .../deliberacoes`;
      mantive sub-paths distintos p/ não partir o one-shot que o FE chama (stop
      condition de rota removida)._
- [x] Apuramento por modo: **nominal** = base `present_power − Σ(voting_power
      excluídos)`, votos ponderados pelo `voting_power` do votante. **secreto** =
      **headcount** (1 boletim por membro; pesos de representação NÃO se aplicam,
      p/ preservar anonimato; coerente com D6 apoio administrativo — confirmar c/
      Regimento). **braço-no-ar** = agregado registado pela Mesa, mesma base de
      power. Maioria via helpers `required_absolute_majority/two_thirds/three_quarters`
      (universo p/ `qualificada_3_4_universo`). `voter_hash=HMAC(SECRET_KEY,
      f"{deliberacao_id}:{user_id}")` igual às eleições.
- [x] `_session_snapshot` ganha `open_vote` (deliberacao_id + voting_mode + ponto) —
      SSE da F0 propaga abertura de voto.
- [x] Testes (32 novos, 99/99 verdes): abrir (RBAC, sessão em curso, quórum, voto
      separado por subitem); votar nominal (presença, can_vote, exclusão, modo
      errado, duplicado 409, audit inclui escolha); votar secreto (boletim sem
      user_id, recibo com HMAC SHA-256 hex, ValueError→409, audit não inclui
      escolha); registar-contagem (RBAC, modo, base, valor); apurar (RBAC, status,
      nominal ponderado com exclusão, secreto headcount, braço usa agregado,
      comunicado dispara 1×); GET (Mesa vs sócio em nominal; secreto sem boletins).
      ruff check limpo; suite completa unit: 1076/1076.

## Remediação da review F0/F1 (resolvida nesta entrega) ✅
- [x] I1: `_finalize_checkin` faz `try/except asyncpg.UniqueViolationError → 409`;
      o índice passou a `UNIQUE INDEX ux_assembpres_assemb_user`.
- [x] I2: SSE `test_token_invalido_401` em `TestStream` cobre token inválido →
      `get_user_from_token` devolve None → 401.
- [x] I3: `AssembleiaCreate.meeting_link` rejeita esquemas não-http(s)
      (`javascript:`/`data:`); testes em `TestMeetingLinkValidation`.
- [x] I4: `get_assembleia` filtra `check_in_code`/`_expires_at` para não-Mesa.

## F4 — 2.3 Moções/requerimentos/recomendações (Art. 6, 26) ✅ (backend) — dep: F3
- [x] `database.py`: + `assembleia_mocoes`; índices `assembleia_id` e
      `(assembleia_id, status)`.
- [x] `models.py`: `MocaoSessao` (tipo `mocao|requerimento|recomendacao`,
      `votacao_imediata`, `deliberacao_id`, status submetida→em_discussao→em_votacao→
      aprovada/rejeitada/retirada) + `MocaoCreate` + `MocaoColocarVoto` (voting_mode/
      tipo_maioria/subitem/conflitos_excluidos com defaults).
- [x] Endpoints: `POST .../mocoes` (membro presente; `requerimento` ⇒
      `votacao_imediata=True` automático), `POST .../mocoes/{mid}/colocar-a-voto`
      (Mesa, exige quórum 2.ª chamada, cria deliberação F3 `status=aberta` ligada
      pelo título/texto/item, marca a moção `em_votacao` + `deliberacao_id`),
      `POST .../mocoes/{mid}/retirar` (proponente ou Mesa, só enquanto submetida/
      em_discussao), `GET .../mocoes` (qualquer membro autenticado).
- [x] Audit: `mocao_submetida`, `mocao_a_voto`, `mocao_retirada`. Bump em todas
      as mutações.
- [x] Testes (15 novos, 114/114 verdes): submeter (sessão em curso, presença,
      requerimento ⇒ votacao_imediata, moção/recomendação não); colocar-a-voto
      (RBAC, 404, status, quórum, cria deliberação aberta + linka moção); retirar
      (proponente ✓, Mesa ✓, outro 403, em_votacao 400); listar.
      Suite unit completa: **1091/1091** (+15 face à F3).

## F5 — 2.4 Antes da ordem de trabalhos + expediente (Art. 14) ✅ (backend) — dep: F1
- [x] `database.py`: + `assembleia_expediente`; índice `assembleia_id`.
- [x] `models.py`: `ExpedienteEntry` (tipo `correspondencia|voto_louvor|
      voto_congratulacao|voto_pesar`, `aprovado_por_aclamacao`) + `ExpedienteCreate`.
- [x] Endpoints: `POST .../expediente` (Mesa) + `GET .../expediente` (qualquer
      autenticado). Fase `antes_ot` e `antes_ot_aberto_em` vêm da F0; cronómetro
      30 min soft é client-side (D4). Audit: `expediente_registado`.
- [x] Testes (6 novos, 120/120 verdes): RBAC, 404, correspondência registada,
      voto-pesar por aclamação, listar; `antes_ot_aberto_em` só escrito 1ª vez.

## F6 — 2.6 Documentos ≥3 dias + convidados (Art. 20, 36) — dep: F0
- [ ] Doc da assembleia ganha `documentos: list[str]` (document_ids — **sem**
      colecção nova). `POST .../documentos` (Mesa/`manage_documents`): valida
      `now > data − MIN_DOC_ANTECEDENCIA_DIAS(=3)` → aviso (config `bloquear`) +
      audit `documento_anexado_tardio`. `GET .../documentos`.
- [ ] `database.py`: + `assembleia_convidados`; índice `assembleia_id`.
- [ ] `models.py`: `Convidado` (`can_speak`, `checked_in`, `invited_by`). Não conta
      p/ quórum nem vota; se `can_speak`, Mesa pode pô-lo na fila (F2).
- [ ] Endpoints: `POST .../convidados`, `GET .../convidados`,
      `POST .../convidados/{cid}/checkin` (Mesa). **Não** enviar email automático.
- [ ] Testes: anexo <3 dias avisa/bloqueia + audita; convidado fora do quórum/voto;
      `can_speak` entra na fila.

## F7 — Sala de sessão (frontend) — incremental por fase
- [ ] `pages/private/AssembleiaSalaPage.js` rota `/assembleias/{id}`
      (`<ProtectedRoute>`). Duas vistas na mesma página:
      - Consola da Mesa (`is_mesa_ag`/admin): fases, código+scan, ordenar/conceder
        palavra, abrir/apurar votos + braço-no-ar, moções/expediente/docs/convidados.
      - Participante (membro presente): "Entrar na reunião" (check-in + abre
        `meeting_link`) / QR da reunião, pedir palavra, votar, submeter moção, ver
        quórum/fila/voto ao vivo.
- [ ] `utils/api.js`: completar `assembleiasAPI` (checkin, stream, palavra, mocoes,
      deliberacoes ciclo novo, expediente, documentos, convidados).
- [ ] Reusar `QRCode`/lookup do validador, upload de documentos, TanStack+SSE.
      Design neutral-led + Carmesim, sem dark mode (skill `frontend-design`).
- [ ] Cronómetros + barra de quórum com estados claros.
- [ ] Testes FE: consola Mesa vs participante, countdown da palavra, barra de quórum,
      cartão de voto por modo, gating por `is_mesa_ag`.

## Ordem dentro de cada fase (spec §12)
models/campos → schema/índices (`ensure_schema`) → endpoints + RBAC + audit + bump
→ testes backend → frontend → testes FE → **ensaio manual** de uma sessão online
(check-in, quórum, palavra, voto) em dev com um link de reunião de teste.

---

## Review
_(a preencher no fim de cada fase: ficheiros tocados, testes, validação)_
