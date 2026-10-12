# ADR-0003: The harness is Python stdlib only — zero `pip install` to run or test it

- **Date:** 2026-10-12
- **Status:** accepted
- **Feature:** project-level

## Context

A benchmark's credibility rests on anyone being able to reproduce it. Every
dependency added to the harness is friction at exactly that moment: a fresh
clone must resolve, pin and install packages before the first test runs, and
each one drifts (breaking minors, deprecated APIs) while nobody is looking.
The forces: portfolio portability (clone-and-run on any machine, often
offline), no dependency rot, "double click" reproducibility. The evidence that
this is already true: CI (`.github/workflows/ci.yml`) is checkout@v4 +
setup-python@v5 (3.12) + oven-sh/setup-bun@v2 — there is **no install step**;
the suite is 207 tests in ~2.8 s (measured 2026-10-12, OK, 2 skipped, no GPU);
every module under `ggufbench/` imports stdlib only (`json`, `urllib`,
`argparse`, `subprocess`, `pathlib`, `statistics`, ...).

## Decision

`ggufbench/` imports from the Python standard library only, and the test suite
must run on a bare `python3 -m unittest discover` — CI enforces it by not
having an install step. The only non-Python pieces are the *executed* world,
not imported code: the llama-server binary, `bun` for the typescript executors,
Temurin for java (those belong to the system under test).

## Alternatives considered

- **pydantic for result/pool schema validation** — install friction plus
  version drift for marginal gain over dicts + explicit field checks:
  discarded.
- **httpx/requests instead of urllib** — `client.py` is ~70 lines; urllib
  covers it, and a single dependency would still force the lockfile question:
  discarded.
- **rich for progress/table rendering** — stderr prints and the hand-rolled
  HTML report (`html_report.py`, escaping via `html.escape`) already do the
  job: discarded.

## Consequences

- Some hand-rolled code where a library would help: the argparse CLI
  (`run.py`), the HTML report, no declarative schema for `pool.jsonl` rows.
- The Strata server is exempt by design: the harness never imports it —
  `server.strata_python()` launches `serve/server.py` from Strata's own
  `.venv` (jinja2/numpy; the docstring records that system python fails with
  an immediate ImportError).
- CI stays trivial: no cache, no lockfile, no matrix; the bun step exists only
  because the tests execute typescript tasks.
- Reversibility: cheap — adding a dependency is one import away and nothing
  architectural prevents it, but each addition should re-justify this ADR
  first.
