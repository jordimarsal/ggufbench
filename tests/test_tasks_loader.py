import unittest, os, textwrap
from benchmark import tasks_loader

class TestLoad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = os.path.join(os.path.dirname(__file__), "..", "tasks", "tools")
        with open(os.path.join(d, "_tmpexample.py"), "w") as f:
            f.write(textwrap.dedent('''
                ID = "tmp"
                PROMPT = "hi"
                TOOLS = []
                EXPECTED = None
            '''))
    @classmethod
    def tearDownClass(cls):
        p = os.path.join(os.path.dirname(__file__), "..", "tasks", "tools", "_tmpexample.py")
        if os.path.exists(p): os.remove(p)
    def test_load_returns_list(self):
        ts = tasks_loader.load("tools")
        self.assertIsInstance(ts, list)
    def test_skips_underscore(self):
        ts = tasks_loader.load("tools")
        self.assertFalse(any(t["id"] == "tmp" for t in ts))

class TestLevel(unittest.TestCase):
    """R1/R2 de hard_code_tier: level per sufix _hard a l'ID, i filtre a load()."""

    @classmethod
    def setUpClass(cls):
        d = os.path.join(os.path.dirname(__file__), "..", "tasks", "code", "python")
        cls.paths = []
        for name, body in (
            ("zz_tmpeasy.py", 'ID = "zz_easy"\nPROMPT = "p"\nLANG = "python"\nTEST_CODE = "t"\n'),
            ("zz_tmphard_hard.py", 'ID = "zz_tmp_hard"\nPROMPT = "p"\nLANG = "python"\nTEST_CODE = "t"\n'),
        ):
            p = os.path.join(d, name)
            with open(p, "w") as f:
                f.write(body)
            cls.paths.append(p)

    @classmethod
    def tearDownClass(cls):
        for p in cls.paths:
            if os.path.exists(p):
                os.remove(p)

    def test_level_hard_by_id_suffix(self):
        ts = {t["id"]: t for t in tasks_loader.load("code")}
        self.assertEqual(ts["zz_easy"]["level"], "easy")
        self.assertEqual(ts["zz_tmp_hard"]["level"], "hard")

    def test_level_filter(self):
        ids = [t["id"] for t in tasks_loader.load("code", level="hard")]
        self.assertIn("zz_tmp_hard", ids)
        self.assertFalse(any(t["id"] == "zz_tmp_hard"
                             for t in tasks_loader.load("code", level="easy")))

    def test_non_code_dims_get_no_level(self):
        for t in tasks_loader.load("tools"):
            self.assertNotIn("level", t)

if __name__ == "__main__":
    unittest.main()