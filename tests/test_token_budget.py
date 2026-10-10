import unittest, json, tempfile, shutil
from pathlib import Path
from benchmark import token_budget


class TestTokenBudget(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.old_file = token_budget.BUDGET_FILE
        token_budget.BUDGET_FILE = self.tmpdir / "token_budgets.json"
        token_budget.reset_cache()

    def tearDown(self):
        token_budget.BUDGET_FILE = self.old_file
        token_budget.reset_cache()
        shutil.rmtree(self.tmpdir)

    def test_get_missing_returns_none(self):
        self.assertIsNone(token_budget.get("code", "model-a", "off", "python", "bubble_sort"))

    def test_put_then_get(self):
        token_budget.put("code", "model-a", "off", "python", "bubble_sort", 4096)
        token_budget.reset_cache()  # simula una nova run
        self.assertEqual(token_budget.get("code", "model-a", "off", "python", "bubble_sort"), 4096)

    def test_keys_are_per_model(self):
        token_budget.put("code", "model-a", "off", "python", "bubble_sort", 4096)
        token_budget.put("code", "model-b", "off", "python", "bubble_sort", 8192)
        token_budget.reset_cache()
        self.assertEqual(token_budget.get("code", "model-a", "off", "python", "bubble_sort"), 4096)
        self.assertEqual(token_budget.get("code", "model-b", "off", "python", "bubble_sort"), 8192)

    def test_persists_to_disk(self):
        token_budget.put("code", "m", "off", "python", "fib", 4096)
        token_budget.reset_cache()
        data = json.loads(token_budget.BUDGET_FILE.read_text())
        self.assertIn("code/m/off/python/fib", data)

    def test_keys_differ_by_thinking(self):
        # R2 thinking_batches: els dos modes calibren independentment
        token_budget.put("code", "m", "off", "python", "fib", 4096)
        token_budget.put("code", "m", "on", "python", "fib", 8192)
        token_budget.reset_cache()
        self.assertEqual(token_budget.get("code", "m", "off", "python", "fib"), 4096)
        self.assertEqual(token_budget.get("code", "m", "on", "python", "fib"), 8192)

    def test_old_schema_ignored(self):
        # R3: era 16384 (sense _schema) -> invisible; es regenera al pròxim put
        token_budget.BUDGET_FILE.write_text(json.dumps({"code/m/off/python/fib": 4096}))
        token_budget.reset_cache()
        self.assertIsNone(token_budget.get("code", "m", "off", "python", "fib"))
        token_budget.put("code", "m", "off", "python", "fib", 8192)
        token_budget.reset_cache()
        data = json.loads(token_budget.BUDGET_FILE.read_text())
        self.assertEqual(data.get("_schema"), 2)
        self.assertEqual(token_budget.get("code", "m", "off", "python", "fib"), 8192)

    def test_put_writes_schema(self):
        token_budget.put("code", "m", "off", "python", "fib", 4096)
        data = json.loads(token_budget.BUDGET_FILE.read_text())
        self.assertEqual(data.get("_schema"), 2)


if __name__ == "__main__":
    unittest.main()
