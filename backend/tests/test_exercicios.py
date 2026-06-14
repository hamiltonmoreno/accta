"""Unit tests — Ciclo do exercício (spec-ciclo §4, Art. 19.1/31.k/37) + F4 (AG).

Cobre a máquina de estados, o congelamento do `dre_snapshot`, a separação de
poderes (CF emite parecer mas não escreve transacções), a aprovação por
deliberação da AG, o aviso do 1.º trimestre, o orçamento estruturado e a
comparação orçado/realizado. Sem DB real (mock_db); colecções ligadas em-teste.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from models import (
    ExercicioAprovar,
    ExercicioReabrir,
    ExercicioCreate,
    ExercicioSubmeterAG,
    OrcamentoLinha,
    OrcamentoSubmit,
    ParecerSubmit,
    PlanoAtividade,
    PlanoSubmit,
    RelatorioContasSubmit,
    TransactionUpdate,
    User,
)
from routes import finances as fin_route
from routes import prestacao_contas as pc

pytestmark = pytest.mark.unit


def _user(role="socio", cargo="socio", privileges=None, uid=None) -> User:
    return User(
        id=uid or str(uuid.uuid4()),
        name=f"Test {role}",
        email=f"{uuid.uuid4().hex[:6]}@example.cv",
        role=role,
        status="ativo",
        cargo=cargo,
        privileges=privileges or [],
        consent_data=True,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


_DIRECAO = lambda: _user("socio", "dir_presidente")  # noqa: E731
_CF = lambda: _user("socio", "cf_presidente", ["view_finances_readonly"])  # noqa: E731
_MESA = lambda: _user("socio", "ag_presidente")  # noqa: E731
_TESOUREIRO = lambda: _user("financeiro", "dir_tesoureiro", ["manage_finances"])  # noqa: E731


def _coll(find_one=None, find_list=None):
    coll = MagicMock()
    coll.find_one = AsyncMock(return_value=find_one)
    coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="x"))
    coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    cur = MagicMock()
    cur.to_list = AsyncMock(return_value=find_list or [])
    cur.sort = MagicMock(return_value=cur)
    cur.limit = MagicMock(return_value=cur)
    coll.find = MagicMock(return_value=cur)
    return coll


def _wire(mock_db, *, ex=None, ex_list=None, delib=None, assembleia=True, doc_exists=True):
    mock_db.exercicios = _coll(find_one=ex, find_list=ex_list)
    mock_db.assembleia_deliberacoes = _coll(find_one=delib)
    mock_db.assembleias = _coll(find_one=({"id": "a1"} if assembleia else None))
    mock_db.documents.find_one = AsyncMock(return_value=({"id": "doc1"} if doc_exists else None))
    return mock_db


def _ex(status="aberto", ano=2026, **kw):
    base = {"id": "e1", "ano": ano, "status": status}
    base.update(kw)
    return base


# --------------------------------------------------------------------------- #
# Abrir
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestAbrir:
    async def test_direcao_abre_ok(self, mock_db):
        _wire(mock_db, ex=None)
        out = await pc.abrir_exercicio(ExercicioCreate(ano=2026), current_user=_DIRECAO())
        assert out.status == "aberto"
        assert out.ano == 2026

    async def test_duplicado_400(self, mock_db):
        _wire(mock_db, ex=_ex())
        with pytest.raises(HTTPException) as e:
            await pc.abrir_exercicio(ExercicioCreate(ano=2026), current_user=_DIRECAO())
        assert e.value.status_code == 400

    async def test_socio_403(self, mock_db):
        _wire(mock_db, ex=None)
        with pytest.raises(HTTPException) as e:
            await pc.abrir_exercicio(ExercicioCreate(ano=2026), current_user=_user("socio"))
        assert e.value.status_code == 403


# --------------------------------------------------------------------------- #
# Relatório (congela dre_snapshot) + aviso 1.º trimestre
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestRelatorio:
    async def test_congela_dre_snapshot(self, mock_db, monkeypatch):
        _wire(mock_db, ex=_ex(status="aberto"))
        snap = {"year": 2026, "total_receitas": 5000, "total_despesas": 2000}
        monkeypatch.setattr(pc, "compute_dre_report", AsyncMock(return_value=snap))
        out = await pc.submeter_relatorio(
            2026, RelatorioContasSubmit(document_id="doc1"), current_user=_DIRECAO()
        )
        assert out["status"] == "relatorio_submetido"
        set_ = mock_db.exercicios.update_one.call_args.args[1]["$set"]
        assert set_["relatorio_contas"]["dre_snapshot"] == snap
        # A ação promove o rascunho do documento associado a público (SEC) —
        # filtro ESCOPADO (só rascunho de prestação), só APÓS a persistência.
        mock_db.documents.update_one.assert_awaited_with(
            {"id": "doc1", "type": "prestacao_contas", "visibility": "direcao"},
            {"$set": {"visibility": "publico"}},
        )

    async def test_estado_errado_400(self, mock_db):
        _wire(mock_db, ex=_ex(status="parecer_emitido"))
        with pytest.raises(HTTPException) as e:
            await pc.submeter_relatorio(2026, RelatorioContasSubmit(document_id="doc1"), current_user=_DIRECAO())
        assert e.value.status_code == 400

    async def test_documento_inexistente_400(self, mock_db):
        _wire(mock_db, ex=_ex(status="aberto"), doc_exists=False)
        with pytest.raises(HTTPException) as e:
            await pc.submeter_relatorio(2026, RelatorioContasSubmit(document_id="x"), current_user=_DIRECAO())
        assert e.value.status_code == 400

    async def test_aviso_fora_prazo_1t(self, mock_db, monkeypatch):
        # 2025: prazo = 2026-03-31; hoje (2026-05-23) já passou → aviso.
        _wire(mock_db, ex=_ex(status="aberto", ano=2025))
        monkeypatch.setattr(pc, "compute_dre_report", AsyncMock(return_value={}))
        out = await pc.submeter_relatorio(2025, RelatorioContasSubmit(document_id="doc1"), current_user=_DIRECAO())
        assert out["aviso"] is not None

    async def test_sem_aviso_dentro_prazo(self, mock_db, monkeypatch):
        # 2026: prazo = 2027-03-31; ainda dentro do prazo → sem aviso.
        _wire(mock_db, ex=_ex(status="aberto", ano=2026))
        monkeypatch.setattr(pc, "compute_dre_report", AsyncMock(return_value={}))
        out = await pc.submeter_relatorio(2026, RelatorioContasSubmit(document_id="doc1"), current_user=_DIRECAO())
        assert out["aviso"] is None


# --------------------------------------------------------------------------- #
# Parecer do CF (separação de poderes)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestParecer:
    async def test_cf_emite_ok(self, mock_db):
        _wire(mock_db, ex=_ex(status="relatorio_submetido"))
        out = await pc.emitir_parecer(
            2026, ParecerSubmit(sentido="favoravel", texto="Contas em ordem."), current_user=_CF()
        )
        assert out["status"] == "parecer_emitido"

    async def test_estado_errado_400(self, mock_db):
        _wire(mock_db, ex=_ex(status="aberto"))
        with pytest.raises(HTTPException) as e:
            await pc.emitir_parecer(2026, ParecerSubmit(sentido="favoravel", texto="x"), current_user=_CF())
        assert e.value.status_code == 400

    async def test_direcao_nao_emite_parecer_403(self, mock_db):
        _wire(mock_db, ex=_ex(status="relatorio_submetido"))
        with pytest.raises(HTTPException) as e:
            await pc.emitir_parecer(
                2026, ParecerSubmit(sentido="favoravel", texto="x"), current_user=_DIRECAO()
            )
        assert e.value.status_code == 403

    async def test_cf_nao_escreve_transacao_403(self, mock_db):
        # Separação de poderes: o CF (view_finances_readonly) NÃO gere transacções.
        _wire(mock_db)
        with pytest.raises(HTTPException) as e:
            await fin_route.update_transaction(
                "t1", TransactionUpdate(amount=10.0), current_user=_CF()
            )
        assert e.value.status_code == 403


# --------------------------------------------------------------------------- #
# Submeter à AG + Aprovar (deliberação) — F4
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestSubmeterAG:
    async def test_mesa_submete_ok(self, mock_db):
        _wire(mock_db, ex=_ex(status="parecer_emitido"))
        out = await pc.submeter_ag(2026, ExercicioSubmeterAG(assembleia_id="a1"), current_user=_MESA())
        assert out["status"] == "em_aprovacao_ag"

    async def test_estado_errado_400(self, mock_db):
        _wire(mock_db, ex=_ex(status="relatorio_submetido"))
        with pytest.raises(HTTPException) as e:
            await pc.submeter_ag(2026, ExercicioSubmeterAG(assembleia_id="a1"), current_user=_MESA())
        assert e.value.status_code == 400

    async def test_assembleia_inexistente_400(self, mock_db):
        _wire(mock_db, ex=_ex(status="parecer_emitido"), assembleia=False)
        with pytest.raises(HTTPException) as e:
            await pc.submeter_ag(2026, ExercicioSubmeterAG(assembleia_id="a1"), current_user=_MESA())
        assert e.value.status_code == 400

    async def test_direcao_nao_submete_403(self, mock_db):
        _wire(mock_db, ex=_ex(status="parecer_emitido"))
        with pytest.raises(HTTPException) as e:
            await pc.submeter_ag(2026, ExercicioSubmeterAG(assembleia_id="a1"), current_user=_DIRECAO())
        assert e.value.status_code == 403


@pytest.mark.asyncio
class TestAprovar:
    async def test_aprova_com_deliberacao(self, mock_db):
        _wire(mock_db, ex=_ex(status="em_aprovacao_ag"), delib={"id": "d1", "aprovado": True})
        out = await pc.aprovar_exercicio(
            2026, ExercicioAprovar(deliberacao_id="d1", aprovado=True), current_user=_MESA()
        )
        assert out["status"] == "aprovado"
        set_ = mock_db.exercicios.update_one.call_args.args[1]["$set"]
        assert set_["deliberacao_id"] == "d1"
        assert set_["aprovado_em"] is not None

    async def test_deliberacao_nao_aprovada_400(self, mock_db):
        _wire(mock_db, ex=_ex(status="em_aprovacao_ag"), delib={"id": "d1", "aprovado": False})
        with pytest.raises(HTTPException) as e:
            await pc.aprovar_exercicio(
                2026, ExercicioAprovar(deliberacao_id="d1", aprovado=True), current_user=_MESA()
            )
        assert e.value.status_code == 400

    async def test_deliberacao_inexistente_400(self, mock_db):
        _wire(mock_db, ex=_ex(status="em_aprovacao_ag"), delib=None)
        with pytest.raises(HTTPException) as e:
            await pc.aprovar_exercicio(
                2026, ExercicioAprovar(deliberacao_id="d1", aprovado=True), current_user=_MESA()
            )
        assert e.value.status_code == 400

    async def test_rejeita_com_deliberacao_existente(self, mock_db):
        _wire(mock_db, ex=_ex(status="em_aprovacao_ag"), delib={"id": "d1", "aprovado": False})
        out = await pc.aprovar_exercicio(
            2026, ExercicioAprovar(deliberacao_id="d1", aprovado=False), current_user=_MESA()
        )
        assert out["status"] == "rejeitado"

    async def test_aprova_deliberacao_mesma_assembleia_ok(self, mock_db):
        _wire(
            mock_db,
            ex=_ex(status="em_aprovacao_ag", assembleia_id="a1"),
            delib={"id": "d1", "aprovado": True, "assembleia_id": "a1"},
        )
        out = await pc.aprovar_exercicio(
            2026, ExercicioAprovar(deliberacao_id="d1", aprovado=True), current_user=_MESA()
        )
        assert out["status"] == "aprovado"

    async def test_deliberacao_de_outra_assembleia_400(self, mock_db):
        # Deliberação aprovada da AG "a2", mas o exercício foi submetido à AG
        # "a1" — não se aprova com o voto de outra assembleia (Art. 19.1/37).
        _wire(
            mock_db,
            ex=_ex(status="em_aprovacao_ag", assembleia_id="a1"),
            delib={"id": "d1", "aprovado": True, "assembleia_id": "a2"},
        )
        with pytest.raises(HTTPException) as e:
            await pc.aprovar_exercicio(
                2026, ExercicioAprovar(deliberacao_id="d1", aprovado=True), current_user=_MESA()
            )
        assert e.value.status_code == 400

    async def test_estado_errado_400(self, mock_db):
        _wire(mock_db, ex=_ex(status="parecer_emitido"), delib={"id": "d1", "aprovado": True})
        with pytest.raises(HTTPException) as e:
            await pc.aprovar_exercicio(
                2026, ExercicioAprovar(deliberacao_id="d1"), current_user=_MESA()
            )
        assert e.value.status_code == 400


# --------------------------------------------------------------------------- #
# Orçamento estruturado + execução (orçado vs realizado)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestOrcamento:
    async def test_submete_linhas_ano_default(self, mock_db):
        _wire(mock_db, ex=_ex(status="relatorio_submetido"))
        out = await pc.submeter_orcamento(
            2026,
            OrcamentoSubmit(
                document_id="doc1",
                linhas=[
                    OrcamentoLinha(categoria="quotas", tipo="receita", valor_previsto=1000),
                    OrcamentoLinha(categoria="operacional", tipo="despesa", valor_previsto=500),
                ],
            ),
            current_user=_DIRECAO(),
        )
        assert out["orcamento"]["ano_orcamento"] == 2027  # default = ano + 1
        assert len(out["orcamento"]["linhas"]) == 2
        # A ação promove o rascunho do documento associado a 'socios' (SEC) —
        # filtro ESCOPADO (só rascunho de prestação), só APÓS a persistência.
        mock_db.documents.update_one.assert_awaited_with(
            {"id": "doc1", "type": "prestacao_contas", "visibility": "direcao"},
            {"$set": {"visibility": "socios"}},
        )

    async def test_categoria_invalida_400(self, mock_db):
        _wire(mock_db, ex=_ex(status="relatorio_submetido"))
        with pytest.raises(HTTPException) as e:
            await pc.submeter_orcamento(
                2026,
                OrcamentoSubmit(linhas=[OrcamentoLinha(categoria="inexistente", tipo="receita", valor_previsto=10)]),
                current_user=_DIRECAO(),
            )
        assert e.value.status_code == 400

    async def test_categoria_invalida_nao_promove_documento(self, mock_db):
        # SEC (bug_006): orçamento com document_id mas categoria INVÁLIDA →
        # 400, e o documento NÃO pode ter sido promovido (a promoção corre só
        # APÓS a validação + persistência, nunca antes).
        _wire(mock_db, ex=_ex(status="relatorio_submetido"))
        with pytest.raises(HTTPException) as e:
            await pc.submeter_orcamento(
                2026,
                OrcamentoSubmit(
                    document_id="doc1",
                    linhas=[OrcamentoLinha(categoria="inexistente", tipo="receita", valor_previsto=10)],
                ),
                current_user=_DIRECAO(),
            )
        assert e.value.status_code == 400
        mock_db.documents.update_one.assert_not_awaited()  # rascunho intacto
        mock_db.exercicios.update_one.assert_not_awaited()  # nada persistido

    async def test_nao_editavel_apos_ag_400(self, mock_db):
        _wire(mock_db, ex=_ex(status="em_aprovacao_ag"))
        with pytest.raises(HTTPException) as e:
            await pc.submeter_orcamento(
                2026,
                OrcamentoSubmit(linhas=[OrcamentoLinha(categoria="quotas", tipo="receita", valor_previsto=10)]),
                current_user=_DIRECAO(),
            )
        assert e.value.status_code == 400

    async def test_execucao_orcado_vs_realizado(self, mock_db, monkeypatch):
        orc = {
            "linhas": [
                {"categoria": "quotas", "tipo": "receita", "valor_previsto": 1000},
                {"categoria": "operacional", "tipo": "despesa", "valor_previsto": 500},
            ],
            "ano_orcamento": 2027,
        }
        _wire(mock_db, ex=_ex(status="aprovado", orcamento=orc))
        monkeypatch.setattr(
            pc,
            "compute_financial_summary",
            AsyncMock(
                return_value={
                    "receitas_por_categoria": {"quotas": 800},
                    "despesas_por_categoria": {"operacional": 600},
                }
            ),
        )
        out = await pc.orcamento_execucao(2026, current_user=_TESOUREIRO())
        by_cat = {linha["categoria"]: linha for linha in out["linhas"]}
        assert by_cat["quotas"]["orcado"] == 1000 and by_cat["quotas"]["realizado"] == 800
        assert by_cat["quotas"]["desvio"] == -200
        assert by_cat["operacional"]["desvio"] == 100

    async def test_execucao_sem_orcamento_400(self, mock_db):
        _wire(mock_db, ex=_ex(status="aberto"))
        with pytest.raises(HTTPException) as e:
            await pc.orcamento_execucao(2026, current_user=_TESOUREIRO())
        assert e.value.status_code == 400


# --------------------------------------------------------------------------- #
# Plano de atividades estruturado
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestPlano:
    async def test_submete_atividades(self, mock_db):
        _wire(mock_db, ex=_ex(status="relatorio_submetido"))
        out = await pc.submeter_plano(
            2026,
            PlanoSubmit(
                atividades=[
                    PlanoAtividade(titulo="Formacao contabilistica", trimestre=2),
                    PlanoAtividade(titulo="Encontro anual"),
                ]
            ),
            current_user=_DIRECAO(),
        )
        assert len(out["plano_atividades"]["atividades"]) == 2
        assert out["plano_atividades"]["atividades"][0]["estado"] == "planeada"


# --------------------------------------------------------------------------- #
# Reabrir
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
class TestReabrir:
    async def test_reabre_rejeitado(self, mock_db):
        _wire(mock_db, ex=_ex(status="rejeitado"))
        out = await pc.reabrir_exercicio(2026, current_user=_MESA())
        assert out["status"] == "reaberto"

    async def test_aberto_nao_reabre_400(self, mock_db):
        _wire(mock_db, ex=_ex(status="aberto"))
        with pytest.raises(HTTPException) as e:
            await pc.reabrir_exercicio(2026, current_user=_MESA())
        assert e.value.status_code == 400

    async def test_reabre_aprovado_sem_delib_400(self, mock_db):
        # Reabrir um exercício aprovado exige deliberação da AG.
        _wire(mock_db, ex=_ex(status="aprovado", assembleia_id="a1"))
        with pytest.raises(HTTPException) as e:
            await pc.reabrir_exercicio(2026, current_user=_MESA())
        assert e.value.status_code == 400

    async def test_reabre_aprovado_com_delib_ok(self, mock_db):
        _wire(
            mock_db,
            ex=_ex(status="aprovado", assembleia_id="a1"),
            delib={"id": "d1", "aprovado": True, "assembleia_id": "a1"},
        )
        out = await pc.reabrir_exercicio(
            2026, ExercicioReabrir(deliberacao_id="d1"), current_user=_MESA()
        )
        assert out["status"] == "reaberto"

    async def test_reabre_aprovado_delib_outra_assembleia_400(self, mock_db):
        _wire(
            mock_db,
            ex=_ex(status="aprovado", assembleia_id="a1"),
            delib={"id": "d1", "aprovado": True, "assembleia_id": "OUTRA"},
        )
        with pytest.raises(HTTPException) as e:
            await pc.reabrir_exercicio(
                2026, ExercicioReabrir(deliberacao_id="d1"), current_user=_MESA()
            )
        assert e.value.status_code == 400
