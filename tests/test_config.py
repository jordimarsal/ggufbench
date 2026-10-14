import json
import tempfile
import unittest
from pathlib import Path

from ggufbench import config, report

class TestConfig(unittest.TestCase):
    def test_paths_exist(self):
        self.assertTrue(config.BASE_DIR.is_dir())
        # MODELS_DIR is a workspace-layout assumption (../models next to the
        # repo): fresh clones and CI ship no models — skip, don't fail.
        if not config.MODELS_DIR.is_dir():
            self.skipTest(f"no models dir at {config.MODELS_DIR} (fresh clone / CI)")
        self.assertTrue(config.MODELS_DIR.is_dir())
    def test_server_flags_includes_ngl(self):
        self.assertIn("-ngl", config.SERVER_FLAGS)
        i = config.SERVER_FLAGS.index("-ngl")
        self.assertEqual(config.SERVER_FLAGS[i+1], "999")
    def test_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(config.WEIGHTS.values()), 1.0, places=6)
    def test_slug_sanitizes(self):
        self.assertEqual(config.slug("Qwen3-VL-8B-Instruct-1M-Q6_K.gguf"),
                         "qwen3-vl-8b-instruct-1m-q6_k")
        self.assertEqual(config.slug("Model Foo (v2)"), "model-foo-v2")
    def test_slug_converts_dots_to_underscores(self):
        # Test that q5.k.m becomes q5_k_m
        self.assertEqual(config.slug("qwen3-vl-8b-gguf-q5.k.m"),
                         "qwen3-vl-8b-gguf-q5_k_m")


class TestOverride(unittest.TestCase):
    """config.override: swap constants inside a with block, restore on exit.
    The sanctioned way for tests to touch config (no hand-edited globals)."""

    def test_sets_inside_and_restores_after(self):
        original = config.PORT
        with config.override(PORT=1234):
            self.assertEqual(config.PORT, 1234)
        self.assertEqual(config.PORT, original)


class TestBaselineArgv(unittest.TestCase):
    """MILLORA §C10: the harness-owned baseline (SERVER_FLAGS + CACHE_FLAGS) is a condition
    the board must be able to name, so it has to be readable as one value."""

    def test_is_the_common_flags_in_order(self):
        # The order the server actually receives: baseline flags first, then the KV cache.
        self.assertEqual(config.baseline_argv(),
                         list(config.SERVER_FLAGS) + list(config.CACHE_FLAGS))

    def test_carries_the_kv_cache_that_changed(self):
        """ADR-0008 (KV q4_0 -> q8_0) is exactly the kind of change the digest exists for."""
        argv = config.baseline_argv()
        self.assertIn("--cache-type-k", argv)
        self.assertIn("q8_0", argv)

    def test_returns_a_fresh_list(self):
        """A caller must not be able to edit the constants through it: the baseline is what
        the digest is computed from, and a mutated constant would silently re-label history."""
        argv = config.baseline_argv()
        argv.append("-c")
        argv[0] = "--tampered"
        self.assertEqual(config.baseline_argv(),
                         list(config.SERVER_FLAGS) + list(config.CACHE_FLAGS))
        self.assertNotIn("-c", config.SERVER_FLAGS)
        self.assertEqual(config.SERVER_FLAGS[0], "-ngl")

if __name__ == "__main__":
    unittest.main()
class TestBaselinePinsTheSampler(unittest.TestCase):
    """MILLORA §C11: llama.cpp applies a GGUF's `general.sampling.*` to every sampler
    parameter the command line does not set explicitly (`common.cpp`, guarded by
    COMMON_PARAMS_SAMPLING_CONFIG_*). The fleet ships top_k 20/64 and nothing at all, so the
    baseline must pin the three parameters it does not choose for a reason — otherwise the
    "same conditions" table compares models with different samplers."""

    def _value_of(self, flag):
        argv = config.SERVER_FLAGS
        return argv[argv.index(flag) + 1] if flag in argv else None

    def test_top_k_is_pinned_at_the_engine_default(self):
        self.assertEqual(self._value_of("--top-k"), "40")

    def test_min_p_and_xtc_are_pinned_too(self):
        self.assertEqual(self._value_of("--min-p"), "0.05")
        self.assertEqual(self._value_of("--xtc-probability"), "0.0")

    def test_every_sampler_parameter_the_engine_exposes_is_pinned(self):
        """temp/top-p/repeat are the protocol values; top-k/min-p/xtc are the neutrals that
        would otherwise come from the metadata (or the engine default, which is the same
        number — pinned so a future GGUF cannot change it)."""
        for flag in ("--temp", "--top-p", "--repeat-penalty", "--repeat-last-n", "--seed",
                     "--top-k", "--min-p", "--xtc-probability"):
            self.assertIn(flag, config.SERVER_FLAGS, flag)

    def test_the_baseline_identity_follows_the_sampler(self):
        """The pin is a condition: adding it changes the baseline id, which is what makes the
        rows measured before it visibly different on the board (§C10)."""
        self.assertNotEqual(report.baseline_id({"baseline_flags": " ".join(config.SERVER_FLAGS)}),
                            report.baseline_id({"baseline_flags": " ".join(config.SERVER_FLAGS + ["--top-k", "20"])}))


