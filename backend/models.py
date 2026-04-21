from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
from datetime import datetime, timezone
import uuid


# ===== USER MODELS =====

CARGOS = [
    "Presidente", "Vice-Presidente", "Secretário-Geral",
    "Tesoureiro", "Vogal", "Membro da Direção", "Sócio"
]

PRIVILEGES = [
    "manage_users", "manage_finances", "manage_events",
    "manage_documents", "moderate_content", "manage_benefits",
    "view_audit_logs"
]


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
    cargo: str = "Sócio"
    privileges: List[str] = []
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
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    status: Optional[str] = None
    cargo: Optional[str] = None
    privileges: Optional[List[str]] = None
    member_id: Optional[str] = None
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
    password: str


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

class Benefit(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    logo_url: Optional[str] = None
    discount_percent: float
    active: bool = True
    validation_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BenefitCreate(BaseModel):
    name: str
    description: str
    logo_url: Optional[str] = None
    discount_percent: float


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

INCOME_CATEGORIES = [
    "quotas", "patrocinios", "doacoes", "eventos", "outros_receita"
]

EXPENSE_CATEGORIES = [
    "operacional", "eventos", "juridico", "comunicacao", "viagens", "outros_despesa"
]


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


# ===== PASSWORD RESET MODELS =====

class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
