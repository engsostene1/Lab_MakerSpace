"""
seed.py
-------
Populate makerspace.db with sample data so the app has something to show
when it's first run. Uses the same MakerSpaceService the app uses, so it
exercises the normal validation and business rules.

Run with:
    python3 seed.py

Safe to run on a fresh database. If the sample members already exist
(same emails), it prints a note and exits without creating duplicates.
"""

from datetime import date, timedelta

from database import Database
from services import MakerSpaceService
from errors import MakerSpaceError

DB_FILE = "makerspace.db"


def seed() -> None:
    db = Database(DB_FILE)
    svc = MakerSpaceService(db)

    try:
        # ------------------------------------------------------------------
        # Members
        # ------------------------------------------------------------------
        ada   = svc.register_member("Ada Lovelace",   "ada@example.com",   "555-1001")
        grace = svc.register_member("Grace Hopper",   "grace@example.com", "555-1002")
        alan  = svc.register_member("Alan Turing",    "alan@example.com",  "555-1003")

        # ------------------------------------------------------------------
        # Equipment — note: one row per PHYSICAL unit.
        # Three soldering kits = three register_equipment calls.
        # ------------------------------------------------------------------
        printer   = svc.register_equipment("3D Printer",    "Printing")
        camera    = svc.register_equipment("DSLR Camera",   "Photography")
        soldering = svc.register_equipment("Soldering Kit", "Electronics")
        _solder2  = svc.register_equipment("Soldering Kit", "Electronics")  # 2nd copy
        laptop    = svc.register_equipment("Laptop",        "Computing")

        # ------------------------------------------------------------------
        # Loans — create a mix of open, overdue, and returned
        # ------------------------------------------------------------------
        # 1) Ada has the printer — still open
        svc.create_loan(ada.id, printer.id, loan_days=14)

        # 2) Grace has the camera — we'll backdate this to make it overdue
        overdue_loan = svc.create_loan(grace.id, camera.id, loan_days=14)
        past_checkout = (date.today() - timedelta(days=20)).isoformat()
        past_due      = (date.today() - timedelta(days=6)).isoformat()
        db.execute(
            "UPDATE loans SET checkout_date = ?, due_date = ? WHERE id = ?",
            (past_checkout, past_due, overdue_loan.id),
        )

        # 3) Alan borrowed a soldering kit and already returned it
        returned_loan = svc.create_loan(alan.id, soldering.id, loan_days=7)
        svc.return_loan(returned_loan.id)

        # ------------------------------------------------------------------
        # Summary
        # ------------------------------------------------------------------
        print("Sample data created:")
        print(f"  Members   : 3  (Ada id={ada.id}, Grace id={grace.id}, Alan id={alan.id})")
        print(f"  Equipment : 5  (printer id={printer.id}, camera id={camera.id}, "
              f"soldering ids={soldering.id}/{_solder2.id}, laptop id={laptop.id})")
        print("  Loans     : 3  (1 open, 1 overdue, 1 returned)")
        print()
        print("Try the app:  python3 main.py")
        print("  Reports -> 1 (currently borrowed), 2 (overdue), 5 (inventory)")

    except MakerSpaceError as e:
        print(f"Seed skipped: {e}")
        print("(This usually means the sample data already exists.)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()