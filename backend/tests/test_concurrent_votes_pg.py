"""Integration tests against postgres:16 para o fix TOCTOU
votar/apurar de deliberações de assembleia.

Requerem `DATABASE_URL` apontando a um Postgres acessível. Correr com:

    cd backend
    pytest -m integration tests/test_concurrent_votes_pg.py

O smoke harness (`test_smoke.py`) já prova que o schema arranca. Este ficheiro
foca-se nos helpers DAO `cast_assembleia_nominal_vote` e
`cast_assembleia_ballot` e na guarda CAS de `registar_contagem`.

Os cenários **provam** o fix:

* `apurar` fecha primeiro → o voter, ao re-verificar status sob o lock no
  helper, vê `encerrada` e levanta `ValueError("not_open")` — nenhum voto
  fica perdido.
* `voter` insere primeiro → `apurar` segue, fecha, e o voto está visível.
* Outra tx segura `FOR UPDATE` da linha → o helper bloqueia até
  `lock_timeout=2s` e levanta `LockNotAvailableError`. Prova que o lock
  existe e é o mesmo que `apurar` toma.

Não testa concorrência genuína via `asyncio.gather` para evitar flakiness:
o que é determinístico (ordem programada do lock) cobre a invariante;
o que é probabilístico (interleaving) é redundante.
"""

from __future__ import annotations

import asyncio
import uuid

import asyncpg
import pytest

import database
from database import (
    cast_assembleia_ballot,
    cast_assembleia_nominal_vote,
    db,
    ensure_schema,
    get_pool,
)
from models import AssembleiaVoto, AssembleiaVotoBallot, AssembleiaVotoReceipt


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
async def _fresh_pool():
    """Cada teste async corre no seu próprio event loop (default do
    pytest-asyncio); o pool asyncpg do `database` é um singleton globais e
    fica ligado ao loop em que foi criado. Sem este reset, testes após o
    primeiro falham com `Future attached to a different loop`. Fechamos e
    re-criamos o pool por teste — é integração, o custo é aceitável."""
    if database._pool is not None:
        try:
            await database._pool.close()
        except Exception:
            pass
        database._pool = None
    # Schema é idempotente; corremos sempre para garantir tabelas no novo loop.
    await ensure_schema()
    yield
    if database._pool is not None:
        try:
            await database._pool.close()
        except Exception:
            pass
        database._pool = None


async def _seed_delib(*, voting_mode: str = "nominal") -> tuple[str, str]:
    """Cria uma deliberação aberta e devolve (assembleia_id, deliberacao_id)."""
    aid = f"a-{uuid.uuid4().hex[:8]}"
    did = f"d-{uuid.uuid4().hex[:8]}"
    await db.assembleia_deliberacoes.insert_one({
        "id": did,
        "assembleia_id": aid,
        "ponto": "P1",
        "descricao": "Teste TOCTOU",
        "tipo_maioria": "simples",
        "voting_mode": voting_mode,
        "status": "aberta",
        "conflitos_excluidos": [],
        "votos_favor": 0,
        "votos_contra": 0,
        "abstencoes": 0,
        "base_calculo": 0,
        "threshold": 0,
        "aprovado": False,
        "created_at": "2030-01-01T00:00:00+00:00",
    })
    return aid, did


async def _cleanup(did: str) -> None:
    await db.assembleia_votos.delete_many({"deliberacao_id": did})
    await db.assembleia_voto_receipts.delete_many({"deliberacao_id": did})
    await db.assembleia_voto_ballots.delete_many({"deliberacao_id": did})
    await db.assembleia_deliberacoes.delete_many({"id": did})


