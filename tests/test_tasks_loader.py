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
    """R1 hard_code_tier + R1 discriminative_tasks: level by ID suffix, filter in load()."""

    @classmethod
    def setUpClass(cls):
        d = os.path.join(os.path.dirname(__file__), "..", "tasks", "code", "python")
        cls.paths = []
        for name, body in (
            ("zz_tmpeasy.py", 'ID = "zz_easy"\nPROMPT = "p"\nLANG = "python"\nTEST_CODE = "t"\n'),
            ("zz_tmphard_hard.py", 'ID = "zz_tmp_hard"\nPROMPT = "p"\nLANG = "python"\nTEST_CODE = "t"\n'),
            ("zz_tmpexpert_expert.py", 'ID = "zz_tmp_expert"\nPROMPT = "p"\nLANG = "python"\nTEST_CODE = "t"\n'),
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
        self.assertEqual(ts["zz_tmp_expert"]["level"], "expert")

    def test_level_filter(self):
        ids = [t["id"] for t in tasks_loader.load("code", level="hard")]
        self.assertIn("zz_tmp_hard", ids)
        self.assertFalse(any(t["id"] == "zz_tmp_hard"
                             for t in tasks_loader.load("code", level="easy")))
        expert = [t["id"] for t in tasks_loader.load("code", level="expert")]
        self.assertIn("zz_tmp_expert", expert)
        self.assertNotIn("zz_tmp_hard", expert)
        self.assertNotIn("zz_easy", expert)
        # the real expert tasks are there; no easy one sneaks in
        self.assertIn("vault_engine_expert", expert)
        for t in tasks_loader.load("code", level="easy"):
            self.assertNotIn(t["id"], expert)

    def test_non_code_dims_get_no_level(self):
        for t in tasks_loader.load("tools"):
            self.assertNotIn("level", t)


class TestExtraFiles(unittest.TestCase):
    """R2 discriminative_tasks: EXTRA_FILES validated in the loader and passed to the task dict."""

    def test_code_tasks_carry_extra_files(self):
        # relative to the manifest: the key is present in EVERY code task and is a dict;
        # tasks with a real fixture carry it full, those without, empty.
        by_id = {t["id"]: t for t in tasks_loader.load("code")}
        for tid, t in by_id.items():
            self.assertIn("extra_files", t, tid)
            self.assertIsInstance(t["extra_files"], dict, tid)
        self.assertEqual(by_id["readings_etl_expert"]["extra_files"].keys(),
                         {"readings.csv"})
        self.assertEqual(by_id["bubble_sort"]["extra_files"], {})

    def test_invalid_extra_files_rejected(self):
        for bad in ("sub/f.csv", "..", "/abs.csv", "solution.py",
                    "test_solution.py", "Test.java", "Solution.java", ""):
            with self.assertRaises(ValueError, msg=bad):
                tasks_loader._check_extra_files("zz_x", {bad: "c"})

    def test_valid_extra_files_accepted(self):
        tasks_loader._check_extra_files("zz_x", {"data.csv": "a", "helper.ts": "b",
                                                 "Helper.java": "c", "fixture.log": "d"})

    def test_extra_files_passthrough_from_module(self):
        d = os.path.join(os.path.dirname(__file__), "..", "tasks", "code", "python")
        p = os.path.join(d, "zz_tmpextra_expert.py")
        with open(p, "w") as f:
            f.write('ID = "zz_tmpextra_expert"\nPROMPT = "p"\nLANG = "python"\n'
                    'TEST_CODE = "t"\nEXTRA_FILES = {"data.csv": "a,b\\n"}\n')
        try:
            ts = {t["id"]: t for t in tasks_loader.load("code")}
            self.assertEqual(ts["zz_tmpextra_expert"]["extra_files"], {"data.csv": "a,b\n"})
            self.assertEqual(ts["zz_tmpextra_expert"]["level"], "expert")
        finally:
            if os.path.exists(p):
                os.remove(p)

if __name__ == "__main__":
    unittest.main()