from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
    """Send notification to all active members"""
    users = await db.users.find({"status": "ativo"}, {"_id": 0, "id": 1}).to_list(1000)
    for user in users:
        await create_notification(user['id'], type, title, message, link)

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
async def get_users(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "financeiro"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
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
async def get_invoices(current_user: User = Depends(get_current_user)):
    if current_user.role in ["admin", "financeiro"]:
        invoices = await db.invoices.find({}, {"_id": 0}).to_list(1000)
    else:
        invoices = await db.invoices.find({"user_id": current_user.id}, {"_id": 0}).to_list(1000)
    
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
async def get_polls(current_user: User = Depends(get_current_user)):
    polls = await db.polls.find({}, {"_id": 0}).to_list(1000)
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
