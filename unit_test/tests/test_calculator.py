import unittest

from app.calculator import add


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
