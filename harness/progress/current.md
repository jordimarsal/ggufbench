# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** _none_ (all 6 `done`; `lora_eval` = feature 7 `spec_ready`,
  waiting on the human Spec Gate)
- **Started:** _—_
- **Agent:** _—_

## Plan

_The task set is frozen at v5 (tools 18 · code 72 · agent 72). What is left is the night of
GPU, not the dataset:_

1. **C9 option 1 — the fleet re-measure at v5.** 7 GGUF + Strata, thinking OFF, `--runs 3`,
   one sitting, one frozen tuple: task set 18/72/72 · engine build · KV baseline `q8_0` ·
   OFF. Never llama-server and Strata at the same time (the harness owns the lifecycle).
   Expected: run time grows (the suite is bigger), so plan the whole night; then
   `python3 -m ggufbench.run --scoreboard --html` and `harness/tools/publish-report.sh`.
   The board afterwards should show ONE task set, ONE baseline id (`f982b06a`) and the new
   engine/build axis; §C10's baseline axis starts reporting from the first new row.
2. **Then the three write-ups** (`docs/writeups/*.md`, 3 languages): they still describe the
   C1-era condition (12/60/28, "42 multi-step agent tasks") and their "top rows are ties"
   conclusion leans on numbers the re-measure will replace.
3. **Then the README scoreboard tables** with the measured v5 rows (the current tables mark
   v5 as "no rows measured yet").

## Log

## Next step

_If a new session opens: read AGENTS.md + current.md + feature_list.json._
