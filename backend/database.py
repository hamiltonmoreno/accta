"""
Postgres/Supabase data layer for the ACCTA Portal.

Migration note (MongoDB -> Supabase): this module replaces the previous
Motor/MongoDB driver with a thin async DAO over PostgreSQL. Each logical
collection is a table `(pk bigserial primary key, doc jsonb not null)`.
The DAO faithfully emulates the *exact* subset of the Mongo API the codebase
uses, so route handlers, `auth.py`, `helpers.py`, the Pydantic models and the
mocked test suite need **zero** changes — they keep calling
`db.<collection>.find_one(...)`, `.find(...).sort(...).to_list(...)`,
`.insert_one(...)`, `.update_one(..., {"$set"/"$inc"/"$push"/"$pull": ...})`,
`.delete_*`, `.count_documents(...)` and `.aggregate([...])` as before.

Why jsonb document emulation instead of a relational remodel: the access
pattern is uniform and schema-flexible (Pydantic models with `extra="ignore"`,
documents serialized via `model_dump()`), and the app's logical key is the
application-generated `id` UUID string — the Mongo `_id` is always excluded
via `{"_id": 0}` projection. A faithful emulator keeps the blast radius to
this one file (Simplicity First / Minimal Impact) while still running on
real Postgres.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

import asyncpg
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env", override=False)

logger = logging.getLogger(__name__)

# Postgres/Supabase connection string. Supabase: use the connection pooler
# URI (port 6543, transaction mode) in production. `statement_cache_size=0`
# is required when talking to pgbouncer in transaction mode.
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is required (PostgreSQL/Supabase connection string). Set it in backend/.env"
    )

UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# All logical collections -> tables. 30 with Pydantic models + 7 without.
COLLECTIONS: tuple[str, ...] = (
    "users",
    "invoices",
    "polls",
    "user_votes",
    "posts",
    "documents",
    "benefits",
    "wall_posts",
    "wall_comments",
    "events",
    "transactions",
    "finance_settings",
    "projects",
    "project_tasks",
    "project_comments",
    "project_expenses",
    "project_milestones",
    "gallery_albums",
    "gallery_photos",
    "notifications",
    "audit_logs",
    # governança estatutária (spec-governanca):
    "assembleias",
    "assembleia_presencas",
    "assembleia_deliberacoes",
    # sessão da AG "ao vivo" (spec-sessao-assembleia-ao-vivo):
    "assembleia_palavra",
    "assembleia_votos",  # voto nominal (registado por nome)
    "assembleia_voto_receipts",  # voto secreto: recibo (HMAC)
    "assembleia_voto_ballots",  # voto secreto: boletim (sem user_id)
    "assembleia_mocoes",  # F4 — moções/requerimentos/recomendações em sessão
    "assembleia_expediente",  # F5 — antes da OT (correspondência + votos de louvor/etc)
    "assembleia_convidados",  # F6 — não-membros autorizados a assistir/intervir
    "eleicoes",
    "eleicao_listas",
    "eleicao_voter_receipts",
    "eleicao_ballots",
    "sancoes",
    "finance_settings_history",
    # controlos financeiros estatutários (spec-controlos §4.1): co-aprovação
    "atos",
    "page_banners",
    "brand_settings",
    # voz e participação do sócio (spec-voz-participacao-socio):
    "patrocinios",
    "honorarios_nominations",
    "peticoes",
    "peticao_assinaturas",
    "propostas_ag",
    "reclamacoes",
    "esclarecimentos",
    # ciclo anual de prestação de contas (spec-ciclo-prestacao-contas):
    "exercicios",
    "balancetes",
    "regulamentos",
    "regulamento_versoes",
    # comunicados (spec-comunicados-email):
    "comunicados",
    # ranking de atuação do sócio (spec-ranking-socio):
    "member_scores",
    "ranking_ajustes",
    "ranking_settings",
    # fins profissionais Cat 5 F2 (spec-fins-profissionais §6/§8):
    "formacoes",
    "publicacoes",
    # fins profissionais Cat 5 F3 (spec-fins-profissionais §5/§7):
    "defesa_profissional",
    "relacoes_externas",
    # no Pydantic model — schema derived from usage:
    "password_resets",
    "tokens_revoked",
    "login_attempts",
    "document_accesses",
    "benefit_validations",
    "benefit_partners",
)
_COLLECTION_SET = frozenset(COLLECTIONS)

# Fields that must round-trip as `datetime` because app code does date
# arithmetic on them (helpers.is_account_locked does `oldest[...] + timedelta`).
# Everything else keeps datetimes as ISO-8601 strings, matching the existing
# code that already calls `.isoformat()` before insert.
_DATETIME_FIELDS: dict[str, frozenset[str]] = {
    "login_attempts": frozenset({"attempted_at"}),
    "tokens_revoked": frozenset({"expires_at", "revoked_at"}),
}

# Tables that grew unbounded under Mongo TTL indexes. Without Mongo TTL we
# purge opportunistically on insert (cheap, index-backed). pg_cron is also
# scheduled in ensure_schema() when the extension is available.
_TTL_PURGE = {
    # table: (jsonb field holding the ISO expiry/timestamp, max age seconds)
    "tokens_revoked": ("expires_at", 0),
    "login_attempts": ("attempted_at", 86400),
}

_pool: Optional[asyncpg.Pool] = None


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _dumps(obj: Any) -> str:
    return json.dumps(obj, default=_json_default)


async def _init_conn(conn: asyncpg.Connection) -> None:
    # Make jsonb columns transparently encode/decode Python dicts.
    await conn.set_type_codec(
        "jsonb",
        encoder=_dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


def _ssl_arg() -> Any:
    """Choose asyncpg's ``ssl`` argument.

    An explicit ``sslmode`` in DATABASE_URL is passed through **verbatim**
    (including ``verify-ca``/``verify-full`` — never downgraded to
    ``require``, which would silently disable certificate/hostname
    verification). Without an explicit ``sslmode``: no SSL for a local
    Postgres (CI ``postgres:16`` service, dev), ``require`` for any remote
    host (Supabase needs TLS).
    """
    parsed = urlparse(DATABASE_URL)
    sslmode = parse_qs(parsed.query or "").get("sslmode", [None])[0]
    if sslmode:
        return False if sslmode == "disable" else sslmode
    host = (parsed.hostname or "").lower()
    if host in ("localhost", "127.0.0.1", "::1") or host.endswith(".local"):
        return False
    return "require"


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            statement_cache_size=0,  # pgbouncer transaction-mode safe
            ssl=_ssl_arg(),
            init=_init_conn,
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def ping() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("SELECT 1")


def _quote_ident(name: str) -> str:
    if name not in _COLLECTION_SET:
        # Defensive: table name is never user-controlled, but never
        # interpolate an unvalidated identifier into SQL.
        if not re.fullmatch(r"[a-z_][a-z0-9_]*", name):
            raise ValueError(f"Invalid collection name: {name!r}")
    return f'"{name}"'


def _safe_jsonb_key(key: str) -> str:
    """Valida uma chave de campo jsonb antes de a interpolar num literal
    `doc->>'<key>'`. Hoje estas chaves são constantes internas (nunca
    controladas pelo utilizador), mas validar — em vez de confiar — espelha a
    defesa de `_quote_ident` contra um futuro chamador descuidado. Devolve a
    chave inalterada (as plicas vêm do f-string em redor)."""
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", key):
        raise ValueError(f"Invalid jsonb key: {key!r}")
    return key


def _to_scalar_text(value: Any) -> Optional[str]:
    """Render a Python scalar the same way Postgres `jsonb ->> 'k'` would."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _rehydrate(table: str, doc: Optional[dict]) -> Optional[dict]:
    if doc is None:
        return None
    dt_fields = _DATETIME_FIELDS.get(table)
    if dt_fields:
        for field in dt_fields:
            raw = doc.get(field)
            if isinstance(raw, str):
                try:
                    doc[field] = datetime.fromisoformat(raw)
                except ValueError:
                    pass
    return doc


def _apply_projection(doc: dict, projection: Optional[dict]) -> dict:
    """Emulate Mongo projection. `_id` does not exist here (the surrogate
    `pk` is never in `doc`), so `{"_id": 0}` is a harmless no-op. Inclusion
    projections (`{"field": 1}`) return only those fields; exclusion
    projections (`{"field": 0}`) return the document **minus** those fields
    (Mongo forbids mixing the two, except for `_id`).
    """
    if not projection:
        return doc
    includes = [k for k, v in projection.items() if k != "_id" and v]
    if includes:
        return {k: doc[k] for k in includes if k in doc}
    excludes = {k for k, v in projection.items() if k != "_id" and not v}
    if excludes:
        return {k: v for k, v in doc.items() if k not in excludes}
    return doc


