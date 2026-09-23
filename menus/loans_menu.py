"""
menus/loans_menu.py
-------------------
Loans menu: create checkout / return / list open / list all.
"""

from services import MakerSpaceService
from errors import MakerSpaceError
from menus.common import prompt, prompt_int


def loans_menu(svc: MakerSpaceService) -> None:
    while True:
        print(
            "\n--- Loans ---\n"
            "1. Create loan (checkout)\n"
            "2. Return a loan\n"
            "3. List open loans\n"
            "4. List all loans\n"
            "0. Back to main menu"
        )
        choice = prompt("Choose: ")

        try:
            if choice == "1":
                mid = prompt_int("Member ID (c to cancel): ")
                if mid is None:
                    continue
                eid = prompt_int("Equipment ID (c to cancel): ")
                if eid is None:
                    continue
                days_raw = prompt("Loan length in days [default 14, 'c' to cancel]: ")
                if days_raw.lower() in ("c", "cancel"):
                    continue
                if not days_raw:
                    days = 14
                else:
                    try:
                        days = int(days_raw)
                        if days <= 0:
                            print("  Loan length must be positive. Using default 14.")
                            days = 14
                    except ValueError:
                        print(f"  '{days_raw}' is not a number. Using default 14.")
                        days = 14
                print(f"  Loan created: {svc.create_loan(mid, eid, days)}")

            elif choice == "2":
                lid = prompt_int("Loan ID to return (c to cancel): ")
                if lid is None:
                    continue
                print(f"  Returned: {svc.return_loan(lid)}")

            elif choice == "3":
                loans = svc.list_loans(status="open")
                if not loans:
                    print("  No open loans.")
                for l in loans:
                    print(" ", l)

            elif choice == "4":
                loans = svc.list_loans()
                if not loans:
                    print("  No loans on record.")
                for l in loans:
                    print(" ", l)

            elif choice == "0":
                return
            else:
                print("  Invalid choice.")

        except MakerSpaceError as e:
            print(f"  Error: {e}")