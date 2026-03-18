from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import hashlib
import qrcode
from io import BytesIO
import base64
import shutil

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get('SECRET_KEY', 'accta-secret-key-cabo-verde-2025')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ===== MODELS =====

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "socio"  # admin, financeiro, socio, publico, moderador
    status: str = "ativo"  # ativo, inadimplente, suspenso, pendente
    member_id: Optional[str] = None
    license_number: Optional[str] = None
    admission_date: Optional[datetime] = None
    phone_number: Optional[str] = None
    consent_data: bool = False

class UserCreate(UserBase):
    password: str

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    qr_code_hash: Optional[str] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str  # quota, joia, evento, doacao
    amount: float
    due_date: datetime
    status: str = "pendente"  # pendente, pago, cancelado
    source: str = "folha_salarial"  # folha_salarial, pagamento_manual, isencao, ajuste_administrativo
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

class Poll(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    options: List[dict]  # [{"id": 1, "label": "Aprovar"}]
    start_date: datetime
    end_date: datetime
    status: str = "rascunho"  # rascunho, aberta, fechada
    result_visibility: str = "socios"  # publico, socios, oculto
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

class Post(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    type: str = "noticia"  # noticia, institucional, educativo
    visibility: str = "publico"  # publico, socios
    tags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PostCreate(BaseModel):
    title: str
    content: str
    type: str = "noticia"
    visibility: str = "publico"
    tags: List[str] = []

class Document(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    file_url: str
    type: str  # ata, estatuto, balancete
    visibility: str = "socios"  # publico, socios, direcao
    tags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DocumentCreate(BaseModel):
    title: str
    file_url: str
    type: str
    visibility: str = "socios"
    tags: List[str] = []

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

class WallPost(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    content: str
    approved: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WallPostCreate(BaseModel):
    content: str

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
    type: str  # poll_opened, invoice_due, document_new, wall_post_approved
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

# Event Models
class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    type: str  # assembleia, formacao, social, reuniao, outro
    date: datetime
    end_date: Optional[datetime] = None
    location: str
    visibility: str = "socios"  # publico, socios, direcao
    max_attendees: Optional[int] = None
    attendees: List[str] = []  # List of user_ids
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

# ===== HELPER FUNCTIONS =====

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def generate_qr_hash(user_id: str) -> str:
    return hashlib.sha256(f"accta-cv-{user_id}-{uuid.uuid4()}".encode()).hexdigest()

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user_doc is None:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        return User(**user_doc)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def create_audit_log(user_id: str, action: str, target_id: Optional[str] = None):
    log = AuditLog(user_id=user_id, action=action, target_id=target_id)
    log_dict = log.model_dump()
    log_dict['created_at'] = log_dict['created_at'].isoformat()
    await db.audit_logs.insert_one(log_dict)

async def create_notification(user_id: str, type: str, title: str, message: str, link: Optional[str] = None):
    """Helper function to create notifications"""
    notification = Notification(user_id=user_id, type=type, title=title, message=message, link=link)
    notif_dict = notification.model_dump()
    notif_dict['created_at'] = notif_dict['created_at'].isoformat()
    await db.notifications.insert_one(notif_dict)

async def notify_all_active_users(type: str, title: str, message: str, link: Optional[str] = None):
    """Send notification to all active members - Batch insert for performance"""
    users = await db.users.find({"status": "ativo"}, {"_id": 0, "id": 1}).to_list(1000)
    
    if not users:
        return
    
    # Batch insert all notifications at once
    notifications = []
    for user in users:
        notification = Notification(user_id=user['id'], type=type, title=title, message=message, link=link)
        notif_dict = notification.model_dump()
        notif_dict['created_at'] = notif_dict['created_at'].isoformat()
        notifications.append(notif_dict)
    
    if notifications:
        await db.notifications.insert_many(notifications)

# ===== ROUTES =====

@api_router.get("/")
async def root():
    return {"message": "ACCTA Portal API v1.0"}

# AUTH ROUTES
@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email já registrado")
    
    user = User(**user_data.model_dump(exclude={"password"}))
    user.qr_code_hash = generate_qr_hash(user.id)
    
    user_dict = user.model_dump()
    user_dict['password'] = hash_password(user_data.password)
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    if user_dict.get('admission_date'):
        user_dict['admission_date'] = user_dict['admission_date'].isoformat()
    if user_dict.get('last_login_at'):
        user_dict['last_login_at'] = user_dict['last_login_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    return user

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    user_doc = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user_doc or not verify_password(credentials.password, user_doc['password']):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    # Update last login
    await db.users.update_one(
        {"email": credentials.email},
        {"$set": {"last_login_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    user_doc.pop('password', None)
    if isinstance(user_doc.get('created_at'), str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    if user_doc.get('admission_date') and isinstance(user_doc['admission_date'], str):
        user_doc['admission_date'] = datetime.fromisoformat(user_doc['admission_date'])
    if user_doc.get('last_login_at') and isinstance(user_doc['last_login_at'], str):
        user_doc['last_login_at'] = datetime.fromisoformat(user_doc['last_login_at'])
    
    user = User(**user_doc)
    token = create_access_token({"sub": user.id})
    
    return Token(access_token=token, token_type="bearer", user=user)

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# USER ROUTES
@api_router.get("/users", response_model=List[User])
async def get_users(skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "financeiro"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    # Enforce max limit of 100 per request
    limit = min(limit, 100)
    users = await db.users.find({}, {"_id": 0, "password": 0}).skip(skip).limit(limit).to_list(None)
    for u in users:
        if isinstance(u.get('created_at'), str):
            u['created_at'] = datetime.fromisoformat(u['created_at'])
        if u.get('admission_date') and isinstance(u['admission_date'], str):
            u['admission_date'] = datetime.fromisoformat(u['admission_date'])
        if u.get('last_login_at') and isinstance(u['last_login_at'], str):
            u['last_login_at'] = datetime.fromisoformat(u['last_login_at'])
    return users

@api_router.patch("/users/{user_id}/status")
async def update_user_status(user_id: str, status: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    await db.users.update_one({"id": user_id}, {"$set": {"status": status}})
    await create_audit_log(current_user.id, f"Alterou status do usuário {user_id} para {status}", user_id)
    return {"message": "Status atualizado"}

# INVOICE ROUTES
@api_router.get("/invoices", response_model=List[Invoice])
async def get_invoices(skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user)):
    limit = min(limit, 100)
    if current_user.role in ["admin", "financeiro"]:
        invoices = await db.invoices.find({}, {"_id": 0}).skip(skip).limit(limit).to_list(None)
    else:
        invoices = await db.invoices.find({"user_id": current_user.id}, {"_id": 0}).skip(skip).limit(limit).to_list(None)
    
    for inv in invoices:
        if isinstance(inv.get('due_date'), str):
            inv['due_date'] = datetime.fromisoformat(inv['due_date'])
        if isinstance(inv.get('created_at'), str):
            inv['created_at'] = datetime.fromisoformat(inv['created_at'])
        if inv.get('confirmed_at') and isinstance(inv['confirmed_at'], str):
            inv['confirmed_at'] = datetime.fromisoformat(inv['confirmed_at'])
    return invoices

@api_router.post("/invoices", response_model=Invoice)
async def create_invoice(invoice_data: InvoiceCreate, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "financeiro"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    invoice = Invoice(**invoice_data.model_dump())
    invoice_dict = invoice.model_dump()
    invoice_dict['due_date'] = invoice_dict['due_date'].isoformat()
    invoice_dict['created_at'] = invoice_dict['created_at'].isoformat()
    if invoice_dict.get('confirmed_at'):
        invoice_dict['confirmed_at'] = invoice_dict['confirmed_at'].isoformat()
    
    await db.invoices.insert_one(invoice_dict)
    await create_audit_log(current_user.id, f"Criou invoice {invoice.id}", invoice.id)
    return invoice

@api_router.patch("/invoices/{invoice_id}/confirm")
async def confirm_invoice(invoice_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "financeiro"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {
            "status": "pago",
            "confirmed_by_admin": True,
            "confirmed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    await create_audit_log(current_user.id, f"Confirmou pagamento do invoice {invoice_id}", invoice_id)
    return {"message": "Invoice confirmado"}

# POLL ROUTES
@api_router.get("/polls", response_model=List[Poll])
async def get_polls(skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user)):
    limit = min(limit, 100)
    polls = await db.polls.find({}, {"_id": 0}).skip(skip).limit(limit).to_list(None)
    for p in polls:
        if isinstance(p.get('start_date'), str):
            p['start_date'] = datetime.fromisoformat(p['start_date'])
        if isinstance(p.get('end_date'), str):
            p['end_date'] = datetime.fromisoformat(p['end_date'])
        if isinstance(p.get('created_at'), str):
            p['created_at'] = datetime.fromisoformat(p['created_at'])
    return polls

@api_router.post("/polls", response_model=Poll)
async def create_poll(poll_data: PollCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    poll = Poll(**poll_data.model_dump())
    poll_dict = poll.model_dump()
    poll_dict['start_date'] = poll_dict['start_date'].isoformat()
    poll_dict['end_date'] = poll_dict['end_date'].isoformat()
    poll_dict['created_at'] = poll_dict['created_at'].isoformat()
    
    await db.polls.insert_one(poll_dict)
    await create_audit_log(current_user.id, f"Criou votação {poll.id}", poll.id)
    
    # Notify all active users about new poll
    await notify_all_active_users(
        "poll_opened",
        "Nova Votação Aberta",
        f"{poll.title} - Participe agora!",
        "/votacoes"
    )
    
    return poll

@api_router.post("/polls/vote", response_model=UserVote)
async def vote(vote_data: VoteCreate, current_user: User = Depends(get_current_user)):
    if current_user.status != "ativo":
        raise HTTPException(status_code=403, detail="Apenas sócios ativos podem votar")
    
    # Check if already voted
    existing_vote = await db.user_votes.find_one({"user_id": current_user.id, "poll_id": vote_data.poll_id})
    if existing_vote:
        raise HTTPException(status_code=400, detail="Você já votou nesta votação")
    
    vote = UserVote(user_id=current_user.id, **vote_data.model_dump())
    vote_dict = vote.model_dump()
    vote_dict['created_at'] = vote_dict['created_at'].isoformat()
    
    await db.user_votes.insert_one(vote_dict)
    return vote

@api_router.get("/polls/{poll_id}/results")
async def get_poll_results(poll_id: str, current_user: User = Depends(get_current_user)):
    poll = await db.polls.find_one({"id": poll_id}, {"_id": 0})
    if not poll:
        raise HTTPException(status_code=404, detail="Votação não encontrada")
    
    votes = await db.user_votes.find({"poll_id": poll_id}, {"_id": 0}).to_list(1000)
    results = {}
    for vote in votes:
        option = vote['vote_option']
        results[option] = results.get(option, 0) + 1
    
    return {"poll_id": poll_id, "total_votes": len(votes), "results": results}

# POST ROUTES
@api_router.get("/posts", response_model=List[Post])
async def get_posts(visibility: Optional[str] = None):
    query = {}
    if visibility:
        query['visibility'] = visibility
    posts = await db.posts.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    for p in posts:
        if isinstance(p.get('created_at'), str):
            p['created_at'] = datetime.fromisoformat(p['created_at'])
    return posts

@api_router.post("/posts", response_model=Post)
async def create_post(post_data: PostCreate, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "moderador"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    post = Post(**post_data.model_dump())
    post_dict = post.model_dump()
    post_dict['created_at'] = post_dict['created_at'].isoformat()
    
    await db.posts.insert_one(post_dict)
    await create_audit_log(current_user.id, f"Criou post {post.id}", post.id)
    return post

# DOCUMENT ROUTES
@api_router.get("/documents", response_model=List[Document])
async def get_documents(current_user: User = Depends(get_current_user)):
    if current_user.role in ["admin", "financeiro", "moderador"]:
        docs = await db.documents.find({}, {"_id": 0}).to_list(1000)
    else:
        docs = await db.documents.find({"visibility": {"$in": ["publico", "socios"]}}, {"_id": 0}).to_list(1000)
    
    for d in docs:
        if isinstance(d.get('created_at'), str):
            d['created_at'] = datetime.fromisoformat(d['created_at'])
    return docs

@api_router.post("/documents", response_model=Document)
async def create_document(doc_data: DocumentCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    doc = Document(**doc_data.model_dump())
    doc_dict = doc.model_dump()
    doc_dict['created_at'] = doc_dict['created_at'].isoformat()
    
    await db.documents.insert_one(doc_dict)
    await create_audit_log(current_user.id, f"Criou documento {doc.id}", doc.id)
    return doc

# BENEFIT ROUTES
@api_router.get("/benefits", response_model=List[Benefit])
async def get_benefits(current_user: User = Depends(get_current_user)):
    if current_user.status != "ativo":
        raise HTTPException(status_code=403, detail="Benefícios disponíveis apenas para sócios ativos")
    
    benefits = await db.benefits.find({"active": True}, {"_id": 0}).to_list(1000)
    for b in benefits:
        if isinstance(b.get('created_at'), str):
            b['created_at'] = datetime.fromisoformat(b['created_at'])
    return benefits

@api_router.post("/benefits", response_model=Benefit)
async def create_benefit(benefit_data: BenefitCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    benefit = Benefit(**benefit_data.model_dump())
    benefit_dict = benefit.model_dump()
    benefit_dict['created_at'] = benefit_dict['created_at'].isoformat()
    
    await db.benefits.insert_one(benefit_dict)
    await create_audit_log(current_user.id, f"Criou benefício {benefit.id}", benefit.id)
    return benefit

# WALL POST ROUTES
@api_router.get("/wall", response_model=List[WallPost])
async def get_wall_posts(current_user: User = Depends(get_current_user)):
    if current_user.status != "ativo":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    posts = await db.wall_posts.find({"approved": True}, {"_id": 0}).sort("created_at", -1).to_list(100)
    for p in posts:
        if isinstance(p.get('created_at'), str):
            p['created_at'] = datetime.fromisoformat(p['created_at'])
    return posts

@api_router.post("/wall", response_model=WallPost)
async def create_wall_post(post_data: WallPostCreate, current_user: User = Depends(get_current_user)):
    if current_user.status != "ativo":
        raise HTTPException(status_code=403, detail="Apenas sócios ativos podem postar")
    
    post = WallPost(user_id=current_user.id, user_name=current_user.name, **post_data.model_dump())
    post_dict = post.model_dump()
    post_dict['created_at'] = post_dict['created_at'].isoformat()
    
    await db.wall_posts.insert_one(post_dict)
    return post

@api_router.patch("/wall/{post_id}/approve")
async def approve_wall_post(post_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "moderador"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    await db.wall_posts.update_one({"id": post_id}, {"$set": {"approved": True}})
    await create_audit_log(current_user.id, f"Aprovou post do mural {post_id}", post_id)
    return {"message": "Post aprovado"}

# EVENT ROUTES
@api_router.get("/events", response_model=List[Event])
async def get_events(visibility: Optional[str] = None, current_user: User = Depends(get_current_user)):
    """Get events based on user role and visibility"""
    query = {}
    
    # Filter by visibility based on user role
    if current_user.role == "admin":
        # Admin sees all events
        pass
    elif current_user.role in ["socio", "financeiro", "moderador"]:
        # Members see public and socios events
        query["visibility"] = {"$in": ["publico", "socios"]}
    else:
        # Others see only public events
        query["visibility"] = "publico"
    
    if visibility:
        query["visibility"] = visibility
    
    events = await db.events.find(query, {"_id": 0}).sort("date", 1).to_list(100)
    for e in events:
        if isinstance(e.get('date'), str):
            e['date'] = datetime.fromisoformat(e['date'])
        if isinstance(e.get('end_date'), str):
            e['end_date'] = datetime.fromisoformat(e['end_date'])
        if isinstance(e.get('created_at'), str):
            e['created_at'] = datetime.fromisoformat(e['created_at'])
    return events

@api_router.get("/events/public")
async def get_public_events():
    """Get public events (no auth required)"""
    events = await db.events.find({"visibility": "publico"}, {"_id": 0}).sort("date", 1).to_list(100)
    for e in events:
        if isinstance(e.get('date'), str):
            e['date'] = datetime.fromisoformat(e['date'])
        if isinstance(e.get('end_date'), str):
            e['end_date'] = datetime.fromisoformat(e['end_date'])
        if isinstance(e.get('created_at'), str):
            e['created_at'] = datetime.fromisoformat(e['created_at'])
        # Remove attendees list for public view
        e.pop('attendees', None)
    return events

@api_router.get("/events/upcoming")
async def get_upcoming_events(current_user: User = Depends(get_current_user)):
    """Get upcoming events for dashboard widget"""
    now = datetime.now(timezone.utc).isoformat()
    query = {"date": {"$gte": now}}
    
    if current_user.role != "admin":
        query["visibility"] = {"$in": ["publico", "socios"]}
    
    events = await db.events.find(query, {"_id": 0}).sort("date", 1).limit(5).to_list(None)
    for e in events:
        if isinstance(e.get('date'), str):
            e['date'] = datetime.fromisoformat(e['date'])
        if isinstance(e.get('end_date'), str):
            e['end_date'] = datetime.fromisoformat(e['end_date'])
        if isinstance(e.get('created_at'), str):
            e['created_at'] = datetime.fromisoformat(e['created_at'])
    return events

@api_router.get("/events/{event_id}", response_model=Event)
async def get_event(event_id: str, current_user: User = Depends(get_current_user)):
    event = await db.events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    
    # Check visibility permissions
    if event['visibility'] == "direcao" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    if isinstance(event.get('date'), str):
        event['date'] = datetime.fromisoformat(event['date'])
    if isinstance(event.get('end_date'), str):
        event['end_date'] = datetime.fromisoformat(event['end_date'])
    if isinstance(event.get('created_at'), str):
        event['created_at'] = datetime.fromisoformat(event['created_at'])
    
    return event

@api_router.post("/events", response_model=Event)
async def create_event(event_data: EventCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem criar eventos")
    
    event = Event(created_by=current_user.id, **event_data.model_dump())
    event_dict = event.model_dump()
    event_dict['date'] = event_dict['date'].isoformat()
    if event_dict.get('end_date'):
        event_dict['end_date'] = event_dict['end_date'].isoformat()
    event_dict['created_at'] = event_dict['created_at'].isoformat()
    
    await db.events.insert_one(event_dict)
    await create_audit_log(current_user.id, f"Criou evento {event.title}", event.id)
    
    # Notify users based on visibility
    if event_data.visibility in ["publico", "socios"]:
        await notify_all_active_users(
            "event_new",
            "Novo Evento",
            f"Novo evento: {event.title}",
            f"/eventos"
        )
    
    return event

@api_router.patch("/events/{event_id}", response_model=Event)
async def update_event(event_id: str, event_data: EventUpdate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    
    update_data = {k: v for k, v in event_data.model_dump().items() if v is not None}
    if 'date' in update_data:
        update_data['date'] = update_data['date'].isoformat()
    if 'end_date' in update_data:
        update_data['end_date'] = update_data['end_date'].isoformat()
    
    await db.events.update_one({"id": event_id}, {"$set": update_data})
    await create_audit_log(current_user.id, f"Atualizou evento {event_id}", event_id)
    
    updated_event = await db.events.find_one({"id": event_id}, {"_id": 0})
    if isinstance(updated_event.get('date'), str):
        updated_event['date'] = datetime.fromisoformat(updated_event['date'])
    if isinstance(updated_event.get('end_date'), str):
        updated_event['end_date'] = datetime.fromisoformat(updated_event['end_date'])
    if isinstance(updated_event.get('created_at'), str):
        updated_event['created_at'] = datetime.fromisoformat(updated_event['created_at'])
    
    return updated_event

@api_router.delete("/events/{event_id}")
async def delete_event(event_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    result = await db.events.delete_one({"id": event_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    
    await create_audit_log(current_user.id, f"Eliminou evento {event_id}", event_id)
    return {"message": "Evento eliminado"}

@api_router.post("/events/{event_id}/register")
async def register_for_event(event_id: str, current_user: User = Depends(get_current_user)):
    """Register current user for an event"""
    if current_user.status != "ativo":
        raise HTTPException(status_code=403, detail="Apenas sócios ativos podem inscrever-se")
    
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    
    # Check if already registered
    if current_user.id in event.get('attendees', []):
        raise HTTPException(status_code=400, detail="Já está inscrito neste evento")
    
    # Check max attendees
    if event.get('max_attendees') and len(event.get('attendees', [])) >= event['max_attendees']:
        raise HTTPException(status_code=400, detail="Evento já está lotado")
    
    await db.events.update_one(
        {"id": event_id},
        {"$push": {"attendees": current_user.id}}
    )
    
    await create_notification(
        current_user.id,
        "event_registered",
        "Inscrição Confirmada",
        f"Sua inscrição no evento '{event['title']}' foi confirmada.",
        "/eventos"
    )
    
    return {"message": "Inscrição realizada com sucesso"}

@api_router.delete("/events/{event_id}/register")
async def unregister_from_event(event_id: str, current_user: User = Depends(get_current_user)):
    """Unregister current user from an event"""
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    
    if current_user.id not in event.get('attendees', []):
        raise HTTPException(status_code=400, detail="Não está inscrito neste evento")
    
    await db.events.update_one(
        {"id": event_id},
        {"$pull": {"attendees": current_user.id}}
    )
    
    return {"message": "Inscrição cancelada"}

@api_router.get("/events/{event_id}/attendees")
async def get_event_attendees(event_id: str, current_user: User = Depends(get_current_user)):
    """Get list of attendees for an event"""
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    
    # Only admin or event creator can see full attendee list
    if current_user.role != "admin" and current_user.id != event.get('created_by'):
        # For regular users, just return count and whether they're registered
        return {
            "count": len(event.get('attendees', [])),
            "is_registered": current_user.id in event.get('attendees', []),
            "attendees": []
        }
    
    # Get attendee details
    attendee_ids = event.get('attendees', [])
    if not attendee_ids:
        return {"count": 0, "is_registered": False, "attendees": []}
    
    attendees = await db.users.find(
        {"id": {"$in": attendee_ids}},
        {"_id": 0, "id": 1, "name": 1, "email": 1, "member_id": 1}
    ).to_list(None)
    
    return {
        "count": len(attendees),
        "is_registered": current_user.id in attendee_ids,
        "attendees": attendees
    }

# VALIDATOR ROUTE (PUBLIC)
@api_router.get("/validate/{qr_hash}")
async def validate_wallet(qr_hash: str):
    user = await db.users.find_one({"qr_code_hash": qr_hash}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Carteira não encontrada")
    
    if isinstance(user.get('created_at'), str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    if user.get('admission_date') and isinstance(user['admission_date'], str):
        user['admission_date'] = datetime.fromisoformat(user['admission_date'])
    
    return {
        "valid": True,
        "name": user['name'],
        "member_id": user.get('member_id'),
        "status": user['status'],
        "admission_date": user.get('admission_date')
    }

# AUDIT LOGS
@api_router.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    logs = await db.audit_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    for log in logs:
        if isinstance(log.get('created_at'), str):
            log['created_at'] = datetime.fromisoformat(log['created_at'])
    return logs

# NOTIFICATIONS
@api_router.get("/notifications", response_model=List[Notification])
async def get_notifications(current_user: User = Depends(get_current_user)):
    notifications = await db.notifications.find({"user_id": current_user.id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    for notif in notifications:
        if isinstance(notif.get('created_at'), str):
            notif['created_at'] = datetime.fromisoformat(notif['created_at'])
    return notifications

@api_router.get("/notifications/unread/count")
async def get_unread_count(current_user: User = Depends(get_current_user)):
    count = await db.notifications.count_documents({"user_id": current_user.id, "read": False})
    return {"count": count}

@api_router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: User = Depends(get_current_user)):
    await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user.id},
        {"$set": {"read": True}}
    )
    return {"message": "Notificação marcada como lida"}

@api_router.patch("/notifications/mark-all-read")
async def mark_all_notifications_read(current_user: User = Depends(get_current_user)):
    result = await db.notifications.update_many(
        {"user_id": current_user.id, "read": False},
        {"$set": {"read": True}}
    )
    return {"message": f"{result.modified_count} notificações marcadas como lidas"}

@api_router.post("/notifications", response_model=Notification)
async def create_notification(notif_data: NotificationCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    notification = Notification(**notif_data.model_dump())
    notif_dict = notification.model_dump()
    notif_dict['created_at'] = notif_dict['created_at'].isoformat()
    
    await db.notifications.insert_one(notif_dict)
    return notification

# STATISTICS
@api_router.get("/stats")
async def get_statistics(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "financeiro"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"status": "ativo"})
    pending_invoices = await db.invoices.count_documents({"status": "pendente"})
    total_revenue = await db.invoices.aggregate([
        {"$match": {"status": "pago"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "pending_invoices": pending_invoices,
        "total_revenue": total_revenue[0]['total'] if total_revenue else 0
    }

# FILE UPLOAD
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {
    "documents": [".pdf", ".doc", ".docx"],
    "proofs": [".pdf", ".jpg", ".jpeg", ".png"],
    "logos": [".png", ".jpg", ".jpeg", ".svg"],
    "avatars": [".jpg", ".jpeg", ".png"],
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file(file: UploadFile, category: str) -> None:
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS.get(category, []):
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo não permitido. Permitidos: {', '.join(ALLOWED_EXTENSIONS[category])}"
        )

@api_router.post("/upload/{category}")
async def upload_file(
    category: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Validate category
    if category not in ["documents", "proofs", "logos", "avatars"]:
        raise HTTPException(status_code=400, detail="Categoria inválida")
    
    # Permission check
    if category in ["documents", "logos"] and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    # Validate file
    validate_file(file, category)
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / category / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Generate URL
        file_url = f"/uploads/{category}/{unique_filename}"
        
        await create_audit_log(current_user.id, f"Upload de arquivo: {file.filename}", unique_filename)
        
        return {
            "filename": file.filename,
            "file_url": file_url,
            "size": file_path.stat().st_size,
            "category": category
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")

@api_router.delete("/upload/{category}/{filename}")
async def delete_file(
    category: str,
    filename: str,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    file_path = UPLOAD_DIR / category / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    try:
        file_path.unlink()
        await create_audit_log(current_user.id, f"Deletou arquivo: {filename}", filename)
        return {"message": "Arquivo deletado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar arquivo: {str(e)}")

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