class _WhereBuilder:
    """Translate the Mongo filter subset used by the codebase into a SQL
    WHERE clause over a `doc jsonb` column. Supported: implicit equality,
    `$in`, `$ne`, `$eq`, `$gt/$gte/$lt/$lte`, `$or`, `$regex` (+`$options`),
    and Mongo scalar-vs-array membership (a plain `{field: value}` also
    matches when `field` is an array containing `value`).
    """

    def __init__(self) -> None:
        self.params: list[Any] = []

    def _ph(self, value: Any) -> str:
        self.params.append(value)
        return f"${len(self.params)}"

    def _cmp(self, field: str, op: str, value: Any) -> str:
        col_txt = f"(doc->>{self._lit(field)})"
        if isinstance(value, bool):
            return f"{col_txt} {op} {self._ph('true' if value else 'false')}"
        if isinstance(value, (int, float)):
            return f"({col_txt} ~ '^-?[0-9]+(\\.[0-9]+)?$' AND ({col_txt})::numeric {op} {self._ph(value)}::numeric)"
        return f"{col_txt} {op} {self._ph(_to_scalar_text(value))}"

    def _lit(self, field: str) -> str:
        # jsonb key literal — single-quote escaped (keys come from code,
        # never end-user free text, but stay safe regardless).
        return "'" + field.replace("'", "''") + "'"

    def _eq(self, field: str, value: Any) -> str:
        key = self._lit(field)
        if value is None:
            return f"(NOT (doc ? {key}) OR doc->>{key} IS NULL)"
        scalar = self._cmp(field, "=", value)
        # Mongo: {field: v} also matches if doc.field is an array containing v.
        # Membership via the `?` existence operator with a *text* parameter — NOT
        # `@> $n::jsonb`: asyncpg binds a jsonb parameter such that `col @> $n::jsonb`
        # never matches (a jsonb literal does), so that branch was dead and any
        # {arrayField: scalar} filter silently returned nothing. `?` tests whether
        # the value is a top-level string element of the array; consistent with the
        # `$in` branch (which uses `?|`). Covers the string arrays in the schema
        # (attendees, team_members, likes, privileges, …).
        arr = f"(jsonb_typeof(doc->{key}) = 'array' AND doc->{key} ? {self._ph(_to_scalar_text(value))})"
        return f"({scalar} OR {arr})"

    def _field_clause(self, field: str, cond: Any) -> str:
        if isinstance(cond, dict) and any(k.startswith("$") for k in cond):
            parts: list[str] = []
            for op, val in cond.items():
                if op == "$in":
                    key = self._lit(field)
                    texts = [_to_scalar_text(v) for v in val]
                    member = f"doc->>{key} = ANY({self._ph(texts)}::text[])"
                    arr = (
                        f"(jsonb_typeof(doc->{key}) = 'array' "
                        f"AND doc->{key} ?| {self._ph([t for t in texts if t is not None])})"
                    )
                    parts.append(f"({member} OR {arr})")
                elif op == "$nin":
                    key = self._lit(field)
                    texts = [_to_scalar_text(v) for v in val]
                    parts.append(f"(doc->>{key} IS NULL OR doc->>{key} <> ALL({self._ph(texts)}::text[]))")
                elif op in ("$ne",):
                    parts.append(f"doc->>{self._lit(field)} IS DISTINCT FROM {self._ph(_to_scalar_text(val))}")
                elif op == "$eq":
                    parts.append(self._eq(field, val))
                elif op == "$gt":
                    parts.append(self._cmp(field, ">", val))
                elif op == "$gte":
                    parts.append(self._cmp(field, ">=", val))
                elif op == "$lt":
                    parts.append(self._cmp(field, "<", val))
                elif op == "$lte":
                    parts.append(self._cmp(field, "<=", val))
                elif op == "$regex":
                    flags = cond.get("$options", "")
                    operator = "~*" if "i" in flags else "~"
                    parts.append(f"doc->>{self._lit(field)} {operator} {self._ph(val)}")
                elif op == "$options":
                    continue  # handled with $regex
                elif op == "$exists":
                    key = self._lit(field)
                    parts.append(f"(doc ? {key})" if val else f"(NOT (doc ? {key}))")
                else:
                    raise NotImplementedError(f"Unsupported query operator: {op}")
            return "(" + " AND ".join(parts) + ")" if parts else "TRUE"
        return self._eq(field, cond)

    def build(self, filt: Optional[dict]) -> str:
        if not filt:
            return "TRUE"
        clauses: list[str] = []
        for key, value in filt.items():
            if key == "$or":
                ors = [self.build_sub(sub) for sub in value]
                clauses.append("(" + " OR ".join(ors) + ")")
            elif key == "$and":
                ands = [self.build_sub(sub) for sub in value]
                clauses.append("(" + " AND ".join(ands) + ")")
            else:
                clauses.append(self._field_clause(key, value))
        return " AND ".join(clauses) if clauses else "TRUE"

    def build_sub(self, filt: dict) -> str:
        return "(" + self.build(filt) + ")"


def _order_by(sort_spec) -> str:
    if not sort_spec:
        return ""
    if isinstance(sort_spec, str):
        sort_spec = [(sort_spec, 1)]
    elif isinstance(sort_spec, tuple):
        sort_spec = [sort_spec]
    def _lit(name: str) -> str:
        return "'" + name.replace("'", "''") + "'"

    pieces: list[str] = []
    for field, direction in sort_spec:
        d = "DESC" if int(direction) < 0 else "ASC"
        if isinstance(field, (tuple, list)):
            # COALESCE de campos alternativos: ordena pelo 1.º presente (ex.
            # published_at→created_at), preservando a semântica de uma chave
            # de ordenação derivada sem materializar um campo extra.
            col = "COALESCE(" + ", ".join(f"(doc->>{_lit(f)})" for f in field) + ")"
        else:
            col = f"(doc->>{_lit(field)})"
        # numeric-aware: sort numbers numerically, everything else (ISO
        # dates, booleans, text) lexically — correct for all real sorts.
        pieces.append(f"CASE WHEN {col} ~ '^-?[0-9]+(\\.[0-9]+)?$' THEN ({col})::numeric END {d} NULLS LAST")
        pieces.append(f"{col} {d}")
    return " ORDER BY " + ", ".join(pieces)


class _InsertResult:
    def __init__(self, inserted_id: Any) -> None:
        self.inserted_id = inserted_id


class _InsertManyResult:
    def __init__(self, inserted_ids: list[Any]) -> None:
        self.inserted_ids = inserted_ids


class _UpdateResult:
    def __init__(self, matched: int, modified: int) -> None:
        self.matched_count = matched
        self.modified_count = modified


class _DeleteResult:
    def __init__(self, deleted: int) -> None:
        self.deleted_count = deleted


def _mongo_update(doc: dict, update: dict) -> dict:
    """Apply the Mongo update-operator subset ($set/$inc/$push/$pull) in
    Python — guarantees behaviour identical to MongoDB (push to a missing
    field creates the array, $inc on a missing field starts at 0, etc.).
    """
    if not any(k.startswith("$") for k in update):
        # Full-document replacement (not used in the codebase, but faithful).
        return dict(update)
    out = dict(doc)
    for op, changes in update.items():
        if op == "$set":
            for k, v in changes.items():
                out[k] = v
        elif op == "$inc":
            for k, v in changes.items():
                out[k] = (out.get(k) or 0) + v
        elif op == "$push":
            for k, v in changes.items():
                arr = list(out.get(k) or [])
                arr.append(v)
                out[k] = arr
        elif op == "$pull":
            for k, v in changes.items():
                out[k] = [x for x in (out.get(k) or []) if x != v]
        elif op == "$addToSet":
            for k, v in changes.items():
                arr = list(out.get(k) or [])
                if v not in arr:
                    arr.append(v)
                out[k] = arr
        elif op == "$unset":
            for k in changes:
                out.pop(k, None)
        else:
            raise NotImplementedError(f"Unsupported update operator: {op}")
    return out


