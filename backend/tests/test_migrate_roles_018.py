"""Testes da migração de roles legados (spec 018, US2 — scripts/migrate_roles_018.py).

Cobre a regra R3 nos dois ramos, união sem duplicados, idempotência, dry-run
sem escrita, `--restore` (M3), seeds com os privilégios da matriz e o edge
case de convites pendentes com role legado.
"""

import importlib.util
import json
import pathlib
from unittest.mock import AsyncMock

import pytest

from governance import LEGACY_ROLE_SEEDS

_SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "migrate_roles_018.py"
_spec = importlib.util.spec_from_file_location("migrate_roles_018", _SCRIPT)
mig = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mig)

pytestmark = pytest.mark.unit

SEED_IDS = {"financeiro": "seed-fin", "moderador": "seed-mod"}


class TestPlanUserMigration:
    def test_financeiro_sem_extras_vai_para_seed(self):
        p = mig.plan_user_migration(
            {"id": "u1", "role": "financeiro", "privileges": ["manage_finances"]}, SEED_IDS
        )
        assert p["regra"] == "seed"
        assert p["set"]["role"] == "socio"
        assert p["set"]["privileges"] == LEGACY_ROLE_SEEDS["financeiro"]["privileges"]
        assert p["set"]["custom_role_id"] == "seed-fin"

    def test_moderador_sem_privilegios_vai_para_seed(self):
        p = mig.plan_user_migration({"id": "u2", "role": "moderador", "privileges": []}, SEED_IDS)
        assert p["regra"] == "seed"
        assert p["set"]["privileges"] == ["moderate_content"]
        assert p["set"]["custom_role_id"] == "seed-mod"

    def test_extras_manuais_viram_privilegios_diretos_sem_funcao(self):
        # financeiro com manage_events extra: união, SEM custom_role_id (R3 —
        # preserva o invariante de propagação da spec 017)
        p = mig.plan_user_migration(
            {"id": "u3", "role": "financeiro", "privileges": ["manage_finances", "manage_events"]},
            SEED_IDS,
        )
        assert p["regra"] == "privilegios_diretos"
        assert p["set"]["custom_role_id"] is None
        assert set(p["set"]["privileges"]) == {"manage_finances", "manage_users", "manage_events"}

    def test_uniao_sem_duplicados(self):
        p = mig.plan_user_migration(
            {"id": "u4", "role": "moderador", "privileges": ["moderate_content", "manage_events"]},
            SEED_IDS,
        )
        privs = p["set"]["privileges"]
        assert len(privs) == len(set(privs))
        assert set(privs) == {"moderate_content", "manage_events"}

    @pytest.mark.parametrize("role", ["admin", "socio", None, "xpto"])
    def test_roles_nao_legados_sao_no_op(self, role):
        assert mig.plan_user_migration({"id": "u5", "role": role, "privileges": []}, SEED_IDS) is None

    def test_idempotente_apos_migrar(self):
        doc = {"id": "u6", "role": "financeiro", "privileges": []}
        p = mig.plan_user_migration(doc, SEED_IDS)
        migrated = {**doc, **p["set"]}
        assert mig.plan_user_migration(migrated, SEED_IDS) is None

    def test_pendente_convite_tambem_migra(self):
        # edge case da spec: convite pendente com role legado migra na mesma
        p = mig.plan_user_migration(
            {"id": "u7", "role": "moderador", "privileges": [], "status": "pendente_convite"},
            SEED_IDS,
        )
        assert p is not None and p["set"]["role"] == "socio"


