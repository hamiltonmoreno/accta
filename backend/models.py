from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Literal, Optional
from datetime import datetime, timezone
import uuid


# ===== USER MODELS =====
# Modelo de identidade e cargos (spec-identidade-cargos):
# - account_type separa pessoas reais ("member") de contas de sistema ("technical").
# - role = nível de acesso "grosso" (admin/financeiro/moderador/socio).
# - cargo = função institucional eleita; privileges = overlays granulares.
# - member_id = identificador permanente e imutável do sócio real.

ACCOUNT_TYPES = ["member", "technical"]

ROLES_VALID = ["admin", "financeiro", "moderador", "socio"]

# Cargos agrupados por órgão social (CV/PT típico). A lista plana `CARGOS` é
# derivada daqui e usada para validação em endpoints e auto-registo.
CARGOS_ORGAOS_SOCIAIS = {
    "Direcção": [
        "Presidente",
        "Vice-Presidente",
        "Secretário-Geral",
        "Tesoureiro",
        "Vogal da Direcção",
    ],
    "Conselho Fiscal": [
        "Presidente do Conselho Fiscal",
        "Vogal do Conselho Fiscal",
    ],
    "Mesa da Assembleia Geral": [
        "Presidente da Mesa",
        "Vice-Presidente da Mesa",
        "Secretário da Mesa",
    ],
    "Coordenações": [
        "Coordenador de Comunicação",
        "Coordenador de Eventos",
        "Coordenador de Projectos",
    ],
    "Comissões": [
        "Membro da Comissão de Ética",
    ],
    "Base": [
        "Sócio",  # default, sem mandato institucional
    ],
}

# Lista plana (15 cargos institucionais + Sócio) para validação.
CARGOS = [c for grupo in CARGOS_ORGAOS_SOCIAIS.values() for c in grupo]

PRIVILEGES = [
    "manage_users",
    "manage_finances",
    "manage_events",
    "manage_documents",
    "moderate_content",
    "manage_benefits",
    "view_audit_logs",
    "view_finances_readonly",  # leitura do módulo financeiro sem poder editar (Conselho Fiscal)
]

# Defaults pré-carregados no modal de aprovação/promoção. O admin pode sobrepor.
# role é o nível grosso; privileges são overlays granulares (ver spec).
CARGO_DEFAULTS = {
    "Presidente": {"role": "admin", "privileges": list(PRIVILEGES)},
    "Vice-Presidente": {"role": "admin", "privileges": list(PRIVILEGES)},
    "Secretário-Geral": {
        "role": "admin",
        "privileges": ["manage_users", "manage_events", "manage_documents", "moderate_content"],
    },
    "Tesoureiro": {"role": "financeiro", "privileges": ["manage_finances", "view_audit_logs"]},
    "Vogal da Direcção": {"role": "moderador", "privileges": ["moderate_content", "manage_events"]},
    "Presidente do Conselho Fiscal": {
        "role": "socio",
        "privileges": ["view_finances_readonly", "view_audit_logs"],
    },
    "Vogal do Conselho Fiscal": {
        "role": "socio",
        "privileges": ["view_finances_readonly", "view_audit_logs"],
    },
    "Presidente da Mesa": {"role": "socio", "privileges": ["manage_events"]},
    "Vice-Presidente da Mesa": {"role": "socio", "privileges": []},
    "Secretário da Mesa": {"role": "socio", "privileges": ["manage_documents"]},
    "Coordenador de Comunicação": {
        "role": "moderador",
        "privileges": ["moderate_content", "manage_events"],
    },
    "Coordenador de Eventos": {"role": "socio", "privileges": ["manage_events"]},
    "Coordenador de Projectos": {"role": "socio", "privileges": ["manage_events", "manage_documents"]},
    "Membro da Comissão de Ética": {"role": "socio", "privileges": ["view_audit_logs"]},
    "Sócio": {"role": "socio", "privileges": []},
}

# Número de vagas por cargo. 0 = sem limite (Sócio é o estado base de todos).
CARGO_SEATS = {
    "Presidente": 1,
    "Vice-Presidente": 1,
    "Secretário-Geral": 1,
    "Tesoureiro": 1,
    "Vogal da Direcção": 3,
    "Presidente do Conselho Fiscal": 1,
    "Vogal do Conselho Fiscal": 2,
    "Presidente da Mesa": 1,
    "Vice-Presidente da Mesa": 1,
    "Secretário da Mesa": 1,
    "Coordenador de Comunicação": 1,
    "Coordenador de Eventos": 1,
    "Coordenador de Projectos": 1,
    "Membro da Comissão de Ética": 3,
    "Sócio": 0,
}


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
    cargo: str = "Sócio"
    privileges: List[str] = []
    cargo_history: List[dict] = []
    bio: Optional[str] = None
    department: Optional[str] = None
    photo_url: Optional[str] = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    qr_code_hash: Optional[str] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None


class UserAdminUpdate(BaseModel):
    # NOTA: member_id NÃO é editável aqui — é imutável depois de atribuído
    # (spec-identidade-cargos). Alterações manuais ficam restritas a script de
    # migração fora da API comum.
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    status: Optional[str] = None
    cargo: Optional[str] = None
    privileges: Optional[List[str]] = None
    license_number: Optional[str] = None
    phone_number: Optional[str] = None
    department: Optional[str] = None
    bio: Optional[str] = None


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


class RegistrationApprove(BaseModel):
    role: str = "socio"  # validado contra ["socio","financeiro","moderador","admin"] na rota
    cargo: Optional[str] = None  # se None, mantém o cargo_declarado


class RegistrationReject(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=500)


# ===== CARGO / MANDATO MODELS (spec-identidade-cargos) =====

# Cada entrada de cargo_history documenta um mandato do sócio. Armazenado como
# dict no doc.cargo_history; este modelo valida/serializa as escritas.
class CargoMandate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cargo: str
    role: str
    inicio: str  # ISO 8601, obrigatório
    fim: Optional[str] = None  # ISO 8601; None = mandato activo
    elected_by: Optional[str] = None  # "AGA 2026", "Direcção", texto livre
    transitioned_by: str  # id do admin que efectuou a alteração
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


class Post(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    type: str = "noticia"
    visibility: str = "publico"
    tags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PostCreate(BaseModel):
    title: str
    content: str
    type: str = "noticia"
    visibility: str = "publico"
    tags: List[str] = []


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
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = None


class FinanceSettingsUpdate(BaseModel):
    quota_amount: Optional[float] = None
    quota_description: Optional[str] = None


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
