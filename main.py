"""
main.py
-------
Entry point for the Campus MakerSpace Checkout System.

This file only:
    - opens the database,
    - shows the main menu,
    - dispatches to the four sub-menu functions from the `menus` package,
    - handles Ctrl-C and closes the DB cleanly.

All real logic lives in services.py / models.py / database.py.
Each sub-menu lives in its own module under menus/.
Run with:  python main.py
"""

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
    """Show the top-level menu and dispatch to sub-menus until Exit."""
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
            return

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
        db.close()
        print("Goodbye!")


if __name__ == "__main__":
    main()