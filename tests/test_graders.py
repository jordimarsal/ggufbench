import contextlib
import json
import io
import unittest
import urllib.error
import tempfile
import shutil
from pathlib import Path
from unittest import mock

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

@unittest.skipUnless(HAS_SANDBOX, "host cannot create isolated namespaces (unshare -Urn); code-execution coverage runs on sandboxed hosts")
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


@unittest.skipUnless(HAS_SANDBOX, "host cannot create isolated namespaces (unshare -Urn); code-execution coverage runs on sandboxed hosts")
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


@unittest.skipUnless(HAS_SANDBOX, "host cannot create isolated namespaces (unshare -Urn); code-execution coverage runs on sandboxed hosts")
class TestGradersMultiRun(unittest.TestCase):
    """C1 stage 2 core: --runs N aggregation semantics."""

    def test_tools_3_of_3_passes(self):
        tasks = [{"id": "t", "prompt": "p", "tools": [], "expected": {"name": "f"}}]
        resp = {"choices": [{"finish_reason": "tool_calls", "message": {
            "tool_calls": [{"function": {"name": "f", "arguments": "{}"}}]}}]}
        r = graders.grade_tools(FakeClient([resp]), tasks, runs=3)
        self.assertEqual(r["score"], 1.0)
        self.assertEqual(r["trace"][0]["runs"], [1, 1, 1])
        self.assertEqual(r["runs"], 3)
        # N==1 omits "runs" key; N>1 includes it
        self.assertIn("runs", r)

    def test_tools_2_of_3_fails(self):
        tasks = [{"id": "t", "prompt": "p", "tools": [], "expected": {"name": "f"}}]
        resp_ok = {"choices": [{"finish_reason": "tool_calls", "message": {
            "tool_calls": [{"function": {"name": "f", "arguments": "{}"}}]}}]}
        resp_fail = {"choices": [{"finish_reason": "tool_calls", "message": {
            "tool_calls": [{"function": {"name": "g", "arguments": "{}"}}]}}], "timings": {}}
        r = graders.grade_tools(FakeClient([resp_ok, resp_fail]), tasks, runs=3)
        self.assertAlmostEqual(r["score"], 0.667, places=2)
        self.assertFalse(r["passed"])
        self.assertEqual(r["trace"][0]["runs"], [1, 0, 1])

    def test_tools_excluded_run_not_counted_as_attempt(self):
        """A server error run is marked 'x' and excluded from attempt counts."""
        tasks = [{"id": "t", "prompt": "p", "tools": [], "expected": {"name": "f"}}]
        resp_ok = {"choices": [{"finish_reason": "tool_calls", "message": {
            "tool_calls": [{"function": {"name": "f", "arguments": "{}"}}]}}]}

        class Flaky:
            def __init__(self): self.n = 0
            def chat(self, *a, **k):
                self.n += 1
                if self.n == 2:
                    raise urllib.error.HTTPError("http://x", 500, "error", {}, None)
                return resp_ok
        r = graders.grade_tools(Flaky(), tasks, runs=3)
        # pass, excluded, pass -> score = 2/2 = 1.0 (excluded doesn't count as attempt)
        self.assertEqual(r["score"], 1.0)
        self.assertTrue(r["passed"])
        self.assertEqual(r["trace"][0]["runs"], [1, "x", 1])

    def test_tools_all_runs_excluded(self):
        """When all runs are server errors for a task, it is fully excluded from the mean."""
        tasks = [{"id": "t", "prompt": "p", "tools": [], "expected": {"name": "f"}}]

        class AlwaysFail:
            def chat(self, *a, **k):
                raise urllib.error.HTTPError("http://x", 500, "error", {}, None)
        r = graders.grade_tools(AlwaysFail(), tasks, runs=3)
        self.assertEqual(r["score"], 0.0)
        self.assertFalse(r["passed"])
        self.assertIn("excluded", r)
        self.assertEqual(r["excluded"], 1)

    def test_code_3_of_3_passes(self):
        tasks = [{"id": "c", "lang": "python", "prompt": "p",
                  "test_code": "from solution import *\nassert f()==1\n"}]
        resp = {"choices": [{"message": {
            "content": "```python\ndef f():\n    return 1\n```"}}]}
        r = graders.grade_code(FakeClient([resp]), tasks, runs=3)
        self.assertEqual(r["score"], 1.0)
        self.assertEqual(r["trace"][0]["runs"], [1, 1, 1])
        self.assertEqual(r["runs"], 3)

    def test_tools_seeds_per_run(self):
        """C1 stage 3: each run uses a different seed (SEED + run_index)."""
        from ggufbench.run import ClientWrapper
        captured = []
        class SeedCap(ClientWrapper):
            def __init__(self, base_url, extra=None):
                super().__init__(base_url, extra)
            def chat(self, *a, **k):
                # Capture the seed that will be injected by super().chat()
                seed_val = config.SEED + self.run_index if self.run_index is not None else None
                captured.append(seed_val)
                return super().chat(*a, **k)
        tasks = [{"id": "t", "prompt": "p", "tools": [], "expected": None}]
        resp = {"choices": [{"finish_reason": "stop", "message": {"content": "ok"}}]}
        c = SeedCap("http://x", extra=None)
        graders.grade_tools(c, tasks, runs=3)
        self.assertEqual(captured, [42, 43, 44])

    def test_code_seeds_per_run(self):
        """Same seed progression for code dimension."""
        from ggufbench.run import ClientWrapper
        captured = []
        class SeedCap(ClientWrapper):
            def __init__(self, base_url, extra=None):
                super().__init__(base_url, extra)
            def chat(self, *a, **k):
                seed_val = config.SEED + self.run_index if self.run_index is not None else None
                captured.append(seed_val)
                return super().chat(*a, **k)
        tasks = [{"id": "c", "lang": "python", "prompt": "p",
                  "test_code": "from solution import *\nassert f()==1\n"}]
        resp = {"choices": [{"message": {
            "content": "```python\ndef f():\n    return 1\n```"}}]}
        c = SeedCap("http://x", extra=None)
        graders.grade_code(c, tasks, runs=3)
        self.assertEqual(captured, [42, 43, 44])

    def test_agent_seeds_per_run(self):
        """Same seed progression for agent dimension."""
        from ggufbench.run import ClientWrapper
        captured = []
        class SeedCap(ClientWrapper):
            def __init__(self, base_url, extra=None):
                super().__init__(base_url, extra)
            def chat(self, *a, **k):
                seed_val = config.SEED + self.run_index if self.run_index is not None else None
                captured.append(seed_val)
                return super().chat(*a, **k)
        tasks = [{"id": "a", "lang": "python", "goal": "g", "max_turns": 2,
                  "initial_files": {"solution.py": ""}, "test_file": "test_solution.py"}]
        # run_agent breaks after turn 1 (no tool_calls in response), so 1 chat/run × 3 runs.
        c = SeedCap("http://x", extra=None)
        graders.grade_agent(c, tasks, runs=3)
        self.assertEqual(len(captured), 3)
        self.assertEqual(captured, [42, 43, 44])

    def test_n1_no_seed_injected(self):
        """N==1 compat: seed key must NOT appear when runs==1."""
        from ggufbench.run import ClientWrapper
        captured = []
        class NoSeed(ClientWrapper):
            def __init__(self, base_url, extra=None):
                super().__init__(base_url, extra)
            def chat(self, *a, **k):
                seed_val = config.SEED + self.run_index if self.run_index is not None else None
                captured.append(seed_val)
                return super().chat(*a, **k)
        tasks = [{"id": "t", "prompt": "p", "tools": [], "expected": None}]
        resp = {"choices": [{"finish_reason": "stop", "message": {"content": "ok"}}]}
        c = NoSeed("http://x", extra=None)
        graders.grade_tools(c, tasks, runs=1)
        # run_index stays None → no seed injected
        self.assertIsNone(captured[-1])


