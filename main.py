"""
main.py
-------
Application entry point: a menu-driven CLI for the Campus MakerSpace
Checkout System. This file only handles:
    - printing menus,
    - reading/validating raw console input,
    - calling MakerSpaceService methods,
    - printing results / catching errors nicely.

All real logic lives in services.py / models.py / database.py.
Run with:  python main.py
"""

import sqlite3
import sys

from database import Database
from services import MakerSpaceService
from errors import MakerSpaceError

DB_FILE = "makerspace.db"


# ---------------------------------------------------------------------- #
# Small input helpers - keep main() readable and avoid crashes on bad input
# ---------------------------------------------------------------------- #
def prompt(text: str) -> str:
    return input(text).strip()


def prompt_int(text: str):
    """Keep asking until the user gives a valid integer, or 'c' to cancel."""
    while True:
        raw = input(text).strip()
        if raw.lower() in ("c", "cancel"):
            return None
        try:
            return int(raw)
        except ValueError:
            print("  Please enter a whole number (or 'c' to cancel).")


def pause():
    input("\nPress Enter to continue...")


# ---------------------------------------------------------------------- #
# Menu sections
# ---------------------------------------------------------------------- #
def members_menu(svc: MakerSpaceService):
    while True:
        print(
            "\n--- Members ---\n"
            "1. Register new member\n"
            "2. List all members\n"
            "3. Update member\n"
            "4. Deactivate member\n"
            "5. Search members\n"
            "0. Back to main menu"
        )
        choice = prompt("Choose: ")

        try:
            if choice == "1":
                name = prompt("Name: ")
                email = prompt("Email: ")
                phone = prompt("Phone (optional): ")
                member = svc.register_member(name, email, phone)
                print(f"  Registered: {member}")

            elif choice == "2":
                members = svc.list_members()
                if not members:
                    print("  No members registered yet.")
                for m in members:
                    print(" ", m)

            elif choice == "3":
                mid = prompt_int("Member ID to update (c to cancel): ")
                if mid is None:
                    continue
                print("  Leave a field blank to keep it unchanged.")
                name = prompt("New name: ")
                email = prompt("New email: ")
                phone = prompt("New phone: ")
                member = svc.update_member(
                    mid, name or None, email or None, phone or None
                )
                print(f"  Updated: {member}")

            elif choice == "4":
                mid = prompt_int("Member ID to deactivate (c to cancel): ")
                if mid is None:
                    continue
                member = svc.deactivate_member(mid)
                print(f"  Deactivated: {member}")

            elif choice == "5":
                q = prompt("Search text (name/email/id): ")
                results = svc.search_members(q)
                if not results:
                    print("  No matches.")
                for m in results:
                    print(" ", m)

            elif choice == "0":
                return
            else:
                print("  Invalid choice.")

        except MakerSpaceError as e:
            print(f"  Error: {e}")


def equipment_menu(svc: MakerSpaceService):
    while True:
        print(
            "\n--- Equipment ---\n"
            "1. Register new equipment\n"
            "2. List all equipment\n"
            "3. Update equipment\n"
            "4. Retire equipment\n"
            "5. Search equipment\n"
            "0. Back to main menu"
        )
        choice = prompt("Choose: ")

        try:
            if choice == "1":
                name = prompt("Equipment name: ")
                category = prompt("Category: ")
                eq = svc.register_equipment(name, category)
                print(f"  Registered: {eq}")

            elif choice == "2":
                items = svc.list_equipment()
                if not items:
                    print("  No equipment registered yet.")
                for e in items:
                    print(" ", e)

            elif choice == "3":
                eid = prompt_int("Equipment ID to update (c to cancel): ")
                if eid is None:
                    continue
                print("  Leave a field blank to keep it unchanged.")
                name = prompt("New name: ")
                category = prompt("New category: ")
                status = prompt("New status (available/maintenance/retired): ")
                eq = svc.update_equipment(
                    eid, name or None, category or None, status or None
                )
                print(f"  Updated: {eq}")

            elif choice == "4":
                eid = prompt_int("Equipment ID to retire (c to cancel): ")
                if eid is None:
                    continue
                eq = svc.retire_equipment(eid)
                print(f"  Retired: {eq}")

            elif choice == "5":
                q = prompt("Search text (name/category/id): ")
                results = svc.search_equipment(q)
                if not results:
                    print("  No matches.")
                for e in results:
                    print(" ", e)

            elif choice == "0":
                return
            else:
                print("  Invalid choice.")

        except MakerSpaceError as e:
            print(f"  Error: {e}")


def loans_menu(svc: MakerSpaceService):
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
                days_raw = prompt("Loan length in days [default 14]: ")
                days = int(days_raw) if days_raw.isdigit() else 14
                loan = svc.create_loan(mid, eid, days)
                print(f"  Loan created: {loan}")

            elif choice == "2":
                lid = prompt_int("Loan ID to return (c to cancel): ")
                if lid is None:
                    continue
                loan = svc.return_loan(lid)
                print(f"  Returned: {loan}")

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


def reports_menu(svc: MakerSpaceService):
    while True:
        print(
            "\n--- Reports ---\n"
            "1. Currently borrowed items\n"
            "2. Overdue loans\n"
            "3. Equipment counts by category & status\n"
            "4. Loan history for a member\n"
            "0. Back to main menu"
        )
        choice = prompt("Choose: ")

        try:
            if choice == "1":
                rows = svc.report_currently_borrowed()
                _print_rows(rows, "No equipment is currently on loan.")

            elif choice == "2":
                rows = svc.report_overdue_loans()
                _print_rows(rows, "No overdue loans. Nice!")

            elif choice == "3":
                rows = svc.report_equipment_by_category()
                _print_rows(rows, "No equipment registered yet.")

            elif choice == "4":
                mid = prompt_int("Member ID (c to cancel): ")
                if mid is None:
                    continue
                rows = svc.report_member_history(mid)
                _print_rows(rows, "This member has no loan history.")

            elif choice == "0":
                return
            else:
                print("  Invalid choice.")

        except MakerSpaceError as e:
            print(f"  Error: {e}")


def _print_rows(rows, empty_message: str):
    """Pretty-print a list of sqlite3.Row objects from a report query."""
    if not rows:
        print(f"  {empty_message}")
        return
    for row in rows:
        parts = [f"{key}={row[key]}" for key in row.keys()]
        print("  " + " | ".join(parts))


# ---------------------------------------------------------------------- #
# Main menu / entry point
# ---------------------------------------------------------------------- #
def main():
    try:
        db = Database(DB_FILE)
    except sqlite3.Error as e:
        print(f"Fatal error: could not open database '{DB_FILE}': {e}")
        sys.exit(1)

    svc = MakerSpaceService(db)

    print("=" * 50)
    print(" Campus MakerSpace Checkout System")
    print(f" Database file: {DB_FILE}")
    print("=" * 50)

    try:
        while True:
            print(
                "\n=== Main Menu ===\n"
                "1. Members\n"
                "2. Equipment\n"
                "3. Loans (checkout / return)\n"
                "4. Reports\n"
                "0. Exit"
            )
            choice = prompt("Choose: ")

            if choice == "1":
                members_menu(svc)
            elif choice == "2":
                equipment_menu(svc)
            elif choice == "3":
                loans_menu(svc)
            elif choice == "4":
                reports_menu(svc)
            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("  Invalid choice, please try again.")
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting cleanly.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
