"""Unit — aviso à Direção de Ato (Art. 54) pendente há mais de X dias (spec 010).

Conduz `notify_overdue_atos()` diretamente, com `members_of_orgao`/`notify_users`
monkeypatched no módulo da rota e uma coleção `atos` falsa que HONRA o filtro
(status + ausência de `overdue_notified_at`) — para testar fielmente a
idempotência. Cobre os 7 casos do quickstart (Cenário A).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

import routes.atos as atos_mod


def _iso_days_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()


def _ato(_id: str, *, status="pendente", created_at=None, **extra) -> dict:
    d = {
        "id": _id,
        "tipo": "pagamento",
        "descricao": "Pagamento X",
        "valor": 50000,
        "status": status,
        "created_at": created_at if created_at is not None else _iso_days_ago(10),
    }
    d.update(extra)
    return d


def _atos_coll(docs: list[dict]) -> MagicMock:
    """Coleção falsa que replica a semântica jsonb REAL do DAO para o filtro do
    varrimento. Spec 010: `{"overdue_notified_at": None}` (`_eq(None)`) casa a chave
    ausente OU o valor null — NÃO uma marca não-null. Spec 013 (recorrência): o
    varrimento usa `$or` de dois ramos sobre a marca — `None` (nunca avisado) OU
    `{"$lte": cutoff}` (marca ISO ≤ cutoff, i.e. último lembrete há ≥ X dias). `$lte`
    é comparação de string ISO (lexicográfica = cronológica); `NULL <= cutoff` é
    falso, logo só o ramo `None` apanha a marca ausente/null."""
    coll = MagicMock(name="atos")

    def _marca_match(d, cond):
        val = d.get("overdue_notified_at")
        if cond is None:  # ramo "nunca avisado": ausente ou null
            return val is None
        if isinstance(cond, dict) and "$lte" in cond:  # ramo "lembrete antigo"
            return val is not None and val <= cond["$lte"]
        return False

    def _find(query=None, projection=None):
        q = query or {}
        res = []
        for d in docs:
            if q.get("status") and d.get("status") != q["status"]:
                continue
            if "$or" in q:
                if not any(_marca_match(d, sub.get("overdue_notified_at")) for sub in q["$or"]):
                    continue
            elif "overdue_notified_at" in q:
                if not _marca_match(d, q["overdue_notified_at"]):
                    continue
            res.append(dict(d))
        cur = MagicMock()
        cur.to_list = AsyncMock(return_value=res)
        return cur

    async def _update_one(filt, update):
        for d in docs:
            if d.get("id") == filt.get("id"):
                d.update(update.get("$set", {}))
        return MagicMock(modified_count=1)

    coll.find = MagicMock(side_effect=_find)
    coll.update_one = AsyncMock(side_effect=_update_one)
    return coll


def _wire_users(mock_db, users: list[dict]) -> MagicMock:
    """Coleção `users` falsa que honra o filtro de elegibilidade do proponente
    (spec 012): `{"id": {"$in": [...]}, "status": "ativo", "account_type": {"$ne": "technical"}}`.
    `users` = [{"id","status","account_type"?}]. `$ne` casa também account_type ausente."""
    coll = MagicMock(name="users")

    def _find(query=None, projection=None):
        q = query or {}
        ids = (q.get("id") or {}).get("$in")
        res = []
        for u in users:
            if ids is not None and u["id"] not in ids:
                continue
            if q.get("status") and u.get("status") != q["status"]:
                continue
            ne = q.get("account_type")
            if isinstance(ne, dict) and "$ne" in ne and u.get("account_type") == ne["$ne"]:
                continue
            res.append({"id": u["id"]})
        cur = MagicMock()
        cur.to_list = AsyncMock(return_value=res)
        return cur

    coll.find = MagicMock(side_effect=_find)
    mock_db.users = coll
    return coll


@pytest.fixture
def wired(mock_db, monkeypatch):
    """Liga os colaboradores: notify_users observável, Direção com 2 membros,
    limiar X=7 por omissão. Devolve (mock_db, notify_users_mock)."""
    notify = AsyncMock()
    monkeypatch.setattr(atos_mod, "notify_users", notify)
    monkeypatch.setattr(atos_mod, "members_of_orgao", AsyncMock(return_value=["d1", "d2"]))
    mock_db.finance_settings.find_one = AsyncMock(return_value={"ato_overdue_dias": 7})
    return mock_db, notify


async def test_pendente_atrasado_avisa_direcao_com_link(wired):
    db, notify = wired
    docs = [_ato("a1", created_at=_iso_days_ago(10))]
    db.atos = _atos_coll(docs)

    result = await atos_mod.notify_overdue_atos()

    assert result["overdue"] == 1 and result["notified_atos"] == 1 and result["recipients"] == 2
    assert notify.await_count == 1
    args = notify.await_args.args
    assert args[0] == ["d1", "d2"]  # destinatários = Direção
    assert args[4] == atos_mod._LINK  # link para agir
    assert docs[0]["overdue_notified_at"]  # marca gravada


async def test_dentro_do_limiar_nao_avisa(wired):
    db, notify = wired
    db.atos = _atos_coll([_ato("a1", created_at=_iso_days_ago(3))])  # < 7

    result = await atos_mod.notify_overdue_atos()

    assert result["overdue"] == 0 and result["notified_atos"] == 0
    notify.assert_not_awaited()


async def test_idempotente_uma_unica_vez(wired):
    db, notify = wired
    docs = [_ato("a1", created_at=_iso_days_ago(10))]
    db.atos = _atos_coll(docs)

    first = await atos_mod.notify_overdue_atos()
    second = await atos_mod.notify_overdue_atos()

    assert first["notified_atos"] == 1
    # 2.º disparo imediato: marca recente (< X dias) ⇒ não re-avisa (cadência, spec 013)
    assert second["notified_atos"] == 0
    assert notify.await_count == 1


async def test_resolvido_nao_avisa(wired):
    db, notify = wired
    db.atos = _atos_coll([_ato("a1", status="aprovado", created_at=_iso_days_ago(30))])

    result = await atos_mod.notify_overdue_atos()

    assert result["evaluated"] == 0 and result["overdue"] == 0
    notify.assert_not_awaited()


async def test_sem_direcao_nao_erra_nem_marca(wired, monkeypatch):
    db, notify = wired
    monkeypatch.setattr(atos_mod, "members_of_orgao", AsyncMock(return_value=[]))
    docs = [_ato("a1", created_at=_iso_days_ago(10))]
    db.atos = _atos_coll(docs)

    result = await atos_mod.notify_overdue_atos()

    assert result["overdue"] == 1 and result["recipients"] == 0 and result["notified_atos"] == 0
    notify.assert_not_awaited()
    assert "overdue_notified_at" not in docs[0]  # não marca ⇒ volta a qualificar


async def test_limiar_menor_passa_a_qualificar(wired):
    db, notify = wired
    db.finance_settings.find_one = AsyncMock(return_value={"ato_overdue_dias": 2})
    db.atos = _atos_coll([_ato("a1", created_at=_iso_days_ago(3))])  # 3 > 2

    result = await atos_mod.notify_overdue_atos()

    assert result["overdue"] == 1 and result["notified_atos"] == 1


async def test_created_at_ausente_ou_invalido_e_ignorado(wired):
    db, notify = wired
    ausente = _ato("a1")
    ausente.pop("created_at")  # campo verdadeiramente ausente
    db.atos = _atos_coll(
        [
            ausente,
            _ato("a2", created_at="not-a-date"),  # inválido
        ]
    )

    result = await atos_mod.notify_overdue_atos()

    assert result["evaluated"] == 2 and result["overdue"] == 0
    notify.assert_not_awaited()


async def test_default_7_quando_settings_ausente(wired):
    db, notify = wired
    db.finance_settings.find_one = AsyncMock(return_value=None)  # nunca configurado
    db.atos = _atos_coll([_ato("a1", created_at=_iso_days_ago(10))])  # 10 > 7 default

    result = await atos_mod.notify_overdue_atos()

    assert result["notified_atos"] == 1


async def test_marca_null_presente_ainda_qualifica(wired):
    """Regressão: `create_ato` faz `model_dump()`, que grava a chave
    `overdue_notified_at` com valor `null`. O filtro tem de casar esse caso
    (não `$exists:false`, que excluiria todos os atos da app)."""
    db, notify = wired
    docs = [_ato("a1", created_at=_iso_days_ago(10), overdue_notified_at=None)]
    db.atos = _atos_coll(docs)

    result = await atos_mod.notify_overdue_atos()

    assert result["overdue"] == 1 and result["notified_atos"] == 1
    assert docs[0]["overdue_notified_at"]  # marca real gravada


# ===== spec 012 — lembrete ao proponente ==================================== #


def _proponente_call(notify, proponente_id):
    """Devolve a chamada a notify_users cujo 1.º arg é [proponente_id], ou None."""
    for c in notify.await_args_list:
        if c.args and c.args[0] == [proponente_id]:
            return c
    return None


async def test_proponente_socio_comum_avisado_uma_vez(wired):
    db, notify = wired  # Direção = ["d1","d2"]
    db.atos = _atos_coll([_ato("a1", created_at=_iso_days_ago(10), created_by="prop1")])
    _wire_users(db, [{"id": "prop1", "status": "ativo"}])

    result = await atos_mod.notify_overdue_atos()

    assert result["notified_atos"] == 1 and result["notified_proponentes"] == 1
    call = _proponente_call(notify, "prop1")
    assert call is not None  # proponente avisado
    assert "10 dias" in call.args[3]  # idade no corpo
    # FR-002: identifica o Ato (descrição + tipo + valor), como o aviso à Direção
    assert "Pagamento X" in call.args[3] and "pagamento" in call.args[3] and "50,000 CVE" in call.args[3]
    assert call.args[4] == atos_mod._LINK  # link para agir
    # spec 010 intacta: a Direção continua avisada
    assert _proponente_call(notify, "prop1") is not None and notify.await_count == 2


async def test_proponente_que_e_direcao_nao_duplica(wired):
    db, notify = wired  # Direção = ["d1","d2"]
    db.atos = _atos_coll([_ato("a1", created_at=_iso_days_ago(10), created_by="d1")])
    _wire_users(db, [{"id": "d1", "status": "ativo"}])

    result = await atos_mod.notify_overdue_atos()

    assert result["notified_atos"] == 1 and result["notified_proponentes"] == 0
    assert _proponente_call(notify, "d1") is None  # sem aviso de proponente separado
    assert notify.await_count == 1  # só o aviso à Direção


async def test_proponente_inativo_ou_tecnico_nao_avisado(wired):
    db, notify = wired
    db.atos = _atos_coll(
        [
            _ato("a1", created_at=_iso_days_ago(10), created_by="inativo1"),
            _ato("a2", created_at=_iso_days_ago(10), created_by="tech1"),
        ]
    )
    _wire_users(
        db, [{"id": "inativo1", "status": "inativo"}, {"id": "tech1", "status": "ativo", "account_type": "technical"}]
    )

    result = await atos_mod.notify_overdue_atos()

    assert result["notified_atos"] == 2 and result["notified_proponentes"] == 0
    assert _proponente_call(notify, "inativo1") is None
    assert _proponente_call(notify, "tech1") is None


async def test_proponente_idempotente_nao_re_avisa(wired):
    db, notify = wired
    db.atos = _atos_coll([_ato("a1", created_at=_iso_days_ago(10), created_by="prop1")])
    _wire_users(db, [{"id": "prop1", "status": "ativo"}])

    first = await atos_mod.notify_overdue_atos()
    second = await atos_mod.notify_overdue_atos()

    assert first["notified_proponentes"] == 1
    assert second["notified_atos"] == 0 and second["notified_proponentes"] == 0  # marca partilhada


async def test_sem_direcao_nao_avisa_proponente(wired, monkeypatch):
    db, notify = wired
    monkeypatch.setattr(atos_mod, "members_of_orgao", AsyncMock(return_value=[]))
    db.atos = _atos_coll([_ato("a1", created_at=_iso_days_ago(10), created_by="prop1")])
    _wire_users(db, [{"id": "prop1", "status": "ativo"}])

    result = await atos_mod.notify_overdue_atos()

    # Sem destinatários Direção ⇒ não marca NEM avisa o proponente (invariante spec 010)
    assert result["notified_atos"] == 0 and result["notified_proponentes"] == 0
    notify.assert_not_awaited()


async def test_proponente_falha_entrega_nao_marca_ato(wired):
    """Ordenação de entrega: a marca de idempotência só é gravada APÓS o aviso ao
    proponente (como o aviso à Direção). Se a entrega ao proponente falhar, o Ato
    NÃO fica marcado ⇒ volta a qualificar no próximo varrimento (entrega ≥1×, sem
    perda silenciosa)."""
    db, notify = wired  # Direção = ["d1","d2"]
    atos = [_ato("a1", created_at=_iso_days_ago(10), created_by="prop1")]
    db.atos = _atos_coll(atos)
    _wire_users(db, [{"id": "prop1", "status": "ativo"}])

    async def _falha_so_no_proponente(user_ids, *a, **k):
        if user_ids == ["prop1"]:
            raise RuntimeError("falha de entrega no insert da notificação")

    notify.side_effect = _falha_so_no_proponente

    with pytest.raises(RuntimeError):
        await atos_mod.notify_overdue_atos()

    # marca ausente ⇒ o Ato continua a qualificar (sem perda silenciosa do aviso)
    assert atos[0].get("overdue_notified_at") is None


# ===== spec 013 — recorrência (escalonamento) ============================== #


async def test_recorrencia_re_avisa_apos_x_dias(wired):
    """US1: marca de há > X dias (último lembrete antigo) ⇒ NOVO lembrete e o
    cursor `overdue_notified_at` avança para agora."""
    db, notify = wired  # X = 7
    docs = [_ato("a1", created_at=_iso_days_ago(30), overdue_notified_at=_iso_days_ago(10))]
    db.atos = _atos_coll(docs)

    result = await atos_mod.notify_overdue_atos()

    assert result["overdue"] == 1 and result["notified_atos"] == 1  # re-avisado
    assert notify.await_count == 1 and notify.await_args.args[0] == ["d1", "d2"]
    assert docs[0]["overdue_notified_at"] > _iso_days_ago(1)  # cursor avançou (≈ agora)


async def test_primeiro_aviso_sem_marca_intacto(wired):
    """US1: Ato pendente sem marca (nunca avisado), idade > X ⇒ 1.º lembrete
    (comportamento das specs 010/012 preservado sob recorrência)."""
    db, notify = wired
    docs = [_ato("a1", created_at=_iso_days_ago(10))]  # sem overdue_notified_at
    db.atos = _atos_coll(docs)

    result = await atos_mod.notify_overdue_atos()

    assert result["notified_atos"] == 1 and notify.await_count == 1
    assert docs[0]["overdue_notified_at"]  # marca gravada


async def test_resolvido_com_marca_antiga_nao_re_avisa(wired):
    """US1: um Ato que saiu de `pendente` NÃO re-avisa, mesmo com marca antiga (FR-007)."""
    db, notify = wired
    db.atos = _atos_coll(
        [_ato("a1", status="aprovado", created_at=_iso_days_ago(30), overdue_notified_at=_iso_days_ago(20))]
    )

    result = await atos_mod.notify_overdue_atos()

    assert result["evaluated"] == 0 and result["notified_atos"] == 0
    notify.assert_not_awaited()


async def test_lembrete_recorrente_reflete_antiguidade(wired):
    """US2: o corpo reflete a antiguidade ATUAL (crescente) e os destinatários
    mantêm-se a Direção — sem alargar a outros órgãos (FR-005)."""
    db, notify = wired
    db.atos = _atos_coll([_ato("a1", created_at=_iso_days_ago(45), overdue_notified_at=_iso_days_ago(10))])

    await atos_mod.notify_overdue_atos()

    assert notify.await_count == 1  # só a Direção (sem outros órgãos)
    call = notify.await_args
    assert call.args[0] == ["d1", "d2"]
    assert "45 dias" in call.args[3]  # antiguidade atual no corpo


async def test_marca_recente_nao_re_avisa(wired):
    """US3: último lembrete há < X dias ⇒ NÃO re-avisa (anti-spam, SC-002)."""
    db, notify = wired  # X = 7
    db.atos = _atos_coll([_ato("a1", created_at=_iso_days_ago(30), overdue_notified_at=_iso_days_ago(2))])

    result = await atos_mod.notify_overdue_atos()

    assert result["evaluated"] == 0 and result["notified_atos"] == 0
    notify.assert_not_awaited()


async def test_cadencia_dois_varrimentos_uma_so_vez(wired):
    """US3: um lembrete agora (cursor antigo) avança o cursor; um 2.º varrimento
    imediato já não re-avisa (≥ X dias entre lembretes, SC-005)."""
    db, notify = wired
    docs = [_ato("a1", created_at=_iso_days_ago(30), overdue_notified_at=_iso_days_ago(10))]
    db.atos = _atos_coll(docs)

    first = await atos_mod.notify_overdue_atos()
    second = await atos_mod.notify_overdue_atos()

    assert first["notified_atos"] == 1  # cursor antigo ⇒ lembra
    assert second["notified_atos"] == 0  # cursor agora recente ⇒ não re-avisa
    assert notify.await_count == 1


async def test_endpoint_admin_audita_disparo(wired, admin_user, monkeypatch):
    """O disparo manual é uma ação de admin que muta atos ⇒ tem de auditar."""
    db, notify = wired
    audit = AsyncMock()
    monkeypatch.setattr(atos_mod, "create_audit_log", audit)
    db.atos = _atos_coll([_ato("a1", created_at=_iso_days_ago(10))])

    result = await atos_mod.notify_overdue_endpoint(MagicMock(), current_user=admin_user)

    assert result["notified_atos"] == 1
    audit.assert_awaited_once()


async def test_endpoint_nega_nao_admin(wired, socio_user):
    db, _ = wired
    db.atos = _atos_coll([_ato("a1", created_at=_iso_days_ago(10))])

    with pytest.raises(HTTPException) as exc:
        await atos_mod.notify_overdue_endpoint(MagicMock(), current_user=socio_user)
    assert exc.value.status_code == 403
