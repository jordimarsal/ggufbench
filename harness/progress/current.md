# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** _none_ (all 6 `done`; `lora_eval` = feature 7 `spec_ready`,
  waiting on the human Spec Gate)
- **Started:** _—_
- **Agent:** _—_

## Plan

_Pick the next job. Open items (2026-10-14 close-out, details in the log/history):_

- **C9 option 1:** re-measure the active fleet (7 GGUF + Strata, OFF × runs 3) under the
  current 16/60/60 suite — the pool still mixes three task sets, and only then is the
  published table homogeneous.
- **The 3 write-ups:** still state the C1-era condition ("16 tool tasks, 60 code, 42
  multi-step agent tasks") and their "top rows are ties" conclusion leans on qwen36's old
  0.84 (now 0.81); deferred by decision until the fleet re-measure moves the numbers again.
- **C3** (more tasks per cell) and **C4** (multi-file agent) from MILLORA §2.

## Log

- **2026-10-14 · feat(report) — the test version is visible per row and the board can be
  ordered by it (human order).** CLI: Table 1 gained a `SET` column (`label·task-set`,
  e.g. `v3·16/60/60`) and `--sort global|tools|code|agent|speed|version` — `version` groups
  the table by set (biggest first, global inside each group), which is the honest view while
  the pool is mixed. HTML: the `SET` badge in every ranking row and model card, a static
  **"By task set"** section (one block per set: signature, label, row count, date span, its
  rows ordered by global) linked from the header chip, and a small inline order control that
  reorders the ranking in place (same six keys, values carried in `data-*`); dimension
  titles now take their counts from the data (16/60/60), never the stale hardcoded 32/24/8.
  *Contract change:* the report is no longer zero-JS — it stays self-contained (one inline
  script, no external resource, no network) and reads correctly with JS off, in the
  server-side order. Docs updated (SPEC §4.6, verification checklist, MILLORA §4.6, C9).
  Verified: JS exercised in node against a stub DOM (all six orders + rank renumbering),
  bench render baseline re-recorded (19.2 → 28.3 ms: the page genuinely grew; the machine
  measures this one 19-33 ms across idle runs). +19 tests (394 total).
- **2026-10-14 · README restructured to one table per task set + lineage.** The scoreboard
  now shows the current set (16/60/60: qwen36, strata-swift), the superseded OFF batch
  (12/60/28: the 7 active models) and a note for the ON batch (8/60/24), plus a
  **Task-set lineage** table (v1 base → v2 hard → v3 expert → v4 the C3 counts) and the
  `--sort version` recipe. No table mixes sets. Repaired on the way: the Quickstart had
  lost its header, opening fence and first step (the table ran straight into `# 2.`), and
  the four-dimensions table still said 8 tools / 36 code.

## Next step

_If a new session opens: read AGENTS.md + current.md + feature_list.json._
