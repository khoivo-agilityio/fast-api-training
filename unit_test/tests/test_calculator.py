import unittest

from src.calculator import add


# command to run unit test: python3 -m unittest discover -s unit_test -p "test*.py"
class TestCalculator(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(1, 2), 3)

    def setUp(self):
        self.a = 1
        self.b = 2

    def tearDown(self):
        del self.a
        del self.b


class TestNums(unittest.TestCase):
    def test_even(self):
        for i in range(6):
            with self.subTest(i=i):
                self.assertEqual(i % 2, 0)
