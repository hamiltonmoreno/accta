# Spec — Sessão da Assembleia "ao vivo" (Categoria 2)

> **Status**: rascunho técnico (2026-05-21). Requer validação da Mesa da AG/
> Regimento nas regras com efeito processual (quórum, modos de voto, cronómetros,
> prazos). Spec de produto/engenharia, **não** parecer jurídico.
> **Objetivo**: dar ao portal a **camada de condução ao vivo** de uma sessão da
> Assembleia Geral — check-in + quórum automático, fila de uso da palavra com
> cronómetros, moções/requerimentos/recomendações em sessão, período "antes da
> ordem de trabalhos", modos de votação com conflito de interesses, e gestão de
> documentos da sessão e convidados.
> **Estado do sistema**: sem sócios reais; aditivo é o padrão. Mexer em `users` é
> stop condition.
> **Base (Regimento/Estatutos)**: Art. 5, 21 (quórum/presenças), 21/27/28/29
> (uso da palavra), 6, 26 (requerimentos a voto imediato), 14 (antes da ordem de
> trabalhos), 32 (modos de voto e conflito de interesses), 20, 36 (documentos e
> convidados). Cada regra sensível guarda `source_article`.

---

## 0. Âmbito e ressalva: assembleias **online** (videochamada/Meet)

**Ressalva do produto (confirmada pelo utilizador)**: as assembleias correm
**tipicamente online**, através de um link de videochamada (Meet/Zoom/Teams). O
portal **não aloja vídeo** — é a **camada de governança/controlo** que corre ao
lado da chamada. Consequências de design, transversais a todas as
funcionalidades:

- A `Assembleia` ganha `modo ∈ {presencial, online, hibrido}` e um
  `meeting_link` (URL externa) + `meeting_provider`/`meeting_notes`. O portal
  mostra o botão "Entrar na reunião" aos presentes; **link out**, sem iframe
  (a maioria dos fornecedores bloqueia embedding).
- **Check-in** tem de funcionar **remotamente**: o caminho primário é o
  **self check-in autenticado** (o sócio com sessão iniciada confirma presença
  com um **código de sessão** partilhado na chamada). O scan do QR pessoal
  (carteira) mantém-se como caminho **presencial** alternativo.
- **Fila de palavra, votação e quórum** são em **tempo real** — reutilizam e
  estendem o mecanismo SSE existente (polling), agora **por-assembleia**.
