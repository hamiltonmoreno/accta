# Quickstart — Validação do Ícone quadrado da marca / PWA

Guia de validação ponta-a-ponta. Pressupõe o ambiente de dev do projeto
(`local-dev-run`): backend `uvicorn` + frontend `craco`, login dev.

## Pré-requisitos

- Backend a correr (porta dev) e frontend a correr (proxy mesma-origem).
- Utilizador **admin** ou **moderador** autenticado.
- Uma imagem de teste quadrada PNG (~512×512).

## C1 — Backend: campo e endpoint (pytest, sem servidor)

```bash
cd backend && pytest tests/test_brand_routes.py -q
```

**Esperado**: verde, incluindo os casos novos —
`GET /api/brand/public` devolve `icon_url`; `PATCH` define/limpa `icon_url` (com apagar
upload órfão); `GET /api/brand/icon` redireciona para o ícone atual ou para o default;
RBAC nega financeiro/socio.

## C2 — Gerir o ícone pela UI (US1)

1. Entrar como admin/moderador → **Aparência do Site → Marca**.
2. Na secção **Ícone (app / partilha)**, carregar a imagem de teste.
3. **Esperado**: pré-visualização atualiza (tamanhos representativos); toast de sucesso;
   ação auditada (`brand_updated` com `icon_url`).
4. Carregar **Repor** → volta ao default; o ficheiro carregado deixa de ser referenciado.

## C3 — Endpoint dinâmico (US2, lado servidor)

Com um ícone carregado:

```bash
# Segue o redirect e confirma que chega a uma imagem
curl -sI "$BACKEND/api/brand/icon" | grep -i '^location'   # → /uploads/brand/<uuid>.png
curl -s -o /dev/null -w '%{http_code}\n' -L "$BACKEND/api/brand/icon"   # → 200
```

Sem ícone (após Repor): o `Location` aponta para `{FRONTEND_URL}/logo512.png`.

## C4 — App instalada / partilha (US2, browser)

1. Confirmar que o `manifest.json` servido tem `icons[].src` =
   `https://api.controlador.cv/api/brand/icon` e o `index.html` tem `og:image` no mesmo URL.
2. **Instalar** o portal (Chrome → "Instalar app" / Android "Adicionar ao ecrã inicial").
3. **Esperado**: o ícone do atalho é o ícone da marca carregado (best-effort; pode exigir
   reinstalar/limpar cache do SO — ver edge case de cache).
4. Partilhar uma ligação pública (ex.: validador de Open Graph) → a pré-visualização usa o
   ícone da marca (best-effort, depende de re-indexação do crawler).

## C5 — Marca compacta in-app (US3)

1. **Recolher** a sidebar (desktop).
2. **Esperado**: aparece o ícone quadrado da marca como mark compacto; sem ícone
   carregado, aparece o mark por defeito (sem espaço vazio).

## C6 — Não-regressão (SC-006)

- Sem qualquer ícone carregado, o portal fica **idêntico** ao estado anterior à feature
  (favicon, logótipos e atalhos por defeito inalterados).

## Verificação em produção (após release + Via B)

Ver "teste decisivo" a registar em `docs/runbook-deploy-backend-via-b.md`:

```bash
curl -s -o /dev/null -w '%{http_code}\n' -L https://api.controlador.cv/api/brand/icon   # 200 (imagem)
curl -fsS https://api.controlador.cv/api/brand/public | grep -o '"icon_url"'            # presente
```

> Nota (Princípio VII): a validação de UI/PWA exige browser real; se não for possível,
> declarar explicitamente em vez de afirmar sucesso.
