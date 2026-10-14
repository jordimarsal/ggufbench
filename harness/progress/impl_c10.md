# Implementation log — c10 (MILLORA §C10: the baseline is a condition; the signal must fire on it)

> Dispatched directly by the leader (not a `feature_list.json` feature). Spec =
> `docs/MILLORA.md` §C10 proposal (items 1–3; item 4 belongs to the fleet re-measure).

## Batch c10-batch-1 — 2026-10-14 · done

- `config.baseline_argv()` = `SERVER_FLAGS + CACHE_FLAGS` (new helper, right after the
  constants it composes).
- `report`: `baseline_flags()`, `baseline_id()` (sha1[:8]; `?` for rows that predate the
  field — a baseline is never invented), `_engine_label()` (engine + build as ONE value:
  the pair is the condition), `CONDITION_AXES` (task set · engine · baseline, fixed order),
  `condition_axes()`, `mixed_axes()`; `save_result` records `baseline_flags` per row;
  `_render_task_sets` → `_render_conditions`: the CLI footer lists EVERY mixed axis.
- `html_report`: `_rows`/`_pack` carry `base`; header chips `task sets` (links, unchanged)
  + `engines …` / `baselines …` when those axes mix; the banner names each mixed axis;
  each row's `<pre>` shows `baseline <id>` (or `baseline ? (not recorded)`) next to the
  per-model flags; compare clauses factored into `_cmp_axis_clauses`, mirrored by
  `_PICKER_JS.axisClauses` (guard test keeps them in sync).
- Docs: `docs/SPEC.md` §2 — new **Baseline (`baseline_flags`)** bullet naming the three
  condition axes; `docs/MILLORA.md` §C10 closed with the evidence note.

### Traceability (C10 proposal → test)

| proposal | tests |
|---|---|
| 1. record the baseline in the row | `TestBaselineArgv` (3, test_config); `test_baseline_flags_is_the_common_baseline`, `test_baseline_id_is_stable_and_unknown_when_unrecorded`, `test_save_result_records_the_baseline` (test_report); `test_conditions_per_model_state_the_baseline_id`, `test_picker_pack_carries_the_baseline_id` (test_html_report) |
| 2. the three surfaces fire on it | CLI: `test_scoreboard_notes_a_baseline_only_mix`, `test_scoreboard_lists_every_mixed_axis`; HTML: `test_banner_and_chip_when_only_the_baseline_differs`; compare: `test_mixed_conditions_when_only_the_baseline_differs`, `test_picker_js_mirrors_the_axis_clauses` |
| 3. fold engine/build into the same signal | `test_mixed_axes_names_the_engine_build`, `test_chip_and_banner_name_the_engine_builds_when_only_the_build_differs`, `test_mixed_conditions_when_only_the_engine_build_differs` |
| axis machinery itself | `test_condition_axes_counts_every_axis_in_a_fixed_order`, `test_mixed_axes_is_empty_for_a_homogeneous_pool`, `test_mixed_axes_names_only_the_axis_that_differs`, `test_mixed_axes_names_the_task_set` |

20 new tests (416 vs 396 before the change). Existing §C9 assertions untouched.

### Gates

`python3 -m unittest discover -s ggufbench/tests -t .` from `/home/jordi/ia/llama` →
**Ran 416 tests — OK (skipped=2)**. Full output: `harness/logs/c10/batch-1.log`.

Not committed (the leader reviews and commits). No GPU/model commands run; `results/`,
`tasks/`, `docs/writeups/` untouched.
