import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

from ggufbench import config, server

class TestBuildArgs(unittest.TestCase):
    def test_fixed_context(self):
        a = server.build_args("/p/m.gguf", "fixed", 8999)
        self.assertIn("-m", a)
        i = a.index("-m"); self.assertEqual(a[i+1], "/p/m.gguf")
        self.assertIn("-c", a)
        i = a.index("-c"); self.assertEqual(a[i+1], str(config.CONTEXT_FIXED))
        self.assertIn("--port", a)
        i = a.index("--port"); self.assertEqual(a[i+1], "8999")
    def test_explicit_context_int(self):
        a = server.build_args("/p/m.gguf", 4096, 8000)
        i = a.index("-c"); self.assertEqual(a[i+1], "4096")
    def test_flags_all_present(self):
        a = server.build_args("/p/m.gguf", "fixed", 8999)
        for flag in ["-ngl", "--flash-attn", "--load-mode", "none", "--jinja", "--temp", "--seed"]:
            self.assertIn(flag, a)

class TestModelConfigTxt(unittest.TestCase):
    """models/<model>.txt is applied last (can override defaults)."""
    def _args_with_txt(self, txt_body, name="m.gguf"):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / Path(name).with_suffix(".txt").name).write_text(txt_body)
            return server.build_args(str(Path(d) / name), "fixed", 8999)
    def test_parser_skips_comments_blanks_and_joins(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "m.txt").write_text(
                "# header comment\n\n-md /ruta/draft.gguf \\\n--mmproj /ruta/mm.gguf\n")
            self.assertEqual(config.load_model_config_args(Path(d) / "m.gguf"),
                             ["-md", "/ruta/draft.gguf", "--mmproj", "/ruta/mm.gguf"])
        # no .txt next to the gguf: no extra flags
        self.assertEqual(server.describe_config("/p/sense_txt.gguf"), None)
    def test_txt_overrides_context(self):
        a = self._args_with_txt("-c 32000\n")
        self.assertEqual(a[a.index("-c") + 1], "32000")
        self.assertEqual(a.count("-c"), 1)  # the harness' -c is not duplicated
    def test_txt_overrides_cache_k_only(self):
        a = self._args_with_txt("--cache-type-k q8_0\n")
        self.assertEqual(a.count("--cache-type-k"), 1)
        self.assertEqual(a[a.index("--cache-type-k") + 1], "q8_0")
        # the baseline's v is kept (read from config so a baseline change does not break this)
        self.assertIn("--cache-type-v", a)
        i = a.index("--cache-type-v")
        baseline_v = config.CACHE_FLAGS[config.CACHE_FLAGS.index("--cache-type-v") + 1]
        self.assertEqual(a[i + 1], baseline_v)
    def test_txt_spec_type_appended_last(self):
        a = self._args_with_txt("--spec-type draft-mtp\n")
        self.assertIn("draft-mtp", a)
        self.assertGreater(a.index("--spec-type"), a.index("--jinja"))
    def test_infra_flags_filtered(self):
        a = self._args_with_txt("--port 1234 --host 0.0.0.0\n--spec-type draft-mtp\n")
        self.assertNotIn("1234", a)
        self.assertNotIn("0.0.0.0", a)
        self.assertIn("draft-mtp", a)
    def test_equals_form_and_comments(self):
        a = self._args_with_txt("# comment\n\n--ctx-size=65536\n--cache-type-v=q8_0\n")
        # the harness' -c disappears (the .txt defines context) and there are no duplicates
        self.assertNotIn("-c", a)
        self.assertIn("--ctx-size=65536", a)
        self.assertIn("--cache-type-v=q8_0", a)
        self.assertEqual(a.count("--cache-type-k"), 1)  # only the baseline one

