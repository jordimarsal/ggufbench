# Requirements: single_token_budget

With fixed seed/temp, max_tokens is a ceiling and not a target: the ladder
2048->4096->8192 reproduces the same generation as a single attempt at 8192, but adds
1-2 dead requests per task with thinking models. (Reviewer proposal: "I would start
at 8192".)

## R1
The system shall use a single per-task code token budget at the harness context ceiling:
`CODE_LADDER == [16384]` and `CODE_MAX_TOKENS == 16384` (CONTEXT_FIXED menys prompt), so
a task whose code block only appears after heavy thinking (8-16k tokens) resolves in a
single request.

## R2
The code trace shall record the completion token count (`out_tokens`) of every attempt
that got a response (with or without extractable code).

## R3
The system shall keep honouring stored budgets from `token_budgets.json`.

## R4
The unit suite shall cover the single-budget resolution, `out_tokens` recording, stored
budget honouring and the no-save-when-default-suffices case.
