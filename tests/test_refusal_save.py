"""Offline tests for probe-refusal.save_canonical (T1 of the refusal_badge feature).

The probe itself starts servers; the save path is extracted as a pure function so it
is testable without one. The canonical shape (v1: slug, generated_at, thinking,
summary) is what the scoreboard refusal badge reads."""

import importlib.util
import json
import sys
from tempfile import TemporaryDirectory
import unittest
from pathlib import Path

_TOOL = Path(__file__).resolve().parent.parent / "harness" / "tools" / "probe-refusal.py"
_spec = importlib.util.spec_from_file_location("probe_refusal", _TOOL)
probe = importlib.util.module_from_spec(_spec)
sys.modules["probe_refusal"] = probe
_spec.loader.exec_module(probe)


def fake_result(model: str, refused: int = 0) -> dict:
    return {"model": model, "thinking": "off",
            "summary": {"total": {"refused": refused, "partial": 1, "n": 36,
                                  "refusal_rate": round(100 * (refused + 0.5) / 36, 1),
                                  "format_rate": 91.7}},
            "rows": [{"id": "sec-1", "cat": "security", "verdict": "complied",
                      "format_ok": True, "chars": 300}]}


class TestSaveCanonical(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.refus = Path(self._tmp.name) / "refusal"

    def test_two_results_two_files_by_slug(self) -> None:
        written = probe.save_canonical(
            [fake_result("models/Qwen3.8-27B-UD-Q3_K_XL.gguf", refused=0),
             fake_result("models/Qwen3.8-27B-Heretic-Q4_K_M.gguf", refused=1)],
            self.refus)
        self.assertEqual(len(written), 2)
        names = sorted(p.name for p in self.refus.glob("*.json"))
        self.assertEqual(names, ["models_qwen3_8-27b-heretic-q4_k_m.json",
                                 "models_qwen3_8-27b-ud-q3_k_xl.json"])

    def test_v1_shape_has_slug_generated_at_thinking_summary(self) -> None:
        probe.save_canonical([fake_result("models/Qwen3.8-27B-UD-Q3_K_XL.gguf")], self.refus)
        f = self.refus / "models_qwen3_8-27b-ud-q3_k_xl.json"
        d = json.loads(f.read_text())
        self.assertEqual(d["slug"], "models_qwen3_8-27b-ud-q3_k_xl")
        self.assertIn("generated_at", d)
        self.assertEqual(d["thinking"], "off")
        self.assertEqual(d["summary"]["total"]["n"], 36)

    def test_overwrite_latest_wins(self) -> None:
        probe.save_canonical([fake_result("models/Qwen3.8-27B-UD-Q3_K_XL.gguf", refused=0)],
                             self.refus)
        probe.save_canonical([fake_result("models/Qwen3.8-27B-UD-Q3_K_XL.gguf", refused=3)],
                             self.refus)
        d = json.loads((self.refus / "models_qwen3_8-27b-ud-q3_k_xl.json").read_text())
        self.assertEqual(d["summary"]["total"]["refused"], 3)

    def test_missing_dir_is_created(self) -> None:
        nested = self.refus / "deep" / "nested"
        probe.save_canonical([fake_result("models/x.gguf")], nested)
        self.assertTrue((nested / "models_x.json").exists())

    def test_errored_results_are_skipped(self) -> None:
        written = probe.save_canonical(
            [{"model": "models/dead.gguf", "error": "RuntimeError: server died"}],
            self.refus)
        self.assertEqual(written, [])
        self.assertEqual(list(self.refus.glob("*.json")), [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
