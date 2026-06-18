# Spec — Central de Ajuda: profundidade e exemplos práticos

**Data:** 2026-06-18 · **Branch:** `feature/ajuda-profundidade-ferramentas` (de `develop`)

## Problema
A Central de Ajuda (`/ajuda`) é genérica: `passos/dicas/faq` curtos, sem orientar
**quando** usar cada ferramenta, **quando não**, nem **como preencher cada campo**.
O utilizador pediu profundidade, exemplos práticos e um guia de decisão entre
ferramentas — **100% alinhado com o sistema real**.

## Decisões confirmadas com o dono
1. **Só ferramentas reais.** O portal NÃO tem "grupos de trabalho" (organiza-se em
   **Projetos**) e a única "comissão" é a **Comissão de Inquérito** (disciplinar). O
   guia de decisão cobre as ferramentas reais: Proposta, Petição, Esclarecimento,
   Reclamação/recurso, Projetos, Comissão de Inquérito. Nada inventado.
2. **Foco nas ferramentas de ação.** Aprofundar **Governança e voz**, **Finanças** e
   **Administração** (onde há formulários, decisões e RBAC). **Comunidade / Primeiros
   passos / Meu portal** afinados levemente (inclui corrigir a confusão
   "grupos e comissões = projetos" em `comunidade.js`).

## Abordagem (escolhida: estender o schema + renderer)
Conteúdo continua a ser a fonte única (`content/ajuda/*`). Adicionam-se campos
**opcionais** aos artigos, desenhados pela `AjudaPage`:

- `quandoUsar: string[]` — bloco "Quando usar".
- `quandoNaoUsar: string[]` — bloco "Quando NÃO usar (use outra ferramenta)".
- `campos: [{ campo, ajuda, exemplo }]` — guia campo-a-campo (o "como preencher").

`passos/dicas/faq/rota/gate` mantêm-se. A pesquisa (`articleHaystack`) passa a
indexar os campos novos. Compatível: artigos sem os campos novos renderizam como hoje.

### Artigo novo — "Qual canal de voz devo usar?" (topo de Governança)
Guia de decisão real via `faq` + `quandoUsar`/`quandoNaoUsar`:
- Levar um ponto à AG → **Proposta** (Art. 9.g/9.h)
- Forçar AG extraordinária (1/4 dos votantes) → **Petição** (Art. 9.f)
- Dúvida a um órgão → **Esclarecimento** (Art. 9.j)
- Contestar um ato/decisão → **Reclamação/recurso** (Art. 9.i)
- Organizar uma iniciativa/tarefas → **Projetos**
- Infração disciplinar → **processo / Comissão de Inquérito**

## Campos reais (fonte: backend/models.py + páginas)
- **Proposta** — `tipo` (Ponto/Medida/Tema), `titulo` (3–180), `descricao` (≤5000).
  Fluxo: submetida → em_triagem (Mesa AG + Direção) → aceite/recusada →
  incluida (só Mesa AG, com `ordem_index`).
- **Petição** — `titulo` (3–180), `fundamentacao` (≤5000); limiar 1/4 votantes;
  aberta → atingida → encaminhada.
- **Esclarecimento** — `orgao_destino` (direcao/mesa_ag/conselho_fiscal), `assunto`
  (3–180), `pergunta` (≤4000).
- **Reclamação** — `assunto` (3–180), `descricao` (≤5000); SLA 15 dias; recurso à AG.
- **Finanças** — transação (categoria/valor/data/descrição/comprovativo); leitura
  (`view_finances_readonly`) vs gestão (`manage_finances`); co-aprovações.
- **Administração** — pedidos de inscrição, utilizadores, cargos/mandatos,
  comunicados (STOP email real), disciplina, honorários, audit logs, aparência.

Exemplos no contexto ACCTA (controladores de tráfego aéreo; jóia/quota na folha).

## Ficheiros
- `frontend/src/pages/private/AjudaPage.js` — render dos blocos novos + haystack.
- `frontend/src/content/ajuda/index.js` — doc do schema.
- `governanca.js`, `financas.js`, `administracao.js` — a fundo.
- `comunidade.js`, `primeirosPassos.js`, `meuPortal.js` — leve.
- Testes: `__tests__/integrity.test.js`, `private/__tests__/AjudaPage.test.js`.

## Invariantes a manter
- Cada artigo mantém `passos` (≥1) e `rota` ∈ ROTAS_VALIDAS (testes de integridade).
- Sem backend. Sem alterar RBAC/gates existentes. GitFlow: PR para `develop`.
- Design: neutral-led; sem inventar números/factos (regras editoriais do portal).