class TestEnsureSeeds:
    async def test_cria_seeds_em_falta_com_privilegios_da_matriz(self, mock_db):
        mock_db.custom_roles.find_one = AsyncMock(return_value=None)
        inserted = []
        mock_db.custom_roles.insert_one = AsyncMock(side_effect=lambda d: inserted.append(d))
        seed_ids = await mig.ensure_seeds(mock_db)
        assert set(seed_ids) == {"financeiro", "moderador"}
        by_name = {d["name"]: d for d in inserted}
        assert by_name["Financeiro"]["privileges"] == LEGACY_ROLE_SEEDS["financeiro"]["privileges"]
        assert by_name["Moderador"]["privileges"] == ["moderate_content"]
        assert all(d["created_by"] == "system" for d in inserted)

    async def test_reutiliza_seeds_existentes(self, mock_db):
        mock_db.custom_roles.find_one = AsyncMock(
            side_effect=[{"id": "fin-1", "name": "Financeiro"}, {"id": "mod-1", "name": "Moderador"}]
        )
        seed_ids = await mig.ensure_seeds(mock_db)
        assert seed_ids == {"financeiro": "fin-1", "moderador": "mod-1"}
        mock_db.custom_roles.insert_one.assert_not_awaited()


def _users_cursor(mock_db, docs):
    cursor = mock_db.users.find.return_value
    cursor.to_list = AsyncMock(return_value=docs)


class TestMigrateDryRunAndApply:
    async def test_dry_run_nao_escreve(self, mock_db, tmp_path, monkeypatch):
        mock_db.custom_roles.find_one = AsyncMock(return_value=None)
        _users_cursor(mock_db, [{"id": "u1", "role": "financeiro", "privileges": []}])
        await mig.migrate(mock_db, apply=False, backup_path=str(tmp_path / "b.json"))
        mock_db.users.update_one.assert_not_awaited()
        mock_db.custom_roles.insert_one.assert_not_awaited()
        assert not (tmp_path / "b.json").exists()

    async def test_apply_migra_faz_backup_e_audita(self, mock_db, tmp_path, monkeypatch):
        audit = AsyncMock()
        monkeypatch.setattr("helpers.create_audit_log", audit)
        mock_db.custom_roles.find_one = AsyncMock(return_value=None)
        _users_cursor(
            mock_db,
            [{"id": "u1", "email": "f@x.cv", "role": "financeiro", "privileges": ["manage_finances"]}],
        )
        backup_path = tmp_path / "backup.json"
        await mig.migrate(mock_db, apply=True, backup_path=str(backup_path))

        mock_db.users.update_one.assert_awaited_once()
        (filt, update), _ = mock_db.users.update_one.await_args
        assert filt == {"id": "u1"}
        assert update["$set"]["role"] == "socio"
        assert update["$set"]["privileges"] == LEGACY_ROLE_SEEDS["financeiro"]["privileges"]

        backup = json.loads(backup_path.read_text(encoding="utf-8"))
        assert backup == [
            {
                "id": "u1",
                "email": "f@x.cv",
                "role": "financeiro",
                "privileges": ["manage_finances"],
                "custom_role_id": None,
            }
        ]

        details = audit.await_args.kwargs["details"]
        assert audit.await_args.args[:2] == ("system", "role_model_migrated")
        assert details["before"]["role"] == "financeiro"
        assert details["after"]["role"] == "socio"
        assert details["regra"] == "seed"


class TestRestore:
    async def test_restore_repoe_estado_before(self, mock_db, tmp_path, monkeypatch):
        audit = AsyncMock()
        monkeypatch.setattr("helpers.create_audit_log", audit)
        backup_path = tmp_path / "backup.json"
        backup_path.write_text(
            json.dumps(
                [
                    {
                        "id": "u1",
                        "email": "f@x.cv",
                        "role": "financeiro",
                        "privileges": ["manage_finances"],
                        "custom_role_id": None,
                    }
                ]
            ),
            encoding="utf-8",
        )
        await mig.restore(mock_db, str(backup_path))
        (filt, update), _ = mock_db.users.update_one.await_args
        assert filt == {"id": "u1"}
        assert update["$set"] == {
            "role": "financeiro",
            "privileges": ["manage_finances"],
            "custom_role_id": None,
        }
        assert audit.await_args.args[:2] == ("system", "role_model_migration_restored")
