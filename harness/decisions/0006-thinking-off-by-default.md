# ADR-0006: Thinking off by default; ON is a separate pool row, never mixed into the score

- **Date:** 2026-10-12
- **Status:** accepted
- **Feature:** thinking_batches

## Context

The R5 smoke of `discriminative_tasks` (2026-10-10) caught hybrid models
exhausting the code budget thinking alone (a 27B hit `out_tokens=16384` with
empty text on 7/12 expert tasks) while Strata measured with
`enable_thinking: false` — conditions were already unequal across engines.
The 2026-10-10 dual bank (60 code tasks × 11 models, both modes, one date;
the 12th model entered the same day as an ad-hoc pair) quantified the rest:
OFF excluded **0/660**; ON excluded **14/660**, 13 of them format failures
("no code block..." — prose, an empty reply or a wrong-language fence) and 1
a timeout; latency multiplied (UD-Q5_K_M speed turn 40 → 665 ms; median
paired out_tokens delta **+253 tok** over the 659 usable pairs, mean +1893).
Small task budgets (speed/tools 128/256 tokens) make it worse: a chain eats
the budget without answering (SPEC §2).

## Decision

`--thinking off` is the default for every run, on both engines, applied
through the request body: `config.thinking_body()` sends
`chat_template_kwargs: {"enable_thinking": false}` (`on` → `{}`, free) — the
same channel for both engines, and no model `.txt` can override it, unlike a
server flag. `on` is measured as a **separate pool row** keyed by
`(slug, thinking)`; the scoreboard splits modes into rows with a `THINK`
column and visible exclusion counts (AGENTS.md rule 3; feature
`thinking_batches` R1-R7).

## Alternatives considered

- **ON default** (factory behavior) — rejected: the scoreboard inflates via
  format collapse (13/660 format exclusions vs 0 OFF) and burns wall-clock on
  chains the tasks never read. The documented exception proves the point is
  per-model, not universal: Coder390-ON thinks 53% less than its 27B siblings
  (2,084 vs 4.2-4.4K tok/task) with 0 exclusions and code 0.95 — exactly why
  ON stays available as its own row.
- **Mixing modes in one score** (average or best-of) — rejected: never mix
  conditions; the mixed-conditions banner exists precisely for *accidental*
  mixing and stays date-driven.
- **Thinking controlled by a per-model server flag** — rejected: a flag is
  `.txt`-overridable, engine-asymmetric and invisible in the receipt; the body
  channel is uniform and recorded as `thinking` in every result.

## Consequences

- Two pool rows per model (24 rows today: 12 models × 2); token budgets keyed
  by `(model, thinking)` (`_schema = 2`, the 16384-era entries ignored); run
  filenames distinguish `-on`/`-off`.
- `THINK` column + `(N excl.)` in Tables 1/2/3 and badges in the HTML:
  exclusions are visible, not folded into an identical-looking `100%`.
- Legacy rows without a `thinking` field render unlabelled (tolerant read).
- Reversibility: cheap — the default is one constant
  (`config.THINKING_DEFAULT`); flipping it is a policy change that re-opens
  the comparison, not a code problem.
