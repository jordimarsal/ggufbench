import unittest, tempfile, shutil
from pathlib import Path
from benchmark import report, config

POOL_FILE = config.RESULTS_MODELS / "pool.jsonl"

def mk(model, gen_tps=None, tools=1.0, code=1.0, agent=1.0,
       code_lang=None, agent_lang=None):
    return {"model": model, "context_mode":"fixed", "ts":"2026-08-03T00:00:00",
            "tasks_version":"x", "server_build":"10250",
            "speed":{"passed":True,"turns":0,"trace":[],"speed_ms":gen_tps},
            "tools":{"passed":True,"turns":0,"trace":[],"score":tools,"by_lang":{},"tasks":[]},
            "code":{"passed":True,"turns":0,"trace":[],"score":code,"by_lang":code_lang or {},"tasks":[]},
            "agent":{"passed":True,"turns":0,"trace":[],"score":agent,"by_lang":agent_lang or {},"tasks":[]}}

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
    def test_compute_global(self):
        a = mk("a", gen_tps=50); b = mk("b", gen_tps=100)
        report.save_result(a); report.save_result(b)
        pool = report.load_pool()
        dims = ["speed", "tools", "code", "agent"]
        ga = report.compute_global([pool[0]], dims)
        gb = report.compute_global([pool[1]], dims)
        self.assertGreater(ga["speed"]["speed_ms"], 0)
        self.assertGreater(gb["speed"]["speed_ms"], 0)
    def test_lang_profile(self):
        r = mk("m", code_lang={"python":1.0,"java":0.0}, agent_lang={"python":0.5})
        prof = report.lang_profile(pool=[r], lang="python")
        self.assertEqual(prof["speed"], {})
        self.assertEqual(prof["tools"], {})
        self.assertIn("python", prof["code"])
        self.assertIn("python", prof["agent"])
    def test_render_has_headers(self):
        a = mk("a"); b = mk("b")
        report.save_result(a); report.save_result(b)
        pool = report.load_pool()
        dims = ["speed", "tools", "code", "agent"]
        out = report.render(pool, dims, title="Test")
        self.assertIn("GLOBAL", out)
        self.assertIn("speed", out)
    def test_forget(self):
        r = mk("m")
        report.save_result(r)
        self.assertEqual(len(report.load_pool()), 1)
        report.forget("m")
        self.assertEqual(len(report.load_pool()), 0)

if __name__ == "__main__":
    unittest.main()