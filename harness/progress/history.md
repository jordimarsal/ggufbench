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
tasks_version v2. 137 tests OK. Commit 6054036.

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
Commits aabff88 + 19305d9 + 4dc88ec. Completion Gate approved with a change: code
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
(environment, outside git). Traceability 7/7 + --all PASS. 187 tests OK. Commits 6e732df
+ 5092aa4 + 541a719. Completion Gate approved without changes.

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
