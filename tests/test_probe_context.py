"""Unit tests for harness/tools/probe-context.py: the bisection's answers, with probe() stubbed.

No servers, no fleet GGUFs: what is under test here is the SEARCH — which contexts get asked
for, and what the tool reports for each shape of answer — not llama.cpp. The loud half (a real
load, VRAM, the mmproj) is measured on the cards and lives in the receipts.
"""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[1] / "harness" / "tools" / "probe-context.py"
_spec = importlib.util.spec_from_file_location("probe_context", _MODULE_PATH)
pc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pc)


class ProbeBisectionTest(unittest.TestCase):
    """main() with a scripted probe(): the calls it makes, and the number it reports."""

    def _run(self, script, floor, ceiling):
        """script(ctx) -> 'ok' | 'tight' | 'fail'; returns (calls, row)."""
        calls = []

        def _probe(model, ctx, port, kv, log_dir, timeout, margin_mib=0):
            calls.append(ctx)
            return script(ctx), [], Path("unused.log")

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "probe.json"
            old, pc.probe = pc.probe, _probe
            try:
                pc.main(["--models", "models/fake.gguf", "--floor", str(floor),
                         "--ceiling", str(ceiling), "--json", str(out)])
            finally:
                pc.probe = old
            rows = json.loads(out.read_text()) if out.exists() else {}
        return calls, rows.get("fake", {})

    def test_ceiling_ok_stops_there(self):
        calls, row = self._run(lambda ctx: "ok", 32768, 233472)
        self.assertEqual(calls, [233472])
        self.assertEqual(row["max_ctx"], 233472)

    def test_bisection_walks_down_then_up(self):
        # ceiling no, mids yes: the best verified value is the last mid that loaded.
        calls, row = self._run(lambda ctx: "fail" if ctx == 233472 else "ok", 200704, 233472)
        self.assertEqual(calls, [233472, 217088, 225280])
        self.assertEqual(row["max_ctx"], 225280)

    def test_at_grid_width_verifies_the_floor(self):
        # 2026-10-16: a window no wider than the 8k grid used to answer "none" without ever
        # touching the declared floor. The floor is now checked, and reported if it loads.
        calls, row = self._run(lambda ctx: "fail" if ctx == 233472 else "ok", 225280, 233472)
        self.assertEqual(calls, [233472, 225280])
        self.assertEqual(row["max_ctx"], 225280)

    def test_tight_is_not_usable(self):
        # "tight" = it loaded, but with less than --margin-mib free: a real run dies later.
        calls, row = self._run(lambda ctx: "tight" if ctx == 233472 else "ok", 225280, 233472)
        self.assertEqual(row["max_ctx"], 225280)

    def test_nothing_loads_reports_none(self):
        calls, row = self._run(lambda ctx: "fail", 225280, 233472)
        self.assertEqual(calls, [233472, 225280])
        self.assertIsNone(row["max_ctx"])


if __name__ == "__main__":
    unittest.main()
