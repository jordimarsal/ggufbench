# Review — feature 5 (discriminative_tasks)

**Verdict:** APPROVED (pending the human Completion Gate)

Reviewer: same agent in review mode (hybrid). Commands re-run, not chat claims:
`check-traceability.py --feature discriminative_tasks` → 7/7 PASS;
`--all` → PASS (after remapping 3 obsolete IDs, see §4);
`harness/init.sh` → green (`batch-7.log`).

## Requirement traceability ↔ tests

- R1: [x] `test_level_hard_by_id_suffix` (`_expert` suffix → expert level),
  `test_level_filter` (filter `level="expert"` includes the 12 real ones, no easy sneaks in),
  `test_level_passes_through_with_code` / `test_level_dropped_without_code` /
  `test_none_level_is_passthrough` / `test_expert_is_a_valid_level` (`--level` only
  affects code; `expert` parses, `bogus` dies), `test_non_code_dims_get_no_level`.
- R2: [x] `test_code_tasks_carry_extra_files` (key `extra_files: dict` on every code
  task; `readings_etl_expert` carries `readings.csv`; `bubble_sort` carries `{}`),
  `test_invalid_extra_files_rejected` (subpaths, absolutes, `..`, `solution*`, `test*`,
  empty), `test_valid_extra_files_accepted`, `test_extra_files_passthrough_from_module`,
  `test_python_sees_fixture` / `test_bash_sees_fixture` /
  `test_java_helper_class_compiled` / `test_typescript_imports_extra_module` (all 4
  runners write the extras FIRST and runner files win on collision:
  `test_runner_files_win_on_collision`), `test_missing_extra_file_fails`,
  `test_data_tasks_carry_their_fixture` (the 4 data tasks carry the fixture the
  TEST_CODE reads).
- R3: [x] Structure: `test_at_least_three_expert_tasks_per_lang` (≥3 × 4 languages),
  `test_ids_end_with_expert_and_level_is_expert`, `test_each_is_specified_and_judged`,
  `test_debug_tasks_embed_the_buggy_context` (the 4 debug ones embed the buggy code
  in the PROMPT). Content (multi-part + TEST_CODE toppling partials): evidence
  `harness/logs/discriminative_tasks/author-validation.log` — 12/12 ref PASS, 12/12
  partial FAIL exactly at the third behaviour (+ 4 buggy failing at the first
  error). Solutions live in `/tmp/opencode/expert/` and are not committed.
- R4: [x] `test_by_level_folded_score_and_breakdown` (folded score with same weight per
  task + per-level breakdown), `test_by_level_defaults_to_easy_without_key`,
  `test_code_by_level_shown_when_present` / `test_no_by_level_section_when_absent`
  (report), `test_v3_marks_expert_tier` (`TASKS_VERSION == "v3"`).
- R5: [x] `test_evidence_covers_at_least_two_models`,
  `test_r5_expert_gap_at_least_20_points`, `test_evidence_only_expert_tasks` over
  `harness/specs/discriminative_tasks/smoke-r5.md` (generated from `smoke-r5.log` with
  `/tmp/opencode/extract_r5.py`): 2 models, 2 tasks separate ✓/✗
  (`log_filter_debug_expert`, `proc_registry_expert`), gap 100 ≥ 20. The 2
  separations are real pass/fail (none depends on exclusions). Pool restored to
  `pool.pre-remeasure.jsonl` after the smoke (homogeneous v1, verified with `diff`).
- R6: [x] `test_weights_sum_to_one`, `test_weights_unchanged` (weights intact),
  `test_non_expert_tasks_untouched` (`bubble_sort`/`fibonacci` easy intact). No
  changes to other dimensions or the folding (score still `sum/len` over scored).
- R7 (retired): [x] `test_r7_retired_no_efficiency_dimension` (weights are exactly
  the 4 dimensions; efficiency remains metric `out_tokens`, not a dimension).

