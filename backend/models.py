from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator
from typing import List, Literal, Optional
from datetime import datetime, timezone, date
import uuid

# Governança estatutária (spec-governanca-estatutaria): a fonte ÚNICA de
# cargos/órgãos/categorias/privilégios é `governance.py`. models.py apenas
# re-exporta estas constantes para preservar imports e testes existentes
# (re-export intencional → noqa F401).
from governance import (  # noqa: F401
    CARGOS,
    CARGO_KEYS,
    CARGOS_ORGAOS_SOCIAIS,
    CARGO_DEFAULTS,
    CARGO_SEATS,
    PRIVILEGES,
    ROLES,
    MEMBER_CATEGORIES,
    MEMBER_CATEGORY_LABELS,
    VOTING_CATEGORIES,
    DEFAULT_MEMBER_CATEGORY,
    MANDATO_ANOS,
    normalize_cargo,
    cargo_label,
    orgao_of_cargo,
    is_estatutary_cargo,
)


# ===== USER MODELS =====
# Modelo de identidade e cargos (spec-identidade-cargos):
# - account_type separa pessoas reais ("member") de contas de sistema ("technical").
# - role = nível de acesso "grosso" (admin/financeiro/moderador/socio).
# - cargo = função institucional eleita; privileges = overlays granulares.
# - member_id = identificador permanente e imutável do sócio real.

ACCOUNT_TYPES = ["member", "technical"]

# Nome legado mantido para compat de imports (admin.py/users.py importam isto).
ROLES_VALID = ROLES


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "socio"
    status: str = "ativo"
    member_id: Optional[str] = None
    license_number: Optional[str] = None
    admission_date: Optional[datetime] = None
    phone_number: Optional[str] = None
    consent_data: bool = False
    account_type: Literal["member", "technical"] = "member"
    # Categoria estatutária de membro (spec-governanca §3.3): fundador / ordinario
    # / honorario. Define o voto base; sanções suspendem direitos sem alterar.
    member_category: str = "ordinario"
    # Órgão social derivado do cargo e denormalizado para filtros/relatórios.
    orgao: Optional[str] = None
    cargo: str = "socio"  # key canónica (governance.py); nunca o label.
    privileges: List[str] = []
    cargo_history: List[dict] = []
    # Perda de direitos disciplinar (spec §13): afecta voto/elegibilidade sem
    # tornar a conta inactiva. ISO-8601 string.
    rights_suspended_until: Optional[str] = None
    rights_suspension_reason: Optional[str] = None
    # Necessário para validar representação em AG (regra do Sal — spec §11).
    residence_island: Optional[str] = None
    bio: Optional[str] = None
    department: Optional[str] = None
    photo_url: Optional[str] = None
    # ===== Perfil pessoal estendido (feature/perfil) =====
    # Campos opcionais geridos pelo próprio sócio (PATCH /users/me/profile) ou
    # por admin. Datas como string ISO "AAAA-MM-DD" (regra do projeto: nunca
    # datetime nos modelos). UserBase fica LENIENTE (sem validação) para nunca
    # falhar a serialização de documentos legados; a validação vive nos modelos
    # de escrita (_EditableProfileFields).
    date_of_birth: Optional[str] = None  # aniversário (AAAA-MM-DD)
    blood_type: Optional[str] = None  # tipo sanguíneo (A+, O-, …)
    gender: Optional[str] = None
    nationality: Optional[str] = None
    nif: Optional[str] = None  # número de identificação fiscal
    address: Optional[str] = None  # morada (rua/linha)
    postal_code: Optional[str] = None  # código postal
    city: Optional[str] = None  # cidade / concelho
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None  # parentesco
    profession: Optional[str] = None
    employer: Optional[str] = None  # entidade empregadora
    license_category: Optional[str] = None  # título/categoria profissional
    # Validade da licença profissional (AAAA-MM-DD). Usada no frontend para
    # avisar o sócio antes do prazo e ajudá-lo a renovar sem multa.
    license_expiry_date: Optional[str] = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    qr_code_hash: Optional[str] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Tipos sanguíneos aceites (sistema ABO/Rh). Usado na validação de escrita.
BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


def _validate_blood_type(v: Optional[str]) -> Optional[str]:
    # None/"" passam (None = não alterar; "" = limpar — o route filtra só None).
    if v is None or v == "":
        return v
    norm = v.strip().upper()
    if norm not in BLOOD_TYPES:
        raise ValueError(f"Tipo sanguíneo inválido. Opções: {', '.join(BLOOD_TYPES)}")
    return norm


def _validate_date_str(v: Optional[str], *, allow_future: bool = True, label: str = "Data") -> Optional[str]:
    """Valida string de data ISO; devolve sempre 'AAAA-MM-DD' normalizado."""
    if v is None or v == "":
        return v
    try:
        parsed = date.fromisoformat(v.strip()[:10])
    except (ValueError, TypeError):
        raise ValueError(f"{label} deve estar no formato AAAA-MM-DD")
    if not allow_future and parsed > date.today():
        raise ValueError(f"{label} não pode estar no futuro")
    return parsed.isoformat()


