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
