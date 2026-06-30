"""Stats do painel (GET /stats): as contagens de sócios excluem contas técnicas.

Regressão: admin@controlador.cv (account_type="technical") não pode ser contado
como sócio em «Total Socios» / «Socios Ativos» no painel.
"""

import routes.stats as stats_module

_MEMBER_FILTER = {"$or": [{"account_type": "member"}, {"account_type": {"$exists": False}}]}


async def test_stats_socio_counts_exclude_technical(mock_db, admin_user):
    """total_users/active_users só contam sócios reais (account_type "member" ou
    ausente) — contas technical ficam de fora das contagens do painel."""
    result = await stats_module.get_statistics(current_user=admin_user)

    calls = mock_db.users.count_documents.call_args_list
    assert len(calls) == 2, "esperadas 2 contagens de users (total + ativos)"
    # «Total Socios» → filtro de membros (exclui technical)
    assert calls[0].args[0] == _MEMBER_FILTER
    # «Socios Ativos» → ativo AND membro
    assert calls[1].args[0] == {"$and": [{"status": "ativo"}, _MEMBER_FILTER]}
    # o endpoint continua a devolver as três chaves esperadas pelo painel
    assert set(result) == {"total_users", "active_users", "active_events"}
