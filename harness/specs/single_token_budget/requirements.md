# Requirements: single_token_budget

Amb seed/temp fixos, max_tokens es un sostre i no un objectiu: l'escala
2048->4096->8192 reprodueix la mateixa generacio que un unic intent a 8192, pero afegeix
1-2 peticions mortes per tasca amb models que pensen. (Proposta del revisor: "jo
comencaria a 8192".)

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
