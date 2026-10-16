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

## 2026-10-14 (cont.) — C10: the baseline and the engine build are conditions too (done)

Found while answering "what is left in MILLORA": the task set was the only condition that
travelled in data and was checked. Two others did not. **Engine build:** llama 0.4.0-dev
(7 rows) and 0.6.0-dev+4413a19 (8 rows) live inside the *same* 12/60/28 set (Strata
0.1.43.1 vs 0.1.44.1 likewise) — displayed per row, never compared. **Baseline flags:**
ADR-0008 switched the KV cache `q4_0`→`q8_0` on 2026-10-13 20:16, i.e. after the whole C1
batch (last row 13:39) and before the two rows of 14/10, and no field recorded which one a
row ran with (`model_config_flags` is the per-model profile). Implemented (human order,
dispatched to the local fleet via the llama-slots skill — Strata iq3_xxs, the skill's
dispatch default, one implementer, leader-reviewed): `config.baseline_argv()`;
`report.baseline_flags()/baseline_id()` (`sha1[:8]`, `?` for rows that predate the field —
never invented), `CONDITION_AXES`, `condition_axes()`, `mixed_axes()`; `save_result` records
`baseline_flags`; the CLI footer, the HTML chips/banner, the per-row `<pre>` and the compare
banner (server + picker JS, kept in sync by a guard test) now fire per axis. Docs: SPEC §2
(three condition axes) + MILLORA §C10 closed with the evidence — current baseline id
`f982b06a`, the pre-ADR-0008 q4_0 one `fd886dd9`, both verified by hand. Reviewer fixed
"1 rows" → "1 row" in the banner counts and recorded the deliberate trade-off that the
digest is the literal argv the server received (an infra edit over-warns rather than hides).
Verified: 416 tests green (2 smoke skips while the local server held the GPUs), `init.sh`
green, the picker JS exercised in node against a stub DOM (six cases: identical → no banner;
baseline-only / engine-only / set-only / date-only / version-only → the right clauses),
evidence in `harness/logs/c10/` + `harness/progress/impl_c10.md`. Published: gh-pages
`b6d20fd` (the page now carries the engines chip and `baseline ? (not recorded)` per row; the
baseline axis stays silent until a row is re-measured under the field). Strata stopped after
the dispatch (GPUs free). Commit b6d20fd.

retro: the second axis was found by *listing what the data does not say*, not by reading the
code — the audit question ("what does the board compare?") transferred from C9 unchanged and
paid again; and giving the implementer the exact function names + the three surfaces turned
a 125B local model into a usable worker, with the review finding only a plural. What stays
human: deciding which flags count as a condition (the digest trade-off) and committing.

## 2026-10-14 (cont.) — C3 fill + C4 multi-file agents; suite becomes v5 (done, 9/12 C4 tasks)

Human order: have **all** the C3 and C4 tasks in place *before* spending the GPU night on
C9, so the fleet is measured once (at v5) instead of twice. Two units, both landed.
**C3 (closed, MILLORA §C3):** tools 16→18 (+2 argument-precision/instruction-following),
code 15→18 per language (+1 hard, +2 expert each) → every code cell is 8 easy + 5 hard +
5 expert (72 tasks), four languages identical (asserted). New: `parse_size_hard` ×4,
`csv_stats_expert` ×3, `ledger_fifo_expert`, `ttl_cache_debug_expert`,
`format_duration_expert`, `schedule_slots_expert`, `diff_objects_expert`. **C4 (§C4):** the
harness learned to grade a project — `list_files` tool, the whole project handed to the
executor (a fix in a module the test never names now changes the verdict; java compiles
every `.java`), flat-sandbox path validation, and **the test file read-only + graded from its
pristine copy** (tasks already said "without touching the tests"; nothing enforced it).
9 multi-file projects (5-8 files, 14 turns): python 3, ts 3, java 2, bash 1, each verified
with the new `harness/tools/check-task.py` (reference outside the repo) and gated by
`tests/test_agent_tasks.py` ("the shipped project MUST fail its own test"). **Rejected and
removed rather than shipped broken:** `typescript/mapped_type_refactor` (types are erased,
bun does not type-check → unmeasurable AND test-less: a free pass for every model),
`bash/csv_quoted_fields`, `bash/retry_pipeline` (tests that could not exercise their own
contract), `java/feature_flag_end_to_end` (passed as shipped). `TASKS_VERSION` → **v5**
(18 tools / 72 code / 68 agent); README's scoreboard restructured (v5 current, no row
measured at it yet) + lineage row; AGENTS/SPEC/MILLORA updated. The local fleet (qwen36,
4 slots) wrote most of the agent tasks: 12 dispatches, 9 usable — the lesson is that the
model's *self*-verification was not reliable (3 tasks reported "VERDICT ok" that do not
survive a re-run) while the tool itself was: every task that ships was re-verified by the
leader. Suite 438 green, `init.sh` green, bench "no benchmark regression", server stopped.
Commits 35a0d2c + d0d05a8. Open: the 3 remaining multi-file tasks (bash 2, java 1) and the
C9 fleet re-measure at v5.

