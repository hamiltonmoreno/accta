#!/usr/bin/env python3
"""
CLI para REPOR a password de uma conta existente (diagnostico + fix de login).

Uso:
    python reset_password.py --email admin@controlador.cv --password <nova-senha>

Diagnostico: corre SEMPRE contra a DATABASE_URL do ambiente onde e executado
(o backend/.env localmente, ou as variaveis do container em producao). Se a conta
NAO existir nesse DB, isso prova que o backend esta apontado a uma base diferente
da esperada (deriva de deploy) — a mensagem deixa-o explicito.

Fix: se a conta existir, atualiza o hash da password usando EXATAMENTE o mesmo
CryptContext de backend/auth.py (bcrypt, rounds=12), pelo que o login passa a
aceitar a nova senha de imediato. So toca em password (+ password_changed_at,
que invalida sessoes/tokens emitidos antes da reposicao, e password_reset_at).

NOTA: nao envia emails, nao altera schema, nao toca noutras contas. Mostra o
estado da conta (status/role/account_type) para confirmar que e a certa.
"""

import asyncio
import argparse
import os
import sys

from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from database import db, ensure_schema, close_pool  # noqa: E402

# Mesmo contexto/parametros que backend/auth.py para garantir hashes compativeis.
from passlib.context import CryptContext  # noqa: E402

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


async def reset_password(email: str, password: str):
    await ensure_schema()

    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        # Diagnostico decisivo: a conta nao existe NO DB que este processo usa.
        host = os.getenv("DATABASE_URL", "")
        host = host.split("@")[-1].split("/")[0] if "@" in host else "(desconhecido)"
        print("=" * 60)
        print(f"  ERRO: nenhuma conta com email {email} neste DB.")
        print(f"  DB em uso (host): {host}")
        print("  => O backend esta apontado a uma base SEM esta conta.")
        print("     Verifique a DATABASE_URL do container de producao,")
        print("     ou use create_admin.py para criar a conta tecnica.")
        print("=" * 60)
        await close_pool()
        sys.exit(2)

    now_iso = datetime.now(timezone.utc).isoformat()
    res = await db.users.update_one(
        {"email": email},
        {
            "$set": {
                "password": hash_password(password),
                # password_changed_at invalida tokens/sessoes emitidos ANTES do
                # reset (auth.token_predates_password_change) — uma reposicao de
                # recuperacao tem de expulsar sessoes/tokens roubados ainda vivos.
                "password_changed_at": now_iso,
                "password_reset_at": now_iso,
            }
        },
    )
    await close_pool()

    print("=" * 60)
    print("  Password reposta com sucesso." if res.modified_count == 1 else
          "  Conta encontrada mas password inalterada (verifique).")
    print("=" * 60)
    print(f"  Email:        {email}")
    print(f"  Nome:         {user.get('name')}")
    print(f"  Role:         {user.get('role')}")
    print(f"  Status:       {user.get('status')}")
    print(f"  account_type: {user.get('account_type', 'member')}")
    print("=" * 60)
    if user.get("status") != "ativo":
        print("  AVISO: status != 'ativo' — o login pode ser recusado a 403")
        print("         mesmo com a password correta. Confirme o status.")
        print("=" * 60)
    print("  Pode agora fazer login com a nova password.")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Repor password de uma conta do Portal ACCTA")
    parser.add_argument("--email", required=True, help="Email da conta")
    parser.add_argument("--password", required=True, help="Nova senha (min. 6 caracteres)")
    args = parser.parse_args()

    if len(args.password) < 6:
        print("ERRO: A senha deve ter pelo menos 6 caracteres")
        sys.exit(1)

    asyncio.run(reset_password(args.email, args.password))
