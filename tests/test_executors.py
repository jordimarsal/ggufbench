import unittest
from benchmark import executors

PY_TEST_PASS = "from solution import *\nassert add(2,3)==5\nprint('OK')\n"
PY_TEST_FAIL = "from solution import *\nassert add(2,3)==6\n"
PY_SOL = "def add(a,b):\n    return a+b\n"
PY_SOL_BAD = "def add(a,b):\n    return a-b\n"

class TestPyExecutor(unittest.TestCase):
    def test_pass(self):
        r = executors.run("python", PY_SOL, PY_TEST_PASS)
        self.assertTrue(r["passed"])
        self.assertIn("OK", r["output"])
    def test_fail(self):
        r = executors.run("python", PY_SOL_BAD, PY_TEST_FAIL)
        self.assertFalse(r["passed"])
        self.assertIn("AssertionError", r["output"])
    def test_no_solution_code(self):
        r = executors.run("python", None, PY_TEST_PASS)
        self.assertFalse(r["passed"])

if __name__ == "__main__":
    unittest.main()