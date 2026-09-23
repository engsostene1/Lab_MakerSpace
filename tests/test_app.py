"""
tests/test_app.py
------------------
Unit tests for the Campus MakerSpace Checkout System.

Run with:
    python -m unittest discover -s tests -v

Each test uses a fresh in-memory SQLite database (":memory:") so tests
never touch or depend on the real makerspace.db file, and tests are
fully isolated from each other.
"""

import sys
import os
import unittest
from datetime import date, timedelta

# Make the project root importable when running tests from /tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import Database
from services import MakerSpaceService
from errors import ValidationError, NotFoundError, ConflictError
from models import Loan, Member, Equipment


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")
        self.svc = MakerSpaceService(self.db)

    def tearDown(self):
        self.db.close()


class TestMembers(BaseTestCase):
    def test_register_member_success(self):
        member = self.svc.register_member("Ada Lovelace", "ada@example.com", "555-1000")
        self.assertIsNotNone(member.id)
        self.assertEqual(member.name, "Ada Lovelace")
        self.assertTrue(member.is_active())

    def test_register_member_duplicate_email_rejected(self):
        self.svc.register_member("Ada", "ada@example.com")
        with self.assertRaises(ValidationError):
            self.svc.register_member("Ada Two", "ada@example.com")

    def test_register_member_invalid_email_rejected(self):
        with self.assertRaises(ValidationError):
            self.svc.register_member("Bad Email", "not-an-email")

    def test_register_member_empty_name_rejected(self):
        with self.assertRaises(ValidationError):
            self.svc.register_member("   ", "someone@example.com")

    def test_list_members(self):
        self.svc.register_member("A", "a@example.com")
        self.svc.register_member("B", "b@example.com")
        members = self.svc.list_members()
        self.assertEqual(len(members), 2)

    def test_list_members_active_only(self):
        m1 = self.svc.register_member("A", "a@example.com")
        m2 = self.svc.register_member("B", "b@example.com")
        self.svc.deactivate_member(m2.id)
        active = self.svc.list_members(active_only=True)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].id, m1.id)

    def test_get_member_not_found(self):
        with self.assertRaises(NotFoundError):
            self.svc.get_member(9999)

    def test_update_member(self):
        m = self.svc.register_member("Grace Hopper", "grace@example.com")
        updated = self.svc.update_member(m.id, phone="555-2000")
        self.assertEqual(updated.phone, "555-2000")
        self.assertEqual(updated.name, "Grace Hopper")  # unchanged

    def test_update_nonexistent_member_raises(self):
        with self.assertRaises(NotFoundError):
            self.svc.update_member(999, name="Ghost")

    def test_deactivate_member(self):
        m = self.svc.register_member("Alan Turing", "alan@example.com")
        deactivated = self.svc.deactivate_member(m.id)
        self.assertFalse(deactivated.is_active())

    def test_deactivate_member_with_open_loan_blocked(self):
        m = self.svc.register_member("Alan Turing", "alan@example.com")
        e = self.svc.register_equipment("Soldering Iron", "Electronics")
        self.svc.create_loan(m.id, e.id)
        with self.assertRaises(ConflictError):
            self.svc.deactivate_member(m.id)

    def test_search_members(self):
        self.svc.register_member("Katherine Johnson", "kj@example.com")
        results = self.svc.search_members("Katherine")
        self.assertEqual(len(results), 1)


