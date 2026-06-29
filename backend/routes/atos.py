"""Co-aprovação / dupla assinatura de actos que vinculam a ACCTA (Art. 54;
spec-controlos-financeiros §4.1).

Um acto nasce `pendente` com os `requisitos` congelados pelo tipo. Cada membro
da Direcção assina (aprovar/rejeitar) uma vez; o estado é reapurado a cada
assinatura por `atos_rules.evaluate_status` (fonte única). Um pagamento aprovado
é `executar`-ado pelo Tesoureiro/admin, criando a despesa ligada (`ato_id`).

RBAC:
- criar:    admin ou membro da Direcção (inclui Tesoureiro)
- assinar:  membro da Direcção (Presidente/Tesoureiro incluídos)
- executar: Tesoureiro ou admin (só pagamentos aprovados)
- cancelar: proponente ou admin (só pendentes)
- ver:      quem vê finanças (admin/financeiro/CF) ou membro da Direcção
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from auth import can_view_finances, get_current_user
from database import db, sign_ato_atomic
from helpers import create_audit_log, members_of_orgao, notify_users
from models import (
    ATO_DECISOES,
    ATO_TIPOS,
    Ato,
    AtoCreate,
    AtoExecute,
    AtoSign,
    EXPENSE_CATEGORIES,
    Transaction,
    User,
)
from permissions import is_direcao, is_tesoureiro
from atos_rules import evaluate_status, requisitos_for_tipo

router = APIRouter(prefix="/atos", tags=["atos"])

logger = logging.getLogger(__name__)

_LINK = "/financeiro/co-aprovacoes"

# Limiar default de dias (FR-004) quando finance_settings não o tem.
_OVERDUE_DEFAULT_DIAS = 7
# Cadência do agendador in-process (spec 010): uma avaliação por dia.
_OVERDUE_LOOP_SECONDS = 24 * 60 * 60
# Serializa a avaliação in-process: se o loop diário e o disparo manual do
# admin coincidirem, evita que ambos leiam o mesmo ato não-marcado e avisem em
# duplicado (sem CAS; basta para single-process — assunção de single-runner).
_overdue_lock = asyncio.Lock()


def _require_view(user: User):
    if not (can_view_finances(user) or is_direcao(user)):
        raise HTTPException(status_code=403, detail="Sem permissao para ver actos de co-aprovacao")


def _require_create(user: User):
    if not (user.role == "admin" or is_direcao(user)):
        raise HTTPException(status_code=403, detail="Apenas a Direccao ou admin pode criar actos")


def _require_sign(user: User):
    if not is_direcao(user):
        raise HTTPException(status_code=403, detail="Apenas membros da Direccao podem assinar")


def _require_execute(user: User):
    if not (user.role == "admin" or is_tesoureiro(user)):
        raise HTTPException(status_code=403, detail="Apenas o Tesoureiro ou admin pode executar")


def _has_signed(ato: dict, user_id: str) -> bool:
    return any(a.get("user_id") == user_id for a in (ato.get("assinaturas") or []))


@router.post("")
async def create_ato(data: AtoCreate, request: Request, current_user: User = Depends(get_current_user)):
    _require_create(current_user)

    if data.tipo not in ATO_TIPOS:
        raise HTTPException(status_code=400, detail=f"Tipo invalido. Use: {ATO_TIPOS}")
    if not (data.descricao or "").strip():
        raise HTTPException(status_code=400, detail="A descricao e obrigatoria")
    if data.tipo == "pagamento" and (data.valor is None or data.valor <= 0):
        raise HTTPException(status_code=400, detail="Um pagamento exige um valor positivo")
    if data.valor is not None and data.valor < 0:
        raise HTTPException(status_code=400, detail="O valor nao pode ser negativo")

    ato = Ato(
        tipo=data.tipo,
        descricao=data.descricao.strip(),
        valor=data.valor,
        beneficiario=data.beneficiario,
        project_id=data.project_id,
        event_id=data.event_id,
        requisitos=requisitos_for_tipo(data.tipo),
        created_by=current_user.id,
    )
    await db.atos.insert_one(ato.model_dump())
    await create_audit_log(
        current_user.id,
        f"Criou acto de co-aprovacao {ato.id} ({data.tipo})",
        ato.id,
        request=request,
        details={"tipo": data.tipo, "valor": data.valor},
    )

    # Notificar os assinantes requeridos (Direcção) — fallback p/ admins.
    signer_ids = await members_of_orgao("direcao")
    await notify_users(
        signer_ids,
        "financeiro",
        "Acto a aguardar assinatura",
        f"{current_user.name} criou um acto ({data.tipo}) que aguarda a sua co-aprovacao.",
        _LINK,
        exclude_id=current_user.id,
    )
    return ato


@router.get("")
async def list_atos(
    status: Optional[str] = None,
    tipo: Optional[str] = None,
    pendentes_para_mim: bool = False,
    current_user: User = Depends(get_current_user),
):
    _require_view(current_user)
    query = {}
    if status:
        query["status"] = status
    if tipo:
        query["tipo"] = tipo
    atos = await db.atos.find(query, {"_id": 0}).sort("created_at", -1).to_list(None)

    if pendentes_para_mim:
        can_sign = is_direcao(current_user)
        atos = [a for a in atos if a.get("status") == "pendente" and can_sign and not _has_signed(a, current_user.id)]
    return {"items": atos, "total": len(atos)}


@router.get("/{ato_id}")
async def get_ato(ato_id: str, current_user: User = Depends(get_current_user)):
    _require_view(current_user)
    ato = await db.atos.find_one({"id": ato_id}, {"_id": 0})
    if not ato:
        raise HTTPException(status_code=404, detail="Acto nao encontrado")
    return ato


@router.post("/{ato_id}/assinar")
async def sign_ato(ato_id: str, data: AtoSign, request: Request, current_user: User = Depends(get_current_user)):
    _require_sign(current_user)
    if data.decisao not in ATO_DECISOES:
        raise HTTPException(status_code=400, detail=f"Decisao invalida. Use: {ATO_DECISOES}")

    # Motivo da rejeicao (spec 011): obrigatorio e nao-vazio ao rejeitar; ignorado
    # ao aprovar. Limite de 500 carateres (recusa, nao trunca).
    motivo = (data.motivo or "").strip()
    if data.decisao == "rejeitado":
        if not motivo:
            raise HTTPException(status_code=400, detail="E obrigatorio indicar o motivo da rejeicao.")
        if len(motivo) > 500:
            raise HTTPException(status_code=400, detail="O motivo nao pode exceder 500 carateres.")
    else:
        motivo = ""  # aprovar nao grava motivo

    assinatura = {
        "user_id": current_user.id,
        "cargo": current_user.cargo,
        "decisao": data.decisao,
        "signed_at": datetime.now(timezone.utc).isoformat(),
    }
    if motivo:
        assinatura["motivo"] = motivo
    # Assinatura + reapuramento de estado SOB lock da linha do acto (fecha a race
    # TOCTOU de duas assinaturas concorrentes — ver database.sign_ato_atomic). A
    # regra estatutária (evaluate_status) entra como callable; o DAO não importa
    # permissions/governance.
    result = await sign_ato_atomic(ato_id, current_user.id, assinatura, evaluate_status)
    outcome = result["outcome"]
    if outcome == "not_found":
        raise HTTPException(status_code=404, detail="Acto nao encontrado")
    if outcome == "not_pending":
        raise HTTPException(status_code=400, detail="O acto ja nao esta pendente")
    if outcome == "already_signed":
        raise HTTPException(status_code=409, detail="Ja assinou este acto")
    if outcome == "locked":
        # Contenção transitória (outra assinatura concorrente segura o lock).
        raise HTTPException(status_code=409, detail="Assinatura concorrente em curso. Tente novamente.")

    ato = result["ato"]
    novo_status = ato["status"]
    details = {"decisao": data.decisao, "status": novo_status}
    if motivo:
        details["motivo"] = motivo
    await create_audit_log(
        current_user.id,
        f"Assinou acto {ato_id} ({data.decisao})",
        ato_id,
        request=request,
        details=details,
    )

    if novo_status in ("aprovado", "rejeitado"):
        await create_audit_log(current_user.id, f"Acto {ato_id} {novo_status}", ato_id, request=request)
        label = "aprovado" if novo_status == "aprovado" else "rejeitado"
        # Rejeicao: o aviso ao proponente inclui o motivo (spec 011, FR-003). Nao se
        # cria um segundo aviso — enriquece-se o existente (FR-006).
        if novo_status == "rejeitado" and motivo:
            mensagem = f'O acto que propos foi rejeitado. Motivo: "{motivo}"'
        else:
            mensagem = f"O acto que propos foi {label}."
        await notify_users(
            [ato["created_by"]],
            "financeiro",
            f"Acto {label}",
            mensagem,
            _LINK,
            exclude_id=current_user.id,
        )

    # Devolve o doc já atualizado por sign_ato_atomic (= dict(row["doc"]), sem
    # pk/_id) em vez de um re-fetch: poupa um round-trip e fecha a janela em que
    # um assinante concorrente devolveria um doc mais recente que o assinado.
    return ato


@router.post("/{ato_id}/executar")
async def execute_ato(ato_id: str, data: AtoExecute, request: Request, current_user: User = Depends(get_current_user)):
    _require_execute(current_user)

    ato = await db.atos.find_one({"id": ato_id}, {"_id": 0})
    if not ato:
        raise HTTPException(status_code=404, detail="Acto nao encontrado")
    if ato.get("tipo") != "pagamento":
        raise HTTPException(status_code=400, detail="So actos de pagamento podem ser executados")
    if ato.get("status") != "aprovado":
        raise HTTPException(status_code=400, detail="O acto nao esta aprovado")
    if ato.get("transaction_id"):
        raise HTTPException(status_code=400, detail="O acto ja foi executado")
    valor = ato.get("valor")
    if valor is None or valor <= 0:
        raise HTTPException(status_code=400, detail="O acto nao tem um valor valido a pagar")

    category = data.category or "operacional"
    if category not in EXPENSE_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Categoria invalida. Use: {EXPENSE_CATEGORIES}")
    date = data.date or datetime.now(timezone.utc).isoformat()

    transaction = Transaction(
        type="despesa",
        category=category,
        description=ato.get("descricao") or f"Pagamento (acto {ato_id})",
        amount=valor,
        date=date,
        reference=data.reference,
        ato_id=ato_id,
        project_id=ato.get("project_id"),  # propaga o vínculo ao projeto, se existir
        event_id=ato.get("event_id"),  # propaga o vínculo ao evento, se existir (ronda 2)
        created_by=current_user.id,
    )
    await db.transactions.insert_one(transaction.model_dump())
    await db.atos.update_one({"id": ato_id}, {"$set": {"status": "executado", "transaction_id": transaction.id}})
    await create_audit_log(
        current_user.id,
        f"Executou acto {ato_id} -> despesa {transaction.id} ({valor} CVE)",
        ato_id,
        request=request,
        details={"transaction_id": transaction.id, "amount": valor},
    )
    await notify_users(
        [ato["created_by"]],
        "financeiro",
        "Acto executado",
        f"O pagamento do acto que propos foi executado ({valor:,.0f} CVE).",
        _LINK,
        exclude_id=current_user.id,
    )
    return await db.atos.find_one({"id": ato_id}, {"_id": 0})


@router.post("/{ato_id}/cancelar")
async def cancel_ato(ato_id: str, request: Request, current_user: User = Depends(get_current_user)):
    ato = await db.atos.find_one({"id": ato_id}, {"_id": 0})
    if not ato:
        raise HTTPException(status_code=404, detail="Acto nao encontrado")
    if not (current_user.role == "admin" or ato.get("created_by") == current_user.id):
        raise HTTPException(status_code=403, detail="So o proponente ou admin pode cancelar")
    if ato.get("status") != "pendente":
        raise HTTPException(status_code=400, detail="So actos pendentes podem ser cancelados")

    await db.atos.update_one({"id": ato_id}, {"$set": {"status": "cancelado"}})
    await create_audit_log(current_user.id, f"Cancelou acto {ato_id}", ato_id, request=request)
    return await db.atos.find_one({"id": ato_id}, {"_id": 0})


# ===== Aviso à Direção de Ato pendente atrasado (spec 010) ==================== #


def _parse_created_at(value) -> Optional[datetime]:
    """Parse defensivo do created_at (ISO-8601). Ausente/inválido ⇒ None (o ato
    é ignorado com segurança, sem disparar com base em data não fiável)."""
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


async def _overdue_limiar_dias() -> int:
    """Limiar X em dias (FR-004), de finance_settings; default 7 se ausente/inválido."""
    s = await db.finance_settings.find_one({"id": "finance_settings"}, {"_id": 0})
    try:
        dias = int((s or {}).get("ato_overdue_dias") or _OVERDUE_DEFAULT_DIAS)
    except (TypeError, ValueError):
        return _OVERDUE_DEFAULT_DIAS
    return dias if dias >= 1 else _OVERDUE_DEFAULT_DIAS


async def notify_overdue_atos() -> dict:
    """Avalia os Atos pendentes e avisa a Direção dos que estão parados há MAIS
    de X dias (X = finance_settings.ato_overdue_dias, default 7). Uma única vez
    por Ato — grava `overdue_notified_at` e o filtro exclui os já avisados
    (idempotência, FR-005). Reutilizada pelo loop diário e pelo endpoint de
    disparo manual; o lock serializa-os para não avisarem em duplicado.
    Non-fatal por desenho (devolve contadores, não levanta)."""
    async with _overdue_lock:
        return await _notify_overdue_atos_locked()


async def _notify_overdue_atos_locked() -> dict:
    dias = await _overdue_limiar_dias()
    # Só pendentes ainda não avisados (sair de `pendente` ⇒ deixa de ser
    # considerado, FR-006; marca presente ⇒ não re-avisa, FR-005). Match por
    # `None` (não `$exists:false`): o `model_dump()` de `create_ato` grava a
    # chave com valor `null`, logo o operador de presença de chave do DAO
    # (`doc ? key`) excluiria TODOS os atos da app. `_eq(None)` casa
    # corretamente chave-ausente (atos legados) OU valor-null (atos novos);
    # a marca, depois de gravada como ISO string, deixa de casar (idempotência).
    atos = await db.atos.find({"status": "pendente", "overdue_notified_at": None}, {"_id": 0}).to_list(None)

    now = datetime.now(timezone.utc)
    counters = {"evaluated": len(atos), "overdue": 0, "notified_atos": 0, "recipients": 0}

    overdue = []
    for ato in atos:
        created = _parse_created_at(ato.get("created_at"))
        if created is None:
            continue  # data ausente/inválida ⇒ ignora com segurança
        # `(now - created).days` trunca para dias inteiros, logo `> dias` só
        # dispara a partir de dias+1 completos — semântica de "mais de X dias".
        if (now - created).days > dias:
            overdue.append((ato, (now - created).days))
    counters["overdue"] = len(overdue)
    if not overdue:
        return counters

    direcao_ids = await members_of_orgao("direcao")
    if not direcao_ids:
        # Sem destinatários ⇒ não avisa NEM marca: volta a qualificar quando a
        # Direção existir (FR-009: sem erro, o sistema continua).
        return counters
    counters["recipients"] = len(direcao_ids)

    for ato, idade in overdue:
        tipo = ato.get("tipo") or "ato"
        valor = ato.get("valor")
        valor_txt = f", {valor:,.0f} CVE" if isinstance(valor, (int, float)) else ""
        descricao = (ato.get("descricao") or "").strip() or "(sem descrição)"
        await notify_users(
            direcao_ids,
            "financeiro",
            f"Ato pendente há {idade} dias",
            f'O ato "{descricao}" ({tipo}{valor_txt}) está pendente há {idade} dias e aguarda ação da Direção.',
            _LINK,
        )
        await db.atos.update_one({"id": ato["id"]}, {"$set": {"overdue_notified_at": now.isoformat()}})
        counters["notified_atos"] += 1

    return counters


async def overdue_atos_loop():
    """Agendador in-process (spec 010): avalia 1x/dia os Atos pendentes
    atrasados. Non-fatal — uma falha nunca derruba o arranque nem interrompe o
    loop. Idempotente, pelo que reiniciar o relógio no arranque é inofensivo."""
    logger.info("overdue_atos_loop: agendador de avisos de Atos pendentes iniciado")
    while True:
        try:
            result = await notify_overdue_atos()
            if result.get("notified_atos"):
                logger.info("overdue_atos_loop: %s", result)
        except Exception as e:  # noqa: BLE001 - loop non-fatal
            logger.warning("overdue_atos_loop erro (non-fatal): %s", e)
        await asyncio.sleep(_OVERDUE_LOOP_SECONDS)


@router.post("/notify-overdue")
async def notify_overdue_endpoint(request: Request, current_user: User = Depends(get_current_user)):
    """Disparo manual / verificação (admin) da avaliação de Atos pendentes
    atrasados — corre o mesmo código do loop diário. Idempotente: uma 2.ª
    chamada seguida devolve `notified_atos: 0`."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem disparar esta avaliação")
    result = await notify_overdue_atos()
    await create_audit_log(
        current_user.id,
        "Disparou a avaliação de Atos pendentes atrasados",
        request=request,
        details=result,
    )
    return result
