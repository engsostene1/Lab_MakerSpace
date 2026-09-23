"""
menus/common.py
---------------
Shared helpers every menu needs: input prompts and report-row printing.
Kept in one place so we don't repeat them in each menu module.
"""

from typing import Optional


def prompt(text: str) -> str:
    """Read a line of input, strip it, and treat Ctrl-D as a clean exit."""
    try:
        return input(text).strip()
    except EOFError:
        print()
        raise KeyboardInterrupt


def prompt_int(text: str) -> Optional[int]:
    """Keep asking until the user gives a valid integer, or 'c' to cancel."""
    while True:
        raw = prompt(text)
        if raw.lower() in ("c", "cancel"):
            return None
        try:
            return int(raw)
        except ValueError:
            print("  Please enter a whole number (or 'c' to cancel).")


def print_rows(rows, empty_message: str) -> None:
    """Pretty-print a list of sqlite3.Row objects returned by a report."""
    if not rows:
        print(f"  {empty_message}")
        return
    for row in rows:
        parts = [f"{key}={row[key]}" for key in row.keys()]
        print("  " + " | ".join(parts))