"""Ciclo anual de prestação de contas (spec-ciclo §4–5; Art. 19.1/31.k/34/37).

F2 — Balancetes: o Tesoureiro publica balancetes periódicos / balanço anual,
**congelando** o snapshot de `/finances/summary` no momento (auditabilidade — os
números não mudam depois); o Conselho Fiscal audita ao nível do período
(`cf_audit`: conferido + observações, decisão §12.3).

F3 — Exercícios (ciclo guiado: relatório/orçamento/plano + parecer CF +
aprovação da AG) é acrescentado neste mesmo módulo.

RBAC:
- publicar balancete: `manage_finances` (inclui o Tesoureiro — role `financeiro`)
- auditar balancete:  Conselho Fiscal (`can_emit_parecer_cf`) — NÃO escreve transacções
- ver balancetes:     `can_view_finances`; o PDF público segue o fluxo de documentos
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from auth import can_manage_finances, can_view_finances, get_current_user
from database import db
from helpers import create_audit_log, members_of_orgao, notify_all_active_users, notify_users
from models import (
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
    Balancete,
    BalanceteAuditar,
    BalanceteCreate,
    Exercicio,
    ExercicioAprovar,
    ExercicioCreate,
    ExercicioSubmeterAG,
    OrcamentoSubmit,
    ParecerCF,
    ParecerSubmit,
    PlanoSubmit,
    RelatorioContasSubmit,
    User,
)
from permissions import can_emit_parecer_cf, is_direcao, is_mesa_ag
from routes.finances import compute_dre_report, compute_financial_summary

router = APIRouter(tags=["prestacao-contas"])

_LINK_BAL = "/financeiro/balancetes"
_LINK_EX = "/financeiro/prestacao-contas"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_manage_finances(user: User):
    if not can_manage_finances(user):
        raise HTTPException(status_code=403, detail="Sem permissao para publicar balancetes")


def _require_view_finances(user: User):
    if not can_view_finances(user):
        raise HTTPException(status_code=403, detail="Sem permissao para ver balancetes")


def _require_cf(user: User):
    if not can_emit_parecer_cf(user):
        raise HTTPException(status_code=403, detail="Apenas o Conselho Fiscal pode auditar")


async def _validate_document(document_id: str):
    doc = await db.documents.find_one({"id": document_id}, {"_id": 0, "id": 1})
    if not doc:
        raise HTTPException(status_code=400, detail="Documento associado nao encontrado")


# --------------------------------------------------------------------------- #
# Balancetes (F2 — Art. 34, 37)
# --------------------------------------------------------------------------- #


@router.post("/balancetes")
async def publish_balancete(data: BalanceteCreate, current_user: User = Depends(get_current_user)):
    _require_manage_finances(current_user)
    if data.document_id:
        await _validate_document(data.document_id)

    # Congela o snapshot no momento da publicação (não recalcular depois).
    if data.date_inicio or data.date_fim:
        snapshot = await compute_financial_summary(date_gte=data.date_inicio, date_lt=data.date_fim)
    elif data.month:
        snapshot = await compute_financial_summary(year=data.exercicio_ano, month=data.month)
    else:
        snapshot = await compute_financial_summary(year=data.exercicio_ano)

    bal = Balancete(
        tipo=data.tipo,
        periodo=data.periodo,
        exercicio_ano=data.exercicio_ano,
        snapshot=snapshot,
        document_id=data.document_id,
        visibility=data.visibility,
        published=True,
        published_by=current_user.id,
        published_at=_now(),
    )
    await db.balancetes.insert_one(bal.model_dump())
    await create_audit_log(
        current_user.id,
        f"Publicou balancete {data.periodo}",
        bal.id,
        details={"tipo": data.tipo, "periodo": data.periodo, "exercicio_ano": data.exercicio_ano},
    )
    cf_ids = await members_of_orgao("conselho_fiscal")
    await notify_users(
        cf_ids,
        "financeiro",
        "Balancete publicado",
        f"Foi publicado o balancete {data.periodo} para auditoria do Conselho Fiscal.",
        _LINK_BAL,
        exclude_id=current_user.id,
    )
    return bal


@router.get("/balancetes")
async def list_balancetes(
    exercicio_ano: Optional[int] = None,
    current_user: User = Depends(get_current_user),
):
    _require_view_finances(current_user)
    query = {}
    if exercicio_ano:
        query["exercicio_ano"] = exercicio_ano
    items = await db.balancetes.find(query, {"_id": 0}).sort("created_at", -1).to_list(None)
    return {"items": items, "total": len(items)}


@router.get("/balancetes/{balancete_id}")
async def get_balancete(balancete_id: str, current_user: User = Depends(get_current_user)):
    _require_view_finances(current_user)
    bal = await db.balancetes.find_one({"id": balancete_id}, {"_id": 0})
    if not bal:
        raise HTTPException(status_code=404, detail="Balancete nao encontrado")
    return bal


@router.post("/balancetes/{balancete_id}/auditar")
async def auditar_balancete(balancete_id: str, data: BalanceteAuditar, current_user: User = Depends(get_current_user)):
    _require_cf(current_user)
    bal = await db.balancetes.find_one({"id": balancete_id}, {"_id": 0})
    if not bal:
        raise HTTPException(status_code=404, detail="Balancete nao encontrado")

    cf_audit = {
        "audited_by": current_user.id,
        "audited_at": _now(),
        "conferido": data.conferido,
        "observacoes": (data.observacoes.strip() if data.observacoes else None),
    }
    await db.balancetes.update_one({"id": balancete_id}, {"$set": {"cf_audit": cf_audit}})
    await create_audit_log(
        current_user.id,
        f"Auditou balancete {bal.get('periodo')} ({'conferido' if data.conferido else 'com observacoes'})",
        balancete_id,
        details={"conferido": data.conferido},
    )
    publisher = bal.get("published_by")
    if publisher:
        await notify_users(
            [publisher],
            "financeiro",
            "Balancete auditado",
            f"O Conselho Fiscal auditou o balancete {bal.get('periodo')}.",
            _LINK_BAL,
            exclude_id=current_user.id,
        )
    return {"id": balancete_id, "cf_audit": cf_audit}


# --------------------------------------------------------------------------- #
# Exercícios — ciclo guiado (F3 — Art. 19.1, 31.k, 37; integra a AG na F4)
# --------------------------------------------------------------------------- #

# Estados em que o Orçamento/Plano ainda são editáveis (antes de ir à AG).
_EDITAVEL = ("aberto", "relatorio_submetido", "parecer_emitido", "reaberto")


def _require_direcao(user: User):
    if not (user.role == "admin" or is_direcao(user)):
        raise HTTPException(status_code=403, detail="Apenas a Direccao ou admin")


def _require_mesa_ag(user: User):
    if not (user.role == "admin" or is_mesa_ag(user)):
        raise HTTPException(status_code=403, detail="Apenas a Mesa da AG ou admin")


async def _get_exercicio(ano: int) -> dict:
    ex = await db.exercicios.find_one({"ano": ano}, {"_id": 0})
    if not ex:
        raise HTTPException(status_code=404, detail="Exercicio nao encontrado")
    return ex


async def _validate_deliberacao_aprovada(deliberacao_id: str) -> dict:
    delib = await db.assembleia_deliberacoes.find_one({"id": deliberacao_id}, {"_id": 0})
    if not delib:
        raise HTTPException(status_code=400, detail="Deliberacao da AG nao encontrada")
    if not delib.get("aprovado"):
        raise HTTPException(status_code=400, detail="A deliberacao da AG nao foi aprovada")
    return delib


def _aviso_prazo_1t(ano: int) -> Optional[str]:
    """Art. 19.1 — a AG ordinária que aprova o exercício N realiza-se no 1.º
    trimestre de N+1. Avisa (NÃO bloqueia) se já passou o prazo."""
    prazo = f"{ano + 1}-03-31T23:59:59"
    if _now() > prazo:
        return f"Submissao/aprovacao fora do 1.o trimestre de {ano + 1} (Art. 19.1)."
    return None


@router.post("/exercicios")
async def abrir_exercicio(data: ExercicioCreate, current_user: User = Depends(get_current_user)):
    _require_direcao(current_user)
    existing = await db.exercicios.find_one({"ano": data.ano}, {"_id": 0, "id": 1})
    if existing:
        raise HTTPException(status_code=400, detail=f"Ja existe um exercicio para {data.ano}")
    ex = Exercicio(ano=data.ano, created_by=current_user.id)
    await db.exercicios.insert_one(ex.model_dump())
    await create_audit_log(current_user.id, f"Abriu exercicio {data.ano}", ex.id, details={"ano": data.ano})
    return ex


@router.get("/exercicios")
async def list_exercicios(current_user: User = Depends(get_current_user)):
    _require_view_finances(current_user)
    items = await db.exercicios.find({}, {"_id": 0}).sort("ano", -1).to_list(None)
    return {"items": items, "total": len(items)}


@router.get("/exercicios/{ano}")
async def get_exercicio(ano: int, current_user: User = Depends(get_current_user)):
    _require_view_finances(current_user)
    return await _get_exercicio(ano)


@router.post("/exercicios/{ano}/relatorio")
async def submeter_relatorio(ano: int, data: RelatorioContasSubmit, current_user: User = Depends(get_current_user)):
    _require_direcao(current_user)
    ex = await _get_exercicio(ano)
    if ex["status"] not in ("aberto", "reaberto"):
        raise HTTPException(status_code=400, detail="O relatorio so pode ser submetido com o exercicio aberto")
    await _validate_document(data.document_id)

    # Congela o DRE do ano no momento da submissão (auditabilidade).
    dre_snapshot = await compute_dre_report(ano)
    relatorio = {
        "document_id": data.document_id,
        "dre_snapshot": dre_snapshot,
        "submitted_by": current_user.id,
        "submitted_at": _now(),
    }
    await db.exercicios.update_one(
        {"ano": ano}, {"$set": {"relatorio_contas": relatorio, "status": "relatorio_submetido"}}
    )
    await create_audit_log(current_user.id, f"Submeteu relatorio e contas do exercicio {ano}", ex["id"])

    cf_ids = await members_of_orgao("conselho_fiscal")
    await notify_users(
        cf_ids,
        "financeiro",
        "Relatorio e Contas submetido",
        f"O Relatorio e Contas do exercicio {ano} aguarda o parecer do Conselho Fiscal.",
        _LINK_EX,
        exclude_id=current_user.id,
    )
    return {"ano": ano, "status": "relatorio_submetido", "aviso": _aviso_prazo_1t(ano)}


@router.post("/exercicios/{ano}/orcamento")
async def submeter_orcamento(ano: int, data: OrcamentoSubmit, current_user: User = Depends(get_current_user)):
    _require_direcao(current_user)
    ex = await _get_exercicio(ano)
    if ex["status"] not in _EDITAVEL:
        raise HTTPException(status_code=400, detail="O exercicio ja foi a AG; orcamento nao editavel")
    if data.document_id:
        await _validate_document(data.document_id)

    # Categorias têm de bater com as estatutárias (para comparar orçado/realizado).
    for linha in data.linhas:
        validas = INCOME_CATEGORIES if linha.tipo == "receita" else EXPENSE_CATEGORIES
        if linha.categoria not in validas:
            raise HTTPException(status_code=400, detail=f"Categoria invalida para {linha.tipo}: {linha.categoria}")

    orcamento = {
        "linhas": [linha.model_dump() for linha in data.linhas],
        "document_id": data.document_id,
        "ano_orcamento": data.ano_orcamento or (ano + 1),
        "submitted_by": current_user.id,
        "submitted_at": _now(),
    }
    await db.exercicios.update_one({"ano": ano}, {"$set": {"orcamento": orcamento}})
    await create_audit_log(current_user.id, f"Submeteu orcamento do exercicio {ano}", ex["id"])
    return {"ano": ano, "orcamento": orcamento}


@router.post("/exercicios/{ano}/plano")
async def submeter_plano(ano: int, data: PlanoSubmit, current_user: User = Depends(get_current_user)):
    _require_direcao(current_user)
    ex = await _get_exercicio(ano)
    if ex["status"] not in _EDITAVEL:
        raise HTTPException(status_code=400, detail="O exercicio ja foi a AG; plano nao editavel")
    if data.document_id:
        await _validate_document(data.document_id)

    plano = {
        "atividades": [a.model_dump() for a in data.atividades],
        "document_id": data.document_id,
        "submitted_by": current_user.id,
        "submitted_at": _now(),
    }
    await db.exercicios.update_one({"ano": ano}, {"$set": {"plano_atividades": plano}})
    await create_audit_log(current_user.id, f"Submeteu plano de atividades do exercicio {ano}", ex["id"])
    return {"ano": ano, "plano_atividades": plano}


@router.post("/exercicios/{ano}/parecer")
async def emitir_parecer(ano: int, data: ParecerSubmit, current_user: User = Depends(get_current_user)):
    _require_cf(current_user)  # CF (ou emit_cf_parecer) — separado de manage_finances
    ex = await _get_exercicio(ano)
    if ex["status"] != "relatorio_submetido":
        raise HTTPException(status_code=400, detail="O parecer so pode ser emitido apos o relatorio submetido")
    if data.document_id:
        await _validate_document(data.document_id)

    parecer = ParecerCF(
        document_id=data.document_id,
        sentido=data.sentido,
        texto=data.texto,
        emitted_by=current_user.id,
        emitted_at=_now(),
    ).model_dump()
    await db.exercicios.update_one({"ano": ano}, {"$set": {"parecer_cf": parecer, "status": "parecer_emitido"}})
    await create_audit_log(current_user.id, f"Emitiu parecer do CF do exercicio {ano} ({data.sentido})", ex["id"])
    mesa_ids = await members_of_orgao("mesa_ag")
    await notify_users(
        mesa_ids,
        "financeiro",
        "Parecer do Conselho Fiscal emitido",
        f"O parecer do CF do exercicio {ano} esta pronto para ir a AG ordinaria.",
        _LINK_EX,
        exclude_id=current_user.id,
    )
    return {"ano": ano, "status": "parecer_emitido"}


@router.post("/exercicios/{ano}/submeter-ag")
async def submeter_ag(ano: int, data: ExercicioSubmeterAG, current_user: User = Depends(get_current_user)):
    _require_mesa_ag(current_user)
    ex = await _get_exercicio(ano)
    if ex["status"] != "parecer_emitido":
        raise HTTPException(status_code=400, detail="So vai a AG apos o parecer do CF emitido")
    assemb = await db.assembleias.find_one({"id": data.assembleia_id}, {"_id": 0, "id": 1})
    if not assemb:
        raise HTTPException(status_code=400, detail="Assembleia nao encontrada")

    await db.exercicios.update_one(
        {"ano": ano}, {"$set": {"assembleia_id": data.assembleia_id, "status": "em_aprovacao_ag"}}
    )
    await create_audit_log(current_user.id, f"Submeteu exercicio {ano} a AG ordinaria", ex["id"])
    return {"ano": ano, "status": "em_aprovacao_ag", "aviso": _aviso_prazo_1t(ano)}


@router.post("/exercicios/{ano}/aprovar")
async def aprovar_exercicio(ano: int, data: ExercicioAprovar, current_user: User = Depends(get_current_user)):
    _require_mesa_ag(current_user)
    ex = await _get_exercicio(ano)
    if ex["status"] != "em_aprovacao_ag":
        raise HTTPException(status_code=400, detail="O exercicio tem de estar em aprovacao na AG")

    # A aprovação É da AG (Art. 19.1/37): exige uma deliberação. Se aprovar, a
    # deliberação tem de estar aprovada.
    delib = (
        await _validate_deliberacao_aprovada(data.deliberacao_id)
        if data.aprovado
        else (await db.assembleia_deliberacoes.find_one({"id": data.deliberacao_id}, {"_id": 0}))
    )
    if not data.aprovado and not delib:
        raise HTTPException(status_code=400, detail="Deliberacao da AG nao encontrada")
    # A deliberação tem de pertencer à AG onde o exercício foi submetido
    # (submeter_ag fixou ex["assembleia_id"]) — senão aprovava-se/rejeitava-se
    # com o voto de outra assembleia (Art. 19.1/37).
    if delib.get("assembleia_id") != ex.get("assembleia_id"):
        raise HTTPException(
            status_code=400,
            detail="A deliberacao tem de pertencer a assembleia onde o exercicio foi submetido a AG",
        )

    novo_status = "aprovado" if data.aprovado else "rejeitado"
    updates = {
        "status": novo_status,
        "deliberacao_id": data.deliberacao_id,
        "aprovado_em": _now() if data.aprovado else None,
    }
    await db.exercicios.update_one({"ano": ano}, {"$set": updates})
    await create_audit_log(current_user.id, f"Exercicio {ano} {novo_status} pela AG", ex["id"])

    if data.aprovado:
        await notify_all_active_users(
            "financeiro",
            "Contas aprovadas",
            f"A Assembleia Geral aprovou o Relatorio e Contas do exercicio {ano}.",
            _LINK_EX,
        )
    return {"ano": ano, "status": novo_status, "aviso": _aviso_prazo_1t(ano)}


@router.post("/exercicios/{ano}/reabrir")
async def reabrir_exercicio(ano: int, current_user: User = Depends(get_current_user)):
    _require_mesa_ag(current_user)
    ex = await _get_exercicio(ano)
    if ex["status"] not in ("rejeitado", "aprovado"):
        raise HTTPException(status_code=400, detail="So um exercicio fechado pode ser reaberto")
    await db.exercicios.update_one({"ano": ano}, {"$set": {"status": "reaberto"}})
    await create_audit_log(current_user.id, f"Reabriu exercicio {ano}", ex["id"])
    return {"ano": ano, "status": "reaberto"}


@router.get("/exercicios/{ano}/orcamento/execucao")
async def orcamento_execucao(ano: int, current_user: User = Depends(get_current_user)):
    """Orçado (linhas do orçamento) vs. realizado (de /finances) por categoria."""
    _require_view_finances(current_user)
    ex = await _get_exercicio(ano)
    orc = ex.get("orcamento")
    if not orc or not orc.get("linhas"):
        raise HTTPException(status_code=400, detail="Exercicio sem orcamento submetido")

    ano_alvo = orc.get("ano_orcamento") or (ano + 1)
    realizado = await compute_financial_summary(year=ano_alvo)
    rec_real = realizado.get("receitas_por_categoria", {})
    desp_real = realizado.get("despesas_por_categoria", {})

    linhas = []
    for linha in orc["linhas"]:
        real = (rec_real if linha["tipo"] == "receita" else desp_real).get(linha["categoria"], 0)
        previsto = linha.get("valor_previsto", 0)
        linhas.append(
            {
                "categoria": linha["categoria"],
                "tipo": linha["tipo"],
                "orcado": previsto,
                "realizado": real,
                "desvio": real - previsto,
            }
        )
    return {"ano": ano, "ano_orcamento": ano_alvo, "linhas": linhas}
