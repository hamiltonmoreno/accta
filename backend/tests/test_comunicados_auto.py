"""Gatilhos automáticos de governança → comunicado oficial (F3).

Cada gatilho (convocatória de AG, abertura de votação, publicação de
deliberação) AGENDA `comunicados_service.dispatch_oficial_auto` via
BackgroundTasks — o envio nunca bloqueia a acção de governança. Aqui só se
verifica que a task ficou agendada com a função correcta; o anti-duplicado e
o fan-out estão cobertos pelos testes do serviço.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import BackgroundTasks

import comunicados_service
from routes import assembleias as a_route
from routes import eleicoes as e_route
from models import AssembleiaCreate, AssembleiaDeliberacaoCreate, User


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

FUTURE = "2030-01-01T10:00:00+00:00"  # antecedência alta


def _request():
    class _R:
        client = type("C", (), {"host": "127.0.0.1"})
        headers = {"User-Agent": "test", "origin": "https://accta.cv"}

    return _R()


def _cursor(items):
    cur = MagicMock()
    cur.sort.return_value = cur
    cur.skip.return_value = cur
    cur.limit.return_value = cur
    cur.to_list = AsyncMock(return_value=items)
    return cur


def _coll(**methods):
    c = MagicMock()
    c.find_one = AsyncMock(return_value=None)
    c.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
    c.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    c.count_documents = AsyncMock(return_value=0)
    c.find = MagicMock(return_value=_cursor([]))
    for k, v in methods.items():
        setattr(c, k, v)
    return c


def _mesa_ag(**over) -> User:
    base = {
        "name": "Mesa",
        "email": "mesa@x.cv",
        "role": "socio",
        "status": "ativo",
        "cargo": "ag_presidente",
        "account_type": "member",
        "member_category": "ordinario",
    }
    base.update(over)
    return User(**base)


def _voters(n: int) -> list[dict]:
    return [
        {"id": f"v{i}", "account_type": "member", "status": "ativo", "member_category": "ordinario"}
        for i in range(n)
    ]


def _scheduled(bt: BackgroundTasks) -> bool:
    return any(t.func is comunicados_service.dispatch_oficial_auto for t in bt.tasks)


def _dispatch_task(bt: BackgroundTasks):
    return next(t for t in bt.tasks if t.func is comunicados_service.dispatch_oficial_auto)


# --------------------------------------------------------------------------- #
# Task 13 — convocatória de AG
# --------------------------------------------------------------------------- #


async def test_create_assembleia_schedules_oficial_comunicado(mock_db, monkeypatch):
    mock_db.assembleias = _coll()
    mock_db.users.find = MagicMock(return_value=_cursor(_voters(10)))
    monkeypatch.setattr(a_route, "create_audit_log", AsyncMock())
    monkeypatch.setattr(a_route, "notify_all_active_users", AsyncMock())

    bt = BackgroundTasks()
    await a_route.create_assembleia(
        request=_request(),
        data=AssembleiaCreate(tipo="ordinaria", titulo="AGO 2030", data=FUTURE, local="Sede"),
        background_tasks=bt,
        current_user=_mesa_ag(),
    )
    assert _scheduled(bt)

    task = _dispatch_task(bt)
    inserted = mock_db.assembleias.insert_one.call_args.args[0]
    assert task.kwargs["source_kind"] == "assembleia_convocatoria"
    assert task.kwargs["ref_id"] == inserted["id"]


# --------------------------------------------------------------------------- #
# Task 14 — abertura de votação (eleição)
# --------------------------------------------------------------------------- #


async def test_abrir_votacao_schedules_oficial_comunicado(mock_db, monkeypatch):
    mock_db.eleicoes = _coll(
        find_one=AsyncMock(return_value={"id": "e1", "ano": 2030, "status": "candidaturas"})
    )
    mock_db.eleicao_listas = _coll(count_documents=AsyncMock(return_value=2))
    monkeypatch.setattr(e_route, "create_audit_log", AsyncMock())

    bt = BackgroundTasks()
    await e_route.abrir_votacao("e1", _request(), bt, current_user=_mesa_ag())
    assert _scheduled(bt)

    task = _dispatch_task(bt)
    assert task.kwargs["source_kind"] == "eleicao_abertura"
    assert task.kwargs["ref_id"] == "e1"


# --------------------------------------------------------------------------- #
# Task 15 — publicação de deliberação
# --------------------------------------------------------------------------- #


async def test_register_deliberacao_schedules_oficial_comunicado(mock_db, monkeypatch):
    mock_db.assembleias = _coll(
        find_one=AsyncMock(
            return_value={"id": "a1", "titulo": "AGO 2030", "status": "convocada", "eligible_voters_count": 10}
        )
    )
    # poder presente = 8 (>= quórum de 2.ª chamada de 10)
    mock_db.assembleia_presencas = _coll(find=MagicMock(return_value=_cursor([{"voting_power": 8}])))
    mock_db.assembleia_deliberacoes = _coll()
    monkeypatch.setattr(a_route, "create_audit_log", AsyncMock())

    bt = BackgroundTasks()
    await a_route.register_deliberacao(
        assembleia_id="a1",
        request=_request(),
        data=AssembleiaDeliberacaoCreate(
            ponto="1",
            descricao="Aprovar contas",
            tipo_maioria="absoluta",
            votos_favor=6,
            votos_contra=2,
            abstencoes=0,
        ),
        background_tasks=bt,
        current_user=_mesa_ag(),
    )
    assert _scheduled(bt)

    task = _dispatch_task(bt)
    delib = mock_db.assembleia_deliberacoes.insert_one.call_args.args[0]
    assert task.kwargs["source_kind"] == "assembleia_deliberacao"
    # ref_id tem de ser o id da DELIBERAÇÃO, nunca o da assembleia-pai.
    assert task.kwargs["ref_id"] == delib["id"]
    assert task.kwargs["ref_id"] != "a1"
