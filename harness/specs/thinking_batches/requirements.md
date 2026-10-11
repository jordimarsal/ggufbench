# Requirements: thinking_batches

The R5 smoke of `discriminative_tasks` (2026-10-10) shows a 27B exhausting
`out_tokens=16384` with empty text on 7/12 expert tasks, while Strata measures with
`enable_thinking: False` under the documented assumption "same as the other models".
If hybrids think and Strata does not, conditions are already unequal. Also, the
16384 budget has become small for expert tasks (reviewer decision:
start at 32768) and exclusions are invisible in the aggregates (Table 1/HTML show an
identical `100%` with 0 or 7 excluded). This feature resolves all of that before the
re-measure.

## R1
The system SHALL accept a `--thinking on|off` run option (default `off`) for both
engines, apply it through the engine's supported mechanism, and record the mode as
`thinking` in every new result.

## R2
WHEN two results share the model slug but differ in `thinking`, the system SHALL
retain both: the pool upsert key SHALL be `(slug, thinking)`, token-budget entries
SHALL be keyed by `(model, thinking)`, and runs history filenames SHALL distinguish
the mode. Rows without a `thinking` field (legacy pool) SHALL render unlabelled.

## R3
The code generation budget SHALL start at 32768 tokens in a single attempt; stored
budgets from the 16384 era SHALL be ignored; the clock cap SHALL cover a full
32768-token generation at the slowest observed generation speed.

## R4
The scoreboard (Tables 1/2/3) SHALL render think/no-think entries as separate rows
labelled with their mode, and the HTML report SHALL badge each row likewise. The
mixed-conditions banner logic SHALL remain date-driven (no change).

## R5
Table 1 code cells and HTML model cards SHALL display the excluded-task count next
to the score. Per-task detail keeps its existing `[exclo]` + reason (no change).

## R6
Both batches SHALL run the same dims, languages and levels with the same protocol.
Thinking overhead on small budgets is recorded data (exclusions stay exclusions).

## R7
The system SHALL NOT modify weights, folding, or score semantics: exclusions never
become fails and the folded score still averages scorable tasks only.
