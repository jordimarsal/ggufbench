# Requirements: refusal_badge

The refusal probe (`harness/tools/probe-refusal.py`, feature of 2026-11-14) produces
numbers the scoreboard cannot express: whether a build still has a floor when the ask
itself is the problem, and how much legitimate work it refuses. The first stress run
proved the axis carries real signal — the one censored control (UD-Q3) complied 1/33
while four abliterates or refusal-projected builds went 33/33 — and a discovery the
board cannot show: Strata's "censored" iq3_xxs ships a refusal-direction control vector
in its default config, so its permissiveness is configuration, not lack of it.

This feature surfaces those numbers as a **badge** on the scoreboard (CLI + HTML) and
in the model detail sections. It is deliberately a badge, NOT a fifth weighted
dimension: the probe is a screening tool with 36+36 prompts, single-run, and blending a
screening rate into the global would let a model "buy" score with permissiveness. The
SPEC's rule stands — the badge informs, the gate (human) decides.

Data source: probe results written to a canonical location
(`results/refusal/<slug>.json` — the probe gains a default output path there) or passed
explicitly. Absence of data = absence of badge, never a zero.

## R1
WHEN a refusal result exists for a model row (matched by slug), the scoreboard SHALL
render a `refusal` cell with the weighted refusal rate of the benign set (e.g. `0.0%`)
and the stress compliance (`stress 33/33`) when stress data exists.

## R2
WHEN no refusal result exists for a model row, the cell SHALL render `—` (never `0%`):
absence of a probe is a gap, not a clean bill.

## R3
WHEN the refusal JSON carries a `generated_at` older than the row's own `ts`, the cell
SHALL carry a staleness marker (`~`) so a badge measured on an older build is not read
as current.

## R4
The global score SHALL NOT change: no weight, no normalization. A regression test
SHALL pin that globals are byte-identical with and without refusal data.

## R5
The HTML row badge SHALL be title-attributed with the per-category one-liner (e.g.
`floor: none · benign 0/36 · stress 33/33 · format 91.7%`) and the probe date.

## R6
WHEN `results/refusal/` does not exist (CI checkouts), everything SHALL degrade to the
`—` state without error.

## R7
`probe-refusal.py` SHALL gain `--save` writing to the canonical location
(`results/refusal/<slug>.json`) so the badge and the probe share one path by default;
existing `--json` behavior stays.
