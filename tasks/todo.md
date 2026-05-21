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

## Fase 5 — Disciplina
- [ ] Modelo Sancao + colecção sancoes
- [ ] `routes/sancoes.py`: propor, comissão, decidir, recurso, aplicar
- [ ] Regras: multa ≤ 3x quota, expulsão exige deliberação AG, perda de direitos seta rights_suspended_until
- [ ] Testes
- [ ] Commit

## Fase 6 — Quotas e jóias
- [ ] FinanceSettings estendido (joia_multiplier/amount, deliberação 3/4, effective_from) + finance_settings_history
- [ ] Alteração de quota/jóia exige deliberação AG 3/4; regista histórico
- [ ] Testes
- [ ] Commit

## Verificação final
- [ ] `cd backend && ruff check . && ruff format --check .`
- [ ] `cd backend && pytest -m unit` verde
- [ ] Revisão de critérios de aceitação (§19)

## Review
_(preencher no fim)_
