# Data Model — Spec 016

**Sem alteração de esquema.** Nenhuma tabela, índice ou modelo persistido muda. Esta feature (i) acrescenta uma constante, (ii) acrescenta rótulos de apresentação, (iii) expõe aditivamente um campo num payload existente, e (iv) consome estruturas já existentes.

## Constantes

### `DEPARTAMENTOS` (nova) — `backend/models.py` (+ espelho em `frontend/src/pages/private/usuarios/tokens.js`)

Lista canónica de departamentos internos da associação (etiqueta organizacional; independente de `role`/`cargo`/`privileges`/órgãos):

```
1. Formação e Certificação
2. Segurança Operacional (Safety)
3. Assuntos Profissionais e Laborais
4. Assuntos Técnicos e Operacionais
5. Relações Institucionais e Internacionais
6. Comunicação e Imagem
7. Assuntos Jurídicos
8. Tesouraria e Finanças
9. Eventos, Cultura e Ação Social
```

+ opção de UI **«Outro»** (não pertence à constante; é acrescentada na apresentação e revela texto livre).

### `PRIVILEGE_LABELS` (editada) — `frontend/src/lib/cargoLabels.js`

Passa de 9 → 12 entradas (acrescenta as 3 em falta):

| Chave (estável, **não** renomear) | Rótulo PT (novo) |
|-----------------------------------|-------------------|
| `emit_cf_parecer`                 | Emitir Parecer (Conselho Fiscal) |
| `send_comunicados`                | Enviar Comunicados |
| `comunicar_intra_orgao`           | Comunicar entre Órgãos |

## Entidades existentes (só de contexto — inalteradas no esquema)

### Utilizador / Sócio (`users` doc jsonb)

| Campo | Tipo | Papel nesta feature |
|-------|------|---------------------|
| `role` | string ∈ {admin, financeiro, moderador, socio} | US3 (4 opções no convite), US4 (preenchido pelo botão) |
| `cargo` | string (key canónica, ex. `dir_tesoureiro`) | US4 (deriva os defaults; só-leitura na edição) |
| `privileges` | string[] (subconjunto de `PRIVILEGES`, 12) | US1 (rótulos), US4 (preenchido pelo botão) |
| `department` | string livre, opcional (max 80) | US2 (passa a ser escolhido por dropdown; **sem** enum-enforcement; legado/vazio preservado) |
| `account_type` | "member" \| "technical" | US4 (botão escondido em `technical`) |

**Invariantes preservadas**: `member_id` imutável; `cargo` só alterado via «Cargos & Mandatos»/eleições (esta feature **não** o escreve — a edição continua a mostrá-lo só-leitura); `privileges` são overlays aditivos «role OR privilege».

### Predefinições de cargo (`CARGO_DEFAULTS`, já existente — `governance.py`)

`{ <cargo_key>: { role, privileges[] } }`, exposto por `GET /api/governance/structure` em `cargos[].role_default` / `cargos[].privileges_default`. **Consumido** por US4; não alterado.

## Validação

- `department`: opcional; comprimento ≤ 80 (regra já existente em `RegistrationRequest`/`UserAdminUpdate`). Sem validação de pertença à lista (permite «Outro» e legado). Validação de apresentação: a dropdown oferece a lista + «Outro».
- `role` (convite): um dos 4 de `ROLES` (a UI só oferece esses).
- Rótulos de privilégio: sempre não-vazios na UI (via `privilegeLabel()` com fallback para a chave).
