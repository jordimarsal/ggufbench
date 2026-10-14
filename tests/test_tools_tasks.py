import unittest

from ggufbench import config, tasks_loader


class TestToolsTasks(unittest.TestCase):
    """Structural invariants of the tool-calling tasks.

    A tools task is graded on ONE call: the model's first call must carry exactly the name
    and arguments of EXPECTED (`graders._args_equal` is a plain `==`). Nothing checked that
    EXPECTED was *reachable*: a typo in the name or in an argument key would define a task no
    model can ever pass, and the row would just read "tools 94%" without saying the task was
    impossible.
    """

    @classmethod
    def setUpClass(cls):
        cls.tasks = tasks_loader.load("tools")

    def _calling(self):
        """Tasks that expect a call. `expected = None` marks the other kind — the task asks
        the model to call NOTHING (`noop`), which is why such a task may ship an empty toolset."""
        return [t for t in self.tasks if t["expected"] is not None]

    def test_every_task_is_specified(self):
        for t in self.tasks:
            self.assertTrue(t["id"], t)
            self.assertGreater(len(t["prompt"]), 30, t["id"])
            if t["expected"] is not None:
                self.assertTrue(t["tools"], f"{t['id']}: a task that expects a call needs tools")

    def test_only_the_no_call_task_has_an_empty_toolset(self):
        for t in self.tasks:
            if not t["tools"]:
                self.assertIsNone(t["expected"], f"{t['id']}: an empty toolset has nothing to call")

    def test_expected_name_exists_in_the_task_toolset(self):
        for t in self._calling():
            names = [f["function"]["name"] for f in t["tools"]]
            self.assertIn(t["expected"]["name"], names, t["id"])

    def test_expected_arguments_match_that_tool_schema(self):
        """Every expected argument key must be declared by the tool it belongs to (values
        are not validated: the task author chooses them), so EXPECTED can be produced."""
        for t in self._calling():
            exp = t["expected"]
            schema = next(f["function"]["parameters"] for f in t["tools"]
                          if f["function"]["name"] == exp["name"])
            allowed = set(schema.get("properties") or {})
            for key in (exp.get("arguments") or {}):
                self.assertIn(key, allowed, f"{t['id']}: argument '{key}' not in the schema")

    def test_ids_are_unique(self):
        ids = [t["id"] for t in self.tasks]
        self.assertEqual(len(ids), len(set(ids)))

    def test_two_state_tasks_are_not_ambiguous(self):
        """A task whose toolset offers both a safe and a destructive path must say which one
        the prompt wants (the whole discrimination of `archive_not_delete`)."""
        by_id = {t["id"]: t for t in self.tasks}
        t = by_id["archive_not_delete"]
        self.assertIn("no facis servir delete_file", t["prompt"])
        self.assertEqual(t["expected"]["name"], "archive_file")

    def test_hard_argument_task_keeps_its_nested_shape(self):
        by_id = {t["id"]: t for t in self.tasks}
        args = by_id["nested_filter_args"]["expected"]["arguments"]
        self.assertEqual(args["filter"]["level"], "ERROR")
        self.assertEqual(args["filter"]["tags"], ["db", "net"])
        self.assertEqual(args["limit"], 5)

    def test_dataset_grew_without_weakening_the_dimension(self):
        # C3 fill: the cell goes from 16 to 18 tasks; the bound keeps typos from shrinking it.
        self.assertGreaterEqual(len(self.tasks), 18)
        self.assertTrue(all(isinstance(t["tools"], list) for t in self.tasks))


if __name__ == "__main__":
    unittest.main()
