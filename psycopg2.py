"""In-browser compatibility shim for ``psycopg2``.

``psycopg2``/``psycopg2-binary`` is a C extension (libpq) with no wasm wheel,
and it needs a live PostgreSQL server over TCP — neither exists in the Pyodide
(in-browser) runtime, so ``import psycopg2`` cannot resolve normally. These
teaching notebooks use only the basic DB-API 2.0 surface, so map it onto the
stdlib ``sqlite3`` (an in-memory database). Any Postgres-specific SQL dialect
(``%s`` placeholders, ``RETURNING``, server-side types) may behave differently
than on a real Postgres server; the common ``CREATE``/``INSERT``/``SELECT``
teaching examples work.
"""

import sqlite3

apilevel = "2.0"
threadsafety = 1
paramstyle = "pyformat"


class Error(Exception):
    pass


class DatabaseError(Error):
    pass


class OperationalError(DatabaseError):
    pass


class ProgrammingError(DatabaseError):
    pass


def connect(*args, **kwargs):
    """Return a connection. The Postgres DSN/host/dbname/user/password are
    ignored — everything runs against a fresh in-memory sqlite database."""
    return _Connection(sqlite3.connect(":memory:"))


class _Connection:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, *a, **k):
        return _Cursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class _Cursor:
    def __init__(self, cur):
        self._cur = cur

    def execute(self, sql, params=None):
        # psycopg2 uses %s placeholders; sqlite3 uses ?. Translate the common
        # positional case (leave %% and named %(x)s parameters untouched).
        if params is not None:
            self._cur.execute(sql.replace("%s", "?"), params)
        else:
            self._cur.execute(sql)
        return self

    def executemany(self, sql, seq):
        self._cur.executemany(sql.replace("%s", "?"), seq)
        return self

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def fetchmany(self, size=1):
        return self._cur.fetchmany(size)

    @property
    def description(self):
        return self._cur.description

    @property
    def rowcount(self):
        return self._cur.rowcount

    def close(self):
        self._cur.close()

    def __iter__(self):
        return iter(self._cur)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