@unittest.skipUnless(HAS_SANDBOX, "host cannot create isolated namespaces (unshare -Urn); code-execution coverage runs on sandboxed hosts")
class TestAgentConversations(unittest.TestCase):
    """grade_agent keeps per-task per-run episode histories so the next HTTP 500
    (or any failure) can be debugged from the receipt, not re-run."""

    def test_histories_collected_per_task_per_run(self):
        class C:
            def chat(self, *a, **k):
                return {"choices": [{"message": {"content": "hi"}}]}
        tasks = [{"id": "a", "lang": "python", "goal": "g", "max_turns": 2,
                  "initial_files": {"solution.py": "", "test_solution.py": "print('OK')"},
                  "test_file": "test_solution.py"}]
        r = graders.grade_agent(C(), tasks, runs=2)
        convos = r["conversations"]
        self.assertEqual(set(convos), {"a"})
        self.assertEqual(len(convos["a"]), 2)
        roles = [m.get("role") for m in convos["a"][0]]
        self.assertEqual(roles[:2], ["system", "user"])
        # the model's reply is recorded verbatim (real servers add "role";
        # minimal fixtures may omit it — receipts stay faithful either way)
        self.assertTrue(any(m.get("content") == "hi" for m in convos["a"][0]))

    def test_truncation_marks_long_content(self):
        out = graders._trunc_history([{"role": "user", "content": "x" * 5000}])
        self.assertTrue(out[0]["content"].endswith("chars]"))
        self.assertLess(len(out[0]["content"]), 5000)
        short = graders._trunc_history([{"role": "a", "content": "short"}])
        self.assertEqual(short[0]["content"], "short")


