# Specification Quality Checklist: Site Público em EN e FR (i18n)

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-07-14
**Feature**: [Link to spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) — biblioteca de i18n é decisão de plan (A-08); só o modelo de URL menciona React Router porque é gate de scope
- [x] Focused on user value and business needs — visitantes internacionais, diáspora, parceiros institucionais
- [x] Written for non-technical stakeholders — cenários em prosa, sem código
- [x] All mandatory sections completed — User Scenarios, Requirements, Success Criteria presentes

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain — 3 gates fechados pelo dono 2026-07-14 (D1 prefixo URL, D2 shell-only, D3 auto-detect); FRs condicionais reescritos
- [x] Requirements are testable and unambiguous — FR-001 a FR-028 com verbos MUST e critérios
- [x] Success criteria are measurable — SC-001 a SC-008 com métricas concretas (%, s, contagens)
- [x] Success criteria are technology-agnostic — nenhum SC menciona i18next, JSON, React
- [x] All acceptance scenarios are defined — cada US com 3+ cenários Given/When/Then
- [x] Edge cases are identified — 8 casos borda listados
- [x] Scope is clearly bounded — secção Out-of-Scope explícita com 8 itens fora do âmbito
- [x] Dependencies and assumptions identified — D-01 a D-03, A-01 a A-09

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria — FRs mapeados nas User Stories
- [x] User scenarios cover primary flows — US1 detecção+navegação, US2 qualidade, US3 UX seletor, US4 SEO, US5 limite scope
- [x] Feature meets measurable outcomes defined in Success Criteria — SCs alinham com FRs
- [x] No implementation details leak into specification — decisões de tech (i18next, cookie vs localStorage exato) delegadas ao plan

## Notes

- **Constitutional dependency**: A entrega desta feature exige emenda MINOR v1.1.0 → v1.2.0 ao Princípio IV. Sem ela, o spec não é executável (violaria a constituição em vigor). O plan deve começar por preparar o `SYNC IMPACT REPORT` e propor a emenda.
- **3 gates fechados pelo dono 2026-07-14**: D1 URL prefix, D2 shell-only, D3 auto-detect (todas as recomendações aceites).
- **4 clarificações adicionais registadas na secção `## Clarifications` (Session 2026-07-14)**: (1) slugs PT mantidos em todos os prefixos, (2) troca de idioma preserva a página, (3) aviso «Content in Portuguese» sempre visível em conteúdo dinâmico com shell EN/FR, (4) 404 traduzida na locale para rotas inexistentes sob `/en/…` / `/fr/…`. FR-005a, FR-018a e FR-019a adicionados.
- Tradução profissional em si é entregável fora do trabalho de engenharia (A-05); a engenharia entrega infraestrutura + placeholders.
- Área privada fica PT-only e sem seletor — SC-008 protege contra regressão.
