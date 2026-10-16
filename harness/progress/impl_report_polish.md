# Implementer log: report_polish

feature: report_polish

Spec: `harness/specs/report_polish/` (approved at the Spec Gate, 2026-10-16).
Feature 8, status `in_progress`. Batches: T1-T2 · T3-T4 · T5.

- 2026-10-16 · batch T1-T2 landed. `render()` splits rows into live/retired; two panes with
  pure-CSS radio tabs (Board default, no tabs without retired rows); retired pane note,
  old gray legend chip removed; `_kpis(live)` + `_rec_section(live)` right under the strip;
  sections extracted to `_sections(rows, sort, *, board, optimal)`; `_by_set_section(anchors=)`
  keeps set ids board-only; `_dim_bars` flipped to best→worst (code written here, its tests
  land in T4/batch 2). `TestRetiredGray` + `test_every_model_row_shows_think_mode` updated;
  new `TestReportTabs` (9 tests). Evidence: `harness/logs/report_polish/batch-1.log` —
  481 passed, 1 skipped, 11 subtests.
- 2026-10-16 · batch T3-T4 landed. Models chip `N models (+M retired)`; task-sets chip links
  only to board blocks (retired-only signature as text). New `TestReportChips` (3) and
  `TestReportOrdering` (3: best-first live, best-first retired, missing last). Evidence:
  `harness/logs/report_polish/batch-2.log` — 487 passed, 1 skipped, 11 subtests.
- Deviation noted: T4's code flip travelled with T1's extraction (one rewrite of `_dim_bars`
  beat two); T4's tests + evidence are in batch 2, and tasks.md points each task at the log
  that actually carried it.

## Traceability

| Requirement | Test(s) | Implementation file(s) | Status |
|-------------|---------|------------------------|--------|
| R1 | test_two_panes_when_retired_rows_exist test_pure_css_switching | html_report.py | done |
| R2 | test_board_is_the_default_tab | html_report.py | done |
| R3 | test_no_tabs_without_retired_rows test_non_retired_unchanged | html_report.py | done |
| R4 | test_retired_pane_has_no_kpis_nor_recommendations test_retired_excluded_from_recommendations | html_report.py | done |
| R5 | test_kpis_ignore_retired_rows | html_report.py | done |
| R6 | test_recommendations_below_the_kpis test_every_model_row_shows_think_mode | html_report.py | done |
| R7 | test_live_lists_best_first test_retired_lists_best_first_too test_missing_measurement_lands_last | html_report.py | done |
| R8 | test_two_panes_when_retired_rows_exist test_retired_row_lives_in_the_retired_tab | html_report.py | done |
| R9 | test_retired_row_lives_in_the_retired_tab test_two_panes_when_retired_rows_exist | html_report.py | done |
| R10 | test_models_chip_counts_live_and_retired test_models_chip_stays_a_single_total_without_retired | html_report.py | done |
| R11 | test_taskset_chip_links_board_blocks_only test_set_anchors_live_only_in_the_board | html_report.py | done |
| R12 | test_pure_css_switching test_self_contained_no_external_resources | html_report.py | done |

