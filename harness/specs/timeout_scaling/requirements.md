# Requirements: timeout_scaling

With the fixed 60 s timeout, slow thinking models (38-44 t/s) run out of coverage on
hard tasks: the timeout expires while they are still legally generating tokens. The real
budget of a code task must be in tokens (same for all models) and the clock only an
anti-hang guard derived from the measured speed.

## R1
The system shall compute the per-attempt code chat timeout as
`code_timeout(budget, gen_tps) = clamp(90, 60 + (budget / gen_tps) * 1.25, 600)` seconds,
and shall use 90 seconds when no `gen_tps` is available.

## R2
The system shall pass that timeout to every chat attempt of the code escalation ladder
(2048, 4096, 8192 tokens), while speed, tools and agent dimensions keep their existing
timeouts.

## R3
The system shall keep recording timeouts as exclusions (never as fails): only the wait
changes, not the score semantics.

## Retired requirement (2026-10-09)

The former fourth requirement (recording the decision as ADR-0001) is retired: an ADR is
not verifiable by test (EARS rule 2) and is therefore not a valid requirement. ADR-0001
exists as an artifact of `design.md`/T3 in `harness/decisions/` and is reviewed in the
review. IDs are not reused.

## R5
The unit suite shall cover the timeout formula (floor, ceiling, no-tps fallback) and
that `grade_code` hands the scaled timeout to the client.
