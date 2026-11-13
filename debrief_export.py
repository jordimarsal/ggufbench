"""debrief evidence export: one ``results.json`` per run, in the contract the debrief
MCP reads (``artifacts/ggufbench/<run-id>/results.json``).

debrief is read-only by design (its ADR-0001), so the write side lives here, at the
source, where the receipt's fields are freshest. The document schema is debrief's
``GgufbenchStore`` input (its ADR-0002 adapter is the only other place that knows
this format); the shape is pinned by tests here, and the derived fields mirror
report.py's own derivations (``baseline_id``, ``_engine_label``, ``config.slug``)
so a row is comparable across both boards.

A run whose receipt carries no graded dimension (``--dims speed``) exports nothing:
debrief's contract is findings with outcome/score, and inventing a pass for an
unmeasured dimension would fabricate evidence.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

from . import config

# Dimensions graded per task (a trace with pass/fail items). Speed is a measurement,
# not a finding: no outcome, no row.
GRADED_DIMS = ("tools", "code", "agent")
VERSION = "0.1.0"


def _baseline_id(flags: Any) -> str:
    """Short id of the common-flags condition — the exact derivation of
    report.baseline_id (sha1[:8]), kept local because report imports this module
    (save_result exports the receipt) and an import back would cycle."""
    if not isinstance(flags, str) or not flags:
        return "?"
    return hashlib.sha1(flags.encode("utf-8")).hexdigest()[:8]


def _score(info: dict[str, Any]) -> float:
    """The dimension score as a finite float (debrief refuses non-finite measures)."""
    try:
        score = float(info.get("score") or 0.0)
    except (TypeError, ValueError, OverflowError):
        return 0.0
    return score if math.isfinite(score) else 0.0


def debrief_document(result: dict[str, Any], receipt_name: str) -> dict[str, Any] | None:
    """Map one run receipt to debrief's document: None when there is nothing to say.

    One row per graded dimension that ran tasks: outcome from the trace (every
    item passed and the dimension passed), ``graded`` = the pass/total counts the
    debrief signature carries, ``artifact`` pointing back at the raw receipt.
    """
    rows: list[dict[str, Any]] = []
    model = config.slug(str(result.get("model", "unknown")))
    for dim in GRADED_DIMS:
        info = result.get(dim)
        trace = info.get("trace") if isinstance(info, dict) else None
        if not isinstance(trace, list) or not trace:
            continue
        passed = sum(1 for item in trace if item.get("passed"))
        score = _score(info) if isinstance(info, dict) else 0.0
        all_passed = bool(isinstance(info, dict) and info.get("passed"))
        outcome = "pass" if passed == len(trace) and all_passed else "fail"
        rows.append(
            {
                "model": model,
                "task": dim,
                "outcome": outcome,
                "reason": f"{dim} {passed}/{len(trace)} tasks passed (score {score:.2f})",
                "score": score,
                "graded": {"passed": passed, "total": len(trace)},
                "artifact": f"results/runs/{receipt_name}",
            }
        )
    if not rows:
        return None
    engine = result.get("engine") or "llama"
    build = result.get("server_build") or "?"
    return {
        "ggufbench": VERSION,
        # Engine and build are ONE condition (a build change makes two rows
        # incomparable — same idea as report._engine_label), but debrief validates
        # this field as a single whitespace-free token, so the joiner is '-'.
        "engine_build": f"{engine}-{build}",
        "baseline": _baseline_id(result.get("baseline_flags")),
        "rows": rows,
    }


def export(
    result: dict[str, Any],
    receipt_name: str,
    artifacts_dir: Path | None = None,
) -> Path | None:
    """Write the debrief contract for one receipt; None when there is no finding."""
    root = Path(artifacts_dir) if artifacts_dir else config.DEBRIEF_DIR
    document = debrief_document(result, receipt_name)
    if document is None:
        return None
    out_dir = root / Path(receipt_name).stem
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "results.json"
    out.write_text(json.dumps(document, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def main() -> int:
    """Backfill: export every receipt already under results/runs (skip sidecars).

    Lets a clone that just pulled the repo regenerate its evidence tree without
    re-running any benchmark.
    """
    written = 0
    for receipt in sorted(config.RESULTS_RUNS.glob("*.json")):
        if "-agent-convos" in receipt.name:
            continue
        try:
            result = json.loads(receipt.read_text(encoding="utf-8"))
        except (OSError, ValueError) as err:
            print(f"✗ {receipt.name}: {err}", file=sys.stderr, flush=True)
            continue
        if not isinstance(result, dict):
            continue
        out = export(result, receipt.name)
        if out is None:
            continue
        written += 1
        print(f"-> {out.relative_to(config.BENCH_DIR)}")
    print(f"{written} artifact(s) under {config.DEBRIEF_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