if __name__ == "__main__":
    unittest.main()

@unittest.skipUnless(HAS_SANDBOX, "host cannot create isolated namespaces (unshare -Urn)")
class TestSharedIdsAcrossLanguages(unittest.TestCase):
    """Regression (found 2026-10-14, fixed before the v5 re-measure): the per-run aggregation
    looked the entry up by `id`, but ids are unique per DIMENSION, not per language —
    `bubble_sort` exists in the four languages, and so do the shared agent ids (debug,
    fix_bug, refactor...). Every shared id therefore took the outcome of the first language
    in loader order (bash), so a python task could be recorded as failed on a bash task's
    failure, its receipt could say `bash`, and `by_lang`/`by_level` lost those tasks.

    The fix indexes the per-run results (one entry per task, in task order) instead."""
    PY_SOL = "def f():\n    return 1\n"

    class _LangClient:
        """Passes python, fails bash: the two tasks must not be able to swap outcomes."""
        run_index = None
        def chat(self, msgs, **k):
            lang = "python" if "python" in msgs[0]["content"] else "bash"
            body = TestSharedIdsAcrossLanguages.PY_SOL if lang == "python" else "nope()\n"
            return {"choices": [{"message": {"content": f"```{lang}\n{body}```"}}],
                    "usage": {"completion_tokens": 3}}

    def _code_tasks(self):
        return [
            {"id": "same_id", "lang": "bash", "level": "easy", "prompt": "bash one",
             "test_code": "echo 'should not run' >&2\nexit 1\n"},
            {"id": "same_id", "lang": "python", "level": "easy", "prompt": "python one",
             "test_code": "from solution import *\nassert f() == 1\nprint('OK')\n"},
        ]

    def test_code_shared_id_keeps_both_outcomes(self):
        r = graders.grade_code(self._LangClient(), self._code_tasks())
        self.assertEqual(r["score"], 0.5)                      # was 0.0 before the fix
        self.assertEqual(r["by_lang"], {"bash": 0.0, "python": 1.0})
        self.assertEqual([t["lang"] for t in r["trace"]], ["bash", "python"])  # was bash, bash
        self.assertEqual([t["runs"] for t in r["trace"]], [[0], [1]])

    def test_code_shared_id_with_runs_3(self):
        r = graders.grade_code(self._LangClient(), self._code_tasks(), runs=3)
        self.assertEqual(r["score"], 0.5)
        self.assertEqual([t["runs"] for t in r["trace"]], [[0, 0, 0], [1, 1, 1]])

    def test_agent_shared_id_keeps_both_outcomes(self):
        """The agent dimension shares ids too (debug, refactor, add_feature...)."""
        tasks = [
            {"id": "same_id", "lang": "bash", "goal": "bash goal", "max_turns": 1,
             "test_file": "test_solution.sh",
             "initial_files": {"solution.sh": "exit 1\n", "test_solution.sh": "exit 1\n"}},
            {"id": "same_id", "lang": "python", "goal": "python goal", "max_turns": 1,
             "test_file": "test_solution.py",
             "initial_files": {"solution.py": "def f():\n    return 1\n",
                               "test_solution.py": "from solution import *\nassert f() == 1\nprint('OK')\n"}},
        ]
        r = graders.grade_agent(self._LangClient(), tasks)
        self.assertEqual(r["score"], 0.5)
        self.assertEqual(r["by_lang"], {"bash": 0.0, "python": 1.0})
        self.assertEqual([t["lang"] for t in r["trace"]], ["bash", "python"])

    def test_tools_shared_id_keeps_both_outcomes(self):
        """Tools ids are unique today, but the lookup was the same: keep it honest."""
        tasks = [
            {"id": "same_id", "prompt": "bash one", "tools": [], "expected": {"name": "a"}},
            {"id": "same_id", "prompt": "python one", "tools": [], "expected": {"name": "b"}},
        ]
        resp_a = {"choices": [{"finish_reason": "tool_calls", "message": {"tool_calls": [
            {"function": {"name": "a", "arguments": "{}"}}]}}]}
        resp_b = {"choices": [{"finish_reason": "tool_calls", "message": {"tool_calls": [
            {"function": {"name": "b", "arguments": "{}"}}]}}]}
        r = graders.grade_tools(FakeClient([resp_a, resp_b]), tasks)
        self.assertEqual(r["score"], 1.0)
        self.assertEqual(len(r["trace"]), 2)

    def test_the_real_dataset_has_shared_ids_and_no_duplicates(self):
        """Why this matters here: the shipped code tasks DO share ids across languages."""
        from ggufbench import tasks_loader
        code = tasks_loader.load("code")
        ids = {}
        for t in code:
            ids.setdefault(t["id"], set()).add(t["lang"])
        shared = {i: langs for i, langs in ids.items() if len(langs) > 1}
        self.assertIn("bubble_sort", shared)
        self.assertEqual(shared["bubble_sort"], {"bash", "java", "python", "typescript"})
        self.assertEqual(len(code), len({(t["lang"], t["id"]) for t in code}))

