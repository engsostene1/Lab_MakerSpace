import sqlite3

class Database:
    def __init__(self, db_path: str = "makerspace.db"):
        self.db_path = db_path
        # check_same_thread=False keeps this simple for a single-threaded
        # CLI app; row_factory lets us access columns by name (row["name"]).
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        # Foreign keys are OFF by default in SQLite -> must enable per connection.
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._create_tables()

#schematic diagram of the database tables:
# members: id, name, email, phone, joined_date, active
# equipment: id, name, category, status, added_date
# loans: id, member_id, equipment_id, checkout_date, due_date, return_date
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

            -- NOTE: "overdue" is NOT a stored status. It is derived at
            -- query time from (due_date < today AND return_date IS NULL).
            -- See Loan.is_overdue() in models.py.
            CREATE TABLE IF NOT EXISTS loans (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id      INTEGER NOT NULL,
                equipment_id   INTEGER NOT NULL,
                checkout_date  TEXT NOT NULL,
                due_date       TEXT NOT NULL,
                return_date    TEXT,
                status         TEXT NOT NULL DEFAULT 'open'
                               CHECK (status IN ('open', 'returned')),
                FOREIGN KEY (member_id)    REFERENCES members(id),
                FOREIGN KEY (equipment_id) REFERENCES equipment(id)
            );

            CREATE INDEX IF NOT EXISTS idx_loans_member    ON loans(member_id);
            CREATE INDEX IF NOT EXISTS idx_loans_equipment ON loans(equipment_id);
            """
        )
        self.conn.commit()

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

    # Support "with Database(...) as db:" so the connection always closes.
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()