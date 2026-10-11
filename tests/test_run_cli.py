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
    """--forget must report honestly: it cannot say 'removed' if it removes nothing."""

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
        # With no matching entry: it must NOT say "removed".
        out = self._run(["--forget", "aixonoexisteix"])
        self.assertNotIn("removed", out)
        self.assertIn("no model matching", out)

    def test_forget_reports_actual_removal(self):
        report.save_result(_mk("m"))
        out = self._run(["--forget", "m"])
        self.assertIn("removed", out)
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

class TestResolveModelsResolution(unittest.TestCase):
    """--models must accept short/partial names, not only full paths."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.old_dir = run.config.MODELS_DIR
        run.config.MODELS_DIR = self.tmp

    def tearDown(self):
        shutil.rmtree(self.tmp)
        run.config.MODELS_DIR = self.old_dir

    def test_resolves_bare_name_without_extension(self):
        gguf = self.tmp / "Ornith-1.5-35B-A3B-APEX-MTP-Quality.gguf"
        gguf.write_bytes(b"x")
        self.assertEqual(run.resolve_models("Ornith-1.5-35B-A3B-APEX-MTP-Quality"),
                         [str(gguf)])

    def test_resolves_partial_name(self):
        (self.tmp / "abc-one.gguf").write_bytes(b"x")
        self.assertEqual(run.resolve_models("abc"), [str(self.tmp / "abc-one.gguf")])

    def test_ambiguous_name_warns_and_skips(self):
        for n in ("abc-one.gguf", "abc-two.gguf"):
            (self.tmp / n).write_bytes(b"x")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(run.resolve_models("abc"), [])
        self.assertIn("ambiguous", err.getvalue())

    def test_existing_path_passthrough(self):
        f = self.tmp / "real.gguf"
        f.write_bytes(b"x")
        self.assertEqual(run.resolve_models(str(f)), [str(f)])

    def test_nonexistent_passthrough(self):
        # nonexistent path: passes through as is (llama-server will report the clear error)
        self.assertEqual(run.resolve_models("inexistent.gguf"), ["inexistent.gguf"])


class TestResolveStrataModels(unittest.TestCase):
    """--engine strata: 'model' = a strata-<name>.json config from STRATA_DIR."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.old_dir = run.config.STRATA_DIR
        run.config.STRATA_DIR = self.tmp
        for n in ("strata-iq3_xxs.json", "strata-iq3_s.json"):
            (self.tmp / n).write_text("{}")

    def tearDown(self):
        shutil.rmtree(self.tmp)
        run.config.STRATA_DIR = self.old_dir

    def test_all_globs_strata_configs(self):
        ms = run.resolve_models("all", engine="strata")
        self.assertEqual([Path(m).name for m in ms],
                         ["strata-iq3_s.json", "strata-iq3_xxs.json"])

    def test_bare_name(self):
        self.assertEqual(run.resolve_models("iq3_xxs", engine="strata"),
                         [str(self.tmp / "strata-iq3_xxs.json")])

    def test_full_config_name(self):
        self.assertEqual(run.resolve_models("strata-iq3_s", engine="strata"),
                         [str(self.tmp / "strata-iq3_s.json")])

    def test_existing_path_passthrough(self):
        p = self.tmp / "config-propio.json"
        p.write_text("{}")
        self.assertEqual(run.resolve_models(str(p), engine="strata"), [str(p)])

    def test_unknown_passes_through(self):
        # same criterion as with llama: passes through as is and the server reports the error
        self.assertEqual(run.resolve_models("inexistent", engine="strata"), ["inexistent"])


class TestModelId(unittest.TestCase):
    """Model identity in the pool: .gguf path for llama, config name for Strata."""

    def test_llama_keeps_path(self):
        self.assertEqual(run.model_id("llama", "models/foo.gguf"), "models/foo.gguf")

    def test_strata_uses_config_stem(self):
        mid = run.model_id("strata", "/x/Strata/strata-iq3_xxs.json")
        self.assertEqual(mid, "strata-iq3_xxs")
        # this is what reaches the scoreboard: a clean slug, without path or extension
        self.assertEqual(run.config.slug(mid), "strata-iq3_xxs")


class TestThinkingCli(unittest.TestCase):
    """R1 thinking_batches: --thinking on|off (default off); R6: the mode does not touch the protocol."""

    def test_thinking_defaults_off(self):
        self.assertEqual(run._parse_args(["--forget", "zz"]).thinking, "off")

    def test_thinking_on_off_passthrough(self):
        self.assertEqual(run._parse_args(["--thinking", "on"]).thinking, "on")
        self.assertEqual(run._parse_args(["--thinking", "off"]).thinking, "off")

    def test_thinking_bogus_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                run._parse_args(["--thinking", "maybe"])

    def test_thinking_leaves_protocol_untouched(self):
        # R6: same dims/langs/levels in both modes (the mode only travels in the body)
        a = run._parse_args(["--thinking", "on"])
        b = run._parse_args(["--thinking", "off"])
        self.assertEqual((a.dims, a.lang, a.level), (b.dims, b.lang, b.level))
        self.assertEqual((a.dims, a.lang, a.level), ("speed,tools,code,agent", None, None))


class TestServerBuild(unittest.TestCase):
    """_server_build must read the version wherever it is (llama-server writes it to stderr)."""

    def _fake(self, stdout, stderr=""):
        import subprocess as _sp

        class R:
            def __init__(self):
                self.stdout = stdout
                self.stderr = stderr
        orig = _sp.run
        _sp.run = lambda *a, **k: R()
        return orig

    def test_reads_version_from_stderr(self):
        import subprocess as _sp
        orig = self._fake("", "version: 0.4.0-dev (build 10872)\nbuilt with GNU\n")
        try:
            self.assertEqual(run._server_build("llama"), "0.4.0-dev")
        finally:
            _sp.run = orig

    def test_reads_version_from_stdout(self):
        import subprocess as _sp
        orig = self._fake("version: 1.2.3\n")
        try:
            self.assertEqual(run._server_build("llama"), "1.2.3")
        finally:
            _sp.run = orig


class TestLevelForCode(unittest.TestCase):
    """--level only affects code (R2 of hard_code_tier); outside code, warn and drop it."""

    def test_level_passes_through_with_code(self):
        self.assertEqual(run._level_for_code(["code", "tools"], "hard"), "hard")
        self.assertEqual(run._level_for_code(["code"], "easy"), "easy")

    def test_level_dropped_without_code(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertIsNone(run._level_for_code(["tools", "agent"], "hard"))
        self.assertIn("code is not in --dims", err.getvalue())

    def test_none_level_is_passthrough(self):
        self.assertIsNone(run._level_for_code(["tools"], None))
        self.assertIsNone(run._level_for_code(["code"], None))

    def test_expert_is_a_valid_level(self):
        # discriminative_tasks R1: the parser accepts expert (and rejects unknown ones)
        self.assertEqual(run._level_for_code(["code"], "expert"), "expert")
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                run.main(["--level", "bogus", "--forget", "zz_nothing"])
        # --level expert parses fine (the --forget branch touches nothing when there is no match)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            run.main(["--level", "expert", "--forget", "zz_nothing"])
        self.assertNotIn("invalid choice", err.getvalue())


if __name__ == "__main__":
    unittest.main()