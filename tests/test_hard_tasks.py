import unittest

from benchmark import tasks_loader


class TestHardTasks(unittest.TestCase):
    """T10 de hard_code_tier: estructura de les 16 tasques hard (4 per llengua)."""

    def test_sixteen_tasks_four_per_lang(self):
        hard = tasks_loader.load("code", level="hard")
        self.assertEqual(len(hard), 16)
        for lang in ("python", "bash", "java", "typescript"):
            n = sum(1 for t in hard if t["lang"] == lang)
            self.assertEqual(n, 4, lang)

    def test_ids_end_with_hard(self):
        for t in tasks_loader.load("code", level="hard"):
            self.assertTrue(t["id"].endswith("_hard"), t["id"])

    def test_each_is_specified_and_judged(self):
        for t in tasks_loader.load("code", level="hard"):
            self.assertGreater(len(t["prompt"]), 60, t["id"])
            self.assertIn("OK", t["test_code"], t["id"])

    def test_levels_are_disjoint_and_complete(self):
        # els IDs easy es repeteixen entre llenguas (bubble_sort x4): la clau es (lang, id)
        easy = {(t["lang"], t["id"]) for t in tasks_loader.load("code", level="easy")}
        hard = {(t["lang"], t["id"]) for t in tasks_loader.load("code", level="hard")}
        expert = {(t["lang"], t["id"]) for t in tasks_loader.load("code", level="expert")}
        self.assertFalse(easy & hard)
        self.assertFalse(easy & expert)
        self.assertFalse(hard & expert)
        total = len(tasks_loader.load("code"))
        self.assertEqual(len(easy) + len(hard) + len(expert), total)


if __name__ == "__main__":
    unittest.main()
