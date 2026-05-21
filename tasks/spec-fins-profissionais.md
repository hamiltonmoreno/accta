# Spec — Fins Profissionais e Relações (Categoria 5)

> **Status**: rascunho técnico (2026-05-21). Requer validação da Direcção no que
> toca a tomadas de posição públicas (reputacional) e a filiações. Spec de
> produto/engenharia, **não** parecer jurídico.
> **Objetivo**: dar ao portal os fins profissionais e relações institucionais da
> ACCTA — grupos de trabalho/comissões, defesa profissional, desenvolvimento
> técnico-profissional, cooperação/filiação (IFATCA) e publicações.
> **Estado do sistema**: sem dados reais; aditivo é o padrão.
> **Base estatutária**: Art. 31.e (grupos de trabalho), 2.a (defesa profissional),
> 2.c (desenvolvimento técnico), 2.f/31.g/53 (cooperação/IFATCA), 5.c
> (publicações). `source_article` em cada documento.

---

## 0. Âmbito

As **5 funcionalidades** da Categoria 5:

| # | Funcionalidade | Artigo | Núcleo |
|---|---|---|---|
| 5.1 | Grupos de trabalho / comissões | 31.e | **reusa o módulo de projetos** |
| 5.2 | Defesa profissional | 2.a | registo de representações/tomadas de posição |
| 5.3 | Desenvolvimento técnico-profissional | 2.c | catálogo de formações/certificações + materiais |
| 5.4 | Cooperação e filiação IFATCA | 2.f, 31.g, 53 | diretório de relações + estado de filiação |
| 5.5 | Publicações | 5.c | publicar/distribuir (e eventualmente vender) |

---

## 1. Specs relacionadas e dependências

- **Módulo de projetos** (implementado): `Project` (status proposta→aprovado→
  em_curso→concluido→cancelado, `responsible_id`, `category`, `budget`/`progress`,
  `visibility`) + `project_tasks`/`milestones`/`expenses`/`comments`, com
  `can_manage_project` (criador/responsável/admin) e admin-cria→`aprovado`. **5.1
  reusa-o.**
- **`tasks/spec-governanca-estatutaria.md` §4.7**: grupos de trabalho/
  coordenadores são **funções operacionais**, **não** cargos estatutários. Em 5.1
  o coordenador é o `responsible_id` do projeto — **nunca** entra em
  `cargo_history`.
- **Módulo de documentos** (implementado): anexos de 5.2 (representações), 5.3
  (materiais), 5.4 (acordos) e 5.5 (ficheiros). Download público
  (`/api/documents/{id}/public/download`).
- **`tasks/spec-controlos-financeiros.md` (Categoria 4)**: a venda de publicações
  (5.5, "eventual") liga-se à receita `category="venda_publicacoes"` e a
  `invoices` — **forward-looking**.
- **`tasks/spec-blog-noticias.md`**: notícias/blog são distintas das
  **publicações** formais (revista/boletim/relatório técnico) — não confundir.
- **Página pública `ProfissaoPage.js`**: superfície natural para defesa
  profissional publicada, relações e formações públicas.

---

## 2. Diagnóstico do estado actual

- **Projetos**: módulo completo e reusável (ver §1). Tem `category` (livre) mas
  **não distingue** grupo de trabalho/comissão de projeto normal.
- **Documentos/Benefícios**: existem; o catálogo de benefícios (`Benefit` +
  `manage_benefits`) é um bom **molde** para o catálogo de formações (5.3), mas é
  domínio distinto.
- **Faturas**: `Invoice` (`user_id`, `type`, `amount`, `status` pendente/pago,
  `source`) — base para a venda de publicações (5.5).
- **Não existe**: defesa profissional, catálogo de formações, diretório de
  relações/IFATCA, publicações.

---

## 3. Decisões transversais (arquitetura)

1. **Módulos**: 5.1 estende `routes/projects.py` (campo + RBAC + filtro); 5.2–5.5
   num novo `backend/routes/profissional.py` (prefixo `/api`). Esqueleto da casa,
   `create_audit_log` em toda a escrita, datas ISO-8601.
2. **5.1 reusa projetos sem novo módulo**: campo aditivo `tipo` na `Project`
   (`projeto`|`grupo_trabalho`|`comissao`, default `projeto`); coordenador =
   `responsible_id` (função operacional). Evita duplicar tasks/milestones/etc.
   (princípio "não abstrair prematuramente").
3. **Visibilidade**: cada entidade tem `visibility` (`socios`|`publico`); o que
   for `publico` aparece na `ProfissaoPage`/página de Publicações via o fluxo de
   documentos existente.
