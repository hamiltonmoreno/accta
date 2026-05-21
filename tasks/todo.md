# TODO — Governança Estatutária da ACCTA (spec-governanca-estatutaria.md)

Branch: `feature/governanca-estatutaria` (off `develop`).
Âmbito desta sessão: **Backend completo (Fases 0–6)**. Exclui Frontend (Fase 7)
e migração destrutiva de dados (Fase 8). Commit por fase.

## Fase 0 — Núcleo de governança (foundation, aditivo) ✅
- [x] `backend/governance.py`: ORGAOS, CARGOS_CATALOG, MEMBER_CATEGORIES, PRIVILEGES, ROLES, LEGACY_CARGO_ALIASES
- [x] Helpers: cargo_info, normalize_cargo, cargo_label, privileges_for_cargo, role_for_cargo, orgao_of_cargo, seats_for_cargo, is_estatutary_cargo, is_voting_member, is_eligible_for_office, required_quorum, required_absolute_majority, required_three_quarters, election_slots, governance_structure
- [x] Re-exports derivados: CARGOS, CARGO_KEYS, CARGO_DEFAULTS, CARGO_SEATS
- [x] `models.py` re-exporta de governance (sem quebrar imports)
- [x] `routes/governance.py`: `GET /api/governance/structure`
- [x] `/users/meta/cargos` + `/users/meta/privileges` viram aliases (deprecated)
- [x] Testes unitários governance + structure (test_governance.py, 44)

## Fase 1 — Normalização compatível (key canónica) ✅
> Fundida na Fase 0: a mudança de taxonomia ripple-a já na validação dos
> endpoints, logo tem de aterrar no mesmo commit para a suite ficar verde.
- [x] UserBase: `member_category`, `orgao`, `rights_suspended_until`, `rights_suspension_reason`, `residence_island`; cargo default → `socio` key
- [x] CargoMandate: campos novos (label, orgao, posse, mandato, suplente, seat_index, eleicao/assembleia ids, transition_id)
- [x] promote/demote/transfer: aceitam key/label/alias, gravam key, setam orgao
- [x] `/cargos`, `/cargos/candidates`, invite, approve_registration, admin_update_user adaptados a keys
- [x] Actualizar test_cargos_routes.py + test_identidade_cargos_models.py + test_auto_registo.py p/ keys
- [x] Commit (Fase 0+1)
- NOTA: 2 falhas pré-existentes em test_users_routes (get_users $or search) — NÃO regressão, fora de âmbito.

## Fase 2 — RBAC e elegibilidade ✅
- [x] `backend/permissions.py`: user_can, is_mesa_ag, is_direcao, is_conselho_fiscal, is_tesoureiro, can_convene_assembleia
- [x] is_voting_member / is_eligible_for_office wired (status, categoria, suspensão)
- [x] Testes RBAC/elegibilidade (test_permissions.py, 17)
- [x] Commit

## Fase 3 — Assembleia Geral ✅
- [x] Modelos: Assembleia, AssembleiaPresenca, AssembleiaDeliberacao (+ Create)
- [x] Colecções + índices (assembleias, assembleia_presencas, assembleia_deliberacoes)
- [x] `routes/assembleias.py`: convocar, presenças, deliberações (+ list), encerrar, quórum
- [x] Testes (quórum 1ª/2ª, representação max 3, Mesa não representa, maiorias, RBAC) — 15
- [x] Commit

## Fase 4 — Eleições + proclamação ✅
- [x] Modelos: Eleicao, EleicaoLista, EleicaoVoterReceipt, EleicaoBallot (+ Create/Votar)
- [x] Colecções + índices (voto secreto: receipt/ballot separados; ux_eleicao_receipt único)
- [x] `database.py`: `cast_ballot` transaccional (receipt + ballot atómico) + voter_hash HMAC
- [x] `routes/eleicoes.py`: ciclo completo (criar→listas→validar→abrir→votar→correspondência→apurar→proclamar); proclamação cria mandatos (serviço comum `_proclaim_list`)
- [x] Testes (lista incompleta/duplicada/comissão, inelegível, boletim anónimo, voto duplo, apuramento, empate, proclamação) — 14
- [x] Commit

## Fase 5 — Disciplina ✅
- [x] Modelo Sancao (+ Create/Comissao/Decidir/Recurso) + colecção sancoes + índices
- [x] `routes/sancoes.py`: propor, comissão, decidir, recurso, aplicar, get/list; `/users/{id}/sancoes` (users.py)
- [x] Regras: multa ≤ 3x quota, expulsão exige deliberação AG aprovada, perda de direitos seta rights_suspended_until (mantém ativo), expulsão inactiva+encerra mandato, redacção de dados sensíveis
- [x] Testes (12)
- [x] Commit

## Fase 6 — Quotas e jóias ✅
- [x] FinanceSettings estendido (joia_multiplier/amount, quota_fixed_by_*, effective_from) + finance_settings_history
- [x] Alteração de quota/jóia exige deliberação AG aprovada por 3/4; regista versão anterior; jóia = mult × quota; quota_description não exige deliberação
- [x] GET /finances/settings/history (view-finances)
- [x] Testes (6) + finances existentes verdes (29)
- [x] Commit