class TestTasksVersion(unittest.TestCase):
    def test_class_marks_the_task_generation(self):
        # discriminative_tasks R4 bumped it to v3 for the expert set; v4 marked the C3
        # counts (16/60/60) and v5 marks the C3+C4 fill (tools 18 / code 72 / agent 68,
        # multi-file agent projects) — a version is a label, and the C3 additions proved it
        # cannot describe a task set (three sets lived under v3): the per-row marker is
        # task_signature (report.task_signature, MILLORA §C9).
        self.assertEqual(config.TASKS_VERSION, "v5")

class TestWeightsUnchanged(unittest.TestCase):
    def test_weights_unchanged(self):
        # R8 hard_code_tier: the hard level does not touch the weights nor the other dimensions
        self.assertEqual(config.WEIGHTS,
                         {"tools": 0.30, "code": 0.30, "agent": 0.25, "speed": 0.15})
    def test_r7_retired_no_efficiency_dimension(self):
        # discriminative_tasks R7 (retired): efficiency (tokens per task) stays as a
        # recorded metric (out_tokens), never as a scored dimension.
        self.assertEqual(set(config.WEIGHTS), {"speed", "tools", "code", "agent"})

class TestThinkingBody(unittest.TestCase):
    """R1 thinking_batches: the thinking mode travels via the body, never via the prompts."""
    def test_default_is_off(self):
        self.assertEqual(config.THINKING_DEFAULT, "off")
    def test_off_disables_for_both_engines(self):
        for engine in ("llama", "strata"):
            self.assertEqual(config.thinking_body(engine, "off"),
                             {"chat_template_kwargs": {"enable_thinking": False}})
    def test_on_is_empty(self):
        self.assertEqual(config.thinking_body("llama", "on"), {})
        self.assertEqual(config.thinking_body("strata", "on"), {})
    def test_rejects_bogus(self):
        with self.assertRaises(ValueError):
            config.thinking_body("llama", "maybe")
        with self.assertRaises(ValueError):
            config.thinking_body("vllm", "off")
    def test_only_touches_extra_channel(self):
        # R6: the mode must not contaminate prompts/dims: the dict only carries the kwarg
        self.assertEqual(set(config.thinking_body("llama", "off")), {"chat_template_kwargs"})


class TestContextFixed(unittest.TestCase):
    """D3: the baseline context is 32768 (the code budget). Pool rows measured at 16384
    are a different condition — the row's ctx_resolved is what tells them apart."""

    def test_baseline_matches_the_code_budget(self):
        self.assertEqual(config.CONTEXT_FIXED, 32768)

    def test_audit_file_lives_with_the_pool(self):
        # results/models/: the same directory the audit tool writes and the pool reads
        self.assertEqual(config.AUDIT_FILE, config.RESULTS_MODELS / "context.json")


class TestResolveContext(unittest.TestCase):
    """D1: `adapted` reads the context-audit artifact. There is no silent fallback:
    the estimator it described never existed, so without the audit it raises."""

    def _audit(self, d, body):
        p = Path(d) / "context.json"
        p.write_text(body if isinstance(body, str) else json.dumps(body), encoding="utf-8")
        return p

    def test_fixed_is_the_baseline_constant(self):
        self.assertEqual(config.resolve_context("fixed"), config.CONTEXT_FIXED)

    def test_int_passes_through(self):
        self.assertEqual(config.resolve_context(4096), 4096)

    def test_adapted_reads_the_audited_value(self):
        with tempfile.TemporaryDirectory() as d:
            audit = self._audit(d, {"models_foo": {"ctx_max": 120000, "note": "measured"}})
            with config.override(AUDIT_FILE=audit):
                self.assertEqual(config.resolve_context("adapted", "models/Foo.gguf"), 120000)

    def test_adapted_without_the_artifact_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with config.override(AUDIT_FILE=Path(d) / "no-existeix.json"):
                with self.assertRaises(ValueError) as cm:
                    config.resolve_context("adapted", "models/Foo.gguf")
        self.assertIn("no context audit for models_foo", str(cm.exception))
        self.assertIn("context-audit.py", str(cm.exception))

    def test_adapted_without_the_slug_raises(self):
        with tempfile.TemporaryDirectory() as d:
            audit = self._audit(d, {"altre-model": {"ctx_max": 8000}})
            with config.override(AUDIT_FILE=audit):
                with self.assertRaises(ValueError) as cm:
                    config.resolve_context("adapted", "models/Foo.gguf")
        self.assertIn("no context audit for models_foo", str(cm.exception))

    def test_adapted_rejects_a_malformed_audit(self):
        # not JSON, or ctx_max not an int: the same honest error, never a guessed number
        for body in ("no és json {", '{"models_foo": {"ctx_max": "120000"}}',
                     '{"models_foo": 120000}'):
            with self.subTest(body=body):
                with tempfile.TemporaryDirectory() as d:
                    audit = self._audit(d, body)
                    with config.override(AUDIT_FILE=audit):
                        with self.assertRaises(ValueError):
                            config.resolve_context("adapted", "models/Foo.gguf")

    def test_adapted_needs_a_model_path(self):
        with self.assertRaises(ValueError):
            config.resolve_context("adapted")

    def test_unknown_mode_raises(self):
        with self.assertRaises(ValueError):
            config.resolve_context("potser", "models/Foo.gguf")

    def test_audit_key_is_the_identity_the_pool_uses(self):
        # .gguf path -> config.slug of the path (what the pool stores as `model`);
        # a Strata config -> its name without extension ('strata-iq3_xxs').
        self.assertEqual(config.audit_key("models/Foo.gguf"), config.slug("models/Foo.gguf"))
        self.assertEqual(config.audit_key("/x/Strata/strata-iq3_xxs.json"), "strata-iq3_xxs")