class TestEquipment(BaseTestCase):
    def test_register_and_list_equipment(self):
        self.svc.register_equipment("3D Printer", "Printing")
        self.svc.register_equipment("DSLR Camera", "Photography")
        items = self.svc.list_equipment()
        self.assertEqual(len(items), 2)
        self.assertTrue(all(i.is_available() for i in items))

    def test_get_equipment_not_found(self):
        with self.assertRaises(NotFoundError):
            self.svc.get_equipment(9999)

    def test_update_equipment_name_and_category(self):
        e = self.svc.register_equipment("Old", "Misc")
        updated = self.svc.update_equipment(e.id, name="New", category="Tools")
        self.assertEqual(updated.name, "New")
        self.assertEqual(updated.category, "Tools")

    def test_update_equipment_invalid_status_rejected(self):
        e = self.svc.register_equipment("Laptop", "Computing")
        with self.assertRaises(ValidationError):
            self.svc.update_equipment(e.id, status="broken")

    def test_update_equipment_cannot_set_borrowed(self):
        e = self.svc.register_equipment("Laptop", "Computing")
        with self.assertRaises(ConflictError):
            self.svc.update_equipment(e.id, status="borrowed")

    def test_retire_equipment(self):
        e = self.svc.register_equipment("Old Laptop", "Computing")
        retired = self.svc.retire_equipment(e.id)
        self.assertEqual(retired.status, "retired")

    def test_retire_borrowed_equipment_blocked(self):
        m = self.svc.register_member("Test User", "tu@example.com")
        e = self.svc.register_equipment("Camera", "Photography")
        self.svc.create_loan(m.id, e.id)
        with self.assertRaises(ConflictError):
            self.svc.retire_equipment(e.id)

    def test_filter_equipment_by_category(self):
        self.svc.register_equipment("3D Printer", "Printing")
        self.svc.register_equipment("Laser Cutter", "Printing")
        self.svc.register_equipment("Camera", "Photography")
        printing_items = self.svc.list_equipment(category="Printing")
        self.assertEqual(len(printing_items), 2)

    def test_search_equipment(self):
        self.svc.register_equipment("3D Printer", "Printing")
        self.svc.register_equipment("Camera", "Photography")
        results = self.svc.search_equipment("Printer")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "3D Printer")


