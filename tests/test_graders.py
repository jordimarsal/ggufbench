import unittest
import urllib.error
import tempfile
import shutil
from pathlib import Path
from ggufbench import config, executors, graders, token_budget

HAS_SANDBOX = executors._probe_sandbox()

class FakeClient:
    """Client that can be scripted with a sequence of responses per task."""
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
        self.assertEqual(r["by_lang"], {})  # tools has no by_lang
    def test_noop_case(self):
        tasks = [{"id":"noop","prompt":"hi","tools":[],"expected":None}]  # None = must not call
        resp = {"choices":[{"finish_reason":"stop","message":{"content":"hi!"}}]}
        r = graders.grade_tools(FakeClient([resp]), tasks)
        self.assertEqual(r["score"], 1.0)
    def test_expected_without_arguments_checks_name_only(self):
        # EXPECTED without an 'arguments' key: only the name is checked. Before, the
        # absence required ABSENT arguments and no model ever passed (get_env asks for
        # 'any variable' with var_name required in the schema: impossible).
        tasks = [{"id":"get_env","prompt":"x","tools":[],
                  "expected":{"name":"get_env"}}]
        resp = {"choices":[{"finish_reason":"tool_calls","message":{"tool_calls":[
            {"function":{"name":"get_env","arguments":'{"var_name":"PATH"}'}}]}}]}
        r = graders.grade_tools(FakeClient([resp]), tasks)
        self.assertEqual(r["score"], 1.0)
    def test_expected_empty_arguments_still_strict(self):
        # 'arguments': {} still requires a call without arguments: a call
        # with arguments is not equal to an empty one.
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

    def test_by_level_folded_score_and_breakdown(self):
        # R3/R4 hard_code_tier: easy+hard folded into the same score (same weight per
        # task); by_level breaks down per level over the scoreable tasks.
        tasks = [
            {"id":"easy_a","lang":"python","prompt":"p","level":"easy",
             "test_code":"from solution import *\nassert add(1,2)==3\n"},
            {"id":"hard_a","lang":"python","prompt":"p","level":"hard",
             "test_code":"from solution import *\nassert add(1,2)==3\n"},
        ]
        resp_ok = {"choices":[{"message":{"content":"```python\ndef add(a,b):\n    return a+b\n```"}}]}
        resp_bad = {"choices":[{"message":{"content":"```python\ndef add(a,b):\n    return a-b\n```"}}]}
        r = graders.grade_code(FakeClient([resp_ok, resp_bad]), tasks)
        self.assertEqual(r["score"], 0.5)
        self.assertEqual(r["by_level"], {"easy": 1.0, "hard": 0.0})
        self.assertEqual([t["level"] for t in r["trace"]], ["easy", "hard"])

    def test_by_level_defaults_to_easy_without_key(self):
        # tasks without a level key (old files): easy (R1)
        tasks = [{"id":"old","lang":"python","prompt":"p",
                  "test_code":"from solution import *\nassert add(1,2)==3\n"}]
        resp = {"choices":[{"message":{"content":"```python\ndef add(a,b):\n    return a+b\n```"}}]}
        r = graders.grade_code(FakeClient([resp]), tasks)
        self.assertEqual(r["by_level"], {"easy": 1.0})

class TestCodeTimeout(unittest.TestCase):
    """R1/R2/R3 of timeout_scaling: budget in tokens, scaled anti-hang clock."""

    def test_formula_floors_ceils_and_falls_back(self):
        self.assertEqual(graders.code_timeout(2048, None), 90)      # without gen_tps
        self.assertEqual(graders.code_timeout(2048, 1000), 90)      # 90 s floor
        self.assertEqual(graders.code_timeout(2048, 41), 122)       # 60 + 62.4
        self.assertEqual(graders.code_timeout(8192, 10), 1000)      # 1000 s ceiling

    def test_scaled_timeout_applied_to_the_single_attempt(self):
        # R2: the single code attempt gets the scaled timeout (32768 at 41 t/s -> 1000 s ceiling)
        tasks = [{"id":"x","lang":"python","prompt":"p","test_code":"t","level":"hard"}]
        cap_timeouts = []

        class Prose:
            def chat(self, *a, **k):
                cap_timeouts.append(k.get("timeout"))
                return {"choices":[{"message":{"content":"prose with no code block"}}]}

        r = graders.grade_code(Prose(), tasks, gen_tps=41)
        self.assertEqual(cap_timeouts, [1000])
        self.assertEqual(r["trace"][0]["excluded"], True)

    def test_transient_timeout_still_excludes(self):
        # R3: a transport timeout is still an exclusion (never a fail); with a transient
        # error the scale does not retry (more tokens don't fix the transport).
        tasks = [{"id":"x","lang":"python","prompt":"p","test_code":"t","level":"hard"}]

        class Boom:
            def chat(self, *a, **k):
                raise urllib.error.URLError("simulated timeout")

        r = graders.grade_code(Boom(), tasks, gen_tps=41)
        self.assertEqual(r["trace"][0]["excluded"], True)
        self.assertTrue(r["trace"][0]["detail"].startswith("server error"))


