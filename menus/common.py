#Shared helpers every menu needs: input prompts and report-row printing.

from typing import Optional

def prompt(text: str) -> str:
    # input() with a safety net: Ctrl-D at a prompt means quit cleanly
    try:
        return input(text).strip()
    except EOFError:
        print()
        raise KeyboardInterrupt

def prompt_int(text: str) -> Optional[int]:
    # Keep asking until the user types a whole number, or 'c' to cancel
    while True:
        raw = prompt(text)
        if raw.lower() in ("c", "cancel"):
            return None
        try:
            return int(raw)
        except ValueError:
            print("  Please enter a whole number (or 'c' to cancel).")

def print_rows(rows, empty_message: str) -> None:
    # Reports come back as sqlite3.Row objects, so print each column
    if not rows:
        print(f"  {empty_message}")
        return
    for row in rows:
        parts = [f"{key}={row[key]}" for key in row.keys()]
        print("  " + " | ".join(parts))