# Campus MakerSpace Checkout System

An Object-Oriented Python CLI application, backed by SQLite, for managing
members, equipment, and loans in a student makerspace.

## Features

- Register / list / update / deactivate **members**
- Register / list / update / retire **equipment** (with availability status)
- **Create a loan** (checkout) with validation — member must exist and be
  active, equipment must exist and be available
- **Return a loan** — updates the loan and frees up the equipment
- **Search** members and equipment by name, category, or ID
- **Four report/query features** built from SQL:
  1. Currently borrowed items
  2. Overdue loans
  3. Equipment counts by category and status
  4. Full loan history for a given member
- Input validation and clear error messages everywhere — the app is
  designed not to crash on bad input.

## Project structure

```
Lab_MakerSpace/
├── main.py          # menu loop and application entry point
├── models.py         # domain classes: Member, Equipment, Loan
├── database.py        # SQLite connection, schema creation, SQL helpers
├── services.py        # business logic that coordinates models + database
├── errors.py          # custom exception types (ValidationError, NotFoundError, ConflictError)
├── requirements.txt    # dependencies (none beyond the standard library)
├── tests/
│   └── test_app.py    # unit tests (30 tests, run with unittest)
├── DESIGN.md          # class design notes and entity-relationship overview
└── README.md
```

## Requirements

- Python 3.9+
- No third-party packages required — `sqlite3` is part of the standard library.

## How to run

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd Lab_MakerSpace

# 2. (Optional) create a virtual environment
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate

# 3. Run the application
python3 main.py
```

On first run, the app automatically creates `makerspace.db` in the project
folder and sets up the `members`, `equipment`, and `loans` tables. On every
later run it reuses the same file, so your data persists between sessions.

## How to run the tests

```bash
python3 -m unittest discover -s tests -v
```

This runs 30 unit tests covering member/equipment/loan validation rules,
loan creation/return logic, and all four reports, using an in-memory
SQLite database so the tests never touch your real `makerspace.db`.

## Class design overview

- **`Member`** — a person who can borrow equipment. Knows whether it is
  active (`is_active`) and how to deactivate/reactivate itself.
- **`Equipment`** — a borrowable item. Knows its own availability
  (`is_available`) and how to transition between `available`, `borrowed`,
  `maintenance`, and `retired` states.
- **`Loan`** — one checkout event linking a member and an item. Knows
  whether it `is_overdue()` and how to `close()` itself when returned.
- **`MakerSpaceService`** — coordinates all three model classes together
  with the database: this is where "object collaboration" happens (e.g.
  `create_loan` checks a `Member`, checks an `Equipment`, and only then
  writes a new `Loan` row and flips the equipment's status).

See `DESIGN.md` for the entity-relationship diagram and more detail on
design decisions (soft deletes, validation strategy, etc.).

## Sample data (optional)

To populate the database with demo data:
    python3 seed.py
This creates 3 members, 4 equipment items, and 3 loans (including one overdue).

## Database schema (summary)

- `members(id, name, email UNIQUE, phone, joined_date, active)`
- `equipment(id, name, category, status, added_date)`
- `loans(id, member_id FK, equipment_id FK, checkout_date, due_date, return_date, status)`

`members` and `equipment` are never hard-deleted — they use soft-delete
style status fields (`active` / `status='retired'`) so loan history stays
intact and referential integrity is preserved.

## Use of Generative AI

Generative AI (Claude) was used to help design and generate an initial
version of this codebase, per the assessment brief's permitted use of AI
tools. All code was reviewed, run, and tested locally before submission.
**Remember to add your own AI-use disclosure statement here, per your
module's specific requirements, before submitting.**