class TestCodeBudgetTravels(unittest.TestCase):
    """MILLORA §C12: the code token cap is a condition (`graders.CODE_MAX_TOKENS`, single
    attempt since ADR-0002) and the row must say which cap its tasks ran under, including the
    case where the `token_budgets` artifact gave a task a different one."""

    def setUp(self):
        # token_budget caches the artifact in module state: without resetting it, one test's
        # temp file leaks into the next (the D1 family of test pollution).
        token_budget.reset_cache()
        self.addCleanup(token_budget.reset_cache)

    def _task(self):
        return [{"id": "t1", "lang": "python", "level": "easy", "prompt": "p",
                 "test_code": "from solution import *\nassert f() == 1\nprint('OK')\n"}]

    class _Client:
        run_index = None
        def __init__(self):
            self.budgets = []
        def chat(self, msgs, max_tokens=None, **k):
            self.budgets.append(max_tokens)
            return {"choices": [{"message": {"content": "```python\ndef f():\n    return 1\n```"}}],
                    "usage": {"completion_tokens": 3}}

    def test_default_run_reports_the_ladder_cap(self):
        r = graders.grade_code(self._Client(), self._task(), model_slug="m", thinking="off")
        self.assertEqual(r["code_budget"], graders.CODE_MAX_TOKENS)
        self.assertEqual(r["code_budget_stored"], {})

    def test_a_stored_calibration_is_recorded_and_used(self):
        """A schema-2 calibration is the one case where the cap is not the ladder value: the
        row must name it (before §C12 it was invisible) and the call must carry it."""
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "tb.json"
            path.write_text(json.dumps({"code/m/off/python/t1": 4096, "_schema": 2}))
            with config.override(TOKEN_BUDGETS=path):
                token_budget.reset_cache()
                client = self._Client()
                r = graders.grade_code(client, self._task(), model_slug="m", thinking="off")
        self.assertEqual(r["code_budget"], graders.CODE_MAX_TOKENS)
        self.assertEqual(r["code_budget_stored"], {4096: 1})
        self.assertEqual(client.budgets, [4096])


