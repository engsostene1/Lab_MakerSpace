"""
seed.py — populate makerspace.db with sample data for demonstration.

Run with: python3 seed.py
"""
from database import Database
from services import MakerSpaceService
from errors import MakerSpaceError

def seed():
    db = Database("makerspace.db")
    svc = MakerSpaceService(db)
    try:
        # Members
        ada = svc.register_member("Ada Lovelace", "ada@example.com", "555-1001")
        grace = svc.register_member("Grace Hopper", "grace@example.com", "555-1002")
        alan = svc.register_member("Alan Turing", "alan@example.com", "555-1003")

        # Equipment
        printer = svc.register_equipment("3D Printer", "Printing")
        camera = svc.register_equipment("DSLR Camera", "Photography")
        soldering = svc.register_equipment("Soldering Kit", "Electronics")
        laptop = svc.register_equipment("Laptop", "Computing")

        # Loans — including one that will be overdue
        svc.create_loan(ada.id, printer.id)          # active
        loan = svc.create_loan(grace.id, camera.id)  # will be made overdue
        svc.return_loan(svc.create_loan(alan.id, soldering.id).id)  # returned

        # Force one loan to be overdue for the demo
        import datetime
        past = (datetime.date.today() - datetime.timedelta(days=20)).isoformat()
        db.execute("UPDATE loans SET checkout_date = ?, due_date = ? WHERE id = ?",
                   (past, past, loan.id))

        print("Seeded sample data:")
        print("  Members: 3 (Ada, Grace, Alan)")
        print("  Equipment: 4 (printer, camera, soldering kit, laptop)")
        print("  Loans: 3 (1 active, 1 overdue, 1 returned)")
    except MakerSpaceError as e:
        print(f"Seed skipped: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()