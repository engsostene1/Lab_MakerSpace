# Reports menu.

from services import MakerSpaceService
from errors import MakerSpaceError
from menus.common import prompt, prompt_int, print_rows


def reports_menu(svc: MakerSpaceService) -> None:
    # loop until the user picks 0 (back to main menu)
    while True:
        print(
            "\n--- Reports ---\n"
            "1. Currently borrowed items\n"
            "2. Overdue loans\n"
            "3. Equipment counts by category & status\n"
            "4. Loan history for a member\n"
            "5. Equipment inventory (units per item)\n"
            "0. Back to main menu"
        )
        choice = prompt("Choose: ")

        try:
            if choice == "1":
                print_rows(svc.report_currently_borrowed(),
                           "No equipment is currently on loan.")

            elif choice == "2":
                print_rows(svc.report_overdue_loans(), "No overdue loans. Nice!")

            elif choice == "3":
                print_rows(svc.report_equipment_by_category(),
                           "No equipment registered yet.")

            elif choice == "4":
                mid = prompt_int("Member ID (c to cancel): ")
                if mid is None:
                    continue
                print_rows(svc.report_member_history(mid),
                           "This member has no loan history.")

            elif choice == "5":
                print_rows(svc.report_equipment_inventory(),
                           "No equipment registered yet.")

            elif choice == "0":
                return
            else:
                print("  Invalid choice.")

        except MakerSpaceError as e:
            print(f"  Error: {e}")