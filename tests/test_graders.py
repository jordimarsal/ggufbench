import unittest
import urllib.error
from benchmark import graders

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

class TestCodeGrader(unittest.TestCase):
    def test_extract_and_run(self):
        tasks = [{"id":"add","lang":"python","prompt":"implement add",
                  "test_code":"from solution import *\nassert add(1,2)==3\n"}]
        resp = {"choices":[{"message":{"content":"```python\ndef add(a,b):\n    return a+b\n```"}}]}
        r = graders.grade_code(FakeClient([resp]), tasks)
        self.assertEqual(r["score"], 1.0)
        self.assertEqual(r["by_lang"], {"python": 1.0})

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