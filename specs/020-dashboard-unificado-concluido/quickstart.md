# Quickstart: Dashboard unificado

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Guia de validação end-to-end depois de `/speckit-implement`. Executar por esta ordem.

## Pré-requisitos

- Ambiente dev isolado (Docker `accta-pg-dev` porta 5433, `backend/.env.dev`) — o mesmo
  usado na spec 017/018. Contas seed: `admin@dev.cv`, `socio1@dev.cv`, `socio2@dev.cv`.
- ⚠️ **NÃO usar** `backend/.env` (aponta para Supabase de PRODUÇÃO com dados reais desde
  o reset de 2026-06-30).
- `curl` + navegador (Chrome/Firefox) + qualquer editor.

## 1. Backend — smoke test do endpoint

```bash
cd backend
uvicorn server:app --reload --port 8001 --env-file .env.dev
```

Noutro terminal, obter tokens (`POST /api/auth/login`) e testar:

```bash
# admin
curl -sH "Authorization: Bearer <admin-token>" http://localhost:8001/api/dashboard/overview | jq
# → 200 com todos os blocos (finance/socios/atos/votacoes/assembleias)

# sócio comum (sem privilégios)
curl -sH "Authorization: Bearer <socio-token>" http://localhost:8001/api/dashboard/overview | jq
# → 200 com o MESMO payload

# sem token
curl -si http://localhost:8001/api/dashboard/overview
# → 401
```

**Verificação decisiva**: os dois tokens devem devolver **exactamente** o mesmo shape
de payload (só os números podem diferir se houver seed diferente — mas em dev seed é
comum).

## 2. Backend — testes automatizados

```bash
cd backend
pytest tests/test_dashboard_routes.py -v
pytest tests/test_access_matrix.py -v          # deve continuar verde (nenhum inline role check adicionado)
pytest -m unit                                  # suíte completa
```

Testes esperados no `test_dashboard_routes.py`:
- `test_admin_get_overview` — 200 + shape correcto
- `test_socio_get_overview` — 200 + shape idêntico ao do admin
- `test_no_auth_returns_401`
- `test_overview_no_pii` — tripwire recursivo
- `test_reuses_compute_functions` — mock de `compute_financial_summary`/`compute_dre_report` para provar reuso

## 3. Frontend — dev com dev backend

```bash
cd frontend
REACT_APP_BACKEND_URL=http://localhost:8001 yarn start
```

Abrir `http://localhost:3000` e:

### Como admin
1. Login `admin@dev.cv`.
2. Dashboard deve mostrar **tudo o que já mostrava** — sem regressões visuais.
3. Clicar em cada widget financeiro → navega para `/financeiro/*` (comportamento actual
   preservado).

### Como sócio comum
1. Login `socio1@dev.cv`.
2. Dashboard deve mostrar **os mesmos widgets** que o admin viu:
   - Stat cards (Total Sócios, Sócios Activos, Eventos Activos, Receita Anual)
   - Gráfico mensal receitas × despesas (Recharts)
   - Pizza de despesas por categoria
   - Banner de saldo financeiro do ano
   - Widgets universais já existentes (votações abertas, próximos eventos, ranking,
     relatório pessoal, feed de actividade)
   - **Novos**: KPIs de vida associativa (novos sócios 90d, próximas AGAs, atos
     pendentes agregados, participação na última votação)
3. **Menu Finanças** — deve estar **escondido**.
4. Tentar navegar directamente para `/financeiro` na barra de endereços → **403** ou
   redirect com aviso "sem permissão".
5. Passar rato pelos widgets financeiros → **sem** cursor pointer, **sem** hover que
   sugira clique, **sem** link para `/financeiro`.
6. Widgets universais anteriores (votações/eventos/etc) → interacção preservada.

### Como financeiro (função seed)
1. Login numa conta com função seed «Financeiro» (ou criar uma via `/gestao/socios`).
2. Dashboard igual ao do admin/sócio comum, mas widgets financeiros **clicáveis** →
   `/financeiro`.

## 4. RankingSettings — confirmar universalização (Q2)

```bash
# como admin, verificar config actual
curl -sH "Authorization: Bearer <admin-token>" http://localhost:8001/api/ranking/settings | jq .visibility
# → esperar "all_members"

# se estiver "direcao_only", mudar:
curl -X PATCH -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"visibility": "all_members"}' \
  http://localhost:8001/api/ranking/settings
```

Em navegador, como sócio comum → widget **RankingTopN** aparece com Top-N + nomes.

## 5. Teste anti-PII no navegador (DevTools)

Como sócio comum, DevTools → Network → filtrar `overview` → Preview do JSON:

- **Não** procurar strings suspeitas: `@` (emails), `+238` (telefones CV), padrões de
  CPF/BI, `member_id`, `password`, `photo_url`.
- Se aparecer algum → **regressão** → bloquear release.

## 6. Deploy — Via B em prod

Depois de tudo verde em dev:

```bash
# no VPS (root@194.164.76.72 via ~/.ssh/accta-vps)
ssh accta-vps
cd /docker/accta
# seguir docs/runbook-deploy-backend-via-b.md com a tag da release
```

**Teste decisivo em prod** (`api.controlador.cv`):

```bash
# criar um token de teste com utilizador sócio real (ou admin de emergência)
curl -sH "Authorization: Bearer <token-socio-real>" https://api.controlador.cv/api/dashboard/overview | jq
# → 200 com payload agregado

curl -si https://api.controlador.cv/api/dashboard/overview
# → 401 (sem token)
```

Depois, o dono valida em navegador (Princípio VII):
1. `controlador.cv` → login como sócio comum → Dashboard.
2. Confirmar visibilidade dos widgets financeiros agregados.
3. Confirmar que menu Finanças continua escondido / `/financeiro` continua 403.
4. Confirmar Top-N do ranking (Q2).