def _validate_name(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    if not v.strip():
        raise ValueError("O nome não pode ficar vazio")
    return v.strip()


class _EditableProfileFields(BaseModel):
    """Campos de perfil editáveis pelo próprio sócio e por admin.

    A validação (formato de datas, tipo sanguíneo, nome não-vazio, limites de
    tamanho) vive aqui — modelos de ESCRITA. `UserBase` permanece leniente na
    leitura. Enviar "" limpa o campo; omitir mantém o valor atual (o route só
    filtra valores None de `model_dump()`).
    """

    name: Optional[str] = Field(default=None, max_length=120)
    phone_number: Optional[str] = Field(default=None, max_length=30)
    bio: Optional[str] = Field(default=None, max_length=1000)
    photo_url: Optional[str] = Field(default=None, max_length=500)
    # Dados pessoais
    date_of_birth: Optional[str] = None  # AAAA-MM-DD
    blood_type: Optional[str] = None
    gender: Optional[str] = Field(default=None, max_length=40)
    nationality: Optional[str] = Field(default=None, max_length=60)
    nif: Optional[str] = Field(default=None, max_length=40)
    # Morada
    address: Optional[str] = Field(default=None, max_length=200)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    city: Optional[str] = Field(default=None, max_length=80)
    residence_island: Optional[str] = Field(default=None, max_length=60)
    # Contacto de emergência
    emergency_contact_name: Optional[str] = Field(default=None, max_length=120)
    emergency_contact_phone: Optional[str] = Field(default=None, max_length=30)
    emergency_contact_relationship: Optional[str] = Field(default=None, max_length=60)
    # Profissional / licença
    profession: Optional[str] = Field(default=None, max_length=120)
    employer: Optional[str] = Field(default=None, max_length=120)
    license_number: Optional[str] = Field(default=None, max_length=60)
    license_category: Optional[str] = Field(default=None, max_length=80)
    license_expiry_date: Optional[str] = None  # AAAA-MM-DD

    @field_validator("name")
    @classmethod
    def _v_name(cls, v):
        return _validate_name(v)

    @field_validator("blood_type")
    @classmethod
    def _v_blood(cls, v):
        return _validate_blood_type(v)

    @field_validator("date_of_birth")
    @classmethod
    def _v_dob(cls, v):
        return _validate_date_str(v, allow_future=False, label="Data de nascimento")

    @field_validator("license_expiry_date")
    @classmethod
    def _v_license_expiry(cls, v):
        return _validate_date_str(v, label="Validade da licença")


class UserProfileUpdate(_EditableProfileFields):
    """Auto-serviço (PATCH /users/me/profile): o sócio gere os seus próprios
    dados pessoais, de contacto, de emergência e profissionais/licença.
    NÃO inclui campos de acesso (role/status/privileges) nem identidade
    (email/member_id/cargo)."""

    pass


class UserAdminUpdate(_EditableProfileFields):
    # NOTA: member_id e cargo NÃO são editáveis aqui (spec-identidade-cargos).
    # - member_id é imutável depois de atribuído (alterações só via script de
    #   migração, fora da API comum).
    # - cargo institucional é atribuído EXCLUSIVAMENTE via /admin/cargos
    #   (promote/demote/transfer), que regista o mandato em cargo_history e
    #   valida as vagas (CARGO_SEATS). Editá-lo aqui contornaria esse histórico.
    # Além dos campos pessoais herdados, o admin pode editar acesso/identidade:
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    status: Optional[str] = None
    privileges: Optional[List[str]] = None
    department: Optional[str] = Field(default=None, max_length=80)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: User


class InviteCreate(BaseModel):
    name: str
    email: EmailStr
    role: str = "socio"
    cargo: Optional[str] = None
    member_id: Optional[str] = None
    license_number: Optional[str] = None
    department: Optional[str] = None
    phone_number: Optional[str] = None


class SetupAccount(BaseModel):
    token: str
    password: str = Field(min_length=6, max_length=72)


# ===== AUTO-REGISTO MODELS (spec-auto-registo) =====

# Cargos que o candidato pode DECLARAR no formulário público. É apenas um
# label informativo para o admin — NÃO promove o role (que é sempre "socio"
# no submit; o admin decide o role final ao aprovar).
CARGOS_DECLARADOS = [
    "Sócio",
    "Vogal",
    "Tesoureiro",
    "Secretário",
    "Vice-Presidente",
    "Presidente",
    "Direcção",
    "Conselho Fiscal",
]


class RegistrationRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = Field(default=None, max_length=30)
    department: Optional[str] = Field(default=None, max_length=80)
    cargo_declarado: str = Field(default="Sócio")  # validado contra CARGOS_DECLARADOS na rota
    consent_data: bool  # tem de ser True (RGPD)
    website: Optional[str] = Field(default=None, max_length=200)  # HONEYPOT — preenchido => descartar
    # Patrocínio de admissão (spec-voz-participacao §3, Art. 8.3): 2 padrinhos
    # (member_id ACCTA-XXXX ou email). Opcional aqui; exigência validada na rota
    # para o auto-registo.
    sponsors: Optional[List[str]] = Field(default=None, max_length=2)


class RegistrationApprove(BaseModel):
    role: str = "socio"  # validado contra ["socio","financeiro","moderador","admin"] na rota
    cargo: Optional[str] = None  # se None, mantém o cargo_declarado
    waive_sponsorship: bool = False  # dispensa Art. 8.3 (bootstrap/excepção, auditável)


# ===== PARTICIPAÇÃO DO SÓCIO (spec-voz-participacao-socio) =====


class Patrocinio(BaseModel):
    # Uma linha por par candidato↔padrinho (espelha user_votes; facilita o
    # "inbox do padrinho"). Art. 8.3.
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    candidate_id: str
    sponsor_user_id: str
    sponsor_member_id: Optional[str] = None  # ACCTA-XXXX (snapshot p/ display)
    status: Literal["pendente", "confirmado", "recusado"] = "pendente"
    responded_at: Optional[str] = None
    note: Optional[str] = Field(default=None, max_length=500)
    created_at: Optional[str] = None
    source_article: str = "8.3"


class PatrocinioRespond(BaseModel):
    note: Optional[str] = Field(default=None, max_length=500)


# 1.3 — Petição para AG extraordinária (Art. 9.f, 19.2.d)


class Peticao(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    titulo: str = Field(min_length=3, max_length=180)
    fundamentacao: str = Field(min_length=1, max_length=5000)
    tipo: str = "ag_extraordinaria"
    threshold_fraction: float = 0.25  # 1/4 dos membros votantes
    target_count: Optional[int] = None  # snapshot do alvo no momento de atingir
    status: Literal["aberta", "atingida", "encaminhada", "encerrada", "expirada"] = "aberta"
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    expires_at: Optional[str] = None
    met_at: Optional[str] = None
    assembleia_id: Optional[str] = None
    source_article: str = "9.f"


class PeticaoCreate(BaseModel):
    titulo: str = Field(min_length=3, max_length=180)
    fundamentacao: str = Field(min_length=1, max_length=5000)


class PeticaoEncaminhar(BaseModel):
    assembleia_id: Optional[str] = None


# 1.6 — Pedidos de esclarecimento (Art. 9.j)


class Esclarecimento(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    orgao_destino: Literal["direcao", "mesa_ag", "conselho_fiscal"]
    assunto: str = Field(min_length=3, max_length=180)
    pergunta: str = Field(min_length=1, max_length=4000)
    status: Literal["submetido", "respondido", "encerrado"] = "submetido"
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    prazo_resposta: Optional[str] = None
    resposta: Optional[dict] = None  # {by, at, text}
    source_article: str = "9.j"


class EsclarecimentoCreate(BaseModel):
    orgao_destino: Literal["direcao", "mesa_ag", "conselho_fiscal"]
    assunto: str = Field(min_length=3, max_length=180)
    pergunta: str = Field(min_length=1, max_length=4000)


class RespostaTexto(BaseModel):
    texto: str = Field(min_length=1, max_length=4000)


# 1.5 — Reclamações e recursos (Art. 9.i) — genérico, NÃO disciplinar


class Reclamacao(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assunto: str = Field(min_length=3, max_length=180)
    descricao: str = Field(min_length=1, max_length=5000)
    status: Literal["submetida", "em_analise", "respondida", "resolvida", "recurso", "encerrada"] = "submetida"
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    prazo_resposta: Optional[str] = None  # SLA +15 dias (decisão do dono)
    direcao_resposta: Optional[dict] = None  # {by, at, text}
    resolvida: Optional[bool] = None
    recurso: Optional[dict] = None  # {opened_at, by, decisao, assembleia_id, deliberacao_id}
    source_article: str = "9.i"


class ReclamacaoCreate(BaseModel):
    assunto: str = Field(min_length=3, max_length=180)
    descricao: str = Field(min_length=1, max_length=5000)


class ReclamacaoResponder(BaseModel):
    texto: str = Field(min_length=1, max_length=4000)
    resolvida: bool = False


class RecursoDecisao(BaseModel):
    decisao: str = Field(min_length=1, max_length=2000)
    assembleia_id: Optional[str] = None
    deliberacao_id: Optional[str] = None


# 1.4 — Propostas e temas para a ordem de trabalhos (Art. 9.g, 9.h)


class PropostaAG(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    titulo: str = Field(min_length=3, max_length=180)
    descricao: str = Field(min_length=1, max_length=5000)
    tipo: Literal["medida", "ponto", "tema"] = "ponto"
    status: Literal["submetida", "em_triagem", "aceite", "recusada", "incluida", "arquivada"] = "submetida"
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    reviewer_id: Optional[str] = None  # quem triou
    reviewed_at: Optional[str] = None
    decisao_motivo: Optional[str] = None
    assembleia_id: Optional[str] = None  # preenchido na inclusão (integração governança)
    ordem_index: Optional[int] = None  # posição na ordem de trabalhos
    source_article: str = "9.g"


class PropostaAGCreate(BaseModel):
    titulo: str = Field(min_length=3, max_length=180)
    descricao: str = Field(min_length=1, max_length=5000)
    tipo: Literal["medida", "ponto", "tema"] = "ponto"


class PropostaTriagem(BaseModel):
    decisao: Literal["aceite", "recusada"]
    decisao_motivo: Optional[str] = Field(default=None, max_length=2000)


class PropostaIncluir(BaseModel):
    assembleia_id: Optional[str] = None
    ordem_index: Optional[int] = None


# 1.2 — Membros honorários (Art. 8.4): Direcção nomeia → AG vota → 2/3 elege.


class HonorarioNomination(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nominee_name: str = Field(min_length=2, max_length=120)
    nominee_user_id: Optional[str] = None  # se elevar membro existente
    nominee_email: Optional[EmailStr] = None  # se pessoa nova → convite se eleito
    justificacao: str = Field(min_length=1, max_length=4000)  # serviços relevantes
    status: Literal["proposta", "em_votacao", "eleito", "rejeitado"] = "proposta"
    proposta_por: Optional[str] = None  # Direcção
    poll_id: Optional[str] = None  # votação 2/3 associada (reusa polls/user_votes)
    # Base do 2/3 (decisão do dono): votos válidos emitidos (favor+contra). Mantém
    # "presentes" no Literal só para forward-compat quando o módulo Assembleia existir.
    base_apuramento: Literal["validos", "presentes"] = "validos"
    votos_favor: Optional[int] = None
    votos_total_base: Optional[int] = None
    assembleia_id: Optional[str] = None
    deliberacao_id: Optional[str] = None
    created_at: Optional[str] = None
    source_article: str = "8.4"


class HonorarioCreate(BaseModel):
    nominee_name: str = Field(min_length=2, max_length=120)
    nominee_user_id: Optional[str] = None
    nominee_email: Optional[EmailStr] = None
    justificacao: str = Field(min_length=1, max_length=4000)


class RegistrationReject(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=500)


# ===== CARGO / MANDATO MODELS (spec-identidade-cargos) =====


# Cada entrada de cargo_history documenta um mandato do sócio. Armazenado como
# dict no doc.cargo_history; este modelo valida/serializa as escritas.
class CargoMandate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cargo: str  # key canónica (governance.py)
    label: Optional[str] = None  # snapshot do label p/ auditoria/display
    role: str
    orgao: Optional[str] = None  # órgão social derivado do cargo
    inicio: str  # ISO 8601, obrigatório
    fim: Optional[str] = None  # ISO 8601; None = mandato activo
    posse_em: Optional[str] = None  # data de posse (eleições)
    mandato_inicio: Optional[str] = None  # início formal do mandato eleitoral
    mandato_fim: Optional[str] = None  # fim formal do mandato eleitoral
    suplente: bool = False
    seat_index: Optional[int] = None
    elected_by: Optional[str] = None  # "AGA 2026", "Direcção", texto livre
    eleicao_id: Optional[str] = None
    assembleia_id: Optional[str] = None
    transitioned_by: str  # id do admin que efectuou a alteração
    transition_id: Optional[str] = None  # liga as 2 pontas de um transfer
    notes: Optional[str] = None


class PromoteUserRequest(BaseModel):
    cargo: str  # tem de estar em CARGOS
    role: str  # tem de estar em ROLES_VALID
    privileges: Optional[List[str]] = None  # se None, usa CARGO_DEFAULTS[cargo]
    elected_by: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=500)
    effective_date: Optional[str] = None  # ISO 8601, default = agora


class DemoteUserRequest(BaseModel):
    effective_date: Optional[str] = None  # ISO 8601, default = agora
    notes: Optional[str] = Field(default=None, max_length=500)


class TransferCargoRequest(BaseModel):
    from_user_id: str
    to_user_id: str
    cargo: str
    role: str
    privileges: Optional[List[str]] = None
    elected_by: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=500)
    effective_date: Optional[str] = None  # ISO 8601, default = agora


# ===== INVOICE MODELS =====


class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str
    amount: float
    due_date: datetime
    status: str = "pendente"
    source: str = "folha_salarial"
    payroll_reference: Optional[str] = None
    confirmed_by_admin: bool = False
    confirmed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InvoiceCreate(BaseModel):
    user_id: str
    type: str
    amount: float
    due_date: datetime
    source: str = "folha_salarial"
    payroll_reference: Optional[str] = None
    notes: Optional[str] = None


# ===== POLL MODELS =====


class Poll(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    options: List[dict]
    start_date: datetime
    end_date: datetime
    status: str = "rascunho"
    result_visibility: str = "socios"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PollCreate(BaseModel):
    title: str
    description: str
    options: List[dict]
    start_date: datetime
    end_date: datetime
    result_visibility: str = "socios"


class UserVote(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    poll_id: str
    vote_option: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VoteCreate(BaseModel):
    poll_id: str
    vote_option: int


class PollStatusUpdate(BaseModel):
    # Transição de ciclo de vida da votação. "rascunho" é o estado inicial
    # (criação); só se transita para "aberta" e depois "encerrada".
    status: Literal["aberta", "encerrada"]


# ===== POST MODELS =====

# Enums do blog/notícias (spec-blog-noticias D8). Strings livres davam lixo nos
# dados; o frontend já assume estes valores fixos.
POST_TYPES = ["noticia", "institucional", "educativo"]
POST_VISIBILITIES = ["publico", "socios", "privado"]
POST_STATUSES = ["rascunho", "publicado"]


class Post(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(min_length=3, max_length=180)
    # slug Optional p/ compat com posts antigos (seed) sem slug; gerado no create.
    slug: Optional[str] = None
    content: str = Field(min_length=1, max_length=20000)
    excerpt: Optional[str] = Field(default=None, max_length=320)
    cover_url: Optional[str] = None  # /uploads/covers/... ou None
    type: Literal["noticia", "institucional", "educativo"] = "noticia"
    visibility: Literal["publico", "socios", "privado"] = "publico"
    status: Literal["rascunho", "publicado"] = "publicado"
    tags: List[str] = Field(default_factory=list, max_length=10)
    author_id: Optional[str] = None
    author_name: Optional[str] = None  # desnormalizado p/ render simples
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[str] = None  # ISO string (regra: datas como str)
    published_at: Optional[str] = None


class PostCreate(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    content: str = Field(min_length=1, max_length=20000)
    excerpt: Optional[str] = Field(default=None, max_length=320)
    cover_url: Optional[str] = None
    type: Literal["noticia", "institucional", "educativo"] = "noticia"
    visibility: Literal["publico", "socios", "privado"] = "publico"
    status: Literal["rascunho", "publicado"] = "publicado"
    tags: List[str] = Field(default_factory=list, max_length=10)
    # D5 — toggle in-app (não email): notifica sócios ao publicar visibility=socios.
    notify_socios: bool = False


class PostUpdate(BaseModel):
    # Todos opcionais (semântica PATCH). Só os campos enviados são aplicados.
    title: Optional[str] = Field(default=None, min_length=3, max_length=180)
    content: Optional[str] = Field(default=None, min_length=1, max_length=20000)
    excerpt: Optional[str] = Field(default=None, max_length=320)
    cover_url: Optional[str] = None
    type: Optional[Literal["noticia", "institucional", "educativo"]] = None
    visibility: Optional[Literal["publico", "socios", "privado"]] = None
    status: Optional[Literal["rascunho", "publicado"]] = None
    tags: Optional[List[str]] = Field(default=None, max_length=10)
    # Flag de comando: só respeitada enquanto rascunho; nunca persistida no doc.
    regenerate_slug: bool = False


# ===== DOCUMENT MODELS =====


class Document(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    file_url: str
    type: str
    visibility: str = "socios"
    tags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DocumentCreate(BaseModel):
    title: str
    file_url: str
    type: str
    visibility: str = "socios"
    tags: List[str] = []


# ===== BENEFIT MODELS =====


class BenefitPartnerLocation(BaseModel):
    """A physical location (parceiro) where a benefit can be redeemed."""

    model_config = ConfigDict(extra="ignore")
    name: str
    address: str = ""
    city: str = ""
    phone: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)


class Benefit(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    logo_url: Optional[str] = None
    discount_percent: float
    category: Optional[str] = None  # e.g. "saude", "restauracao", "viagens"
    website: Optional[str] = None
    locations: List[BenefitPartnerLocation] = []
    active: bool = True
    validation_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BenefitCreate(BaseModel):
    name: str
    description: str
    logo_url: Optional[str] = None
    discount_percent: float
    category: Optional[str] = None
    website: Optional[str] = None
    locations: List[BenefitPartnerLocation] = []


class BenefitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    discount_percent: Optional[float] = None
    category: Optional[str] = None
    website: Optional[str] = None
    locations: Optional[List[BenefitPartnerLocation]] = None
    active: Optional[bool] = None


# ===== WALL MODELS =====


class WallPost(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    content: str
    category: str = "geral"
    approved: bool = False
    pinned: bool = False
    likes: List[str] = []
    comment_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WallPostCreate(BaseModel):
    content: str
    category: str = "geral"


class WallComment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    post_id: str
    user_id: str
    user_name: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WallCommentCreate(BaseModel):
    content: str


# ===== GALLERY MODELS =====


class GalleryAlbum(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    cover_url: str = ""
    photo_count: int = 0
    order: int = 0
    visibility: str = "public"  # public, private
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GalleryAlbumCreate(BaseModel):
    title: str
    description: str = ""
    cover_url: str = ""
    order: int = 0
    visibility: str = "public"


class GalleryPhoto(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    album_id: str
    url: str
    caption: str = ""
    order: int = 0
    status: str = "pending"  # pending, approved, rejected
    uploaded_by: Optional[str] = None
    uploaded_by_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GalleryPhotoCreate(BaseModel):
    album_id: str
    caption: str = ""
    order: int = 0


# ===== EVENT MODELS =====


class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    type: str
    date: datetime
    end_date: Optional[datetime] = None
    location: str
    visibility: str = "socios"
    max_attendees: Optional[int] = None
    attendees: List[str] = []
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EventCreate(BaseModel):
    title: str
    description: str
    type: str
    date: datetime
    end_date: Optional[datetime] = None
    location: str
    visibility: str = "socios"
    max_attendees: Optional[int] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    visibility: Optional[str] = None
    max_attendees: Optional[int] = None


# ===== COMMON MODELS =====


class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    action: str
    target_id: Optional[str] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str
    title: str
    message: str
    link: Optional[str] = None
    read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NotificationCreate(BaseModel):
    user_id: str
    type: str
    title: str
    message: str
    link: Optional[str] = None


# ===== FINANCE MODELS =====

TRANSACTION_TYPES = ["receita", "despesa"]

INCOME_CATEGORIES = ["quotas", "patrocinios", "doacoes", "eventos", "outros_receita"]

EXPENSE_CATEGORIES = ["operacional", "eventos", "juridico", "comunicacao", "viagens", "outros_despesa"]


class Transaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # "receita" or "despesa"
    category: str
    description: str
    amount: float
    date: datetime
    reference: Optional[str] = None
    user_id: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TransactionCreate(BaseModel):
    type: str
    category: str
    description: str
    amount: float
    date: datetime
    reference: Optional[str] = None
    user_id: Optional[str] = None


class TransactionUpdate(BaseModel):
    type: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[datetime] = None
    reference: Optional[str] = None


class FinanceSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "finance_settings"
    quota_amount: float = 2000.0
    quota_description: str = "Quota Mensal"
    # Jóia de admissão (spec-governanca §14): default = 2x quota, salvo
    # deliberação em contrário. joia_amount resolvido pelo backend.
    joia_multiplier: float = 2.0
    joia_amount: Optional[float] = None
    # Alterar quota/jóia exige deliberação de AG por maioria 3/4.
    quota_fixed_by_assembleia_id: Optional[str] = None
    quota_fixed_by_deliberacao_id: Optional[str] = None
    effective_from: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = None


class FinanceSettingsUpdate(BaseModel):
    quota_amount: Optional[float] = None
    quota_description: Optional[str] = None
    joia_multiplier: Optional[float] = None
    joia_amount: Optional[float] = None
    # Referência à deliberação de AG (obrigatória para alterar quota/jóia).
    assembleia_id: Optional[str] = None
    deliberacao_id: Optional[str] = None
    effective_from: Optional[str] = None


# Estados válidos de conta. NÃO existe "inadimplente" (quotas são descontadas
# em folha) — invariante de negócio do projeto.
# - pendente_aprovacao / rejeitado: fluxo de auto-registo (spec-auto-registo).
#   `rejeitado` mantém o documento (auditoria + evita re-registo trivial).
USER_STATUSES = ["ativo", "inativo", "pendente_convite", "pendente_aprovacao", "rejeitado"]


# ===== PROJECT MODELS =====

PROJECT_STATUSES = ["proposta", "aprovado", "em_curso", "concluido", "cancelado"]
PROJECT_VISIBILITIES = ["publico", "privado"]
TASK_STATUSES = ["pendente", "em_curso", "concluido"]
TASK_PRIORITIES = ["baixa", "media", "alta"]


class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    status: str = "proposta"
    visibility: str = "publico"
    category: str = ""
    created_by: str = ""
    created_by_name: str = ""
    responsible_id: Optional[str] = None
    responsible_name: Optional[str] = None
    budget: float = 0.0
    spent: float = 0.0
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    progress: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectCreate(BaseModel):
    title: str
    description: str = ""
    visibility: str = "publico"
    category: str = ""
    budget: float = 0.0
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    visibility: Optional[str] = None
    category: Optional[str] = None
    responsible_id: Optional[str] = None
    budget: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    progress: Optional[int] = None


class ProjectTask(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    title: str
    description: str = ""
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = None
    status: str = "pendente"
    priority: str = "media"
    due_date: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectTaskCreate(BaseModel):
    title: str
    description: str = ""
    assignee_id: Optional[str] = None
    status: str = "pendente"
    priority: str = "media"
    due_date: Optional[str] = None


class ProjectTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None


class ProjectComment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    user_id: str
    user_name: str = ""
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectExpense(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    description: str
    amount: float
    date: str
    created_by: str
    created_by_name: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectMilestone(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    title: str
    date: str
    completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Request models — validação Pydantic em vez de `data: dict` cru
# (payload inválido → 422 em vez de TypeError/500).
class ProjectCommentCreate(BaseModel):
    content: str = Field(min_length=1)


class ProjectExpenseCreate(BaseModel):
    description: str = Field(min_length=1)
    amount: float = Field(gt=0)
    date: Optional[str] = None


class ProjectMilestoneCreate(BaseModel):
    title: str = Field(min_length=1)
    date: str = Field(min_length=1)


class ProjectMilestoneUpdate(BaseModel):
    completed: Optional[bool] = None
    title: Optional[str] = None
    date: Optional[str] = None


# ===== PASSWORD RESET MODELS =====


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=72)


# ===== GOVERNANÇA: ASSEMBLEIA GERAL (spec-governanca §11) =====

ASSEMBLEIA_TIPOS = ["ordinaria", "extraordinaria", "eleitoral"]
ASSEMBLEIA_STATUS = ["rascunho", "convocada", "em_curso", "encerrada", "anulada"]
MAIORIA_TIPOS = ["absoluta", "qualificada_3_4_presentes", "qualificada_3_4_universo"]
MAX_REPRESENTADOS = 3  # um membro representa no máximo 3 outros (Estatutos)


class Assembleia(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tipo: Literal["ordinaria", "extraordinaria", "eleitoral"]
    titulo: str
    data: str  # ISO 8601 (data/hora da sessão)
    local: str
    convocada_por: str
    convocatoria_em: str  # ISO 8601 (momento da convocação)
    antecedencia_dias: int
    requerente_tipo: Optional[str] = None  # mesa | direcao | conselho_fiscal | membros
    requerentes: List[str] = []
    ordem_trabalhos: List[dict] = []
    status: Literal["rascunho", "convocada", "em_curso", "encerrada", "anulada"] = "convocada"
    eligible_voters_count: int = 0
    chamada_actual: Literal[1, 2] = 1
    quorum_required: int = 0
    quorum_met: bool = False
    acta_document_id: Optional[str] = None
    encerrada_em: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AssembleiaCreate(BaseModel):
    tipo: Literal["ordinaria", "extraordinaria", "eleitoral"]
    titulo: str = Field(min_length=3, max_length=200)
    data: str  # ISO 8601
    local: str = Field(min_length=2, max_length=200)
    antecedencia_dias: Optional[int] = None  # se None, calculado de (data - agora)
    requerente_tipo: Optional[str] = None
    requerentes: List[str] = []
    ordem_trabalhos: List[dict] = []


class AssembleiaPresenca(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assembleia_id: str
    user_id: str  # membro presente
    tipo: Literal["propria", "representacao"] = "propria"
    representados: List[str] = []  # ids de membros representados
    voting_power: int = 1  # 1 (se votante) + nº de representados votantes
    documento_id: Optional[str] = None  # procuração/representação
    registado_por: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AssembleiaPresencaCreate(BaseModel):
    user_id: str
    representados: List[str] = Field(default_factory=list, max_length=MAX_REPRESENTADOS)
    documento_id: Optional[str] = None


class AssembleiaDeliberacao(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assembleia_id: str
    ponto: str  # ponto da ordem de trabalhos
    descricao: str
    tipo_maioria: Literal["absoluta", "qualificada_3_4_presentes", "qualificada_3_4_universo"]
    base_calculo: int  # poder de voto presente OU universo (computado pelo servidor)
    votos_favor: int
    votos_contra: int
    abstencoes: int
    threshold: int  # nº de votos necessário (computado)
    aprovado: bool
    source_article: Optional[str] = None
    registado_por: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AssembleiaDeliberacaoCreate(BaseModel):
    ponto: str = Field(min_length=1, max_length=200)
    descricao: str = Field(min_length=1, max_length=2000)
    tipo_maioria: Literal["absoluta", "qualificada_3_4_presentes", "qualificada_3_4_universo"]
    votos_favor: int = Field(ge=0)
    votos_contra: int = Field(ge=0)
    abstencoes: int = Field(ge=0)
    source_article: Optional[str] = Field(default=None, max_length=50)


# ===== GOVERNANÇA: ELEIÇÕES (spec-governanca §12) =====

ELEICAO_STATUS = [
    "preparacao",
    "candidaturas",
    "campanha",
    "votacao",
    "apurada",
    "recurso",
    "proclamada",
    "anulada",
]
MODO_VOTACAO = ["presencial", "correspondencia", "digital", "hibrido"]
# Marcadores de boletim que NÃO contam para os votos válidos.
VOTO_BRANCO = "branco"
VOTO_NULO = "nulo"


class Eleicao(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ano: int
    mandato_inicio: str  # ISO 8601
    mandato_fim: str  # ISO 8601
    status: Literal[
        "preparacao",
        "candidaturas",
        "campanha",
        "votacao",
        "apurada",
        "recurso",
        "proclamada",
        "anulada",
    ] = "preparacao"
    calendario: dict = {}  # convocatoria, candidaturas_fim, votacao, etc. (ISO strings)
    assembleia_id: Optional[str] = None
    comissao_eleitoral: List[str] = []  # ids; não podem ser candidatos
    mesa_voto: List[str] = []  # ids; não podem ser candidatos
    modo_votacao: Literal["presencial", "correspondencia", "digital", "hibrido"] = "presencial"
    direcao_titulares: int = 5  # 5 ou 7 (spec decisão #3)
    resultado: Optional[dict] = None
    created_by: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EleicaoCreate(BaseModel):
    ano: int = Field(ge=2024, le=2100)
    mandato_inicio: str
    mandato_fim: str
    calendario: dict = {}
    assembleia_id: Optional[str] = None
    comissao_eleitoral: List[str] = []
    mesa_voto: List[str] = []
    modo_votacao: Literal["presencial", "correspondencia", "digital", "hibrido"] = "presencial"
    direcao_titulares: Literal[5, 7] = 5


class EleicaoLista(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    eleicao_id: str
    letra: str
    nome: Optional[str] = None
    candidatos: List[dict]  # {slot_key, cargo, user_id, suplente, seat_index}
    programa_document_id: Optional[str] = None
    estado: Literal["submetida", "aceite", "rejeitada"] = "submetida"
    rejeicao_motivo: Optional[str] = None
    submetida_por: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EleicaoListaCreate(BaseModel):
    letra: str = Field(min_length=1, max_length=2)
    nome: Optional[str] = Field(default=None, max_length=120)
    candidatos: List[dict]  # cada item: slot_key, cargo, user_id, suplente, seat_index
    programa_document_id: Optional[str] = None


class EleicaoListaValidar(BaseModel):
    aceite: bool
    motivo: Optional[str] = Field(default=None, max_length=500)


class VotarRequest(BaseModel):
    # lista_id da escolha, ou "branco"/"nulo".
    voto: str


class VotoCorrespondenciaRequest(BaseModel):
    user_id: str
    voto: str  # lista_id, "branco" ou "nulo"
    justificacao: str = Field(min_length=3, max_length=500)


# Boletim secreto: NUNCA contém user_id nem voter_hash (spec §7).
class EleicaoBallot(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    eleicao_id: str
    voto: str  # lista_id, "branco" ou "nulo"
    ballot_box_id: Optional[str] = None
    modo: str = "digital"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Recibo de eleitor: prova (anónima por HMAC) que um eleitor votou uma vez.
# NUNCA contém o sentido de voto (spec §7).
class EleicaoVoterReceipt(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    eleicao_id: str
    voter_hash: str  # HMAC(secret, f"{eleicao_id}:{user_id}")
    modo: str = "digital"
    justificacao: Optional[str] = None  # só para voto por correspondência
    registado_por: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ===== GOVERNANÇA: REGIME DISCIPLINAR (spec-governanca §13) =====

SANCAO_TIPOS = ["advertencia", "multa", "perda_direitos", "expulsao"]
SANCAO_STATUS = ["proposta", "inquerito", "decidida", "recurso", "aplicada", "arquivada", "anulada"]
COMISSAO_INQUERITO_MEMBROS = 3
INQUERITO_PRAZO_DIAS = 30
RECURSO_PRAZO_DIAS = 15
MULTA_MAX_QUOTAS = 3  # multa <= 3x quota mensal


class Sancao(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    tipo: Literal["advertencia", "multa", "perda_direitos", "expulsao"]
    motivo: str
    artigo_violado: Optional[str] = None
    status: Literal["proposta", "inquerito", "decidida", "recurso", "aplicada", "arquivada", "anulada"] = "proposta"
    proposta_por: str
    comissao_inquerito: List[dict] = []
    inquerito_prazo: Optional[str] = None
    conclusoes_document_id: Optional[str] = None
    decisao: Optional[dict] = None
    multa_valor: Optional[float] = None
    perda_direitos_ate: Optional[str] = None
    assembleia_id: Optional[str] = None
    deliberacao_id: Optional[str] = None
    recurso: Optional[dict] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SancaoCreate(BaseModel):
    user_id: str
    tipo: Literal["advertencia", "multa", "perda_direitos", "expulsao"]
    motivo: str = Field(min_length=3, max_length=2000)
    artigo_violado: Optional[str] = Field(default=None, max_length=50)
    multa_valor: Optional[float] = Field(default=None, ge=0)  # obrigatório se tipo=multa
    perda_direitos_ate: Optional[str] = None  # obrigatório se tipo=perda_direitos


class SancaoComissao(BaseModel):
    membros: List[str] = Field(min_length=COMISSAO_INQUERITO_MEMBROS, max_length=COMISSAO_INQUERITO_MEMBROS)
    prazo_dias: int = INQUERITO_PRAZO_DIAS
    conclusoes_document_id: Optional[str] = None


class SancaoDecidir(BaseModel):
    aprovado: bool
    fundamentacao: Optional[str] = Field(default=None, max_length=2000)
    # Obrigatórios para expulsão (decisão da AG):
    assembleia_id: Optional[str] = None
    deliberacao_id: Optional[str] = None


class SancaoRecurso(BaseModel):
    fundamentacao: str = Field(min_length=3, max_length=2000)


# ===== BANNERS DE PÁGINA (spec-padronizacao-banners) =====
# Molde single-doc por chave (como FinanceSettings). 1 doc por banner em
# `page_banners`. Datas serializadas como ISO-8601 string no doc.


class PageBanner(BaseModel):
    model_config = ConfigDict(extra="ignore")
    key: str  # "home" | "sobre" | … (ver BANNER_KEYS em routes/banners.py)
    image_url: str  # /uploads/banners/<uuid>.jpg (ou URL de fallback)
    alt: Optional[str] = None  # texto alternativo (acessibilidade/SEO)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = None


class PageBannerUpdate(BaseModel):
    image_url: Optional[str] = None
    alt: Optional[str] = Field(default=None, max_length=300)


# ===== GESTÃO DA MARCA / LOGO (spec-gestao-logo-marca) =====
# Single-doc settings (molde finance_settings). logo_*_url None → SVG fallback.
# Semântica de "limpar": "" repõe default (grava None); None/ausente = manter.


class BrandSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "brand_settings"
    logo_light_url: Optional[str] = None  # fundo claro; None → SVG fallback
    logo_dark_url: Optional[str] = None  # fundo escuro; None → SVG fallback
    alt: str = "ACCTA Cabo Verde"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = None


class BrandSettingsUpdate(BaseModel):
    logo_light_url: Optional[str] = None  # "" = repor default; None = manter
    logo_dark_url: Optional[str] = None
    alt: Optional[str] = Field(default=None, max_length=200)
