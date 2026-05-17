#!/usr/bin/env python3
"""
CLI para criar o primeiro administrador em producao.
Uso: python create_admin.py --email admin@controlador.cv --password <senha> --name "Nome Admin"
"""

import asyncio
import argparse
import uuid
import hashlib
import os
import sys

from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from database import db, ensure_schema, close_pool  # noqa: E402

try:
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
except ImportError:
    import bcrypt

    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def generate_qr_hash(user_id: str) -> str:
    return hashlib.sha256(f"accta-wallet-{user_id}".encode()).hexdigest()


async def create_admin(email: str, password: str, name: str):
    await ensure_schema()

    existing = await db.users.find_one({"email": email})
    if existing:
        print(f"ERRO: Utilizador com email {email} ja existe.")
        print(f"  Nome: {existing.get('name')}")
        print(f"  Role: {existing.get('role')}")
        print(f"  Status: {existing.get('status')}")
        await close_pool()
        sys.exit(1)

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    admin_doc = {
        "id": user_id,
        "name": name,
        "email": email,
        "password": hash_password(password),
        "role": "admin",
        "status": "ativo",
        "cargo": "Administrador",
        "member_id": "ACCTA-ADMIN",
        "license_number": "",
        "department": "Direcao",
        "phone_number": "",
        "admission_date": now,
        "privileges": [
            "manage_users",
            "manage_finances",
            "manage_events",
            "manage_documents",
            "moderate_content",
            "manage_benefits",
            "view_audit_logs",
        ],
        "consent_data": True,
        "qr_code_hash": generate_qr_hash(user_id),
        "last_login_at": None,
        "created_at": now,
        "bio": "",
        "photo_url": "",
    }

    await db.users.insert_one(admin_doc)
    await close_pool()

    print("=" * 50)
    print("  Administrador criado com sucesso!")
    print("=" * 50)
    print(f"  Email:  {email}")
    print(f"  Nome:   {name}")
    print("  Role:   admin")
    print(f"  ID:     {user_id}")
    print("=" * 50)
    print("  Pode agora fazer login no portal.")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Criar administrador inicial do Portal ACCTA"
    )
    parser.add_argument("--email", required=True, help="Email do administrador")
    parser.add_argument(
        "--password", required=True, help="Senha do administrador (min. 6 caracteres)"
    )
    parser.add_argument(
        "--name", default="Administrador ACCTA", help="Nome do administrador"
    )

    args = parser.parse_args()

    if len(args.password) < 6:
        print("ERRO: A senha deve ter pelo menos 6 caracteres")
        sys.exit(1)

    asyncio.run(create_admin(args.email, args.password, args.name))
