import unittest
from ggufbench import executors

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


class TestExtraFiles(unittest.TestCase):
    """R2/R3 discriminative_tasks: els fitxers de suport existeixen al sandbox."""

    def test_python_sees_fixture(self):
        sol = "def first():\n    return open('data.csv').read().strip()\n"
        tst = "from solution import *\nassert first() == 'alpha\\nbeta'\nprint('OK')\n"
        r = executors.run("python", sol, tst, extra_files={"data.csv": "alpha\nbeta\n"})
        self.assertTrue(r["passed"], r["output"])

    def test_bash_sees_fixture(self):
        sol = 'first() { head -n 1 fixture.txt; }\n'
        tst = 'source solution.sh\n[ "$(first)" = "alpha" ] || exit 1\necho OK\n'
        r = executors.run("bash", sol, tst, extra_files={"fixture.txt": "alpha\nbeta\n"})
        self.assertTrue(r["passed"], r["output"])

    def test_java_helper_class_compiled(self):
        # R3: EXTRA_FILES pot ser una classe de suport compilada amb solution+test
        sol = ('public class Solution { public static int twice(int x){ return Helper.dbl(x); } }\n')
        helper = 'public class Helper { public static int dbl(int x){ return 2*x; } }\n'
        tst = ('public class Test { public static void main(String[] a){\n'
               ' if (Solution.twice(21)!=42) throw new RuntimeException("FAIL");\n'
               ' System.out.println("OK"); } }\n')
        r = executors.run("java", sol, tst, extra_files={"Helper.java": helper})
        self.assertTrue(r["passed"], r["output"])

    def test_typescript_imports_extra_module(self):
        sol = ('import { twice } from "./helper";\n'
               'export function quad(x: number): number { return twice(twice(x)); }\n')
        helper = "export function twice(n: number): number { return n * 2; }\n"
        tst = ('import { quad } from "./solution";\n'
               'if (quad(3) !== 12) throw new Error("FAIL");\nconsole.log("OK");\n')
        r = executors.run("typescript", sol, tst, extra_files={"helper.ts": helper})
        self.assertTrue(r["passed"], r["output"])

    def test_runner_files_win_on_collision(self):
        # Els noms reservats (solution/test) es escriuen DESPRÉS: l'extra no els pot capturar
        sol = "def ok():\n    return 1\n"
        tst = "from solution import *\nassert ok() == 1\nprint('OK')\n"
        r = executors.run("python", sol, tst, extra_files={"solution.py": "BAD"})
        self.assertTrue(r["passed"], r["output"])

    def test_missing_extra_file_fails(self):
        sol = "def first():\n    return open('data.csv').read().strip()\n"
        tst = "from solution import *\nassert first() == 'alpha'\n"
        r = executors.run("python", sol, tst)  # sense extra_files: no hi ha fixture
        self.assertFalse(r["passed"])

if __name__ == "__main__":
    unittest.main()