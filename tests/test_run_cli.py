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

class TestResolveModelsResolution(unittest.TestCase):
    """--models ha d'acceptar noms curts/parcials, no només camins complets."""

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
        self.assertIn("ambigu", err.getvalue())

    def test_existing_path_passthrough(self):
        f = self.tmp / "real.gguf"
        f.write_bytes(b"x")
        self.assertEqual(run.resolve_models(str(f)), [str(f)])

    def test_nonexistent_passthrough(self):
        # camí inexistent: passa tal qual (llama-server en donarà l'error clar)
        self.assertEqual(run.resolve_models("inexistent.gguf"), ["inexistent.gguf"])


class TestResolveStrataModels(unittest.TestCase):
    """--engine strata: 'model' = un config strata-<nom>.json de STRATA_DIR."""

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
        # mateix criteri que amb llama: passa tal qual i el servidor dona l'error
        self.assertEqual(run.resolve_models("inexistent", engine="strata"), ["inexistent"])


class TestModelId(unittest.TestCase):
    """Identitat del model al pool: camí .gguf per a llama, nom del config per a Strata."""

    def test_llama_keeps_path(self):
        self.assertEqual(run.model_id("llama", "models/foo.gguf"), "models/foo.gguf")

    def test_strata_uses_config_stem(self):
        mid = run.model_id("strata", "/x/Strata/strata-iq3_xxs.json")
        self.assertEqual(mid, "strata-iq3_xxs")
        # és el que arriba al marcador: un slug net, sense camí ni extensió
        self.assertEqual(run.config.slug(mid), "strata-iq3_xxs")


class TestThinkingCli(unittest.TestCase):
    """R1 thinking_batches: --thinking on|off (default off); R6: el mode no toca el protocol."""

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
        # R6: mateixos dims/langs/levels en els dos modes (el mode només viatja al cos)
        a = run._parse_args(["--thinking", "on"])
        b = run._parse_args(["--thinking", "off"])
        self.assertEqual((a.dims, a.lang, a.level), (b.dims, b.lang, b.level))
        self.assertEqual((a.dims, a.lang, a.level), ("speed,tools,code,agent", None, None))


class TestLevelForCode(unittest.TestCase):
    """--level només afecta code (R2 de hard_code_tier); fora de code, avís i fora."""

    def test_level_passes_through_with_code(self):
        self.assertEqual(run._level_for_code(["code", "tools"], "hard"), "hard")
        self.assertEqual(run._level_for_code(["code"], "easy"), "easy")

    def test_level_dropped_without_code(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertIsNone(run._level_for_code(["tools", "agent"], "hard"))
        self.assertIn("code no és a --dims", err.getvalue())

    def test_none_level_is_passthrough(self):
        self.assertIsNone(run._level_for_code(["tools"], None))
        self.assertIsNone(run._level_for_code(["code"], None))

    def test_expert_is_a_valid_level(self):
        # discriminative_tasks R1: el parser accepta expert (i rebutja desconeguts)
        self.assertEqual(run._level_for_code(["code"], "expert"), "expert")
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                run.main(["--level", "bogus", "--forget", "zz_nothing"])
        # --level expert parseja bé (el branch --forget no toca res si no hi ha match)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            run.main(["--level", "expert", "--forget", "zz_nothing"])
        self.assertNotIn("invalid choice", err.getvalue())


if __name__ == "__main__":
    unittest.main()