# Design: refusal_badge

## Files to modify

| File | Change |
|---|---|
| `report.py` | `receipts()`-style: new `refusal_cell(r)` reading `results/refusal/<slug>.json` (cached per render); returns `(text, title, stale)` — `—` when absent. `_scores()`, `_global_score()`, `_score_parts()` UNTOUCHED (R4 is a pin, not a wish). |
| `html_report.py` | the row: new `<span class="badge refusal">` next to the think badge; `title` attribute with the per-category line; staleness `~`. `_is_retired`-like loader `_refusal_data(slug)` with per-render cache. |
| `harness/tools/probe-refusal.py` | `--save` flag → writes canonical `results/refusal/<slug>.json` (the full JSON it already writes, plus `slug` + `generated_at`). `--json` untouched. |
| `tests/test_report.py` | cell text tests: present, absent (`—`), stale `~`, R4 pin (globals identical with/without data). |
| `tests/test_html_report.py` | badge rendering, title content, no-badge case, missing-dir degrade (R6). |
| `README.md` | Scoreboard paragraph: the badge is screening, never a weight; how to produce data (`--stress --save`). |

## Canonical result shape (v1)

```json
{
  "slug": "qwen3_8-27b-ud-q3_k_xl",
  "generated_at": "2026-11-14T22:41:02",
  "thinking": "off",
  "summary": {
    "total": {"refused": 0, "partial": 2, "n": 36, "refusal_rate": 2.8, "format_rate": 91.7},
    "stress_complied": 1, "stress_n": 33,
    "canaries": {"complied": 0, "partial": 2, "refused": 1, "n": 3}
  }
}
```

The probe's `--save` derives `slug` with `config.slug(model)` (or the `--models` label
for external mode), so llama.cpp rows and Strata configs match the same keying the
scoreboard already uses.

## Decisions

- **Badge text**: `refus 0.0% · stress 33/33` (stress shown only when present). The
  weighted refusal_rate comes from the probe's own summary — the scoreboard does not
  re-derive grading from answers (deterministic classifier stays in one place).
- **Staleness** (R3): compare `generated_at` against the row's `ts`; older by any
  amount → `~` prefix. No cutoff heuristic: the human reads the date in the tooltip.
- **`refusal_rate` rounding stays the probe's** (1 decimal): two sources of rounding
  truth would drift apart.
- **The CLI board** prints the same cell text after `SET` (width +14, per `_CELLS`
  convention where a ± only widens by its own).
- **`results/refusal/` joins `.gitignore` alongside `results/runs/`** — probe artifacts
  are receipts, not tracked data; the badge reads the local tree and the published page
  simply reflects whatever the rig measured when it was rendered.

## T1-T3 (test-first)

- [ ] T1: probe `--save` canonical write (slug derivation, dir creation, existing-file
      overwrite) — probe-side.
      refs: R7
- [ ] T2: scoreboard cell — present/absent/stale/missing-dir, CLI width, R4 pin.
      refs: R1, R2, R3, R4, R6
- [ ] T3: HTML badge + title + README/docs.
      refs: R1, R2, R5, R6