class TestProfileFlagAllowList(unittest.TestCase):
    """LOW security fix: model .txt flags pass through without allow-list validation."""

    def _args_with_txt(self, txt_body, name="m.gguf"):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / Path(name).with_suffix(".txt").name).write_text(txt_body)
            return server.build_args(str(Path(d) / name), "fixed", 8999)

    def test_allow_listed_flag_passes_through(self):
        """Allow-listed flags pass through ('--flag value' and '--flag=value').
        --jinja is NOT allow-listed on purpose: the baseline SERVER_FLAGS already
        sets it, so the profile's --jinja is dropped + warned, never passed a
        second time."""
        f = io.StringIO()
        with redirect_stderr(f):
            valid, dropped = server._validate_model_flags(
                ["--jinja", "--spec-type", "draft-mtp"])
        self.assertEqual(valid, ["--spec-type", "draft-mtp"])
        self.assertEqual(dropped, ["--jinja"])
        self.assertIn("dropped: --jinja", f.getvalue())
        # the same through the real command line
        a = self._args_with_txt("--jinja\n--spec-type draft-mtp\n")
        i = a.index("--spec-type"); self.assertEqual(a[i + 1], "draft-mtp")
        self.assertEqual(a.count("--jinja"), 1)  # only the baseline one

    def test_dropping_a_flag_does_not_shift_the_following_pairs(self):
        """Regression: an unknown flag must not swallow the token after it. Each
        flag is judged on its own, so the allow-listed pair that follows a
        dropped one still passes through."""
        f = io.StringIO()
        with redirect_stderr(f):
            valid, dropped = server._validate_model_flags(
                ["--jinja", "--frobnicate", "3", "--ctx-size", "65536",
                 "--spec-type=draft-mtp"])
        self.assertEqual(valid, ["--ctx-size", "65536", "--spec-type=draft-mtp"])
        self.assertEqual(dropped, ["--jinja", "--frobnicate"])
        self.assertIn("dropped: --jinja", f.getvalue())
        self.assertIn("dropped: --frobnicate", f.getvalue())

    def test_unknown_flag_dropped_with_warning(self):
        f = io.StringIO()
        with redirect_stderr(f):
            valid, dropped = server._validate_model_flags(["--frobnicate", "3"])
        self.assertEqual(valid, [])
        self.assertEqual(dropped, ["--frobnicate"])
        self.assertIn("dropped: --frobnicate", f.getvalue())

    def test_value_like_flag_pair_dropped(self):
        f = io.StringIO()
        with redirect_stderr(f):
            valid, dropped = server._validate_model_flags(["--unknown-flag", "-v"])
        self.assertEqual(valid, [])
        # a value that starts with "-" is flag-shaped: it is judged as a flag, so
        # both tokens end up dropped + warned (and neither one swallows the other)
        self.assertIn("--unknown-flag", dropped)
        self.assertIn("-v", dropped)
        self.assertIn("dropped: --unknown-flag", f.getvalue())
        self.assertIn("dropped: -v", f.getvalue())

    def test_infra_flags_still_filtered_before_validation(self):
        """Infra flags (-m/--model/--port/--host) are stripped by _strip_infra
        before validation; they never reach the allow-list check."""
        a = self._args_with_txt("--port 1234 --host 0.0.0.0\n--spec-type draft-mtp\n")
        self.assertNotIn("1234", a)
        self.assertNotIn("0.0.0.0", a)
        self.assertIn("draft-mtp", a)

    def test_describe_config_shows_dropped_names(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "m.txt").write_text(
                "--jinja\n--frobnicate 3\n--ctx-size 65536\n")
            desc = server.describe_config(Path(d) / "m.gguf")
        kept, dropped = desc.split(" | dropped: ")
        self.assertIn("--ctx-size 65536", kept)  # allow-listed: kept, with its value
        self.assertIn("--jinja", dropped)         # not allow-listed: dropped + warned
        self.assertIn("--frobnicate", dropped)
        self.assertNotIn("--ctx-size", dropped)  # a dropped flag must not shift this pair


