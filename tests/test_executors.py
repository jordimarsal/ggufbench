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
    def test_bash_pass(self):
        sol = 'add() { echo $(($1+$2)); }\n'
        tst = 'source solution.sh\n[ "$(add 2 3)" = "5" ] || { echo FAIL; exit 1; }\necho OK\n'
        r = executors.run("bash", sol, tst)
        self.assertTrue(r["passed"])
    def test_bash_fail(self):
        sol = 'add() { echo $(($1-$2)); }\n'
        tst = 'source solution.sh\n[ "$(add 2 3)" = "5" ] || exit 1\n'
        r = executors.run("bash", sol, tst)
        self.assertFalse(r["passed"])
    def test_java_pass(self):
        sol = 'public class Solution { public static int add(int a,int b){ return a+b; } }\n'
        tst = ('public class Test { public static void main(String[] a){\n'
               ' if (Solution.add(2,3)!=5) throw new RuntimeException("FAIL");\n'
               ' System.out.println("OK"); } }\n')
        r = executors.run("java", sol, tst)
        self.assertTrue(r["passed"], r["output"])
    def test_java_fail(self):
        sol = 'public class Solution { public static int add(int a,int b){ return a-b; } }\n'
        tst = ('public class Test { public static void main(String[] a){\n'
               ' if (Solution.add(2,3)!=5) throw new RuntimeException("FAIL"); } }\n')
        r = executors.run("java", sol, tst)
        self.assertFalse(r["passed"])
    def test_typescript_pass(self):
        sol = 'export function add(a:number,b:number):number { return a+b; }\n'
        tst = 'import { add } from "./solution";\nif (add(2,3)!==5) throw new Error("FAIL");\nconsole.log("OK");\n'
        r = executors.run("typescript", sol, tst)
        self.assertTrue(r["passed"], r["output"])

if __name__ == "__main__":
    unittest.main()