class _Cursor:
    """Lazy cursor mirroring Motor: `.sort().skip().limit().to_list()` and
    `async for`. Query executes only on materialisation."""

    def __init__(self, collection: "_Collection", filt, projection):
        self._c = collection
        self._filt = filt
        self._proj = projection
        self._sort = None
        self._skip = 0
        self._limit = None

    def sort(self, key_or_list, direction: int = 1) -> "_Cursor":
        if isinstance(key_or_list, str):
            self._sort = [(key_or_list, direction)]
        else:
            self._sort = list(key_or_list)
        return self

    def skip(self, n: int) -> "_Cursor":
        self._skip = n or 0
        return self

    def limit(self, n: int) -> "_Cursor":
        self._limit = n or None
        return self

    async def to_list(self, length: Optional[int] = None) -> list[dict]:
        wb = _WhereBuilder()
        where = wb.build(self._filt)
        sql = f"SELECT doc FROM {_quote_ident(self._c.name)} WHERE {where}"
        sql += _order_by(self._sort)
        lim = self._limit if self._limit is not None else length
        if lim is not None:
            sql += f" LIMIT {int(lim)}"
        if self._skip:
            sql += f" OFFSET {int(self._skip)}"
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *wb.params)
        return [_apply_projection(_rehydrate(self._c.name, dict(r["doc"])), self._proj) for r in rows]

    def __await__(self):
        return self.to_list().__await__()

    async def __aiter__(self):
        for item in await self.to_list():
            yield item


class _Collection:
    def __init__(self, name: str) -> None:
        self.name = name

    # ---- reads -------------------------------------------------------- #

    def find(self, filt: Optional[dict] = None, projection: Optional[dict] = None) -> _Cursor:
        return _Cursor(self, filt or {}, projection)

    async def find_one(
        self,
        filt: Optional[dict] = None,
        projection: Optional[dict] = None,
        *,
        sort=None,
    ) -> Optional[dict]:
        cur = _Cursor(self, filt or {}, projection)
        if sort:
            cur.sort(sort)
        cur.limit(1)
        rows = await cur.to_list()
        return rows[0] if rows else None

    async def count_documents(self, filt: Optional[dict] = None) -> int:
        wb = _WhereBuilder()
        where = wb.build(filt or {})
        sql = f"SELECT count(*) AS n FROM {_quote_ident(self.name)} WHERE {where}"
        pool = await get_pool()
        async with pool.acquire() as conn:
            return int(await conn.fetchval(sql, *wb.params))

    # ---- writes ------------------------------------------------------- #

    async def _purge_ttl(self, conn: asyncpg.Connection) -> None:
        rule = _TTL_PURGE.get(self.name)
        if not rule:
            return
        field, max_age = rule
        if max_age == 0:
            cutoff = datetime.now(tz=__import__("datetime").timezone.utc).isoformat()
        else:
            from datetime import timedelta, timezone

            cutoff = (datetime.now(tz=timezone.utc) - timedelta(seconds=max_age)).isoformat()
        await conn.execute(
            f"DELETE FROM {_quote_ident(self.name)} WHERE doc->>'{field}' IS NOT NULL AND doc->>'{field}' < $1",
            cutoff,
        )

    async def insert_one(self, document: dict) -> _InsertResult:
        doc = dict(document)
        pool = await get_pool()
        async with pool.acquire() as conn:
            await self._purge_ttl(conn)
            pk = await conn.fetchval(
                f"INSERT INTO {_quote_ident(self.name)}(doc) VALUES($1) RETURNING pk",
                doc,
            )
        return _InsertResult(doc.get("id", pk))

    async def insert_many(self, documents: list[dict]) -> _InsertManyResult:
        docs = [dict(d) for d in documents]
        if not docs:
            return _InsertManyResult([])
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.executemany(
                f"INSERT INTO {_quote_ident(self.name)}(doc) VALUES($1)",
                [(d,) for d in docs],
            )
        return _InsertManyResult([d.get("id") for d in docs])

    async def _update(self, filt: dict, update: dict, *, many: bool) -> _UpdateResult:
        wb = _WhereBuilder()
        where = wb.build(filt or {})
        limit_sql = "" if many else " LIMIT 1"
        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                rows = await conn.fetch(
                    f"SELECT pk, doc FROM {_quote_ident(self.name)} WHERE {where} ORDER BY pk{limit_sql} FOR UPDATE",
                    *wb.params,
                )
                modified = 0
                for r in rows:
                    new_doc = _mongo_update(dict(r["doc"]), update)
                    if new_doc != dict(r["doc"]):
                        await conn.execute(
                            f"UPDATE {_quote_ident(self.name)} SET doc=$1 WHERE pk=$2",
                            new_doc,
                            r["pk"],
                        )
                        modified += 1
        return _UpdateResult(len(rows), modified)

    async def update_one(self, filt: dict, update: dict, **_: Any) -> _UpdateResult:
        return await self._update(filt, update, many=False)

    async def update_many(self, filt: dict, update: dict, **_: Any) -> _UpdateResult:
        return await self._update(filt, update, many=True)

    async def delete_one(self, filt: dict) -> _DeleteResult:
        wb = _WhereBuilder()
        where = wb.build(filt or {})
        pool = await get_pool()
        async with pool.acquire() as conn:
            n = await conn.fetchval(
                f"WITH victim AS (SELECT pk FROM {_quote_ident(self.name)} "
                f"WHERE {where} ORDER BY pk LIMIT 1) "
                f"DELETE FROM {_quote_ident(self.name)} t USING victim "
                f"WHERE t.pk = victim.pk RETURNING 1",
                *wb.params,
            )
        return _DeleteResult(1 if n else 0)

    async def delete_many(self, filt: Optional[dict] = None) -> _DeleteResult:
        wb = _WhereBuilder()
        where = wb.build(filt or {})
        pool = await get_pool()
        async with pool.acquire() as conn:
            status = await conn.execute(
                f"DELETE FROM {_quote_ident(self.name)} WHERE {where}",
                *wb.params,
            )
        # asyncpg returns e.g. "DELETE 5"
        try:
            deleted = int(status.split()[-1])
        except (ValueError, IndexError):
            deleted = 0
        return _DeleteResult(deleted)

    # ---- aggregation -------------------------------------------------- #

    def aggregate(self, pipeline: list[dict]) -> "_AggCursor":
        return _AggCursor(self, pipeline)

    async def _aggregate(self, pipeline: list[dict]) -> list[dict]:
        # Stage 1 is always $match in the codebase's 7 pipelines; fetch the
        # matched docs then group/count/sort in Python (datasets are bounded
        # subsets — one user's votes, one project's expenses, etc.).
        docs: list[dict]
        match: dict = {}
        rest = list(pipeline)
        if rest and "$match" in rest[0]:
            match = rest[0]["$match"]
            rest = rest[1:]
        wb = _WhereBuilder()
        where = wb.build(match)
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(f"SELECT doc FROM {_quote_ident(self.name)} WHERE {where}", *wb.params)
        docs = [dict(r["doc"]) for r in rows]

        result: list[dict] = docs
        for stage in rest:
            if "$group" in stage:
                spec = stage["$group"]
                gid = spec["_id"]
                groups: dict[Any, dict] = {}
                order: list[Any] = []
                for d in result:
                    if gid is None:
                        key = None
                    elif isinstance(gid, str) and gid.startswith("$"):
                        key = d.get(gid[1:])
                    else:
                        key = gid
                    if key not in groups:
                        groups[key] = {"_id": key}
                        order.append(key)
                        for acc in spec:
                            if acc != "_id":
                                groups[key][acc] = 0
                    for acc, expr in spec.items():
                        if acc == "_id":
                            continue
                        groups[key][acc] += _eval_accumulator(expr, d)
                result = [groups[k] for k in order]
            elif "$count" in stage:
                result = [{stage["$count"]: len(result)}]
            elif "$sort" in stage:
                for field, direction in reversed(list(stage["$sort"].items())):
                    result.sort(
                        key=lambda r, f=field: (r.get(f) is None, r.get(f)),
                        reverse=int(direction) < 0,
                    )
            elif "$limit" in stage:
                result = result[: stage["$limit"]]
            elif "$project" in stage:
                proj = stage["$project"]
                inc = [k for k, v in proj.items() if v]
                result = [{k: r.get(k) for k in inc} for r in result]
            else:
                raise NotImplementedError(f"Unsupported aggregation stage: {list(stage)}")
        return result


def _eval_accumulator(expr: Any, doc: dict) -> float:
    """Evaluate a `$group` accumulator value for one document. Supports
    `$sum: 1`, `$sum: "$field"` and `$sum: {$cond: [cond, then, else]}`."""
    if isinstance(expr, dict):
        if "$sum" in expr:
            return _eval_value(expr["$sum"], doc)
        raise NotImplementedError(f"Unsupported accumulator: {list(expr)}")
    return float(expr or 0)


def _eval_value(expr: Any, doc: dict) -> float:
    if isinstance(expr, (int, float)):
        return float(expr)
    if isinstance(expr, str) and expr.startswith("$"):
        return float(doc.get(expr[1:]) or 0)
    if isinstance(expr, dict) and "$cond" in expr:
        cond, then, otherwise = expr["$cond"]
        return _eval_value(then, doc) if _eval_condition(cond, doc) else _eval_value(otherwise, doc)
    return float(expr or 0)


