# Review — feature 6 (thinking_batches)

**Verdict:** APPROVED (pending the human Completion Gate)

Reviewer: same agent in review mode (hybrid). Commands re-run:
`check-traceability.py --feature thinking_batches` → 7/7 PASS; `--all` → PASS;
`harness/init.sh` → green (`batch-4.log`: 187 passed, 1 skipped).

## Requirement traceability ↔ tests

- R1: [x] `test_default_is_off`, `test_off_disables_for_both_engines`,
  `test_on_is_empty`, `test_rejects_bogus` (body per mode and engine + validation),
  `test_thinking_defaults_off` / `test_thinking_on_off_passthrough` /
  `test_thinking_bogus_rejected` (pure CLI via `_parse_args`, no GPU),
  `test_thinking_recorded_and_validated` (ServerManager records),
  `test_extra_merges_into_body` (the kwarg reaches the sent body).
- R2: [x] `test_upsert_keeps_both_thinking_modes` (coexist; re-run replaces),
  `test_legacy_row_without_thinking_coexists_with_off` (`(slug,None)`≠`(slug,off)`),
  `test_runs_filenames_distinguish_mode` (`-on`/`-off`),
  `test_forget_removes_both_modes`,
  `test_render_tolerates_rows_without_thinking`,
  `test_keys_differ_by_thinking` (independent budgets per mode).
- R3: [x] `test_formula_floors_ceils_and_falls_back` (BODY: ceiling 1000),
  `test_scaled_timeout_applied_to_the_single_attempt` (BODY: `[1000]` with ladder 32768;
  NAME intact), `test_single_generous_budget_resolves_long_output` /
  `test_stored_budget_still_honoured` / `test_no_save_when_default_suffices` (single
  ladder), `test_old_schema_ignored` / `test_put_writes_schema` (16384 era invalidated).
- R4: [x] `test_table1_labels_think_and_excluded` (per-row asserts),
  `test_table2_labels_rows_with_mode`, `test_table3_marks_mode`,
  `test_code_by_level_shown_when_present` / `test_no_by_level_section_when_absent`
  (intact), `test_banner_only_with_mixed_dates` (banner unchanged),
  `test_think_badges_and_excluded_line`,
  `test_legacy_row_without_thinking_has_no_badge`.
- R5: [x] `test_table1_labels_think_and_excluded` (`100% (2 excl.)`),
  `test_think_badges_and_excluded_line` + legacy (`excluded code: 0`).
- R6: [x] `test_only_touches_extra_channel` (the dict carries only the kwarg),
  `test_thinking_leaves_protocol_untouched` (dims/langs/levels identical on/off).
- R7: [x] `test_weights_unchanged`, `test_weights_sum_to_one`,
  `test_by_level_folded_score_and_breakdown` (weights and folding intact).

## Task completion

- T1–T6: [x] (batches 1–3, green). T7: [x] (`batch-4.log` green + this review).

## Checkpoints

- C1: [x] base files + docs present; init.sh exit 0 (batch-4).
- C2: [x] single `in_progress` (feature 6); `done` with green tests; current.md active.
- C3: [x] flat package, zero new dependencies; no print/TODO in committed `.py`
  (grep, see batch-4); comments in Catalan, identifiers in English.
- C4: [x] every touched module has tests (config, run, server, report, html_report,
  token_budget, graders, client); suite green.
- C5: [ ] open — closure pending the Gate.
- C6: [x] 3-file spec, strict EARS ("SHALL"); every R<n> with a read test
  (not just a name: bodies verified one by one above).
- C7: [x] `audit_level: basic` — checklist confirmed: (1) no secrets (code + 3
  `.txt` profiles with flags only); (2) no new `subprocess`; (3) model code
  confined to the sandbox (untouched); (4) no `eval`/`exec` (untouched); (5) HTML with
  `_esc` on the mode badge and ints in counts (escape test green);
  (6) 127.0.0.1 (untouched); (7) no new `curl|sh`.

## Observations (non-blocking; for the human Gate)

1. **Profiles outside git:** the 3 `-c 65536` lines live in `models/*.txt` (outside the
   repo). Environment condition documented in the impl + in the `.txt` files
   themselves; the re-measure needs them. If the environment is reinstalled they must
   be re-applied.
2. **The 32768 value is not stamped per row:** it is fixed by era (v3 + this
   feature + git log). Accepted: the pool is re-measured wholesale and
   `token_budgets.json` carries `_schema = 2`.
3. **Cleanup done along the way:** the impl table cited 3 nonexistent IDs (a
   `thinking_body_` infix the tests do not have) — the check itself caught it and the
   table was corrected, not the tests.
4. **GPU cost:** the dual batch (~2×) falls on `remeasure_pool`, not here (no GPU run in
   this feature: all verification is no-GPU by design).

## Verdict

**APPROVED** — I request the human Completion Gate for `thinking_batches`. After the
Gate: `remeasure_pool` → `in_progress` and dual re-measure (off first, on after;
never both engines at once).
