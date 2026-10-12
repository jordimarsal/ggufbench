# ADR-0007: Ports are infrastructure — fixed, harness-owned, filtered out of profiles

- **Date:** 2026-10-12
- **Status:** accepted
- **Feature:** project-level

## Context

The serving endpoint is the instrument, not a variable: a benchmark where each
model listens on its own port measures nothing except port numbers. Both
engines have fixed ports owned by the harness — llama.cpp
`config.PORT = 8999`, Strata `config.STRATA_PORT = 8080` — and the endpoint is
part of "same conditions" (SPEC §2). The exact failure mode this prevents
happened: on 2026-10-12 a hardcoded port literal in a bare `client.chat` had
already diverged and talked to the wrong server (recorded in the `client.py`
docstring; the D2 fix). A per-model `.txt` must never control infrastructure:
`server.py`'s comment is explicit — "a different --port would break the
ready-check".

## Decision

Infrastructure flags are harness property, enforced in both directions:
`server.build_args` strips `_INFRA_FLAGS = {"-m", "--model", "--port",
"--host"}` from every profile before composing the command line (the harness
injects `-m` and `--port` itself), and the Strata contract is identical —
`strata_command()` passes `--port` explicitly regardless of what the JSON
config says. Client-side, `client.chat` resolves its default `base_url` from
`config.PORT`, never a literal; the Strata path passes its URL explicitly.
Model profiles compete on model flags only.

## Alternatives considered

- **Ephemeral ports** (a free port per start) — rejected: receipts and
  debugging get harder (which server answered this run?), firewall noise
  appears, and the ready-check gains a race against the port probe.
- **Per-model ports** (one per `.txt`) — rejected: pointless variability;
  nothing measured depends on the port number, and collisions would become
  model-dependent.

## Consequences

- Ports must be free before a run: `ServerManager` owns the lifecycle, and the
  2026-10-12 incident shows the cost of a foreign process on 8999 — the client
  answers, but it is the wrong server.
- Receipts stay meaningful: `model_config_flags` records what the profile
  actually contributed, and it can never include the endpoint.
- A bare `client.chat()` in scripts and tests always hits the config port —
  single source of truth instead of a second place to drift.
- Reversibility: cheap — two constants and one filter set; the binding
  constraint is ops (free the ports before a run), not the design.
