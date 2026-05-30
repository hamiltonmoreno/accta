from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator, model_validator
from typing import List, Literal, Optional
from datetime import datetime, timezone, date
import re
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
    admission_date: Optional[str] = None
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
    # Opt-out de comunicados informativos por email (spec-comunicados-email).
    # Round-trips por /auth/me para o toggle do perfil refletir o valor guardado.
    email_opt_out_informativos: bool = False
    # Opt-out do ranking (spec-ranking-socio §2.5): membro fora das LISTAS
    # públicas (leaderboard) mas continua a ver a sua própria posição (/me).
    ranking_opt_out: bool = False
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
    # Jóia de admissão (spec-controlos §6, Art. 6) — aditivos/opcionais:
    # - cta_qualified_since: ISO date em que se qualificou como CTA (a jóia é
    #   2× a quota se >4 meses, salvo isenção/fundador).
    # - joia_devida: valor assinalado na admissão (assinalar, não cobrar).
    # - joia_isento: fundador/honorário/decisão manual.
    cta_qualified_since: Optional[str] = None
    joia_devida: Optional[float] = None
    joia_isento: Optional[bool] = None
    # MFA TOTP (spec-mfa-f2). Só a flag é exposta; segredo/backup vivem no doc
    # jsonb e nunca em modelos (User tem extra="ignore").
    mfa_enabled: bool = False


class UserCreate(UserBase):
    password: str


class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    qr_code_hash: Optional[str] = None
    last_login_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Campos secretos de MFA — NUNCA expostos (a par de password). Usar em toda
# projeção de utilizador que vá para o cliente.
MFA_SECRET_FIELDS = ("mfa_secret", "mfa_pending_secret", "mfa_backup_codes")


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


def _validate_datetime_str(v, *, label: str = "Data"):
    """Valida string de data-hora ISO-8601 (input do cliente) e devolve-a
    normalizada. As datas guardam-se como string ISO (regra models.md); este
    validador preserva a validação que o tipo `datetime` dava de borla nos
    modelos de escrita. None passa (campos Optional); "" é rejeitado — uma
    string vazia num campo de data dava 422 com o tipo `datetime` e, sem isto,
    seria guardada como data inválida (parte sorts/$gte e crasha _parse_dt)."""
    if v is None:
        return v
    if isinstance(v, datetime):
        return v.isoformat()
    try:
        parsed = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        raise ValueError(f"{label} deve ser uma data-hora ISO-8601 válida")
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
    # NOTA: photo_url NÃO vive aqui de propósito — só o próprio gere a sua foto
    # (UserProfileUpdate). Admin/moderador apenas REMOVEM via
    # DELETE /users/{id}/photo, nunca definem (spec-foto-de-perfil §5.2).
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

    # Foto de perfil — só o próprio a define/troca/limpa ("" limpa; o route
    # apaga o ficheiro antigo). Fora do UserAdminUpdate por design.
    photo_url: Optional[str] = Field(default=None, max_length=500)

    @field_validator("photo_url")
    @classmethod
    def _v_photo_url(cls, v):
        # Só aceita avatares carregados pelo nosso endpoint (/uploads/avatars/…),
        # "" (limpar) ou None (manter). Bloqueia URLs externas — impede beacons de
        # tracking embutidos no avatar e carregamento de imagem de terceiros.
        if v in (None, ""):
            return v
        if not v.startswith("/uploads/avatars/"):
            raise ValueError("URL de foto inválida")
        return v


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
    otp: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    user: User
    mfa_setup_required: bool = False


class MfaVerifyRequest(BaseModel):
    otp: str


class MfaDisableRequest(BaseModel):
    password: str


class InviteCreate(BaseModel):
    name: str
    email: EmailStr
    role: str = "socio"
    cargo: Optional[str] = None
    member_id: Optional[str] = None
    license_number: Optional[str] = None
    department: Optional[str] = None
    phone_number: Optional[str] = None
    # Data de qualificação como CTA (AAAA-MM-DD) — assinala a jóia (Art. 6).
    cta_qualified_since: Optional[str] = None

    @field_validator("cta_qualified_since", mode="before")
    @classmethod
    def _v_cta(cls, v):
        return _validate_date_str(v, allow_future=False, label="Data de qualificação CTA")


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
    # Data de qualificação como CTA (AAAA-MM-DD) — assinala a jóia (Art. 6) na
    # admissão. Se None, mantém o valor já no documento (ou fica por decidir).
    cta_qualified_since: Optional[str] = None

    @field_validator("cta_qualified_since", mode="before")
    @classmethod
    def _v_cta(cls, v):
        return _validate_date_str(v, allow_future=False, label="Data de qualificação CTA")


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


class HonorarioLigar(BaseModel):
    # Reconciliação manual com Assembleia (spec-voz §2.4, F6): a Mesa liga uma
    # nomeação apurada à deliberação da AG que a ratificou. Referência, não recria.
    assembleia_id: str = Field(min_length=1)
    deliberacao_id: Optional[str] = None


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
    due_date: str
    status: str = "pendente"
    source: str = "folha_salarial"
    payroll_reference: Optional[str] = None
    confirmed_by_admin: bool = False
    confirmed_at: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InvoiceCreate(BaseModel):
    user_id: str
    type: str
    amount: float
    due_date: str
    source: str = "folha_salarial"
    payroll_reference: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("due_date", mode="before")
    @classmethod
    def _v_due_date(cls, v):
        return _validate_datetime_str(v, label="Data de vencimento")


# ===== POLL MODELS =====


