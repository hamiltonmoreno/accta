# Spec — Revisão da página pública "Sobre / Quem Somos"

- **Data:** 2026-06-13
- **Ramo de trabalho:** `feature/sobre-page-revisao` (a partir de `develop`)
- **Página alvo:** `frontend/src/pages/public/SobrePage.js` (rota `/sobre`)
- **Origem:** pedido do dono — a seguir à Home v2, rever a página seguinte:
  verificar veracidade da informação, melhorar layout, corrigir erros, garantir
  PT-PT, e na secção **Corpos Sociais** mostrar os órgãos que dirigem a
  associação com **fotos e nomes reais importados do sistema** (dirigentes
  eleitos do mandato). Correr `ui-ux-pro-max` antes e incluir o relatório de
  melhoria nesta spec.

---

## 1. Objetivos

1. **Veracidade** — corrigir afirmações factualmente erradas ou não verificáveis,
   alinhando com a base de conhecimento autoritativa (`memory/deep-research-report.md`)
   e com o conteúdo canónico `frontend/src/content/cta/*`.
2. **Corpos Sociais dinâmicos** — substituir os placeholders hardcoded ("A nomear")
   por dados reais do sistema (nome + foto dos titulares de cargo estatutário),
   via **endpoint público novo**, com estado **"Vago"** elegante quando o cargo
   não tem titular.
3. **Layout & UI/UX** — aplicar o relatório `ui-ux-pro-max` (§4): hierarquia,
   acessibilidade, responsividade, marca neutral-led.
4. **Copy** — reescrever o texto com tom factual (coerente com a Home v2), PT-PT.
5. **PT-PT** — grafias europeias e rótulos de cargo vindos do sistema
   ("Direcção", "Conselho Fiscal", …).

### Decisões fechadas (com o dono)
- Fonte de dados dos dirigentes: **endpoint público dinâmico** (lê a BD em tempo real).
- Âmbito: **estrutura estatutária completa** (3 órgãos × todos os cargos).
- Dados em produção: **ainda não/parcialmente** atribuídos → o design tem de
  degradar bem ("Vago"); o dono preenche depois pelo painel admin.

---

## 2. Correções factuais (veracidade)

