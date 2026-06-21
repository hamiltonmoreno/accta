# Quickstart — Validação: Comunicados Segmentados (v2)

Guia de validação executável que prova a feature ponta-a-ponta. Não contém
implementação — só pré-requisitos, comandos e resultados esperados. Detalhes em
[data-model.md](./data-model.md) e [contracts/](./contracts/).

## Pré-requisitos

- Backend a correr local: `cd backend && uvicorn server:app --reload --port 8001`
  (ou suite unit via `pytest`, que não precisa de servidor).
- Frontend: `cd frontend && yarn start` (proxy mesma-origem; login dev
  `dev@accta.cv` — ver memória `local-dev-run`).
- DB de dev com ≥ alguns sócios em cargos diferentes (Direcção, Conselho
  Fiscal), categorias (`ordinario`/`fundador`/`honorario`), e ≥1 conta
  `account_type=technical` (ex. `admin@controlador.cv`).
- `ENVIRONMENT` **não** `production` (para validar dry-run sem enviar emails).
- `bcrypt==4.0.1` no venv (constituição / CLAUDE.md).

## Validação por User Story

### US1 (P1) — Direcção comunica internamente
1. Login como membro da Direcção (ou admin com `send_comunicados`).
2. Composer → filtro **Órgão: Direcção** → "Calcular audiência".
3. **Esperado**: preview mostra contagem = nº de membros da Direcção, amostra
   ≤5 nomes, "…mais N" se >5; nenhum sócio fora da Direcção contado.
4. Enviar (Floresta) com `dry_run` ON.
5. **Esperado**: doc fica `enviado` com `dry_run=true`, `audience_resolved`
   preenchido com os `member_id` da Direcção, audit log `comunicado_enviado`
   com `dry_run=true`; **nenhum** email/notificação real criada.
6. RBAC: repetir como `socio` sem privilégio → **403** ao abrir/POST.
7. (Se D2) compor sem enviar, recarregar → rascunho disponível para editar/cancelar.

### US2 (P2) — Convocatória de AGA para subconjunto
1. Login Mesa AG. Filtro composto: **Categoria: ordinario** + **Status: ativo**
   + **Período: admitidos antes de 2024-01-01**.
2. "Calcular audiência" → **Esperado**: contagem exacta + amostra ≤5 + "…mais N";
   `per_type_counts` + `intersected_count` visíveis (efeito AND, FR-014).
3. Filtro que dá 0 (ex. categoria fundador + status pendente_aprovacao sem
   ninguém) → **enviar** bloqueado com "Filtro não selecciona nenhum sócio —
   revê os critérios" (**422**, FR-006).
4. Após envio bem-sucedido, abrir histórico → vê `audience_filter` original +
   `audience_resolved` (member_ids), imutável a mudanças de cargo posteriores
   (US2-AS3).

### US3 (P3) — Boas-vindas a sócios em onboarding
1. Filtro **Status: pendente_aprovacao** (com 3 sócios nesse estado).
2. Preview → **Esperado**: lista os 3; warning `includes_unapproved`; sócios
   `ativo` não contados.

### US4 (P3) — Conselho Fiscal → Direcção *(depende de D1)*
1. Login membro do Conselho Fiscal com `comunicar_intra_orgao`.
2. Filtro **Órgão: Direcção** → enviar → **Esperado**: Direcção recebe; audit
   log identifica autor (CF) + audiência (Direcção).

## Edge cases a exercitar (spec §Edge Cases)
- Lista nominal com `member_id` inexistente → warning `nominal_not_found`,
  prossegue com os válidos.
- `account_type=technical` via nominal → excluída + warning `technical_excluded`.
- Lista nominal + outro filtro → intersecção AND (warning `intersection_reduced`).
- Cargos mudam entre preview e envio → snapshot reflecte o **envio**, não o preview.

## Testes automatizados (pytest, in-process)

```bash
cd backend && pytest tests/test_comunicados_audience.py tests/test_comunicados_preview.py -q
cd backend && pytest tests/test_comunicados_routes.py tests/test_comunicados_service.py -q  # não regredir o legado
```

Cobertura mínima esperada: OR-dentro/AND-entre-tipos; exclusão `technical`;
nominal inexistente; período por `admission_date` (incl. `None`); preview
count+sample+warnings; bloqueio 0-destinatários; dry-run não envia; RBAC 403;
imutabilidade de estados terminais; status aditivo não quebra docs legados.

## Critérios de aceitação (mapa para Success Criteria)
- SC-003: `audit_logs` filtrado por `action=comunicado_enviado` mostra
  `audience_filter` + `recipients_count` + amostra em 100% dos envios.
- SC-004: 0 envios a `account_type=technical` (validável por inspecção do
  `audience_resolved` vs `users.account_type`).