class TestLegacyBudgetsAreInert(unittest.TestCase):
    """The scare of 2026-10-14: `results/token_budgets.json` carries 37 pre-schema entries
    (4096/8192) naming fleet models. They are ignored on purpose (`_load()` returns {} without
    `_schema: 2`), so they are NOT hidden smaller caps — pinned here so nobody re-introduces
    the gate by accident."""

    def setUp(self):
        token_budget.reset_cache()
        self.addCleanup(token_budget.reset_cache)

    def test_pre_schema_file_is_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "tb.json"
            path.write_text(json.dumps({"code/m/off/python/t1": 4096}))   # no _schema
            with config.override(TOKEN_BUDGETS=path):
                token_budget.reset_cache()
                self.assertIsNone(token_budget.get("code", "m", "off", "python", "t1"))


class TestCapProbes(unittest.TestCase):
    """§C13: the harness probes its own ceilings during a run (a task at the token cap, a
    tool call cut by it, an agent turn that answered nothing) and records what it saw, instead
    of leaving the diagnosis to a post-mortem over receipts."""

    def setUp(self):
        token_budget.reset_cache()
        self.addCleanup(token_budget.reset_cache)

    def test_code_budget_hit_is_counted(self):
        tasks = [{"id": "t1", "lang": "python", "level": "easy", "prompt": "p",
                  "test_code": "from solution import *\nassert f() == 1\nprint('OK')\n"}]

        class C:
            run_index = None
            def chat(self, msgs, **k):
                return {"choices": [{"message": {"content": "```python\ndef f():\n    return 1\n```"}}],
                        "usage": {"completion_tokens": graders.CODE_MAX_TOKENS}}   # exactly at the cap

        r = graders.grade_code(C(), tasks, model_slug="m", thinking="off")
        self.assertEqual(r["code_budget_hits"], 1)
        self.assertEqual(r["code_budget"], graders.CODE_MAX_TOKENS)

    def test_tool_call_cut_by_the_cap_is_counted(self):
        tasks = [{"id": "t1", "prompt": "x", "tools": [], "expected": {"name": "f"}}]
        resp = {"choices": [{"finish_reason": "length", "message": {"tool_calls": [
            {"function": {"name": "f", "arguments": "{\"a\":"}}]}}]}      # truncated JSON
        r = graders.grade_tools(FakeClient([resp]), tasks, max_tokens=128)
        self.assertEqual(r["tools_capped"], 1)
        self.assertEqual(r["tools_max_tokens"], 128)

    def test_agent_turn_answered_empty_is_counted(self):
        """The LFM2.5-24B-A2B signature: reasoning spends the whole turn budget and the model
        answers neither content nor a tool call."""
        class Empty:
            run_index = None
            def chat(self, msgs, **k):
                return {"choices": [{"message": {"content": "", "tool_calls": []}}]}
        tasks = [{"id": "t1", "lang": "python", "goal": "g", "max_turns": 3,
                  "test_file": "test_solution.py",
                  "initial_files": {"solution.py": "x = 1\n",
                                    "test_solution.py": "from solution import *\nassert x == 1\n"}}]
        r = graders.grade_agent(Empty(), tasks, max_tokens=512)
        self.assertEqual(r["agent_empty_replies"], 1)
        self.assertEqual(r["agent_max_tokens"], 512)
        self.assertIn("empty=1", r["trace"][0]["detail"])

    def test_a_clean_run_reports_no_probes(self):
        class Ok:
            run_index = None
            def chat(self, msgs, **k):
                return {"choices": [{"finish_reason": "stop", "message": {"content": "hi"}}],
                        "usage": {"completion_tokens": 3}}
        tasks = [{"id": "t1", "prompt": "x", "tools": [], "expected": None}]
        r = graders.grade_tools(Ok(), tasks)
        self.assertEqual(r["tools_capped"], 0)
