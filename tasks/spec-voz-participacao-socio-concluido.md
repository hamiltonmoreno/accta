# Spec — Voz e Participação do Sócio (Categoria 1)

> ⚠️ **ATUALIZAÇÃO (2026-06-15) — Feature 1.1 (Patrocínio de admissão, Art. 8.3)
> REMOVIDA.** O patrocínio de admissão foi removido ponta-a-ponta na release
> **v0.5.17** (PR #245): o auto-registo deixou de exigir 2 padrinhos, caiu o gate
> de aprovação e os endpoints `/participacao/patrocinios/*` + a página foram
> eliminados. A coleção `patrocinios` e os dados ficam em DB (dormentes, sem
> drop). A aprovação do pedido pela Direcção mantém-se. **As restantes 5
> funcionalidades (1.2–1.6) continuam em produção.** A §3 abaixo fica como
> registo histórico do que existiu.

> **Status**: rascunho técnico (2026-05-21). Requer validação da Direcção/Mesa da
> AG nas regras com efeito estatutário (limiares, maiorias, prazos) antes de
> implementar. É spec de produto/engenharia, **não** parecer jurídico.
> **Objetivo**: dar ao sócio canais formais e rastreáveis de participação na vida
> associativa — patrocínio de admissão, membros honorários, petição para AG
> extraordinária, propostas para a ordem de trabalhos, reclamações/recursos e
> pedidos de esclarecimento.
> **Estado do sistema**: ainda sem sócios reais em produção; aditivo é o padrão.
> Qualquer limpeza/migração em `users` continua a ser **stop condition**.
> **Base estatutária**: Art. 8.3 (patrocínio), 8.4 (honorários), 9.f/g/h/i/j
> (direitos de participação do sócio), 19.2.d (AG extraordinária a pedido de
> membros). Cada regra sensível guarda `source_article` no documento.

---

## 0. Âmbito e o que isto NÃO é

Esta spec cobre as **6 funcionalidades** da Categoria 1 ("Voz e participação do
sócio"):

| # | Funcionalidade | Artigo | Núcleo |
|---|---|---|---|
| ~~1.1~~ | ~~Patrocínio de admissão (2 padrinhos)~~ **[REMOVIDA — v0.5.17/#245]** | 8.3 | ~~bloqueia aprovação sem 2 patrocínios confirmados~~ |
| 1.2 | Membros honorários | 8.4 | Direcção nomeia → AG vota → 2/3 elege; categoria que não vota |
| 1.3 | Petição para AG extraordinária | 9.f, 19.2.d | sócios assinam; ao atingir 1/4 notifica a Mesa |
| 1.4 | Propostas/temas para a ordem de trabalhos | 9.g, 9.h | sócio submete; Mesa/Direcção tria e inclui na OT |
| 1.5 | Reclamações e recursos (genérico) | 9.i | reclama à Direcção; se não resolvido, recorre à AG |
| 1.6 | Pedidos de esclarecimento | 9.j | pergunta formal a um órgão, resposta escrita rastreável |

**O que isto NÃO é:**

- **Não é o módulo disciplinar.** 1.5 (reclamações/recursos) é o sócio a
  reclamar de actos que considera lesivos — sentido **sócio → órgão**. O regime
  disciplinar (`spec-governanca-estatutaria.md` §13, colecção `sancoes`) é o
  inverso: a associação a sancionar um sócio. Não confundir nem partilhar
  colecção.
- **Não constrói a Assembleia Geral.** O modelo `Assembleia`
  (`requerentes`, `requerente_tipo`, `ordem_trabalhos`, deliberações) pertence à
  `spec-governanca-estatutaria.md` (§11). Esta spec define apenas os **pontos de
  integração** com esse modelo e funciona de forma autónoma até ele existir.
- **Não decide voto digital vinculativo.** A votação de honorários (1.2) opera
  como apoio administrativo/registo, salvo validação expressa do Regimento.

---

## 1. Specs relacionadas e contrato de integração

- **`tasks/spec-auto-registo.md`** (implementado): fluxo de auto-registo
  (`POST /api/auth/register` → `status=pendente_aprovacao` → admin aprova em
  `routes/auth_routes.py`, handler `approve_registration`). **1.1 estende este
  fluxo** (não o substitui).
- **`tasks/spec-identidade-cargos.md`** (implementado): `account_type`
  (`member`/`technical`), `member_id` imutável, `cargo`/`cargo_history`,
  `privileges` aditivos, RBAC granular (`has_role_or_privilege`).
- **`tasks/spec-governanca-estatutaria.md`** (planeado, ainda não implementado):
  fornece os seguintes contratos de que esta spec depende. Onde ainda não
  existirem, esta spec **introduz a fatia mínima** e marca-a para reconciliação:
  - `member_category ∈ {fundador, ordinario, honorario}` (default `ordinario`),
    e `VOTING_CATEGORIES = {fundador, ordinario}` — **honorário não vota** (1.2).
  - Helpers de órgão: `is_direcao(user)`, `is_mesa_ag(user)`,
    `is_conselho_fiscal(user)`, `members_of_orgao(orgao)` (1.3–1.6).
  - `Assembleia` com `requerentes`, `requerente_tipo`, `ordem_trabalhos`,
    deliberações com maioria qualificada (1.2, 1.3, 1.4, 1.5-recurso).

**Princípio**: as 6 funcionalidades são **shippable de forma independente** da
implementação completa da governança. Cada uma guarda o seu próprio estado e
notifica o órgão competente; quando o módulo `Assembleia` existir, os "encaixes"
(petição → convocatória, proposta → ordem de trabalhos, recurso → deliberação)
ligam-se sem reescrita.

---

## 2. Decisões transversais (arquitetura)

### 2.1 Organização de módulos

| Funcionalidade | Onde vive |
|---|---|
| 1.1 Patrocínio | estende `routes/auth_routes.py` (register/approve) + nova colecção `patrocinios` + endpoints de confirmação em `routes/participacao.py` |
| 1.2 Honorários | `routes/participacao.py` (interim) — migra para `routes/governanca.py` quando existir; reusa `polls`/`user_votes` para a votação |
| 1.3–1.6 | **novo módulo `backend/routes/participacao.py`**, prefixo `/api`, colecções dedicadas |

`routes/participacao.py` segue o esqueleto da casa (ver `routes/polls.py`):
`router = APIRouter(tags=["participacao"])`, `current_user: User =
Depends(get_current_user)`, check de RBAC explícito, `create_audit_log` em toda a
escrita, notificação ao destinatário. Registar o router em `server.py` junto dos
restantes.

**Decisão**: colecções **separadas por domínio** (idioma do projecto: 1 colecção
= 1 domínio). 1.5 e 1.6 são parecidos mas têm ciclos de vida, RBAC e
sensibilidade distintos — uma tabela genérica com discriminador exigiria
condicionais a mais (anti-padrão face ao princípio "três linhas parecidas batem
uma abstracção prematura"). Partilham o **módulo** (`participacao.py`), não a
tabela.

### 2.2 Resolução de órgão e RBAC

Vários fluxos endereçam-se a "a Direcção", "a Mesa da AG" ou "o Conselho Fiscal".
Definir helpers em `backend/permissions.py` (ou `auth.py`), alinhados com a
`spec-governanca-estatutaria.md` §8:

```python
def is_direcao(user) -> bool: ...          # orgao_of_cargo(user.cargo) == "direcao"
def is_mesa_ag(user) -> bool: ...           # normalize_cargo(user.cargo).startswith("ag_")
def is_conselho_fiscal(user) -> bool: ...   # orgao == "conselho_fiscal"

async def members_of_orgao(orgao: str) -> list[str]:
    """IDs de utilizadores activos com cargo no órgão. Fallback: se nenhum
    titular estiver definido, devolve os admins (para não perder notificações
    antes da governança estar povoada)."""
```

**Interim (antes da governança)**: enquanto `orgao`/`cargo` não estiverem
povoados, `members_of_orgao` cai em `notify_admins`. Nunca falha silenciosamente.

`is_voting_member(user)` (introduzido aqui se ainda não existir):
`account_type == "member"` **e** `status == "ativo"` **e**
`member_category in VOTING_CATEGORIES` **e** sem `rights_suspended_until` vigente.
**A eligibilidade de voto em `routes/polls.py` passa a usar `is_voting_member`**
em vez de só `status == "ativo"` (necessário para excluir honorários — 1.2).

### 2.3 Convenções comuns

- **Estados** em `snake_case`; cada documento tem `created_at` ISO-8601 string,
  `created_by` (id do autor) e `source_article`.
- **Auditoria**: toda a escrita chama `create_audit_log(user_id, action,
  target_id, request=request, details={...})` com `action` em snake_case
  (ex.: `peticao_assinada`). (Nota: rotas legadas usam frases PT como acção; a
  convenção nova/recente é a key snake_case — seguir esta.)
- **Notificações**: usar `create_notification`/`notify_users`/`notify_admins`
  (assinaturas em `helpers.py`). Tipo de notificação: reusar `"system"` para
  avisos a órgãos e `"poll"` para a votação de honorários (evita mexer no
  mapeamento de ícones do frontend). Um tipo dedicado `"participacao"` é
  opcional e fica como decisão em aberto.
- **Contagem de membros elegíveis** (1.3 limiar, 1.2 base de voto): helper
  `count_voting_members()` em `helpers.py` — `db.users.count_documents` com
  filtro de elegibilidade. Usar `math.ceil` para limiares fraccionários.
- **Datas**: sempre ISO-8601 string no `doc` (regra do projecto; nunca
  `datetime` cru em `doc`).

### 2.4 Pontos de integração com `Assembleia` (forward-looking)

| Origem | Liga a |
|---|---|
| 1.3 Petição atingida | `Assembleia.requerente_tipo="membros"`, `requerentes=<signatários>` |
| 1.4 Proposta aceite | item em `Assembleia.ordem_trabalhos` |
| 1.5 Recurso | `Assembleia` + `AssembleiaDeliberacao` que decide o recurso |
| 1.2 Votação honorário | `AssembleiaDeliberacao` com `tipo_maioria="qualificada_2_3"` |

Até existirem, cada documento guarda os campos `assembleia_id`/`deliberacao_id`
como `Optional[str] = None`, preenchidos manualmente pela Mesa/admin.

---

## 3. Feature 1.1 — Patrocínio de admissão (Art. 8.3) — ❌ REMOVIDA (v0.5.17 / #245)

> **Esta funcionalidade foi removida ponta-a-ponta em 2026-06-15** (release
> v0.5.17, PR #245). O conteúdo abaixo é **registo histórico** do que existiu —
> não corresponde ao código atual. Auto-registo já não pede padrinhos; gate de
> aprovação removido; endpoints `/participacao/patrocinios/*` e `PatrociniosPage`
> eliminados; modelos `Patrocinio`/`PatrocinioRespond` e campos `sponsors`/
> `waive_sponsorship` removidos. Coleção `patrocinios` + dados ficam em DB (sem
> drop). Aprovação do pedido pela Direcção mantém-se.

**Resumo**: ao candidatar-se, o novo membro tem de ser apadrinhado por **2
sócios activos**; o sistema regista os padrinhos e **bloqueia a aprovação** sem
2 patrocínios confirmados.

### 3.1 Estado actual

`POST /api/auth/register` cria o candidato (`status=pendente_aprovacao`) e
`approve_registration` (`routes/auth_routes.py` ~169-231) gera o invite e
transita para `pendente_convite`. Não há qualquer noção de padrinho.

### 3.2 Modelo de dados

Nova colecção **`patrocinios`** (uma linha por par candidato↔padrinho — mais
fácil de consultar "candidatos à minha espera" do que um array embebido no
`users`, espelhando o padrão de `user_votes`):

```python
class Patrocinio(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    candidate_id: str           # users.id do candidato (pendente_aprovacao)
    sponsor_user_id: str        # users.id do sócio padrinho
    sponsor_member_id: str      # ACCTA-XXXX (snapshot p/ display)
    status: Literal["pendente", "confirmado", "recusado"] = "pendente"
    responded_at: Optional[str] = None
    note: Optional[str] = None
    created_at: str
    source_article: str = "8.3"
```

Índice único `(candidate_id, sponsor_user_id)` (um padrinho não patrocina o
mesmo candidato duas vezes). Índice por `sponsor_user_id` (inbox do padrinho) e
por `candidate_id` (contagem).

`RegistrationApprove` ganha um campo de dispensa (override admin, p/ bootstrap de
fundadores e excepções):

```python
class RegistrationApprove(BaseModel):
    role: str = "socio"
    cargo: Optional[str] = None
    waive_sponsorship: bool = False   # NOVO — dispensa Art. 8.3 (auditável)
```

### 3.3 Endpoints

**`POST /api/auth/register`** (estende o existente): aceita
`sponsors: list[str]` (exactamente 2 identificadores — `member_id` `ACCTA-XXXX`
ou email). Validações:
- cada identificador resolve para um utilizador `account_type=member`,
  `status=ativo` → senão 422 (mensagem neutra, sem enumeração).
- os 2 padrinhos têm de ser **distintos** e não-`technical`.
- cria 2 linhas `patrocinios` (`status=pendente`) e notifica cada padrinho.
- candidato fica `pendente_aprovacao` como hoje.

**`GET /api/participacao/patrocinios/pendentes`** (sócio activo): candidatos à
espera da MINHA confirmação (`sponsor_user_id == current_user.id`,
`status=pendente`).

**`POST /api/participacao/patrocinios/{candidate_id}/confirmar`** /
**`.../recusar`** (o padrinho nomeado): regista `confirmado`/`recusado` +
`responded_at`; auditoria; quando os 2 ficam `confirmado`, `notify_admins`
("candidato X tem patrocínio completo").

**`POST .../approve`** (modificado): antes de gerar o invite, calcular
`confirmados = count(patrocinios where candidate_id, status=confirmado)`. Se
`confirmados < 2` **e** `waive_sponsorship` for `False` → **409**
`"Aprovação bloqueada: faltam patrocínios (Art. 8.3)."`. Se dispensado, registar
`create_audit_log(..., "sponsorship_waived", ...)`.

`GET /api/admin/registration-requests` passa a incluir, por candidato, o resumo
`{sponsors: [{name, member_id, status}], confirmed_count}`.

### 3.4 RBAC, notificações, auditoria

- Confirmar/recusar: só o `sponsor_user_id` nomeado (sócio activo). Aprovar: admin.
- Notif.: a cada padrinho no submit; aos admins quando 2 confirmados.
- Audit: `patrocinio_pedido`, `patrocinio_confirmado`, `patrocinio_recusado`,
  `sponsorship_waived`.

### 3.5 Frontend

- `/criar-conta` (`pages/public/CriarContaPage.js`): 2 campos de padrinho
  (`member_id` ou email) + nota "Precisa de 2 sócios activos que confirmem o seu
  patrocínio (Art. 8.3)". Validação zod em `utils/authSchemas.js`.
- **Inbox do padrinho**: secção no Dashboard + página
  `/participacao/patrocinios` (lista "à minha espera", botões Confirmar
  (primário Carmesim) / Recusar (secundário)). Deep-link a partir da notificação.
- `AdminPedidosInscricaoPage.js`: badges de estado dos padrinhos por candidato;
  botão **Aprovar desabilitado** até 2 confirmados, com toggle "Dispensar
  patrocínio (Art. 8.3)" que o reactiva (e marca o override).
- `utils/api.js`: `patrociniosAPI = { pendentes, confirmar, recusar }`.

### 3.6 Decisões/abertos específicos

- Aplica-se ao **auto-registo**; no fluxo de **convite por admin** o patrocínio é
  **dispensado por omissão** (o convite do admin é já controlo de admissão).
  Tornar configurável (`require_two_sponsors`, default só no auto-registo).
- **Bootstrap de fundadores**: sem sócios activos no arranque não há padrinhos →
  usar `waive_sponsorship` nos primeiros membros (auditável).

### 3.7 Critérios de aceitação

Aprovar com <2 confirmados devolve 409; com 2 confirmados gera invite normalmente;
`waive_sponsorship=True` permite aprovar e fica auditado; um não-padrinho recebe
403 ao confirmar; padrão de email/anti-enumeração do auto-registo preservado.

---

## 4. Feature 1.2 — Membros honorários (Art. 8.4)

**Resumo**: a Direcção nomeia um honorário; a AG vota; só é eleito com **2/3 dos
votos**. Marca a categoria do membro e **exclui-o do voto comum**.

### 4.1 Estado actual

`member_category` ainda não existe (planeado na governança). O sistema de
`polls` conta votos em bruto, sem limiar/maioria, e a elegibilidade só verifica
`status == "ativo"`.

### 4.2 Modelo de dados

Introduzir `member_category` em `UserBase` (aditivo, default `"ordinario"`) e
`VOTING_CATEGORIES = {"fundador", "ordinario"}` (alinhado com a governança).

Nova colecção **`honorarios_nominations`**:

```python
class HonorarioNomination(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nominee_name: str
    nominee_user_id: Optional[str] = None   # se elevar membro existente
    nominee_email: Optional[str] = None      # se pessoa nova (vira convite se eleito)
    justificacao: str                        # serviços relevantes
    status: Literal["proposta", "em_votacao", "eleito", "rejeitado"] = "proposta"
    proposta_por: str                        # Direcção
    poll_id: Optional[str] = None            # votação 2/3 associada
    base_apuramento: Literal["validos", "presentes"] = "validos"
    votos_favor: Optional[int] = None
    votos_total_base: Optional[int] = None
    assembleia_id: Optional[str] = None
    deliberacao_id: Optional[str] = None
    created_at: str
    source_article: str = "8.4"
```

### 4.3 Votação 2/3

Interim (sem `Assembleia`): a abertura cria um `Poll` com opções
`[A favor, Contra, Abstenção]` (`status=aberta`), ligado por `poll_id`. O voto
reusa `POST /api/polls/vote` (já existente) restrito a `is_voting_member`. No
apuramento: `aprovado = votos_favor >= ceil(2/3 * base)`, onde
`base = votos_favor + votos_contra` (abstenções excluídas) por omissão.
**A base do 2/3 é decisão em aberto** (votos válidos vs. presentes vs. universo);
default = votos válidos emitidos. Quando a `Assembleia` existir, migrar para
`AssembleiaDeliberacao` com `tipo_maioria="qualificada_2_3"`.

### 4.4 Endpoints (`routes/participacao.py`)

- `POST /api/honorarios` (Direcção/admin) — cria nomeação (`proposta`).
- `GET /api/honorarios` / `GET /api/honorarios/{id}`.
- `POST /api/honorarios/{id}/abrir-votacao` (Mesa AG/admin) — cria o poll,
  `status=em_votacao`, notifica votantes.
- `POST /api/honorarios/{id}/apurar` (Mesa AG/admin) — fecha o poll, calcula 2/3,
  `eleito`/`rejeitado`. Em `eleito`: se `nominee_user_id`, seta
  `member_category="honorario"`; se pessoa nova, cria utilizador
  `pendente_convite` (reusa `send_invite_email`) com `member_category="honorario"`.

### 4.5 RBAC, notificações, auditoria

- Nomear: Direcção/admin. Abrir/apurar: Mesa AG/admin. Votar: `is_voting_member`.
- Honorário eleito **não vota** (excluído por `member_category`).
- Audit: `honorario_nomeado`, `honorario_votacao_aberta`, `honorario_apurado`.
- Notif.: votantes na abertura; Direcção/Mesa no apuramento; o próprio honorário
  (se já é utilizador) ao ser eleito.

### 4.6 Frontend

- `/governanca/honorarios` (gated Direcção/Mesa/admin): listar, nomear, abrir
  votação, ver resultado/2/3. O sócio vê a votação aberta na página `Votações`
  existente (sem nova UI de voto).
- `utils/api.js`: `honorariosAPI = { list, get, create, abrirVotacao, apurar }`.

### 4.7 Critérios de aceitação

Honorário eleito fica com `member_category="honorario"` e recebe 403 ao votar;
apuramento aplica o limiar 2/3 com `ceil`; nomear exige Direcção; abrir/apurar
exige Mesa/admin; sócio comum recebe 403 nessas acções.

---

## 5. Feature 1.3 — Petição para AG extraordinária (Art. 9.f, 19.2.d)

**Resumo**: página onde sócios assinam um pedido fundamentado de convocação; ao
atingir **1/4 dos membros**, notifica automaticamente a Mesa para convocar.

### 5.1 Modelo de dados

Colecção **`peticoes`** + **`peticao_assinaturas`** (assinaturas numa colecção
própria, como `user_votes`, para contagem distinta e índice único):

```python
class Peticao(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    titulo: str
    fundamentacao: str
    tipo: str = "ag_extraordinaria"
    threshold_fraction: float = 0.25     # 1/4
    target_count: Optional[int] = None   # snapshot do alvo no momento de atingir
    status: Literal["aberta", "atingida", "encaminhada", "encerrada", "expirada"] = "aberta"
    created_by: str
    created_at: str
    expires_at: Optional[str] = None
    met_at: Optional[str] = None
    assembleia_id: Optional[str] = None
    source_article: str = "9.f"

class PeticaoAssinatura(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    peticao_id: str
    user_id: str
    created_at: str
```

Índice único `(peticao_id, user_id)`; índice por `peticao_id` e por `status`.

### 5.2 Limiar

`target = ceil(count_voting_members() * 0.25)`. A cada assinatura recontar; se
`assinaturas >= target` **e** `status == "aberta"` → `status="atingida"`,
`met_at=now`, `target_count=target`, **notificar a Mesa AG uma única vez** (e
admins). Idempotente (não re-notifica em assinaturas subsequentes).

### 5.3 Endpoints (`routes/participacao.py`)

- `POST /api/peticoes` (votante) — cria.
- `GET /api/peticoes` / `GET /api/peticoes/{id}` (membros) — inclui
  `signature_count`, `target_count` e `viewer_has_signed`.
- `POST /api/peticoes/{id}/assinar` (votante) — assina (único). Reconta + limiar.
- `DELETE /api/peticoes/{id}/assinar` — retira assinatura (só enquanto `aberta`).
- `POST /api/peticoes/{id}/encaminhar` (Mesa AG/admin) — marca `encaminhada` e
  liga `assembleia_id` (integração governança; manual até existir).

### 5.4 RBAC, notificações, auditoria

- Criar/assinar: `is_voting_member`. Encaminhar: Mesa AG/admin.
- Audit: `peticao_criada`, `peticao_assinada`, `peticao_assinatura_retirada`,
  `peticao_atingiu_limiar`, `peticao_encaminhada`.
- Notif.: Mesa+admins ao atingir; signatários quando convocada.

### 5.5 Frontend

- `/participacao/peticoes`: lista + criar + assinar; detalhe com **barra de
  progresso** (`signature_count / target_count`) e estado. Só membros.
- `utils/api.js`: `peticoesAPI = { list, get, create, assinar, retirar, encaminhar }`.

### 5.6 Critérios de aceitação

Assinar duas vezes é bloqueado (índice único); ao cruzar 1/4 o estado vira
`atingida` e a Mesa é notificada uma só vez; não-votante recebe 403; barra de
progresso reflecte a contagem real.

---

## 6. Feature 1.4 — Propostas e temas para a ordem de trabalhos (Art. 9.g, 9.h)

**Resumo**: o sócio submete medidas ou pontos; a Mesa/Direcção recebe, tria e
pode incluí-los na próxima ordem de trabalhos.

### 6.1 Modelo de dados

Colecção **`propostas_ag`**:

```python
class PropostaAG(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    titulo: str
    descricao: str
    tipo: Literal["medida", "ponto", "tema"] = "ponto"
    status: Literal["submetida", "em_triagem", "aceite", "recusada", "incluida", "arquivada"] = "submetida"
    created_by: str
    created_at: str
    reviewer_id: Optional[str] = None
    reviewed_at: Optional[str] = None
    decisao_motivo: Optional[str] = None
    assembleia_id: Optional[str] = None
    ordem_index: Optional[int] = None
    source_article: str = "9.g"
```

### 6.2 Endpoints (`routes/participacao.py`)

- `POST /api/propostas-ag` (membro) — submete.
- `GET /api/propostas-ag` — membro vê as próprias + aceites/incluídas;
  Mesa/Direcção/admin vêem todas (filtro por `status`).
- `GET /api/propostas-ag/{id}`.
- `POST /api/propostas-ag/{id}/triagem` (Mesa/Direcção/admin) — `aceite`/
  `recusada` + `decisao_motivo`.
- `POST /api/propostas-ag/{id}/incluir` (Mesa/admin) — `incluida` + liga
  `assembleia_id`/`ordem_index` (integração governança).

### 6.3 RBAC, notificações, auditoria

- Submeter: membros. Triar/incluir: Mesa AG ou Direcção ou admin.
- Audit: `proposta_submetida`, `proposta_triada`, `proposta_incluida`.
- Notif.: Mesa/Direcção em nova submissão; autor na decisão e na inclusão.

### 6.4 Frontend

- `/participacao/propostas`: submeter + acompanhar as próprias.
- `/governanca/propostas` (ou a mesma página, role-gated): vista de triagem para
  Mesa/Direcção.
- `utils/api.js`: `propostasAgAPI = { list, get, create, triar, incluir }`.

### 6.5 Critérios de aceitação

Membro vê só as suas + as aceites; triagem/inclusão exigem Mesa/Direcção; autor é
notificado da decisão; inclusão regista a assembleia-alvo.

---

## 7. Feature 1.5 — Reclamações e recursos (Art. 9.i)

**Resumo**: canal para reclamar à Direcção de actos que considere lesivos e, se
não resolvido, recorrer à Assembleia. **Genérico (não disciplinar)**, com prazos
e estado.

### 7.1 Modelo de dados

Colecção **`reclamacoes`** (conteúdo **sensível**: visível só ao autor +
Direcção + admin):

```python
class Reclamacao(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assunto: str
    descricao: str
    status: Literal["submetida", "em_analise", "respondida", "resolvida", "recurso", "encerrada"] = "submetida"
    created_by: str
    created_at: str
    prazo_resposta: Optional[str] = None     # SLA configurável (ex.: +15 dias)
    direcao_resposta: Optional[dict] = None   # {by, at, text}
    resolvida: Optional[bool] = None
    recurso: Optional[dict] = None            # {opened_at, by, status, assembleia_id, deliberacao_id, decisao}
    source_article: str = "9.i"
```

### 7.2 Endpoints (`routes/participacao.py`)

- `POST /api/reclamacoes` (membro) — submete; define `prazo_resposta`.
- `GET /api/reclamacoes` — autor vê as próprias; Direcção/admin vêem todas.
- `GET /api/reclamacoes/{id}` — 403 se não for autor/Direcção/admin.
- `POST /api/reclamacoes/{id}/responder` (Direcção/admin) — grava
  `direcao_resposta`, `status=respondida`/`resolvida`.
- `POST /api/reclamacoes/{id}/recurso` (autor) — `status=recurso` (só após
  resposta ou prazo expirado).
- `POST /api/reclamacoes/{id}/decidir-recurso` (Mesa AG/admin) — regista decisão
  da AG (liga `assembleia_id`/`deliberacao_id`).

### 7.3 RBAC, sensibilidade, notificações, auditoria

- **Não confundir com `sancoes`** (disciplinar, governança §13).
- Conteúdo só para autor + Direcção + admin (respostas ocultam para outros).
- Audit: `reclamacao_submetida`, `reclamacao_respondida`, `reclamacao_recurso`,
  `reclamacao_decidida`.
- Notif.: Direcção em nova; autor na resposta; Mesa/AG no recurso. Aviso de prazo
  a expirar (Direcção) — opcional.

### 7.4 Frontend

- `/participacao/reclamacoes`: submeter + acompanhar estado/prazo; abrir recurso.
- Vista Direcção para responder (role-gated).
- `utils/api.js`: `reclamacoesAPI = { list, get, create, responder, recurso, decidirRecurso }`.

### 7.5 Critérios de aceitação

Não-autor sem cargo recebe 403 no detalhe; recurso só abre após resposta/prazo;
decisão de recurso exige Mesa/AG; conteúdo não vaza para sócios sem permissão.

---

## 8. Feature 1.6 — Pedidos de esclarecimento (Art. 9.j)

**Resumo**: o sócio faz uma pergunta formal a um órgão (Direcção/Mesa/CF) e
recebe **resposta escrita rastreável**.

### 8.1 Modelo de dados

Colecção **`esclarecimentos`**:

```python
class Esclarecimento(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    orgao_destino: Literal["direcao", "mesa_ag", "conselho_fiscal"]
    assunto: str
    pergunta: str
    status: Literal["submetido", "respondido", "encerrado"] = "submetido"
    created_by: str
    created_at: str
    prazo_resposta: Optional[str] = None
    resposta: Optional[dict] = None       # {by, at, text}
    source_article: str = "9.j"
```

### 8.2 Endpoints (`routes/participacao.py`)

- `POST /api/esclarecimentos` (membro) — body inclui `orgao_destino`.
- `GET /api/esclarecimentos` — autor vê os próprios; membros do órgão-destino
  vêem os endereçados ao seu órgão; admin vê tudo.
- `GET /api/esclarecimentos/{id}`.
- `POST /api/esclarecimentos/{id}/responder` (membro do órgão-destino ou admin) —
  grava `resposta`, `status=respondido`.

### 8.3 RBAC, notificações, auditoria

- Perguntar: membros. Responder: membro do `orgao_destino`
  (`is_direcao`/`is_mesa_ag`/`is_conselho_fiscal`) ou admin.
- Audit: `esclarecimento_submetido`, `esclarecimento_respondido`.
- Notif.: `members_of_orgao(orgao_destino)` em nova pergunta; autor na resposta.

### 8.4 Frontend

- `/participacao/esclarecimentos`: perguntar (escolhe órgão) + acompanhar.
- Inbox por órgão (role/cargo-gated) para responder.
- `utils/api.js`: `esclarecimentosAPI = { list, get, create, responder }`.

### 8.5 Critérios de aceitação

Pergunta chega ao órgão certo; só membro desse órgão (ou admin) responde; resposta
fica rastreável (audit + `resposta.by/at`); autor é notificado.

---

## 9. Colecções e índices (consolidado)

Adicionar ao tuplo `COLLECTIONS` em `backend/database.py` (acessível como
`db.<name>` dinamicamente) e o DDL a `_INDEX_DDL`:

| Colecção | Índices mínimos |
|---|---|
| `patrocinios` | unique `(candidate_id, sponsor_user_id)`; `sponsor_user_id`; `candidate_id` |
| `honorarios_nominations` | `status`; `nominee_user_id` |
| `peticoes` | `status`; `created_at` DESC |
| `peticao_assinaturas` | unique `(peticao_id, user_id)`; `peticao_id` |
| `propostas_ag` | `status`; `created_by`; `created_at` DESC |
| `reclamacoes` | `created_by`; `status` |
| `esclarecimentos` | `orgao_destino`; `created_by`; `status` |

Padrão DDL (ver `_INDEX_DDL` existente):
`CREATE [UNIQUE] INDEX IF NOT EXISTS ix_<t>_<f> ON "<t>" ((doc->>'<f>'))`.
A votação de honorários reusa `polls`/`user_votes` — sem colecção nova.

---

## 10. Frontend (consolidado)

- **Nova secção de sidebar "Participação"** em `PrivateLayout.js` (`menuSections`):
  Petições, Propostas, Reclamações, Esclarecimentos, Patrocínios (com badge de
  pendentes do próprio). `roles: ['all']` para o sócio; itens de
  triagem/órgão (Honorários, vistas Direcção/Mesa) gated por `roles`/`privileges`
  ou cargo.
- **Rotas** em `App.js` sob `/participacao/*` e `/governanca/honorarios`,
  envolvidas em `<ProtectedRoute allowedRoles=[...] allowedPrivileges=[...]>`
  (padrão existente). Páginas em `pages/private/`.
- **`AuthContext`**: adicionar helpers `isMesaAG`, `isDirecao`,
  `isConselhoFiscal`, `isVotingMember` (espelho do backend) para gating de UI.
- **Design**: sistema neutral-led + Carmesim como único acento (≤1 botão
  primário por vista); sem dark mode; seguir o skill `frontend-design`.
  Estados de loading com `Skeleton`; empty states em PT.

---

## 11. Plano de execução faseado

PRs pequenos, um por funcionalidade, em `feature/* → develop` (GitFlow). Não
misturar com migração destrutiva.

| Fase | Entrega | Depende |
|---|---|---|
| F0 | Transversais: `member_category` (aditivo), helpers de órgão + `is_voting_member` + `count_voting_members`; eligibilidade de `polls` passa a `is_voting_member`; `routes/participacao.py` registado | — |
| F1 | **1.1 Patrocínio** (colecção, register/approve gate, confirmação, UI) | F0 |
| F2 | **1.3 Petição** (colecções, limiar 1/4, UI) | F0 |
| F3 | **1.6 Esclarecimentos** + **1.5 Reclamações** (parecidos; mesmo módulo) | F0 |
| F4 | **1.4 Propostas OT** | F0 |
| F5 | **1.2 Honorários** (nomeação + votação 2/3 via poll; categoria) | F0 |
| F6 | Reconciliação com `Assembleia` quando existir (encaixes 2.4) | governança |

### Ordem dentro de cada fase

Models + status → schema/índices em `ensure_schema()` → endpoints + RBAC + audit
→ testes backend → frontend (página + api.js + sidebar) → testes frontend →
verificação manual no browser (golden path + edge cases).

---

## 12. Testes obrigatórios

**Backend (unit/in-process, `conftest.py`):** lembrar que colecções novas **não
estão pré-cabladas** no `mock_db` — cablar em-teste (`mock_db.peticoes =
MagicMock(...)` com `AsyncMock`s). Casos-chave:

- 1.1: approve com 0/1/2 confirmados (409 vs. sucesso); `waive_sponsorship`
  permite e audita; não-padrinho 403; auto-sponsor/duplicado rejeitado.
- 1.2: `is_voting_member` exclui honorário/inactivo/técnico/suspenso; apuramento
  2/3 com `ceil` (limites: exactamente 2/3, just-below); nomear exige Direcção.
- 1.3: assinatura única (índice); limiar `ceil(n/4)` dispara `atingida` +
  notifica Mesa **uma vez**; retirar assinatura só enquanto `aberta`.
- 1.4: visibilidade (autor vê próprias; Mesa vê todas); triagem exige Mesa/Direcção.
- 1.5: detalhe 403 para terceiros; recurso só após resposta/prazo; **não** toca
  `sancoes`.
- 1.6: resposta só por membro do `orgao_destino`/admin; routing por órgão.

**Frontend:** render+submit de cada página (happy/erro), gating de menu por
role/cargo, barra de progresso da petição, botão Aprovar desabilitado sem 2
patrocínios.

---

## 13. Stop conditions (CLAUDE.md)

Confirmar com o utilizador antes de:

- Migrar/limpar dados em `users` (ex.: backfill de `member_category`) — usar
  default aditivo, sem reescrita destrutiva.
- Enviar emails reais (invite de honorário eleito; rejeição). Em piloto, validar
  com inbox de dev.
- Tratar a votação de honorários como **juridicamente vinculativa** sem validação
  do Regimento (default: apoio administrativo).
- Alterar Pydantic de forma incompatível com documentos existentes (tudo aqui é
  aditivo/opcional).
- Remover rotas que o frontend chama.

---

## 14. Decisões em aberto

1. **1.1 — captura de padrinhos**: candidato indica 2 padrinhos no formulário
   público (recomendado) **ou** o admin atribui na revisão? Recomendação:
   candidato indica + padrinhos confirmam no portal.
2. **1.1 — âmbito**: patrocínio só no auto-registo (recomendado) ou também no
   convite por admin?
3. **1.2 — base do 2/3**: votos válidos emitidos (recomendado), presentes em AG,
   ou universo de membros?
4. **1.2 — honorário externo**: permitir nomear não-membro (cria conta se eleito)
   ou só elevar membro existente?
5. **1.3 — limiar**: 1/4 dos **membros votantes** (recomendado) ou do universo
   total (inclui honorários/técnicos)? Confirmar com o estatuto.
6. **1.5 — SLA de resposta** da Direcção: prazo default (ex.: 15 dias) e se o
   incumprimento abre recurso automaticamente.
7. **Tipo de notificação dedicado** (`"participacao"`) com ícone próprio, ou
   reutilizar `"system"`/`"poll"` (recomendado para já)?
8. **Módulo de honorários**: nascer em `routes/participacao.py` (recomendado,
   interim) ou esperar por `routes/governanca.py`?
