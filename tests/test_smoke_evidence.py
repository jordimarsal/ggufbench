import re
import unittest
from pathlib import Path

# R5 de discriminative_tasks: el fum amb >= 2 models ha de tenir >= 1 tasca expert
# L'evidència viu a harness/specs/ (versionada): harness/logs/ és ignorat per git
# i en un checkout net el test no trobaria el fitxer.
# que separe els models per >= 20 punts. L'evidència viu en un .md versionable
# (els .log els ignora el gitignore global: *.log) generat des del log de la run.
EVIDENCE = (Path(__file__).resolve().parents[1] / "harness" / "specs"
            / "discriminative_tasks" / "smoke-r5.md")

_SYMBOLS = {"✓": 100, "✗": 0}


def _parse(text):
    """Taula `| Tasca expert | <model>... | gap |` -> (models, {tasca: {model: símbol}})."""
    models, rows = [], {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0].startswith("Tasca"):
            models = cells[1:-1]  # sense la columna del gap
            continue
        if models and cells[0].endswith("_expert") and set(cells[1:-1]) <= (
                set(_SYMBOLS) | {"⊘"}):
            rows[cells[0]] = dict(zip(models, cells[1:-1]))
    return models, rows


class TestR5SmokeEvidence(unittest.TestCase):
    """Fum de discriminació R5: >= 2 models, >= 1 tasca expert amb gap >= 20 pts."""

    @classmethod
    def setUpClass(cls):
        if not EVIDENCE.is_file():
            raise AssertionError(f"falta l'evidència R5: {EVIDENCE}")
        cls.models, cls.rows = _parse(EVIDENCE.read_text(encoding="utf-8"))

    def test_evidence_covers_at_least_two_models(self):
        self.assertGreaterEqual(len(self.models), 2, "el fum ha de tenir >= 2 models")
        self.assertTrue(self.rows, "cap fila d'evidència parsejada")

    def test_r5_expert_gap_at_least_20_points(self):
        # símbols binaris (✓=100, ✗=0): un ✓ contra un ✗ = gap de 100 punts (>= 20).
        # Un ⊘ (error de servidor) NO compta com a discriminació: no és capacitat.
        separating = [
            tid for tid, per_model in self.rows.items()
            if set(per_model.values()) >= {"✓", "✗"}
        ]
        self.assertTrue(
            separating,
            "cap tasca expert separe els models amb pass/fail real (≥ 20 punts)",
        )

    def test_evidence_only_expert_tasks(self):
        for tid in self.rows:
            self.assertTrue(tid.endswith("_expert"), tid)


if __name__ == "__main__":
    unittest.main()