def _eval_condition(cond: Any, doc: dict) -> bool:
    if isinstance(cond, dict) and "$eq" in cond:
        left, right = cond["$eq"]
        lv = doc.get(left[1:]) if isinstance(left, str) and left.startswith("$") else left
        rv = doc.get(right[1:]) if isinstance(right, str) and right.startswith("$") else right
        return lv == rv
    return bool(cond)


class _AggCursor:
    """Lazy aggregation cursor: `await db.x.aggregate([...]).to_list()`."""

    def __init__(self, collection: _Collection, pipeline: list[dict]) -> None:
        self._collection = collection
        self._pipeline = pipeline

    async def to_list(self, length: Optional[int] = None) -> list[dict]:
        rows = await self._collection._aggregate(self._pipeline)
        return rows if length is None else rows[:length]

    def __await__(self):
        return self.to_list().__await__()

    async def __aiter__(self):
        for item in await self.to_list():
            yield item


class _Database:
    """`db.users` / `db["users"]` -> `_Collection`. Mirrors the Motor
    database object the codebase used (`from database import db`)."""

    def __getattr__(self, name: str) -> _Collection:
        if name.startswith("_"):
            raise AttributeError(name)
        return _Collection(name)

    def __getitem__(self, name: str) -> _Collection:
        return _Collection(name)


db = _Database()


# --------------------------------------------------------------------------- #
# Schema + indexes (idempotent — same contract as the old ensure_indexes()).
# --------------------------------------------------------------------------- #

