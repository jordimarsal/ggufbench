import shutil
import unittest

from ggufbench import agent, config, executors, tasks_loader

LANGS = ("python", "bash", "java", "typescript")
HAS_SANDBOX = executors._probe_sandbox()

# C4: what "a project, not a file" means in numbers — 5+ files and a turn budget a real
# fix needs. Tasks below this size are the original single-file ones and keep MAX_TURNS=8.
MULTI_FILE_MIN = 5
MULTI_FILE_TURNS = 12


def _solution_key(task):
    """The task's entry point as the runner resolves it: 'solution<ext>', case-insensitive
    (java ships Solution.java)."""
    ext = config.Lang.exts()[task["lang"]]
    want = f"solution{ext}".lower()
    return next((k for k in task["initial_files"] if k.lower() == want), None)


class TestAgentTasks(unittest.TestCase):
    """Structure of the agent dimension. The agent is the only dimension whose tasks are
    *programs* (initial files + a test), so a broken task is silent: the port would just read
    "agent 82%" and nobody would know the test could never pass.
    """

    @classmethod
    def setUpClass(cls):
        cls.tasks = tasks_loader.load("agent")

    def test_every_task_is_specified(self):
        for t in self.tasks:
            self.assertTrue(t["id"], t)
            self.assertIn(t["lang"], LANGS, t["id"])
            # A multi-file brief must say enough to work from (C4: the symptom + the entry
            # point); the legacy single-file tasks (e.g. "add_feature", 38 chars) stay as they
            # were, they are not part of this batch.
            floor = 60 if len(t["initial_files"]) >= MULTI_FILE_MIN else 20
            self.assertGreater(len(t["goal"]), floor, t["id"])
            # A task may ship no solution file (a from-scratch task: the model creates it,
            # e.g. log_triage). Its TEST is mandatory — this assertion is what removed
            # `mapped_type_refactor` (types are erased at runtime and bun does not type-check,
            # so the task was unmeasurable and its empty test passed for every model).
            self.assertIn(t["test_file"], t["initial_files"], f"{t['id']}: its test is missing")

    def test_ids_are_unique_per_language(self):
        pairs = [(t["lang"], t["id"]) for t in self.tasks]
        self.assertEqual(len(pairs), len(set(pairs)))

    def test_turn_budget_is_bounded(self):
        for t in self.tasks:
            self.assertGreaterEqual(t["max_turns"], 8, t["id"])
            self.assertLessEqual(t["max_turns"], 20, t["id"])

    def test_the_dataset_grew_with_multifile_projects(self):
        """C4 fill: 3 multi-file tasks per language is the target (the cell goes 15 -> 18).
        Delivered 2026-10-14: python 3, bash 3, java 3, typescript 4 (its extra one replaces
        `mapped_type_refactor`, a legacy task that was unmeasurable and gave every model a
        free pass). Floor, not target: the strict half of this gate is
        `test_multifile_tasks_start_from_a_failing_state` — a multi-file task that does not
        measure anything is rejected however many there are."""
        multi = [t for t in self.tasks if len(t["initial_files"]) >= MULTI_FILE_MIN]
        self.assertGreaterEqual(len(multi), 12, f"{len(multi)} multi-file tasks")
        for lang in LANGS:
            n = sum(1 for t in multi if t["lang"] == lang)
            self.assertGreaterEqual(n, 3, f"{lang}: {n} multi-file tasks")

    def test_multifile_tasks_get_a_real_turn_budget(self):
        """A 6-file project cannot be fixed in 8 turns: the old budget was the reason the
        dimension could not say anything about agentic work (MILLORA §C4)."""
        for t in self.tasks:
            if len(t["initial_files"]) >= MULTI_FILE_MIN:
                self.assertGreaterEqual(t["max_turns"], MULTI_FILE_TURNS, t["id"])

    @unittest.skipUnless(HAS_SANDBOX, "host cannot create isolated namespaces (unshare -Urn)")
    def test_multifile_tasks_start_from_a_failing_state(self):
        """The mechanical half of "the task discriminates": the project as shipped MUST fail
        its own test (the reference fix, which is never committed, is what makes it pass —
        `harness/tools/check-task.py` runs that half by hand). Running the executor for every
        task would add ~1 min to the suite; this covers the multi-file ones, where a
        copy-paste slip is likeliest."""
        for t in self.tasks:
            if len(t["initial_files"]) < MULTI_FILE_MIN:
                continue
            env = agent.MockEnv(t["initial_files"], t["lang"], t["test_file"])
            ok, out = env.run_tests()
            self.assertFalse(ok, f"{t['id']} already passes as shipped:\n{out[-400:]}")


if __name__ == "__main__":
    unittest.main()
