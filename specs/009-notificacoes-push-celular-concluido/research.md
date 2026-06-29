# Research — Notificações Push no Celular (Web Push / PWA)

**Feature**: 009-notificacoes-push-celular | **Date**: 2026-06-28

Sem `NEEDS CLARIFICATION` na spec. As decisões abaixo registam o "porquê" das
escolhas técnicas (a implementação já existe no PR #362).

## D1 — Mecanismo de entrega: Web Push (VAPID) vs. push nativo (FCM/APNs)

- **Decision**: Web Push com VAPID, sobre o PWA existente.
- **Rationale**: O portal é uma web app React instalável como PWA; não há app
  nativa. Web Push é o único caminho que entrega à bandeja com a app fechada sem
  construir e distribuir apps nativas. No iOS funciona a partir do 16.4 quando
  instalado na Tela de Início.
- **Alternatives considered**: FCM/APNs nativos (exigiria apps nativas + lojas —
  fora de âmbito e desproporcionado); OneSignal/serviço externo (dependência de
  terceiros, custo, dados de sócios fora do sistema — rejeitado).

## D2 — Biblioteca de envio backend

- **Decision**: `pywebpush==2.0.0` (assina o pedido com a chave privada VAPID e
  cifra o payload).
- **Rationale**: Padrão de facto em Python para Web Push; encapsula VAPID + cifra
  (http-ece). `cryptography` já vem por `python-jose[cryptography]`.
- **Alternatives considered**: Implementar VAPID/ECE à mão (complexo, propenso a
  erro — viola Simplicity First). `requests` já está nas deps (usado por
  pywebpush). Nota operacional: `http-ece` (dep) só publica sdist — build sensível
  a setuptools recente; vigiar no CI.

## D3 — Onde disparar o push ("espelhar todas")

- **Decision**: Helper `dispatch_push(user_ids, title, body, link)` chamado nos
  **pontos únicos** de criação de notificações em `helpers.py`:
  `create_notification`, `notify_users`, `notify_all_active_users`
  (`notify_admins` passa por `notify_users`).
- **Rationale**: Espelha 100% das notificações sem tocar nas dezenas de
  call-sites espalhados pelas rotas. Minimiza superfície de alteração.
- **Alternatives considered**: Disparar em cada rota (duplicação, risco de
  esquecer); um worker/fila que lê a coleção `notifications` (infra extra,
  desproporcionado para o MVP).

## D4 — Não bloquear o event loop nem a criação da notificação

- **Decision**: `pywebpush` (síncrono, baseado em `requests`) corre em
  `asyncio.to_thread`, com `asyncio.gather` sobre as subscrições; falhas são
  engolidas (best-effort) e a notificação in-app nunca rebenta por causa do push.
- **Rationale**: Mantém o handler async não bloqueado; um broadcast resolve as
  subscrições numa única query `{$in: ids}` (sem N+1).
- **Alternatives considered**: Envio inline síncrono (bloqueia o request);
  fila/worker dedicado (infra extra). `create_task` fire-and-forget foi
  rejeitado por fragilidade (exceções engolidas, GC de tasks órfãs).

## D5 — Distribuição da chave pública VAPID

- **Decision**: Endpoint `GET /api/push/vapid-public-key` (autenticado) serve a
  chave; o frontend lê em runtime.
- **Rationale**: Permite rodar/definir a chave sem rebuild do frontend; mantém a
  config só no backend.
- **Alternatives considered**: `REACT_APP_*` no build (exigiria rebuild a cada
  mudança de chave — rejeitado).

## D6 — Degradação graciosa sem chaves VAPID

- **Decision**: `push_enabled()` é False sem o par VAPID; `dispatch_push` é no-op,
  endpoints respondem 503, e o toggle reage em conformidade. `pywebpush` é
  importado *lazy* (dentro das funções).
- **Rationale**: A organização pode fazer deploy antes de gerar as chaves; nada
  quebra e as notificações in-app continuam intactas. O import lazy evita que a
  ausência do pacote impeça o arranque.

## D7 — Segurança: anti-SSRF na subscrição

- **Decision**: `is_safe_push_endpoint()` exige HTTPS e rejeita
  localhost/`.local`/`.internal` e IPs literais privados/loopback/link-local/
  reservados; aplicado na subscrição e como defesa no envio.
- **Rationale**: O `endpoint` vem do cliente; sem validação, um sócio
  autenticado podia registar um URL interno e usar `/push/test` para forçar o
  servidor a fazer POST nesse alvo (SSRF — ex.: metadata cloud 169.254.169.254).
- **Alternatives considered**: Allowlist estrita de hosts de push (frágil — novos
  serviços/regiões partem-se). Resolução DNS no pedido para apanhar rebinding
  (latência/complexidade desproporcionada para o MVP; o bloqueio de IPs literais
  e hosts internos cobre o vetor óbvio).

## D8 — Ciclo de vida das subscrições

- **Decision**: Upsert por `endpoint` (único — um registo por dispositivo);
  remoção no `unsubscribe`; **poda automática** quando o envio devolve 404/410
  (Gone).
- **Rationale**: Mantém a tabela limpa e a taxa de falhas repetidas perto de 0,
  sem job de limpeza dedicado.

## D9 — Comportamento iOS e agrupamento na bandeja

- **Decision**: Detetar iPhone fora do PWA (`getIosNeedsInstall`,
  independente do suporte a push) e mostrar instrução de instalação; no service
  worker, **não** forçar um `tag` fixo (cada aviso aparece separado salvo se o
  backend enviar `tag`).
- **Rationale**: No iOS o `PushManager` nem existe fora do PWA — gating no
  suporte esconderia a dica a quem mais precisa. Um `tag` fixo colapsaria avisos
  distintos num só.
