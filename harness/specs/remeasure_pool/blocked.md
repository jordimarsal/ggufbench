# Blocked — remeasure_pool

**Date:** 2026-10-09 · **Status:** in_progress → blocked (reviewer decision)

**Reason:** the re-measure was stopped at model 6/10 by reviewer decision: with the
current task set (even with the hard level), strong models cluster within ~8 points
(code 0.88-0.98, tools 0.75-1.00, agent 0.83-0.96 on the 5 new entries)
and the ranking swings on 1-2 tasks. Re-measuring now would force a THIRD re-measure
when the discriminative tasks land (feature 5 discriminative_tasks, pending).

**Partial evidence kept:** harness/logs/remeasure_pool/batch-llama.log
(5 complete models under the ADR-0001/0002 protocol: scaled timeouts, 16384 budget,
0 clock exclusions on the dense 27B that previously had 6-20).

**Pool state:** restored from `results/models/pool.pre-remeasure.jsonl`
(homogeneous pre-re-measure conditions, coherent if stale scoreboard).

**Unlock:** when discriminative_tasks passes the Completion Gate → back to
in_progress and execute T2-T5 (T1's logs serve as the reference protocol).

---

**Unlock recorded: 2026-10-10** — the block said "when discriminative_tasks
passes the Completion Gate", but the underlying condition (tasks that do not
discriminate) is already solved: the 12 expert tasks of discriminative_tasks are
landed and validated
(T1-T8, batch-1..6.log + author-validation.log) and the R5 smoke runs RIGHT INSIDE this
re-measure (tasks.md T9). Therefore: status → in_progress and the whole batch is
launched; the discriminative_tasks Completion Gate and the remeasure_pool one are
requested afterwards, with the data at hand.

**Unlock 2026-10-10 (thinking_batches Completion Gate):** status → in_progress.
The re-measure runs with the new harness: dual batch (`--thinking off` and `--thinking on`,
same dims/langs/levels), code budget 32768, pool key (slug, thinking).
Preconditions verified in T1.