@unittest.skipUnless(HAS_SANDBOX, "host cannot create isolated namespaces (unshare -Urn); code-execution coverage runs on sandboxed hosts")
class TestCodeBudget(unittest.TestCase):
    """ADR-0002 + R3 thinking_batches: a single generous budget (32768). With fixed
    seed/temp, max_tokens is a ceiling, not a target: one attempt at the ceiling produces the
    same generation as the old scale, with no wasted requests on thinking
    models. Output tokens are recorded in the trace (efficiency)."""
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.enterContext(config.override(TOKEN_BUDGETS=self.tmpdir / "tb.json"))
        token_budget.reset_cache()

    def tearDown(self):
        token_budget.reset_cache()
        shutil.rmtree(self.tmpdir)

    def _client(self, threshold):
        """Returns prose (no fence) if max_tokens < threshold, otherwise a valid block."""
        code = "```python\ndef f():\n    return 1\n```"
        prose = "hmmm let me think... "
        class C:
            def __init__(self): self.calls = 0
            def chat(self, *a, **k):
                self.calls += 1
                mt = k.get("max_tokens", 0)
                return {"choices": [{"message": {"content": code if mt >= threshold else prose * 50}}]}
        return C()

    def test_single_generous_budget_resolves_long_output(self):
        # before it took 2 requests (scale 2048->4096); now a single one at the ceiling
        c = self._client(threshold=4096)
        tasks = [{"id": "t1", "lang": "python", "prompt": "p",
                  "test_code": "from solution import *\nassert f()==1\n"}]
        graders.grade_code(c, tasks, model_slug="skyrl")
        self.assertEqual(c.calls, 1)
        self.assertIsNone(token_budget.get("code", "skyrl", None, "python", "t1"))  # the default already suffices

    def test_stored_budget_still_honoured(self):
        token_budget.put("code", "skyrl", None, "python", "t1", 4096)
        token_budget.reset_cache()
        c = self._client(threshold=4096)
        tasks = [{"id": "t1", "lang": "python", "prompt": "p",
                  "test_code": "from solution import *\nassert f()==1\n"}]
        graders.grade_code(c, tasks, model_slug="skyrl")
        self.assertEqual(c.calls, 1)

    def test_output_tokens_recorded_in_trace(self):
        tasks = [{"id": "t3", "lang": "python", "prompt": "p",
                  "test_code": "from solution import *\nassert f()==1\n"}]
        resp = {"choices": [{"message": {"content": "```python\ndef f():\n    return 1\n```"}}],
                "usage": {"completion_tokens": 321}}
        r = graders.grade_code(FakeClient([resp]), tasks)
        self.assertEqual(r["trace"][0]["out_tokens"], 321)

    def test_no_save_when_default_suffices(self):
        c = self._client(threshold=1024)  # the block appears even without extra budget
        tasks = [{"id": "t2", "lang": "python", "prompt": "p",
                  "test_code": "from solution import *\nassert f()==1\n"}]
        graders.grade_code(c, tasks, model_slug="m")
        self.assertIsNone(token_budget.get("code", "m", None, "python", "t2"))  # nothing to record

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
        # python: produces code (passes); bash: prose only -> truncation, excluded.
        class C:
            def chat(self, messages, **k):
                if "```python" in messages[0]["content"]:
                    return {"choices": [{"message": {"content":
                            "```python\ndef f():\n    return 1\n```"}}]}
                return {"choices": [{"message": {"content": "hmm, I won't write code, only prose"}}]}
        tasks = [
            {"id": "good", "lang": "python", "prompt": "p",
             "test_code": "from solution import *\nassert f()==1\n"},
            {"id": "bad", "lang": "bash", "prompt": "p", "test_code": "echo x"},
        ]
        r = graders.grade_code(C(), tasks, model_slug="x")
        self.assertEqual(r["excluded"], 1)              # the truncated bash one
        self.assertEqual(r["score"], 1.0)               # only the python one counts (pass)
        self.assertTrue(r["trace"][1]["excluded"])
        self.assertFalse(r["trace"][0]["excluded"])

    def test_real_failure_is_counted(self):
        # Valid code that fails the tests: must count as a failure (not excluded).
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
        self.assertAlmostEqual(r["speed_ms"], 61.0, places=0)  # mean of [100,50,33] ~ 61 ms
    def test_captures_tokens_per_second(self):
        def make(gen, prom): return {"timings": {"predicted_per_second": gen,
                                                 "prompt_per_second": prom,
                                                 "predicted_ms": 100}}
        r = graders.grade_speed(FakeClient([make(50.0, 1000.0)]),
                                tasks=[{"id": "s", "prompt": "hi"}])
        self.assertAlmostEqual(r["gen_tps"], 50.0)
        self.assertAlmostEqual(r["prompt_tps"], 1000.0)


class TestTransientErrors(unittest.TestCase):
    """A 500/timeout from the server must only fail the affected task, not abort the run."""
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
        self.assertEqual(len(r["trace"]), 3)            # no task aborted
        self.assertFalse(r["trace"][1]["passed"])       # the one that 500'd → failure
        self.assertIn("server error", r["trace"][1]["detail"].lower())
        self.assertTrue(r["trace"][0]["passed"])        # the others keep running
    def test_tools_500_isolated(self):
        tasks = [{"id": "a", "prompt": "p", "tools": [], "expected": None},
                 {"id": "b", "prompt": "p", "tools": [], "expected": None}]
        r = graders.grade_tools(self._flaky(1), tasks)
        self.assertEqual(len(r["trace"]), 2)
        self.assertFalse(r["trace"][0]["passed"])
    def test_agent_500_isolated(self):
        # run_agent makes multiple chat() calls; a 500 mid-turn must fail only that task.
        tasks = [{"id": "a", "lang": "python", "goal": "g", "max_turns": 4,
                  "initial_files": {"solution.py": ""}, "test_file": "test_solution.py"},
                 {"id": "b", "lang": "python", "goal": "g", "max_turns": 4,
                  "initial_files": {"solution.py": ""}, "test_file": "test_solution.py"}]
        r = graders.grade_agent(self._flaky(1), tasks)
        self.assertEqual(len(r["trace"]), 2)
        self.assertFalse(r["trace"][0]["passed"])

if __name__ == "__main__":
    unittest.main()