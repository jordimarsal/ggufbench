import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

from benchmark import run, report


def _mk(model="m"):
    return {"model": model, "context_mode": "fixed", "ts": "t", "tasks_version": "x",
            "server_build": "b", "speed": {"passed": True, "turns": 0, "trace": [], "score": 0},
            "tools": {"passed": True, "turns": 0, "trace": [], "score": 0},
            "code": {"passed": True, "turns": 0, "trace": [], "score": 0},
            "agent": {"passed": True, "turns": 0, "trace": [], "score": 0}}


class TestForgetCLI(unittest.TestCase):
    """--forget ha d'informar honestament: no pot dir 'esborrat' si no esborra res."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.old_pool = report.POOL_FILE
        report.POOL_FILE = self.tmpdir / "pool.jsonl"

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        report.POOL_FILE = self.old_pool

    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            run.main(argv)
        return out.getvalue() + err.getvalue()

    def test_forget_reports_when_nothing_matches(self):
        # Sense cap entrada coincident: NO ha de dir "esborrat".
        out = self._run(["--forget", "aixonoexisteix"])
        self.assertNotIn("esborrat", out)
        self.assertIn("no s'ha trobat", out)

    def test_forget_reports_actual_removal(self):
        report.save_result(_mk("m"))
        out = self._run(["--forget", "m"])
        self.assertIn("esborrat", out)
        self.assertEqual(len(report.load_pool()), 0)


class TestParseWeights(unittest.TestCase):
    def test_parse_weights(self):
        w = run.parse_weights("tools=0.4,code=0.3,agent=0.2,speed=0.1")
        self.assertAlmostEqual(w["tools"], 0.4)
        self.assertAlmostEqual(sum(w.values()), 1.0)
    def test_resolve_models_explicit(self):
        ms = run.resolve_models(["a.gguf","b.gguf"])
        self.assertEqual(ms, ["a.gguf", "b.gguf"])
    def test_resolve_models_all(self):
        ms = run.resolve_models("all")
        self.assertIsInstance(ms, list)
        self.assertTrue(all(str(m).endswith(".gguf") for m in ms))
    def test_limit_quick(self):
        tasks = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        self.assertEqual(run._limit(tasks, True), [{"id": "a"}])
        self.assertEqual(run._limit(tasks, False), tasks)

if __name__ == "__main__":
    unittest.main()