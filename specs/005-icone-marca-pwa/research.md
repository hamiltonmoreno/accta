# Research — Ícone quadrado da marca / PWA

Fase 0. Resolve as incógnitas técnicas da abordagem "servir dinâmico" (Q1) e o
encaixe na infraestrutura de marca existente. Sem `NEEDS CLARIFICATION` em aberto.

---

## D1 — Como tornar o ícone PWA/og dinâmico sem novo deploy

**Decisão**: Introduzir um endpoint público estável **`GET /api/brand/icon`** que serve
sempre o ícone atual (ou o default quando não há upload). O `manifest.json` (ícones PWA)
e o `index.html` (`og:image`/`twitter:image`) passam a referenciar **esse URL absoluto e
fixo** em vez de um ficheiro estático.

**Rationale**:
- `manifest.json` e `index.html` são **estáticos na Vercel**; não sabem o nome do
  ficheiro carregado (que muda a cada upload via `/uploads/brand/<uuid>.png`). Um URL
  fixo que resolve para o ícone corrente é a única forma de trocar o ícone **sem
  rebuild**.
- O backend **já serve `/uploads/brand/...` estaticamente** (`UploadsStaticFiles` em
  `server.py`), por isso o endpoint só precisa de resolver "qual o ícone atual" e
  entregá-lo.
- Os crawlers de partilha não correm JS → uma atualização runtime em React não chegaria
  ao `og:image`; só um URL servido pelo backend reflete a marca nas partilhas
  (best-effort, conforme Q1).

**Mecanismo**: o endpoint faz **302 redirect** para o recurso correto:
- `icon_url` definido → redirect para `icon_url` (já é `/uploads/brand/<file>`, servido
  estaticamente no mesmo origin do backend);
- sem `icon_url` → redirect para o default estático do frontend
  (`{FRONTEND_URL}/logo512.png`), evitando duplicar o asset no backend.
Com `Cache-Control` curto-médio (ex.: `public, max-age=3600`) para equilibrar frescura e
carga. **Alternativa considerada**: streaming dos bytes via `FileResponse` (evita
problemas com crawlers que não seguem redirects). **Rejeitada como default** por ser mais
código e por o redirect ser suficiente para PWA/Apple e best-effort para og (Q1). Fica
como plano B documentado se algum crawler relevante falhar o redirect.

**Alternativas consideradas e rejeitadas**:
- *Regenerar `logo192/512.png`/og estáticos num passo de build* (Q1 opção C) — exige
  deploy a cada troca; contraria o valor "pela UI / sem deploy".
- *Gerar `manifest` dinâmico via Blob no runtime + trocar `<link rel=manifest>`* — frágil
  para a instalação inicial e inútil para crawlers; mais complexo que um endpoint.

---

## D2 — URL absoluto fixo em ficheiros estáticos (manifest/index.html)

**Decisão**: Hardcodar o origin de prod **`https://api.controlador.cv`** no
`manifest.json` (`icons[].src`) e no `index.html` (`og:image`/`twitter:image`),
apontando para `/api/brand/icon`.

**Rationale**:
- A Vercel não interpola variáveis de ambiente no `manifest.json` (copiado tal-e-qual);
  no `index.html` o CRA só interpola fiavelmente `%PUBLIC_URL%`.
- O `index.html` **já hardcoda** URLs de prod (`og:image` =
  `https://controlador.cv/logo512.png`, `canonical`, `og:url`) — portanto hardcodar o
  origin do backend é **coerente** com o existente.
- PWA install e og só importam em **produção**; em dev/preview a divergência é inócua
  (já é assim hoje com o og estático).

**Alternativas**: endpoint no próprio domínio do frontend (proxy Vercel→backend) —
desnecessário e adiciona uma indireção; o origin do backend é estável e público.

---

## D3 — Tamanhos do ícone: servir a imagem-mestre tal-e-qual

**Decisão**: O gestor carrega **uma** imagem quadrada (recomendado ~512×512 PNG
transparente). O endpoint serve essa imagem-mestre **sem redimensionar**; o `manifest`
declara uma entrada de ícone com `"sizes": "any"` e `"purpose": "any"`. O navegador/SO
escala conforme precisa.

