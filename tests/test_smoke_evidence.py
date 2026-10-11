import re
import unittest
from pathlib import Path

# R5 of discriminative_tasks: the smoke with >= 2 models must have >= 1 expert task
# Evidence lives in harness/specs/ (versioned): harness/logs/ is git-ignored
# and in a clean checkout the test would not find the file.
# that separates the models by >= 20 points. Evidence lives in a versionable .md
# (the .log files are ignored by the global gitignore: *.log) generated from the run log.
EVIDENCE = (Path(__file__).resolve().parents[1] / "harness" / "specs"
            / "discriminative_tasks" / "smoke-r5.md")

_SYMBOLS = {"✓": 100, "✗": 0}


def _parse(text):
    """Table `| Expert task | <model>... | gap |` -> (models, {task: {model: symbol}}).

    The first header cell is matched by prefix ("Expert task" in the current .md,
    "Tasca expert" in older versions of the evidence).
    """
    models, rows = [], {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0].startswith(("Expert task", "Tasca")):
            models = cells[1:-1]  # without the gap column
            continue
        if models and cells[0].endswith("_expert") and set(cells[1:-1]) <= (
                set(_SYMBOLS) | {"⊘"}):
            rows[cells[0]] = dict(zip(models, cells[1:-1]))
    return models, rows


class TestR5SmokeEvidence(unittest.TestCase):
    """R5 discrimination smoke: >= 2 models, >= 1 expert task with gap >= 20 pts."""

    @classmethod
    def setUpClass(cls):
        if not EVIDENCE.is_file():
            raise AssertionError(f"missing R5 evidence: {EVIDENCE}")
        cls.models, cls.rows = _parse(EVIDENCE.read_text(encoding="utf-8"))

    def test_evidence_covers_at_least_two_models(self):
        self.assertGreaterEqual(len(self.models), 2, "the smoke must have >= 2 models")
        self.assertTrue(self.rows, "no evidence rows parsed")

    def test_r5_expert_gap_at_least_20_points(self):
        # binary symbols (✓=100, ✗=0): a ✓ against a ✗ = 100-point gap (>= 20).
        # A ⊘ (server error) does NOT count as discrimination: it is not capability.
        separating = [
            tid for tid, per_model in self.rows.items()
            if set(per_model.values()) >= {"✓", "✗"}
        ]
        self.assertTrue(
            separating,
            "no expert task separates the models with real pass/fail (≥ 20 points)",
        )

    def test_evidence_only_expert_tasks(self):
        for tid in self.rows:
            self.assertTrue(tid.endswith("_expert"), tid)


if __name__ == "__main__":
    unittest.main()