# Expression indexes mirroring the original MongoDB indexes from database.py.
_INDEX_DDL: tuple[str, ...] = (
    # users
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email ON \"users\" ((doc->>'email'))",
    "CREATE INDEX IF NOT EXISTS ix_users_invite_token ON \"users\" ((doc->>'invite_token')) WHERE doc ? 'invite_token'",
    "CREATE INDEX IF NOT EXISTS ix_users_id ON \"users\" ((doc->>'id'))",
    "CREATE INDEX IF NOT EXISTS ix_users_status ON \"users\" ((doc->>'status'))",
    "CREATE INDEX IF NOT EXISTS ix_users_role ON \"users\" ((doc->>'role'))",
    # auto-registo: listagem rápida de pedidos pendentes/rejeitados (painel admin)
    "CREATE INDEX IF NOT EXISTS ix_users_status_registration ON \"users\" ((doc->>'status')) "
    "WHERE doc->>'status' IN ('pendente_aprovacao', 'rejeitado')",
    # auth
    "CREATE INDEX IF NOT EXISTS ix_pwreset_token ON \"password_resets\" ((doc->>'token'))",
    "CREATE INDEX IF NOT EXISTS ix_pwreset_email ON \"password_resets\" ((doc->>'email'))",
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_tokrev_jti ON \"tokens_revoked\" ((doc->>'jti'))",
    "CREATE INDEX IF NOT EXISTS ix_tokrev_exp ON \"tokens_revoked\" ((doc->>'expires_at'))",
    "CREATE INDEX IF NOT EXISTS ix_login_email_at ON \"login_attempts\" ((doc->>'email'), (doc->>'attempted_at') DESC)",
    "CREATE INDEX IF NOT EXISTS ix_login_at ON \"login_attempts\" ((doc->>'attempted_at'))",
    # notifications
    'CREATE INDEX IF NOT EXISTS ix_notif_user_created ON "notifications" '
    "((doc->>'user_id'), (doc->>'created_at') DESC)",
    "CREATE INDEX IF NOT EXISTS ix_notif_user_read ON \"notifications\" ((doc->>'user_id'), (doc->>'read'))",
    # wall
    'CREATE INDEX IF NOT EXISTS ix_wall_appr_pin_created ON "wall_posts" '
    "((doc->>'approved'), (doc->>'pinned') DESC, (doc->>'created_at') DESC)",
    "CREATE INDEX IF NOT EXISTS ix_wall_user_appr ON \"wall_posts\" ((doc->>'user_id'), (doc->>'approved'))",
    'CREATE INDEX IF NOT EXISTS ix_wallc_post_created ON "wall_comments" '
    "((doc->>'post_id'), (doc->>'created_at') DESC)",
    # transactions
    "CREATE INDEX IF NOT EXISTS ix_tx_date ON \"transactions\" ((doc->>'date') DESC)",
    "CREATE INDEX IF NOT EXISTS ix_tx_cat_date ON \"transactions\" ((doc->>'category'), (doc->>'date') DESC)",
    "CREATE INDEX IF NOT EXISTS ix_tx_user_date ON \"transactions\" ((doc->>'user_id'), (doc->>'date') DESC)",
    "CREATE INDEX IF NOT EXISTS ix_tx_type ON \"transactions\" ((doc->>'type'))",
    # events (attendees is an array -> GIN for membership queries)
    "CREATE INDEX IF NOT EXISTS ix_events_date ON \"events\" ((doc->>'date'))",
    "CREATE INDEX IF NOT EXISTS ix_events_vis_date ON \"events\" ((doc->>'visibility'), (doc->>'date'))",
    "CREATE INDEX IF NOT EXISTS gin_events_attendees ON \"events\" USING GIN ((doc->'attendees') jsonb_path_ops)",
    # projects
    "CREATE INDEX IF NOT EXISTS ix_proj_status_created ON \"projects\" ((doc->>'status'), (doc->>'created_at') DESC)",
    "CREATE INDEX IF NOT EXISTS gin_proj_team ON \"projects\" USING GIN ((doc->'team_members') jsonb_path_ops)",
    "CREATE INDEX IF NOT EXISTS ix_proj_created_by ON \"projects\" ((doc->>'created_by'))",
    'CREATE INDEX IF NOT EXISTS ix_projc_proj_created ON "project_comments" '
    "((doc->>'project_id'), (doc->>'created_at') DESC)",
    'CREATE INDEX IF NOT EXISTS ix_projm_proj_status ON "project_milestones" '
    "((doc->>'project_id'), (doc->>'status'))",
    # polls / votes
    "CREATE INDEX IF NOT EXISTS ix_polls_status_created ON \"polls\" ((doc->>'status'), (doc->>'created_at') DESC)",
    # UNIQUE: no máximo 1 voto por (user_id, poll_id) — fecha a race em vote().
    # Também serve as queries por (user_id, poll_id).
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_votes_user_poll ON \"user_votes\" ((doc->>'user_id'), (doc->>'poll_id'))",
    "CREATE INDEX IF NOT EXISTS ix_votes_poll ON \"user_votes\" ((doc->>'poll_id'))",
    # gallery
    "CREATE INDEX IF NOT EXISTS ix_gphoto_album_status ON \"gallery_photos\" ((doc->>'album_id'), (doc->>'status'))",
    'CREATE INDEX IF NOT EXISTS ix_gphoto_status_created ON "gallery_photos" '
    "((doc->>'status'), (doc->>'created_at') DESC)",
    "CREATE INDEX IF NOT EXISTS ix_gphoto_uploader ON \"gallery_photos\" ((doc->>'uploaded_by'))",
    # documents / posts
    "CREATE INDEX IF NOT EXISTS ix_docs_vis ON \"documents\" ((doc->>'visibility'))",
    "CREATE INDEX IF NOT EXISTS ix_posts_vis_created ON \"posts\" ((doc->>'visibility'), (doc->>'created_at') DESC)",
    # blog/notícias (spec-blog-noticias §4.4): lookup por slug + listas públicas/gestão
    "CREATE INDEX IF NOT EXISTS ix_posts_slug ON \"posts\" ((doc->>'slug'))",
    'CREATE INDEX IF NOT EXISTS ix_posts_status_vis_pub ON "posts" '
    "((doc->>'status'), (doc->>'visibility'), (doc->>'published_at') DESC)",
    # invoices
    "CREATE INDEX IF NOT EXISTS ix_inv_user_status ON \"invoices\" ((doc->>'user_id'), (doc->>'status'))",
    "CREATE INDEX IF NOT EXISTS ix_inv_status_created ON \"invoices\" ((doc->>'status'), (doc->>'created_at') DESC)",
    # audit
    "CREATE INDEX IF NOT EXISTS ix_audit_created ON \"audit_logs\" ((doc->>'created_at') DESC)",
    "CREATE INDEX IF NOT EXISTS ix_audit_user_created ON \"audit_logs\" ((doc->>'user_id'), (doc->>'created_at') DESC)",
    'CREATE INDEX IF NOT EXISTS ix_audit_target_created ON "audit_logs" '
    "((doc->>'target_id'), (doc->>'created_at') DESC)",
    'CREATE INDEX IF NOT EXISTS ix_audit_action_created ON "audit_logs" '
    "((doc->>'action'), (doc->>'created_at') DESC)",
    # document accesses / benefits
    'CREATE INDEX IF NOT EXISTS ix_docacc_user_at ON "document_accesses" '
    "((doc->>'user_id'), (doc->>'accessed_at') DESC)",
    "CREATE INDEX IF NOT EXISTS ix_docacc_user_doc ON \"document_accesses\" ((doc->>'user_id'), (doc->>'document_id'))",
    'CREATE INDEX IF NOT EXISTS ix_benval_user_at ON "benefit_validations" '
    "((doc->>'user_id'), (doc->>'validated_at') DESC)",
    # governança — assembleias
    "CREATE INDEX IF NOT EXISTS ix_assemb_status ON \"assembleias\" ((doc->>'status'))",
    "CREATE INDEX IF NOT EXISTS ix_assemb_tipo ON \"assembleias\" ((doc->>'tipo'))",
    "CREATE INDEX IF NOT EXISTS ix_assemb_data ON \"assembleias\" ((doc->>'data') DESC)",
    # UNIQUE: um membro só pode ter UMA presença própria por assembleia — backstop
    # de integridade à verificação aplicacional (corrida de dois check-ins
    # simultâneos do mesmo sócio inflaria o poder de voto presente / quórum).
    'CREATE UNIQUE INDEX IF NOT EXISTS ux_assembpres_assemb_user ON "assembleia_presencas" '
    "((doc->>'assembleia_id'), (doc->>'user_id'))",
    'CREATE INDEX IF NOT EXISTS ix_assembdelib_assemb ON "assembleia_deliberacoes" '
    "((doc->>'assembleia_id'), (doc->>'created_at') DESC)",
    # sessão "ao vivo" — fila de uso da palavra
    "CREATE INDEX IF NOT EXISTS ix_assembpalavra_assemb ON \"assembleia_palavra\" ((doc->>'assembleia_id'))",
    'CREATE INDEX IF NOT EXISTS ix_assembpalavra_assemb_status ON "assembleia_palavra" '
    "((doc->>'assembleia_id'), (doc->>'status'))",
    # sessão "ao vivo" — modos de votação (spec-sessao-assembleia §7/§9)
    # voto nominal: um voto por (deliberação, membro)
    'CREATE UNIQUE INDEX IF NOT EXISTS ux_assembvoto_delib_user ON "assembleia_votos" '
    "((doc->>'deliberacao_id'), (doc->>'user_id'))",
    "CREATE INDEX IF NOT EXISTS ix_assembvoto_delib ON \"assembleia_votos\" ((doc->>'deliberacao_id'))",
    # voto secreto: recibo prova que votou (único por eleitor); boletim é anónimo
    'CREATE UNIQUE INDEX IF NOT EXISTS ux_assembvotoreceipt_delib_hash ON "assembleia_voto_receipts" '
    "((doc->>'deliberacao_id'), (doc->>'voter_hash'))",
    "CREATE INDEX IF NOT EXISTS ix_assembvotoballot_delib ON \"assembleia_voto_ballots\" ((doc->>'deliberacao_id'))",
    # sessão "ao vivo" — moções/requerimentos/recomendações (F4)
    "CREATE INDEX IF NOT EXISTS ix_assembmocoes_assemb ON \"assembleia_mocoes\" ((doc->>'assembleia_id'))",
    'CREATE INDEX IF NOT EXISTS ix_assembmocoes_assemb_status ON "assembleia_mocoes" '
    "((doc->>'assembleia_id'), (doc->>'status'))",
    # sessão "ao vivo" — expediente do antes-OT (F5)
    "CREATE INDEX IF NOT EXISTS ix_assembexpediente_assemb ON \"assembleia_expediente\" ((doc->>'assembleia_id'))",
    # sessão "ao vivo" — convidados (F6)
    "CREATE INDEX IF NOT EXISTS ix_assembconvidados_assemb ON \"assembleia_convidados\" ((doc->>'assembleia_id'))",
    # governança — eleições
    "CREATE INDEX IF NOT EXISTS ix_eleicoes_status_ano ON \"eleicoes\" ((doc->>'status'), (doc->>'ano'))",
    "CREATE INDEX IF NOT EXISTS ix_eleicoes_assemb ON \"eleicoes\" ((doc->>'assembleia_id'))",
    'CREATE UNIQUE INDEX IF NOT EXISTS ux_eleicao_lista_letra ON "eleicao_listas" '
    "((doc->>'eleicao_id'), (doc->>'letra'))",
    # voto secreto: recibo prova que votou (único por eleitor); boletim é anónimo
    'CREATE UNIQUE INDEX IF NOT EXISTS ux_eleicao_receipt ON "eleicao_voter_receipts" '
    "((doc->>'eleicao_id'), (doc->>'voter_hash'))",
    'CREATE INDEX IF NOT EXISTS ix_eleicao_ballots_eleicao ON "eleicao_ballots" '
    "((doc->>'eleicao_id'), (doc->>'ballot_box_id'))",
    # governança — disciplina
    "CREATE INDEX IF NOT EXISTS ix_sancoes_user ON \"sancoes\" ((doc->>'user_id'), (doc->>'status'))",
    "CREATE INDEX IF NOT EXISTS ix_sancoes_status_tipo ON \"sancoes\" ((doc->>'status'), (doc->>'tipo'))",
    # governança — histórico de quota/jóia
    "CREATE INDEX IF NOT EXISTS ix_finsetthist_eff ON \"finance_settings_history\" ((doc->>'effective_from') DESC)",
    "CREATE INDEX IF NOT EXISTS ix_finsetthist_assemb ON \"finance_settings_history\" ((doc->>'assembleia_id'))",
    # controlos financeiros — actos de co-aprovação (spec-controlos §7)
    "CREATE INDEX IF NOT EXISTS ix_atos_status_created ON \"atos\" ((doc->>'status'), (doc->>'created_at') DESC)",
    "CREATE INDEX IF NOT EXISTS ix_atos_tipo ON \"atos\" ((doc->>'tipo'))",
    # voz e participação do sócio (spec-voz-participacao-socio §9)
    'CREATE UNIQUE INDEX IF NOT EXISTS ux_patrocinio_cand_sponsor ON "patrocinios" '
    "((doc->>'candidate_id'), (doc->>'sponsor_user_id'))",
    "CREATE INDEX IF NOT EXISTS ix_patrocinio_sponsor ON \"patrocinios\" ((doc->>'sponsor_user_id'), (doc->>'status'))",
    "CREATE INDEX IF NOT EXISTS ix_patrocinio_candidate ON \"patrocinios\" ((doc->>'candidate_id'), (doc->>'status'))",
    "CREATE INDEX IF NOT EXISTS ix_honorarios_status ON \"honorarios_nominations\" ((doc->>'status'))",
    "CREATE INDEX IF NOT EXISTS ix_honorarios_nominee ON \"honorarios_nominations\" ((doc->>'nominee_user_id'))",
    "CREATE INDEX IF NOT EXISTS ix_peticoes_status_created ON \"peticoes\" ((doc->>'status'), (doc->>'created_at') DESC)",
    'CREATE UNIQUE INDEX IF NOT EXISTS ux_peticao_assinatura ON "peticao_assinaturas" '
    "((doc->>'peticao_id'), (doc->>'user_id'))",
    "CREATE INDEX IF NOT EXISTS ix_peticao_assinatura_pet ON \"peticao_assinaturas\" ((doc->>'peticao_id'))",
    'CREATE INDEX IF NOT EXISTS ix_propostas_status_created ON "propostas_ag" '
    "((doc->>'status'), (doc->>'created_at') DESC)",
    "CREATE INDEX IF NOT EXISTS ix_propostas_autor ON \"propostas_ag\" ((doc->>'created_by'))",
    "CREATE INDEX IF NOT EXISTS ix_reclamacoes_autor ON \"reclamacoes\" ((doc->>'created_by'), (doc->>'status'))",
    "CREATE INDEX IF NOT EXISTS ix_reclamacoes_status ON \"reclamacoes\" ((doc->>'status'))",
    'CREATE INDEX IF NOT EXISTS ix_esclarecimentos_orgao ON "esclarecimentos" '
    "((doc->>'orgao_destino'), (doc->>'status'))",
    "CREATE INDEX IF NOT EXISTS ix_esclarecimentos_autor ON \"esclarecimentos\" ((doc->>'created_by'))",
    # ciclo anual de prestação de contas (spec-ciclo §7)
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_exercicios_ano ON \"exercicios\" ((doc->>'ano'))",
    "CREATE INDEX IF NOT EXISTS ix_exercicios_status ON \"exercicios\" ((doc->>'status'))",
    "CREATE INDEX IF NOT EXISTS ix_balancetes_exercicio ON \"balancetes\" ((doc->>'exercicio_ano'))",
    "CREATE INDEX IF NOT EXISTS ix_balancetes_tipo_periodo ON \"balancetes\" ((doc->>'tipo'), (doc->>'periodo'))",
    "CREATE INDEX IF NOT EXISTS ix_balancetes_published ON \"balancetes\" ((doc->>'published'))",
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_regulamentos_slug ON \"regulamentos\" ((doc->>'slug'))",
    "CREATE INDEX IF NOT EXISTS ix_regversoes_reg ON \"regulamento_versoes\" ((doc->>'regulamento_id'))",
    'CREATE UNIQUE INDEX IF NOT EXISTS ux_regversoes_reg_versao ON "regulamento_versoes" '
    "((doc->>'regulamento_id'), (doc->>'versao'))",
    "CREATE INDEX IF NOT EXISTS ix_regversoes_status ON \"regulamento_versoes\" ((doc->>'status'))",
    # comunicados (spec-comunicados-email)
    "CREATE INDEX IF NOT EXISTS ix_comunicados_created ON \"comunicados\" ((doc->>'created_at') DESC)",
    "CREATE INDEX IF NOT EXISTS ix_comunicados_status ON \"comunicados\" ((doc->>'status'))",
    "CREATE INDEX IF NOT EXISTS ix_comunicados_created_by ON \"comunicados\" ((doc->>'created_by'))",
    'CREATE INDEX IF NOT EXISTS ix_comunicados_source ON "comunicados" '
    "((doc->>'source_kind'), (doc->>'source_ref_id'))",
    # Anti-duplicado (race) entre dispatch_oficial_auto chamado pelo registo e
    # pelo apuramento da mesma deliberação: se duas tarefas correrem o find_one
    # antes de qualquer insert_one, ambas inseriam — enviando 2× o email oficial
    # para todos os activos. Este UNIQUE parcial bloqueia ao nível da BD; o
    # serviço captura a violação e trata como no-op (issue #157). Tolerante a
    # duplicados pré-existentes: ensure_schema só emite warning se a criação
    # falhar, e o ix_comunicados_source acima mantém a performance de lookup.
    'CREATE UNIQUE INDEX IF NOT EXISTS ux_comunicados_source_ref ON "comunicados" '
    "((doc->>'source_kind'), (doc->>'source_ref_id')) "
    "WHERE doc->>'source_kind' IS NOT NULL",
    # ranking de atuação do sócio (spec-ranking-socio)
    'CREATE UNIQUE INDEX IF NOT EXISTS ux_mscores_user_period ON "member_scores" '
    "((doc->>'user_id'), (doc->>'period_key'))",
    "CREATE INDEX IF NOT EXISTS ix_mscores_period_rank ON \"member_scores\" ((doc->>'period_key'), (doc->>'rank'))",
    'CREATE INDEX IF NOT EXISTS ix_rajustes_user_period ON "ranking_ajustes" '
    "((doc->>'user_id'), (doc->>'period_key'))",
    "CREATE INDEX IF NOT EXISTS ix_rajustes_created ON \"ranking_ajustes\" ((doc->>'created_at') DESC)",
    # fins profissionais Cat 5 F2 — formacoes (spec-fins-profissionais §6/§9)
    "CREATE INDEX IF NOT EXISTS ix_formacoes_tipo ON \"formacoes\" ((doc->>'tipo'))",
    "CREATE INDEX IF NOT EXISTS ix_formacoes_ativo ON \"formacoes\" ((doc->>'ativo'))",
    "CREATE INDEX IF NOT EXISTS ix_formacoes_categoria ON \"formacoes\" ((doc->>'categoria'))",
    # F4 — recorte público (visibility, ativo)
    "CREATE INDEX IF NOT EXISTS ix_formacoes_vis_ativo ON \"formacoes\" ((doc->>'visibility'), (doc->>'ativo'))",
    # fins profissionais Cat 5 F2 — publicacoes (spec-fins-profissionais §8/§9)
    "CREATE INDEX IF NOT EXISTS ix_publicacoes_tipo ON \"publicacoes\" ((doc->>'tipo'))",
    'CREATE INDEX IF NOT EXISTS ix_publicacoes_vis_data ON "publicacoes" '
    "((doc->>'visibility'), (doc->>'data_publicacao') DESC)",
    # fins profissionais Cat 5 F3 — defesa_profissional (spec §5)
    'CREATE INDEX IF NOT EXISTS ix_defesa_status_data ON "defesa_profissional" '
    "((doc->>'status'), (doc->>'data') DESC)",
    "CREATE INDEX IF NOT EXISTS ix_defesa_visibility ON \"defesa_profissional\" ((doc->>'visibility'))",
    "CREATE INDEX IF NOT EXISTS ix_defesa_created_by ON \"defesa_profissional\" ((doc->>'created_by'))",
    # fins profissionais Cat 5 F3 — relacoes_externas (spec §7)
    "CREATE INDEX IF NOT EXISTS ix_relacoes_tipo ON \"relacoes_externas\" ((doc->>'tipo'))",
    "CREATE INDEX IF NOT EXISTS ix_relacoes_estado ON \"relacoes_externas\" ((doc->>'estado_filiacao'))",
)

