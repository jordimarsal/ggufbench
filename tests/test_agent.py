import shutil
import unittest
from ggufbench import agent, executors

# run_tests for java shells out to javac; skip on machines without the toolchain.
HAS_JAVAC = shutil.which("javac") is not None
HAS_SANDBOX = executors._probe_sandbox()

@unittest.skipUnless(HAS_SANDBOX, "host cannot create isolated namespaces (unshare -Urn); code-execution coverage runs on sandboxed hosts")
class TestMockEnv(unittest.TestCase):
    def test_read_write(self):
        e = agent.MockEnv({"a.py": "x=1"}, "python")
        self.assertEqual(e.read_file("a.py"), "x=1")
        e.write_file("a.py", "x=2")
        self.assertEqual(e.read_file("a.py"), "x=2")
    def test_read_missing(self):
        e = agent.MockEnv({}, "python")
        self.assertIn("no such file", e.read_file("nope.py").lower())
    def test_run_tests_pass(self):
        e = agent.MockEnv({"solution.py": "def add(a,b):\n    return a+b\n",
                           "test_solution.py": "from solution import *\nassert add(1,2)==3\n"},
                          "python")
        ok, out = e.run_tests()
        self.assertTrue(ok)
    def test_run_tests_fail(self):
        e = agent.MockEnv({"solution.py": "def add(a,b):\n    return a-b\n",
                           "test_solution.py": "from solution import *\nassert add(1,2)==3\n"},
                          "python")
        ok, out = e.run_tests()
        self.assertFalse(ok)

    # --- C4 (MILLORA §C4): the agent works on a project, not one file ----------------
    def test_tools_schema_offers_list_files(self):
        """The cheap first move of a real agent: see what is there before reading it. A task
        can then ask for a fix without naming the file."""
        names = [t["function"]["name"] for t in agent.TOOLS]
        self.assertIn("list_files", names)

    def test_list_files_lists_the_project_sorted(self):
        e = agent.MockEnv({"b.py": "", "a.py": "", "test_solution.py": ""}, "python")
        self.assertEqual(e.list_files(), "a.py\nb.py\ntest_solution.py")

    def test_list_files_on_an_empty_project(self):
        self.assertEqual(agent.MockEnv({}, "python").list_files(), "(no files)")

    def test_write_rejects_names_outside_the_flat_sandbox(self):
        """The sandbox is flat (the executor writes plain names): a path with a directory
        would either crash the runner or escape it. The model gets a clear error and the
        file is not created."""
        e = agent.MockEnv({"solution.py": "x=1\n"}, "python")
        for bad in ("src/util.py", "../outside.py", "a\\b.py", "", ".."):
            self.assertIn("error", e.write_file(bad, "x=2"))
        self.assertEqual(list(e.files), ["solution.py"])

    def test_the_test_file_is_read_only_and_ignored_when_grading(self):
        """The task's goal says "fix the code without touching the tests" (test_driven_fix
        states it): nothing enforced it, so a model could rewrite the test into `exit(0)`."""
        e = agent.MockEnv({"solution.py": "def add(a,b):\n    return a-b\n",
                           "test_solution.py": "from solution import *\nassert add(1,2)==3\n"},
                          "python")
        out = e.write_file("test_solution.py", "print('OK')")
        self.assertIn("read-only", out)
        self.assertIn("assert", e.read_file("test_solution.py"))   # untouched
        ok, _ = e.run_tests()
        self.assertFalse(ok)                                       # still graded on it

    def test_a_project_file_edit_reaches_the_executor(self):
        """The multi-file case C4 exists for: the bug is in a module the test never names,
        and the only way to pass is to edit that module. Before this, `run_tests` handed the
        executor the solution and the test only, so the edit was invisible."""
        e = agent.MockEnv(
            {"solution.py": "from utils import double\n\n\ndef compute(x):\n    return double(x)\n",
             "utils.py": "def double(x):\n    return x          # BUG: should be 2 * x\n",
             "test_solution.py": "from solution import compute\nassert compute(3) == 6\nprint('OK')\n"},
            "python")
        ok, out = e.run_tests()
        self.assertFalse(ok, out)
        e.write_file("utils.py", "def double(x):\n    return 2 * x\n")
        ok, out = e.run_tests()
        self.assertTrue(ok, out)

    @unittest.skipUnless(HAS_JAVAC, "javac not installed")
    def test_a_java_support_class_edit_reaches_the_compiler(self):
        """Java compiles every .java in the sandbox, so a support class travels too."""
        e = agent.MockEnv(
            {"Solution.java": "public class Solution { public static int go(int x){ return Helper.twice(x); } }\n",
             "Helper.java": "class Helper { static int twice(int x){ return x; } }\n",
             "Test.java": "public class Test { public static void main(String[] a){ if (Solution.go(3) != 6) throw new RuntimeException(\"fail\"); System.out.println(\"OK\"); } }\n"},
            "java", test_file="Test.java")
        ok, out = e.run_tests()
        self.assertFalse(ok, out)
        e.write_file("Helper.java", "class Helper { static int twice(int x){ return 2 * x; } }\n")
        ok, out = e.run_tests()
        self.assertTrue(ok, out)


