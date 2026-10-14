import unittest

from ggufbench import tasks_loader


class TestHardTasks(unittest.TestCase):
    """T10 de hard_code_tier (16 tasques, 4 per llengua) + C3 fill 2026-10-14 (+1 per
    llengua: la cel·la de codi arriba a 8 easy + 5 hard + 5 expert = 18 per llengua)."""

    def test_twenty_tasks_five_per_lang(self):
        hard = tasks_loader.load("code", level="hard")
        self.assertEqual(len(hard), 20)
        for lang in ("python", "bash", "java", "typescript"):
            n = sum(1 for t in hard if t["lang"] == lang)
            self.assertEqual(n, 5, lang)

    def test_each_cell_has_the_same_shape(self):
        """C3: the four languages carry the same counts (8 easy + 5 hard + 5 expert), so a
        by_lang difference is the model's, not the dataset's."""
        for lang in ("python", "bash", "java", "typescript"):
            counts = {lvl: len(tasks_loader.load("code", level=lvl, lang_filter=lang))
                      for lvl in ("easy", "hard", "expert")}
            self.assertEqual(counts, {"easy": 8, "hard": 5, "expert": 5}, lang)

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