REQUIRED_INDEX_NAMES = {
    "ux_votes_user_poll",
    "ux_eleicao_receipt",  # garante 1 voto por eleitor (voto secreto)
}


def _required_index_name(ddl: str) -> str | None:
    for index_name in REQUIRED_INDEX_NAMES:
        if index_name in ddl:
            return index_name
    return None


# pg_cron purge for the formerly-TTL collections (best-effort; the DAO also
# purges opportunistically on insert so growth is bounded without pg_cron).
_PGCRON_DDL: tuple[str, ...] = (
    "CREATE EXTENSION IF NOT EXISTS pg_cron",
    # Compara como timestamptz, NÃO como texto: `now()::text` produz separador
    # espaço ('2026-06-07 12:00:00+00') enquanto os valores são ISO-8601 com 'T',
    # e 'T'(0x54) > ' '(0x20) faria a comparação lexicográfica falhar no dia
    # corrente. O cast (doc->>'campo')::timestamptz torna a comparação correcta.
    "SELECT cron.schedule('accta_purge_tokens_revoked', '*/15 * * * *', "
    "$$DELETE FROM \"tokens_revoked\" WHERE (doc->>'expires_at')::timestamptz < now()$$)",
    "SELECT cron.schedule('accta_purge_login_attempts', '0 * * * *', "
    "$$DELETE FROM \"login_attempts\" WHERE (doc->>'attempted_at')::timestamptz "
    "< now() - interval '24 hours'$$)",
)


# audit_logs append-only (spec-verificacao-seguranca-saas §8.1, F5.1) —
# DEFESA EM PROFUNDIDADE, não garantia absoluta: trigger que rejeita
# UPDATE/DELETE/TRUNCATE. Bloqueia mutação acidental (bugs da app, SQL
# descuidado, acesso casual) e complementa o HMAC do F4 (HMAC deteta
# modificação; o trigger impede-a). NÃO protege contra quem detém a credencial
# runtime: o ensure_schema corre COM essa credencial e o role da app é DONO da
# tabela, logo esse role pode DISABLE/DROP o trigger ou CREATE OR REPLACE a
# função. A imutabilidade AUTORITATIVA exige separação de roles no operador
# (owner/migração ≠ runtime) + REVOKE UPDATE/DELETE/TRUNCATE ao role runtime —
# ver runbook F5.1. Seguro: a app só faz INSERT/SELECT; ensure_schema só cria;
# _TTL_PURGE não inclui audit_logs. Idempotente e SEM janela destrutiva
# (CREATE OR REPLACE TRIGGER, sem DROP — PG ≥ 14).
_AUDIT_IMMUTABILITY_DDL: tuple[str, ...] = (
    "CREATE OR REPLACE FUNCTION accta_audit_logs_immutable() "
    "RETURNS trigger LANGUAGE plpgsql AS $$ "
    "BEGIN RAISE EXCEPTION 'audit_logs is append-only: % not allowed', TG_OP; END; $$",
    'CREATE OR REPLACE TRIGGER trg_audit_logs_immutable BEFORE UPDATE OR DELETE ON "audit_logs" '
    "FOR EACH ROW EXECUTE FUNCTION accta_audit_logs_immutable()",
    'CREATE OR REPLACE TRIGGER trg_audit_logs_no_truncate BEFORE TRUNCATE ON "audit_logs" '
    "FOR EACH STATEMENT EXECUTE FUNCTION accta_audit_logs_immutable()",
)


