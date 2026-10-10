# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** remeasure_pool (id 2, in_progress — desbloquejat 2026-10-10)
- **Started:** 2026-10-10
- **Agent:** hybrid (un agent, rols sequencials)

## Plan

- T1 pre-flight (servidors morts, ports lliures, suite verda, pool homogeni v1,
  perfils `-c`, config Strata, sonda del kwarg contra llama-server) → preflight.log.
- T2 batch llama OFF (10 models, dims completes, tots els nivells) → batch-llama-off.log.
- T3 batch Strata OFF (`iq3_xxs`, només quan cap llama-server quedi viu) → batch-strata-off.log.
- T2b/T3b ídem amb `--thinking on` → batch-llama-on.log / batch-strata-on.log.
- T4 verificació (pool amb les dues claus, by_level, tasks_version, report sense
  banner espuri) + T5 summary.log + traçabilitat + Completion Gate.

## Log

- `thinking_batches` tancada (done, gate sense canvis, commit pendent de les actes).
- `remeasure_pool` → in_progress; `blocked.md` amb l'historial de blocatge+desbloqueig.

## Next step

Commit de les actes del gate (APPROVAL + completion-gate.md + traceability-check.txt
de thinking_batches) i T1 pre-flight.
