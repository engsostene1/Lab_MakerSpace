"""
Every menu action ends up calling one method here. This is where we
validate input, check rules ("can this member borrow?"), talk to the
database, and return objects back to the menu.
"""
import re
import sqlite3
from datetime import date, timedelta
from typing import List, Optional

from database import Database
from models import Equipment, Loan, Member
from errors import ValidationError, NotFoundError, ConflictError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DEFAULT_LOAN_DAYS = 14

class MakerSpaceService:

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
    # Members: Create ; Read ; Update ; Delete(status)
    # ------------------------------------------------------------------ #
    def register_member(self, name: str, email: str, phone: str = "") -> Member:
        name = self._require_non_empty(name, "Name")
        email = self._validate_email(self._require_non_empty(email, "Email"))

         # check email isn't already taken before we try to insert
        existing = self.db.fetchone("SELECT id FROM members WHERE email = ?", (email,))
        if existing:
            raise ValidationError(f"A member with email '{email}' already exists.")

        joined = date.today().isoformat()
        try:
            cur = self.db.execute(
                "INSERT INTO members (name, email, phone, joined_date, active) "
                "VALUES (?, ?, ?, ?, 1)",
                (name, email, phone.strip(), joined),
            )
        except sqlite3.IntegrityError:
            # the UNIQUE constraint also guards against duplicate emails —
            # translate it into our own error so main.py can catch it
            raise ValidationError(f"A member with email '{email}' already exists.")

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
        member = self.get_member(member_id)   # raises NotFoundError if it doesn't exist

        # only change fields the caller actually passed
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

        try:
            self.db.execute(
                "UPDATE members SET name = ?, email = ?, phone = ? WHERE id = ?",
                (member.name, member.email, member.phone, member.id),
            )
        except sqlite3.IntegrityError:
            raise ValidationError(f"Email '{member.email}' is already used by another member.")
        return member

    def deactivate_member(self, member_id: int) -> Member:
        #delete: flip active to 0 so we keep their loan history
        member = self.get_member(member_id)

        # block deactivation if they still have equipment out
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
        # LIKE with % on both sides = "contains" match.
        # CAST(id AS TEXT) lets people search by id too.

        query = f"%{query.strip()}%"
        rows = self.db.fetchall(
            "SELECT * FROM members WHERE name LIKE ? OR email LIKE ? OR CAST(id AS TEXT) = ? "
            "ORDER BY id",
            (query, query, query.strip("%")),
        )
        return [Member.from_row(r) for r in rows]

    # ------------------------------------------------------------------ #
    # Equipment: Create ; Read ; Update ; Delete(status)
    # ------------------------------------------------------------------ #
    def register_equipment(self, name: str, category: str) -> Equipment:
        # one call = one physical unit. If the space owns 3 soldering kits,
        # register_equipment gets called 3 times.
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
        # WHERE 1=1 is a trick so we can keep appending " AND ..." safely
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
            if status == "borrowed":
                 # "borrowed" only happens through create_loan(), so the
                # equipment status stays in sync with the loans table
                raise ConflictError(
                    "Use the loan checkout feature to mark equipment as borrowed."
                )
            equipment.status = status

        self.db.execute(
            "UPDATE equipment SET name = ?, category = ?, status = ? WHERE id = ?",
            (equipment.name, equipment.category, equipment.status, equipment.id),
        )
        return equipment

    def retire_equipment(self, equipment_id: int) -> Equipment:
        #delete via 'retired' status — keeps its loan history
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
    # Loans: create (checkout) and return, with validation
    # ------------------------------------------------------------------ #
    def create_loan(
        self, member_id: int, equipment_id: int, loan_days: int = DEFAULT_LOAN_DAYS
    ) -> Loan:
        # step 1: member must exist and be active
        member = self.get_member(member_id)
        if not member.is_active():
            raise ConflictError(f"Member {member_id} is deactivated and cannot borrow equipment.")
        
        # step 2: equipment must exist and be available
        equipment = self.get_equipment(equipment_id)
        if not equipment.is_available():
            raise ConflictError(
                f"Equipment '{equipment.name}' is not available (status: {equipment.status})."
            )

        # step 3: extra safety — make sure there isn't already an open loan
        # on this item (catches any status desync)
        open_loan = self.db.fetchone(
            "SELECT id FROM loans WHERE equipment_id = ? AND status = 'open'",
            (equipment_id,),
        )
        if open_loan:
            raise ConflictError(
                f"Equipment '{equipment.name}' already has an open loan "
                f"(loan id {open_loan['id']})."
            )

        # step 4: write the loan and flip the equipment to 'borrowed'
        checkout = date.today()
        due = checkout + timedelta(days=loan_days)
        cur = self.db.execute(
            "INSERT INTO loans (member_id, equipment_id, checkout_date, due_date, status) "
            "VALUES (?, ?, ?, ?, 'open')",
            (member_id, equipment_id, checkout.isoformat(), due.isoformat()),
        )
        equipment.mark_borrowed()    # the object owns its own state change
        self.db.execute(
            "UPDATE equipment SET status = ? WHERE id = ?",
            (equipment.status, equipment_id),
        )

        return Loan(cur.lastrowid, member_id, equipment_id, checkout.isoformat(), due.isoformat())

    def return_loan(self, loan_id: int) -> Loan:
        row = self.db.fetchone("SELECT * FROM loans WHERE id = ?", (loan_id,))
        if not row:
            raise NotFoundError(f"No loan found with id {loan_id}.")
        loan = Loan.from_row(row)
        if loan.status != "open":
            raise ConflictError(f"Loan {loan_id} is already {loan.status}, not open.")

        loan.close(date.today().isoformat())

        # free the equipment in the same step — fetch it as an object first
        equipment = self.get_equipment(loan.equipment_id)
        equipment.mark_available()

        self.db.execute(
            "UPDATE loans SET return_date = ?, status = ? WHERE id = ?",
            (loan.return_date, loan.status, loan_id),
        )
        self.db.execute(
            "UPDATE equipment SET status = ? WHERE id = ?",
            (equipment.status, loan.equipment_id),
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
    # Reports
    # ------------------------------------------------------------------ #
    def report_currently_borrowed(self):
        # JOINs bring in names so the report is human-readable
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
        # "overdue" is calculated here from due_date < today
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
        # GROUP BY = one row per (category, status) pair with a count

        return self.db.fetchall(
            """
            SELECT category, status, COUNT(*) AS count
            FROM equipment
            GROUP BY category, status
            ORDER BY category, status
            """
        )

    def report_member_history(self, member_id: int):
    
        self.get_member(member_id)  # raises NotFoundError if the id is bad
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

    def report_equipment_inventory(self):
        # for each item name: how many units exist, how many are out
        # This is what "one row = one unit" lets us compute.
        return self.db.fetchall(
            """
            SELECT name, category,
                   COUNT(*) AS total_units,
                   SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) AS available_now,
                   SUM(CASE WHEN status = 'borrowed'  THEN 1 ELSE 0 END) AS on_loan
            FROM equipment
            GROUP BY name, category
            ORDER BY category, name
            """
        )