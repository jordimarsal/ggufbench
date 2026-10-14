# Historical log (append-only)

> Each time a session closes, its summary is appended here.
> Do not edit previous entries. Only append.

Entry shape — the `retro:` line is the per-feature efficiency record
(inspect it to see where process friction accumulates):

    ## <date> — <feature>

    <3-5 line summary>

    retro: <n> dispatches · <s> stalls · <r> restarts

## 2026-10-09 — hard_code_tier (done)

Feature 1 completed following SDD hybrid: Spec Gate approved (spec-gate.md),
6 batches with evidence in harness/logs/hard_code_tier/, traceability 8/8 PASS
(traceability-check.txt), Completion Gate approves (APPROVAL). 16 hard tasks
(4 per language), --level easy|hard, by_level in the code result,
tasks_version v2. 137 tests OK. Commit b80df2b.

Next feature: 2 remeasure_pool (pending) — re-measure of all models
with the hard level and the fixed harness (~1 h GPU, never both engines at once).

## 2026-10-09 — timeout_scaling (done)

Feature 3 (express, inside the re-measure): fixed 60 s left hard tasks uncovered
for slow thinking models (20 exclusions mid-run). New code_timeout(budget,
gen_tps) = clamp(90, 60 + (budget/gen_tps)*1.25, 600): token budget equal for
everyone, anti-hang clock derived from measured speed; timeouts remain
exclusions. ADR-0001. remeasure_pool run aborted and repeated under the new
protocol. 139 tests OK, traceability 4/4 PASS.

## 2026-10-09 — single_token_budget (done)

Feature 4 (reviewer proposal): a single 16384-token budget (context ceiling)
instead of the 2048->4096->8192 ladder. With fixed seed/temp the score is identical
(deterministic prefix) but 1-2 dead requests per task are removed with thinking models, and
the long thinking queue (8-16k) gets measured. out_tokens recorded in the trace as
an efficiency metric. ADR-0002. 139 tests OK, traceability 4/4 PASS.

## 2026-10-10 — discriminative_tasks (done)

Feature 5: expert code level (`_expert`, `--level easy|hard|expert`): 12 tasks
(3 per language: whole module / ~100-line debug with 3 bugs / messy data via
EXTRA_FILES in the sandbox), author validation 12/12 (ref OK, partial fails at the 3rd
behaviour), `by_level` with expert + report, `tasks_version` v3. Weights and folding
untouched. R5 smoke with 2 real models: `log_filter_debug_expert` and `proc_registry_expert`
separate ✓/✗ with gap 100 (smoke-r5.md + mechanical test). Findings: D6 (without `speed` the
code timeout falls to fixed 90 s) and a 16384 ceiling with empty text on the 27B (think
hypothesis). Traceability 7/7 + --all PASS (3 obsolete IDs remapped). 165 tests OK.
Commits c982cb9 + 3fc5004 + ef116f4. Completion Gate approved with a change: code
budget starts at 32768 (in the next feature).

Next feature: 6 thinking_batches (pending) — dual think/no-think batch +
32768 budget + signalled exclusions + pool key by (slug, thinking).

## 2026-10-10 — thinking_batches (done)

Feature 6 (reviewer decision: dual think/no-think batch + Q1 with 32768): `--thinking
on|off` (default off) via `thinking_body()` through the body (generalizes the old
STRATA_EXTRA_BODY, removed); `thinking` in every result; pool keyed by
(slug, thinking) + filenames `-on/-off` + tolerant legacy; `token_budget` keyed by
mode with `_schema = 2` (16384 era ignored); `CODE_MAX_TOKENS = 32768` + clock cap
1000 (same formula); THINK column + `(N excl.)` in Tables 1/2/3; badge +
`excluded code` in the HTML; banner intact; docs (SPEC/AGENTS/MILLORA: D6 closed, C2
updated). Precondition found and solved: 3 profiles without `-c` → `-c 65536`
(environment, outside git). Traceability 7/7 + --all PASS. 187 tests OK. Commits c3402b5
+ 7254e04 + ef61d53. Completion Gate approved without changes.

## 2026-10-10 — remeasure_pool (done)

Unlocked by the thinking_batches gate. Dual batch with the new harness (32768 tok,
1000 s cap, pool key by mode): llama OFF 10/10 (~31 min) + llama ON 10/10 (restart
for early process death at 3/10, indeterminate cause; stable setsid+faulthandler)
+ Strata OFF + Strata ON, 0 serve_failed, never both engines at once. Final pool: 22 fresh
v3 rows from a single date (11 off + 11 on; legacy archived). Report regenerated without
banner, badges 11+11, exclusions visible (`96% (4 excl.)`). Results: OFF leads
GLOBAL; in code the 27Bs rise thinking (0.82→0.96) and the small MoE burns itself (5 exclusions);
expert bites (OFF 0.73–0.88). Traceability 5/5 + --all PASS. 187 tests OK.
Completion Gate approved with declared deviations (v3+expert, two rows per model).

## 2026-10-12 — c1_stage2_core (done)

