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

## 2026-10-09 — timeout_scaling (done)

Feature 3 (exprés, dins la re-mesura): 60 s fixes deixaven sense cobertura les tasques
hard als models lents que pensen (20 exclusions a mig run). Nou code_timeout(budget,
gen_tps) = clamp(90, 60 + (budget/gen_tps)*1.25, 600): pressupost en tokens igual per
a tothom, rellotge anti-penjam derivat de la velocitat mesurada; timeouts segueixen
sendo exclusions. ADR-0001. Run de remeasure_pool avortada i repetida amb el protocol
nou. 139 tests OK, tracabilitat 4/4 PASS.

## 2026-10-09 — single_token_budget (done)

Feature 4 (proposta del revisor): un unic pressupost de 16384 tokens (sostre de context)
en lloc de l'escala 2048->4096->8192. Amb seed/temp fixos el score es identic (prefix
determinista) pero s'eliminen 1-2 peticions mortes per tasca amb models que pensen, i
la cua de pensament llarg (8-16k) queda mesurada. out_tokens registrat a la tracca com
a metrica d'eficiencia. ADR-0002. 139 tests OK, tracabilitat 4/4 PASS.
