#Opens the database, shows the main menu, and dispatches to the
#sub-menus imported from the menus package.


import sqlite3
import sys

from database import Database
from services import MakerSpaceService
from errors import MakerSpaceError
from menus import (
    members_menu,
    equipment_menu,
    loans_menu,
    reports_menu,
)

DB_FILE = "makerspace.db"


def main_menu(svc: MakerSpaceService) -> None:
    # top-level loop: pick a section, or 0 to exit
    while True:
        print(
            "\n=== Main Menu ===\n"
            "1. Members\n"
            "2. Equipment\n"
            "3. Loans (checkout / return)\n"
            "4. Reports\n"
            "0. Exit"
        )
        try:
            choice = input("Choose: ").strip()
        except EOFError:
            print()
            return  # Ctrl-D = clean exit

        try:
            if choice == "1":
                members_menu(svc)
            elif choice == "2":
                equipment_menu(svc)
            elif choice == "3":
                loans_menu(svc)
            elif choice == "4":
                reports_menu(svc)
            elif choice == "0":
                return
            else:
                print("  Invalid choice, please try again.")
        except MakerSpaceError as e:
            print(f"  Error: {e}")


def main() -> None:
    # open (or create) the database
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
        main_menu(svc)
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting cleanly.")
    finally:
        # always close the DB, even if we exited with an error
        db.close()
        print("Exiting...")
        print("Au revoir!")


if __name__ == "__main__":
    main()