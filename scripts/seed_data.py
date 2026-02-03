import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv

# Load env
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password):
    return pwd_context.hash(password)

def generate_qr_hash(user_id):
    return hashlib.sha256(f"accta-cv-{user_id}-{uuid.uuid4()}".encode()).hexdigest()

async def seed_database():
    print("🌱 Iniciando seed do banco de dados...")
    
    # Limpar coleções existentes
    collections = ['users', 'invoices', 'polls', 'user_votes', 'posts', 'documents', 'benefits', 'wall_posts', 'audit_logs']
    for collection in collections:
        await db[collection].delete_many({})
    print("✅ Coleções limpas")
    
    # ===== USERS =====
    users = []
    
    # Admin
    admin_id = str(uuid.uuid4())
    admin = {
        "id": admin_id,
        "name": "Maria Santos",
        "email": "admin@accta.cv",
        "password": hash_password("admin123"),
        "role": "admin",
        "status": "ativo",
        "member_id": "ACCTA-001",
        "license_number": "ATC-CV-2015-001",
        "admission_date": datetime(2015, 3, 15, tzinfo=timezone.utc).isoformat(),
        "phone_number": "+238 9876543",
        "consent_data": True,
        "qr_code_hash": generate_qr_hash(admin_id),
        "last_login_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    users.append(admin)
    
    # Financeiro
    fin_id = str(uuid.uuid4())
    financeiro = {
        "id": fin_id,
        "name": "João Rodrigues",
        "email": "financeiro@accta.cv",
        "password": hash_password("fin123"),
        "role": "financeiro",
        "status": "ativo",
        "member_id": "ACCTA-002",
        "license_number": "ATC-CV-2016-002",
        "admission_date": datetime(2016, 6, 20, tzinfo=timezone.utc).isoformat(),
        "phone_number": "+238 9876544",
        "consent_data": True,
        "qr_code_hash": generate_qr_hash(fin_id),
        "last_login_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    users.append(financeiro)
    
    # Sócios ativos
    socio_names = [
        "Carlos Mendes", "Ana Silva", "Pedro Fonseca", "Luisa Tavares",
        "José Pereira", "Rita Costa", "António Gomes", "Sofia Martins"
    ]
    
    socio_users = []
    for i, name in enumerate(socio_names):
        socio_id = str(uuid.uuid4())
        socio = {
            "id": socio_id,
            "name": name,
            "email": f"socio{i+1}@accta.cv",
            "password": hash_password("socio123"),
            "role": "socio",
            "status": "ativo",
            "member_id": f"ACCTA-{str(i+3).zfill(3)}",
            "license_number": f"ATC-CV-{2017+i}-{str(i+3).zfill(3)}",
            "admission_date": datetime(2017+i, (i % 12) + 1, 15, tzinfo=timezone.utc).isoformat(),
            "phone_number": f"+238 987654{i+5}",
            "consent_data": True,
            "qr_code_hash": generate_qr_hash(socio_id),
            "last_login_at": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        users.append(socio)
        socio_users.append(socio)
    
    # Sócio inadimplente
    inad_id = str(uuid.uuid4())
    inadimplente = {
        "id": inad_id,
        "name": "Manuel Oliveira",
        "email": "inadimplente@accta.cv",
        "password": hash_password("socio123"),
        "role": "socio",
        "status": "inadimplente",
        "member_id": "ACCTA-011",
        "license_number": "ATC-CV-2018-011",
        "admission_date": datetime(2018, 5, 10, tzinfo=timezone.utc).isoformat(),
        "phone_number": "+238 9876555",
        "consent_data": True,
        "qr_code_hash": generate_qr_hash(inad_id),
        "last_login_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    users.append(inadimplente)
    
    await db.users.insert_many(users)
    print(f"✅ {len(users)} usuários criados")
    
    # ===== INVOICES =====
    invoices = []
    current_year = datetime.now().year
    
    # Criar quotas para todos os sócios
    for user in users:
        if user['role'] == 'socio':
            # Quotas dos últimos 6 meses
            for month in range(6):
                due_date = datetime(current_year, datetime.now().month - month, 10, tzinfo=timezone.utc)
                if due_date.month < 1:
                    due_date = due_date.replace(year=current_year-1, month=12+due_date.month)
                
                # Status pendente para inadimplente, pago para outros
                status = "pendente" if user['status'] == 'inadimplente' and month < 3 else "pago"
                
                invoice = {
                    "id": str(uuid.uuid4()),
                    "user_id": user['id'],
                    "type": "quota",
                    "amount": 500.0,  # 500 CVE
                    "due_date": due_date.isoformat(),
                    "status": status,
                    "source": "folha_salarial",
                    "payroll_reference": f"Folha AAC {due_date.strftime('%B/%Y')}",
                    "confirmed_by_admin": status == "pago",
                    "confirmed_at": due_date.isoformat() if status == "pago" else None,
                    "notes": None,
                    "created_at": (due_date - timedelta(days=15)).isoformat()
                }
                invoices.append(invoice)
    
    await db.invoices.insert_many(invoices)
    print(f"✅ {len(invoices)} invoices criados")
    
    # ===== POLLS =====
    polls = []
    
    # Poll aberta
    open_poll = {
        "id": str(uuid.uuid4()),
        "title": "Proposta de Atualização do Estatuto",
        "description": "Votação para aprovar as alterações propostas no artigo 15 do estatuto da ACCTA, referente aos critérios de admissão de novos sócios.",
        "options": [
            {"id": 1, "label": "Aprovar as alterações"},
            {"id": 2, "label": "Rejeitar as alterações"},
            {"id": 3, "label": "Abstenção"}
        ],
        "start_date": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
        "end_date": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
        "status": "aberta",
        "result_visibility": "socios",
        "created_at": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    }
    polls.append(open_poll)
    
    # Poll fechada
    closed_poll_id = str(uuid.uuid4())
    closed_poll = {
        "id": closed_poll_id,
        "title": "Aprovação do Orçamento Anual 2025",
        "description": "Votação para aprovar o orçamento proposto pela diretoria para o ano de 2025.",
        "options": [
            {"id": 1, "label": "Aprovar"},
            {"id": 2, "label": "Rejeitar"}
        ],
        "start_date": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
        "end_date": (datetime.now(timezone.utc) - timedelta(days=15)).isoformat(),
        "status": "fechada",
        "result_visibility": "publico",
        "created_at": (datetime.now(timezone.utc) - timedelta(days=35)).isoformat()
    }
    polls.append(closed_poll)
    
    await db.polls.insert_many(polls)
    print(f"✅ {len(polls)} votações criadas")
    
    # Votos na poll fechada
    votes = []
    for i, socio in enumerate(socio_users[:6]):
        vote = {
            "id": str(uuid.uuid4()),
            "user_id": socio['id'],
            "poll_id": closed_poll_id,
            "vote_option": 1 if i < 5 else 2,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()
        }
        votes.append(vote)
    
    if votes:
        await db.user_votes.insert_many(votes)
        print(f"✅ {len(votes)} votos criados")
    
    # ===== POSTS =====
    posts = [
        {
            "id": str(uuid.uuid4()),
            "title": "ACCTA Celebra 10 Anos de Excelência",
            "content": "A Associação de Controladores de Tráfego Aéreo de Cabo Verde completa uma década de atuação em defesa dos profissionais e da segurança aérea no arquipélago. Ao longo destes anos, a ACCTA tem sido fundamental na representação dos controladores junto às autoridades nacionais e organizações internacionais.",
            "type": "noticia",
            "visibility": "publico",
            "tags": ["aniversário", "história", "celebração"],
            "created_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Nova Parceria com IFATCA",
            "content": "A ACCTA firma parceria com a Federação Internacional de Associações de Controladores de Tráfego Aéreo (IFATCA) para promover intercâmbio de conhecimento e melhores práticas. Esta colaboração permitirá que os controladores cabo-verdianos tenham acesso a treinamentos internacionais e participem de eventos globais da categoria.",
            "type": "noticia",
            "visibility": "publico",
            "tags": ["internacional", "parceria", "IFATCA"],
            "created_at": (datetime.now(timezone.utc) - timedelta(days=12)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Estatutos Atualizados Disponíveis",
            "content": "Os novos estatutos da ACCTA, aprovados em assembleia geral, já estão disponíveis na área de documentos. Todos os sócios são convidados a consultar as alterações implementadas.",
            "type": "institucional",
            "visibility": "socios",
            "tags": ["estatuto", "documentos"],
            "created_at": (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "O Papel do Controlador na Aviação Moderna",
            "content": "Artigo educativo sobre a evolução da profissão de controlador de tráfego aéreo e sua importância crescente no contexto da aviação global. Aborda tecnologias emergentes, desafios contemporâneos e perspectivas futuras para a profissão em Cabo Verde.",
            "type": "educativo",
            "visibility": "publico",
            "tags": ["educação", "profissão", "tecnologia"],
            "created_at": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        }
    ]
    
    await db.posts.insert_many(posts)
    print(f"✅ {len(posts)} posts/notícias criados")
    
    # ===== DOCUMENTS =====
    documents = [
        {
            "id": str(uuid.uuid4()),
            "title": "Estatuto da ACCTA - Versão 2025",
            "file_url": "https://example.com/documents/estatuto-2025.pdf",
            "type": "estatuto",
            "visibility": "publico",
            "tags": ["estatuto", "legal"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Ata da Assembleia Geral - Janeiro 2025",
            "file_url": "https://example.com/documents/ata-jan-2025.pdf",
            "type": "ata",
            "visibility": "socios",
            "tags": ["assembleia", "2025"],
            "created_at": (datetime.now(timezone.utc) - timedelta(days=15)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Balancete Financeiro - 2024",
            "file_url": "https://example.com/documents/balancete-2024.pdf",
            "type": "balancete",
            "visibility": "socios",
            "tags": ["financeiro", "2024"],
            "created_at": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Regulamento Interno",
            "file_url": "https://example.com/documents/regulamento.pdf",
            "type": "estatuto",
            "visibility": "socios",
            "tags": ["regulamento", "normas"],
            "created_at": (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        }
    ]
    
    await db.documents.insert_many(documents)
    print(f"✅ {len(documents)} documentos criados")
    
    # ===== BENEFITS =====
    benefits = [
        {
            "id": str(uuid.uuid4()),
            "name": "Restaurante Sabores do Mar",
            "description": "Desfrute da melhor gastronomia cabo-verdiana com desconto exclusivo para sócios ACCTA. Localizado em Praia, oferece pratos típicos e ambiente acolhedor.",
            "logo_url": None,
            "discount_percent": 15.0,
            "active": True,
            "validation_count": 23,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Livraria Atlântico",
            "description": "Desconto em livros técnicos, literatura e material de escritório. Parceiro oficial da ACCTA para desenvolvimento profissional.",
            "logo_url": None,
            "discount_percent": 10.0,
            "active": True,
            "validation_count": 45,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Ginásio FitZone",
            "description": "Academia completa com equipamentos modernos e instrutores qualificados. Planos especiais para sócios ACCTA e seus familiares.",
            "logo_url": None,
            "discount_percent": 20.0,
            "active": True,
            "validation_count": 18,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Hotel Praiamar",
            "description": "Hospedagem com vista para o mar e todas as comodidades. Desconto especial em reservas para sócios e convidados.",
            "logo_url": None,
            "discount_percent": 25.0,
            "active": True,
            "validation_count": 12,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.benefits.insert_many(benefits)
    print(f"✅ {len(benefits)} benefícios criados")
    
    # ===== WALL POSTS =====
    wall_posts = [
        {
            "id": str(uuid.uuid4()),
            "user_id": socio_users[0]['id'],
            "user_name": socio_users[0]['name'],
            "content": "Parabéns à toda a equipe pela excelente gestão da associação! É gratificante fazer parte da ACCTA.",
            "approved": True,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": socio_users[1]['id'],
            "user_name": socio_users[1]['name'],
            "content": "Sugiro que possamos organizar um encontro técnico para discutir os novos procedimentos implementados pela AAC.",
            "approved": True,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": socio_users[2]['id'],
            "user_name": socio_users[2]['name'],
            "content": "Os novos benefícios são ótimos! Já utilizei o desconto no Restaurante Sabores do Mar. Recomendo!",
            "approved": True,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
        }
    ]
    
    await db.wall_posts.insert_many(wall_posts)
    print(f"✅ {len(wall_posts)} posts do mural criados")
    
    # ===== AUDIT LOGS =====
    audit_logs = [
        {
            "id": str(uuid.uuid4()),
            "user_id": admin_id,
            "action": "Criou votação: Proposta de Atualização do Estatuto",
            "target_id": open_poll['id'],
            "created_at": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": fin_id,
            "action": "Confirmou pagamento de quota",
            "target_id": invoices[0]['id'] if invoices else None,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": admin_id,
            "action": "Aprovou post do mural",
            "target_id": wall_posts[0]['id'],
            "created_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        }
    ]
    
    await db.audit_logs.insert_many(audit_logs)
    print(f"✅ {len(audit_logs)} logs de auditoria criados")
    
    print("\n🎉 Seed completo!")
    print("\n📝 Credenciais de acesso:")
    print("\nAdmin:")
    print("  Email: admin@accta.cv")
    print("  Senha: admin123")
    print("\nFinanceiro:")
    print("  Email: financeiro@accta.cv")
    print("  Senha: fin123")
    print("\nSócio Ativo:")
    print("  Email: socio1@accta.cv")
    print("  Senha: socio123")
    print("\nSócio Inadimplente:")
    print("  Email: inadimplente@accta.cv")
    print("  Senha: socio123")
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(seed_database())
