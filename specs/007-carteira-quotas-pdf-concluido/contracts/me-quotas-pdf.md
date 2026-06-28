# Contrato — `GET /api/finances/me/quotas/pdf`

Endpoint **novo** (único da feature). Exporta a carteira de quotas do **próprio**
sócio autenticado como PDF.

## Pedido

```
GET /api/finances/me/quotas/pdf
Cookie: <sessão httpOnly>            # auth via get_current_user (withCredentials)
```

- **Sem parâmetros.** O âmbito é sempre o próprio (`current_user.id`); não há forma de
  pedir a carteira de outro sócio (FR-005).
- **Sem privilégio** exigido — qualquer utilizador autenticado (igual a `/me/quotas`).

## Resposta — 200

```
Content-Type: application/pdf
Content-Disposition: attachment; filename=Carteira_Quotas_ACCTA_<member_id|socio>.pdf
<corpo: bytes do PDF>
```

Conteúdo: cabeçalho ACCTA, identificação do sócio, tabela de lançamentos (Data,
Período/Descrição, Categoria, Valor), Total pago, rodapé de uso interno. Para carteira
vazia: documento válido com "Sem lançamentos registados." e Total 0 (FR-007).

## Erros

| Código | Quando |
|--------|--------|
| 401 | Pedido não autenticado (FR-006) |

> Não há 403/404: não existe parâmetro de "outro sócio"; um sócio sem lançamentos
> recebe 200 com PDF vazio (não um erro).

## Invariantes

- Os lançamentos e o Total do PDF **coincidem** com `GET /api/finances/me/quotas`
  (mesma query e somatório) — FR-008/SC-003.
- Devolve **exclusivamente** dados do `current_user` — FR-005/SC-004.
- Não escreve nada (sem audit, sem persistência do PDF).
