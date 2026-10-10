import unittest

from benchmark import tasks_loader


class TestExpertTasks(unittest.TestCase):
    """T8 de discriminative_tasks: estructura de les tasques expert (R3, R2)."""

    def test_at_least_three_expert_tasks_per_lang(self):
        # R3: >= 3 per llengua; les dadescreixen no han de trencar aquest test
        expert = tasks_loader.load("code", level="expert")
        self.assertTrue(expert, "cap tasca expert")
        for lang in ("python", "bash", "java", "typescript"):
            n = sum(1 for t in expert if t["lang"] == lang)
            self.assertGreaterEqual(n, 3, lang)

    def test_ids_end_with_expert_and_level_is_expert(self):
        expert = tasks_loader.load("code", level="expert")
        self.assertTrue(expert)
        for t in expert:
            self.assertTrue(t["id"].endswith("_expert"), t["id"])
            self.assertEqual(t["level"], "expert", t["id"])

    def test_each_is_specified_and_judged(self):
        for t in tasks_loader.load("code", level="expert"):
            self.assertGreater(len(t["prompt"]), 60, t["id"])
            self.assertIn("OK", t["test_code"], t["id"])

    def test_data_tasks_carry_their_fixture(self):
        # R2/R3: les tasques de dades porten EXTRA_FILES amb el fitxer que
        # el TEST_CODE llegeix en temps d'execucio
        by_id = {t["id"]: t for t in tasks_loader.load("code", level="expert")}
        for tid, key in (("readings_etl_expert", "readings.csv"),
                         ("access_agg_expert", "access.log"),
                         ("csv_index_expert", "sales.csv"),
                         ("jsonl_agg_expert", "events.jsonl")):
            self.assertIn(tid, by_id, "tasca expert desapareguda")
            self.assertIn(key, by_id[tid]["extra_files"], tid)

    def test_debug_tasks_embed_the_buggy_context(self):
        # les tasques de debug proveeixen el codi defectuos dins el PROMPT
        by_id = {t["id"]: t for t in tasks_loader.load("code", level="expert")}
        for tid in ("metrics_debug_expert", "log_filter_debug_expert",
                    "ledger_debug_expert", "event_debug_expert"):
            self.assertIn(tid, by_id, "tasca expert desapareguda")
            self.assertIn("```", by_id[tid]["prompt"], tid)

    def test_non_expert_tasks_untouched(self):
        # R6: el nivell expert no toca les tasques easy (les de tota la vida)
        easy = {(t["lang"], t["id"]) for t in tasks_loader.load("code", level="easy")}
        self.assertIn(("python", "bubble_sort"), easy)
        self.assertIn(("bash", "fibonacci"), easy)