class TestLoans(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.member = self.svc.register_member("Loan Tester", "loan@example.com")
        self.equipment = self.svc.register_equipment("Camera", "Photography")

    def test_create_loan_marks_equipment_borrowed(self):
        loan = self.svc.create_loan(self.member.id, self.equipment.id)
        self.assertEqual(loan.status, "open")
        equipment_after = self.svc.get_equipment(self.equipment.id)
        self.assertEqual(equipment_after.status, "borrowed")

    def test_cannot_borrow_unavailable_equipment(self):
        self.svc.create_loan(self.member.id, self.equipment.id)
        with self.assertRaises(ConflictError):
            self.svc.create_loan(self.member.id, self.equipment.id)

    def test_cannot_borrow_with_unknown_member(self):
        with self.assertRaises(NotFoundError):
            self.svc.create_loan(9999, self.equipment.id)

    def test_cannot_borrow_with_unknown_equipment(self):
        with self.assertRaises(NotFoundError):
            self.svc.create_loan(self.member.id, 9999)

    def test_deactivated_member_cannot_borrow(self):
        self.svc.deactivate_member(self.member.id)
        with self.assertRaises(ConflictError):
            self.svc.create_loan(self.member.id, self.equipment.id)

    def test_return_loan_frees_equipment(self):
        loan = self.svc.create_loan(self.member.id, self.equipment.id)
        returned = self.svc.return_loan(loan.id)
        self.assertEqual(returned.status, "returned")
        equipment_after = self.svc.get_equipment(self.equipment.id)
        self.assertTrue(equipment_after.is_available())

    def test_cannot_return_already_returned_loan(self):
        loan = self.svc.create_loan(self.member.id, self.equipment.id)
        self.svc.return_loan(loan.id)
        with self.assertRaises(ConflictError):
            self.svc.return_loan(loan.id)

    def test_return_unknown_loan_raises(self):
        with self.assertRaises(NotFoundError):
            self.svc.return_loan(9999)

    def test_list_loans_filters_by_status(self):
        loan = self.svc.create_loan(self.member.id, self.equipment.id)
        open_loans = self.svc.list_loans(status="open")
        self.assertEqual(len(open_loans), 1)
        self.svc.return_loan(loan.id)
        open_loans = self.svc.list_loans(status="open")
        self.assertEqual(len(open_loans), 0)


class TestReports(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.member = self.svc.register_member("Report Tester", "report@example.com")
        self.equipment = self.svc.register_equipment("Laptop", "Computing")

    def test_currently_borrowed_report(self):
        self.svc.create_loan(self.member.id, self.equipment.id)
        rows = self.svc.report_currently_borrowed()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["member_name"], "Report Tester")

    def test_overdue_report_detects_overdue_loan(self):
        loan = self.svc.create_loan(self.member.id, self.equipment.id, loan_days=14)
        # Manually push the due_date into the past to simulate an overdue loan.
        past_due = (date.today() - timedelta(days=1)).isoformat()
        self.db.execute("UPDATE loans SET due_date = ? WHERE id = ?", (past_due, loan.id))
        rows = self.svc.report_overdue_loans()
        self.assertEqual(len(rows), 1)

    def test_overdue_report_excludes_future_due_dates(self):
        self.svc.create_loan(self.member.id, self.equipment.id, loan_days=14)
        rows = self.svc.report_overdue_loans()
        self.assertEqual(len(rows), 0)

    def test_equipment_by_category_report(self):
        self.svc.register_equipment("Camera", "Photography")
        rows = self.svc.report_equipment_by_category()
        categories = {row["category"] for row in rows}
        self.assertIn("Computing", categories)
        self.assertIn("Photography", categories)

    def test_member_history_report(self):
        loan = self.svc.create_loan(self.member.id, self.equipment.id)
        self.svc.return_loan(loan.id)
        rows = self.svc.report_member_history(self.member.id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "returned")

    def test_inventory_report_counts_copies(self):
        self.svc.register_equipment("Soldering Kit", "Electronics")
        self.svc.register_equipment("Soldering Kit", "Electronics")
        self.svc.register_equipment("Soldering Kit", "Electronics")
        rows = self.svc.report_equipment_inventory()
        kit = next(r for r in rows if r["name"] == "Soldering Kit")
        self.assertEqual(kit["total_units"], 3)
        self.assertEqual(kit["available_now"], 3)
        self.assertEqual(kit["on_loan"], 0)


class TestModels(unittest.TestCase):
    """Model-level tests that don't need the database at all."""

    def test_is_overdue_true_when_past_due(self):
        loan = Loan(id=1, member_id=1, equipment_id=1,
                    checkout_date="2024-01-01", due_date="2024-01-08",
                    status="open")
        self.assertTrue(loan.is_overdue(reference_date=date(2024, 1, 10)))

    def test_is_overdue_false_when_not_yet_due(self):
        loan = Loan(id=1, member_id=1, equipment_id=1,
                    checkout_date="2024-01-01", due_date="2024-01-08",
                    status="open")
        self.assertFalse(loan.is_overdue(reference_date=date(2024, 1, 5)))

    def test_is_overdue_false_once_returned(self):
        loan = Loan(id=1, member_id=1, equipment_id=1,
                    checkout_date="2024-01-01", due_date="2024-01-08",
                    status="returned")
        self.assertFalse(loan.is_overdue(reference_date=date(2024, 6, 1)))

    def test_loan_close_sets_returned(self):
        loan = Loan(id=1, member_id=1, equipment_id=1,
                    checkout_date="2024-01-01", due_date="2024-01-08")
        loan.close("2024-01-05")
        self.assertEqual(loan.status, "returned")
        self.assertEqual(loan.return_date, "2024-01-05")
        self.assertTrue(loan.is_returned())

    def test_member_deactivate_and_reactivate(self):
        m = Member(id=1, name="X", email="x@example.com",
                   phone="", joined_date="2024-01-01")
        self.assertTrue(m.is_active())
        m.deactivate()
        self.assertFalse(m.is_active())
        m.reactivate()
        self.assertTrue(m.is_active())

    def test_equipment_status_transitions(self):
        e = Equipment(id=1, name="Drill", category="Tools")
        self.assertTrue(e.is_available())
        e.mark_borrowed()
        self.assertFalse(e.is_available())
        e.mark_available()
        self.assertTrue(e.is_available())
        e.mark_maintenance()
        self.assertEqual(e.status, "maintenance")
        e.mark_retired()
        self.assertEqual(e.status, "retired")


if __name__ == "__main__":
    unittest.main()
