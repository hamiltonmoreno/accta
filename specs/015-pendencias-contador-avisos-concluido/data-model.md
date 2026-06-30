# Data Model: Pendências v2 — contador + avisos

**Sem entidades persistidas novas. Sem alteração de schema/migração.** Esta feature é derivação
no cliente + mudança de um valor de campo já existente.

## Entidades derivadas (não armazenadas)

### Contador de pendências
- **Origem**: derivado em runtime pelo hook `usePendencias()` a partir de leituras existentes.
- **Fórmula** (role-aware):
  `total = votacoes + eventos + (isDir ? assinatura + propostos : 0)`
  - `votacoes` = `polls` com `status==='aberta' && !has_voted`
  - `eventos` = `events.upcoming` onde `user.id ∉ attendees`
  - `assinatura` = `atos.list({pendentes_para_mim:true}).items` (só `isDir`)
  - `propostos` = `atos.list({status:'pendente'}).items` filtrados por `created_by===user.id` (só `isDir`)
- **Regras de validação / apresentação**: `total > 9 → "9+"`; `total === 0 → sem badge`.
- **Fonte única**: o mesmo hook alimenta o badge (sidebar) e o painel (`/pendencias`) ⇒ contador
  ≡ painel (SC-002).
- **Exclusões**: eleições/deliberações secretas não entram (nunca são lidas pela derivação).

## Campo existente alterado (só valor, não forma)

### `Notification.link` (`backend/models.py` — `Optional[str]`)
- **Sem mudança de tipo/forma.** Muda o **valor** gravado em 3 call-sites de `routes/atos.py`:

| Categoria de aviso | `link` antes | `link` depois |
|--------------------|--------------|---------------|
| Ato **pendente** (criado / atrasado-Direção / atrasado-proponente) | `/financeiro/co-aprovacoes` | **`/pendencias`** |
| Ato **decidido** (aprovado / rejeitado-com-motivo / executado) | `/financeiro/co-aprovacoes` | `/financeiro/co-aprovacoes` (inalterado) |

- **Transições de estado relevantes**: a categoria (pendente vs decidido) é determinada pelo
  call-site, não por um campo — um Ato `pendente` gera avisos com `_LINK_PENDENTE`; ao passar a
  `aprovado`/`rejeitado`, os avisos subsequentes usam `_LINK`. Avisos antigos **não** são
  reprocessados (mantêm o link com que foram criados).
