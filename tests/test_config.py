import unittest
from benchmark import config

class TestConfig(unittest.TestCase):
    def test_paths_exist(self):
        self.assertTrue(config.BASE_DIR.is_dir())
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

if __name__ == "__main__":
    unittest.main()
class TestTasksVersion(unittest.TestCase):
    def test_v3_marks_expert_tier(self):
        # discriminative_tasks R4: el conjunt expert (+12 tasques, EXTRA_FILES)
        # ha de pujar la versió; el pool la fa servir per distingir condicions.
        self.assertEqual(config.TASKS_VERSION, "v3")

class TestWeightsUnchanged(unittest.TestCase):
    def test_weights_unchanged(self):
        # R8 hard_code_tier: el nivell hard no toca els pesos ni la resta de dimensions
        self.assertEqual(config.WEIGHTS,
                         {"tools": 0.30, "code": 0.30, "agent": 0.25, "speed": 0.15})
    def test_r7_retired_no_efficiency_dimension(self):
        # discriminative_tasks R7 (retired): l'eficiència (tokens per tasca) queda com a
        # mètrica registrada (out_tokens), mai com a dimensió puntuada.
        self.assertEqual(set(config.WEIGHTS), {"speed", "tools", "code", "agent"})

class TestThinkingBody(unittest.TestCase):
    """R1 thinking_batches: el mode de pensament viatja pel cos, mai pels prompts."""
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
        # R6: el mode no pot contaminar prompts/dims: el dict només porta el kwarg
        self.assertEqual(set(config.thinking_body("llama", "off")), {"chat_template_kwargs"})
