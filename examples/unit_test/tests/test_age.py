import unittest

from src import age


class TestCategorizeByAge(unittest.TestCase):
    def test_child(self):
        "Test child age category"
        self.assertEqual(age.categorize_by_age(5), "Child")

    def test_adolescent(self):
        "Test adolescent age category"
        self.assertEqual(age.categorize_by_age(15), "Adolescent")

    def test_adult(self):
        "Test adult age category"
        self.assertEqual(age.categorize_by_age(30), "Adult")

    def test_golden_age(self):
        "Test golden age category"
        self.assertEqual(age.categorize_by_age(70), "Golden age")

    def test_negative_age(self):
        "Test negative age input"
        self.assertEqual(age.categorize_by_age(-1), "Invalid age: -1")

    def test_too_old(self):
        "Test age input greater than 150"
        self.assertEqual(age.categorize_by_age(151), "Invalid age: 151")

    def test_boundary_child_adolescent(self):
        "Test boundary between child and adolescent"
        self.assertEqual(age.categorize_by_age(9), "Child")
        self.assertEqual(age.categorize_by_age(10), "Adolescent")

    def test_boundary_adolescent_adult(self):
        "Test boundary between adolescent and adult"
        self.assertEqual(age.categorize_by_age(18), "Adolescent")
        self.assertEqual(age.categorize_by_age(19), "Adult")

    def test_boundary_adult_golden_age(self):
        "Test boundary between adult and golden age"
        self.assertEqual(age.categorize_by_age(65), "Adult")
        self.assertEqual(age.categorize_by_age(66), "Golden age")
