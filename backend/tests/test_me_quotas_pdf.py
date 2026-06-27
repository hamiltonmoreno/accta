"""Testes do endpoint GET /finances/me/quotas/pdf (spec 007 — carteira em PDF).

Unit/in-process: chama a função de rota diretamente com o `mock_db` (que faz patch
de `routes.finances.db`). Sem servidor/DB. O 401 a não-autenticados é fornecido pela
dependência partilhada `get_current_user` (testada na suite de auth) — aqui
verifica-se estruturalmente que o endpoint a declara.
"""
import inspect
from unittest.mock import AsyncMock

import routes.finances as finances
from auth import get_current_user


async def _read_body(resp) -> bytes:
    return b"".join([chunk async for chunk in resp.body_iterator])


def _wire_quotas(mock_db, items):
    # find(query, proj).sort("date", -1).to_list(None) → items
    mock_db.transactions.find.return_value.to_list = AsyncMock(return_value=items)


class TestMeQuotasPdf:
    async def test_export_own_quotas_pdf(self, mock_db, socio_user):
        items = [
            {"id": "1", "date": "2026-03-01T00:00:00+00:00", "description": "Quota Marco",
             "category": "quotas", "amount": 1000},
            {"id": "2", "date": "2026-01-15T00:00:00+00:00", "description": "Joia de admissao",
             "category": "joias", "amount": 5000},
        ]
        _wire_quotas(mock_db, items)

        resp = await finances.export_my_quotas_pdf(current_user=socio_user)

        # Headers de download + corpo é mesmo um PDF.
        assert resp.media_type == "application/pdf"
        cd = resp.headers["content-disposition"]
        assert cd.startswith("attachment;") and cd.endswith(".pdf")
        body = await _read_body(resp)
        assert body.startswith(b"%PDF")

        # Own-data: a query filtra SEMPRE pelo próprio user_id, categoria quota/jóia.
        # Não há parâmetro de "outro sócio" — impossível exportar a de terceiros.
        called_query = mock_db.transactions.find.call_args.args[0]
        assert called_query["user_id"] == socio_user.id
        assert called_query["type"] == "receita"
        assert called_query["category"] == {"$in": ["quotas", "joias"]}

    async def test_empty_carteira_still_valid_pdf(self, mock_db, socio_user):
        _wire_quotas(mock_db, [])
        resp = await finances.export_my_quotas_pdf(current_user=socio_user)
        assert resp.media_type == "application/pdf"
        body = await _read_body(resp)
        assert body.startswith(b"%PDF")

    def test_endpoint_protected_by_auth(self):
        # 401 a não-autenticados é garantido pela dependência partilhada
        # get_current_user (mesma de /me/quotas e de todo o portal).
        dep = inspect.signature(finances.export_my_quotas_pdf).parameters["current_user"].default
        assert getattr(dep, "dependency", None) is get_current_user