**Rationale**: Princípio I (Simplicity) — evita uma dependência de processamento de
imagem (Pillow) e a complexidade de variantes; alinha com o que a feature do favicon já
faz (servir o ficheiro tal-e-qual). `sizes:"any"` é válido e instrui o agente a escalar.

**Alternativas**:
- *Múltiplas variantes (192/512/maskable) geradas no servidor* — exige Pillow + lógica de
  geração + armazenamento; desproporcionado para o ganho.
- *Declarar `purpose:"maskable"`* — exigiria garantir "safe zone"; **rejeitado** porque
  não controlamos a imagem carregada. Mitigação: a UI **recomenda** conteúdo centrado com
  margem de segurança (FR-009); declaramos só `purpose:"any"`.

---

## D4 — Campo distinto do favicon (Q2) + semântica de limpar

**Decisão**: Novo campo `icon_url` em `brand_settings`, **separado** de `favicon_url`.
Reutiliza a mecânica já existente em `routes/brand.py`: acrescentar `icon_url` ao tuplo
`url_fields` (PATCH, semântica `""`=repor default→`None`, limpeza de uploads órfãos que
deixem de estar referenciados) e ao `_public_view`/audit.

**Rationale**: Q2 = campos distintos. `favicon_url` já está em prod (v0.5.34); favicon e
ícone de app legitimamente diferem (favicon é mais simples/pequeno). Adicionar ao tuplo
`url_fields` é a extensão de menor risco — a lógica de limpeza partilhada já lida com
N campos e até deduplica ficheiros partilhados entre campos.

**Alternativas**: subsumir `favicon_url` (Q2 opção C) — exigiria migração do campo já
lançado e perderia flexibilidade; rejeitado pela decisão do dono.

---

## D5 — Superfície in-app (US3) e relação com o componente de marca existente

**Decisão**: Novo componente **`BrandIcon.js`** (espelha `BrandLogo`/`FaviconManager`):
lê a marca pública via TanStack Query (mesma query/cache, `staleTime` alto) e renderiza
`icon_url` (via `mediaUrl`) ou um **mark por defeito** quando ausente. A sidebar recolhida
(`PrivateLayout.js`) passa a mostrar `<BrandIcon />` no topo (US3, P3).

**Rationale**: consistência com o padrão de marca já existente; runtime, sem deploy; a
sidebar recolhida hoje não mostra marca nenhuma, por isso é ganho incremental e reversível.

**Default in-app**: usar o ícone vetorial compacto já existente (`ACCTALogo variant="icon"`
se disponível) ou um mark neutro com as iniciais — a decidir em `/speckit-tasks`; não bloqueia.

---

## D6 — RBAC, upload e segurança (sem alterações de política)

**Decisão**: Sem política nova. Upload pela categoria **`brand`** existente (2 MB,
admin+moderador, **SVG bloqueado**, validação por magic bytes). `GET /api/brand/icon` e
`/api/brand/public` são **públicos** (a marca aparece antes do login). Escrita audita.

**Rationale**: Princípio III; reutilização total da infraestrutura validada na feature do
favicon. `icon_url` aceita string arbitrária como `logo_*_url`/`favicon_url`, mas só
admin/moderador escreve e o valor é servido como imagem (sem execução). Sem regressão.

---

## Resumo das decisões

| # | Decisão |
|---|---|
| D1 | Endpoint estável `GET /api/brand/icon` (302 → atual/default) torna PWA/og dinâmicos sem deploy |
| D2 | `manifest.json`/`index.html` hardcodam `https://api.controlador.cv/api/brand/icon` (coerente com o existente) |
| D3 | Servir imagem-mestre tal-e-qual; `manifest` `sizes:"any"`/`purpose:"any"`; sem processamento de imagem |
| D4 | `icon_url` novo e distinto de `favicon_url`; reutiliza `url_fields` (PATCH/limpeza/audit) |
| D5 | `BrandIcon.js` runtime para a marca compacta in-app (sidebar recolhida) |
| D6 | RBAC/upload/segurança reutilizados sem alteração (categoria `brand`, SVG bloqueado, audit) |
