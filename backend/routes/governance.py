"""Rotas de governança estatutária (spec-governanca-estatutaria.md).

Fase 0: endpoint de estrutura. As fases seguintes (assembleias, eleições,
disciplina) vivem em módulos dedicados (`routes/assembleias.py`, etc.).
Corpos sociais públicos: spec-sobre §3.
"""

from fastapi import APIRouter, Depends

from auth import get_current_user
from database import db
from governance import (
    ASSEMBLEIA_GERAL,
    CARGOS_CATALOG,
    CONSELHO_FISCAL,
    DIRECAO,
    ORGAOS,
    governance_structure,
)
from models import CorposSociaisResponse, User

router = APIRouter(prefix="/governance", tags=["governance"])

# Ordem e rótulos de exibição pública dos órgãos sociais (a Mesa da AG
# apresenta-se como "Mesa da Assembleia Geral").
_PUBLIC_ORGAO_ORDER = [ASSEMBLEIA_GERAL, DIRECAO, CONSELHO_FISCAL]
_ORGAO_DISPLAY = {
    ASSEMBLEIA_GERAL: "Mesa da Assembleia Geral",
    DIRECAO: "Direcção",
    CONSELHO_FISCAL: "Conselho Fiscal",
}
# Sócios reais: account_type "member" ou ausente (retro-compat). Igual ao
# filtro usado em routes/admin.py (_MEMBER_FILTER).
_MEMBER_FILTER = {"$or": [{"account_type": "member"}, {"account_type": {"$exists": False}}]}


@router.get("/structure")
async def get_governance_structure(current_user: User = Depends(get_current_user)):
    """Estrutura completa de governança: órgãos sociais, catálogo de cargos
    (key + label + órgão + vagas + role/privilégios default), categorias de
    membro, privilégios, roles, duração de mandato e slots eleitorais.

    Fonte única para o frontend (substitui o hard-code e os aliases
    deprecated /users/meta/cargos e /users/meta/privileges)."""
    return governance_structure()


@router.get("/corpos-sociais", response_model=CorposSociaisResponse)
async def get_corpos_sociais():
    """Titulares atuais dos órgãos sociais para a página pública /sobre.

    Público (sem autenticação). Devolve a estrutura estatutária completa dos
    3 órgãos a partir do catálogo, com `titulares: []` (→ "Vago" no frontend)
    quando o cargo não tem titular ativo. Expõe APENAS nome + foto."""
    orgaos_out = []
    for orgao_id in _PUBLIC_ORGAO_ORDER:
        cargos = sorted(
            (c for c in CARGOS_CATALOG if c["orgao"] == orgao_id),
            key=lambda c: c["ordem"],
        )
        cargos_out = []
        for cargo in cargos:
            holders = await db.users.find(
                {"cargo": cargo["key"], "status": "ativo", **_MEMBER_FILTER},
                {"_id": 0, "name": 1, "photo_url": 1},
            ).to_list(cargo["seats"] or 100)
            titulares = [{"name": h.get("name") or "—", "photo_url": h.get("photo_url")} for h in holders]
            cargos_out.append(
                {
                    "key": cargo["key"],
                    "label": cargo["label"],
                    "ordem": cargo["ordem"],
                    "seats": cargo["seats"],
                    "titulares": titulares,
                }
            )
        orgaos_out.append(
            {
                "id": orgao_id,
                "nome": _ORGAO_DISPLAY[orgao_id],
                "tipo": ORGAOS[orgao_id]["tipo"],
                "cargos": cargos_out,
            }
        )
    return CorposSociaisResponse(orgaos=orgaos_out)
