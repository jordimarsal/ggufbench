# Design: remeasure_pool

Operations feature: there is no new code to produce (the harness already supports
everything); the design is the **execution protocol** and the checks that make the
result trustworthy.

---

## Protocol

1. **Pre-flight (entry gate):**
   - No live servers: `pgrep -af "llama-server|engine/strata"` empty and ports 8999/8080
     free (never both engines at once — R2).
   - `python3 -m unittest discover` green before burning GPU.
   - Backup of the current pool to
     `results/models/pool.pre-remeasure.jsonl` (cheap rollback if the GPU dies mid-run).
2. **llama batch (R1, R2):** `python3 -m benchmark.run --models all` from the workspace
   root. The harness starts/stops `llama-server` per model, sequentially.
   Progress on stderr → captured to `harness/logs/remeasure_pool/batch-llama.log`.
3. **Strata batch (R1, R2):** `python3 -m benchmark.run --engine strata --models
   iq3_xxs` → `harness/logs/remeasure_pool/batch-strata.log`. Started only when the
   llama batch has finished and no llama-server process remains alive.
4. **Verification (R3, R4):** count pool entries per `ts` (single session),
   check every entry has `by_level` and `tasks_version: "v2"`, regenerate
   `results/report.html` and verify the mixed-conditions banner does NOT appear.
5. **Evidence (R5):** final scoreboard, ts list per model and check results →
   `harness/logs/remeasure_pool/summary.log` + table in the Completion Gate.

## Public signatures

(no new product code: none. Uses the existing CLI.)

## Exceptions and error cases

| Case | Behavior | Req |
|---|---|---|
| A specific model fails to load (OOM, broken GGUF) | `serve_failed`: recorded, continue with the rest; the pool keeps its old entry marked as failed → reported at the gate | R1 |
| GPU runs out of memory mid-run | Stop the run, restore `pool.pre-remeasure.jsonl`, re-plan (fewer models per invocation) | R2 |
| Strata takes longer than 600 s to load | The harness ready-check already covers it; if it fails, report and retry once | R1 |
| A model leaves an entry with an empty `by_level` | Detected in verification (step 4) and that model re-run alone | R4 |

## Discarded alternatives

1. **Re-measure only the "important" models** — would leave the pool with two conditions and
   a permanent banner: discarded (the goal is a homogeneous scoreboard).
2. **A single invocation measuring llama and Strata together** — the CLI is one engine per run
   by design (same discipline as never-both-at-once): discarded.
3. **Delete the pool and let the re-run rebuild it** — loses the `results/runs/`
   history and the cheap rollback: discarded.
4. **`--quick` to save time** — measures 1 task per dimension: not a re-measure,
   it is a smoke: discarded.
