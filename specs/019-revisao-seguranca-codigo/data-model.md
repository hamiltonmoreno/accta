# Data Model — Revisão de Segurança (spec 019)

**Esta revisão não altera o esquema de produção nem faz migração.** Os «modelos»
abaixo são (a) as **estruturas de trabalho da revisão** (registo de achados,
taxonomia de classe de acesso) e (b) as poucas **restrições de validação** aditivas
em modelos Pydantic existentes. Documentos existentes na BD ficam intactos (FR-024).

## Entidades de trabalho (artefactos da spec, não persistidas em prod)

### Achado de Segurança (Security Finding)
| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | str | H1..H8, M-*, ou LOW-* (ver `research.md`) |
| `severity` | enum | `Critical` / `High` / `Medium` / `Low` |
| `domain` | enum | um dos 9 domínios do levantamento |
| `surface` | str | ficheiro/endpoint afetado |
| `workstream` | enum | A..G (ou FR-013), ou `—` |
| `status` | enum | `aberto` / `corrigido` / `aceite` / `adiado` / `verify-only` / `recomendação-infra` |
| `regression_guard` | str | referência ao teste/tripwire que o tranca (obrigatório quando `corrigido`) |

Fonte de verdade: a tabela em `research.md`. Ao fechar o ciclo, todos os HIGH+MEDIUM
ficam `corrigido` (com `regression_guard`) ou `aceite`/`adiado` com justificação
(SC-007); os LOW ficam `adiado` num backlog.

### Classe de Acesso (access_class) — registo `AUDIT` do WS-C
Taxonomia usada por `test_idor_coverage.py` para classificar **cada** rota que recebe
`{id}` e provar SC-001. Uma rota = exatamente uma classe, com citação do gate.

| Classe | Significado | Como é provada |
|--------|-------------|----------------|
| `public` | deliberadamente não autenticada (`/public/*`, `/brand/icon`) | expõe só dados não sensíveis |
| `authenticated` | qualquer membro autenticado (objeto é association-wide por desenho) | gate de sessão |
| `role` | gated por helper (`has_role_or_privilege`/`is_admin`/`module_gate`/`permissions.is_*`), sem posse por-utilizador | `test_access_matrix.py` + governança |
| `owner` | acesso depende de o chamador possuir o objeto (`user_id`/`created_by`/self) | negativo comportamental em `test_idor.py` |
| `parent_scoped` | objeto-filho re-consultado com escopo pelo `id` do pai da URL | negativo comportamental em `test_idor.py` |

Invariante (SC-001): `set(rotas_id_taking_enumeradas) == set(AUDIT)` e todas as
`owner`/`parent_scoped` mutantes têm negativo comportamental registado.

## Restrições de validação aditivas (modelos Pydantic existentes)

Sem novos campos nem alteração de tipos — apenas `field_validator` de escrita
(não tocam documentos já guardados; FR-016/FR-024).

| Modelo(s) | Campo | Regra nova | WS |
|-----------|-------|-----------|----|
| `Benefit`/`BenefitCreate`/`BenefitUpdate` | `logo_url` | `_v_local_upload_url`: `None`/`""` ou começa por `/uploads/` (senão 422) | F |
| `Post`/`PostCreate`/`PostUpdate` | `cover_url` | idem | F |
| `Publicacao`/`PublicacaoCreate`/`PublicacaoUpdate` | `capa_url` | idem | F |

> `photo_url` (users) e `image_url` (banners) já têm o validator equivalente
> (`_v_photo_url`/`_v_image_url`) — reutilizar o mesmo helper partilhado.

## Restrições de configuração / arranque (não são dados)

Gates fail-closed adicionados (WS-E, WS-D, WS-G) — validação de fronteira, não persistência:

- `SECRET_KEY`: comprimento ≥ 32 (arranque recusa senão).
- Postura de prod: `_looks_like_production()` ⇒ exige `ENVIRONMENT=production` (arranque
  recusa senão), ligando cookie-seguro/HSTS/docs-off/CORS a uma única env afirmativa.
- `starlette.MultiPartParser.max_part_size` ≈ 11 MB (para os limites por-categoria
  existentes continuarem a mandar após o bump).

## Campos existentes reutilizados (sem alteração)

- `Transaction.proof_url` (já existe) — usado pelo novo endpoint gated de `proof` (WS-A).
- `MFA_SECRET_FIELDS`, `SENSITIVE_PROFILE_FIELDS`, `_user_projection` — inalterados;
  continuam a ser o guard de projeção (WS-B).
- `_is_trusted_proxy`/`_TRUSTED_PROXY_NETS` — reutilizados por `client_ip()`/`rate_limit_key()` (WS-D).

## Fora deste ciclo (migração = STOP, adiado)

- Purga física de `mfa_secret*`/`password` legado do jsonb de `users` — migração
  destrutiva; desnecessária (exposição já bloqueada). Tarefa separada gated pelo dono.
- Contador persistente de volume de upload por-utilizador — substituído por rate-limit.
- Retenção/redação de `audit_logs.details` — registado, avaliar em ciclo futuro.