retro: the gate was worth more than the generator — `check-task.py` caught three of my own
wrong expectations and every broken fleet task, while the fleet's own claims were wrong
twice; and "remove it" beat "ship it broken" every time the gate said no.

## 2026-10-14 (cont.) — C4 completed: 13 multi-file projects, 18/72/72 (done)

The three tasks the gate had rejected were rewritten by hand with that same gate, plus one
extra for typescript so its cell recovers the task lost to `mapped_type_refactor`:
`bash/csv_quoted_fields` (a parser splitting quoted fields on the inner comma),
`bash/retry_pipeline` (gives up on the first failure; the fake operation now lives in a FILE
— `attempt.sh` — because the rejected version defined it inside the test, in a shell the
child process cannot see), `java/feature_flag_end_to_end` (Cli ignores `--quiet`, Renderer
ignores the flag it gets; the test captures stdout/stderr and asserts the header is gone and
the rows are not) and `typescript/order_merge_duplicates` (repeated SKUs must accumulate).
All four verified with `check-task.py` (shipped FAILS / reference PASSES — references stay in
/tmp) and by the structural gate, which is back to its real target (>=3 multi-file per
language, >=12 total; `test_multifile_tasks_start_from_a_failing_state` keeps rejecting any
project that passes as shipped). **Final ledger of the fill: tools 18 · code 72 · agent 72
(bash/java/python/typescript each 18), tasks_version v5** — the four cells finally have the
same shape, which is what makes a by_language difference the model's and not the dataset's.
Suite 438 green, `init.sh` green, bench "no benchmark regression" (loaders 1.20-1.24x, inside
the warning band), no server running. Commits d0d05a8 + 12bf918 (+ the harness commit
35a0d2c). **The task set is frozen: what is left is the C9 fleet re-measure at v5, then the
three write-ups and the README tables with the new numbers.**

retro: the two bash rewrites cost less than repairing the originals because the contract was
written from the test backwards ("what can a child process actually see and assert?"); the
generator (a local model) was useful for volume, the gate for truth, and the second pass was
pure gate-driven authorship.

## 2026-10-14 — pla de la nit del v5 (executat els dies 14-15)

_The task set is frozen at v5 (tools 18 · code 72 · agent 72) and the sampler is pinned in the
baseline (`ed3153c0`), so what is left is a night of GPU: the holes on the board are
conditions, not data. Sequence fixed with the human (2026-10-14), running detached:_

1. **Dense fleet, thinking OFF, at v5** — Heretic, TurboFCFusion, UD-Q3_K_XL, Qwen3-VL-8B,
   `--runs 3`. Running; log `harness/logs/v5_off/dense.log`. Upserts the four dense rows.
2. **Strata: calibrate the engine, then OFF, then ON.** `./setup.sh --calibrate` measures the
   four PC-dependent settings (the share of missed experts copied over PCIe instead of computed
   by the CPU, the draft confidence, the CPU pool threads, the VRAM expert cache) and writes
   them **into the config's args** — so they land in `model_config_flags` of every row measured
   after it (the §C9 lesson: a condition that differs must be visible in the row). Calibrate
   both configs (`iq3_xxs`, `swift-iq3_xxs`), then OFF ×3 on both and ON ×3 on `iq3_xxs` (the
   ★ optimal-mode marker needs the pair; the swift row has no ON counterpart in the pool).
