# Requirements: context_receipts

A dev.to reader (2026-11) asks how much context a local model BURNS to pass the
same tasks: the agent loop re-sends the whole conversation every turn, so two
models with the same pass rate can cost very differently in sent tokens. Today
the trace records `out_tokens` (completion_tokens, `graders.py`) and the
timings (`gen_tps`, `prompt_tps`, `prompt_ms` via `client.parse_timings`), but
`prompt_tokens` — the tokens actually SENT per call — is counted nowhere: no
scoreboard column, no per-session aggregate in the agent loop. This feature
records receipts (in_tokens per call, tokens per agent session) next to the
pass rate, without touching scores, weights or pool keys.

## R1
The system SHALL expose `client.parse_usage(resp)` returning `in_tokens` as
`usage.prompt_tokens` of the response, falling back to
`round(prompt_tps * prompt_ms / 1000)` from the timings when usage is absent,
and returning None when neither source is present.

## R2
WHEN a chat call produces a response, every trace entry of the four dimensions
(tools, code, agent, speed) SHALL carry `in_tokens` next to `out_tokens` /
`gen_tps`. IF a call fails with a transport error, its (excluded) entry SHALL
omit the receipt, exactly as it omits `out_tokens` today.

## R3
The agent loop SHALL record the `in_tokens` of every turn and SHALL accumulate
`session_in_tokens` as the sum over the episode's turns, so the sum reflects
the conversation growing as the loop re-sends it; `grade_agent` SHALL write
both (per-turn list and session sum) into the task's trace entry.

## R4
Every dimension result SHALL carry receipt rollups with the same pattern as the
`gen_tps` aggregates: mean and median `in_tokens` per call for tools and code,
and mean and median tokens per session (`avg_session_in_tokens`,
`median_session_in_tokens`) for agent, computed over every non-excluded call
across all runs.

## R5
WHEN the scoreboard or the HTML report is rendered, each row SHALL show the
receipt rollups (tools in/call, code in/call, agent in/session), rendering '?'
for a row that predates the field. The receipts SHALL NOT enter the picker
sort keys or the compare page.

## R6
The docs SHALL describe the receipts pipeline (`docs/SPEC.md`: a context
receipts section; client and grader sections updated), and the unittest suite
SHALL stay green with the new fake-client tests (test_client.py /
test_graders.py / test_agent.py patterns).

## R7
The system SHALL NOT modify weights, folding, score semantics, or pool keys:
receipts are recorded metadata, not a pool condition, and pass/time numbers
stay byte-comparable for rows measured the same way.