4. **Venda de publicações = fase 2**: o estatuto diz "eventualmente vender"; a
   distribuição (download) entra já, a **venda** fica desenhada e integra Cat. 4
   (`venda_publicacoes`/`invoices`) numa fase posterior.
5. **RBAC**: gestão por Direcção/admin (helper `is_direcao` da Cat. 4/governança;
   interim admin + privilégio); leitura por sócios; subconjunto público.
6. **Aditivo**: `Project.tipo` é aditivo/opcional → não quebra projetos
   existentes.

---

## 4. Feature 5.1 — Grupos de trabalho / comissões (Art. 31.e)

**Resumo**: a Direcção cria grupos eventuais, designa coordenadores e acompanha
estudos/atividades — reusando o módulo de projetos.

### 4.1 Modelo

Campo aditivo na `Project`:

```python
tipo: Literal["projeto", "grupo_trabalho", "comissao"] = "projeto"
```

- **Coordenador** = `responsible_id` (+ `responsible_name`) — função operacional
  (governança §4.7), **não** cargo; não toca `cargo_history`.
- **Grupos eventuais** (ad-hoc): encerram-se com `end_date` + `status` em
  `concluido`/`cancelado`. Estudos/atividades = `project_tasks`/`milestones`/
  `expenses`/`comments` existentes.

### 4.2 Endpoints (reusa `routes/projects.py`)

- `POST /api/projects` com `tipo="grupo_trabalho"|"comissao"`: **só Direcção/admin**
  cria estes (Art. 31.e) e ficam logo `aprovado` (projetos normais seguem o fluxo
  actual — sócio ativo → `proposta`).
- `GET /api/projects?tipo=grupo_trabalho` (filtro novo).
- Restantes (tasks/milestones/expenses/comments, designar `responsible_id`,
  aprovar) **inalterados**.

### 4.3 RBAC, auditoria, frontend

- Criar grupo/comissão: Direcção/admin. Gerir: `can_manage_project` (coordenador =
  `responsible_id`, criador, admin). Auditoria já existente + `tipo` no log.
- Frontend: na `ProjectsPage`, abas/filtro **Projetos · Grupos de Trabalho ·
  Comissões**; badge de `tipo`; coordenador destacado.

### 4.4 Critérios de aceitação

A Direcção cria um grupo/comissão já `aprovado` com coordenador; reusa tasks/
milestones/despesas/comentários; o coordenador **não** vira cargo estatutário;
filtro por `tipo` funciona; projetos normais mantêm o fluxo `proposta→aprovado`.

---

## 5. Feature 5.2 — Defesa profissional (Art. 2.a)

**Resumo**: registo de representações e tomadas de posição em defesa dos
interesses profissionais dos controladores.

### 5.1 Modelo — colecção `defesa_profissional`

```python
class DefesaProfissional(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    titulo: str
    tipo: Literal["representacao", "tomada_posicao", "comunicado"]
    descricao: str
    entidade_destino: Optional[str] = None     # a quem foi dirigida (regulador, entidade patronal…)
    data: str
    status: Literal["rascunho", "publicado", "arquivado"] = "rascunho"
    document_id: Optional[str] = None
    visibility: Literal["socios", "publico"] = "socios"
    created_by: str
    created_at: str
    source_article: str = "2.a"
```

### 5.2 Endpoints (`routes/profissional.py`), RBAC, frontend

- `POST/GET/GET{id}/PATCH/DELETE /api/defesa-profissional`;
  `POST .../{id}/publicar` (rascunho→publicado).
- Criar/gerir/publicar: Direcção/admin. Ver: sócios; `publicado`+`publico` →
  `ProfissaoPage` pública.
- Frontend: gestão (Direcção) + lista para sócios; publicadas na página pública.
- Audit: `defesa_criada`, `defesa_publicada`, `defesa_arquivada`.

### 5.3 Critérios de aceitação

Registo com tipo/entidade; publicar torna público (após decisão da Direcção);
arquivável; sócios vêem `socios`, público só vê `publicado`+`publico`.

---

## 6. Feature 5.3 — Desenvolvimento técnico-profissional (Art. 2.c)

**Resumo**: catálogo de formações/certificações e materiais para o
desenvolvimento dos membros.

### 6.1 Modelo — colecção `formacoes`

```python
class Formacao(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    titulo: str
    tipo: Literal["formacao", "certificacao", "material"]
    descricao: str
    entidade: Optional[str] = None              # provedor/entidade formadora
    categoria: Optional[str] = None
    url: Optional[str] = None                    # inscrição/recurso externo
    document_id: Optional[str] = None            # material anexo
    data: Optional[str] = None
    validade: Optional[str] = None               # certificações
    ativo: bool = True
    created_by: str
    created_at: str
    source_article: str = "2.c"
```

