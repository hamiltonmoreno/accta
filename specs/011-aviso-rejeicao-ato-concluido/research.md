# Phase 0 — Research: Aviso de rejeição de Ato com o motivo

Não havia `NEEDS CLARIFICATION` em aberto (Q1 resolvida = motivo obrigatório). As
decisões abaixo fecham as escolhas técnicas com o critério da Simplicidade (Princípio I).

## D1 — Onde guardar o motivo da rejeição

- **Decision**: Guardar o motivo **na assinatura de rejeição**, dentro do array
  `Ato.assinaturas[]` (cada assinatura já tem `user_id`, `cargo`, `decisao`,
  `signed_at`; acrescenta-se `motivo`). A vista de detalhe lê o motivo da assinatura
  com `decisao == "rejeitado"`.
- **Rationale**: A assinatura já identifica **quem** rejeitou e **quando**; juntar o
  **porquê** no mesmo registo é o local natural e mantém um único ponto de verdade.
  **Zero schema novo, zero migração, zero alteração ao DAO** — o `sign_ato_atomic` já
  persiste a assinatura tal-e-qual a rota a constrói.
- **Alternatives considered**:
  - *Campo denormalizado `Ato.motivo_rejeicao` + `Ato.rejeitado_por`*: redundante (a
    info já está na assinatura) e implicaria uma 2.ª escrita fora do lock atómico.
    Rejeitado por duplicação e risco de incoerência.
  - *Coleção/tabela separada de motivos*: sobre-engenharia para um campo de texto.

## D2 — Obrigatoriedade e validação do motivo

- **Decision**: Ao rejeitar (`decisao == "rejeitado"`), o motivo é **obrigatório e
  não-vazio** após `strip()`. Rejeição sem motivo → **HTTP 400** com `detail` em PT.
  Ao **aprovar**, o motivo é ignorado (não exigido, não gravado).
- **Rationale**: Cumpre a Q1 (dono) e a SC-001 (aviso nunca sai sem razão). `strip()`
  fecha o caso "só espaços".
- **Alternatives considered**: opcional / opcional-com-incentivo — descartados pela
  escolha do dono (Q1=A).

## D3 — Limite de tamanho do motivo

- **Decision**: Máximo **500 carateres**; acima → **HTTP 400** com mensagem clara (sem
  truncar). Validação no modelo/rota (Pydantic + verificação explícita).
- **Rationale**: 500 carateres chegam para uma justificação acionável sem inflar o doc
  jsonb nem a notificação; coerente com FR-005 (recusar, não truncar).
- **Alternatives considered**: sem limite (risco de payloads/avisos enormes); 140
  (curto demais para justificar). 500 é o meio-termo pragmático.

## D4 — Formato do aviso ao proponente

- **Decision**: **Enriquecer o aviso de rejeição já existente** em `sign_ato` (não criar
  um segundo). Mensagem PT do tipo: «O ato que propôs foi rejeitado. Motivo: "<motivo>"».
  Mantém título, tipo `financeiro`, link `/financeiro/co-aprovacoes` e
  `exclude_id=quem_rejeitou` (evita auto-aviso quando o proponente é quem rejeita).
  Entrega in-app + espelho push reaproveitados (spec 009, via `notify_users`).
- **Rationale**: Um único aviso, agora útil. Sem novo canal nem email (fora do âmbito).
- **Alternatives considered**: aviso novo dedicado (duplicaria a notificação — viola
  FR-006); incluir o nome de quem rejeitou na mensagem (decidido **não** expor o autor
  no texto do aviso — o detalhe do Ato já mostra quem rejeitou; mantém o aviso focado no
  porquê).

## D5 — Auditoria

- **Decision**: Acrescentar o motivo ao `create_audit_log` **já emitido** na assinatura
  (no `details`, p.ex. `{"decisao": ..., "status": ..., "motivo": ...}`). Sem nova
  entrada de auditoria.
- **Rationale**: Princípio III (audit em ações) já cumprido; só enriquece o detalhe.

## D6 — Frontend (diálogo de rejeição)

- **Decision**: Em `CoAprovacoesPage.js`, a ação **Rejeitar** abre um confirm com uma
  **textarea** de motivo (obrigatória; contador até 500; botão de confirmação
  desativado enquanto vazia). Botão de confirmação destrutivo = **Carmesim sólido**
  dentro do diálogo irreversível (resto neutro), por `frontend-design`. O motivo é
  mostrado nos Atos já rejeitados (lido da assinatura de rejeição). `api.js`
  `atos.assinar` passa `{ decisao, motivo }`.
- **Rationale**: Fricção mínima e alinhada com o sistema de design; aprovar continua
  sem diálogo de motivo.
- **Alternatives considered**: `window.prompt` (fora do design system, sem limite/UX);
  página separada (excessivo).
