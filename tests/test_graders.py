import unittest
import urllib.error
import tempfile
import shutil
from pathlib import Path
from benchmark import graders, token_budget

class FakeClient:
    """Client que pot ser programat amb una seqüència de respostes per tasca."""
    def __init__(self, responses):
        self.responses = list(responses); self.i = 0
    def chat(self, *a, **k):
        r = self.responses[self.i % len(self.responses)]; self.i += 1
        return r

class TestToolsGrader(unittest.TestCase):
    def test_pass_and_fail(self):
        tasks = [
            {"id":"t1","prompt":"x","tools":[],"expected":{"name":"f","arguments":{"a":1}}},
            {"id":"t2","prompt":"y","tools":[],"expected":{"name":"g","arguments":{}}},
        ]
        resp_pass = {"choices":[{"finish_reason":"tool_calls","message":{"tool_calls":[
            {"function":{"name":"f","arguments":'{"a":1}'}}]}}]}
        resp_fail = {"choices":[{"finish_reason":"tool_calls","message":{"tool_calls":[
            {"function":{"name":"g","arguments":'{"b":2}'}}]}}], "timings":{}}
        r = graders.grade_tools(FakeClient([resp_pass, resp_fail]), tasks)
        self.assertEqual(r["score"], 0.5)
        self.assertEqual(r["by_lang"], {})  # tools no té by_lang
    def test_noop_case(self):
        tasks = [{"id":"noop","prompt":"hola","tools":[],"expected":None}]  # None = no ha de cridar
        resp = {"choices":[{"finish_reason":"stop","message":{"content":"hola!"}}]}
        r = graders.grade_tools(FakeClient([resp]), tasks)
        self.assertEqual(r["score"], 1.0)
    def test_expected_without_arguments_checks_name_only(self):
        # EXPECTED sense clau 'arguments': només es comprova el nom. Abans, la
        # absència exigia arguments ABSENTS i cap model ho passava (get_env demana
        # 'qualsevol variable' amb var_name required a l'schema: impossible).
        tasks = [{"id":"get_env","prompt":"x","tools":[],
                  "expected":{"name":"get_env"}}]
        resp = {"choices":[{"finish_reason":"tool_calls","message":{"tool_calls":[
            {"function":{"name":"get_env","arguments":'{"var_name":"PATH"}'}}]}}]}
        r = graders.grade_tools(FakeClient([resp]), tasks)
        self.assertEqual(r["score"], 1.0)
    def test_expected_empty_arguments_still_strict(self):
        # 'arguments': {} segueix exigint una crida sense arguments: una crida
        # amb arguments no és igual que una de buida.
        tasks = [{"id":"get_time","prompt":"x","tools":[],
                  "expected":{"name":"get_time","arguments":{}}}]
        resp = {"choices":[{"finish_reason":"tool_calls","message":{"tool_calls":[
            {"function":{"name":"get_time","arguments":'{"tz":"UTC"}'}}]}}]}
        r = graders.grade_tools(FakeClient([resp]), tasks)
        self.assertEqual(r["score"], 0.0)

class TestCodeGrader(unittest.TestCase):
    def test_extract_and_run(self):
        tasks = [{"id":"add","lang":"python","prompt":"implement add",
                  "test_code":"from solution import *\nassert add(1,2)==3\n"}]
        resp = {"choices":[{"message":{"content":"```python\ndef add(a,b):\n    return a+b\n```"}}]}
        r = graders.grade_code(FakeClient([resp]), tasks)
        self.assertEqual(r["score"], 1.0)
        self.assertEqual(r["by_lang"], {"python": 1.0})


