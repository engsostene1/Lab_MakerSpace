#Domain classes: Member, Equipment, Loan.

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

@dataclass
class Member:      #defines a member who can borrow an equipment

    id: Optional[int]
    name: str
    email: str
    phone: str
    joined_date: str
    active: bool = True

    def is_active(self) -> bool:
        return bool(self.active)

    def deactivate(self) -> None:     #mark this member as inactive
        self.active = False

    def reactivate(self) -> None:
        self.active = True

    @classmethod
    def from_row(cls, row) -> "Member":    #Build a Member from a sqlite3.Row returned by the database layer
        
        return cls(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            phone=row["phone"],
            joined_date=row["joined_date"],
            active=bool(row["active"]),
        )

    def __str__(self) -> str:
        status = "active" if self.active else "inactive"
        return f"[{self.id}] {self.name} <{self.email}> ({status})"


@dataclass
class Equipment:
    # One row = one physical item. Two soldering kits = two rows.

    id: Optional[int]
    name: str
    category: str
    status: str = "available"  # available ; borrowed ; maintenance ; retired
    added_date: str = ""

    VALID_STATUSES = {"available", "borrowed", "maintenance", "retired"}

    def is_available(self) -> bool:
        return self.status == "available"

    def mark_borrowed(self) -> None:
        self.status = "borrowed"

    def mark_available(self) -> None:
        self.status = "available"

    def mark_maintenance(self) -> None:
        self.status = "maintenance"

    def mark_retired(self) -> None:
        self.status = "retired"

    @classmethod
    def from_row(cls, row) -> "Equipment":
        return cls(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            status=row["status"],
            added_date=row["added_date"],
        )

    def __str__(self) -> str:
        return f"[{self.id}] {self.name} ({self.category}) - {self.status}"


@dataclass
class Loan:

    id: Optional[int]
    member_id: int
    equipment_id: int
    checkout_date: str
    due_date: str
    return_date: Optional[str] = None
    #Only "open" and "returned" are stored. Overdue is calculated, not saved.
    status: str = "open"

    def is_returned(self) -> bool:
        return self.status == "returned"

    def is_overdue(self, reference_date: Optional[date] = None) -> bool:
        #Only "open" and "returned" are stored. Overdue is calculated, not saved.
        if self.status != "open":
            return False
        ref = reference_date or date.today()   # allow tests to inject a fake "today"
        due = datetime.strptime(self.due_date, "%Y-%m-%d").date()
        return ref > due

    def close(self, return_date: str) -> None:
        """Mark this loan as returned."""
        self.return_date = return_date
        self.status = "returned"

    @classmethod
    def from_row(cls, row) -> "Loan":
        return cls(
            id=row["id"],
            member_id=row["member_id"],
            equipment_id=row["equipment_id"],
            checkout_date=row["checkout_date"],
            due_date=row["due_date"],
            return_date=row["return_date"],
            status=row["status"],
        )

    def __str__(self) -> str:
        end = self.return_date or "not returned"
        return (
            f"[{self.id}] member={self.member_id} equipment={self.equipment_id} "
            f"out={self.checkout_date} due={self.due_date} back={end} status={self.status}"
        )