import json
import math
import tempfile
import unittest
from pathlib import Path

from ggufbench import config, debrief_export


def mk_result(**overrides):
    """A minimal receipt: tools 1/1, code 1/2 (dimension fails), no agent trace."""
    r = {
        "model": "ia/models/Qwen3.5-4B-UD-Q4_K_XL.gguf",
        "engine": "llama",
        "server_build": "0.9.0+cd959ba",
        "baseline_flags": "-ngl 999 --flash-attn auto",
        "tools": {
            "passed": True,
            "score": 1.0,
            "trace": [{"id": "archive_not_delete", "passed": True}],
        },
        "code": {
            "passed": False,
            "score": 0.5,
            "trace": [{"id": "hello", "passed": True}, {"id": "fizz", "passed": False}],
        },
    }
    r.update(overrides)
    return r


class TestDebriefDocument(unittest.TestCase):
    def test_one_row_per_graded_dimension_with_trace(self):
        doc = debrief_export.debrief_document(mk_result(), "20261113-120000-m-off.json")
        self.assertIsNotNone(doc)
        self.assertEqual([row["task"] for row in doc["rows"]], ["tools", "code"])
        self.assertEqual(doc["engine_build"], "llama-0.9.0+cd959ba")
        self.assertEqual(doc["ggufbench"], debrief_export.VERSION)

    def test_outcome_pass_only_when_every_trace_item_passed(self):
        doc = debrief_export.debrief_document(mk_result(), "r.json")
        tools, code = doc["rows"]
        self.assertEqual(tools["outcome"], "pass")
        self.assertEqual(tools["graded"], {"passed": 1, "total": 1})
        self.assertEqual(code["outcome"], "fail")
        self.assertEqual(code["graded"], {"passed": 1, "total": 2})

    def test_baseline_id_is_sha1_of_flags_like_the_board(self):
        import hashlib

        doc = debrief_export.debrief_document(mk_result(), "r.json")
        expected = hashlib.sha1(b"-ngl 999 --flash-attn auto").hexdigest()[:8]
        self.assertEqual(doc["baseline"], expected)

    def test_missing_baseline_flags_degrade_to_unknown_not_invented(self):
        doc = debrief_export.debrief_document(mk_result(baseline_flags=None), "r.json")
        self.assertEqual(doc["baseline"], "?")

    def test_model_is_the_slug_token(self):
        doc = debrief_export.debrief_document(mk_result(), "r.json")
        self.assertEqual(doc["rows"][0]["model"], config.slug(mk_result()["model"]))

    def test_speed_only_receipt_exports_nothing(self):
        # no trace in any graded dimension: there is no finding to report
        empty = {"passed": True, "score": 1.0, "trace": []}
        doc = debrief_export.debrief_document(
            mk_result(tools=empty, code=empty, agent=empty), "r.json"
        )
        self.assertIsNone(doc)

    def test_nonfinite_score_clamps_to_zero(self):
        doc = debrief_export.debrief_document(
            mk_result(tools={"passed": True, "score": math.inf,
                             "trace": [{"passed": True}]}),
            "r.json",
        )
        self.assertEqual(doc["rows"][0]["score"], 0.0)

    def test_artifact_points_at_the_raw_receipt(self):
        doc = debrief_export.debrief_document(mk_result(), "20261113-120000-m-off.json")
        self.assertEqual(doc["rows"][0]["artifact"], "results/runs/20261113-120000-m-off.json")


class TestExport(unittest.TestCase):
    def test_export_writes_one_results_json_per_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = debrief_export.export(mk_result(), "20261113-120000-m-off.json",
                                        artifacts_dir=Path(tmp))
            self.assertIsNotNone(out)
            doc = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(len(doc["rows"]), 2)
            self.assertEqual(out.parent.name, "20261113-120000-m-off")

    def test_export_skips_runs_without_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = {"passed": True, "score": 1.0, "trace": []}
            out = debrief_export.export(
                mk_result(tools=empty, code=empty, agent=empty),
                "r.json", artifacts_dir=Path(tmp))
            self.assertIsNone(out)


if __name__ == "__main__":
    unittest.main()
