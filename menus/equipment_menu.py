"""
menus/equipment_menu.py
-----------------------
Equipment menu: register / list / update / retire / search.
"""

from services import MakerSpaceService
from errors import MakerSpaceError
from menus.common import prompt, prompt_int


def equipment_menu(svc: MakerSpaceService) -> None:
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
                print(f"  Registered: {svc.register_equipment(name, category)}")

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
                name     = prompt("New name: ")
                category = prompt("New category: ")
                status   = prompt("New status (available/maintenance/retired): ")
                updated = svc.update_equipment(
                    eid, name or None, category or None, status or None
                )
                print(f"  Updated: {updated}")

            elif choice == "4":
                eid = prompt_int("Equipment ID to retire (c to cancel): ")
                if eid is None:
                    continue
                print(f"  Retired: {svc.retire_equipment(eid)}")

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