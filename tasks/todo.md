# TODO — Finanças Cat 4.1: Dupla assinatura / co-aprovação (Art. 54)

Spec `spec-controlos-financeiros` §4 (Feature 4.1) + §8 frontend. Fecha a spec
(restava F3+F4; F5 `--apply` é STOP). Branch `feature/financas-coaprovacao`,
empilhada sobre `feature/financas-joia` (que tem F0+jóia).

Decisões do dono (gates §12 confirmados 2026-05-23):
- **§12.4** Proponente **pode** assinar (a sua assinatura conta; 1 assinatura/utilizador).
- **§12.2** Gate de pagamentos **opt-in**: `coaprovacao_limiar` 0 = desligado; acima
  de limiar positivo a despesa exige Ato aprovado (aplicado em `POST /finances/transactions`).
- **§12.8** Contratos (vinculativos não-pagamento) **só registados** (anexo p/ fase futura).
- **§12.3** Default estatutário: pagamento exige Tesoureiro; vinculativo não.

## Backend
- [x] `models.py`: `ATO_TIPOS`/`ATO_STATUSES`/`ATO_DECISOES` + `AtoCreate`/`AtoSign`/`AtoExecute`/`Ato`
- [x] `atos_rules.py` (puro, sem DB): `requisitos_for_tipo(tipo)` + `evaluate_status(assinaturas, requisitos)`
      (rejeição fecha; ≥2 Direção incl. Presidente; Tesoureiro se exigido; Presidente conta como Direção)
- [x] `database.py`: `atos` em `COLLECTIONS` + índices `(status,created_at)` e `tipo`
- [x] `routes/atos.py` (prefixo `/atos`): POST criar · GET listar (`?pendentes_para_mim`/`?status`/`?tipo`) ·
      GET `{id}` · POST `{id}/assinar` · POST `{id}/executar` · POST `{id}/cancelar`
      (RBAC: criar=admin/Direção; assinar=Direção; executar=Tesoureiro/admin; cancelar=proponente/admin)
- [x] `routes/__init__.py`: registar `atos_router` (5 rotas confirmadas em `/api/atos`)
- [x] `routes/finances.py`: gate de pagamentos em `create_transaction` (despesa > limiar exige Ato; limiar 0 = off)
- [x] Audit (`ato_criado`/`ato_assinado`/`ato_aprovado`/`ato_rejeitado`/`ato_executado`/`ato_cancelado`)
      + notif (`financeiro`) aos assinantes da Direção na criação e ao proponente em aprovado/rejeitado

## Frontend
- [x] `utils/api.js`: grupo `atosAPI` (prefixo `/atos`)
- [x] `lib/queryClient.js`: chaves `atos.list`/`atos.byId`
- [x] `pages/private/CoAprovacoesPage.js`: secção "à minha assinatura" + todos (filtro de estado), criar,
      cartão de assinaturas (Direção X/2 · Presidente · Tesoureiro), botões Aprovar/Rejeitar/Executar/Cancelar
- [x] `App.js`: rota `/financeiro/co-aprovacoes` (ProtectedRoute; gate de conteúdo na própria página)
- [x] `PrivateLayout.js`: item de menu "Co-aprovações" (`match: 'direcao'` + roles/privilégios financeiros) + título
- [x] AuthContext já expõe `isDirecao`/`isPresidente`/`isTesoureiro` — usados directamente

## Testes & gates
- [x] `tests/test_atos.py` (34 casos): regras puras (vinculativo/pagamento; rejeição; assinante duplicado;
      Presidente conta como Direção) + endpoints (criar/assinar/executar/cancelar; gate de pagamentos)
- [x] `pytest -m unit` → **762 passed** (era 728; +34, sem regressões) · `ruff check`/`format` ✓ ·
      `eslint` (meus ficheiros) ✓ · `npm run build` ✓

## Review
- **Fonte única da regra**: `atos_rules.py` (sem DB) — `evaluate_status` deriva órgão/cargo via
  `permissions`/`governance` (keys canónicas), usado pela rota e pelos testes → sem drift.
- **Requisitos congelados na criação** (`requisitos_for_tipo`): alterar o default estatutário no futuro
  não muda actos já abertos. Presidente conta como 1 dos 2 da Direção (espelhado no cartão do frontend).
- **Gate não-quebra** (decisão §12.2): `coaprovacao_limiar` 0 (default) = desligado; o lançamento directo
  de despesas em `finances.py` fica intacto. Só com limiar positivo é que despesas acima exigem Ato.
  `executar` insere a despesa directamente (com `ato_id`), contornando o gate por construção.
- **STOP respeitado**: sem migração de dados, sem alterar `quota_amount`/`joia_multiplier`, sem emails novos;
  todos os campos Pydantic são aditivos/opcionais (já existiam na fundação F0).
- **RBAC**: criar=admin/Direção; assinar=Direção (Presidente/Tesoureiro incluídos); executar=Tesoureiro/admin;
  cancelar=proponente/admin; ver=finanças(admin/financeiro/CF)/Direção. Backend impõe; frontend espelha.

## Fora de escopo / STOP (spec fica completa salvo isto)
- **F5** migração real `--apply` das categorias (STOP — confirmar com o dono; inócuo com DB vazia)
- Alterar `quota_amount`/`joia_multiplier` (exige deliberação AG §14)
- Anexo de documento ao ato (fase futura, aditivo)
