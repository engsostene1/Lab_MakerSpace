# Campus MakerSpace Checkout System

A command-line Python app for a student makerspace. It keeps track of
members, equipment, and loans in a small SQLite database so we don't
lose track of who borrowed what.

## What it does

- Register, list, update, and deactivate members
- Register, list, update, and retire equipment
- Create a loan (checkout) with validation — the member must exist and
  be active, and the equipment must be available
- Return a loan and free up the equipment
- Search members and equipment by name, category, or id
- Five reports: currently borrowed, overdue loans, equipment by
  category, member loan history, and equipment inventory
- Input is validated everywhere, so bad input gives a clear error
  message instead of crashing

## Project layout

```
Lab_MakerSpace/
├── main.py               # main menu, entry point
├── menus/                # one file per sub-menu
│   ├── common.py
│   ├── members_menu.py
│   ├── equipment_menu.py
│   ├── loans_menu.py
│   └── reports_menu.py
├── models.py             # Member, Equipment, Loan classes
├── database.py           # SQLite connection and schema
├── services.py           # business logic and SQL
├── errors.py             # custom exception classes
├── seed.py               # optional: fill the DB with sample data
├── tests/
│   └── test_app.py       # unit tests
├── requirements.txt
├── README.md
└── DESIGN.md
```

## Requirements

- Python 3.9 or newer
- Nothing to install — sqlite3 ships with Python

## How to run it

```bash
git clone <your-repo-url>
cd Lab_MakerSpace
python main.py
```

The first time you run it, the app creates `makerspace.db` and the three
tables it needs. The database file stays there between runs, so your
data is saved.

## Sample data (optional)

If you want the app to start with something in it:

```bash
python seed.py
```

This adds three members, a few pieces of equipment (including two of the
same item, so the "one row per unit" idea is visible), and three loans —
one open, one overdue, and one returned. Then all five reports have
something to show.

## How to run the tests

```bash
python -m unittest discover -s tests -v
```

The tests use an in-memory database, so they never touch your real
`makerspace.db`. They cover the validation rules, loan creation and
return, and all five reports.

## A quick tour of the classes

- **Member** — a person who can borrow things. Knows if it's active and
  how to activate/deactivate itself.
- **Equipment** — one physical item. Two soldering kits = two rows. Knows
  its own status (available, borrowed, maintenance, retired).
- **Loan** — one checkout event, linking a member and a piece of
  equipment. Knows if it's overdue and how to close itself.
- **Database** — owns the SQLite connection. Creates the schema and
  gives simple `execute` / `fetchone` / `fetchall` helpers.
- **MakerSpaceService** — the brain. Validates input, applies rules, and
  coordinates the models with the database.

Three rules keep the layers separate:

1. Only `database.py` imports `sqlite3`.
2. Only `services.py` raises custom exceptions.
3. Only `main.py` and the menu files catch `MakerSpaceError`.

## Database schema

Three tables, kept simple:

- `members(id, name, email, phone, joined_date, active)`
- `equipment(id, name, category, status, added_date)`
- `loans(id, member_id, equipment_id, checkout_date, due_date, return_date, status)`

Members and equipment are never actually deleted — we flip a flag
(`active = 0`) or a status (`retired`) so their loan history stays
intact. And "overdue" is not stored anywhere; it's calculated from
`due_date < today`.
More detail in DESIGN.md