- **Braço no ar** numa chamada de vídeo não é auto-contável: a Mesa **regista a
  contagem agregada** manualmente; voto **nominal**/**secreto** são digitais.

**Cada uma das 6 funcionalidades** da Categoria 2:

| # | Funcionalidade | Artigo |
|---|---|---|
| 2.1 | Check-in por QR + quórum automático | 5, 21 |
| 2.2 | Fila de uso da palavra com cronómetros | 21, 27, 28, 29 |
| 2.3 | Moções, requerimentos e recomendações em sessão | 6, 26 |
| 2.4 | Período "antes da ordem de trabalhos" (máx. 30 min) | 14 |
| 2.5 | Modos de votação + conflito de interesses + voto separado | 32 |
| 2.6 | Documentos da sessão (≥3 dias) + convidados | 20, 36 |

---

## 1. Dependência: a `Assembleia` da governança é **pré-requisito**

Esta spec é o **runtime** de uma `Assembleia`. O **núcleo** (convocatória,
estados, presenças, deliberações, quórum, ordem de trabalhos, helpers de órgão,
`is_voting_member`) é definido em **`tasks/spec-governanca-estatutaria.md` §11**
e **ainda não está implementado** (confirmado: não há `governance.py`,
`assembleias`, `presenca`, `deliberacao`, `quorum` no código; o `Event` aceita
`type="assembleia"` mas sem lógica).

**Contrato**: Categoria 2 **consome** da governança e **adiciona** a camada ao
vivo. Não redefine o núcleo. Se a Categoria 2 for implementada antes da
governança completa, a fatia mínima da `Assembleia` (do §11 da governança) é
pré-requisito da Fase F0 — implementar primeiro esse núcleo, não duplicá-lo.

| Vem da governança (§11) | Adicionado por esta spec |
|---|---|
| `Assembleia` (status, ordem_trabalhos, eligible_voters_count, chamada_actual, quorum_required) | `modo`, `meeting_link`, `session_phase`, `current_item_id`, `check_in_code`, `session_version` |
| `AssembleiaPresenca` (própria/representação, voting_power) | check-in ao vivo (self/QR/Mesa) escreve nestas |
| `AssembleiaDeliberacao` (maioria absoluta/qualificada) | `voting_mode`, `conflitos_excluidos`, voto separado, votos nominais/secretos |
| `required_quorum`, `is_voting_member`, `is_mesa_ag`, `members_of_orgao` | uso em tempo real |

Specs irmãs: `tasks/spec-voz-participacao-socio.md` (Categoria 1 — a petição 1.3
e as propostas 1.4 alimentam `requerentes`/`ordem_trabalhos` desta sessão).

---

## 2. Decisões transversais (arquitetura)

### 2.1 Módulo e modelo

- Novo módulo **`backend/routes/assembleias.py`** (prefixo `/api`), registado em
  `server.py`. Esqueleto da casa (`routes/polls.py`): `APIRouter`,
  `current_user: User = Depends(get_current_user)`, RBAC explícito,
  `create_audit_log` em toda a escrita.
- Campos novos no documento `assembleias` (aditivos ao modelo da governança):

```python
modo: Literal["presencial", "online", "hibrido"] = "online"   # ressalva: online é o default
meeting_link: Optional[str] = None
meeting_provider: Optional[str] = None      # "meet" | "zoom" | "teams" | "outro"
meeting_notes: Optional[str] = None         # instruções/dial-in
session_phase: Literal["fechada", "checkin", "antes_ot", "ordem_trabalhos", "encerramento"] = "fechada"
current_item_id: Optional[str] = None        # ponto da ordem de trabalhos em curso
check_in_code: Optional[str] = None          # código curto rotativo p/ self check-in
check_in_code_expires_at: Optional[str] = None
session_version: int = 0                      # bump a cada mutação → base do SSE
antes_ot_aberto_em: Optional[str] = None      # p/ limite de 30 min (Art. 14)
```

`session_phase` é o estado **fino** enquanto a governança `status == "em_curso"`.
Transições só pela Mesa: `fechada → checkin → antes_ot → ordem_trabalhos →
encerramento`.

### 2.2 Tempo real — SSE por-assembleia

O SSE actual (`GET /api/notifications/stream`) é **polling por-utilizador** (a
cada 5 s conta unread, emite quando muda; auth por cookie/Bearer/`?token=`; FE
`EventSource(withCredentials)` + fallback de 30 s via TanStack). **Reutilizar o
padrão**, agora por-assembleia:

- `GET /api/assembleias/{id}/stream`: o gerador faz poll de um **snapshot** da
  sessão a cada ~3 s e emite quando `session_version` muda:

```json
{"version": 42, "phase": "ordem_trabalhos", "chamada": 2,
 "quorum": {"required": 34, "present_power": 51, "met": true},
 "speaking": {"current": {"name": "...", "tipo": "intervencao", "ends_at": "..."}, "queue_len": 3},
 "open_vote": {"deliberacao_id": "...", "mode": "nominal", "favor": 12, "contra": 3, "abst": 1},
 "current_item_id": "ot-3"}
```

- **`session_version` faz bump** em toda a mutação (check-in, fila, fase, abrir/
  fechar voto). Sem pub/sub nem `asyncio.Queue` — coerente com a simplicidade do
  código actual; adequado a ~50–150 presentes. (Escala maior: rever com Redis
  pub/sub — fora de scope, decisão em aberto.)
- Auth e fallback de 30 s iguais ao stream de notificações.

### 2.3 RBAC e elegibilidade

- **Mesa da AG** conduz a sessão (`is_mesa_ag(user)` ou `admin`): abrir/fechar
  fases, ordenar a palavra, abrir/apurar votos, registar contagem de braço no ar,
  gerir documentos/convidados.
- **Participar** (pedir palavra, submeter moção, votar) exige `is_voting_member`
  **e** presença registada (`checked_in`) na sessão.
- Helpers vêm da governança/Categoria 1 (`is_mesa_ag`, `is_voting_member`,
  `required_quorum`, `members_of_orgao`); fallback para admins se ainda não
  povoados.

### 2.4 Convenções

`created_at` ISO-8601, `source_article` por documento, auditoria com `action`
snake_case (ex.: `assembleia_checkin`), notificações via helpers existentes
(reusar tipo `"event"` para avisos de sessão; `"poll"` para votos abertos).

---

## 3. Feature 2.1 — Check-in por QR + quórum automático (Art. 5, 21)

**Resumo**: cada sócio faz check-in (pelo QR que já tem ou por self check-in
online); o sistema confere a qualidade de membro e conta presenças/
representações em tempo real, declarando o quórum de 1ª ou 2ª convocatória.

### 3.1 Modelo de dados

A presença canónica é `AssembleiaPresenca` (governança §11). Campos relevantes
ao check-in ao vivo:

```python
class AssembleiaPresenca(BaseModel):   # estende a da governança
    id: str
    assembleia_id: str
    user_id: str
    tipo: Literal["propria", "representacao"] = "propria"
    represented_ids: list[str] = []         # até 3 (Mesa não representa)
    voting_power: int = 1                    # 1 + nº de representados
    is_member: bool = True
    can_vote: bool                           # is_voting_member no momento
    method: Literal["self_code", "qr_scan", "mesa_manual"]
    checked_in_at: str
    source_article: str = "21"
```

Índices: unique `(assembleia_id, user_id)`; `assembleia_id`.

### 3.2 Caminhos de check-in

- **Self check-in (online, primário)** — `POST /assembleias/{id}/checkin` com
  `{code}`. Valida: sessão em `checkin`/`em_curso`, `code == check_in_code`
  (não expirado), utilizador autenticado é `is_voting_member` (ou membro
  presente sem voto, p. ex. honorário/suspenso → `can_vote=false`). O código é
  **partilhado pela Mesa na videochamada** (anti-proxy básico).
- **QR scan (presencial)** — `POST /assembleias/{id}/checkin/scan` com `{qr_hash}`
  (a Mesa lê o QR da carteira do sócio). Reusa o lookup de
  `GET /stats/validate/{qr_hash}` (resolve `qr_code_hash → user`). Regista
  presença em nome desse user.
- **Representação** — `POST /assembleias/{id}/checkin` com
  `{code, represented_member_ids: [...]}` (máx. 3; cada representado tem de ser
  votante e não estar já presente; o representante não pode ser da Mesa). Define
  `voting_power = 1 + len(represented)`; cria/atualiza presenças de representação.

### 3.3 Quórum automático

Contagem em tempo real de `present_power = Σ voting_power` (presenças que votam)
vs. `eligible_voters_count`:

- 1ª convocatória: `required = floor(n/2) + 1` (maioria).
- 30 min depois (ou por decisão da Mesa), 2ª convocatória:
  `required = ceil(n/3)`.

Usa `required_quorum(n, chamada)` (governança). `GET /assembleias/{id}/quorum`
devolve `{chamada, required, present_power, met}`; o `session_version` faz bump a
cada check-in para o SSE propagar.

### 3.4 Endpoints

`POST /assembleias/{id}/checkin` (self/representação), `POST .../checkin/scan`
(Mesa), `GET .../quorum`, `GET .../presencas` (Mesa),
`POST .../checkin/abrir`/`fechar` (Mesa abre/fecha janela e roda `check_in_code`),
`POST .../segunda-convocatoria` (Mesa declara 2ª chamada).

### 3.5 RBAC, notificações, auditoria

- Self check-in: membro autenticado. Scan/abrir/fechar/2ª chamada: Mesa/admin.
- Audit: `assembleia_checkin`, `assembleia_checkin_scan`,
  `assembleia_segunda_convocatoria`. Notif.: aviso aos membros quando o check-in
  abre (`"event"`).

### 3.6 Frontend

Sala de sessão (`/assembleias/{id}`): widget de **quórum ao vivo** (barra
present_power/required + chamada), botão "Entrar na reunião" (`meeting_link`),
modal de **self check-in** (introduz código), e modo **Mesa-scan** (câmara/colar
`qr_hash`, reusa `ValidadorPage`/`QRCode`).

### 3.7 Critérios de aceitação

Self check-in só com código válido e sessão aberta; QR scan resolve o sócio certo;
representação respeita o limite de 3 e Mesa-não-representa; quórum recalcula em
tempo real e distingue 1ª/2ª convocatória; presença duplicada bloqueada (índice).

---

## 4. Feature 2.2 — Fila de uso da palavra com cronómetros (Art. 21/27/28/29)

**Resumo**: inscrição digital para falar, ordenada pela Mesa, com temporizadores
por tipo de intervenção.

### 4.1 Modelo de dados — colecção `assembleia_palavra`

```python
class PalavraRequest(BaseModel):
    id: str
    assembleia_id: str
    item_id: Optional[str] = None
    user_id: str
    tipo: Literal["intervencao", "protesto", "esclarecimento", "defesa_honra"]
    status: Literal["inscrito", "a_falar", "concluido", "retirado", "negado"] = "inscrito"
    ordem: Optional[int] = None             # posição atribuída pela Mesa
    duration_limit_s: int                    # default por tipo
    requested_at: str
    started_at: Optional[str] = None
    ends_at: Optional[str] = None            # started_at + duration_limit_s
    ended_at: Optional[str] = None
    source_article: str = "27"
```

Durações default por tipo (configuráveis; confirmar com o Regimento), em
constantes: `PALAVRA_DURACOES = {"intervencao": 180, "protesto": 60,
"esclarecimento": 120, "defesa_honra": 120}` (segundos). Regras de prioridade do
Regimento (protesto/esclarecimento podem ter precedência) refletidas na ordenação
sugerida.

### 4.2 Endpoints

`POST /assembleias/{id}/palavra` (membro presente — pede a palavra),
`DELETE .../palavra/{qid}` (retira), `POST .../palavra/{qid}/ordenar` (Mesa
reordena), `POST .../palavra/{qid}/iniciar` (Mesa concede — arranca cronómetro,
`status=a_falar`, `ends_at`), `POST .../palavra/{qid}/terminar` (Mesa encerra),
`GET .../palavra` (lista).

### 4.3 RBAC, real-time, frontend

- Pedir/retirar: membro **presente**. Ordenar/iniciar/terminar: Mesa/admin.
- O cronómetro corre no cliente (countdown até `ends_at`) e é registado no
  servidor; a Mesa pode estender. Fila + orador actual + tempo restante via SSE.
- Frontend: lista da fila com tipo (badge), botão "Pedir a palavra" (escolhe
  tipo), e — para a Mesa — reordenar/conceder/terminar + cronómetro grande.

### 4.4 Critérios de aceitação

Só presentes pedem a palavra; a Mesa ordena e concede; o cronómetro usa a duração
do tipo e termina/regista corretamente; a fila atualiza em tempo real.

---

## 5. Feature 2.3 — Moções, requerimentos e recomendações em sessão (Art. 6, 26)

**Resumo**: submissão durante a reunião; **requerimentos vão a voto imediato sem
discussão**, conforme o Regimento.

### 5.1 Modelo de dados — colecção `assembleia_mocoes`

```python
class MocaoSessao(BaseModel):
    id: str
    assembleia_id: str
    item_id: Optional[str] = None
    tipo: Literal["mocao", "requerimento", "recomendacao"]
    titulo: str
    texto: str
    proposta_por: str
    status: Literal["submetida", "em_discussao", "em_votacao", "aprovada", "rejeitada", "retirada"] = "submetida"
    votacao_imediata: bool = False           # True p/ requerimento (Art. 6, 26)
    deliberacao_id: Optional[str] = None      # criada ao colocar a voto
    created_at: str
    source_article: str = "26"
```

### 5.2 Regra do requerimento

`tipo == "requerimento"` ⇒ `votacao_imediata = True`: ao ser aceite pela Mesa,
**salta a discussão** e cria de imediato uma `AssembleiaDeliberacao`
(`status=em_votacao`). Moções/recomendações podem entrar em discussão (fila de
palavra) e só depois ir a voto.

### 5.3 Endpoints, RBAC, frontend

- `POST /assembleias/{id}/mocoes` (membro presente), `POST .../mocoes/{mid}/
  colocar-a-voto` (Mesa → cria deliberação 2.5), `POST .../mocoes/{mid}/retirar`,
  `GET .../mocoes`.
- Submeter: membro presente. Colocar a voto/retirar: Mesa/admin.
- Frontend: formulário "Submeter moção/requerimento/recomendação"; lista com
  estado; a Mesa coloca a voto (requerimento aparece já pronto a votar).
- Audit: `mocao_submetida`, `mocao_a_voto`, `mocao_retirada`.

### 5.4 Critérios de aceitação

Requerimento gera deliberação imediata sem fase de discussão; moção/recomendação
seguem discussão→voto; só a Mesa coloca a voto.

---

## 6. Feature 2.4 — Período "antes da ordem de trabalhos" (Art. 14)

**Resumo**: espaço inicial (**máx. 30 min**) para correspondência e votos de
louvor/congratulação/pesar.

### 6.1 Modelo de dados — colecção `assembleia_expediente`

```python
class ExpedienteEntry(BaseModel):
    id: str
    assembleia_id: str
    tipo: Literal["correspondencia", "voto_louvor", "voto_congratulacao", "voto_pesar"]
    texto: str
    registado_por: str
    aprovado_por_aclamacao: Optional[bool] = None   # votos de louvor etc.
    created_at: str
    source_article: str = "14"
```

### 6.2 Fase e limite de 30 min

A Mesa entra na fase `antes_ot` (regista `antes_ot_aberto_em`). O cliente mostra
um cronómetro de 30 min (**limite soft**: aviso visual ao expirar; a Mesa
encerra/estende com nota — recomendado, em vez de auto-fechar). Transição
`antes_ot → ordem_trabalhos` pela Mesa.

### 6.3 Endpoints, RBAC, frontend

- `POST /assembleias/{id}/fase` (Mesa — transita fases),
  `POST .../expediente` (regista correspondência/votos), `GET .../expediente`.
- Registar/transitar: Mesa/admin (votos de louvor podem ser propostos por
  membros — opcional).
- Frontend: painel "Antes da Ordem de Trabalhos" com cronómetro de 30 min e
  lista de expediente; botão da Mesa "Iniciar Ordem de Trabalhos".
- Audit: `expediente_registado`, `assembleia_fase`.

### 6.4 Critérios de aceitação

Fase `antes_ot` com cronómetro de 30 min visível; expediente registado e listado;
transição para a ordem de trabalhos só pela Mesa.

---

## 7. Feature 2.5 — Modos de votação + conflito de interesses (Art. 32)

**Resumo**: suporte a voto de **braço no ar**, **nominal** ou **secreto**;
**exclusão automática** de quem tem conflito de interesses e **voto separado**
quando o ponto tem vários assuntos.

### 7.1 Modelo de dados — estende `AssembleiaDeliberacao` (governança)

```python
class AssembleiaDeliberacao(BaseModel):   # campos adicionados por esta spec
    # ... ponto, tipo_maioria, base, votos favor/contra/abstencao, aprovado (governança)
    voting_mode: Literal["braco_no_ar", "nominal", "secreto"] = "braco_no_ar"
    item_id: Optional[str] = None
    subitem: Optional[str] = None             # voto separado: vários assuntos no mesmo ponto
    conflitos_excluidos: list[str] = []       # user_ids sem direito a voto neste ponto
    status: Literal["aberta", "encerrada", "anulada"] = "aberta"
    source_article: str = "32"
```

- **`braco_no_ar`**: a Mesa **regista a contagem agregada** (favor/contra/
  abstenção) — adequado a reunião online (a Mesa conta as mãos na chamada). Sem
  registos por-votante.
- **`nominal`**: cada votante presente vota e o voto fica **registado por nome**
  (colecção `assembleia_votos`: `{deliberacao_id, user_id, escolha}`, único
  `(deliberacao_id, user_id)`).
- **`secreto`**: urna anónima — reutiliza o desenho de **voto secreto** das
  eleições da governança (par recibo/boletim: `assembleia_voto_receipts` prova
  que votou; `assembleia_voto_ballots` guarda a escolha sem `user_id`). Em sessão
  online, tratar como **apoio administrativo** salvo o Regimento autorizar urna
  digital vinculativa.
- **Conflito de interesses**: `conflitos_excluidos` são bloqueados de votar e
  **retirados da base** de cálculo da maioria (Art. 32). Declarados pela Mesa ou
  auto-declarados antes da abertura.
- **Voto separado**: um ponto da ordem de trabalhos pode ter **N deliberações**
  (`item_id` + `subitem`), votadas em separado.

### 7.2 Apuramento

Maioria via helpers da governança (`absoluta`/`qualificada`). Base =
`present_power − Σ(voting_power dos conflitos_excluidos)`; abstenções tratadas
conforme `tipo_maioria`. `aprovado` calculado no apuramento.

### 7.3 Endpoints, RBAC, real-time, frontend

- `POST /assembleias/{id}/deliberacoes` (Mesa abre: `voting_mode`, `tipo_maioria`,
  `item_id/subitem`, `conflitos_excluidos`).
- `POST .../deliberacoes/{did}/votar` (votante; nominal/secreto) — bloqueia
  excluídos e não-presentes.
- `POST .../deliberacoes/{did}/registar-contagem` (Mesa; braço no ar — agregados).
- `POST .../deliberacoes/{did}/apurar` (Mesa — fecha e calcula).
- `GET .../deliberacoes/{did}`.
- Abrir/contagem/apurar: Mesa/admin. Votar: votante presente não-excluído.
- Voto aberto propagado por SSE; tally ao vivo em modo nominal; **nunca** expor
  ligação eleitor↔boletim em modo secreto.
- Frontend: a Mesa escolhe o modo ao abrir; o membro vê o cartão de voto
  (Favor/Contra/Abstenção) em nominal/secreto; em braço no ar a Mesa introduz a
  contagem; resultado e maioria mostrados ao apurar.

### 7.4 Critérios de aceitação

Os 3 modos funcionam; excluídos por conflito não votam e saem da base; voto
separado permite várias deliberações por ponto; secreto não liga eleitor a voto;
braço no ar guarda só agregados.

---

## 8. Feature 2.6 — Documentos da sessão (≥3 dias) + convidados (Art. 20, 36)

**Resumo**: anexar documentos a discutir com **pelo menos 3 dias** de
antecedência e gerir **não-membros** autorizados a assistir/intervir.

### 8.1 Documentos da sessão

Reusa o módulo de documentos (modelo `Document`: title/file_url/type/visibility/
tags; upload `/upload/documents` 10 MB, admin/`manage_documents`). Ligação à
assembleia por lista `documentos: list[str]` (document_ids) no doc da assembleia
(sem colecção nova).

- `POST /assembleias/{id}/documentos` (Mesa/`manage_documents`) — anexa um
  `document_id`. **Validação Art. 20**: se `now > data − 3 dias`, devolver aviso
  (ou bloquear, configurável `MIN_DOC_ANTECEDENCIA_DIAS=3`) e registar
  `documento_anexado_tardio` na auditoria.
- `GET /assembleias/{id}/documentos` — lista (visibilidade `socios` por omissão).

### 8.2 Convidados — colecção `assembleia_convidados`

```python
class Convidado(BaseModel):
    id: str
    assembleia_id: str
    nome: str
    email: Optional[str] = None
    can_speak: bool = False        # autorizado a intervir (não só assistir)
    motivo: Optional[str] = None
    invited_by: str
    checked_in: bool = False
    created_at: str
    source_article: str = "36"
```

Convidados **não contam** para quórum nem votam. Se `can_speak`, a Mesa pode
adicioná-los à fila de palavra (2.2). Para online, o `meeting_link` pode ser
partilhado por email ao convidado (fora do scope o envio automático; é stop
condition se for email a utilizadores reais).

- `POST /assembleias/{id}/convidados` (Mesa), `GET .../convidados`,
  `POST .../convidados/{cid}/checkin` (Mesa marca presença do convidado).

### 8.3 Critérios de aceitação

Anexar documento <3 dias antes avisa/bloqueia e fica auditado; documentos da
sessão respeitam visibilidade; convidados não entram no quórum/voto; convidado
`can_speak` pode ser posto na fila pela Mesa.

---

## 9. Colecções e índices

Acrescentar ao tuplo `COLLECTIONS` (`database.py`) e DDL a `_INDEX_DDL`. As
colecções `assembleias`, `assembleia_presencas`, `assembleia_deliberacoes` vêm da
**governança** (não duplicar). Net-new desta spec:

| Colecção | Índices mínimos |
|---|---|
| `assembleia_palavra` | `assembleia_id`; `(assembleia_id, status)` |
| `assembleia_mocoes` | `assembleia_id`; `(assembleia_id, status)` |
| `assembleia_expediente` | `assembleia_id` |
| `assembleia_convidados` | `assembleia_id` |
| `assembleia_votos` (nominal) | unique `(deliberacao_id, user_id)`; `deliberacao_id` |
| `assembleia_voto_receipts` (secreto) | unique `(deliberacao_id, voter_hash)` |
| `assembleia_voto_ballots` (secreto) | `deliberacao_id` (sem `user_id`) |

Voto secreto: inserir recibo + boletim numa transacção; `voter_hash =
HMAC(secret, f"{deliberacao_id}:{user_id}")` (igual ao desenho das eleições).
Documentos da sessão: lista no doc da assembleia (sem colecção).

---

## 10. Tempo real (detalhe)

- `GET /api/assembleias/{id}/stream` (SSE) — mesmo padrão do
  `notifications/stream`: loop com `request.is_disconnected()`, `asyncio.sleep(3)`,
  emite o snapshot (§2.2) quando `session_version` muda. Auth cookie/Bearer/
  `?token=`.
- **`session_version += 1`** num helper único chamado por toda a mutação de
  sessão (check-in, fila, fase, abrir/registar/apurar voto, expediente).
- Frontend: hook `useAssembleiaStream(id)` espelha `NotificationContext` —
  `EventSource(withCredentials)`, `onmessage` actualiza cache TanStack, `onerror`
  → polling de 30 s, pausa quando o separador está oculto.
- **Limite**: polling por presente; ~50–150 ok. Escala maior → pub/sub (aberto).

---

## 11. Frontend — sala de sessão

- Páginas: `/assembleias` (lista) e **`/assembleias/{id}`** (sala ao vivo). Em
  `pages/private/`. Rotas com `<ProtectedRoute>`; item de sidebar "Assembleias"
  (secção Governança/Participação).
- A sala tem **duas vistas na mesma página**, conforme o utilizador:
  - **Consola da Mesa** (`is_mesa_ag`/admin): abrir/fechar fases, código de
    check-in + scan, ordenar/conceder palavra, abrir/apurar votos e registar
    braço no ar, gerir moções/expediente/documentos/convidados.
  - **Participante** (membro presente): "Entrar na reunião" (`meeting_link`),
    self check-in, pedir a palavra, votar, submeter moção, ver quórum/fila/voto
    ao vivo.
- Reutilizar: `QRCode` (carteira) e o lookup do validador para o scan; upload de
  documentos; TanStack Query + SSE. Design neutral-led + Carmesim, sem dark mode
  (skill `frontend-design`); cronómetros e barra de quórum com estados claros.
- `utils/api.js`: grupo `assembleiasAPI` (sessão, checkin, quorum, palavra,
  mocoes, deliberacoes, expediente, documentos, convidados).

---

## 12. Plano de execução faseado

Pré-requisito: núcleo `Assembleia` da governança (§11). Depois, PRs pequenos por
funcionalidade, `feature/* → develop`.

| Fase | Entrega | Depende |
|---|---|---|
| F0 | Campos de sessão (`modo`, `meeting_link`, `session_phase`, `check_in_code`, `session_version`) + SSE por-assembleia + `routes/assembleias.py` | governança §11 |
| F1 | **2.1** Check-in (self/QR/representação) + quórum ao vivo | F0 |
| F2 | **2.2** Fila de palavra + cronómetros | F0, F1 |
| F3 | **2.5** Modos de voto + conflito + voto separado | F0, F1 |
| F4 | **2.3** Moções/requerimentos (+ voto imediato) | F3 |
| F5 | **2.4** Antes da ordem de trabalhos (fases + expediente) | F1 |
| F6 | **2.6** Documentos ≥3 dias + convidados | F0 |
| F7 | Sala de sessão (frontend) — incremental por fase | todas |

### Ordem dentro de cada fase

Models/campos → schema/índices (`ensure_schema`) → endpoints + RBAC + audit +
bump de `session_version` → testes backend → frontend → testes frontend →
**ensaio manual** de uma sessão online (check-in, quórum, palavra, voto) num
ambiente de dev com um link de reunião de teste.

---

## 13. Testes obrigatórios

Colecções novas **não** estão pré-cabladas no `mock_db` — cablar em-teste.

- 2.1: self check-in só com código válido + sessão aberta; scan resolve o user
  por `qr_hash`; representação ≤3 e Mesa-não-representa; quórum 1ª (`floor/2+1`)
  vs 2ª (`ceil/3`); presença duplicada bloqueada.
- 2.2: pedir palavra só presente; concessão arranca `ends_at` correcto; ordenação
  só pela Mesa.
- 2.3: requerimento ⇒ deliberação imediata (sem discussão); moção segue
  discussão→voto.
- 2.4: fase `antes_ot` regista abertura; transição só pela Mesa; expediente
  listado.
- 2.5: 3 modos; excluído por conflito não vota e sai da base; voto separado cria
  ≥2 deliberações; boletim secreto sem `user_id`; braço no ar guarda só agregados.
- 2.6: anexo <3 dias avisa/bloqueia e audita; convidado fora do quórum/voto.
- SSE: snapshot muda só quando `session_version` muda; auth por token.

Frontend: render da sala (consola Mesa vs participante), countdown da palavra,
barra de quórum, cartão de voto por modo, gating por `is_mesa_ag`.

---

## 14. Stop conditions (CLAUDE.md)

Confirmar com o utilizador antes de:

- Tratar voto **secreto/nominal online** como **juridicamente vinculativo** sem
  validação do Regimento (default: apoio administrativo).
- Enviar emails reais (ex.: `meeting_link` a convidados).
- Migrar/limpar dados; alterar Pydantic de forma incompatível (tudo aqui é
  aditivo).
- Remover rotas que o frontend chama.

---

## 15. Decisões em aberto

1. **Check-in online anti-proxy**: código de sessão partilhado na chamada
   (recomendado) é suficiente, ou exigir ligação mais forte (confirmação por
   par, presença na chamada)?
2. **`meeting_link`**: só armazenar/abrir (recomendado) ou tentar embeber? (A
   maioria dos fornecedores bloqueia iframe.)
3. **Durações da palavra** por tipo: confirmar valores com o Regimento.
4. **Limite dos 30 min** (Art. 14): soft com aviso (recomendado) ou auto-fecho?
5. **Braço no ar online**: contagem manual da Mesa (recomendado) — confirmar que
   não se espera contagem automática de mãos na videochamada.
6. **Voto secreto online**: vinculativo (urna digital) vs. apoio administrativo
   (default, alinhado com a governança "voto digital com cautela").
7. **Escala de tempo real**: manter polling SSE (recomendado p/ <150) ou
   introduzir pub/sub (Redis) desde já?
8. **Localização do módulo**: `routes/assembleias.py` autónomo (recomendado) ou
   dentro de um futuro `routes/governanca.py`?
9. **Representação online**: como comprovar a procuração (upload de documento vs.
   registo manual da Mesa)?