class TestStrata(unittest.TestCase):
    """--engine strata mode: startup command, port, waits and configuration."""

    def test_strata_command(self):
        a = server.strata_command("/c/strata-iq3_xxs.json", 8080)
        self.assertTrue(str(a[1]).endswith(str(Path("serve") / "server.py")))
        i = a.index("--engine"); self.assertEqual(a[i + 1], "strata")
        i = a.index("--config"); self.assertEqual(a[i + 1], "/c/strata-iq3_xxs.json")
        i = a.index("--port"); self.assertEqual(a[i + 1], "8080")

    def test_ports_and_ready_timeout_per_engine(self):
        st = server.ServerManager("/c/strata-iq3_xxs.json", engine="strata")
        ll = server.ServerManager("/p/m.gguf")
        self.assertEqual(st.port, config.STRATA_PORT)
        self.assertEqual(ll.port, config.PORT)
        # Strata takes minutes to load tens of GB: longer wait than llama-server
        self.assertGreater(st.ready_timeout, ll.ready_timeout)
        # an explicit --port wins (the harness must be able to choose the port)
        self.assertEqual(server.ServerManager("/p/m.gguf", port=9000).port, 9000)
        self.assertEqual(server.ServerManager("/c/x.json", engine="strata", port=9001).port, 9001)

    def test_unknown_engine_rejected(self):
        with self.assertRaises(ValueError):
            server.ServerManager("/p/m.gguf", engine="vllm")

    def test_thinking_recorded_and_validated(self):
        # R1 thinking_batches: the mode is recorded (control goes via the body, ADR-4)
        self.assertEqual(server.ServerManager("/p/m.gguf").thinking, "off")
        self.assertEqual(server.ServerManager("/p/m.gguf", thinking="on").thinking, "on")
        with self.assertRaises(ValueError):
            server.ServerManager("/p/m.gguf", thinking="maybe")

    def test_describe_strata_config(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "strata-iq3_xxs.json"
            p.write_text(json.dumps({"model_name": "qwen3.8-flash-next-iq3_xxs",
                                     "args": ["--max-context", "131072"]}))
            desc = server.describe_config(p, engine="strata")
            self.assertIn("qwen3.8-flash-next-iq3_xxs", desc)
            self.assertIn("--max-context 131072", desc)
            # unreadable config: None (the real error will surface at startup)
            self.assertIsNone(server.describe_config(Path(d) / "no-te-la-tinc.json",
                                                     engine="strata"))
        # the default stays llama (compatibility with existing code)
        self.assertIsNone(server.describe_config("/p/sense_txt.gguf"))


    def test_strata_python_uses_strata_venv(self):
        import sys as _sys
        with tempfile.TemporaryDirectory() as d:
            with config.override(STRATA_DIR=Path(d)):
                # no .venv: fallback to the harness' python (the error stays in the log)
                self.assertEqual(server.strata_python(), _sys.executable)
                (Path(d) / ".venv" / "bin").mkdir(parents=True)
                (Path(d) / ".venv" / "bin" / "python").write_text("")
                # with .venv (the normal case: setup.sh creates it) it uses Strata's interpreter
                self.assertEqual(server.strata_python(),
                                 str(Path(d) / ".venv" / "bin" / "python"))
                # the command really uses it
                a = server.strata_command("/c/strata-iq3_xxs.json", 8080)
                self.assertEqual(a[0], server.strata_python())

    def test_strata_server_output_is_logged(self):
        # the server output must not go to DEVNULL: a startup error
        # (bad venv, busy port) must be readable
        sm = server.ServerManager("/c/strata-iq3_xxs.json", engine="strata", port=8123)
        self.assertIn("strata-server-8123.log", str(sm.log_path))


class TestContextResolution(unittest.TestCase):
    """D1: one code path decides the context — the same (value, source) build_args puts
    on the command line and the receipt records. The profile's pin wins over the mode."""

    def _model(self, d, txt_body=None, name="m.gguf"):
        p = Path(d) / name
        p.write_bytes(b"x")
        if txt_body is not None:
            p.with_suffix(".txt").write_text(txt_body)
        return str(p)

    def test_txt_pin_is_the_profile_source(self):
        with tempfile.TemporaryDirectory() as d:
            mp = self._model(d, "-c 32000\n")
            self.assertEqual(server.resolve_context_and_source(mp, "fixed"),
                             (32000, "profile"))

    def test_equals_form_pin_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            mp = self._model(d, "--ctx-size=65536\n")
            self.assertEqual(server.resolve_context_and_source(mp, "fixed"),
                             (65536, "profile"))

    def test_without_pin_is_the_baseline(self):
        with tempfile.TemporaryDirectory() as d:
            mp = self._model(d)
            self.assertEqual(server.resolve_context_and_source(mp, "fixed"),
                             (config.CONTEXT_FIXED, "baseline"))

    def test_build_args_appends_exactly_what_it_resolved(self):
        # no drift between the decision and the args: one -c, and it is the resolved one
        with tempfile.TemporaryDirectory() as d:
            for body in (None, "-c 32000\n"):
                with self.subTest(txt=body):
                    mp = self._model(d, body)
                    ctx, _src = server.resolve_context_and_source(mp, "fixed")
                    a = server.build_args(mp, "fixed", 8999)
                    self.assertEqual(a.count("-c"), 1)
                    self.assertEqual(a[a.index("-c") + 1], str(ctx))

    def test_adapted_without_the_audit_raises(self):
        with tempfile.TemporaryDirectory() as d:
            mp = self._model(d)
            with config.override(AUDIT_FILE=Path(d) / "no-existeix.json"):
                with self.assertRaises(ValueError) as cm:
                    server.resolve_context_and_source(mp, "adapted")
                self.assertIn("no context audit for", str(cm.exception))
                # the same error before booting a server nobody configured
                with self.assertRaises(ValueError):
                    server.build_args(mp, "adapted", 8999)

    def test_adapted_with_the_audit_is_the_audit_source(self):
        with tempfile.TemporaryDirectory() as d:
            mp = self._model(d)
            audit = Path(d) / "context.json"
            audit.write_text(json.dumps({config.audit_key(mp): {"ctx_max": 120000}}),
                             encoding="utf-8")
            with config.override(AUDIT_FILE=audit):
                self.assertEqual(server.resolve_context_and_source(mp, "adapted"),
                                 (120000, "audit"))

    def test_non_numeric_pin_is_an_error_not_a_silent_default(self):
        with tempfile.TemporaryDirectory() as d:
            mp = self._model(d, "-c molt\n")
            with self.assertRaises(ValueError) as cm:
                server.resolve_context_and_source(mp, "fixed")
            self.assertIn("no numeric value", str(cm.exception))

    def test_strata_config_pin_is_the_profile_source(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "strata-iq3_xxs.json"
            p.write_text(json.dumps({"args": ["--max-context", "131072"]}), encoding="utf-8")
            self.assertEqual(server.resolve_context_and_source(str(p), "fixed", engine="strata"),
                             (131072, "profile"))
            # a config that pins nothing: the engine chooses, the harness does not invent
            q = Path(d) / "strata-x.json"
            q.write_text(json.dumps({"args": ["--pack", "/p"]}), encoding="utf-8")
            self.assertEqual(server.resolve_context_and_source(str(q), "fixed", engine="strata"),
                             (None, "engine-default"))


class TestServerCrashLog(unittest.TestCase):
    """stop() archives the server log when the process died on its own
    (the crash evidence must survive the next start, which truncates it)."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.enterContext(config.override(RESULTS_RUNS=self.tmpdir / "runs"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        for p in Path(tempfile.gettempdir()).glob("ggufbench-llama-server-81*.log"):
            p.unlink(missing_ok=True)

    def _sm(self, port=8199):
        sm = server.ServerManager("/m.gguf", engine="llama", port=port)
        sm.log_path.write_text("boom\n")
        return sm

    def test_crash_preserves_log(self):
        sm = self._sm()
        sm.proc = mock.MagicMock()
        sm.proc.poll.return_value = -6
        sm.pgid = None
        sm._logfh = None
        with redirect_stderr(io.StringIO()):
            sm.stop()
        saved = list((self.tmpdir / "runs").glob("*-CRASH.log"))
        self.assertEqual(len(saved), 1)
        self.assertIn("boom", saved[0].read_text())

    def test_clean_stop_preserves_nothing(self):
        sm = self._sm()
        sm.proc = mock.MagicMock()
        sm.proc.poll.return_value = None
        sm.proc.wait.return_value = 0
        sm.pgid = None
        sm._logfh = None
        with redirect_stderr(io.StringIO()):
            sm.stop()
        where = self.tmpdir / "runs"
        self.assertFalse(where.exists() and any(where.iterdir()))


if __name__ == "__main__":
    unittest.main()

class TestSamplerFlagsAreAllowed(unittest.TestCase):
    """MILLORA §C11 + the A/B experiment of 2026-10-14: a model's profile is where "it runs as
    its authors intend" lives (SPEC §2), so the *sampler* must be declarable there — without
    `--top-k`/`--min-p`/`--xtc-probability` in the allow-list, a profile carrying the card's
    sampler was silently trimmed (the harness dropped `--top-k` and said so), which would have
    measured a half-B."""

    def test_sampler_flags_are_allowed(self):
        for flag in ("--temp", "--top-p", "--top-k", "--min-p", "--xtc-probability",
                     "--repeat-penalty", "--repeat-last-n"):
            self.assertIn(flag, config.ALLOWED_MODEL_FLAGS, flag)

    def test_seed_stays_out_because_it_is_protocol(self):
        """`--seed` is the per-run protocol (C1 stage 2 draws seeds 42+idx); letting a profile
        pin it would silently defeat the repeated-runs measurement."""
        self.assertNotIn("--seed", config.ALLOWED_MODEL_FLAGS)


class TestDraftFlagsAreAllowed(unittest.TestCase):
    """The MTP A/B of 2026-10-16. Heretic's GGUF carries no MTP layers (no `blk.64.nextn.*`),
    so the copy the user asked to isolate lives in its own file — the family's head,
    `models/nerkior/mtp-Qwen3.8-27B-Q4_0.gguf` — and the A/B needs `--spec-draft-model`.
    The allow-list had only the flag's OLD name (`-md`) and dropped the new one without
    failing the run: the leg went out with `--spec-type draft-mtp` and no head, the server
    answered "model doesn't contain MTP layers" and died on load. Only the stderr warning said
    why. Same failure mode as the sampler flags above: a profile that is silently trimmed
    measures something that is not the experiment."""

    def test_draft_head_and_where_it_lives_are_allowed(self):
        for flag in ("--spec-draft-model", "-ngld", "--n-gpu-layers-draft",
                     "--spec-draft-type-k", "-ctkd", "--spec-draft-type-v", "-ctvd"):
            self.assertIn(flag, config.ALLOWED_MODEL_FLAGS, flag)
