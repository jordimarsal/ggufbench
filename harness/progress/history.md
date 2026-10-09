# Historical log (append-only)

> Each time a session closes, its summary is appended here.
> Do not edit previous entries. Only append.

Entry shape — the `retro:` line is the per-feature efficiency record
(inspect it to see where process friction accumulates):

    ## <date> — <feature>

    <3-5 line summary>

    retro: <n> dispatches · <s> stalls · <r> restarts

## 2026-10-09 — hard_code_tier (done)

Feature 1 completada seguint SDD hybrid: Spec Gate aprovat (spec-gate.md),
6 batches amb evidencies a harness/logs/hard_code_tier/, tracabilitat 8/8 PASS
(traceability-check.txt), Completion Gate aprova (APPROVAL). 16 tasques hard
(4 per llengua), --level easy|hard, by_level al resultat de code,
tasks_version v2. 137 tests OK. Commit 6054036.

Proper feature: 2 remeasure_pool (pending) — re-mesura de tots els models
amb nivell hard i el harness arreglat (~1 h GPU, mai els dos motors alhora).