## Fase 7 — Frontend (em curso)
- [x] Transversal: `governanceAPI`/`assembleiasAPI`/`eleicoesAPI`/`sancoesAPI` em api.js; `lib/governanceLabels.js` (labels + cargoLabelFrom, fallback leve); queryKeys (governance/assembleias/eleicoes/sancoes)
- [x] `AuthContext`: `can(p)`, `isMesaAG`, `isDirecao`, `isConselhoFiscal`, `isTesoureiro`, `isVotingMember`
- [x] `PrivateLayout`: secção "Órgãos Sociais" (Assembleias, Eleições; Disciplina gated Direcção/admin) + títulos
- [x] `App.js`: rotas + lazy imports das novas páginas
- [x] `/admin/cargos`: keys + órgão (label, não key)
- [x] `/perfil`: "Os Meus Cargos e Mandatos" (labels + suplente), categoria, banner de suspensão de direitos
- [x] `/admin/assembleias`: convocar, presenças/representação, quórum, deliberações, encerrar (subagent)
- [x] `/admin/eleicoes`: ciclo + listas/slots + votar (membro) + apuramento/proclamação; resultados só agregados (subagent)
- [x] `/admin/disciplinar`: processos, comissão, decidir, recurso, aplicar; access-gate Direcção/admin (subagent)
- [x] eslint limpo (0 erros; 2 warnings pré-existentes, < threshold 60)
- [x] `craco build` verde — "Compiled successfully" (corrigido: AdminAssembleiasPage importava framer-motion, que não é dependência → trocado por CSS `animate-fade-up`)
- [x] Commit

## Fase 8 — Migração de dados (script criado; --apply NÃO corrido)
- [x] `scripts/migrate_governance_cargos.py`: `plan_user_changes` (pura, idempotente) — cargo→key, orgao denormalizado, account_type/member_category default, cargo_history (key+label+orgao); contas técnicas fora do catálogo
- [x] `--dry-run` (default, só leitura) + `--apply --confirm` (duplo guard; AVISO STOP condition); UTF-8 stdout p/ Windows
- [x] test_migrate_governance.py (7) — transform verificado sem DB
- [ ] **`--apply` por correr** — STOP condition (§20): exige confirmação do utilizador + DB acessível + backup. Não há `DATABASE_URL` neste ambiente (dry-run live não corre aqui).
- [x] Commit

## Verificação final
- [x] `cd backend && ruff check .` — All checks passed
- [x] `ruff format` aplicado aos ficheiros tocados (commit style)
- [x] Suite unitária completa (29 ficheiros, sem integração): **579 passed, 2 failed**
  (as 2 falhas — test_users_routes get_users `$or` search — são PRÉ-EXISTENTES na
  branch base, confirmado por `git stash`; fora de âmbito)
- [x] Revisão de critérios de aceitação §19 — ver abaixo

## Review

Branch `feature/governanca-estatutaria` (off `develop`). 7 commits:
0+1 núcleo/taxonomia · 2 RBAC · 3 Assembleia · 4 Eleições · 5 Disciplina ·
6 Quotas/jóias · style (ruff format).

Entregue (Fases 0-6, backend): `governance.py` (fonte única) + `permissions.py`,
4 grupos de rotas novos (`/api/governance`, `/api/assembleias`, `/api/eleicoes`,
`/api/sancoes`) = 28 endpoints de governança, 9 colecções novas + índices,
`database.cast_ballot` (voto atómico), FinanceSettings estendido. ~120 testes
unitários novos de governança.

Critérios §19: ✅ governance.py fonte única · ✅ models.py só re-exporta · ✅ 3
órgãos + Relator + Secretário (sem -Geral) · ✅ sem Coordenações/Comissões · ✅
cargo/cargo_history em keys canónicas · ✅ honorário/técnico/inactivo/suspenso não
votam · ✅ quórum/maiorias por helpers testados · ✅ boletim sem user_id/voter_hash
· ✅ proclamação cria mandatos (posse/cessantes) · ✅ expulsão exige deliberação AG
· ✅ quota/jóia exigem 3/4.

FORA DE ÂMBITO (não pedido nesta sessão): Fase 7 (frontend) e Fase 8 (migração
destrutiva `scripts/migrate_governance_cargos.py --apply` — STOP condition).

Notas de seguimento para o owner (não bloqueantes):
- Docs com contagens agora desactualizadas: `.claude/rules/database.md` ("27
  tables" → +9 colecções de governança) e CLAUDE.md menciona spec-identidade-cargos
  (a taxonomia foi superada por spec-governanca). Não editei (políticas de doc
  canónica) — sinalizo para revisão.
- 2 falhas pré-existentes em `test_users_routes` (get_users `$or` search) merecem
  fix à parte.
- Decisões em aberto §21 que afectam fases futuras: voto digital vinculativo?,
  Direcção 5 vs 7 (default 5), representação de honorário, residência no Sal.
