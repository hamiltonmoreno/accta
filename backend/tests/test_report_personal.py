"""Regressão para o rácio do relatório pessoal (issue #193).

`events_attended` conta presenças em eventos de QUALQUER visibilidade
(incl. `direcao`/`privado`), mas o denominador `total_events` contava apenas
`publico`/`socios`. Um sócio presente num evento restrito fazia
`events_attended > total_events` → o dashboard mostrava um rácio > 100%.

O fix: o denominador passa a incluir também os eventos restritos em que o
utilizador esteve presente (`{"attendees": uid}`), garantindo
`total_events >= events_attended`.
"""

from unittest.mock import AsyncMock

import pytest

import routes.report as report_route


@pytest.mark.asyncio
async def test_total_events_inclui_eventos_atendidos(mock_db, socio_user, monkeypatch):
    """O filtro de `total_events` tem de ter o ramo `{"attendees": uid}`."""
    uid = socio_user.id

    # gather_signal_counts é a fonte única do score; isolamos a rota dele.
    monkeypatch.setattr(
        report_route,
        "gather_signal_counts",
        AsyncMock(return_value={
            "evento_presenca": 3,
            "votacao_voto": 0,
            "mural_post": 0,
            "mural_like_recebido": 0,
            "mural_comentario": 0,
            "projeto_participacao": 0,
            "galeria_foto": 0,
        }),
    )

    await report_route.get_personal_report(current_user=socio_user)

    # A rota tem de consultar events.count_documents com o $or que inclui as
    # presenças do utilizador — senão volta o bug do rácio > 100%.
    events_filter = mock_db.events.count_documents.call_args.args[0]
    assert "$or" in events_filter, "denominador perdeu o $or — regressão #193"
    branches = events_filter["$or"]
    assert {"attendees": uid} in branches, (
        "denominador não inclui os eventos atendidos pelo utilizador"
    )
    assert {"visibility": {"$in": ["publico", "socios"]}} in branches


@pytest.mark.asyncio
async def test_ratio_nunca_excede_100pct(mock_db, socio_user, monkeypatch):
    """Cenário do bug: presenças incluem 1 evento restrito não contado antes.

    Com o fix, esse evento entra no denominador via o ramo `attendees`, por
    isso o count devolvido é >= events_attended e o rácio fica <= 100%.
    """
    monkeypatch.setattr(
        report_route,
        "gather_signal_counts",
        AsyncMock(return_value={
            "evento_presenca": 5,
            "votacao_voto": 0,
            "mural_post": 0,
            "mural_like_recebido": 0,
            "mural_comentario": 0,
            "projeto_participacao": 0,
            "galeria_foto": 0,
        }),
    )
    # O $or (publico/socios OU atendidos) devolve >= presenças por construção.
    mock_db.events.count_documents = AsyncMock(return_value=5)

    result = await report_route.get_personal_report(current_user=socio_user)

    assert result["events_attended"] <= result["total_events"]
    assert result["total_events"] >= 5