## Task completion

- T1–T8: [x] (batches 1–6, all green). T9: [x] (R5 smoke + `smoke-r5.md`). T10: [x]
  (docs + traceability + `batch-7.log` green + this review).

## Checkpoints

- C1: [x] AGENTS.md + init.sh + feature_list.json + current.md present; docs
  architecture/conventions/verification present; init.sh exit 0.
- C2: [x] Single `in_progress` feature (feature 5; remeasure_pool `blocked`);
  `done` features with green tests (`--all` PASS); current.md describes the active session.
- C3: [x] Flat package (no `src/`); no debug prints or context-free TODOs in
  committed files (grep over changed `.py`: only asserts and TEST_CODE with `echo`,
  which is test code by design).
- C4: [x] Every new behaviour has a test (loader, CLI, executors, graders, config,
  structural, R5, R7); suite green.
- C5: [ ] open — session closure pending the Gate (history.md, cleanup).
- C6: [x] 3-file spec + EARS ("shall" in R1–R6); all tasks [x]; every R<n>
  covered by a concrete test (bodies read, not just names).
- C7: [x] `audit_level: basic` — checklist from `docs/verification.md` confirmed:
  (1) no secrets in new files (CSV/log fixtures, code, docs); (2) no new `subprocess`
  (runners go through `_safe_run` with timeout, unchanged); (3) model code only runs
  in the `executors.py` sandbox (EXTRA_FILES written to the same tempdir under the
  same limits; java compiles all `.java` inside the sandbox); (4) no `eval`/`exec` on
  model output (textual extraction, untouched); (5) HTML escapes (`_esc`,
  self-containment tests intact; `html_report.py` untouched); (6) servers on
  127.0.0.1 (untouched); (7) no new `curl|sh`.

## Observations (non-blocking; for the human Gate)

1. **D6 (new, in MILLORA.md):** `--dims` without `speed` degrades `code_timeout` to
   fixed 90 s → the smoke's first attempt excluded 4/4 tasks by clock timeout
   (`smoke-r5-attempt1.log`). The full re-measure does not fall into it (`speed` runs
   first). Proposal recorded (fallback from `token_budget`/pool), not implemented here.
2. **Token ceiling in the smoke:** the 27B exhausted `out_tokens=16384` with empty text on
   7/12 tasks (hypothesis: `<think>` from the Qwen3 template into `reasoning_content`, outside
   `content`; the client is a faithful pass-through). The harness excludes it (does not count
   it), which is the designed honesty — but it flatters the folded score (1.00 over 5
   scorable). Observation for the re-measure, not a defect of this feature (R6
   forbids touching the fold).
3. **ID remaps in `done` features (§4):** my commit `c982cb9` had renamed 2
   tests (`test_easy_and_hard_are_disjoint_and_complete` →
   `test_levels_are_disjoint_and_complete`, verifying a superset;
   `test_v2_marks_hard_tier` → `test_v3_marks_expert_tier`, same mechanism with v3⊃v2)
   and broke `hard_code_tier` traceability; plus one obsolete ID from feature 4
   (`test_ladder_uses_scaled_timeouts` → `test_scaled_timeout_applied_to_the_single_attempt`,
   which verifies the surviving intent). Remapped IDs only in `impl_*.md` (zero
   code): `--all` PASS again. The `requirements.md` of `timeout_scaling` R2 still
   cites the old ladder (2048/4096/8192) — documented staleness, out of scope.
4. **Eviction of `smoke-r5.md`:** first in `harness/logs/` (git-ignored) and moved to
   `harness/specs/discriminative_tasks/` because the R5 test needs it in a clean
   checkout. The full `.log` stays unversioned (gitignore `*.log`).

## Verdict

**APPROVED** — I request the human Completion Gate for `discriminative_tasks`. After the
Gate: `remeasure_pool` → `in_progress` and full re-measure (10 llama + Strata).
