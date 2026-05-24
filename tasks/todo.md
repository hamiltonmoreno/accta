# TODO — Ciclo Anual de Prestação de Contas (Categoria 3)

Spec: `tasks/spec-ciclo-prestacao-contas.md`. Branch `feature/ciclo-prestacao-contas`
(ramificado de `develop` **após** merge da pilha Cat 4 — PRs #105/#106/#108).

## Decisões do dono (gates §12, fechadas 2026-05-23)
- **§12.1 Aprovação**: sempre via **AG ordinária** (deliberação); a Mesa regista
  resultado interino manual enquanto não há sessão ao vivo.
- **§12.3 Conferência CF**: **ao nível do balancete** (`cf_audit`: conferido + observações).
- **§12.8 Orçamento/Plano**: **DADOS ESTRUTURADOS** — `orcamento.linhas[]` (categoria/
  tipo/valor_previsto) + endpoint orçado-vs-realizado; `plano_atividades.atividades[]`.
- **§12.4/§12.7**: `proof_url`/`conferido` já na `Transaction` (via #105). Parecer
  gated por `is_conselho_fiscal(user) OR privilégio emit_cf_parecer`.
- **§12.5**: semear só o **Regimento da AG** (competência AG); restantes `direcao`.
- **§12.2/§12.6**: `periodo` mensal/trimestral/anual; Transparência via PDF
  (snapshot inline público fica opcional/futuro).

## F0 — Fundação ✅ (commit 7c6eef7)
- [x] `database.py`: + colecções `exercicios`, `balancetes`, `regulamentos`, `regulamento_versoes` em `COLLECTIONS`
- [x] `database.py`: + índices (§7) em `_INDEX_DDL` (ano unique; status; exercicio_ano; tipo+periodo; published; slug unique; regulamento_id; regulamento_id+versao)
- [x] `governance.py`: + privilégio `emit_cf_parecer` em `PRIVILEGES`
- [x] `permissions.py`: helper `can_emit_parecer_cf` (= `is_conselho_fiscal` OR privilégio)
- [x] route modules registados (regulamentos na F1; `prestacao_contas` na F2 — criados com conteúdo, sem esqueletos mortos)

## F1 — 3.3 Regulamentos versionados (Art. 31.j, 56) — independente das finanças ✅
- [x] `models.py`: `Regulamento` + `RegulamentoVersao` (+ `*Create`/`Aprovar`/`Revogar`, literais)
- [x] `routes/regulamentos.py`: criar · listar/detalhe (+ histórico) · nova versão (rascunho) · submeter · aprovar (Direção ou Mesa-AG c/ deliberação) · revogar
- [x] RBAC (manage_documents/Direção; competência-AG exige `deliberacao_id` aprovada) + audit + notif (`system`)
- [x] Seed do **Regimento da AG** (`slug=regimento-ag`, competência `assembleia_geral`) no arranque
- [x] Testes: 22/22 — aprovar troca `current_version` e revoga anterior; Regimento exige deliberação; `slug` único + validador kebab-case

## F2 — 3.2 Balancetes (Art. 34, 37) ✅
- [x] `models.py`: `Balancete` (+ `BalanceteCreate`/`BalanceteAuditar`); `proof_url` adicionado ao `TransactionUpdate`
- [x] `finances.py`: extraído `compute_financial_summary` (fonte única — endpoint + snapshot)
- [x] `routes/prestacao_contas.py`: publicar (Tesoureiro — congela snapshot; janela mensal/anual/trimestral) · listar/detalhe · auditar (CF)
- [x] `proof_url` aceite no `PATCH /finances/transactions/{id}` (testado)
- [x] RBAC (publicar=manage_finances; auditar=`can_emit_parecer_cf`; ver=can_view_finances) + audit + notif (`finance`)
- [x] Testes: 13/13 — snapshot congelado; só Tesoureiro publica; CF readonly não publica; só CF audita; `proof_url` aceite. Sem regressões nos testes de finanças unit (50✓)
- ℹ️ Exposição pública inline do balancete: adiada (§12.6) — público vê só o PDF via fluxo de documentos

## F3 — 3.1 Ciclo do exercício + orçamento/plano estruturados (Art. 19.1, 31.k, 37) ✅
- [x] `models.py`: `Exercicio` (máquina de estados), `ParecerCF`, `OrcamentoLinha`, `PlanoAtividade` (+ `*Submit`/`Create`/`Aprovar`)
- [x] `finances.py`: extraído `compute_dre_report` (fonte única do `dre_snapshot`)
- [x] `routes/prestacao_contas.py`: abrir · relatório (congela `dre_snapshot`) · orçamento (linhas estruturadas, categorias validadas) · plano (atividades) · parecer (CF) · submeter-AG · aprovar · reabrir
- [x] `GET /exercicios/{ano}/orcamento/execucao` — orçado vs. realizado por categoria + desvio
- [x] Estados avançam por ordem; aviso fora do 1.º trimestre (não bloqueia)
- [x] RBAC (Direção/CF/Mesa) + audit + notif (`finance`)
- [x] Testes: 29/29 — ordem dos estados; `dre_snapshot` congelado; só CF emite parecer; CF não escreve transação (403); aprovar exige deliberação aprovada; aviso 1.º trimestre; execução orçado/realizado

## F4 — Integração aprovação na AG ordinária ✅ (integrada na F3)
- [x] `aprovar`/`submeter-ag` ligam `assembleia_id`/`deliberacao_id`; aprovar exige deliberação **aprovada** (`assembleia_deliberacoes`, governança em `develop`)
- [x] Testes da deliberação: aprovada→aprovado; não aprovada→400; inexistente→400; rejeição com deliberação existente

## F5 — Frontend ✅
- [x] `utils/api.js`: `exerciciosAPI`, `balancetesAPI`, `regulamentosAPI`; `lib/queryClient.js`: query keys
- [x] `FinanceiroPage`: abas "Prestação de Contas" (dashboard do ciclo: stepper + ações por papel + dialogs) e "Balancetes" (cards + auditoria CF)
- [x] Página `/regulamentos` + rota (`App.js`) + item de menu (Órgãos Sociais) + título; histórico de versões + ações
- [x] Vista orçado-vs-realizado (tabela com desvio); badges de auditoria/estado; gating por `isDirecao`/`isConselhoFiscal`/`isMesaAG`/`canManageFinances`
- [x] Design `frontend-design` (neutral-led + Carmesim, ≤1 botão primário/vista, focus rings, sem dark mode); eslint 0 erros/0 avisos

## Verificação por fase
models → schema/índices (`ensure_schema`) → endpoints+RBAC+audit → testes backend (`pytest -m unit`)
→ frontend → eslint/build → verificação manual. PRs pequenos `feature/* → develop`.

## Stop conditions (§11)
Confirmar antes de: mudar `Transaction` para além de aditivos/opcionais; migrar dados
financeiros; emails reais; remover rotas usadas; tratar aprovação como vinculativa sem
deliberação da AG. Push para `main` nunca.

---

## Review (2026-05-24)

**Estado: F0–F5 FEITAS** no branch `feature/ciclo-prestacao-contas` (de `develop`,
após merge da pilha Cat 4 #105/#106/#108). 5 commits:
`7c6eef7` F0 · `7b47253` F1 · `35ec7f9` F2 · `297582d` F3+F4 · `1de8cc9` F5.

- **Testes backend**: suite unit completa **826 passed** (762 baseline Cat 4 + 64
  novos: 22 regulamentos + 13 balancetes + 29 exercícios), 0 regressões. O único
  erro (`test_activity_feed.py`) é pré-existente/ambiental (teste de integração
  que lê `REACT_APP_BACKEND_URL` no import). `ruff` limpo.
- **Frontend**: `eslint` 0 erros/0 avisos; `craco build` de produção OK.
- **Fonte única dos números**: `compute_financial_summary`/`compute_dre_report`
  extraídos em `finances.py` e reutilizados pelos snapshots (sem drift).
- **Separação de poderes**: parecer/auditoria do CF gated por `can_emit_parecer_cf`
  (cargo CF ou privilégio `emit_cf_parecer`), distinto de `manage_finances` — o CF
  audita mas **não** escreve transacções (testado: 403).
- **Aprovação via AG**: aprovar exige `deliberacao_id` **aprovada** em
  `assembleia_deliberacoes` (integração F4); estados avançam só pela ordem.
- **Decisão §12.8 (estruturado)**: orçamento em linhas por categoria estatutária +
  endpoint orçado-vs-realizado; plano em atividades.
- **Aditivo**: `proof_url` (já em `develop`) + `conferido`; novas colecções e
  índices; `TransactionUpdate` ganhou `proof_url` (request model, aditivo). Sem
  migração destrutiva, sem emails, sem mexer em `main`.

**Aberto/futuro**: exposição pública inline do balancete (§12.6, adiada — público
vê o PDF); lista estatutária completa de competência dos regulamentos (semeado só
o Regimento da AG); upload de documentos integrado nos diálogos (hoje recebem
`document_id`). Falta **push do branch + PR para `develop`** (decisão do dono).