Feature C1 stage 2 core (`--runs N` multi-run aggregation on tools/code/agent graders):
added `--runs N` CLI flag (int ≥ 1, default 1), plumbing into `_bench_one` → graders.
Each of grade_tools/grade_code/grade_agent loops N times with fresh model calls and grading;
per-task trace entries gain `"runs": [passed_or_x,...]`; excluded runs marked "x" don't count
as attempts. Section score = mean over tasks of non-excluded pass-rates; fully excluded tasks
dropped from mean. N=1 byte-compatible (omits `"runs"` key); N>1 adds back `"excluded"` boolean
for API compat. Fixed: `by_lang` in grade_code to aggregate across runs, turns accumulation
in grade_agent across all N runs, exclusion key handling. Test suite: new TestGradersMultiRun
(3 cases), new TestRunsCLI (--runs parsing/validation/propagation). Suite 264 passed.

## 2026-10-14 — ad-hoc: C1 close-out + two report defects + C9 signature (done)

Human order, outside gates (all 6 features stay `done`; `lora_eval` still `spec_ready`).
C1: the llama ON re-pass was **dropped by decision** (C8 already answers the thinking
question with measurements) and qwen36 — the model the jinja template degeneration had
kept out of the batch, fixed by the llama.cpp update — was measured OFF × runs 3 at the
full suite (16/60/60): global **0.81 ±0** (tools 94% ±0, code 76% ±2, agent 77% ±3,
18 ms, 212.7 t/s, **0 exclusions**), wall 1104 s, rank 7/30. The expert tier is its weak
spot (by_level expert 0.58 vs hard 0.81 / easy 0.79; code by_lang: ts 1.00, py 0.90,
java 0.71, bash 0.69). Two defects found and closed on the way: **D7** retired rows lost
their gray marking because the only source was `models/retired/*.txt`, outside the repo
and deleted — the registry is now tracked data (`harness/retired.json`, union with the
archived profiles, degrades to empty); **D8** one model held two pool identities because
`--models` globs absolute paths while a hand-passed path stays relative — `run.model_id`
stores a workspace-relative path and `report._key_of` identifies by file name (ADR-0009),
collapsing the qwen36 twin (31 → 30 rows). Finding: the pool held **three task sets under
one `tasks_version`** (8/60/24 ×11, 12/60/28 ×17, 16/60/60 ×2) because the C3 commits added
tasks and never bumped it. Decision: make the drift impossible — `report.task_signature`
(derived from the traces, stored per row, retroactively derived for legacy rows) + CLI
footer note + HTML chip/banner + compare banner and picker `sig`, `TASKS_VERSION` → v4
(MILLORA §2c/C9 option 2 done; option 1, the fleet re-measure, stays open). Also closed:
**D9** the suite wrote 5572 junk receipts into the real `results/runs/` since 2026-08-03
(three setUps overrode `POOL_FILE` but not `RESULTS_RUNS`) — fixed + rule in
`docs/conventions.md §Testing` + the guard test that snapshots the real dir; parked in
`results/runs/_test-junk/` with a README. Loader baselines re-recorded (the C3 growth:
load_agent 2.33x, load_tools 1.91x, matching the file ratios; code loader 1.01x).
Report regenerated and **published** (`gh-pages` b6a7c57, main 0dd372e): 30 models, 9 gray,
no `_home_jordi` twin, task-sets chip. Suite 375 green (1 skip); `harness/init.sh` green;
bench gate "no benchmark regression". Commits 8431a01 → 729fd66.

retro: the two defects were both **two sources of truth** (file location vs tracked
registry; path string vs model identity) and the third (D9) a writer path nobody had
enumerated — one grep for "what writes where" would have caught all three; the pool drift,
in turn, came from a *label* (`tasks_version`) doing a *data* job, which is why the fix is
derived data rather than a promise to bump a constant.

## 2026-10-14 (cont.) — test version visible per row + orderable board (done)

Human order: every model must show which test version it was measured with, the board
must be orderable by value *and* by test version, and no doc may present a mixture of
versions as one table (each version documented instead). Delivered in three layers.
**CLI:** Table 1 gained a `SET` column (`label·task-set`, e.g. `v3·16/60/60` — label and
real set shown together because they disagree exactly where it matters) and
`--sort global|tools|code|agent|speed|version`, where `version` groups by set (biggest
first, global inside each group). **Report:** `SET` badge in every row and card, a static
"By task set" section (one block per set with its rows ordered by global, linked from the
header chip) and an inline order control that reorders the ranking in place by the same six
keys; dimension titles take their counts from the data (the stale 32/24/8 is gone).
*Contract:* the report is no longer zero-JS — still self-contained (one inline script, no
external resource, no network) and correct with JS off (spec + checklist + MILLORA updated).
**Docs:** README now holds one table per set (current 16/60/60, superseded 12/60/28, the ON
batch noted) plus a Task-set lineage table (v1 base → v2 hard → v3 expert → v4 C3) and the
`--sort version` recipe; the damaged Quickstart (missing header, fence and step 1) was
repaired. The 3 write-ups stay for after the fleet re-measure, as decided. Verified: the JS
comparator exercised in node against a stub DOM (six orders, rank renumbering, missing speed
last), render bench baseline re-recorded (19.2 → 28.3 ms, the page grew; 19-33 ms noise),
394 tests green, bench "no benchmark regression", report re-published (gh-pages, main
44508eb). Commits: 44508eb.

retro: the request was really "make the condition self-evident in the artifact" — the data
(`task_signature`) already existed from the morning's fix, so this pass only had to surface
it and order by it; the expensive part was the report's zero-JS contract, which had to be
renegotiated in docs and tests instead of quietly broken.