@unittest.skipUnless(HAS_SANDBOX, "host cannot create isolated namespaces (unshare -Urn); code-execution coverage runs on sandboxed hosts")
class TestRunTestsFileLookup(unittest.TestCase):
    """The solution-file lookup is case-insensitive: java tasks use
    Solution.java/Test.java (javac requires file == public class) and an exact
    'solution.java' lookup left the solution empty: they never passed."""

    @unittest.skipUnless(HAS_JAVAC, "javac not installed")
    def test_java_capitalized_files(self):
        sol = 'public class Solution { public static int add(int a,int b){ return a+b; } }\n'
        tst = ('public class Test { public static void main(String[] a){\n'
               '  if (Solution.add(2,3) != 5) throw new RuntimeException("fail");\n'
               '  System.out.println("OK");\n}}\n')
        e = agent.MockEnv({"Solution.java": sol, "Test.java": tst},
                          "java", test_file="Test.java")
        ok, out = e.run_tests()
        self.assertTrue(ok, out)

    @unittest.skipUnless(HAS_JAVAC, "javac not installed")
    def test_java_broken_solution_still_fails(self):
        # the tolerance must not inflate the score: a broken solution fails
        sol = 'public class Solution { public static int add(int a,int b){ return a-b; } }\n'
        tst = ('public class Test { public static void main(String[] a){\n'
               '  if (Solution.add(2,3) != 5) throw new RuntimeException("fail");\n'
               '  System.out.println("OK");\n}}\n')
        e = agent.MockEnv({"Solution.java": sol, "Test.java": tst},
                          "java", test_file="Test.java")
        ok, out = e.run_tests()
        self.assertFalse(ok)

    def test_lowercase_convention_unchanged(self):
        e = agent.MockEnv({"solution.py": "x = 1\n",
                           "test_solution.py": "from solution import x\nassert x == 1\n"}, "python")
        ok, out = e.run_tests()
        self.assertTrue(ok, out)

@unittest.skipUnless(HAS_SANDBOX, "host cannot create isolated namespaces (unshare -Urn); code-execution coverage runs on sandboxed hosts")
class TestRunAgentScripted(unittest.TestCase):
    def test_scripted_success(self):
        # fake client: first calls write_file with the correct solution, then stops
        calls = {"n": 0}
        class FakeClient:
            def chat(self, messages, tools=None, tool_choice=None, max_tokens=256):
                calls["n"] += 1
                if calls["n"] == 1:
                    args_json = '{"path":"solution.py","content":"def add(a,b):\\n    return a+b\\n"}'
                    return {"choices":[{"finish_reason":"tool_calls","message":{
                        "tool_calls":[{"function":{"name":"write_file","arguments":args_json}}]}}]}
                return {"choices":[{"finish_reason":"stop","message":{"content":"done"}}]}
        task = {"lang":"python","goal":"fix add",
                "initial_files":{"solution.py":"def add(a,b):\n    return a-b\n",
                                 "test_solution.py":"from solution import *\nassert add(1,2)==3\n"},
                "test_file":"test_solution.py"}
        r = agent.run_agent(FakeClient(), task, max_turns=4)
        self.assertTrue(r["success"])
        self.assertEqual(r["tool_calls"], 1)

if __name__ == "__main__":
    unittest.main()