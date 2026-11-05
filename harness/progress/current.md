# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** `context_receipts` (id 9) — **spec_ready, waiting on
  the human Spec Gate**
- **Started:** 2026-11-05
- **Agent:** in-session (hybrid)

## Plan

- Fix the dev environment on this macOS checkout until `harness/init.sh` is green.
- Spec mode for `context_receipts` (lowest `pending` id): requirements/design/tasks.
- Mark `spec_ready` and STOP at the Spec Gate (no implementation before approval).

## Log

- **Env fixes (macOS checkout, committed before any feature work):**
  - `c6fec11` chore(harness): the uncommitted `feature_list.json` edit (the 3 new
    pending features from the human) committed as its own change.
  - `273b6a6` fix(executors): `_sandbox_prefix` skips the GNU `timeout` prefix when
    the binary is missing (macOS) — `_safe_run`'s subprocess clock keeps guarding;
    regression tests added (`test_prefix_skips/keeps_timeout_binary_*`).
  - `31f4044` fix(tests): the nvidia-smi mock in `test_run_cli.py` intercepted
    `subprocess.run` globally; on macOS `platform.platform()` shells out to `file`
    (Mach-O) and choked on the fake. New `_only_nvidia` helper delegates
    non-nvidia-smi calls to the real `subprocess.run`.
  - `e6b7af4` chore(harness): `init.sh` ran `pytest` (not installed; conventions
    forbid it) — now the canonical `python3 -m unittest discover -s tests -t ..`
    (top level at the parent dir so the package imports as `ggufbench`).
  - Gates: **490 tests, 0 errors, 67 skips (platform)**; `harness/init.sh` →
    `[OK] Environment ready`.
- **Spec mode `context_receipts`:** read client/graders/agent/report/html_report
  seams + test patterns; wrote `harness/specs/context_receipts/{requirements,design,tasks}.md`
  (7 R's, 7 tasks, 4 batches; ADR-1 receipts-not-a-condition, ADR-2 pure parser in
  client.py, ADR-3 mean+median rollups). Status → `spec_ready`.

## Next step

**STOP — human Spec Gate.** On approval: batch mode (B1 = T1+T2 client+graders
trace), evidence logs to `harness/logs/context_receipts/batch-<n>.log`. Notes:
`lora_eval` (id 7) still waits on its own Spec Gate; two more pending features
(grammar_toolcalls_ab, kv_cache_f16_ab) queued behind this one.
