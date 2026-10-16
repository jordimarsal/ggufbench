# Tasks: report_polish

- [x] T1: Split rows into live/retired; two panes (board + retired) behind pure-CSS radio
      tabs when retired rows exist, single board layout otherwise; retired pane note
      ("Record only…"); board pane free of retired rows; `.tabs` CSS block. Tests:
      two-panes, board-checked-by-default, no-tabbar case, board-has-no-retired,
      pure-CSS-switching; update `TestRetiredGray` (row/badge/note assertions).
      (evidence: harness/logs/report_polish/batch-1.log)
      depends_on: (none)
      refs: R1, R2, R3, R8, R9, R12
- [x] T2: KPI strip computed on live rows (`_kpis(live)`) and Recommendations moved right
      below it, before "Weighted global"; retired pane carries neither. Tests:
      kpis-ignore-retired, recommendations-below-the-kpis, retired-pane-has-no-recs-nor-kpis;
      update `test_every_model_row_shows_think_mode` regions.
      (evidence: batch-1.log)
      depends_on: T1
      refs: R4, R5, R6
- [x] T3: Header chips — models count split into live + retired; task-sets chip links only
      to board-pane blocks (retired-only signatures as text); `_by_set_section(anchors=False)`
      for the retired pane (no duplicate ids). Tests: models-chip, tasksets-chip-scoping,
      retired set block without id.
      (evidence: harness/logs/report_polish/batch-2.log)
      depends_on: T1
      refs: R10, R11
- [x] T4: Flip every per-dimension list to best→worst (`_dim_bars`: scores/tps descending,
      latency ascending, missing values last) in both panes. Tests: dim-lists-best-first
      (code/speed/gen, live and retired rows).
      (evidence: batch-2.log)
      depends_on: T1
      refs: R7
- [x] T5: Docs (`README.md` retired wording; ADR-0010 note) + traceability
      (`python3 harness/tools/check-traceability.py --feature report_polish` → save to
      `harness/specs/report_polish/review.md`) + full suite + request the Completion Gate.
      (evidence: harness/logs/report_polish/batch-3.log; traceability 12/12 PASS;
      checklist walk in review.md)
      depends_on: T2, T3, T4
      refs: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12
