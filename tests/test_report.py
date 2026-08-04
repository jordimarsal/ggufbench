import unittest, tempfile, shutil
from pathlib import Path
from benchmark import report, config

POOL_FILE = config.RESULTS_MODELS / "pool.jsonl"

W = {"tools": 0.30, "code": 0.30, "agent": 0.25, "speed": 0.15}


def mk(model, gen_tps=None, tools=1.0, code=1.0, agent=1.0,
       code_lang=None, agent_lang=None):
    return {"model": model, "context_mode": "fixed", "ts": "2026-08-03T00:00:00",
            "tasks_version": "x", "server_build": "10250",
            "speed": {"passed": True, "turns": 0, "trace": [], "speed_ms": gen_tps},
            "tools": {"passed": True, "turns": 0, "trace": [], "score": tools, "by_lang": {}, "tasks": []},
            "code": {"passed": True, "turns": 0, "trace": [], "score": code, "by_lang": code_lang or {}, "tasks": []},
            "agent": {"passed": True, "turns": 0, "trace": [], "score": agent, "by_lang": agent_lang or {}, "tasks": []}}


class TestReport(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.old_pool_file = report.POOL_FILE
        report.POOL_FILE = self.tmpdir / "pool.jsonl"

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        report.POOL_FILE = self.old_pool_file

    def test_save_and_load(self):
        r = mk("m", gen_tps=100)
        report.save_result(r)
        pool = report.load_pool()
        self.assertEqual(len(pool), 1)
        self.assertEqual(pool[0]["model"], "m")

    def test_upsert_replaces_same_model(self):
        report.save_result(mk("m", gen_tps=50, tools=0.4))
        report.save_result(mk("m", gen_tps=99, tools=0.8))  # re-run -> upsert
        pool = report.load_pool()
        self.assertEqual(len(pool), 1)
        self.assertEqual(pool[0]["speed"]["speed_ms"], 99)

    def test_render_shows_per_model_scores(self):
        report.save_result(mk("alpha", gen_tps=100, tools=0.5, code=1.0, agent=0.0))
        out = report.render(report.load_pool(), W)
        self.assertIn("MODEL", out)
        self.assertIn("GLOBAL", out)
        self.assertIn("alpha", out)
        self.assertIn("50%", out)   # tools
        self.assertIn("100%", out)  # code

    def test_global_score_weighted(self):
        r = mk("m", gen_tps=100, tools=1.0, code=1.0, agent=1.0)
        # model únic -> min_speed = el seu -> speed_score = 1.0 -> global = 1.0
        g = report._global_score(r, W, 100)
        self.assertAlmostEqual(g, 1.0)

    def test_global_score_missing_speed(self):
        r = mk("m", gen_tps=0, tools=1.0, code=1.0, agent=1.0)
        # sense speed_ms -> speed_score = 0; la resta suma 0.85
        g = report._global_score(r, W, 100)
        self.assertAlmostEqual(g, 0.85)

    def test_speed_normalization_fastest_is_best(self):
        a = mk("a", gen_tps=100, tools=1.0, code=1.0, agent=1.0)  # ràpid
        b = mk("b", gen_tps=200, tools=1.0, code=1.0, agent=1.0)  # lent
        report.save_result(a)
        report.save_result(b)
        min_speed = 100
        ga = report._global_score(a, W, min_speed)
        gb = report._global_score(b, W, min_speed)
        self.assertAlmostEqual(ga, 1.0)     # el més ràpid -> speed_score 1.0
        self.assertAlmostEqual(gb, 0.925)   # speed_score 0.5
        self.assertGreater(ga, gb)

    def test_render_sorted_by_global_desc(self):
        report.save_result(mk("slow", gen_tps=300, tools=0.2, code=0.2, agent=0.2))
        report.save_result(mk("fast", gen_tps=50, tools=1.0, code=1.0, agent=1.0))
        out = report.render(report.load_pool(), W)
        i_fast = out.index("fast")
        i_slow = out.index("slow")
        self.assertLess(i_fast, i_slow)  # fast (millor global) apareix abans

    def test_lang_profile(self):
        r = mk("m", code_lang={"python": 1.0, "java": 0.0}, agent_lang={"python": 0.5})
        prof = report.lang_profile(pool=[r], lang="python")
        self.assertEqual(prof["speed"], {})
        self.assertEqual(prof["tools"], {})
        self.assertIn("python", prof["code"])
        self.assertIn("python", prof["agent"])

    def test_forget(self):
        r = mk("m")
        report.save_result(r)
        self.assertEqual(len(report.load_pool()), 1)
        report.forget("m")
        self.assertEqual(len(report.load_pool()), 0)


if __name__ == "__main__":
    unittest.main()