class Poll(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    options: List[dict]
    start_date: str
    end_date: str
    status: str = "rascunho"
    result_visibility: str = "socios"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PollCreate(BaseModel):
    title: str
    description: str
    options: List[dict]
    start_date: str
    end_date: str
    result_visibility: str = "socios"

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def _v_dates(cls, v):
        return _validate_datetime_str(v)


class UserVote(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    poll_id: str
    vote_option: int
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


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
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
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
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


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
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


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
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


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
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


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
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


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
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


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
    date: str
    end_date: Optional[str] = None
    location: str
    visibility: str = "socios"
    max_attendees: Optional[int] = None
    attendees: List[str] = []
    created_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EventCreate(BaseModel):
    title: str
    description: str
    type: str
    date: str
    end_date: Optional[str] = None
    location: str
    visibility: str = "socios"
    max_attendees: Optional[int] = None

    @field_validator("date", "end_date", mode="before")
    @classmethod
    def _v_dates(cls, v):
        return _validate_datetime_str(v)


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    visibility: Optional[str] = None
    max_attendees: Optional[int] = None

    @field_validator("date", "end_date", mode="before")
    @classmethod
    def _v_dates(cls, v):
        return _validate_datetime_str(v)


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
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    # Tamper-evidence (spec-verificacao-seguranca-saas §8.1, F4): HMAC-SHA256 do
    # conteúdo imutável da entrada, com chave derivada do SECRET_KEY (que vive no
    # env da app, nunca na BD). Quem tem escrita na BD mas não o SECRET_KEY não
    # consegue FORJAR um hash válido → uma alteração que deixe o hash antigo é
    # apanhada. (Pode REMOVER o hash → a entrada fica "não verificável", o que o
    # endpoint /verify reflete; a resistência completa a remoção/apagamento fica
    # no role da BD — revogar UPDATE/DELETE, F5.) Aditivo/opcional: docs legados
    # (pré-F4) não o têm.
    entry_hash: Optional[str] = None


class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str
    title: str
    message: str
    link: Optional[str] = None
    read: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class NotificationCreate(BaseModel):
    user_id: str
    type: str
    title: str
    message: str
    link: Optional[str] = None


# ===== COMUNICADOS (spec-comunicados-email) =====

COMUNICADO_TIPOS = ["oficial", "informativo"]
COMUNICADO_CHANNELS = ["in_app", "email"]
COMUNICADO_SEGMENT_KINDS = ["all_active", "role", "orgao", "member_category", "manual"]
COMUNICADO_STATUSES = ["a_enviar", "enviando", "enviado", "parcial", "falhado"]


class ComunicadoSegment(BaseModel):
    kind: Literal["all_active", "role", "orgao", "member_category", "manual"]
    value: Optional[str] = None
    user_ids: Optional[List[str]] = None


def _dedupe_nonempty_channels(v):
    if not v:
        raise ValueError("Selecione pelo menos um canal")
    return list(dict.fromkeys(v))  # dedupe preservando ordem


class ComunicadoCreate(BaseModel):
    subject: str
    body: str
    tipo: Literal["oficial", "informativo"] = "informativo"
    channels: List[Literal["in_app", "email"]]
    segment: ComunicadoSegment
    notification_type: str = "comunicado"
    cta_label: Optional[str] = None
    cta_url: Optional[str] = None

    @field_validator("subject")
    @classmethod
    def _v_subject(cls, v):
        v = (v or "").strip()
        if not v:
            raise ValueError("Assunto obrigatório")
        if len(v) > 200:
            raise ValueError("Assunto demasiado longo (máx. 200)")
        return v

    @field_validator("body")
    @classmethod
    def _v_body(cls, v):
        v = (v or "").strip()
        if len(v) < 10:
            raise ValueError("Corpo demasiado curto")
        return v

    @field_validator("channels")
    @classmethod
    def _v_channels(cls, v):
        return _dedupe_nonempty_channels(v)

    @field_validator("cta_url")
    @classmethod
    def _v_cta_url(cls, v):
        if v is None:
            return v
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL do CTA deve começar por http:// ou https://")
        return v

    @model_validator(mode="after")
    def _v_segment(self):
        seg = self.segment
        if seg.kind in ("role", "orgao", "member_category") and not seg.value:
            raise ValueError("Este segmento requer 'value'")
        if seg.kind == "manual" and not seg.user_ids:
            raise ValueError("Selecione pelo menos um sócio")
        return self


class RecipientsCountRequest(BaseModel):
    tipo: Literal["oficial", "informativo"] = "informativo"
    channels: List[Literal["in_app", "email"]]
    segment: ComunicadoSegment

    @field_validator("channels")
    @classmethod
    def _v_channels(cls, v):
        return _dedupe_nonempty_channels(v)


class EmailPreferencesUpdate(BaseModel):
    email_opt_out_informativos: bool


# ===== FINANCE MODELS =====

TRANSACTION_TYPES = ["receita", "despesa"]

# Categorias de receita estatutárias (Art. 5; spec-controlos-financeiros §5.1).
INCOME_CATEGORIES = [
    "quotas",
    "joias",
    "subvencoes",
    "donativos",
    "venda_publicacoes",
    "juros",
    "extraordinarias",
]

EXPENSE_CATEGORIES = ["operacional", "eventos", "juridico", "comunicacao", "viagens", "outros_despesa"]

# Labels para o endpoint meta (frontend) — PT com acentos. O CSV/DRE-PDF usa um
# conjunto ASCII-safe próprio em routes/finances.py (CATEGORY_LABELS).
INCOME_CATEGORY_LABELS = {
    "quotas": "Quotas",
    "joias": "Jóias",
    "subvencoes": "Subvenções",
    "donativos": "Donativos",
    "venda_publicacoes": "Venda de Publicações",
    "juros": "Juros",
    "extraordinarias": "Receitas Extraordinárias",
}
EXPENSE_CATEGORY_LABELS = {
    "operacional": "Operacional",
    "eventos": "Eventos",
    "juridico": "Jurídico",
    "comunicacao": "Comunicação",
    "viagens": "Viagens",
    "outros_despesa": "Outras Despesas",
}

# Mapa de alias legado → key estatutária (decisões do dono, 2026-05-21:
# patrocinios → extraordinarias). Aplica-se SÓ a receitas — a categoria de
# DESPESA "eventos" mantém-se válida e não é renomeada. Fonte única partilhada
# pelo script scripts/migrate_income_categories.py e pelos testes.
LEGACY_INCOME_ALIASES = {
    "patrocinios": "extraordinarias",
    "doacoes": "donativos",
    "eventos": "extraordinarias",
    "outros_receita": "extraordinarias",
}


def canonical_income_category(category: str) -> str:
    """Mapeia um alias legado de receita para a key estatutária; já-canónica
    fica inalterada (idempotente). Semântica income-only: chamar apenas para
    transacções type=="receita" (ver migrate_income_categories.py)."""
    return LEGACY_INCOME_ALIASES.get(category, category)


class Transaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # "receita" or "despesa"
    category: str
    description: str
    amount: float
    date: str
    reference: Optional[str] = None
    user_id: Optional[str] = None
    created_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    # Controlos financeiros estatutários — aditivos/opcionais (não quebram docs):
    # - ato_id: liga a despesa a um Ato de co-aprovação (spec-controlos §4.1).
    # - proof_url: comprovativo de despesa anexado pelo Tesoureiro (spec-ciclo §5.2).
    # - conferido: marca de conferência do Conselho Fiscal por transacção (§5.2).
    ato_id: Optional[str] = None
    proof_url: Optional[str] = None
    conferido: Optional[bool] = None


class TransactionCreate(BaseModel):
    type: str
    category: str
    description: str
    amount: float
    date: str
    reference: Optional[str] = None
    user_id: Optional[str] = None

    @field_validator("date", mode="before")
    @classmethod
    def _v_date(cls, v):
        return _validate_datetime_str(v)


class TransactionUpdate(BaseModel):
    type: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[str] = None
    reference: Optional[str] = None
    # comprovativo de despesa anexado pelo Tesoureiro (spec-ciclo §5.3) — o CF
    # confere a partir daqui. Aditivo/opcional.
    proof_url: Optional[str] = None

    @field_validator("date", mode="before")
    @classmethod
    def _v_date(cls, v):
        return _validate_datetime_str(v)


class FinanceSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "finance_settings"
    quota_amount: float = 2000.0
    quota_description: str = "Quota Mensal"
    # Jóia de admissão (spec-governanca §14): default = 2x quota, salvo
    # deliberação em contrário. joia_amount resolvido pelo backend.
    joia_multiplier: float = 2.0
    joia_amount: Optional[float] = None
    # Pagamentos acima deste limiar exigem um Ato de co-aprovação aprovado
    # (spec-controlos §4.1, Art. 54). 0.0 = regra ainda não activada.
    coaprovacao_limiar: float = 0.0
    # Alterar quota/jóia exige deliberação de AG por maioria 3/4.
    quota_fixed_by_assembleia_id: Optional[str] = None
    quota_fixed_by_deliberacao_id: Optional[str] = None
    effective_from: Optional[str] = None
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
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


# ===== ATOS — Co-aprovação / dupla assinatura (Art. 54; spec-controlos §4.1) =====
# Actos que vinculam a ACCTA exigem 2 da Direcção (um deles o Presidente); os
# pagamentos exigem também o Tesoureiro. A regra (requisitos + apuramento de
# estado) vive em `atos_rules.py` (puro, testável sem DB) — fonte única.
ATO_TIPOS = ["vinculativo", "pagamento"]
ATO_STATUSES = ["pendente", "aprovado", "rejeitado", "executado", "cancelado"]
ATO_DECISOES = ["aprovado", "rejeitado"]


class AtoCreate(BaseModel):
    tipo: str
    descricao: str
    valor: Optional[float] = None
    beneficiario: Optional[str] = None


class AtoSign(BaseModel):
    decisao: str


class AtoExecute(BaseModel):
    # Categoria/data/referência da despesa criada ao executar um pagamento.
    # `category` default resolvido na rota ("operacional") se omisso.
    category: Optional[str] = None
    date: Optional[str] = None
    reference: Optional[str] = None

    @field_validator("date", mode="before")
    @classmethod
    def _v_date(cls, v):
        return _validate_datetime_str(v)


class Ato(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tipo: str
    descricao: str
    valor: Optional[float] = None
    beneficiario: Optional[str] = None
    # Snapshot dos requisitos no momento da criação (congela a regra estatutária).
    requisitos: dict
    # {user_id, cargo (key canónica), decisao: "aprovado"|"rejeitado", signed_at}
    assinaturas: List[dict] = Field(default_factory=list)
    status: str = "pendente"
    transaction_id: Optional[str] = None  # despesa criada ao executar (pagamento)
    created_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_article: str = "54"


# Estados válidos de conta. NÃO existe "inadimplente" (quotas são descontadas
# em folha) — invariante de negócio do projeto.
# - pendente_aprovacao / rejeitado: fluxo de auto-registo (spec-auto-registo).
#   `rejeitado` mantém o documento (auditoria + evita re-registo trivial).
USER_STATUSES = ["ativo", "inativo", "pendente_convite", "pendente_aprovacao", "rejeitado"]


# ===== PROJECT MODELS =====

PROJECT_STATUSES = ["proposta", "aprovado", "em_curso", "concluido", "cancelado"]
PROJECT_VISIBILITIES = ["publico", "privado"]
# Cat 5 F1 (spec-fins-profissionais §4): distingue projetos comuns de
# grupos de trabalho/comissões (Art. 31.e). `tipo` é aditivo e imutável após
# criação — não migra dados antigos (default "projeto").
PROJECT_TIPOS = ["projeto", "grupo_trabalho", "comissao"]
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
    tipo: Literal["projeto", "grupo_trabalho", "comissao"] = "projeto"
    created_by: str = ""
    created_by_name: str = ""
    responsible_id: Optional[str] = None
    responsible_name: Optional[str] = None
    budget: float = 0.0
    spent: float = 0.0
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    progress: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ProjectCreate(BaseModel):
    title: str
    description: str = ""
    visibility: str = "publico"
    category: str = ""
    tipo: Literal["projeto", "grupo_trabalho", "comissao"] = "projeto"
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
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


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
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ProjectExpense(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    description: str
    amount: float
    date: str
    created_by: str
    created_by_name: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ProjectMilestone(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    title: str
    date: str
    completed: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


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
MAIORIA_TIPOS = ["absoluta", "qualificada_2_3", "qualificada_3_4_presentes", "qualificada_3_4_universo"]
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
    # --- Camada "ao vivo" (spec-sessao-assembleia-ao-vivo §2.1; aditivo) ---
    modo: Literal["presencial", "online", "hibrido"] = "online"  # online é o default
    meeting_link: Optional[str] = None  # URL externa da videochamada (link out, sem iframe)
    meeting_provider: Optional[str] = None  # meet | zoom | teams | outro
    meeting_notes: Optional[str] = None  # instruções / dial-in
    # Estado fino enquanto status == "em_curso"; transições só pela Mesa.
    session_phase: Literal["fechada", "checkin", "antes_ot", "ordem_trabalhos", "encerramento"] = "fechada"
    current_item_id: Optional[str] = None  # ponto da ordem de trabalhos em curso
    check_in_code: Optional[str] = None  # código curto rotativo p/ self check-in
    check_in_code_expires_at: Optional[str] = None  # ISO 8601
    session_version: int = 0  # bump a cada mutação de sessão → base do SSE
    antes_ot_aberto_em: Optional[str] = None  # p/ limite soft de 30 min (Art. 14)
    # Lista de document_ids anexados à sessão (Art. 20). Escrita via $push com
    # guarda de duplicados em POST .../documentos. Declarado para o campo sair no
    # model_dump() e sobreviver a qualquer reconstrução por `Assembleia(**doc)`.
    documentos: List[str] = Field(default_factory=list)
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
    # Config da sessão ao vivo (opcional na convocação; editável depois).
    modo: Literal["presencial", "online", "hibrido"] = "online"
    meeting_link: Optional[str] = Field(default=None, max_length=500)
    meeting_provider: Optional[str] = None  # meet | zoom | teams | outro
    meeting_notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("meeting_link")
    @classmethod
    def _v_meeting_link(cls, v):
        # Só http(s): impede esquemas perigosos (javascript:, data:) no botão
        # "Entrar na reunião" que abre esta URL (link out).
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("meeting_link deve começar por http:// ou https://")
        return v


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
    # --- Camada "ao vivo" (spec-sessao-assembleia §3.1; aditivo) ---
    method: Literal["join_click", "qr_meeting", "qr_scan", "self_code", "mesa_manual"] = "mesa_manual"
    can_vote: bool = True  # is_voting_member no momento do check-in
    checked_in_at: Optional[str] = None  # ISO 8601
    source_article: str = "21"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AssembleiaPresencaCreate(BaseModel):
    user_id: str
    representados: List[str] = Field(default_factory=list, max_length=MAX_REPRESENTADOS)
    documento_id: Optional[str] = None


class AssembleiaCheckinRequest(BaseModel):
    """Self check-in do próprio membro (online). Representação NÃO entra aqui —
    é registada pela Mesa em `POST /presencas` (decisão D9)."""

    method: Literal["join_click", "qr_meeting", "self_code"] = "join_click"
    code: Optional[str] = None  # código de sessão (reforço anti-proxy opcional — D1)


class AssembleiaCheckinScan(BaseModel):
    """A Mesa lê o QR pessoal da carteira de um sócio (presencial)."""

    qr_hash: str = Field(min_length=8, max_length=200)


class AssembleiaDeliberacao(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assembleia_id: str
    ponto: str  # ponto da ordem de trabalhos
    descricao: str
    tipo_maioria: Literal["absoluta", "qualificada_2_3", "qualificada_3_4_presentes", "qualificada_3_4_universo"]
    # Contagens/apuramento: opcionais para suportar o ciclo ao vivo (abre sem
    # votos; preenchidos no apuramento). O caminho one-shot passa-os explícitos.
    base_calculo: int = Field(default=0, ge=0)
    votos_favor: int = Field(default=0, ge=0)
    votos_contra: int = Field(default=0, ge=0)
    abstencoes: int = Field(default=0, ge=0)
    threshold: int = Field(default=0, ge=0)
    aprovado: bool = False
    source_article: Optional[str] = None
    registado_por: str
    # --- Camada "ao vivo" (spec-sessao-assembleia §7; aditivo) ---
    voting_mode: Literal["braco_no_ar", "nominal", "secreto"] = "braco_no_ar"
    item_id: Optional[str] = None  # ponto da OT
    subitem: Optional[str] = None  # voto separado: vários assuntos no mesmo ponto
    conflitos_excluidos: List[str] = []  # user_ids sem direito a voto neste ponto (Art. 32)
    # one-shot nasce já "encerrada" (final); o ciclo ao vivo abre em "aberta".
    status: Literal["aberta", "encerrada", "anulada"] = "encerrada"
    apurado_em: Optional[str] = None  # ISO 8601 — quando a Mesa fechou o voto
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AssembleiaDeliberacaoCreate(BaseModel):
    ponto: str = Field(min_length=1, max_length=200)
    descricao: str = Field(min_length=1, max_length=2000)
    tipo_maioria: Literal["absoluta", "qualificada_2_3", "qualificada_3_4_presentes", "qualificada_3_4_universo"]
    votos_favor: int = Field(ge=0)
    votos_contra: int = Field(ge=0)
    abstencoes: int = Field(ge=0)
    source_article: Optional[str] = Field(default=None, max_length=50)


class AssembleiaDeliberacaoAbrir(BaseModel):
    """Abre uma deliberação para votação ao vivo (spec-sessao-assembleia §7).
    A Mesa escolhe o modo; as contagens vêm depois (votos individuais ou o
    agregado do braço no ar) e o apuramento fecha-a."""

    ponto: str = Field(min_length=1, max_length=200)
    descricao: str = Field(min_length=1, max_length=2000)
    tipo_maioria: Literal["absoluta", "qualificada_2_3", "qualificada_3_4_presentes", "qualificada_3_4_universo"] = (
        "absoluta"
    )
    voting_mode: Literal["braco_no_ar", "nominal", "secreto"] = "braco_no_ar"
    item_id: Optional[str] = None
    subitem: Optional[str] = Field(default=None, max_length=200)
    conflitos_excluidos: List[str] = Field(default_factory=list)
    source_article: Optional[str] = Field(default=None, max_length=50)


class AssembleiaVotoCast(BaseModel):
    """Voto individual (nominal ou secreto) numa deliberação aberta."""

    escolha: Literal["favor", "contra", "abstencao"]


class AssembleiaContagem(BaseModel):
    """Contagem agregada do braço no ar — a Mesa conta as mãos na chamada (D5)."""

    votos_favor: int = Field(ge=0)
    votos_contra: int = Field(ge=0)
    abstencoes: int = Field(ge=0)


class AssembleiaVoto(BaseModel):
    """Voto NOMINAL — registado por nome (spec §7.1). Único por
    (deliberacao_id, user_id); apurado com o peso de voto da presença."""

    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deliberacao_id: str
    assembleia_id: str
    user_id: str
    escolha: Literal["favor", "contra", "abstencao"]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Voto SECRETO: par recibo/boletim, gravado numa transação (database.cast_assembleia_ballot),
# igual ao desenho das eleições. O boletim NUNCA liga ao eleitor (spec §7.1, §9).
class AssembleiaVotoBallot(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deliberacao_id: str
    escolha: Literal["favor", "contra", "abstencao"]  # sem user_id / voter_hash
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AssembleiaVotoReceipt(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deliberacao_id: str
    voter_hash: str  # HMAC(secret, f"{deliberacao_id}:{user_id}") — prova de voto, não o sentido
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ===== F4 — Moções, requerimentos e recomendações em sessão (spec §5; Art. 6, 26) =====


class MocaoSessao(BaseModel):
    """Submissão durante a reunião. Requerimento (Art. 6, 26) vai a voto imediato
    sem discussão; moções/recomendações podem entrar em discussão antes do voto."""

    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assembleia_id: str
    item_id: Optional[str] = None
    tipo: Literal["mocao", "requerimento", "recomendacao"]
    titulo: str
    texto: str
    proposta_por: str  # user_id do membro presente
    status: Literal["submetida", "em_discussao", "em_votacao", "aprovada", "rejeitada", "retirada"] = "submetida"
    votacao_imediata: bool = False  # True p/ requerimento (salta discussão)
    deliberacao_id: Optional[str] = None  # preenchido quando a Mesa coloca a voto
    source_article: str = "26"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MocaoCreate(BaseModel):
    tipo: Literal["mocao", "requerimento", "recomendacao"] = "mocao"
    titulo: str = Field(min_length=3, max_length=200)
    texto: str = Field(min_length=1, max_length=4000)
    item_id: Optional[str] = None


class MocaoColocarVoto(BaseModel):
    """A Mesa coloca uma moção a voto — cria uma `AssembleiaDeliberacao` (F3)."""

    tipo_maioria: Literal["absoluta", "qualificada_2_3", "qualificada_3_4_presentes", "qualificada_3_4_universo"] = (
        "absoluta"
    )
    voting_mode: Literal["braco_no_ar", "nominal", "secreto"] = "braco_no_ar"
    subitem: Optional[str] = Field(default=None, max_length=200)
    conflitos_excluidos: List[str] = Field(default_factory=list)


# ===== F5 — Período "antes da ordem de trabalhos" (spec §6; Art. 14) =====


class ExpedienteEntry(BaseModel):
    """Correspondência ou votos de louvor/congratulação/pesar registados pela
    Mesa no período `antes_ot` (limite soft de 30 min — D4)."""

    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assembleia_id: str
    tipo: Literal["correspondencia", "voto_louvor", "voto_congratulacao", "voto_pesar"]
    texto: str
    registado_por: str
    aprovado_por_aclamacao: Optional[bool] = None  # só para votos de louvor/congratulação/pesar
    source_article: str = "14"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ExpedienteCreate(BaseModel):
    tipo: Literal["correspondencia", "voto_louvor", "voto_congratulacao", "voto_pesar"]
    texto: str = Field(min_length=1, max_length=4000)
    aprovado_por_aclamacao: Optional[bool] = None


# ===== F6 — Documentos da sessão + convidados (spec §8; Art. 20, 36) =====


class AssembleiaDocumentoAttach(BaseModel):
    """A Mesa anexa um documento já existente em `documents` à assembleia."""

    document_id: str = Field(min_length=8, max_length=200)


class Convidado(BaseModel):
    """Não-membro autorizado a assistir/intervir (Art. 36). NÃO conta p/ quórum
    nem vota. Se `can_speak`, a Mesa pode pô-lo na fila de palavra (F2)."""

    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assembleia_id: str
    nome: str
    email: Optional[str] = None
    can_speak: bool = False
    motivo: Optional[str] = None
    invited_by: str  # user_id da Mesa
    checked_in: bool = False
    source_article: str = "36"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ConvidadoCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=200)
    email: Optional[str] = Field(default=None, max_length=200)
    can_speak: bool = False
    motivo: Optional[str] = Field(default=None, max_length=500)


class PalavraConvidadoCreate(BaseModel):
    """A Mesa põe um convidado `can_speak` na fila de palavra (F2)."""

    convidado_id: str
    tipo: Literal["intervencao", "protesto", "esclarecimento", "defesa_honra"] = "intervencao"


class AssembleiaFaseUpdate(BaseModel):
    """Transição da fase fina da sessão ao vivo (spec-sessao-assembleia §2.1)."""

    session_phase: Literal["fechada", "checkin", "antes_ot", "ordem_trabalhos", "encerramento"]
    current_item_id: Optional[str] = None  # ponto da OT em curso (opcional)


# Durações default da palavra por tipo, em segundos (spec §4.1; confirmar com o
# Regimento — decisão D3).
PALAVRA_DURACOES = {
    "intervencao": 180,
    "protesto": 60,
    "esclarecimento": 120,
    "defesa_honra": 120,
}


class PalavraRequest(BaseModel):
    """Inscrição para uso da palavra (spec-sessao-assembleia §4.1).

    Para membros, `user_id` está preenchido e `convidado_id=None`. Para convidados
    autorizados a intervir (F6), `convidado_id` está preenchido e `user_id=None`
    (inserido pela Mesa)."""

    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assembleia_id: str
    item_id: Optional[str] = None  # ponto da ordem de trabalhos
    user_id: Optional[str] = None  # membro presente; None se for convidado
    convidado_id: Optional[str] = None  # F6 — convidado autorizado pela Mesa
    tipo: Literal["intervencao", "protesto", "esclarecimento", "defesa_honra"]
    status: Literal["inscrito", "a_falar", "concluido", "retirado", "negado"] = "inscrito"
    ordem: Optional[int] = None  # posição atribuída pela Mesa
    duration_limit_s: int = Field(ge=5, le=3600)  # default por tipo (PALAVRA_DURACOES)
    requested_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    ends_at: Optional[str] = None  # started_at + duration_limit_s
    ended_at: Optional[str] = None
    source_article: str = "27"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @model_validator(mode="after")
    def _v_user_xor_convidado(self):
        # Exactamente um dos dois identifica o orador (membro vs convidado F6).
        has_user = bool(self.user_id)
        has_conv = bool(self.convidado_id)
        if has_user == has_conv:
            raise ValueError("PalavraRequest exige exactamente um de `user_id` ou `convidado_id`.")
        return self


class PalavraCreate(BaseModel):
    tipo: Literal["intervencao", "protesto", "esclarecimento", "defesa_honra"] = "intervencao"
    item_id: Optional[str] = None


class PalavraOrdenar(BaseModel):
    ordem: int = Field(ge=0)


class PalavraIniciar(BaseModel):
    duration_s: Optional[int] = Field(default=None, ge=5, le=3600)  # override opcional da Mesa


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
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
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
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_by: Optional[str] = None


class BrandSettingsUpdate(BaseModel):
    logo_light_url: Optional[str] = None  # "" = repor default; None = manter
    logo_dark_url: Optional[str] = None
    alt: Optional[str] = Field(default=None, max_length=200)


# ===== REGULAMENTOS INTERNOS VERSIONADOS (spec-ciclo §6, Art. 31.j/56) =====
# Repositório versionado: cada `Regulamento` tem N `RegulamentoVersao` (1,2,3…);
# aprovar uma versão torna-a `current_version_id` e revoga a anterior (histórico
# preservado). Competência "assembleia_geral" (ex.: Regimento da AG) exige uma
# deliberação da AG para aprovar; "direcao" aprova internamente (Art. 31.j).

REGULAMENTO_COMPETENCIAS = ["direcao", "assembleia_geral"]
REGULAMENTO_VERSAO_STATUSES = ["rascunho", "em_aprovacao", "aprovado", "revogado"]


class Regulamento(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slug: str
    titulo: str
    descricao: Optional[str] = None
    competencia_aprovacao: Literal["direcao", "assembleia_geral"] = "direcao"
    current_version_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_article: str = "56"


class RegulamentoVersao(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    regulamento_id: str
    versao: int
    document_id: str
    status: Literal["rascunho", "em_aprovacao", "aprovado", "revogado"] = "rascunho"
    changelog: Optional[str] = None
    created_by: str
    approved_by: Optional[str] = None
    assembleia_id: Optional[str] = None  # se competência = AG
    deliberacao_id: Optional[str] = None
    effective_from: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RegulamentoCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=80)
    titulo: str = Field(min_length=2, max_length=200)
    descricao: Optional[str] = Field(default=None, max_length=2000)
    competencia_aprovacao: Literal["direcao", "assembleia_geral"] = "direcao"

    @field_validator("slug")
    @classmethod
    def _v_slug(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", v):
            raise ValueError("slug deve ser kebab-case (a-z, 0-9, hifens)")
        return v


class RegulamentoVersaoCreate(BaseModel):
    document_id: str
    changelog: Optional[str] = Field(default=None, max_length=2000)


class RegulamentoVersaoAprovar(BaseModel):
    # obrigatórios apenas se competência = assembleia_geral (validado na rota)
    assembleia_id: Optional[str] = None
    deliberacao_id: Optional[str] = None
    effective_from: Optional[str] = None  # default: agora, definido na rota


class RegulamentoVersaoRevogar(BaseModel):
    motivo: Optional[str] = Field(default=None, max_length=1000)


# ===== BALANCETES E BALANÇO ANUAL (spec-ciclo §5, Art. 34/37) =====
# O Tesoureiro publica um balancete congelando o snapshot de /finances/summary
# no momento (auditabilidade — os números não mudam depois). O Conselho Fiscal
# audita ao nível do período (cf_audit: conferido + observações; decisão §12.3).

BALANCETE_TIPOS = ["periodico", "balanco_anual"]
BALANCETE_VISIBILITIES = ["socios", "publico", "direcao"]


class Balancete(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tipo: Literal["periodico", "balanco_anual"] = "periodico"
    periodo: str  # rótulo: "2026-03" | "2026-Q1" | "2026"
    exercicio_ano: int
    snapshot: dict  # congelado de /finances/summary (totais + por categoria)
    document_id: Optional[str] = None  # PDF opcional
    published: bool = False
    published_by: Optional[str] = None  # Tesoureiro
    published_at: Optional[str] = None
    # {audited_by, audited_at, conferido: bool, observacoes}
    cf_audit: Optional[dict] = None
    visibility: Literal["socios", "publico", "direcao"] = "socios"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_article: str = "34"


class BalanceteCreate(BaseModel):
    tipo: Literal["periodico", "balanco_anual"] = "periodico"
    periodo: str = Field(min_length=4, max_length=12)
    exercicio_ano: int = Field(ge=2000, le=2100)
    # Janela do snapshot. Sem month/datas → ano inteiro (balanço anual). month →
    # mensal. date_inicio/date_fim → trimestral ou janela custom.
    month: Optional[int] = Field(default=None, ge=1, le=12)
    date_inicio: Optional[str] = None
    date_fim: Optional[str] = None
    document_id: Optional[str] = None
    visibility: Literal["socios", "publico", "direcao"] = "socios"

    @field_validator("date_inicio", "date_fim", mode="before")
    @classmethod
    def _v_dt(cls, v):
        return _validate_datetime_str(v) if v else v


class BalanceteAuditar(BaseModel):
    conferido: bool
    observacoes: Optional[str] = Field(default=None, max_length=2000)


# ===== EXERCÍCIO / CICLO DE PRESTAÇÃO DE CONTAS (spec-ciclo §4, Art. 19.1/31.k/37) =====
# Máquina de estados que guia o ciclo anual: a Direcção submete Relatório e
# Contas (+ Orçamento e Plano do ano seguinte, em DADOS ESTRUTURADOS — decisão
# §12.8), o CF emite Parecer, a Mesa liga à AG ordinária e a deliberação aprova.
#   aberto → relatorio_submetido → parecer_emitido → em_aprovacao_ag → aprovado
#                                                                    ↘ rejeitado → reaberto

EXERCICIO_STATUSES = [
    "aberto",
    "relatorio_submetido",
    "parecer_emitido",
    "em_aprovacao_ag",
    "aprovado",
    "rejeitado",
    "reaberto",
]
PARECER_SENTIDOS = ["favoravel", "favoravel_com_reservas", "desfavoravel"]
PLANO_ATIVIDADE_ESTADOS = ["planeada", "em_curso", "concluida"]


class OrcamentoLinha(BaseModel):
    categoria: str
    tipo: Literal["receita", "despesa"]
    valor_previsto: float = Field(ge=0)
    nota: Optional[str] = Field(default=None, max_length=500)


class PlanoAtividade(BaseModel):
    titulo: str = Field(min_length=2, max_length=200)
    descricao: Optional[str] = Field(default=None, max_length=2000)
    trimestre: Optional[int] = Field(default=None, ge=1, le=4)
    responsavel: Optional[str] = Field(default=None, max_length=200)
    estado: Literal["planeada", "em_curso", "concluida"] = "planeada"


class Exercicio(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ano: int  # exercício económico
    status: Literal[
        "aberto",
        "relatorio_submetido",
        "parecer_emitido",
        "em_aprovacao_ag",
        "aprovado",
        "rejeitado",
        "reaberto",
    ] = "aberto"
    relatorio_contas: Optional[dict] = None  # {document_id, dre_snapshot, submitted_by, submitted_at}
    orcamento: Optional[dict] = None  # {linhas[], document_id?, ano_orcamento, submitted_by, submitted_at}
    plano_atividades: Optional[dict] = None  # {atividades[], document_id?, submitted_by, submitted_at}
    parecer_cf: Optional[dict] = None  # ver ParecerCF
    assembleia_id: Optional[str] = None  # AG ordinária do 1.º trimestre
    deliberacao_id: Optional[str] = None  # deliberação que aprova
    aprovado_em: Optional[str] = None
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_article: str = "37"


class ParecerCF(BaseModel):
    document_id: Optional[str] = None
    sentido: Literal["favoravel", "favoravel_com_reservas", "desfavoravel"]
    texto: str
    emitted_by: str  # membro do CF
    emitted_at: str


class ExercicioCreate(BaseModel):
    ano: int = Field(ge=2000, le=2100)


class RelatorioContasSubmit(BaseModel):
    document_id: str


class OrcamentoSubmit(BaseModel):
    linhas: List[OrcamentoLinha] = Field(min_length=1)
    document_id: Optional[str] = None
    ano_orcamento: Optional[int] = Field(default=None, ge=2000, le=2100)  # default = exercicio.ano + 1


class PlanoSubmit(BaseModel):
    atividades: List[PlanoAtividade] = Field(min_length=1)
    document_id: Optional[str] = None


class ParecerSubmit(BaseModel):
    sentido: Literal["favoravel", "favoravel_com_reservas", "desfavoravel"]
    texto: str = Field(min_length=1, max_length=10000)
    document_id: Optional[str] = None


class ExercicioSubmeterAG(BaseModel):
    assembleia_id: str


class ExercicioAprovar(BaseModel):
    deliberacao_id: str
    aprovado: bool = True


# ===== RANKING DE ATUAÇÃO DO SÓCIO (spec-ranking-socio) =====
# A pontuação é DERIVADA de sinais já gravados (não event-sourcing); a fonte
# única do cálculo é `backend/ranking.py` (`compute_member_score`), onde também
# vivem os pesos default (`DEFAULT_WEIGHTS`). Estes modelos NÃO importam de
# `ranking.py` de propósito: `ranking` → `auth` → `models` formaria um ciclo.
# Os defaults de pesos são aplicados em runtime por `ranking.load_settings()`.


class RankingAjuste(BaseModel):
    """Delta manual auditável (o "registar" do que o sistema não infere)."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # membro pontuado
    period_key: str  # "2026" | "all"
    delta: float  # +/-; pode ser negativo
    reason: str  # obrigatório, auditável
    created_by: str  # admin/Direcção que registou
    created_at: str


class RankingAjusteCreate(BaseModel):
    """Body do registo de ajuste manual (F4)."""

    user_id: str
    period_key: str = Field(min_length=1, max_length=16)
    delta: float
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("delta")
    @classmethod
    def _v_delta(cls, v):
        if v == 0:
            raise ValueError("O ajuste não pode ser 0")
        return v


class MemberScore(BaseModel):
    """Cache materializada (derivada/descartável) — uma linha do leaderboard."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    period_key: str
    score: float
    rank: int  # 1 = topo (dentro do período)
    breakdown: dict  # {chave: {"count": int, "points": float}}
    # snapshot de display (evita join no leaderboard)
    member_name: str
    member_id: Optional[str] = None
    cargo: Optional[str] = None
    photo_url: Optional[str] = None
    status: str  # ativo/inativo
    ranking_opt_out: bool = False  # denormalizado p/ filtrar listas públicas (§2.5)
    computed_at: str


class RankingSettings(BaseModel):
    """Doc único de configuração do ranking (editável por admin na F4)."""

    weights: dict = Field(default_factory=dict)  # defaults aplicados por load_settings()
    max_like_points_per_period: int = 50
    visibility: Literal["all_members", "direcao_only"] = "all_members"
    top_n_dashboard: int = Field(default=5, ge=1, le=50)
    enabled: bool = True
    last_rebuild_at: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None


class RankingSettingsUpdate(BaseModel):
    """Body parcial de edição de definições (F4)."""

    weights: Optional[dict] = None
    max_like_points_per_period: Optional[int] = Field(default=None, ge=0)
    visibility: Optional[Literal["all_members", "direcao_only"]] = None
    top_n_dashboard: Optional[int] = Field(default=None, ge=1, le=50)
    enabled: Optional[bool] = None


class RankingOptOut(BaseModel):
    """Body do opt-out do próprio membro (F5, §2.5)."""

    opt_out: bool


# ============================================================================
# Cat 5 F2 — Desenvolvimento técnico-profissional + Publicações
# (spec-fins-profissionais §6/§8)
# ============================================================================

# 5.3 Formações / Certificações / Materiais (Art. 2.c)
FORMACAO_TIPOS = ["formacao", "certificacao", "material"]


class Formacao(BaseModel):
    """Catálogo de formações, certificações e materiais para desenvolvimento
    técnico-profissional dos sócios (spec-fins-profissionais §6.1)."""

    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    titulo: str
    tipo: Literal["formacao", "certificacao", "material"]
    descricao: str = ""
    entidade: Optional[str] = None  # provedor / entidade formadora
    categoria: Optional[str] = None
    url: Optional[str] = None  # inscrição ou recurso externo
    document_id: Optional[str] = None  # material anexo via módulo de documentos
    data: Optional[str] = None  # ISO 8601
    validade: Optional[str] = None  # ISO 8601, certificações
    ativo: bool = True
    created_by: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_article: str = "2.c"


class FormacaoCreate(BaseModel):
    titulo: str = Field(min_length=1)
    tipo: Literal["formacao", "certificacao", "material"]
    descricao: str = ""
    entidade: Optional[str] = None
    categoria: Optional[str] = None
    url: Optional[str] = None
    document_id: Optional[str] = None
    data: Optional[str] = None
    validade: Optional[str] = None
    ativo: bool = True


class FormacaoUpdate(BaseModel):
    titulo: Optional[str] = Field(default=None, min_length=1)
    descricao: Optional[str] = None
    entidade: Optional[str] = None
    categoria: Optional[str] = None
    url: Optional[str] = None
    document_id: Optional[str] = None
    data: Optional[str] = None
    validade: Optional[str] = None
    ativo: Optional[bool] = None
    # tipo é imutável após criação (define indexação e UI); não está aqui.


# 5.5 Publicações formais (Art. 5.c) — distintas de notícias/blog
PUBLICACAO_TIPOS = ["revista", "boletim", "artigo", "relatorio_tecnico"]
PUBLICACAO_VISIBILITIES = ["publico", "socios"]


class Publicacao(BaseModel):
    """Publicações formais da associação — revista, boletim, artigo, relatório
    técnico (spec-fins-profissionais §8.1). Venda fica para F5 (Cat. 4)."""

    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    titulo: str
    descricao: Optional[str] = None
    tipo: Literal["revista", "boletim", "artigo", "relatorio_tecnico"]
    autor: Optional[str] = None
    document_id: str  # PDF/ficheiro principal (obrigatório)
    capa_url: Optional[str] = None
    data_publicacao: str  # ISO 8601
    visibility: Literal["publico", "socios"] = "socios"
    a_venda: bool = False  # FASE 2 (F5)
    preco: Optional[float] = Field(default=None, ge=0)
    created_by: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_article: str = "5.c"


class PublicacaoCreate(BaseModel):
    titulo: str = Field(min_length=1)
    descricao: Optional[str] = None
    tipo: Literal["revista", "boletim", "artigo", "relatorio_tecnico"]
    autor: Optional[str] = None
    document_id: str = Field(min_length=1)
    capa_url: Optional[str] = None
    data_publicacao: str = Field(min_length=1)
    visibility: Literal["publico", "socios"] = "socios"
    a_venda: bool = False
    preco: Optional[float] = Field(default=None, ge=0)


class PublicacaoUpdate(BaseModel):
    titulo: Optional[str] = Field(default=None, min_length=1)
    descricao: Optional[str] = None
    autor: Optional[str] = None
    document_id: Optional[str] = Field(default=None, min_length=1)
    capa_url: Optional[str] = None
    data_publicacao: Optional[str] = None
    visibility: Optional[Literal["publico", "socios"]] = None
    a_venda: Optional[bool] = None
    preco: Optional[float] = Field(default=None, ge=0)
    # tipo é imutável após criação (define listagem/filtros); não está aqui.


# ============================================================================
# Cat 5 F3 — Defesa Profissional + Relações/IFATCA
# (spec-fins-profissionais §5/§7)
# ============================================================================

# 5.2 Defesa Profissional (Art. 2.a)
# Fluxo com aprovação da Direcção (decisão dono 2026-05-29, §14 #3):
#   rascunho -> submetido -> publicado | rascunho (rejeitado) -> arquivado
DEFESA_TIPOS = ["representacao", "tomada_posicao", "comunicado"]
DEFESA_STATUSES = ["rascunho", "submetido", "publicado", "arquivado"]
DEFESA_VISIBILITIES = ["socios", "publico"]


class DefesaProfissional(BaseModel):
    """Registo de representações e tomadas de posição em defesa dos interesses
    profissionais dos controladores (spec-fins-profissionais §5.1)."""

    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    titulo: str
    tipo: Literal["representacao", "tomada_posicao", "comunicado"]
    descricao: str = ""
    entidade_destino: Optional[str] = None
    data: str  # ISO 8601, data do facto/representação
    status: Literal["rascunho", "submetido", "publicado", "arquivado"] = "rascunho"
    document_id: Optional[str] = None
    visibility: Literal["socios", "publico"] = "socios"
    # Workflow de aprovação (segregação criador != aprovador)
    submetido_em: Optional[str] = None
    submetido_por: Optional[str] = None
    aprovado_em: Optional[str] = None
    aprovado_por: Optional[str] = None
    motivo_rejeicao: Optional[str] = None
    arquivado_em: Optional[str] = None
    arquivado_por: Optional[str] = None
    created_by: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_article: str = "2.a"


class DefesaProfissionalCreate(BaseModel):
    titulo: str = Field(min_length=1)
    tipo: Literal["representacao", "tomada_posicao", "comunicado"]
    descricao: str = ""
    entidade_destino: Optional[str] = None
    data: str = Field(min_length=1)
    document_id: Optional[str] = None
    visibility: Literal["socios", "publico"] = "socios"


class DefesaProfissionalUpdate(BaseModel):
    titulo: Optional[str] = Field(default=None, min_length=1)
    descricao: Optional[str] = None
    entidade_destino: Optional[str] = None
    data: Optional[str] = None
    document_id: Optional[str] = None
    visibility: Optional[Literal["socios", "publico"]] = None
    # tipo e status NÃO editáveis aqui — status muda só por endpoints de transição.


class DefesaRejeicao(BaseModel):
    motivo: str = Field(min_length=1)


# 5.4 Cooperação e filiação IFATCA (Art. 2.f, 31.g, 53)
RELACAO_TIPOS = ["federacao_internacional", "associacao_congenere", "parceiro"]
ESTADOS_FILIACAO = ["filiado", "em_negociacao", "nao_filiado", "suspenso"]
RELACAO_VISIBILITIES = ["socios", "publico"]


class RelacaoExterna(BaseModel):
    """Diretório de relações com a IFATCA e associações congéneres, com o
    estado da filiação (spec-fins-profissionais §7.1)."""

    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    tipo: Literal["federacao_internacional", "associacao_congenere", "parceiro"]
    descricao: Optional[str] = None
    website: Optional[str] = None
    contacto: Optional[str] = None
    estado_filiacao: Literal["filiado", "em_negociacao", "nao_filiado", "suspenso"] = "nao_filiado"
    desde: Optional[str] = None  # ISO 8601, data inicial da filiação
    quota_anual: Optional[float] = Field(default=None, ge=0)
    logo_url: Optional[str] = None
    documentos: list[str] = Field(default_factory=list)  # document_ids de acordos
    visibility: Literal["socios", "publico"] = "socios"
    created_by: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_article: str = "2.f"


class RelacaoExternaCreate(BaseModel):
    nome: str = Field(min_length=1)
    tipo: Literal["federacao_internacional", "associacao_congenere", "parceiro"]
    descricao: Optional[str] = None
    website: Optional[str] = None
    contacto: Optional[str] = None
    estado_filiacao: Literal["filiado", "em_negociacao", "nao_filiado", "suspenso"] = "nao_filiado"
    desde: Optional[str] = None
    quota_anual: Optional[float] = Field(default=None, ge=0)
    logo_url: Optional[str] = None
    documentos: list[str] = Field(default_factory=list)
    visibility: Literal["socios", "publico"] = "socios"


class RelacaoExternaUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1)
    descricao: Optional[str] = None
    website: Optional[str] = None
    contacto: Optional[str] = None
    estado_filiacao: Optional[Literal["filiado", "em_negociacao", "nao_filiado", "suspenso"]] = None
    desde: Optional[str] = None
    quota_anual: Optional[float] = Field(default=None, ge=0)
    logo_url: Optional[str] = None
    documentos: Optional[list[str]] = None
    visibility: Optional[Literal["socios", "publico"]] = None
    # tipo é imutável após criação.
