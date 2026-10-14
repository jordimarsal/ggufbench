# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** c10 — baseline conditions recorded per row + mixed-conditions
  signal on the engine/baseline axes (MILLORA §C10, dispatched directly; batch 1 done,
  awaiting review). `lora_eval` = feature 7 remains `spec_ready`, waiting on the human
  Spec Gate.
- **Started:** 2026-10-14
- **Agent:** implementer (c10 batch 1)

## Plan

**c10** (MILLORA §C10): tasks = the §C10 proposal items 1–3, implemented as one batch —
see `harness/progress/impl_c10.md`. Review + human approval pending; item 4 (the frozen
tuple) belongs to the C9 fleet re-measure below.

Open items (2026-10-14):

- **C9 option 1:** re-measure the active fleet (7 GGUF + Strata, OFF × runs 3) under the
  current 16/60/60 suite — the pool still mixes three task sets and only then is the
  published board homogeneous (the CLI `--sort version` and the report's "By task set"
  section make the mix visible meanwhile, not comparable).
- **The 3 write-ups:** still state the C1-era condition ("16 tool tasks, 60 code, 42
  multi-step agent tasks") and their "top rows are ties" conclusion leans on qwen36's old
  0.84 (now 0.81); deferred by decision until the fleet re-measure moves the numbers again.
- **C3** (more tasks per cell) and **C4** (multi-file agent) from MILLORA §2.

## Log

- **2026-10-14 · c10 batch 1 done (awaiting review).** Implemented MILLORA §C10 proposals
  1–3: `config.baseline_argv()` recorded per row (`baseline_flags`, `report.save_result`);
  `report.condition_axes`/`mixed_axes` (task set · engine build · baseline) now drive the CLI
  footer note, the HTML chips/banner, the compare banner and the picker JS; per-row `<pre>`
  shows `baseline <id>` (`?` = not recorded, never invented). Docs updated (SPEC §2, MILLORA
  §C10 closed). Gates: 416 tests OK (skipped=2) → `harness/logs/c10/batch-1.log`; details +
  traceability in `harness/progress/impl_c10.md`. Not committed.
- **2026-10-14 · Finding recorded as MILLORA §C10 (open, human decision).** Auditing what
  the board actually compares turned up two more conditions that travel with a row and are
  never checked: the **engine build** (llama 0.4.0-dev ×7 vs 0.6.0-dev+4413a19 ×8 *inside*
  the same 12/60/28 set; Strata 0.1.43.1 vs 0.1.44.1) and the **baseline flags** — ADR-0008
  switched the KV cache `q4_0`→`q8_0` on 2026-10-13 20:16, i.e. after the whole C1 batch
  (last row 13:39) and before the two rows of 14/10, so all 28 older rows carry a KV cache
  nothing in the row records. Proposal in §C10: store a baseline digest per row, make the
  three surfaces (CLI note, HTML banner/chip, compare banner) fire on build+baseline as they
  now do on the task set, then run the fleet re-measure under one frozen tuple. ~½ day, no
  GPU. → **Implemented the same day** (batch 1, entry above) after the human decision.

## Next step

_If a new session opens: read AGENTS.md + current.md + feature_list.json._