3. **Fleet ON at v5** — 8 GGUF (3 MoE + MiniCPM + the 4 dense) with `--thinking on` and the
   per-call caps raised **for the whole batch**, the same value in every row: `--tools-max-tokens
   256 --agent-max-tokens 1024`. The 128-token cap is measurably too tight (Heretic's OFF run
   hit it twice on `refuse_delete_protected`). The code budget stays 32768 so the ON/OFF pair
   is not confounded by anything but the mode.
4. **Then the paperwork**: `--scoreboard --html` + `harness/tools/publish-report.sh`, the three
   write-ups (`docs/writeups/*.md`) and the README tables, which still describe the C1-era
   condition (12/60/28, "42 multi-step agent tasks").

## 2026-10-14 — MiniCPM 4.7, mostreig, LFM2.5 retirat, sondes, Strata calibrada

- **2026-10-14 · New model preview: MiniCPM-V 4.7 35B-A3B (OpenBMB, human order).** The tweet
  (2026-10-12) announces the MiniCPM-V 4.7 series; the 35B-A3B is the first MoE of the family
  (on-device MLLM, LES lookahead expert scheduling, Apache-2.0). Checked before downloading:
  the GGUF declares arch **`qwen35moe`**, which this repo's llama.cpp (0.6.0-dev+4413a1924)
  supports — `llama_model_qwen35moe` + `src/models/qwen35moe.cpp` are in libllama.so, MTP
  branch included. Header read over HTTP range (no download): ctx 262144, 40 blocks with
  `full_attention_interval 4` (hybrid SSM/attention), GQA 2/16 with key/value length 256 →
  KV is cheap (~1.5 GB at 128k, q8_0), 256 experts / 8 active, **no MTP tensors** (their
  speculative path is the separate DSpark draft + LES fork), and the chat template honours
  `enable_thinking: false` → the harness's OFF mode is a clean instruct run.
  Downloaded `MiniCPM-V-4_7-35B-A3B-Q4_K_M.gguf` (21.2 GB) with `hf download` into
  `models/`, plus the profile `models/MiniCPM-V-4_7-35B-A3B-Q4_K_M.txt` (`-c 131072`: the
  32768 code budget must fit with the prompt; sampling stays the harness baseline).
  Run: `--models models/MiniCPM-V-4_7-35B-A3B-Q4_K_M.gguf --runs 3` (thinking OFF, the pool
  protocol), log in `harness/logs/minicpm_v47/`.
- **2026-10-14 · First run done (24 min) — and it found a grader bug, not a model trait.** The
  row came out `tools 1.000 ±0 · code 0.571 ±4 · agent 0.895 ±1 · 18→23 ms · global 0.826 ±1`
  with a nonsense level breakdown (`easy 0.44 < hard 0.75`) and a bash-only language pattern.
  Reading the trace showed java/python/typescript tasks recorded as `bash` entries: the
  multi-run aggregation looked entries up by `id`, and ids are unique per *dimension*, not per
  language (the easy tier mirrors `bubble_sort` etc. across the four) — so every shared id took
  bash's outcome. The same refactor had also hardcoded `grade_agent`'s `by_lang` to `{}` and
  dropped `lang` from the agent trace. Fixed (MILLORA §D10, commit 53779ba) with 5 regression
  tests; SPEC §4.4 + AGENTS §3 now state the identity rule. **Consequence: every existing row's
  code/agent score is skewed — the C9 re-measure is the only way to valid numbers**, and the
  MiniCPM row was re-measured right after the fix (log `batch-off-runs3-fixed.log`).
  Tweets aside, the interesting part: the model itself looks strong on tools/agent and weak on
  bash (it answers bash prompts with rust/python fences → exclusions), which the fixed grader
  will now attribute to the right language.
