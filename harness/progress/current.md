# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** _none_ (12 features `done`; `lora_eval` = feature 7
  `spec_ready`, waiting on its Spec Gate; `grammar_toolcalls_ab` and
  `kv_cache_f16_ab` = features 10/11 `pending`)
- **Started:** 2026-11-14
- **Agent:** in-session
- **Session log (2026-11-14, heretic/abliterated review):**
  - Benchmark pass over the 2026-11 candidate batch (thinking off, fixed 32k,
    no MTP): SC117 and Huihui confirmed as fleet entries; 6 candidates measured,
    5 files pruned same day (Wave 1) and 2 more in Wave 2 (Heretic, Ornith-APEX,
    + the orphaned external draft) — registered in `harness/retired.json`.
  - `harness/tools/probe-refusal.py`: standalone 36-prompt refusal/format probe
    (deterministic grading, full answers stored); run against the batch + 2
    controls at identical conditions.
  - `bin/mtp-sweep.py` rewritten (no hardcoded models, off/n3/n4/n6/n4-tensor/
    tensor arms): MTP adds nothing on SC117 or Huihui; the Huihui gain is
    `--split-mode tensor`. Profiles written with measured context pins.
  - **Speed metric fix (SPEC §5):** the global normalized latency
    (`min_speed / speed_ms`), so a 13 ms reply with 0 t/s took speed index 1.0
    and the full 0.15 weight — and headline cards crowned it fastest. Now
    normalized by `gen_tps / max_tps`: missing throughput scores 0 and is never
    ranked first (scoreboard, `--sort speed`, picks, KPI strip, latency pane,
    in-page reorder).
