"""
menus/members_menu.py
---------------------
Members menu: register / list / update / deactivate / search.
"""

from services import MakerSpaceService
from errors import MakerSpaceError
from menus.common import prompt, prompt_int


def members_menu(svc: MakerSpaceService) -> None:
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
                print(f"  Registered: {svc.register_member(name, email, phone)}")

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
                name  = prompt("New name: ")
                email = prompt("New email: ")
                phone = prompt("New phone: ")
                updated = svc.update_member(mid, name or None, email or None, phone or None)
                print(f"  Updated: {updated}")

            elif choice == "4":
                mid = prompt_int("Member ID to deactivate (c to cancel): ")
                if mid is None:
                    continue
                print(f"  Deactivated: {svc.deactivate_member(mid)}")

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