### 6.2 Endpoints, RBAC, frontend, critérios

- `POST/GET/GET{id}/PATCH/DELETE /api/formacoes`. Gerir: Direcção/admin (ou
  privilégio dedicado `manage_formacoes` — decisão em aberto). Ver: sócios
  (catálogo). Materiais via documentos.
- Frontend: catálogo navegável (cartões por tipo/categoria) + gestão Direcção.
- Audit: `formacao_criada`/`atualizada`/`removida`.
- Critérios: sócios navegam o catálogo; só Direcção gere; materiais descarregáveis;
  certificações com validade.

---

## 7. Feature 5.4 — Cooperação e filiação IFATCA (Art. 2.f, 31.g, 53)

**Resumo**: diretório de relações com a IFATCA e associações congéneres, com o
estado da filiação.

### 7.1 Modelo — colecção `relacoes_externas`

```python
class RelacaoExterna(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str                                    # ex.: "IFATCA"
    tipo: Literal["federacao_internacional", "associacao_congenere", "parceiro"]
    descricao: Optional[str] = None
    website: Optional[str] = None
    contacto: Optional[str] = None
    estado_filiacao: Literal["filiado", "em_negociacao", "nao_filiado", "suspenso"] = "nao_filiado"
    desde: Optional[str] = None
    quota_anual: Optional[float] = None
    logo_url: Optional[str] = None
    documentos: list[str] = []                   # acordos/protocolos (document_id)
    visibility: Literal["socios", "publico"] = "socios"
    created_by: str
    created_at: str
    source_article: str = "2.f"
```

Semear a **IFATCA** (`tipo="federacao_internacional"`).

### 7.2 Endpoints, RBAC, critérios

- `POST/GET/GET{id}/PATCH/DELETE /api/relacoes-externas`. Gerir: Direcção/admin.
  Ver: sócios; `publico` → página pública de relações/parceiros.
- Frontend: diretório com logos, estado de filiação (badge), `desde`, acordos
  anexos.
- Audit: `relacao_criada`/`atualizada`/`removida`.
- Critérios: diretório com estado de filiação; IFATCA presente; acordos
  anexáveis; gestão só pela Direcção.

---

## 8. Feature 5.5 — Publicações (Art. 5.c)

**Resumo**: espaço para publicar/distribuir (e eventualmente vender) publicações
da associação.

### 8.1 Modelo — colecção `publicacoes`

```python
class Publicacao(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    titulo: str
    descricao: Optional[str] = None
    tipo: Literal["revista", "boletim", "artigo", "relatorio_tecnico"]
    autor: Optional[str] = None
    document_id: str                             # ficheiro principal (PDF)
    capa_url: Optional[str] = None
    data_publicacao: str
    visibility: Literal["publico", "socios"] = "socios"
    a_venda: bool = False                         # FASE 2
    preco: Optional[float] = None
    created_by: str
    created_at: str
    source_article: str = "5.c"
```

### 8.2 Distribuição e venda

- **Distribuição (fase 1)**: download via documentos conforme `visibility`
  (`publico`/`socios`). Publicações `publico` aparecem na página pública.
- **Venda (fase 2, "eventual")**: quando `a_venda`, a compra gera um `Invoice`
  (`type="publicacao"`) e/ou uma receita `category="venda_publicacoes"` (Cat. 4).
  `POST /api/publicacoes/{id}/comprar` fica desenhado mas **não** entra na fase 1.

### 8.3 Endpoints, RBAC, critérios

- `POST/GET/GET{id}/PATCH/DELETE /api/publicacoes`. Gerir: Direcção/admin
  (`manage_documents`). Ver: conforme `visibility`.
- Distinção do blog/notícias (`spec-blog-noticias.md`): publicações são formais
  (revista/boletim/relatório técnico), não notícias.
- Critérios: catálogo + download conforme visibilidade; venda desenhada mas em
  fase 2; público vê só `publico`.

---

## 9. Colecções e índices

| Colecção | Índices mínimos |
|---|---|
| `defesa_profissional` | `status`; `(visibility, status)`; `data` DESC |
| `formacoes` | `tipo`; `ativo`; `categoria` |
| `relacoes_externas` | `tipo`; `estado_filiacao` |
| `publicacoes` | `tipo`; `(visibility, data_publicacao)` DESC |

5.1 reusa `projects` (campo aditivo `tipo`, sem colecção nova). Ficheiros/anexos
reusam `documents`.

---

## 10. Frontend (consolidado)

