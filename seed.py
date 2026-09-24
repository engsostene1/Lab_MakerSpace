# seed.py — fills makerspace.db with sample data so that the system can have 
# something to show on first run. Uses the same MakerSpaceService
# the app uses, so all the normal rules apply.

from datetime import date, timedelta

from database import Database
from services import MakerSpaceService
from errors import MakerSpaceError

DB_FILE = "makerspace.db"


def seed() -> None:
    db = Database(DB_FILE)
    svc = MakerSpaceService(db)

    try:
        # --- Members ---
        ada   = svc.register_member("Ada Lovelace",   "ada@example.com",   "555-1001")
        grace = svc.register_member("Grace Hopper",   "grace@example.com", "555-1002")
        alan  = svc.register_member("Alan Turing",    "alan@example.com",  "555-1003")

        # --- Equipment ---
        # One call = one physical unit. Two soldering kits = two calls.
        printer   = svc.register_equipment("3D Printer",    "Printing")
        camera    = svc.register_equipment("DSLR Camera",   "Photography")
        soldering = svc.register_equipment("Soldering Kit", "Electronics")
        _solder2  = svc.register_equipment("Soldering Kit", "Electronics")
        laptop    = svc.register_equipment("Laptop",        "Computing")

        # --- Loans ---
        # 1) Ada has the printer — still open
        svc.create_loan(ada.id, printer.id, loan_days=14)

        # 2) Grace has the camera — we backdate it so the overdue report fires
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

        # --- Summary ---
        print("Sample data created:")
        print(f"  Members   : 3  (Ada id={ada.id}, Grace id={grace.id}, Alan id={alan.id})")
        print(f"  Equipment : 5  (printer id={printer.id}, camera id={camera.id}, "
              f"soldering ids={soldering.id}/{_solder2.id}, laptop id={laptop.id})")
        print("  Loans     : 3  (1 open, 1 overdue, 1 returned)")
        print()
        print("Try the app:  python main.py")
        print("  Reports -> 1 (currently borrowed), 2 (overdue), 5 (inventory)")

    except MakerSpaceError as e:
        # most likely the sample data already exists
        print(f"Seed skipped: {e}")
        print("(This usually means the sample data already exists.)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()