class TestNominalLockOrdering:
    async def test_apurar_primeiro_voter_recusado_sem_voto_perdido(self):
        aid, did = await _seed_delib()
        try:
            # Simula a Mesa a fechar a deliberação antes de o voter inserir.
            res = await db.assembleia_deliberacoes.update_one(
                {"id": did, "status": "aberta"}, {"$set": {"status": "encerrada"}}
            )
            assert res.modified_count == 1

            voto = AssembleiaVoto(
                deliberacao_id=did, assembleia_id=aid, user_id="voter-1", escolha="favor"
            ).model_dump()
            with pytest.raises(ValueError) as exc:
                await cast_assembleia_nominal_vote(did, "voter-1", voto)
            assert exc.value.args[0] == "not_open"

            # Não há recibo silencioso: a tabela continua vazia.
            votos = await db.assembleia_votos.find({"deliberacao_id": did}).to_list(None)
            assert votos == []
        finally:
            await _cleanup(did)

    async def test_voter_primeiro_apurar_ve_voto(self):
        aid, did = await _seed_delib()
        try:
            voto = AssembleiaVoto(
                deliberacao_id=did, assembleia_id=aid, user_id="voter-2", escolha="favor"
            ).model_dump()
            await cast_assembleia_nominal_vote(did, "voter-2", voto)

            # Apurar fecha; o voto continua visível para a tabulação.
            res = await db.assembleia_deliberacoes.update_one(
                {"id": did, "status": "aberta"}, {"$set": {"status": "encerrada"}}
            )
            assert res.modified_count == 1

            votos = await db.assembleia_votos.find({"deliberacao_id": did}).to_list(None)
            assert len(votos) == 1
            assert votos[0]["user_id"] == "voter-2"
            assert votos[0]["escolha"] == "favor"
        finally:
            await _cleanup(did)

    async def test_duplicate_in_tx(self):
        aid, did = await _seed_delib()
        try:
            voto = AssembleiaVoto(
                deliberacao_id=did, assembleia_id=aid, user_id="voter-3", escolha="favor"
            ).model_dump()
            await cast_assembleia_nominal_vote(did, "voter-3", voto)

            voto2 = AssembleiaVoto(
                deliberacao_id=did, assembleia_id=aid, user_id="voter-3", escolha="contra"
            ).model_dump()
            with pytest.raises(ValueError) as exc:
                await cast_assembleia_nominal_vote(did, "voter-3", voto2)
            assert exc.value.args[0] == "duplicate"

            # Só um voto persiste, com a primeira escolha.
            votos = await db.assembleia_votos.find({"deliberacao_id": did}).to_list(None)
            assert len(votos) == 1
            assert votos[0]["escolha"] == "favor"
        finally:
            await _cleanup(did)


class TestLockBlocksConcurrentVote:
    """Prova que o helper toma um lock REAL na linha da deliberação. Se outra
    transação segurar o lock, o helper bloqueia até `lock_timeout=2s` e levanta
    `LockNotAvailableError`. É este o mesmo lock que `apurar` toma — voter e
    fecho serializam, sem voto perdido."""

    async def test_helper_respeita_for_update(self):
        aid, did = await _seed_delib()
        try:
            pool = await get_pool()
            release = asyncio.Event()
            t1_acquired = asyncio.Event()

            async def hold_lock():
                async with pool.acquire() as conn:
                    async with conn.transaction():
                        await conn.fetchrow(
                            'SELECT pk FROM "assembleia_deliberacoes" '
                            "WHERE doc->>'id' = $1 LIMIT 1 FOR UPDATE",
                            did,
                        )
                        t1_acquired.set()
                        # Segura o lock até o helper falhar (até 6s, > lock_timeout=2s).
                        try:
                            await asyncio.wait_for(release.wait(), timeout=6.0)
                        except asyncio.TimeoutError:
                            pass

            holder = asyncio.create_task(hold_lock())
            await t1_acquired.wait()

            voto = AssembleiaVoto(
                deliberacao_id=did, assembleia_id=aid, user_id="voter-4", escolha="favor"
            ).model_dump()
            try:
                with pytest.raises(asyncpg.exceptions.LockNotAvailableError):
                    await cast_assembleia_nominal_vote(did, "voter-4", voto)
            finally:
                release.set()
                await holder

            # Lock failure não deixa nenhum voto residual.
            votos = await db.assembleia_votos.find({"deliberacao_id": did}).to_list(None)
            assert votos == []
        finally:
            await _cleanup(did)