class TestCodeEscalation(unittest.TestCase):
    """Quan una tasca no extreu bloc de codi (model truncat), el grader escala el
    pressupost de tokens i persisteix el valor calibrat a token_budget."""
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.old_file = token_budget.BUDGET_FILE
        token_budget.BUDGET_FILE = self.tmpdir / "tb.json"
        token_budget.reset_cache()

    def tearDown(self):
        token_budget.BUDGET_FILE = self.old_file
        token_budget.reset_cache()
        shutil.rmtree(self.tmpdir)

    def _client(self, threshold):
        """Retorna prosa (sense fence) si max_tokens < threshold, sinó un bloc vàlid."""
        code = "```python\ndef f():\n    return 1\n```"
        prose = "hmmm deixa'm pensar... "
        class C:
            def __init__(self): self.calls = 0
            def chat(self, *a, **k):
                self.calls += 1
                mt = k.get("max_tokens", 0)
                return {"choices": [{"message": {"content": code if mt >= threshold else prose * 50}}]}
        return C()

    def test_escalation_saves_budget(self):
        c = self._client(threshold=4096)
        tasks = [{"id": "t1", "lang": "python", "prompt": "p",
                  "test_code": "from solution import *\nassert f()==1\n"}]
        graders.grade_code(c, tasks, model_slug="skyrl")
        self.assertEqual(token_budget.get("code", "skyrl", "python", "t1"), 4096)
        self.assertGreater(c.calls, 1)  # ha escalat

    def test_stored_budget_skips_escalation(self):
        token_budget.put("code", "skyrl", "python", "t1", 4096)
        token_budget.reset_cache()
        c = self._client(threshold=4096)
        tasks = [{"id": "t1", "lang": "python", "prompt": "p",
                  "test_code": "from solution import *\nassert f()==1\n"}]
        graders.grade_code(c, tasks, model_slug="skyrl")
        self.assertEqual(c.calls, 1)  # pressupost guardat -> una sola crida

    def test_no_save_when_default_suffices(self):
        c = self._client(threshold=1024)  # el bloc apareix fins i tot a 2048
        tasks = [{"id": "t2", "lang": "python", "prompt": "p",
                  "test_code": "from solution import *\nassert f()==1\n"}]
        graders.grade_code(c, tasks, model_slug="m")
        self.assertIsNone(token_budget.get("code", "m", "python", "t2"))  # no cal anotar res

    def test_system_prompt_asks_for_export_on_typescript(self):
        captured = {}
        class Cap:
            def chat(self, messages, **k):
                captured["messages"] = messages
                return {"choices": [{"message": {"content":
                        "```typescript\nexport function add(a,b){return a+b}\n```"}}]}
        graders.grade_code(Cap(), [{"id": "t", "lang": "typescript", "prompt": "p",
                                    "test_code": "import{add}from'./solution'"}], model_slug="x")
        sysmsg = [m for m in captured["messages"] if m["role"] == "system"][0]["content"]
        self.assertIn("export", sysmsg.lower())
        self.assertIn("```typescript", sysmsg)

    def test_truncation_excluded_from_score(self):
        # python: produeix codi (passa); bash: només prosa -> truncament, exclòs.
        class C:
            def chat(self, messages, **k):
                if "```python" in messages[0]["content"]:
                    return {"choices": [{"message": {"content":
                            "```python\ndef f():\n    return 1\n```"}}]}
                return {"choices": [{"message": {"content": "hmmm, no escric codi, només prosa"}}]}
        tasks = [
            {"id": "good", "lang": "python", "prompt": "p",
             "test_code": "from solution import *\nassert f()==1\n"},
            {"id": "bad", "lang": "bash", "prompt": "p", "test_code": "echo x"},
        ]
        r = graders.grade_code(C(), tasks, model_slug="x")
        self.assertEqual(r["excluded"], 1)              # la bash truncada
        self.assertEqual(r["score"], 1.0)               # només compta la python (pass)
        self.assertTrue(r["trace"][1]["excluded"])
        self.assertFalse(r["trace"][0]["excluded"])

    def test_real_failure_is_counted(self):
        # Codi vàlid però que falla els tests: ha de comptar com a fallida (no exclosa).
        class C:
            def chat(self, messages, **k):
                return {"choices": [{"message": {"content":
                        "```python\ndef f():\n    return 0\n```"}}]}
        r = graders.grade_code(C(), [{"id": "wrong", "lang": "python", "prompt": "p",
                                      "test_code": "from solution import *\nassert f()==1\n"}],
                                model_slug="y")
        self.assertEqual(r["excluded"], 0)
        self.assertEqual(r["score"], 0.0)

class TestSpeedGrader(unittest.TestCase):
    def test_median(self):
        def make(ms): return {"timings":{"predicted_ms": ms}}
        r = graders.grade_speed(FakeClient([make(100), make(50), make(33)]), tasks=[{"id":"s1","prompt":"hi"}])
        self.assertAlmostEqual(r["speed_ms"], 61.0, places=0)  # mitjana de [100,50,33] ~ 61 ms
    def test_captures_tokens_per_second(self):
        def make(gen, prom): return {"timings": {"predicted_per_second": gen,
                                                 "prompt_per_second": prom,
                                                 "predicted_ms": 100}}
        r = graders.grade_speed(FakeClient([make(50.0, 1000.0)]),
                                tasks=[{"id": "s", "prompt": "hi"}])
        self.assertAlmostEqual(r["gen_tps"], 50.0)
        self.assertAlmostEqual(r["prompt_tps"], 1000.0)


class TestTransientErrors(unittest.TestCase):
    """Un 500/timeout del servidor només ha de fallar la tasca afectada, no avortar la run."""
    def _flaky(self, fail_on):
        class FlakyClient:
            def __init__(self): self.n = 0
            def chat(self, *a, **k):
                self.n += 1
                if self.n == fail_on:
                    raise urllib.error.HTTPError("http://x", 500, "Internal Server Error", {}, None)
                return {"choices": [{"message": {"content": "```python\nx=1\n```"}}]}
        return FlakyClient()
    def test_code_500_isolated(self):
        tasks = [{"id": f"t{i}", "lang": "python", "prompt": "p", "test_code": "pass"} for i in range(3)]
        r = graders.grade_code(self._flaky(2), tasks)
        self.assertEqual(len(r["trace"]), 3)            # cap tasca abortada
        self.assertFalse(r["trace"][1]["passed"])       # la que va 500 → fallada
        self.assertIn("server error", r["trace"][1]["detail"].lower())
        self.assertTrue(r["trace"][0]["passed"])        # les altres segueixen corrent
    def test_tools_500_isolated(self):
        tasks = [{"id": "a", "prompt": "p", "tools": [], "expected": None},
                 {"id": "b", "prompt": "p", "tools": [], "expected": None}]
        r = graders.grade_tools(self._flaky(1), tasks)
        self.assertEqual(len(r["trace"]), 2)
        self.assertFalse(r["trace"][0]["passed"])
    def test_agent_500_isolated(self):
        # run_agent fa múltiples chat(); un 500 a mig torn ha de fallar només aquesta tasca.
        tasks = [{"id": "a", "lang": "python", "goal": "g", "max_turns": 4,
                  "initial_files": {"solution.py": ""}, "test_file": "test_solution.py"},
                 {"id": "b", "lang": "python", "goal": "g", "max_turns": 4,
                  "initial_files": {"solution.py": ""}, "test_file": "test_solution.py"}]
        r = graders.grade_agent(self._flaky(1), tasks)
        self.assertEqual(len(r["trace"]), 2)
        self.assertFalse(r["trace"][0]["passed"])

if __name__ == "__main__":
    unittest.main()