# RLS auto-enable (review Supabase 2026-06-07) — DEFESA EM PROFUNDIDADE contra a
# superfície do Data API (PostgREST). A app fala direto com o Postgres como role
# `postgres` (owner/bypassrls) e faz toda a autorização em Python; NÃO usa o Data
# API. Mas o Supabase concede por omissão DML a `anon`/`authenticated` em todas as
# tabelas de `public` — quem tiver a `anon` key poderia ler/escrever via REST. A
# proteção é **RLS ON + 0 policies = deny-all** para esses roles; o role da app
# (owner/bypassrls) não é afetado. Este bloco garante essa postura em código:
#   (1) backfill — ativa RLS em qualquer tabela de `public` que ainda não a tenha;
#   (2) event trigger `ensure_rls` — ativa RLS em cada tabela nova (idempotente;
#       `CREATE EVENT TRIGGER` não tem OR REPLACE, daí o guard IF NOT EXISTS).
# Como o trigger de audit, é **non-fatal**: criar event trigger exige superuser;
# numa instalação endurecida (roles separados) é o operador que o instala e a
# garantia autoritativa é dele — ver runbook **F5.6** (REVOKE/Data API off).
_RLS_BACKFILL_DDL: str = (
    "DO $$ DECLARE t record; BEGIN "
    "FOR t IN SELECT c.oid::regclass AS ident FROM pg_class c "
    "JOIN pg_namespace n ON n.oid = c.relnamespace "
    "WHERE n.nspname = 'public' AND c.relkind = 'r' AND NOT c.relrowsecurity LOOP "
    "EXECUTE format('alter table %s enable row level security', t.ident); "
    "END LOOP; END $$"
)
_RLS_AUTO_ENABLE_DDL: tuple[str, ...] = (
    # Corpo fiel ao já instalado em produção (pg_get_functiondef) — CREATE OR
    # REPLACE é no-op contra a DB atual; só repõe a função se for reconstruída.
    "CREATE OR REPLACE FUNCTION public.rls_auto_enable() "
    "RETURNS event_trigger LANGUAGE plpgsql SECURITY DEFINER "
    "SET search_path TO 'pg_catalog' AS $$ "
    "DECLARE cmd record; BEGIN "
    "FOR cmd IN SELECT * FROM pg_event_trigger_ddl_commands() "
    "WHERE command_tag IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO') "
    "AND object_type IN ('table','partitioned table') LOOP "
    "IF cmd.schema_name = 'public' THEN BEGIN "
    "EXECUTE format('alter table if exists %s enable row level security', cmd.object_identity); "
    "EXCEPTION WHEN OTHERS THEN "
    "RAISE LOG 'rls_auto_enable: failed to enable RLS on %', cmd.object_identity; "
    "END; END IF; END LOOP; END; $$",
    "DO $$ BEGIN "
    "IF NOT EXISTS (SELECT 1 FROM pg_event_trigger WHERE evtname = 'ensure_rls') THEN "
    "CREATE EVENT TRIGGER ensure_rls ON ddl_command_end EXECUTE FUNCTION public.rls_auto_enable(); "
    "END IF; END $$",
)


async def ensure_schema() -> None:
    """Create all tables + indexes. Idempotent (safe to re-run on every
    startup) — same operational contract as the old ensure_indexes()."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        for table in COLLECTIONS:
            await conn.execute(
                f"CREATE TABLE IF NOT EXISTS {_quote_ident(table)} (pk bigserial PRIMARY KEY, doc jsonb NOT NULL)"
            )
        # Sequência atómica para member_id do auto-registo (resolve race sob carga).
        # NOTA deploy: em produção, fazer setval para MAX(member_id numérico
        # existente)+1 ANTES do primeiro pedido, senão colide com IDs já dados.
        try:
            await conn.execute("CREATE SEQUENCE IF NOT EXISTS member_id_seq START 1")
        except Exception as e:  # noqa: BLE001 - sequence creation non-fatal
            logger.warning(f"member_id_seq creation warning (non-fatal): {e}")
        for ddl in _INDEX_DDL:
            try:
                await conn.execute(ddl)
            except Exception as e:  # noqa: BLE001 - index creation is non-fatal
                required_index = _required_index_name(ddl)
                if required_index:
                    raise RuntimeError(
                        f"Required index {required_index} could not be created. "
                        "Check existing duplicate user_votes by user_id/poll_id before startup."
                    ) from e
                logger.warning(f"Index creation warning (non-fatal): {e}")
        for ddl in _PGCRON_DDL:
            try:
                await conn.execute(ddl)
            except Exception as e:  # noqa: BLE001 - pg_cron optional
                logger.info(f"pg_cron not configured (using opportunistic purge): {e}")
        # Instala atomicamente (transação) e sem janela destrutiva (CREATE OR
        # REPLACE, sem DROP). Non-fatal de propósito: numa instalação endurecida
        # com roles separados, o role runtime pode (e deve) não ter direito de
        # criar o trigger — aí é o role de migração/owner que o instala e a
        # imutabilidade autoritativa vem do REVOKE (runbook F5.1). A app arranca.
        try:
            async with conn.transaction():
                for ddl in _AUDIT_IMMUTABILITY_DDL:
                    await conn.execute(ddl)
            logger.info("audit_logs immutability trigger (defesa em profundidade) instalado")
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "audit_logs immutability trigger (defesa em profundidade) NAO instalado — "
                "a imutabilidade autoritativa e o REVOKE/role-separation do operador (runbook F5.1): %s",
                e,
            )
        # RLS em todas as tabelas de public (deny-all p/ o Data API) — ver nota em
        # _RLS_AUTO_ENABLE_DDL. Backfill e trigger em try/except independentes: o
        # backfill (precisa só de owner) protege as tabelas atuais mesmo que a
        # criação do event trigger (precisa de superuser) não seja permitida.
        try:
            await conn.execute(_RLS_BACKFILL_DDL)
        except Exception as e:  # noqa: BLE001 - non-fatal, ver runbook F5.6
            logger.warning("RLS backfill (defesa em profundidade) NAO aplicado — autoritativo via operador (runbook F5.6): %s", e)
        try:
            async with conn.transaction():
                for ddl in _RLS_AUTO_ENABLE_DDL:
                    await conn.execute(ddl)
            logger.info("RLS auto-enable event trigger (defesa em profundidade) instalado")
        except Exception as e:  # noqa: BLE001 - non-fatal, ver runbook F5.6
            logger.warning("RLS auto-enable event trigger NAO instalado — autoritativo via operador (runbook F5.6): %s", e)
    logger.info("PostgreSQL schema and indexes ensured")


async def next_member_id() -> str:
    """Atribui o próximo member_id sequencial e imutável via `member_id_seq`.
    Formato `ACCTA-{n:04d}` (zero-padded, expande para 5+ dígitos > 9999).
    Mantém o raw SQL no DAO — as rotas chamam só este helper (regra api.md).
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        n = await conn.fetchval("SELECT nextval('member_id_seq')")
    return f"ACCTA-{int(n):04d}"


async def register_event_attendee(event_id: str, user_id: str) -> str:
    """Append one attendee while the event document is locked.

    Returns one of: registered, missing, already_registered, full.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            wb = _WhereBuilder()
            where = wb.build({"id": event_id})
            row = await conn.fetchrow(
                f"SELECT pk, doc FROM {_quote_ident('events')} WHERE {where} ORDER BY pk LIMIT 1 FOR UPDATE",
                *wb.params,
            )
            if row is None:
                return "missing"

            event = dict(row["doc"])
            attendees = list(event.get("attendees") or [])
            if user_id in attendees:
                return "already_registered"

            max_attendees = event.get("max_attendees")
            if max_attendees and len(attendees) >= max_attendees:
                return "full"

            attendees.append(user_id)
            event["attendees"] = attendees
            await conn.execute(
                f"UPDATE {_quote_ident('events')} SET doc=$1 WHERE pk=$2",
                event,
                row["pk"],
            )
    return "registered"


async def transfer_cargo(from_user_id: str, to_user_id: str, from_transform, to_transform) -> None:
    """Aplica duas transformações de utilizador numa ÚNICA transação atómica
    (transferência de mandato: despromove `from_user`, promove `to_user`).

    `from_transform`/`to_transform` são callables `doc -> novo_doc` aplicados ao
    documento JÁ BLOQUEADO (`FOR UPDATE`). Recomputar derivados do estado actual
    (ex.: `cargo_history`) DENTRO do lock evita lost-update contra edições de
    cargo concorrentes (promote/demote) — antes a rota passava um array
    pré-calculado a partir de uma leitura fora da transação, que sobre-escrevia
    alterações entretanto feitas. Ambos os docs têm de existir, senão rollback +
    ValueError. O raw SQL fica aqui no DAO (regra api.md).
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            for uid, transform in ((from_user_id, from_transform), (to_user_id, to_transform)):
                wb = _WhereBuilder()
                where = wb.build({"id": uid})
                row = await conn.fetchrow(
                    f"SELECT pk, doc FROM {_quote_ident('users')} WHERE {where} ORDER BY pk LIMIT 1 FOR UPDATE",
                    *wb.params,
                )
                if row is None:
                    raise ValueError(f"Utilizador {uid} não encontrado")
                new_doc = transform(dict(row["doc"]))
                await conn.execute(
                    f"UPDATE {_quote_ident('users')} SET doc=$1 WHERE pk=$2",
                    new_doc,
                    row["pk"],
                )


