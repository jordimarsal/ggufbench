import unittest
from benchmark import agent

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


class TestRunTestsFileLookup(unittest.TestCase):
    """La cerca del fitxer de solució no distingeix majúscules: les tasques de
    java usen Solution.java/Test.java (javac exigeix file == classe pública) i
    cercar-hi 'solution.java' exacte deixava la solució buida: mai passaven."""

    def test_java_capitalized_files(self):
        sol = 'public class Solution { public static int add(int a,int b){ return a+b; } }\n'
        tst = ('public class Test { public static void main(String[] a){\n'
               '  if (Solution.add(2,3) != 5) throw new RuntimeException("fail");\n'
               '  System.out.println("OK");\n}}\n')
        e = agent.MockEnv({"Solution.java": sol, "Test.java": tst},
                          "java", test_file="Test.java")
        ok, out = e.run_tests()
        self.assertTrue(ok, out)

    def test_java_broken_solution_still_fails(self):
        # la tolerància no ha d'inflar el score: una solució trencada falla
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

class TestRunAgentScripted(unittest.TestCase):
    def test_scripted_success(self):
        # client fake: primer crida write_file amb la solució correcta, després atura
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