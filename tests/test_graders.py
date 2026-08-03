import unittest
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

if __name__ == "__main__":
    unittest.main()