# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** _none_ (all 6 `done`; `lora_eval` = feature 7 `spec_ready`,
  waiting on the human Spec Gate)
- **Started:** _—_
- **Agent:** _—_

## Plan

_Next session — the goal is one GPU night, at v5, with everything frozen:_

1. **Finish C4's task fill** (3 multi-file agent projects: bash 2, java 1) so all four
   languages have 3 each (18 agent/lang; the accepted floor today is 9 of 12, asserted).
   Follow the C3/C4 recipe: project that FAILS its own test + reference in /tmp +
   `python3 harness/tools/check-task.py --task <task> --reference <ref>` → `VERDICT: ok`,
   then `python3 -m unittest ggufbench.tests.test_agent_tasks`.
2. **Then the C9 fleet re-measure** (option 1) at v5: 7 GGUF + Strata, OFF × runs 3, one
   frozen tuple (task set 18/72/68 · engine build · KV baseline q8_0 · thinking off). This
   is the run that makes the published board homogeneous and makes the baseline/engine axes
   of §C10 start reporting.
3. **After it:** the 3 write-ups (they still state the C1-era condition) + README tables
   with the new numbers.

## Log

## Next step

_If a new session opens: read AGENTS.md + current.md + feature_list.json._
