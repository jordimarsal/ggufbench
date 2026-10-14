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

- **2026-10-14 · fix(html_report) — retired rows were no longer gray.** The only source
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

- **2026-10-14 · Finding (needs a human decision) — the pool holds three task sets.**
  The qwen36 row came out with 16/60/60 tasks while its neighbours have 12/60/28, and
  the `tasks_version` field is "v3" for all of them: 8/60/24 (11 rows, 2026-10-10 ON
  batch), 12/60/28 (17 rows, 2026-10-12/13 C1 batch), 16/60/60 (2 rows, 2026-10-14
  strata-swift + qwen36). The C3 commits added the tasks *after* the pool was measured
  and did not bump the version, so the drift is invisible to metadata (trace length
  only) and the report's mixed-conditions banner keys on dates. Written up as MILLORA
  §2c/C9 with options (re-measure the fleet / derive the signature from the trace /
  both); README + the 3 write-ups still state the C1-era condition. No action taken —
  it is the user's call.

- **2026-10-14 · chore(bench) — loader baselines re-recorded.** The strict gate was red
  on `test_load_agent` (2.33x, critical) and `test_load_tools` (1.91x) while the code
  loader stayed at 1.01x: the C3 growth (tools 8→16, agent 24→60 files) is the cause and
  the ratios match the file ratios. New means + a note in each entry; verdict is
  "no benchmark regression" again. `test_render_pool_24` fluctuates 19-33 ms across idle
  runs (warning band) and was left alone. Also noticed: the suite writes junk receipts
  (`m-na.json`, `solo-na.json`…) into the real `results/runs/` — test isolation leaks
  there (the pool itself is safe, POOL_FILE is overridden); candidate fix, not taken.

- Suite after both fixes: 361 tests OK (1 skipped) —
  `python3 -m unittest discover -s ggufbench/tests -t .`

## Next step

_If a new session opens: read AGENTS.md + current.md + feature_list.json._