async def _cast_secret_ballot_locked(
    *,
    parent_table: str,
    parent_id: str,
    expected_status: str,
    receipt_table: str,
    ballot_table: str,
    dup_field: str,
    dup_value: str,
    parent_id_field_in_receipt: str,
    receipt_doc: dict,
    ballot_doc: dict,
) -> None:
    """Voto secreto genérico SOB lock da linha-pai. Numa única transação:
    1. `SELECT … FOR UPDATE` da linha-pai (`parent_table`/`parent_id`) com
       `lock_timeout=2s` — bloqueia voters concorrentes; `apurar` que faça CAS
       `update_one({id, status:expected_status}, …)` segura o mesmo lock.
    2. Re-verifica `status == expected_status` SOB o lock → fecha a janela
       TOCTOU contra o `apurar` (sem isto, um voter podia inserir o boletim
       imediatamente depois do `apurar` ler/fechar).
    3. Verifica recibo duplicado por `(parent_id_field_in_receipt, dup_field)`.
    4. Insere recibo + boletim atomicamente.

    Levanta `ValueError("not_found"|"not_open"|"duplicate")`; em contenção
    extrema do pool levanta `asyncpg.exceptions.LockNotAvailableError`.

    Helpers `cast_ballot` (eleições) e `cast_assembleia_ballot` (assembleias)
    delegam aqui — o raw SQL fica no DAO (regra api.md)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SET LOCAL lock_timeout = '2s'")
            row = await conn.fetchrow(
                f"SELECT pk, doc FROM {_quote_ident(parent_table)} WHERE doc->>'id' = $1 LIMIT 1 FOR UPDATE",
                parent_id,
            )
            if row is None:
                raise ValueError("not_found")
            if (row["doc"] or {}).get("status") != expected_status:
                raise ValueError("not_open")
            existing = await conn.fetchrow(
                f"SELECT pk FROM {_quote_ident(receipt_table)} "
                f"WHERE doc->>'{_safe_jsonb_key(parent_id_field_in_receipt)}' = $1 "
                f"AND doc->>'{_safe_jsonb_key(dup_field)}' = $2 LIMIT 1",
                parent_id,
                dup_value,
            )
            if existing is not None:
                raise ValueError("duplicate")
            await conn.execute(
                f"INSERT INTO {_quote_ident(receipt_table)} (doc) VALUES ($1)",
                receipt_doc,
            )
            await conn.execute(
                f"INSERT INTO {_quote_ident(ballot_table)} (doc) VALUES ($1)",
                ballot_doc,
            )


async def cast_ballot(eleicao_id: str, voter_hash: str, receipt_doc: dict, ballot_doc: dict) -> None:
    """Voto secreto de eleição (spec-governanca §7).

    Fecha a janela TOCTOU contra `apurar_eleicao` via `_cast_secret_ballot_locked`:
    `SELECT FOR UPDATE` em `eleicoes` + recheck `status="votacao"` na mesma
    transação onde o recibo+boletim são inseridos. Ver helper para detalhes."""
    await _cast_secret_ballot_locked(
        parent_table="eleicoes",
        parent_id=eleicao_id,
        expected_status="votacao",
        receipt_table="eleicao_voter_receipts",
        ballot_table="eleicao_ballots",
        dup_field="voter_hash",
        dup_value=voter_hash,
        parent_id_field_in_receipt="eleicao_id",
        receipt_doc=receipt_doc,
        ballot_doc=ballot_doc,
    )


async def cast_assembleia_ballot(deliberacao_id: str, voter_hash: str, receipt_doc: dict, ballot_doc: dict) -> None:
    """Voto secreto de uma deliberação de assembleia (spec-sessao-assembleia §7).

    Fecha a janela TOCTOU contra `apurar_deliberacao` via `_cast_secret_ballot_locked`:
    `SELECT FOR UPDATE` em `assembleia_deliberacoes` + recheck `status="aberta"`
    na mesma transação onde o recibo+boletim são inseridos."""
    await _cast_secret_ballot_locked(
        parent_table="assembleia_deliberacoes",
        parent_id=deliberacao_id,
        expected_status="aberta",
        receipt_table="assembleia_voto_receipts",
        ballot_table="assembleia_voto_ballots",
        dup_field="voter_hash",
        dup_value=voter_hash,
        parent_id_field_in_receipt="deliberacao_id",
        receipt_doc=receipt_doc,
        ballot_doc=ballot_doc,
    )


async def cast_assembleia_nominal_vote(deliberacao_id: str, user_id: str, voto_doc: dict) -> None:
    """Voto nominal de uma deliberação de assembleia. Análogo a
    `cast_assembleia_ballot` mas para `assembleia_votos`: trava a linha da
    deliberação (`FOR UPDATE`), re-confirma `status="aberta"` e insere o voto
    na mesma transação — fecha a janela TOCTOU contra `apurar_deliberacao`.

    Levanta `ValueError("not_found"|"not_open"|"duplicate")`. Voto duplicado
    está coberto duas vezes: in-tx (`EXISTS`) e pelo índice único
    `ux_assembvoto_delib_user`. `lock_timeout=2s` evita pool starvation."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SET LOCAL lock_timeout = '2s'")
            row = await conn.fetchrow(
                f"SELECT pk, doc FROM {_quote_ident('assembleia_deliberacoes')} "
                "WHERE doc->>'id' = $1 LIMIT 1 FOR UPDATE",
                deliberacao_id,
            )
            if row is None:
                raise ValueError("not_found")
            if (row["doc"] or {}).get("status") != "aberta":
                raise ValueError("not_open")
            dup = await conn.fetchrow(
                f"SELECT pk FROM {_quote_ident('assembleia_votos')} "
                "WHERE doc->>'deliberacao_id' = $1 AND doc->>'user_id' = $2 LIMIT 1",
                deliberacao_id,
                user_id,
            )
            if dup is not None:
                raise ValueError("duplicate")
            await conn.execute(
                f"INSERT INTO {_quote_ident('assembleia_votos')} (doc) VALUES ($1)",
                voto_doc,
            )


async def register_presenca_locked(
    assembleia_id: str,
    claimed_ids: list[str],
    presenca_doc: dict,
    allowed_statuses: tuple[str, ...] = ("convocada", "em_curso"),
) -> None:
    """Regista uma presença de assembleia SOB lock da linha da assembleia.

    Serializa todos os check-ins concorrentes da MESMA assembleia: numa única
    transação trava a assembleia (`FOR UPDATE`), re-confirma que está aberta e
    que nenhum dos `claimed_ids` (o próprio + representados) já está presente ou
    representado, e só então insere. Fecha a janela em que dois registos
    concorrentes reivindicavam o mesmo representado — o índice único
    `ux_assembpres_assemb_user` só cobre `user_id`, não `representados`.

    Levanta `ValueError("not_found" | "not_open" | "duplicate:<ids>")`; em
    contenção extrema do pool levanta `asyncpg.exceptions.LockNotAvailableError`.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SET LOCAL lock_timeout = '2s'")
            row = await conn.fetchrow(
                f"SELECT pk, doc FROM {_quote_ident('assembleias')} "
                "WHERE doc->>'id' = $1 LIMIT 1 FOR UPDATE",
                assembleia_id,
            )
            if row is None:
                raise ValueError("not_found")
            if (row["doc"] or {}).get("status") not in allowed_statuses:
                raise ValueError("not_open")
            rows = await conn.fetch(
                f"SELECT doc FROM {_quote_ident('assembleia_presencas')} WHERE doc->>'assembleia_id' = $1",
                assembleia_id,
            )
            already: set[str] = set()
            for r in rows:
                d = r["doc"] or {}
                if d.get("user_id"):
                    already.add(d["user_id"])
                already.update(d.get("representados") or [])
            conflict = sorted(set(claimed_ids) & already)
            if conflict:
                raise ValueError("duplicate:" + ",".join(conflict))
            await conn.execute(
                f"INSERT INTO {_quote_ident('assembleia_presencas')} (doc) VALUES ($1)",
                presenca_doc,
            )
