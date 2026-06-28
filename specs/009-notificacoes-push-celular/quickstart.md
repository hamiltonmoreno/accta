# Quickstart — Validar Notificações Push no Celular

**Feature**: 009-notificacoes-push-celular | **Date**: 2026-06-28

Guia de validação ponta-a-ponta. Detalhes de dados/endpoints em
[data-model.md](./data-model.md) e [contracts/push-api.md](./contracts/push-api.md).

## Pré-requisitos

- Backend e frontend a correr (ou ambiente de preview).
- Chaves VAPID configuradas no backend:
  ```bash
  python scripts/generate_vapid_keys.py   # imprime VAPID_PUBLIC_KEY / PRIVATE_KEY / SUBJECT
  # exportar as 3 no ambiente do backend e reiniciar
  ```
- Um dispositivo de teste: **Android/Chrome** (mais simples) e/ou **iPhone com o
  PWA na Tela de Início** (iOS 16.4+).

## Testes automatizados (backend)

```bash
cd backend && pytest tests/test_push_routes.py -v
cd backend && ruff check push_service.py routes/push.py tests/test_push_routes.py
```

Esperado: subscribe (insert/update), unsubscribe, vapid-key (503 sem config /
200 com config), test (400/200), `dispatch_push` (no-op desligado; envio + poda
410), e a matriz `is_safe_push_endpoint` (aceita serviços públicos, rejeita
não-HTTPS/localhost/IPs privados/link-local) — todos verdes.

## Cenário 1 — Ativar e receber (US1 + US2)

1. Login no portal num dispositivo suportado → **Perfil**.
2. No cartão **"Notificações no Celular"**, ligar o interruptor.
3. Conceder a permissão de notificações do navegador.
   - **Esperado**: interruptor fica ligado; toast de confirmação.
4. Acionar `POST /api/push/test` (ou gerar uma notificação real, ex.: um
   comunicado para o sócio).
5. **Fechar a app** e provocar/aguardar a notificação.
   - **Esperado (SC-002/SC-003)**: o aviso aparece na bandeja com título +
     resumo, mesmo com a app fechada.
6. Tocar no aviso.
   - **Esperado (FR-002)**: o portal abre/foca na página do `url` (ex.:
     `/carteira`).

## Cenário 2 — Desativar (US2)

1. No Perfil, desligar o interruptor.
   - **Esperado (FR-003/FR-010)**: deixa de receber push; o registo do
     dispositivo é removido.

## Cenário 3 — Permissão negada (US2)

1. Ligar o interruptor e **negar** a permissão do navegador.
   - **Esperado (FR-005)**: mensagem clara de que a permissão é necessária; o
     interruptor permanece desligado.

## Cenário 4 — iPhone antes de instalar o PWA (US3)

1. Abrir o portal num **iPhone via Safari** (sem PWA instalado) → Perfil.
   - **Esperado (FR-006)**: em vez do interruptor, surge a instrução
     "Adicionar à Tela de Início".
2. Instalar o PWA e abrir pelo ícone → Perfil.
   - **Esperado**: aparece o interruptor normal e é possível ativar.

## Cenário 5 — Degradação graciosa (FR-008)

1. Remover/limpar as chaves VAPID e reiniciar o backend.
   - **Esperado (SC-004)**: `GET /api/push/vapid-public-key` → 503; o cartão de
     ativação não permite ligar; **as notificações in-app continuam a funcionar**
     sem erros visíveis.

## Cenário 6 — Anti-SSRF (FR-009)

1. Com a feature ligada, chamar `POST /api/push/subscribe` com
   `endpoint: "https://169.254.169.254/…"` (ou `http://…`, `https://localhost/…`).
   - **Esperado**: **400** "Endpoint de push inválido."; nada é gravado.
