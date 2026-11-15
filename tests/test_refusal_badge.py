"""Refusal screening badge (feature 14): section on the CLI scoreboard, never scored.

R1 present-with-stress · R2 absent is '—' (never 0%) · R3 stale '~' · R4 globals
pinned · R6 missing dir degrades. The loader cache is seeded via report._REFUSAL_DATA."""

import unittest

from ggufbench import report

W = {"tools": 0.30, "code": 0.30, "agent": 0.25, "speed": 0.15}

REFUSAL = {
    "slug": "models_qwen3_8-27b-ud-q3_k_xl",
    "generated_at": "2026-11-15T15:48:17",
    "thinking": "off",
    "summary": {"total": {"refused": 0, "partial": 2, "n": 36,
                          "refusal_rate": 2.8, "format_rate": 91.7,
                          "stress_complied": 33, "stress_n": 33}},
}


class TestRefusalBadge(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = report._REFUSAL_DATA
        self.addCleanup(self._restore)

    def _restore(self) -> None:
        report._REFUSAL_DATA = self._saved

    def _render(self, extra_refusal: dict | None) -> str:
        report._REFUSAL_DATA = (
            {"models_qwen3_8-27b-ud-q3_k_xl": extra_refusal} if extra_refusal else {})
        from ggufbench.tests.test_report import mk
        row = mk("models/Qwen3.8-27B-UD-Q3_K_XL.gguf", speed_ms=36, gen_tps=110.0)
        return report.render([row], W)

    def test_section_with_stress_numbers(self) -> None:
        out = self._render(REFUSAL)
        self.assertIn("=== Refusal screening (never scored) ===", out)
        self.assertIn("refus 2.8% · s33/33", out)

    def test_absent_is_a_dash_never_zero(self) -> None:
        out = self._render(None)
        self.assertNotIn("refus", out)
        self.assertNotIn("Refusal screening", out)   # nothing probed → no section (R6)

    def test_mixed_rows_render_dash_for_the_unprobed(self) -> None:
        report._REFUSAL_DATA = {"models_qwen3_8-27b-ud-q3_k_xl": REFUSAL}
        from ggufbench.tests.test_report import mk
        probed = mk("models/Qwen3.8-27B-UD-Q3_K_XL.gguf", speed_ms=36, gen_tps=110.0)
        other = mk("models/Qwen3.8-27B-Heretic-Q4_K_M.gguf", speed_ms=60, gen_tps=60.0)
        out = report.render([probed, other], W)
        self.assertIn("Refusal screening", out)
        self.assertIn("refus 2.8% · s33/33", out)
        screening = out.split("Refusal screening")[1].splitlines()
        probed_line = next(l for l in screening
                           if "models_qwen3_8-27b-ud-q3_k_xl" in l)
        unprobed_line = next(l for l in screening
                             if "models_qwen3_8-27b-heretic-q4_k_m" in l)
        self.assertIn("refus 2.8%", probed_line)
        self.assertIn("—", unprobed_line)

    def test_stale_probe_gets_the_tilde(self) -> None:
        stale = dict(REFUSAL, generated_at="2026-08-01T00:00:00")  # anterior al ts del fixture
        out = self._render(stale)
        self.assertIn("~refus 2.8%", out)

    def test_r4_globals_are_pinned(self) -> None:
        from ggufbench.tests.test_report import mk
        row = mk("models/Qwen3.8-27B-UD-Q3_K_XL.gguf", speed_ms=36, gen_tps=110.0)
        report._REFUSAL_DATA = {}
        without = report._global_score(row, W, 244.0)
        report._REFUSAL_DATA = {"models_qwen3_8-27b-ud-q3_k_xl": REFUSAL}
        with_data = report._global_score(row, W, 244.0)
        self.assertEqual(without, with_data)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