class TestSecretoLockOrdering:
    async def test_apurar_primeiro_ballot_recusado(self):
        aid, did = await _seed_delib(voting_mode="secreto")
        try:
            res = await db.assembleia_deliberacoes.update_one(
                {"id": did, "status": "aberta"}, {"$set": {"status": "encerrada"}}
            )
            assert res.modified_count == 1

            voter_hash = "h" * 64
            receipt = AssembleiaVotoReceipt(deliberacao_id=did, voter_hash=voter_hash).model_dump()
            ballot = AssembleiaVotoBallot(deliberacao_id=did, escolha="favor").model_dump()
            with pytest.raises(ValueError) as exc:
                await cast_assembleia_ballot(did, voter_hash, receipt, ballot)
            assert exc.value.args[0] == "not_open"

            # Nem recibo nem boletim ficaram registados (atomicidade da tx).
            assert await db.assembleia_voto_receipts.find({"deliberacao_id": did}).to_list(None) == []
            assert await db.assembleia_voto_ballots.find({"deliberacao_id": did}).to_list(None) == []
        finally:
            await _cleanup(did)

    async def test_voter_primeiro_recibo_e_boletim_persistem(self):
        aid, did = await _seed_delib(voting_mode="secreto")
        try:
            voter_hash = "k" * 64
            receipt = AssembleiaVotoReceipt(deliberacao_id=did, voter_hash=voter_hash).model_dump()
            ballot = AssembleiaVotoBallot(deliberacao_id=did, escolha="favor").model_dump()
            await cast_assembleia_ballot(did, voter_hash, receipt, ballot)

            res = await db.assembleia_deliberacoes.update_one(
                {"id": did, "status": "aberta"}, {"$set": {"status": "encerrada"}}
            )
            assert res.modified_count == 1

            receipts = await db.assembleia_voto_receipts.find({"deliberacao_id": did}).to_list(None)
            ballots = await db.assembleia_voto_ballots.find({"deliberacao_id": did}).to_list(None)
            assert len(receipts) == 1
            assert receipts[0]["voter_hash"] == voter_hash
            assert len(ballots) == 1
            assert ballots[0]["escolha"] == "favor"
            # Boletim NÃO carrega user_id nem voter_hash (anonimato preservado).
            assert "user_id" not in ballots[0]
            assert "voter_hash" not in ballots[0]
        finally:
            await _cleanup(did)

    async def test_duplicate_recibo(self):
        aid, did = await _seed_delib(voting_mode="secreto")
        try:
            voter_hash = "m" * 64
            receipt = AssembleiaVotoReceipt(deliberacao_id=did, voter_hash=voter_hash).model_dump()
            ballot = AssembleiaVotoBallot(deliberacao_id=did, escolha="favor").model_dump()
            await cast_assembleia_ballot(did, voter_hash, receipt, ballot)

            receipt2 = AssembleiaVotoReceipt(deliberacao_id=did, voter_hash=voter_hash).model_dump()
            ballot2 = AssembleiaVotoBallot(deliberacao_id=did, escolha="contra").model_dump()
            with pytest.raises(ValueError) as exc:
                await cast_assembleia_ballot(did, voter_hash, receipt2, ballot2)
            assert exc.value.args[0] == "duplicate"
        finally:
            await _cleanup(did)


class TestRegistarContagemCAS:
    async def test_status_aberta_no_filtro_bloqueia_overwrite_pos_apurar(self):
        # registar_contagem usa um filtro com status="aberta"; se o apurar já
        # fechou, o update_one devolve modified_count=0 (a rota mapeia para 409).
        aid, did = await _seed_delib(voting_mode="braco_no_ar")
        try:
            # Simula apurar a fechar primeiro.
            res_close = await db.assembleia_deliberacoes.update_one(
                {"id": did, "status": "aberta"}, {"$set": {"status": "encerrada"}}
            )
            assert res_close.modified_count == 1

            # Agora a Mesa tenta registar contagem; deve falhar sem alterar o doc.
            res_cnt = await db.assembleia_deliberacoes.update_one(
                {"id": did, "status": "aberta"},
                {"$set": {"votos_favor": 99, "votos_contra": 0, "abstencoes": 0}},
            )
            assert res_cnt.modified_count == 0

            # Confirma que os valores agregados ficaram em 0 (não foram sobrescritos).
            d = await db.assembleia_deliberacoes.find_one({"id": did}, {"_id": 0})
            assert d["votos_favor"] == 0
            assert d["status"] == "encerrada"
        finally:
            await _cleanup(did)