- **Secção de sidebar "Profissional"**: Grupos de Trabalho/Comissões (via
  Projetos), Defesa Profissional, Formação & Certificação, Relações/IFATCA,
  Publicações. Gestão gated por Direcção/admin; leitura por sócios.
- **`ProjectsPage`**: abas/filtro por `tipo` (5.1) + badge.
- **Páginas novas** (`pages/private/`): catálogo de formações, diretório de
  relações, lista de publicações, gestão de defesa profissional.
- **Público**: `ProfissaoPage` ganha defesa profissional publicada + relações
  públicas + formações públicas; **página pública de Publicações** para os
  ficheiros `publico`.
- Design neutral-led + Carmesim, sem dark mode (skill `frontend-design`).
- `utils/api.js`: `defesaProfissionalAPI`, `formacoesAPI`, `relacoesAPI`,
  `publicacoesAPI`; extensão de `projectsAPI` (filtro `tipo`).

---

## 11. Plano de execução faseado

PRs pequenos, `feature/* → develop`.

| Fase | Entrega | Depende |
|---|---|---|
| F0 | `Project.tipo` aditivo; `routes/profissional.py` registado; helper `is_direcao` (Cat. 4) | Cat. 4 F0 |
| F1 | **5.1** Grupos/Comissões (tipo + RBAC Direcção + filtro + UI) | F0 |
| F2 | **5.3** Formações + **5.5** Publicações (catálogos + distribuição) | F0 |
| F3 | **5.2** Defesa profissional + **5.4** Relações/IFATCA | F0 |
| F4 | Superfícies públicas (`ProfissaoPage`, Publicações) | F1–F3 |
| F5 | **Venda de publicações** (integra Cat. 4 `invoices`/`venda_publicacoes`) | Cat. 4 + confirmação |

### Ordem dentro de cada fase

Models/campos → schema/índices (`ensure_schema`) → endpoints + RBAC + audit →
testes backend → frontend → testes frontend → verificação manual (criar grupo de
trabalho com coordenador; publicar uma tomada de posição; semear IFATCA; carregar
uma publicação e descarregá-la conforme visibilidade).

---

## 12. Testes obrigatórios

Colecções novas **não** estão pré-cabladas no `mock_db` — cablar em-teste.

- 5.1: só Direcção/admin cria `grupo_trabalho`/`comissao` (sócio comum → 403);
  grupo criado fica `aprovado`; coordenador (`responsible_id`) **não** altera
  `cargo_history`; filtro `?tipo=` devolve só o tipo certo; projeto normal mantém
  `proposta`.
- 5.2: publicar muda `status`/visibilidade; público só vê `publicado`+`publico`.
- 5.3: catálogo visível a sócios; só Direcção gere; certificação com validade.
- 5.4: diretório com `estado_filiacao`; IFATCA semeada; só Direcção gere.
- 5.5: download conforme `visibility`; `comprar` **não** existe na fase 1; gestão
  só Direcção.

Frontend: filtro de `tipo` em Projetos; catálogo de formações; diretório de
relações; lista de publicações; superfícies públicas; gating por `isDirecao`.

---

## 13. Stop conditions (CLAUDE.md)

Confirmar com o utilizador antes de:

- **Publicar tomadas de posição reais** (reputacional/efeito externo).
- Implementar a **venda** de publicações (envolve `invoices`/receita — Cat. 4).
- Enviar emails reais; remover rotas que o frontend chama.
- Alterar Pydantic para além de campos aditivos/opcionais (`Project.tipo` é
  aditivo).

---

## 14. Decisões em aberto

1. **5.1 grupos**: distinguir por `Project.tipo` (recomendado) ou por convenção em
   `category`? E confirmar que **só a Direcção** cria grupos/comissões.
2. **5.3 gestão**: privilégio dedicado `manage_formacoes` ou role Direcção/admin
   (recomendado para já)?
3. **5.2 publicação**: as tomadas de posição passam por **aprovação interna** da
   Direcção antes de ficarem públicas (recomendado), e quais são públicas vs. só
   sócios?
4. **5.4 visibilidade**: o diretório de relações/IFATCA é público ou só para
   sócios?
5. **5.5 venda**: fase 2 — pagamento via `invoices` (folha/admin) ou gateway
   externo? Preço/moeda (CVE)? Sócios pagam preço diferente?
6. **Publicações vs. notícias**: confirmar a fronteira com o `spec-blog-noticias`
   (revista/boletim/relatório técnico aqui; notícias/blog lá).
7. **Materiais de formação**: só link/anexo (recomendado) ou também controlo de
   inscrições/conclusões dos membros?
