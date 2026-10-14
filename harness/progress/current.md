# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** _none_ — ad-hoc session 2026-10-14 (human order): C1 follow-up
  + two report defects. All 6 `done` features stay `done`; `lora_eval` (feature 7) is
  `spec_ready`, waiting on the human Spec Gate.
- **Started:** 2026-10-14
- **Agent:** hybrid (single in-session agent, AGENTS.md §4)

## Plan

1. **C1 (human decision):** drop the ON re-pass (C8 already answers "is thinking worth
   it?" with measurements) and measure **qwen36**, the model whose jinja template
   degenerated under the baseline — fixed by the llama.cpp update.
2. **Fix the two report defects found on the way:** retired models lost their gray
   marking (the archived profiles were deleted) and one model could hold two pool rows
   (path-shaped identity).

## Log

- **Ad-hoc (Oct 11, cont.): ngram (lookup) drafting on UD-Q3** — own copy-heavy probe
  (65-line module + rename): ngram-map-k4v 352.3 t/s vs MTP n4 139.5 (2.5×);
  new text 51.2 vs 113-127 (no gain). Exclusive per server. Profile stays
  MTP n4 (mixed traffic); ngram documented in the skill for editing sessions.
  Technical note: isolated attempts in zsh failed on word-splitting (zsh does not
  split $BASE) — sweeps must run under bash.


- **Ad-hoc (Oct 11, cont.): MTP/split sweep on the fleet** (tools at bin/mtp-sweep.py +
  bin/mtp-probe.py, from the qwen38-mtp repo): tensor-split +25-45% on the 4 splitters
  (udq5/heretic/turbofcf/coder390), n4 winner (+3-6% vs n3), n6 kills prose.
  Flags applied to the .txt files: --spec-draft-n-max 4 + --split-mode tensor (UD-Q3 only n4,
  13 GB almost single-GPU; tensor untested). WARNING: pool rows for these 4
  models are now STALE (serving conditions changed) — re-measure pending whenever
  wanted (not now, human order).


- **Ad-hoc (Oct 11, cont.): Strata 0.1.42 reserve tuning** — res 1400 lost OFF decode
  (89.3 t/s); res 1000 passes the verification and wins everything: OFF 116.1 t/s gen
  (+8%), prefill 169.4 (+17%), 43 ms; ON 125.4 t/s (+14%), 465 ms, 0 excluded, code
  0.93. Final config fixed: reserve 1000. llama-slots skill §6f documented.

- **Ad-hoc (Oct 11): Strata 0.1.41 → 0.1.42** (`./update.sh`, engine recompiled, configs
  intact with the §6g budget). First start failed: the new verification
  (70 MiB arena) did not fit on CUDA0 (PROFILE cache 5232 slots over-committed; auto would
  have set 3745). Fix: `--vram-reserve-mib 1400` in strata-iq3_xxs.json (DETAILS §cache).
  Green smoke: health, models, chat with chat_template_kwargs, clean shutdown.
- **Ad-hoc (Oct 10): Coder390 into the pool** (OFF+ON): "-53% tokens" claim CONFIRMED vs
  27B siblings (2,084 vs 4.2-4.4K tok), 0 exclusions in ON, code ON 0.95. llama-slots
  skill: preferred ON reserve. 0.1.41 strata rows saved to
  harness/logs/remeasure_pool/strata-0.1.41-rows.json before measuring 0.1.42.

- **Ad-hoc (direct human order, outside gates):** out_tokens ON vs OFF analysis
  (659 paired instances) + `fix(html_report)`: readable text in the matrix
  (solid background by luminance, no alpha) + think badge in the 8 per-model sections.
  Suite 189 passed. Commit `d486a5d`. report.html regenerated (22 badges/mode).

- **2026-10-14 · feat(report) — the pool can now tell task sets apart (§C9, human decision).**
  `report.task_signature(row)` derives `tools/code/agent` counts from the traces (`?` for
  an unmeasured dimension), `save_result` stores it in the row (legacy rows get it
  derived on read, so the whole pool is labelled retroactively), and the drift is
  announced instead of hidden: CLI footer note, HTML chip + banner, compare-page banner
  when two rows differ *only* by signature, and `sig` in the picker packs so the JS path
  warns too. `config.TASKS_VERSION` → **v4** (a version is a label; the comment says what
  it can and cannot do). +12 tests, 373 total. The fleet re-measure at the current suite
  (C9 option 1) stays open.

- **2026-10-14 · fix(html_report) — retired rows were no longer gray (D7).** The only source
  of "retired" was `models/retired/*.txt`; that directory lives outside the repo and its
  profiles were deleted as duplicated information → the 9 models pruned on 2026-10-13
  rendered as live fleet (chip, badges and their exclusion from Recommendations gone).
  Registry is now tracked data (`harness/retired.json` + `config.RETIRED_FILE`), unioned
  with whatever profile is still parked under `models/retired/`, degrading to empty on a
  missing/corrupt file. +7 tests (`tests/test_html_report.py`).

- **2026-10-14 · fix(report) — one model, two pool identities.** qwen36 held two rows:
  an absolute path (from a `--models` glob) and a relative one (passed by hand), so the
  scoreboard and the compare picker listed the same model twice. `run.model_id` now
  stores a workspace-relative path and `report._key_of` identifies the model by its file
  name; the legacy twin collapses on load, most recent wins. ADR-0009. +4 tests.

- **2026-10-14 · C1 follow-up (human order).** ON re-pass dropped by human decision
  (C8 already answers the thinking question with measurements). qwen36 measured instead
  — the llama.cpp update fixed the template degeneration that had kept it out of the
  batch: `--models models/qwen36-35b-distill-mxfp4_moe.gguf --runs 3` (thinking off,
  ctx 211968 = profile pin, 16/60/60 tasks). Log:
  `harness/logs/remeasure_pool/batch-qwen36-c1-runs3.log`. Result: **global 0.81 ±0**,
  tools 94% ±0, code 76% ±2, agent 77% ±3, 18 ms, 212.7 t/s, **0 exclusions**, wall
  1104 s, rank 7/30. Expert level 0.58 vs hard 0.81 / easy 0.79; code by_lang:
  typescript 1.00, python 0.90, java 0.71, bash 0.69. The bare `--models` name is
  ambiguous (matches the `.gguf` and the `.txt`) and the resolver correctly refused it.
  Report regenerated: 30 models, 9 gray (retired), no `_home_jordi` leakage.

- **2026-10-14 · Finding — the pool holds three task sets (decided: §C9 option 2).**
  The qwen36 row came out with 16/60/60 tasks while its neighbours have 12/60/28, and
  the `tasks_version` field is "v3" for all of them: 8/60/24 (11 rows, 2026-10-10 ON
  batch), 12/60/28 (17 rows, 2026-10-12/13 C1 batch), 16/60/60 (2 rows, 2026-10-14
  strata-swift + qwen36). The C3 commits added the tasks *after* the pool was measured
  and did not bump the version, so the drift was invisible to metadata (trace length
  only) and the report's mixed-conditions banner keyed on dates. Human decision:
  implement the signature now (done above), re-measure the fleet on a GPU night
  (open). README + the 3 write-ups still state the C1-era condition.

- **2026-10-14 · fix(tests) — the suite no longer writes into the real results/ (D9).**
  `report.save_result` writes the pool *and* the receipt under `RESULTS_RUNS`; three test
  setUps (test_report ×2, test_run_cli ×1) overrode only `POOL_FILE`, so **4419 junk
  receipts** (78% of `results/runs/`, back to 2026-08-03) had accumulated — `m-na.json`,
  `solo-na.json`, `partial1-…`. Fixed the overrides, wrote the rule into
  `docs/conventions.md §Testing` ("isolate every path a writer touches") and added the
  test that would have caught it (snapshot the real dir around two saves). The junk is
  parked in `results/runs/_test-junk/` with a README, not deleted. 1268 real receipts
  remain; verified the full suite leaves the directory untouched.

- **2026-10-14 · Report published (human order).** `--scoreboard --html` + `--compare`
  (strata off/on, refreshed with the §C9 code) + `harness/tools/publish-report.sh` →
  `gh-pages` `b6a7c57` (main 0dd372e). Verified in the branch: 30 models, 9 grey rows, no
  `_home_jordi` twin, task-sets chip `12/60/28 · 8/60/24 · 16/60/60`. The public page
  still served the previous copy at first fetch (GitHub Pages CDN caches HTML ~10 min).
 The strict gate was red
  on `test_load_agent` (2.33x, critical) and `test_load_tools` (1.91x) while the code
  loader stayed at 1.01x: the C3 growth (tools 8→16, agent 24→60 files) is the cause and
  the ratios match the file ratios. New means + a note in each entry; verdict is
  "no benchmark regression" again. `test_render_pool_24` fluctuates 19-33 ms across idle
  runs (warning band) and was left alone. Also noticed: the suite writes junk receipts
  (`m-na.json`, `solo-na.json`…) into the real `results/runs/` — test isolation leaks
  there (the pool itself is safe, POOL_FILE is overridden); candidate fix, not taken.

- Suite: **373 tests OK (1 skipped)** —
  `python3 -m unittest discover -s ggufbench/tests -t .`; bench gate: no regression.

## Next step

- **Open:** re-measure the active fleet (7 GGUF + Strata, OFF × runs 3) under the current
  16/60/60 suite (C9 option 1) — only then is the published table homogeneous again.
- **Open:** README scoreboard (states the C1 condition and "harness v3") and the three
  write-ups (say "42 multi-step agent tasks"; the ties conclusion leans on qwen36's old
  0.84) need the same pass.
- **Open:** the test suite writes junk receipts (`m-na.json`, `solo-na.json`…) into the
  real `results/runs/`: override `RESULTS_RUNS` in the affected tests.

_If a new session opens: read AGENTS.md + current.md + feature_list.json._
