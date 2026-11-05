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
- **Spec mode `context_receipts`:** spec written and APPROVED by the human
  (2026-11-05) → `in_progress`.
- **Batch B1 (T1+T2, `5e65413`):** `client.parse_usage` + `in_tokens` in the
  tools/code/speed trace entries (omitted on transport errors). Gates: 500 tests
  (`harness/logs/context_receipts/batch-1.log`).
- **Batch B2 (T3+T4, `e3e0037`):** agent per-turn `turn_in_tokens` +
  `session_in_tokens`; mean/median rollups per dim over all calls across runs.
  Gates: 506 tests (`batch-2.log`).
- **Batch B3 (T5+T6, `95001ec`):** `report.receipts()` + CLI `Context receipts`
  table + HTML section ('?' with the `miss` class). Gates: 511 tests
  (`batch-3.log`).
- **Batch B4 (T7):** SPEC §4.2/§4.4 + new §4.7; ADR-0011
  (`harness/decisions/0011-context-receipts-not-a-condition.md`); traceability
  **7/7 PASS** (`harness/specs/context_receipts/review.md`); review
  APPROVED (`harness/progress/review_context_receipts.md`). Gates: **512 tests,
  0 errors, 68 skips** (`batch-4.log`).
- Nota `--all`: 2 gaps preexistents d'identificadors morts amb la passada v5
  (`discriminative_tasks` R4, `hard_code_tier` R6/R7) — aliens a aquesta feature,
  documentats a la review per a higiene de portafoli.
- mypy: no instal·lat en aquest checkout (CI el cobreix); les funcions públiques
  noves porten anotacions (convencions §Type hints).

## Next step

**STOP — human Completion Gate** for `context_receipts` (evidence: 4 batch logs,
review APPROVED, traceability 7/7). On explicit human approval: create
`harness/specs/context_receipts/APPROVAL`, set `done` in `feature_list.json`,
move the summary to `history.md`. Then the queue: `lora_eval` (spec_ready,
waiting its Spec Gate), `grammar_toolcalls_ab`, `kv_cache_f16_ab` (pending).
