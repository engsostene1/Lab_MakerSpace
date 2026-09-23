"""
services.py
-----------
The "business logic" layer. This is where object collaboration happens:
a MakerSpaceService takes a Database, and coordinates Member / Equipment /
Loan objects with SQL statements to implement the actual features required
by the assessment brief (register/list/update members & equipment, create
and close loans with validation, search, and reports).

main.py should only ever talk to this class - it should never touch
sqlite3 or the Database class directly. That separation is what keeps
main.py a thin menu loop instead of a big tangled script.
"""

import re
from datetime import date, datetime, timedelta
from typing import List, Optional

from database import Database
from models import Equipment, Loan, Member
from errors import ValidationError, NotFoundError, ConflictError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DEFAULT_LOAN_DAYS = 14


class MakerSpaceService:
    """
    Coordinates Member, Equipment and Loan objects together with the
    Database. Every public method here corresponds to a menu feature
    required by the assessment brief.
    """

    def __init__(self, db: Database):
        self.db = db

    # ------------------------------------------------------------------ #
    # Validation helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _require_non_empty(value: str, field_name: str) -> str:
        if value is None or not str(value).strip():
            raise ValidationError(f"{field_name} cannot be empty.")
        return str(value).strip()

    @staticmethod
    def _validate_email(email: str) -> str:
        email = email.strip()
        if not EMAIL_RE.match(email):
            raise ValidationError(f"'{email}' is not a valid email address.")
        return email

    # ------------------------------------------------------------------ #
    # Members: Create / Read / Update / Delete(-status)
    # ------------------------------------------------------------------ #
    def register_member(self, name: str, email: str, phone: str = "") -> Member:
        name = self._require_non_empty(name, "Name")
        email = self._validate_email(self._require_non_empty(email, "Email"))

        existing = self.db.fetchone("SELECT id FROM members WHERE email = ?", (email,))
        if existing:
            raise ValidationError(f"A member with email '{email}' already exists.")

        joined = date.today().isoformat()
        cur = self.db.execute(
            "INSERT INTO members (name, email, phone, joined_date, active) "
            "VALUES (?, ?, ?, ?, 1)",
            (name, email, phone.strip(), joined),
        )
        return Member(cur.lastrowid, name, email, phone, joined, True)

    def list_members(self, active_only: bool = False) -> List[Member]:
        query = "SELECT * FROM members"
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY id"
        return [Member.from_row(r) for r in self.db.fetchall(query)]

    def get_member(self, member_id: int) -> Member:
        row = self.db.fetchone("SELECT * FROM members WHERE id = ?", (member_id,))
        if not row:
            raise NotFoundError(f"No member found with id {member_id}.")
        return Member.from_row(row)

    def update_member(
        self,
        member_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Member:
        member = self.get_member(member_id)  # raises NotFoundError if missing

        if name:
            member.name = self._require_non_empty(name, "Name")
        if email:
            new_email = self._validate_email(email)
            clash = self.db.fetchone(
                "SELECT id FROM members WHERE email = ? AND id != ?", (new_email, member_id)
            )
            if clash:
                raise ValidationError(f"Email '{new_email}' is already used by another member.")
            member.email = new_email
        if phone is not None:
            member.phone = phone.strip()

        self.db.execute(
            "UPDATE members SET name = ?, email = ?, phone = ? WHERE id = ?",
            (member.name, member.email, member.phone, member.id),
        )
        return member

    def deactivate_member(self, member_id: int) -> Member:
        """'Delete' a member = soft delete, so loan history is preserved."""
        member = self.get_member(member_id)
        open_loans = self.db.fetchone(
            "SELECT COUNT(*) AS c FROM loans WHERE member_id = ? AND status = 'open'",
            (member_id,),
        )
        if open_loans["c"] > 0:
            raise ConflictError(
                "Cannot deactivate a member who currently has equipment on loan."
            )
        member.deactivate()
        self.db.execute("UPDATE members SET active = 0 WHERE id = ?", (member_id,))
        return member

    def search_members(self, query: str) -> List[Member]:
        query = f"%{query.strip()}%"
        rows = self.db.fetchall(
            "SELECT * FROM members WHERE name LIKE ? OR email LIKE ? OR CAST(id AS TEXT) = ? "
            "ORDER BY id",
            (query, query, query.strip("%")),
        )
        return [Member.from_row(r) for r in rows]

    # ------------------------------------------------------------------ #
    # Equipment: Create / Read / Update / Delete(-status)
    # ------------------------------------------------------------------ #
    def register_equipment(self, name: str, category: str) -> Equipment:
        name = self._require_non_empty(name, "Equipment name")
        category = self._require_non_empty(category, "Category")
        added = date.today().isoformat()
        cur = self.db.execute(
            "INSERT INTO equipment (name, category, status, added_date) "
            "VALUES (?, ?, 'available', ?)",
            (name, category, added),
        )
        return Equipment(cur.lastrowid, name, category, "available", added)

    def list_equipment(
        self, status: Optional[str] = None, category: Optional[str] = None
    ) -> List[Equipment]:
        query = "SELECT * FROM equipment WHERE 1=1"
        params: list = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY id"
        return [Equipment.from_row(r) for r in self.db.fetchall(query, tuple(params))]

    def get_equipment(self, equipment_id: int) -> Equipment:
        row = self.db.fetchone("SELECT * FROM equipment WHERE id = ?", (equipment_id,))
        if not row:
            raise NotFoundError(f"No equipment found with id {equipment_id}.")
        return Equipment.from_row(row)

    def update_equipment(
        self,
        equipment_id: int,
        name: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Equipment:
        equipment = self.get_equipment(equipment_id)

        if name:
            equipment.name = self._require_non_empty(name, "Equipment name")
        if category:
            equipment.category = self._require_non_empty(category, "Category")
        if status:
            status = status.strip().lower()
            if status not in Equipment.VALID_STATUSES:
                raise ValidationError(
                    f"Status must be one of {sorted(Equipment.VALID_STATUSES)}."
                )
            equipment.status = status

        self.db.execute(
            "UPDATE equipment SET name = ?, category = ?, status = ? WHERE id = ?",
            (equipment.name, equipment.category, equipment.status, equipment.id),
        )
        return equipment

    def retire_equipment(self, equipment_id: int) -> Equipment:
        """'Delete' equipment = soft delete via 'retired' status."""
        equipment = self.get_equipment(equipment_id)
        if equipment.status == "borrowed":
            raise ConflictError("Cannot retire equipment that is currently on loan.")
        equipment.mark_retired()
        self.db.execute("UPDATE equipment SET status = 'retired' WHERE id = ?", (equipment_id,))
        return equipment

    def search_equipment(self, query: str) -> List[Equipment]:
        query = f"%{query.strip()}%"
        rows = self.db.fetchall(
            "SELECT * FROM equipment WHERE name LIKE ? OR category LIKE ? "
            "OR CAST(id AS TEXT) = ? ORDER BY id",
            (query, query, query.strip("%")),
        )
        return [Equipment.from_row(r) for r in rows]

    # ------------------------------------------------------------------ #
    # Loans: create (checkout) & return, with validation
    # ------------------------------------------------------------------ #
    def create_loan(
        self, member_id: int, equipment_id: int, loan_days: int = DEFAULT_LOAN_DAYS
    ) -> Loan:
        member = self.get_member(member_id)
        if not member.is_active():
            raise ConflictError(f"Member {member_id} is deactivated and cannot borrow equipment.")

        equipment = self.get_equipment(equipment_id)
        if not equipment.is_available():
            raise ConflictError(
                f"Equipment '{equipment.name}' is not available (status: {equipment.status})."
            )

        checkout = date.today()
        due = checkout + timedelta(days=loan_days)
        cur = self.db.execute(
            "INSERT INTO loans (member_id, equipment_id, checkout_date, due_date, status) "
            "VALUES (?, ?, ?, ?, 'open')",
            (member_id, equipment_id, checkout.isoformat(), due.isoformat()),
        )
        self.db.execute("UPDATE equipment SET status = 'borrowed' WHERE id = ?", (equipment_id,))

        return Loan(cur.lastrowid, member_id, equipment_id, checkout.isoformat(), due.isoformat())

    def return_loan(self, loan_id: int) -> Loan:
        row = self.db.fetchone("SELECT * FROM loans WHERE id = ?", (loan_id,))
        if not row:
            raise NotFoundError(f"No loan found with id {loan_id}.")
        loan = Loan.from_row(row)
        if loan.status != "open":
            raise ConflictError(f"Loan {loan_id} is already {loan.status}, not open.")

        loan.close(date.today().isoformat())
        self.db.execute(
            "UPDATE loans SET return_date = ?, status = 'returned' WHERE id = ?",
            (loan.return_date, loan_id),
        )
        self.db.execute(
            "UPDATE equipment SET status = 'available' WHERE id = ?", (loan.equipment_id,)
        )
        return loan

    def list_loans(self, status: Optional[str] = None) -> List[Loan]:
        query = "SELECT * FROM loans"
        params: tuple = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY id"
        return [Loan.from_row(r) for r in self.db.fetchall(query, params)]

    # ------------------------------------------------------------------ #
    # Reports (at least two required by the brief - four provided)
    # ------------------------------------------------------------------ #
    def report_currently_borrowed(self):
        """Report 1: everything currently out on loan, with member & item names."""
        return self.db.fetchall(
            """
            SELECT l.id AS loan_id, m.name AS member_name, e.name AS equipment_name,
                   l.checkout_date, l.due_date
            FROM loans l
            JOIN members m   ON m.id = l.member_id
            JOIN equipment e ON e.id = l.equipment_id
            WHERE l.status = 'open'
            ORDER BY l.due_date
            """
        )

    def report_overdue_loans(self):
        """Report 2: open loans whose due_date is before today."""
        today = date.today().isoformat()
        return self.db.fetchall(
            """
            SELECT l.id AS loan_id, m.name AS member_name, e.name AS equipment_name,
                   l.checkout_date, l.due_date
            FROM loans l
            JOIN members m   ON m.id = l.member_id
            JOIN equipment e ON e.id = l.equipment_id
            WHERE l.status = 'open' AND l.due_date < ?
            ORDER BY l.due_date
            """,
            (today,),
        )

    def report_equipment_by_category(self):
        """Report 3: equipment counts grouped by category and status."""
        return self.db.fetchall(
            """
            SELECT category, status, COUNT(*) AS count
            FROM equipment
            GROUP BY category, status
            ORDER BY category, status
            """
        )

    def report_member_history(self, member_id: int):
        """Report 4: full loan history for a single member."""
        self.get_member(member_id)  # validates existence
        return self.db.fetchall(
            """
            SELECT l.id AS loan_id, e.name AS equipment_name, l.checkout_date,
                   l.due_date, l.return_date, l.status
            FROM loans l
            JOIN equipment e ON e.id = l.equipment_id
            WHERE l.member_id = ?
            ORDER BY l.checkout_date DESC
            """,
            (member_id,),
        )