| # | Onde | Atual (errado/duvidoso) | Correção | Fonte |
|---|------|--------------------------|----------|-------|
| F1 | `SobrePage.js` bloco FIR (linhas ~58-64) | "operada pela **ASA — Navegação Aérea de Cabo Verde**" | Usar o nome canónico **"ASA — Aeroportos e Segurança Aérea, S.A."** reutilizando o conteúdo `cta` (`camadas`/`fir.descricao`), em vez de hardcoded divergente | `content/cta/estruturaAts.js` (aprovado em #203); `deep-research-report.md` |
| F2 | Intro (linha ~36) | "a entidade representativa **máxima** da classe" | "associação de **representação profissional** dos controladores de tráfego aéreo em Cabo Verde" (sem superlativo não comprovável) | Ressalva editorial do relatório (associação "em organização / a confirmar registralmente") |
| F3 | Intro (linhas ~41-43) | "**Não somos apenas uma voz sindical**; somos parceiros estratégicos…" | **Remover** a referência sindical (a ACCTA é uma **associação**, não um sindicato — induz em erro). Manter a ideia de parceria técnica, em tom factual | Identidade institucional `cta/index.js` |
| F4 | Banner/Intro | "entidade representativa máxima dos controladores…" (subtítulo do banner) | Reformular sem "máxima" | idem F2 |
| F5 | Geral | Sem datas de fundação / nº de associados (não inventar) | Manter ausência; nenhuma estatística não publicada | Regra editorial da base de conhecimento |

> Nota: os valores de FIR (`fir.nome` = "FIR Oceânica do Sal", `fir.baseLegal` =
> "Decreto-Lei n.º 9/80…") já estão corretos e vêm do `cta`. Manter.

---

## 3. Backend — endpoint público de Corpos Sociais

### 3.1 Endpoint
`GET /api/governance/corpos-sociais` — **público (sem `get_current_user`)**, porque
a página `/sobre` é pública.

### 3.2 Lógica
- Construir a estrutura **sempre completa** a partir de `governance.CARGOS_CATALOG`,
  excluindo o cargo base `socio` e o técnico de sistema.
- Para cada cargo (key canónica), procurar titulares: utilizadores com
  `cargo == key`, `status == "ativo"` e conta de membro
  (`account_type == "member"` ou ausente) — mesmo filtro de `_count_cargo_holders`
  em `routes/admin.py`.
- **Projeção mínima** (só o que é público): `{name, photo_url}`. **Não** expor
  `email`, `id`, `member_id`, `role`, `privileges` nem qualquer outro campo.
- Agrupar por órgão na ordem `ASSEMBLEIA_GERAL → DIRECAO → CONSELHO_FISCAL`,
  cargos pela `ordem`.

### 3.3 Forma da resposta (Pydantic em `models.py`)
```jsonc
{
  "orgaos": [
    {
      "id": "assembleia_geral",
      "nome": "Mesa da Assembleia Geral",   // ver §3.4
      "tipo": "deliberativo",
      "cargos": [
        { "key": "ag_presidente", "label": "Presidente da Mesa da AG",
          "ordem": 1, "seats": 1,
          "titulares": [ { "name": "…", "photo_url": "/uploads/avatars/…" } ] },
        // cargo sem titular → "titulares": []  (frontend mostra "Vago")
      ]
    }
    // … Direcção, Conselho Fiscal
  ]
}
```
- Modelos: `CorpoSocialTitular {name, photo_url}`, `CorpoSocialCargo
  {key, label, ordem, seats, titulares}`, `CorpoSocialOrgao
  {id, nome, tipo, cargos}`, `CorposSociaisResponse {orgaos}`.

### 3.4 Rótulo do órgão na UI
- `ASSEMBLEIA_GERAL` → exibir **"Mesa da Assembleia Geral"** (é a mesa que se
  apresenta publicamente). `DIRECAO` → "Direcção". `CONSELHO_FISCAL` →
  "Conselho Fiscal". (Mapa de exibição no backend para não hardcodear no front.)

### 3.5 Privacidade / segurança
- Só titulares **ativos** de cargo **estatutário** (um punhado de pessoas, são os
  representantes públicos da associação) — exposição apropriada e intencional.
- `photo_url` já é auto-gerido pelo próprio e servido em `/uploads/avatars/…`.
- Sem rate-limit especial (entra no default 200/min).

### 3.6 Testes (backend)
`backend/tests/test_governance_corpos_sociais.py` (unit/in-process, `mock_db`):
- estrutura completa devolvida mesmo com **0 titulares** (todos "Vago");
- titular ativo aparece com `name`+`photo_url`; **nenhum** campo sensível na resposta;
- utilizador `inativo` / conta `technical` / cargo `socio` **não** aparecem;
- endpoint acessível **sem token** (público);
- ordem dos órgãos e dos cargos respeitada.

---

## 4. Relatório de melhoria UI/UX (`ui-ux-pro-max`)

> Tokens de cor devolvidos pelo motor (`#DC2626` etc.) foram **descartados** — a
> skill é brand-locked e defere para `frontend-design` (Carmesim `#C7202F`,
> Grafite `#3A3A3A`, neutral-led, Floresta `#166534` para ação positiva).
> Padrão recomendado aplicável: **"Trust & Authority"** (credenciais, hierarquia
> clara, profissionalismo; evitar "conteúdo genérico").

| # | Achado | Severidade | Ação |
|---|--------|-----------|------|
| U1 | **Avatares sem `alt`** quando entrarem fotos reais | Alta | `alt="Foto de {nome} — {cargo}"`; cargo "Vago" usa ícone decorativo com `aria-hidden` |
| U2 | **Sem focus-visible** explícito nos CTA/links | Alta | Aplicar anel da marca `focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 ring-offset-2` |
| U3 | **Cartões de Valores multicolor** (vermelho/âmbar/azul/verde) contrariam o neutral-led/single-accent | Média | Migrar para neutral: ícones Grafite sobre superfície neutra; **Carmesim** só no valor-chave "Segurança". Sem paleta arco-íris |
| U4 | `animate-fade-up` pode ignorar `prefers-reduced-motion` | Média | Garantir guard global `@media (prefers-reduced-motion: reduce)`; verificar em `index.css`/`App.css` e adicionar se faltar |
| U5 | Estado "**A nomear**" pouco claro e estático | Média | Substituir por **"Vago"** com placeholder de avatar (ícone `UserCircle` neutro + inicial), contraste ≥4.5:1 |
| U6 | Bloco gradiente grafite genérico | Baixa | Refinar para "credencial/autoridade": FIR Oceânica do Sal + base legal + prestador ATS (factual), reutilizando `cta` |
| U7 | Responsividade dos cartões de titulares | Alta | Grid reflui a 375/768/1024/1440px; sem scroll horizontal; texto ≥16px no mobile; cartão de titular empilha avatar+nome sem corte |
| U8 | Skeleton ausente durante o fetch dos Corpos Sociais | Média | `Skeleton` (shadcn) enquanto `useQuery` carrega; erro → estado neutro "informação indisponível de momento" (sem `console.error`) |
| U9 | Hover/transição | Baixa | `transition-colors`/`shadow` 150-300ms; `cursor-default` (titulares não são links) |

**Checklist de entrega (pré-merge):** sem emojis como ícones (Lucide ✓);
`alt` em todas as imagens; focus visível; contraste ≥4.5:1; `prefers-reduced-motion`
respeitado; responsivo 375/768/1024/1440; sem scroll horizontal mobile.

---

## 5. Frontend — implementação

### 5.1 Dados
- `frontend/src/lib/queryClient.js`: adicionar `queryKeys.governance.corposSociais()`.
- `frontend/src/utils/api.js`: grupo `governanceApi.getCorposSociais()` →
  `GET /governance/corpos-sociais` (cliente axios público; sem header de auth
  obrigatório).
- `SobrePage.js`: `useQuery({ queryKey, queryFn, staleTime: 5*60*1000 })`
  (dado quase estático) com `Skeleton` no `isLoading`.

### 5.2 Secção "Corpos Sociais" (redesenho)
- 3 blocos por órgão (Mesa da AG · Direcção · Conselho Fiscal), cada um lista os
  seus cargos pela ordem do backend.
- **Cartão de titular**: avatar redondo (foto ou placeholder "Vago") + nome +
  rótulo do cargo. Vários titulares por cargo (ex.: Vogais) → lista.
- Estado **"Vago"**: avatar placeholder neutro + texto "Vago" (Grafite/cinza ≥
  `#6B7280`).
- Marca: Direcção continua a ser o bloco com acento Carmesim (borda), restantes
  neutros; sem vermelho sobre fundo escuro.

### 5.3 Copy (tom factual, PT-PT)
- **Banner/Intro**: aplicar F2/F3/F4. Mensagem: associação profissional dos CTA
  em Cabo Verde, foco em segurança operacional, valorização da carreira e
  cooperação institucional.
- **Missão/Visão/Valores**: afinar texto (conciso, factual); Valores re-tonalizados
  (U3).
- **Intro Corpos Sociais**: "Os órgãos sociais que dirigem e fiscalizam a
  associação" (factual).
- **CTA final**: manter ligações a `/transparencia` e `/contactos` (botão positivo
  = Floresta, secundário neutro), copy afinada.

### 5.4 Ficheiros tocados
1. `backend/routes/governance.py` — endpoint público.
2. `backend/models.py` — modelos de resposta.
3. `backend/tests/test_governance_corpos_sociais.py` — testes (novo).
4. `frontend/src/pages/public/SobrePage.js` — redesign + copy + fetch.
5. `frontend/src/utils/api.js` — `governanceApi.getCorposSociais`.
6. `frontend/src/lib/queryClient.js` — queryKey.

> São >3 ficheiros: é a funcionalidade pedida, não um "small fix". Sem alterações
> destrutivas de schema, sem envio de emails, sem mexer em CORS/JWT.

---

## 6. Critérios de aceitação

- [ ] `GET /api/governance/corpos-sociais` responde **sem autenticação** e devolve
      a estrutura completa dos 3 órgãos (cargos "Vago" quando sem titular).
- [ ] A resposta **não** contém `email`/`id`/`member_id`/`role`/`privileges`.
- [ ] A página `/sobre` mostra os Corpos Sociais a partir do endpoint, com
      Skeleton no carregamento e "Vago" elegante.
- [ ] Correções factuais F1–F5 aplicadas; nenhuma afirmação não verificável nova.
- [ ] UI/UX U1–U9 aplicados; checklist de entrega cumprido.
- [ ] PT-PT em toda a página; rótulos de cargo vêm do sistema.
- [ ] `ruff check`/`ruff format` no backend e `eslint` no frontend sem novos erros;
      testes do endpoint verdes.
- [ ] Build do frontend OK.

---

## 7. Fora de âmbito

- Atribuir cargos/fotos reais em produção (fá-lo o dono via `/admin/cargos`).
- Outras páginas públicas.
- Alterações a `governance.py` (catálogo de cargos) — só leitura.
