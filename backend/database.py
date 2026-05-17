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

# All logical collections -> tables. 21 with Pydantic models + 6 without.
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


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            statement_cache_size=0,  # pgbouncer transaction-mode safe
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
    """Emulate Mongo projection. `_id` does not exist here (always excluded
    in callers). Inclusion projections (`{"field": 1}`) return only those
    fields; pure exclusion / `{"_id": 0}` returns the full document.
    """
    if not projection:
        return doc
    includes = [k for k, v in projection.items() if k != "_id" and v]
    if not includes:
        return doc
    return {k: doc[k] for k in includes if k in doc}


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
        arr = f"(jsonb_typeof(doc->{key}) = 'array' AND doc->{key} @> {self._ph(_dumps([value]))}::jsonb)"
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
    pieces: list[str] = []
    for field, direction in sort_spec:
        d = "DESC" if int(direction) < 0 else "ASC"
        lit = "'" + field.replace("'", "''") + "'"
        col = f"(doc->>{lit})"
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
    "CREATE INDEX IF NOT EXISTS ix_votes_user_poll ON \"user_votes\" ((doc->>'user_id'), (doc->>'poll_id'))",
    "CREATE INDEX IF NOT EXISTS ix_votes_poll ON \"user_votes\" ((doc->>'poll_id'))",
    # gallery
    "CREATE INDEX IF NOT EXISTS ix_gphoto_album_status ON \"gallery_photos\" ((doc->>'album_id'), (doc->>'status'))",
    'CREATE INDEX IF NOT EXISTS ix_gphoto_status_created ON "gallery_photos" '
    "((doc->>'status'), (doc->>'created_at') DESC)",
    "CREATE INDEX IF NOT EXISTS ix_gphoto_uploader ON \"gallery_photos\" ((doc->>'uploaded_by'))",
    # documents / posts
    "CREATE INDEX IF NOT EXISTS ix_docs_vis ON \"documents\" ((doc->>'visibility'))",
    "CREATE INDEX IF NOT EXISTS ix_posts_vis_created ON \"posts\" ((doc->>'visibility'), (doc->>'created_at') DESC)",
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
)

# pg_cron purge for the formerly-TTL collections (best-effort; the DAO also
# purges opportunistically on insert so growth is bounded without pg_cron).
_PGCRON_DDL: tuple[str, ...] = (
    "CREATE EXTENSION IF NOT EXISTS pg_cron",
    "SELECT cron.schedule('accta_purge_tokens_revoked', '*/15 * * * *', "
    "$$DELETE FROM \"tokens_revoked\" WHERE doc->>'expires_at' < now()::text$$)",
    "SELECT cron.schedule('accta_purge_login_attempts', '0 * * * *', "
    "$$DELETE FROM \"login_attempts\" WHERE doc->>'attempted_at' "
    "< (now() - interval '24 hours')::text$$)",
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
        for ddl in _INDEX_DDL:
            try:
                await conn.execute(ddl)
            except Exception as e:  # noqa: BLE001 - index creation is non-fatal
                logger.warning(f"Index creation warning (non-fatal): {e}")
        for ddl in _PGCRON_DDL:
            try:
                await conn.execute(ddl)
            except Exception as e:  # noqa: BLE001 - pg_cron optional
                logger.info(f"pg_cron not configured (using opportunistic purge): {e}")
    logger.info("PostgreSQL schema and indexes ensured")
