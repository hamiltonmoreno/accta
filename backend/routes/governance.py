"""Rotas de governança estatutária (spec-governanca-estatutaria.md).

Fase 0: endpoint de estrutura. As fases seguintes (assembleias, eleições,
disciplina) vivem em módulos dedicados (`routes/assembleias.py`, etc.).
"""

from fastapi import APIRouter, Depends

from auth import get_current_user
from governance import governance_structure
from models import User

router = APIRouter(prefix="/governance", tags=["governance"])


@router.get("/structure")
async def get_governance_structure(current_user: User = Depends(get_current_user)):
    """Estrutura completa de governança: órgãos sociais, catálogo de cargos
    (key + label + órgão + vagas + role/privilégios default), categorias de
    membro, privilégios, roles, duração de mandato e slots eleitorais.

    Fonte única para o frontend (substitui o hard-code e os aliases
    deprecated /users/meta/cargos e /users/meta/privileges)."""
    return governance_structure()
