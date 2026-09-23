"""
database.py
-----------
Handles everything related to SQLite: opening/creating the database file,
creating the schema (tables), and providing small generic helpers
(execute / fetchone / fetchall) that the rest of the application uses.

Keeping all raw SQL and connection handling in one place means the rest
of the codebase (services.py, models.py) never has to talk to sqlite3
directly. This is the "data access layer" of the app.
"""

import sqlite3
from pathlib import Path


class Database:
    """
    Thin wrapper around a sqlite3 connection.

    Responsibilities:
        - Open (and create if missing) the .db file.
        - Create the members / equipment / loans tables on first run.
        - Enforce foreign keys.
        - Provide execute/fetchone/fetchall helpers used by services.py.

    Using a class (rather than free functions) means we can hold a single
    open connection for the lifetime of the app and reuse it everywhere.
    """

    def __init__(self, db_path: str = "makerspace.db"):
        self.db_path = db_path
        # check_same_thread=False keeps this simple for a single-threaded
        # CLI app; row_factory lets us access columns by name (row["name"]).
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        # Foreign keys are OFF by default in SQLite -> must enable per connection.
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._create_tables()

    # ------------------------------------------------------------------ #
    # Schema
    # ------------------------------------------------------------------ #
    def _create_tables(self) -> None:
        """Create the three core tables if they do not already exist."""
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS members (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL,
                email        TEXT NOT NULL UNIQUE,
                phone        TEXT,
                joined_date  TEXT NOT NULL,
                active       INTEGER NOT NULL DEFAULT 1  -- 1 = active, 0 = deactivated
            );

            CREATE TABLE IF NOT EXISTS equipment (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL,
                category     TEXT NOT NULL,
                status       TEXT NOT NULL DEFAULT 'available'
                             CHECK (status IN ('available', 'borrowed', 'maintenance', 'retired')),
                added_date   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS loans (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id      INTEGER NOT NULL,
                equipment_id   INTEGER NOT NULL,
                checkout_date  TEXT NOT NULL,
                due_date       TEXT NOT NULL,
                return_date    TEXT,
                status         TEXT NOT NULL DEFAULT 'open'
                               CHECK (status IN ('open', 'returned', 'overdue')),
                FOREIGN KEY (member_id)    REFERENCES members(id),
                FOREIGN KEY (equipment_id) REFERENCES equipment(id)
            );

            CREATE INDEX IF NOT EXISTS idx_loans_member    ON loans(member_id);
            CREATE INDEX IF NOT EXISTS idx_loans_equipment ON loans(equipment_id);
            """
        )
        self.conn.commit()

    # ------------------------------------------------------------------ #
    # Generic helpers
    # ------------------------------------------------------------------ #
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Run an INSERT/UPDATE/DELETE (or any) statement and commit.
        Returns the cursor so callers can read lastrowid / rowcount.
        """
        cur = self.conn.cursor()
        cur.execute(query, params)
        self.conn.commit()
        return cur

    def fetchone(self, query: str, params: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchone()

    def fetchall(self, query: str, params: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

    def close(self) -> None:
        self.conn.close()

    # Support "with Database(...) as db:" usage.
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def db_exists(db_path: str) -> bool:
        return Path(db_path).exists()
