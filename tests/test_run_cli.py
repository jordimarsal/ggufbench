import contextlib
import io
import json
import platform
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ggufbench import config, run, report


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
        self.enterContext(config.override(POOL_FILE=self.tmpdir / "pool.jsonl"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

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
        self.enterContext(config.override(MODELS_DIR=self.tmp))

    def tearDown(self):
        shutil.rmtree(self.tmp)

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
        self.enterContext(config.override(STRATA_DIR=self.tmp))
        for n in ("strata-iq3_xxs.json", "strata-iq3_s.json"):
            (self.tmp / n).write_text("{}")

    def tearDown(self):
        shutil.rmtree(self.tmp)

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


KNOWN_ENV = {"gpu": ["RTX 5080 16GB", "RTX 5080 16GB"], "driver": "580.82.09",
             "os": "Linux-test", "ram_gb": 60}


class TestEnvironmentProbe(unittest.TestCase):
    """C5: every result carries a hardware/OS snapshot. The probe is best-effort:
    without nvidia-smi (CPU-only, CI) it degrades to an empty GPU list but never
    raises, and os/ram_gb are always filled."""

    KNOWN = KNOWN_ENV

    def _fake_nvidia_smi(self, stdout, returncode=0):
        return subprocess.CompletedProcess(args=[], returncode=returncode,
                                           stdout=stdout, stderr="")

    def test_nvidia_smi_output_is_shaped(self):
        # One line per GPU: name compacted (vendor prefix out, VRAM in), driver hoisted.
        out = ("NVIDIA GeForce RTX 5080, 16311 MiB, 580.82.09\n"
               "NVIDIA GeForce RTX 5080, 16311 MiB, 580.82.09\n")
        with mock.patch.object(run.subprocess, "run",
                               return_value=self._fake_nvidia_smi(out)):
            env = run._probe_environment()
        self.assertEqual(env["gpu"], ["RTX 5080 16GB", "RTX 5080 16GB"])
        self.assertEqual(env["driver"], "580.82.09")
        # os/ram_gb keep their real values even when the GPU side is faked.
        self.assertEqual(env["os"], platform.platform())
        self.assertTrue(env["ram_gb"] is None or isinstance(env["ram_gb"], int))

    def test_probe_degrades_without_nvidia_smi(self):
        # Missing binary (OSError), hung probe (TimeoutExpired) and a failing call
        # (nonzero exit): gpu empty, driver None, os/ram_gb intact, no exception.
        cases = [OSError("no such file"),
                 subprocess.TimeoutExpired(cmd="nvidia-smi", timeout=5),
                 self._fake_nvidia_smi("", returncode=1)]
        for exc in cases:
            with self.subTest(exc=type(exc).__name__):
                kwargs = {"side_effect": exc} if isinstance(exc, Exception) \
                    else {"return_value": exc}
                with mock.patch.object(run.subprocess, "run", **kwargs):
                    env = run._probe_environment()
                self.assertEqual(env["gpu"], [])
                self.assertIsNone(env["driver"])
                self.assertEqual(env["os"], platform.platform())
                self.assertTrue(env["ram_gb"] is None or isinstance(env["ram_gb"], int))

    def test_real_probe_never_raises(self):
        # No-GPU CI safe: gpu may be [], but the snapshot must always be usable.
        env = run._probe_environment()
        self.assertIsInstance(env["gpu"], list)
        self.assertTrue(env["os"])
        self.assertTrue(env["ram_gb"] is None or env["ram_gb"] > 0)
        self.assertEqual(sorted(env), ["driver", "gpu", "os", "ram_gb"])

    def test_bench_one_records_environment(self):
        # The row produced by _bench_one carries the probe dict (helper patched,
        # not config globals; server/warmup mocked, dims empty -> no grader calls).
        sm = mock.MagicMock()
        sm.wait_ready.return_value = True
        with mock.patch.object(run, "_probe_environment", return_value=self.KNOWN), \
             mock.patch.object(run.S, "ServerManager", return_value=sm), \
             mock.patch.object(run, "warmup", return_value=[0.1, 0.1, 0.1]), \
             contextlib.redirect_stderr(io.StringIO()):
            res = run._bench_one("fake-model.gguf", [], [], None, 8999)
        self.assertEqual(res["environment"], self.KNOWN)
        # Additive only: the pre-existing metadata keys are untouched.
        self.assertIn("model_config_flags", res)
        self.assertIn("server_build", res)


class TestEnvironmentInSavedRow(unittest.TestCase):
    """End-to-end through the CLI (mocked server): the row persisted in the pool
    keeps the environment snapshot. Uses config.override for the tmp results dir."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.enterContext(config.override(POOL_FILE=self.tmpdir / "pool.jsonl",
                                          RESULTS_MODELS=self.tmpdir / "models",
                                          RESULTS_RUNS=self.tmpdir / "runs"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_main_persists_environment(self):
        sm = mock.MagicMock()
        sm.wait_ready.return_value = True
        with mock.patch.object(run, "_probe_environment", return_value=KNOWN_ENV), \
             mock.patch.object(run.S, "ServerManager", return_value=sm), \
             mock.patch.object(run, "warmup", return_value=[0.1, 0.1, 0.1]):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                run.main(["--models", "fake-model.gguf", "--dims", ""])
        pool = report.load_pool()
        self.assertEqual(len(pool), 1)
        self.assertEqual(pool[0]["environment"], KNOWN_ENV)


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


class TestHtmlFlag(unittest.TestCase):
    """--html: regenerate results/report.html from the accumulated pool (the same
    source --scoreboard reads, not just this run's rows), with one line of
    feedback either way."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.enterContext(config.override(POOL_FILE=self.tmpdir / "pool.jsonl",
                                          RESULTS_DIR=self.tmpdir / "results",
                                          RESULTS_MODELS=self.tmpdir / "models",
                                          RESULTS_RUNS=self.tmpdir / "runs"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            run.main(argv)
        return out.getvalue(), err.getvalue()

    def _seed_pool(self):
        # Minimal valid row, same fixture shape as the html report tests
        # (test_html_report._mk): the report needs speed timings and a real ts.
        row = _mk("seed.gguf")
        row["ts"] = "2026-10-10T10:00:00"
        row["speed"].update(speed_ms=100, gen_tps=100.0, prompt_tps=300.0)
        config.POOL_FILE.write_text(json.dumps(row) + "\n", encoding="utf-8")

    def test_flag_parses(self):
        self.assertFalse(run._parse_args([]).html)
        self.assertTrue(run._parse_args(["--html"]).html)

    def test_html_after_mocked_run_writes_and_prints_path(self):
        sm = mock.MagicMock()
        sm.wait_ready.return_value = True
        with mock.patch.object(run, "_probe_environment", return_value=KNOWN_ENV), \
             mock.patch.object(run.S, "ServerManager", return_value=sm), \
             mock.patch.object(run, "warmup", return_value=[0.1, 0.1, 0.1]):
            out, err = self._run(["--models", "fake-model.gguf", "--dims", "", "--html"])
        report_html = config.RESULTS_DIR / "report.html"
        self.assertTrue(report_html.is_file())
        self.assertTrue(report_html.read_text(encoding="utf-8").startswith("<!doctype html>"))
        self.assertIn("→ report:", err)
        self.assertIn(str(report_html), err)

    def test_scoreboard_with_html_writes_report(self):
        # --scoreboard --html = the "refresh everything" combo (read-only mode
        # still regenerates the report from the seeded pool).
        self._seed_pool()
        out, err = self._run(["--scoreboard", "--html"])
        report_html = config.RESULTS_DIR / "report.html"
        self.assertTrue(report_html.is_file())
        self.assertTrue(report_html.read_text(encoding="utf-8").startswith("<!doctype html>"))
        self.assertIn("→ report:", err)
        self.assertIn(str(report_html), err)
        self.assertIn("seed", out)  # the scoreboard itself is still printed

    def test_empty_pool_skips_write_with_message(self):
        out, err = self._run(["--scoreboard", "--html"])
        self.assertFalse((config.RESULTS_DIR / "report.html").exists())
        self.assertIn("pool is empty", err)


if __name__ == "__main__":
    unittest.main()