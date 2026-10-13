# ADR-0008: KV cache baseline is q8_0, aligned with the startup script

- **Date:** 2026-10-13
- **Status:** accepted
- **Feature:** project-level

## Context

The harness baseline in `config.CACHE_FLAGS` said `q4_0/q4_0` since the first
pool, but the server has been launched with `--cache-type-k/v q8_0` from
`start-dev-ai.sh` for the recent runs. The two sources disagreed: a reader who
cloned the repo and ran the harness without the external script would get
`q4_0` and different numbers, while the published scoreboard was measured with
`q8_0`. `model_config_flags` in each result records what the model actually
ran with, so the data was never wrong; the documented baseline was.

## Decision

The harness baseline moves to `q8_0/q8_0` (`config.CACHE_FLAGS`), matching the
startup script and the runs behind the current scoreboard. Model profiles can
still override the cache types last, and the existing dedup rule keeps them
from being applied twice.

This documents the condition that was already in effect. It is not a change of
conditions, so the existing pool does not need a re-measure under AGENTS.md
rule 2. Any future run that wants `q4_0` uses a model profile, and the choice
appears in `model_config_flags`.

## Alternatives considered

Leave `config` at `q4_0` and document the script as the source of truth.
Rejected: the repo would keep publishing a baseline its own numbers do not
reproduce.

Re-measure the whole pool after the change. Rejected as unnecessary: the
measured condition does not change. Rows were already produced with `q8_0`.

## Consequences

Cloning the repo and running the harness reproduces the published conditions
without the external script. `q8_0` uses more KV memory per token than `q4_0`,
so profiles that set their own `-c` still need to pass the context audit.
Cheap to reverse: one line in `config.py` plus this record.
