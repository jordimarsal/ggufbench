# Requirements: remeasure_pool

The current pool mixes conditions: the 10 llama models ran with two impossible tasks
(get_env/get_time) and the broken java agent (0.00 for all); Strata is in there
measured post-fix but without the hard level. With the harness fixed and the hard level
available (tasks_version v2), the whole pool must be re-measured to have a homogeneous,
publishable scoreboard.

## R1
The system shall re-measure every model present in the pool at the start of the
re-measure (10 llama-server models + `strata-iq3_xxs`) with the current harness
(`tasks_version` v2, hard level included, no `--level`: easy + hard folded).

## R2
The system shall not run llama-server and Strata at the same time: the llama batch
(`--models all`) shall complete and stop its server before the Strata invocation starts.

## R3
When the re-measure finishes, the pool shall contain exactly the re-measured entries
(one per model, upsert per slug, no entries from a previous condition).

## R4
When the pool is regenerated, the system shall rebuild `results/report.html` from it, and
the mixed-conditions banner shall not appear (all entries from a single session).

## R5
The re-measure evidence (commands, start/end of each model, final scoreboard output)
shall be recorded under `harness/logs/remeasure_pool/` before requesting the Completion
Gate.
