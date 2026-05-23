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

## F2 — 3.2 Balancetes (Art. 34, 37)
- [ ] `models.py`: `Balancete` (tipo, periodo, exercicio_ano, snapshot, cf_audit, visibility)
- [ ] `routes/prestacao_contas.py`: publicar (Tesoureiro — congela snapshot de `/finances/summary`) · listar/detalhe · auditar (CF)
- [ ] confirmar `proof_url` aceite no `PATCH /finances/transactions/{id}`
- [ ] RBAC (publicar=manage_finances; auditar=CF; ver=can_view_finances; publicados→Transparência) + audit + notif
- [ ] Testes: snapshot congelado; só Tesoureiro publica; só CF audita; readonly lê não publica; `proof_url` aceite

## F3 — 3.1 Ciclo do exercício + orçamento/plano estruturados (Art. 19.1, 31.k, 37)
- [ ] `models.py`: `Exercicio` (+ máquina de estados), `ParecerCF`, `OrcamentoLinha`, `PlanoAtividade`
- [ ] `routes/prestacao_contas.py`: abrir · relatório (congela `dre_snapshot`) · orçamento (linhas estruturadas) · plano (atividades) · parecer (CF) · submeter-AG · aprovar
- [ ] `GET /exercicios/{ano}/orcamento/execucao` — orçado vs. realizado (de `/finances/dre`) por categoria + desvio
- [ ] Estados avançam por ordem; aviso fora do 1.º trimestre (não bloqueia)
- [ ] RBAC (Direção/CF/Mesa) + audit + notif
- [ ] Testes: ordem dos estados; `dre_snapshot` congelado; só CF emite parecer; CF não escreve transação (403); aprovar exige deliberação; aviso 1.º trimestre

## F4 — Integração aprovação na AG ordinária
- [ ] Ligar `assembleia_id`/`deliberacao_id` (governança já em `develop`); aprovar exige deliberação aprovada
- [ ] Testes de integração da deliberação

## F5 — Frontend
- [ ] `utils/api.js`: `exerciciosAPI`, `balancetesAPI`, `regulamentosAPI`
- [ ] `FinanceiroPage`: abas "Prestação de Contas" (dashboard do ciclo) e "Balancetes"
- [ ] Página `/regulamentos` + rota + item de menu (gating por `isConselhoFiscal`/`isTesoureiro`/`isDirecao`/`isMesaAG`)
- [ ] Vista orçado-vs-realizado (Recharts); badges de auditoria/estado; histórico de versões
- [ ] Design `frontend-design` (neutral-led + Carmesim, sem dark mode); eslint + build

## Verificação por fase
models → schema/índices (`ensure_schema`) → endpoints+RBAC+audit → testes backend (`pytest -m unit`)
→ frontend → eslint/build → verificação manual. PRs pequenos `feature/* → develop`.

## Stop conditions (§11)
Confirmar antes de: mudar `Transaction` para além de aditivos/opcionais; migrar dados
financeiros; emails reais; remover rotas usadas; tratar aprovação como vinculativa sem
deliberação da AG. Push para `main` nunca.