- **2026-10-14 · Sampler settled with data, not doctrine (baseline `f982b06a` → `ed3153c0`).**
  The Ornith A/B: A (temp 0.2 / top_k 40, the harness baseline) against B (temp 1.0 / top_k 20,
  the author's card) gave **0 of 72** code verdict flips with identical code tokens (16,433) and
  2 of 72 agent flips (0.928 → 0.918, inside the ±). So the sampler stays pinned in the baseline
  and (B) remains available as an explicit per-profile option. Receipts: the two
  `results/runs/20261014-*ornith*-off.json` files. Rows measured before the pin keep the old id
  and the board flags them — the reason the dense/MoE OFF rows are re-measured tonight.
- **2026-10-14 · LFM2.5-24B-A2B retired (human decision) — and the reason is a harness lesson.**
  Its chat template always opens a `<think>` block and has no `enable_thinking` switch, so the
  harness's OFF mode was impossible for it and the reasoning ate the per-call budget: 0.59 global
  (tools 78 / code 74 / agent 51). A focused re-run with 256/2048-token caps lifted tools to ~91%
  and the agent to ~75% at half of the dimension — better, still under the fleet's 87-93%. The
  GGUF and its profile are deleted; the stem is in `harness/retired.json` so its pool row stays as
  a record and renders gray (`7a73168`).
- **2026-10-14 · Probes and traceability, so that no condition can hide.** Every row now carries
  `code_budget` / `code_budget_stored` and `ctx_resolved` + `ctx_source`, and the harness probes
  the run itself (`code_budget_hits`, `tools_capped`, `agent_empty_replies`,
  `thinking_mode_applied` via `/props`, with a `probes:` line on the model card). Live proof
  today: the LFM pass warned on 7 truncated tool calls and 5 empty agent turns, and Heretic's OFF
  run warned twice on the 128-token tool cap — which is the evidence behind the 256/1024 caps of
  the ON batch. Legacy `token_budgets.json` entries (37 rows, 4096/8192) are inert: no `_schema: 2`.
- **2026-10-14 · Strata was calibrated — with the engine of 2026-10-01.** Checked
  `~/.config/strata/settings.json`: the calibration ran on 2026-10-01 for
  `qwen3.8-flash-next-iq3_xxs|131072` and kept a single setting, `--pool-workers 4` (65.5 t/s
  then), which is the value our config carries. That day's engine is not today's (0.1.44.1), so
  the measurement is re-run as the first Strata step of the night. `--calibrate` rewrites only the
  config's args and the settings file — it never reinstalls — and `--yes --no-start` makes it
  non-interactive without leaving a server up.

## 2026-10-16 — Heretic: l'A/B d'MTP (i dos paranys pel camí)

**El MTP natiu no existeix en aquest GGUF.** Verificat amb el lector de GGUF: l'Heretic no té cap
bloc MTP (no hi ha `blk.64.nextn.*`; l'últim és `blk.63`) i el servidor ho diu tal qual: "context
type MTP requested but model doesn't contain MTP layers". La nota que hi havia al perfil ("el GGUF
el declara (ffn_mtp)") era meva i era falsa, i està corregida. Qui sí que en porta: qwen36
(`blk.40`), Ornith-APEX (`blk.40`) i UD-Q3 (`blk.64`).

**La família, però, porta el cap MTP separat**: `models/nerkior/mtp-Qwen3.8-27B-Q4_0.gguf` (18
tensors: `blk.64.nextn.*` + `token_embd` + `output`), i el build l'accepta com a esborrany
(`--spec-draft-model`). Sonda en viu a `-c 86016` amb el cap a la GPU: **151,4 t/s contra 47,0
t/s** del mateix model sol, 149/197 acceptats (76%). Amb el cap a CPU: 10,9 t/s — pèrdua.

**Disseny del 2×2**: quatre cames a `-c 86016` (el pin del seu OFF, on el cap hi cap; a 233472 no
hi entra: el KV de l'esborrany demana 456 MiB i el seu graf 1220 MiB a la targeta 0), OFF/ON ×
sense/amb cap, 3 passades, sostres 1024/8192, perfil tornat a 233472 al final i **taulell
protegit** (`pool.before-heretic-mtp-ab.jsonl` + restauració per `trap`): les files de l'A/B
viuen com a rebuts a `results/runs/` i no toquen el taulell. Les cames amb cap diuen "amb cap de
la família", no "MTP natiu" — mesuren el cap com a esborrany, que és una altra cosa.

**Dos paranys, tots dos del mateix tipus** (una condició que diu una cosa i n'és una altra):

1. *La llista blanca del harness* (`config.py`) portava el nom vell de la bandera (`-md`) i
   tirava la nova (`--spec-draft-model`) sense aturar la passada: la cama va sortir amb
   `--spec-type draft-mtp` i sense cap, i el servidor va morir en carregar. Arreglat (`b1efb8e`)
   amb test que el nomena, mateix tractament que les banderes de mostreig de §C11. La sonda en
   viu no hi va caure perquè afegia les banderes *després* de `build_args`.
2. *El meu esborrador del perfil* ancorava els patrons en el nom solt i deixava
   `--spec-draft-model <ruta>` i `--spec-draft-n-max 4` al fitxer després de cada neteja: per
   això la cama 3, tot i ser un ON net, arrossega un `--spec-draft-n-max 4` inert (sense
   `--spec-type` no hi ha esborrany). Esborrador arreglat; queda anotat com a condició que hi és.

**Estat de les cames** — tancat el 16-10 a les 17:15, amb perfil (233472, sense cap) i taulell
(byte a byte igual al snapshot) restaurats. Totes a `-c 86016`, 3 passades, sostres 1024/8192:

| cama | mode | cap | tools | code | agent | sonda | t/s | global | passada |
|---|---|---|---|---|---|---|---|---|---|
| 1 | OFF sense cap | no | 100 | 86,1 | 93,1 | 69 ms | 57,6 | 0,819 | 56 min |
| 2 | OFF amb cap | sí | 100 | 82,9 | 94,9 | 41 ms | 97,2 | 0,833 | 33 min |
| 3 | ON sense cap | no | 94,4 | 89,8 | 97,2 | 1075 ms | 66,9 | 0,798 | 7 h 44 |

**Què en surt**: el cap funciona i és un guany d'**1,7×** (sonda 69→41 ms, generació 57,6→97,2
t/s, passada 56→33 min) **sense cost de qualitat** dins el que tres passades permeten dir (code
−3,2 i agent +1,8 punts; tools igual; la dispersió del taulell és ±2-4). El global de l'OFF puja
+0,014 (0,819→0,833): el cap es paga per la via de la velocitat. La cama 1, a més, diu que els
sostres alts no mouen l'OFF (dims idèntiques als de la fila canònica amb 512), i la cama 3 que
comparar l'ON a 86016 amb el canònic a 233472 és just (0,798 vs 0,796; sonda 1075 vs 1060 ms).

**El preu del cap és context**: a 233472 no hi cap (KV de l'esborrany 456 MiB + graf 1220 MiB, i a
la targeta 0 n'hi havia ~1 GB); a 86016 hi cap de sobres. El sostre exacte amb cap no està
mesurat (entre 86k i 233k). Per això el perfil no el porta per defecte: el context és el que
aquest model ven al taulell, i la nota del perfil deixa la comanda preparada per a qui prefereixi
latència.

**No mesurat**: la cama 4 (ON amb cap), aturada a posta l'16-10 pel cost (~2-3 h) contra el que
aporta (mecanisme, no decisió). Nota per a qui ho repengui: en ON el coll és el pressupost de
32768 (6 topades a la cama 3, 0 a les dues OFF) i el cap no mou tokens, només rellotge — el que
s'hi guanyaria són hores de passada, no punts.

## 2026-10-16 (vespre) — Els pins de context màxim són de màquina tranquil·la

La suite ha caigut avui per una cosa que no era el codi: `test_smoke.py` aixeca un servidor de
debò amb el perfil de producció del model petit, i el d'UD-Q3 (`--spec-type draft-mtp --mmproj
-c 262144`) demana 1226 MiB per al graf de l'MTP i la targeta diu no. Amb el despatx actiu (~1,8
GB a la targeta 0), Heretic tampoc carrega a 233472: mor al mmproj (884 MiB); a 220k i a 212k
carrega, però amb 660 i 591 MiB lliures — per sota del marge de 1200 MiB que la sonda exigeix.

És a dir: les files ON de context màxim (Heretic, UD-Q3, qwen36, Ornith, qwen39, gemma) són
mesures de **màquina tranquil·la** — les vam fer de nit. Els rebuts són vàlids; el que no es
reprodueix és la condició. Si un run falla en arrencar amb `cudaMalloc ... out of memory`, és
això i no el codi: tancar el navegador, o baixar el pin. Verificat amb la sonda arreglada (que
ara, quan el sostre falla, comprova el terra abans de dir "none"): rebut complet a
`harness/logs/probe-context-smoke.log`.

Arreglat de passada, i és el que fa tornar la suite a verd:

- `ServerManager(extra_args=...)`: van al final, després del perfil — mateixa convenció que el
  propi perfil, o sigui que l'última paraula és del qui crida.
- El smoke carrega a `-c 8192`: la seva feina és la canonada (arrencar → xerrar → correctors),
  no validar el pin de producció; per a això ja hi ha el smoke de nivell 3 de
  `docs/verification.md`. 473 tests, verd, amb 1 salt (el del `--version`, que ja era).

**I el pin, baixat** (petició de l'usuari, 17:34): Heretic passa de `-c 233472` a **147456**.
Mesurat amb la sonda amb el despatx actiu i marge 2000 MiB: 196k→937 lliures, 170k→1509,
157k→1797, 150k→1961, i 144k→**2047**, l'únic que passa. Amb el marge estàndard de 1200 hi
cabria ~170k; s'ha triat 2000 perquè entre nit i dia el despatx bascula ~1 GB i encara hi ha
d'haver lloc per a un navegador. La fila ON (233472) queda com a rebut de màquina tranquil·la;
el proper run sortirà a 147456 i escriurà la seva pròpia condició (`ctx_resolved`), que és el
que el taulell llegeix. Si mai es vol més context, la variant d'~170k és a la nota del perfil.

## 2026-10-16 — Publicació del taulell v5 (README + gh-pages)

L'ordre era "publica el report actualitzat", i el report només era mitja veritat si la portada
del repo deia el contrari: el README encara anunciava *"One row so far"* per al conjunt v5 quan
al pool ja hi ha la re-mesura de l'estol sencer. Publicat, doncs, en dos passos:

- **README**: la secció del taulell porta ara la taula v5 completa (6 GGUF + Strata, OFF i ON =
  14 files, ordenades pel global com al CLI) amb el ★ del mode òptim. El text del voltant diu
  el que el report ja sap: 13 retirats (9+1+3, `harness/retired.json`), les files de context
  màxim són de màquina tranquil·la (el report imprimeix les banderes amb el `-c` de cada fila) i
  el pin diürn de l'Heretic (147456). **Dues files ON segueixen devent una passada justa** i ara
  ho diu la portada: gemma (sostres vells 256/2048) i Strata (512, 51 respostes buides).
- **`models/ASSIGNACIO.md`** (fora del repo, sense commit): la fila de l'Heretic deia que "el
  GGUF SÍ que declara MTP" — la nota falsa que em vaig empassar ahir — i portava el pin vell
  (262144). Ara diu 147456 (diürn), que **no té MTP**, i que el cap de la família existeix a
  part i dona 1,7× d'esborrany (A/B del 16-10). La capçalera recull l'excepció al criteri
  "pin = màxim mesurat en viu".

- **`harness/tools/publish-report.sh`** → gh-pages actualitzat (ref nou `7bf7c92`, el commit
  diu `main 937e862`). Verificat que no és un CDN enganyat: la pàgina servida és **byte a byte
  igual** al render local (`curl -o` + `diff`, 133262 bytes, IDENTICS). URL:
  <https://jordimarsal.github.io/ggufbench/>. `compare.html` s'ha enviat tal qual, que és el
  disseny del script (l'últim parell executat amb `--compare`).

## 2026-10-16 — Spec `report_polish` (polit del report) → Spec Gate

L'usuari demana tres canvis de polit al report publicat: (1) els models retirats, en una
pestanya HTML pròpia (avui s'intercalen en gris a *totes* les seccions: global, code,
agent, tools, speed, t/s, matriu, condicions), (2) les recomanacions just sota la franja
de KPIs, (3) tots els llistats d'stats, de millor a pitjor. Spec escrita en mode híbrid
(fem de spec-author): `harness/specs/report_polish/` — 12 R, 5 T en 3 tandes — i la
decisió de fons a **ADR-0010**: les pestanyes amb radios + CSS pur, sense cap script nou
(la pàgina manté el pressupost d'≤1 script i es llegeix sense JS). Decidit també a la
spec: la franja de KPIs passa a comptar *només* files vives (avui «Fastest 307 t/s» i
«Lowest latency 13 ms» els guanya el Nemotron, retirat) i la pestanya Retired és el
mirall del board, sense KPIs ni recomanacions (instruments d'elecció). Res de codi
tocat: **atura i espera el Spec Gate humà** (feature 8 = `spec_ready`).

## 2026-10-16 (vespre) — report_polish: implementació (tandes 1 i 2)

Spec aprovada a la porta → feature 8 `in_progress`. L'ordre del report ara és: KPIs → recomanacions
→ "Weighted global" → resta de seccions; les files vives i les retirades viuen en panes separades
amb pestanyes de radios + CSS pur (cap script nou: la pàgina manté ≤1 script i es llegeix sense JS).

- **Tanda 1 (T1+T2)**: `render()` parteix `rows` en `live`/`gone`; panes `.pane-board`/`.pane-retired`
  amb `#tab-board:checked~…` (Board és la pestanya per defecte; sense retirats no hi ha pestanyes);
  nota "Record only…" a la pane retirada i fora el xip gris vell ("gray = retired model" descrivia un
  board que ja no existeix). Franja de KPIs i recomanacions passen a `live` (`_kpis(live)`,
  `_rec_section(live)`); la pane retirada no en porta. Seccions extretes a
  `_sections(rows, sort, *, board, optimal)`; `_by_set_section(anchors=…)` deixa els `id="set-…"`
  només al board (cap id duplicat); `_dim_bars` invertit a millor→pitjor en aquesta tanda (el codi va
  néixer amb l'extracció; els seus tests són a la tanda 2). Evidència: `harness/logs/report_polish/
  batch-1.log` (481 tests, verd).
- **Tanda 2 (T3+T4)**: xip de models `N models (+M retired)` (comptes separats només quan n'hi ha) i
  enllaços del xip de task sets només cap a blocs del board — una signatura només retirada queda com
  a text (`<span class="miss">`). Tests d'ordre per a les dues panes (code/speed/gen; sense mesura,
  al final). Evidència: `batch-2.log` (487 tests, verd).
- **T1–T5 marcats `[x]`** a `harness/specs/report_polish/tasks.md` amb referència als logs
  (`batch-1/2/3.log`). T5 feta: README ("behind its **Retired** tab — record only"), nota
  *Landed* a l'ADR-0010, traçabilitat **12/12 PASS** (`check-traceability.py --feature
  report_polish`, sortida a `harness/specs/report_polish/review.md`) i revisió caminada
  (també `harness/progress/review_report_polish.md`, veredicte APPROVED). Verificació extra
  amb el taulell real: render a `/tmp/opencode/report-polish-preview.html` — 1 sol `.tabs`,
  KPIs `0.85 / 207 t/s / 19 ms / 2026-10-15` (el Nemotron retirat ja no fa titular), llistes
  vives començant `93%` / `19 ms` / `207 t/s`, i la pestanya Retired amb 19 files sense ids.
  **Aturada a la Completion Gate per a l'humà.** El render local (`results/report.html`) i la
  pàgina publicada NO s'han tocat encara: es regeneraran (i publicaran) quan l'humà tanqui la
  porta, perquè el taulell i la pàgina no es contradiguin.

## 2026-10-16 (nit) — tancament: aprovada, `done`, report pulit publicat

Completion Gate aprovada per l'humà → feature 8 **`done`**. Tancament executat:

- `python3 -m ggufbench.run --scoreboard --html` (taulell + render nous) i
  `harness/tools/publish-report.sh` → gh-pages republicat des de `main 297c226`; la pàgina
  servida queda alineada amb `results/report.html` (135890 bytes; el CDN de GitHub Pages
  triga uns minuts a refrescar — verificar amb `?cb=<epoch>`).
- Resum de sessió mogut aquí; `current.md` net. Suite final verda (`init.sh`), arbre net.
- KPIs publicats amb el nou contracte (només files vives): **0.85 · 207 t/s · 19 ms ·
  2026-10-15** — el Nemotron retirat ja no fa titular.

**Pendents que queden (heretats, sense canvi):** la fila ON de **gemma** (sostres vells
256/2048) i la de **Strata ON** (512, 51 buides) volen una passada amb els sostres de
l'estol; re-mesurar l'ON d'**Heretic** al pin nou 147456 (una nit); oferta d'actualitzar
els tres write-ups (`docs/writeups/*.md`, encara v4) — esperant resposta; i la feature 7
**`lora_eval`** segueix `spec_ready`, esperant la seva Spec Gate.
