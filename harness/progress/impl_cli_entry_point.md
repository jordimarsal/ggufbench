# Implementation: cli_entry_point

feature: cli_entry_point

**Session:** 2026-11-08 (hybrid — one agent, sequential roles)
**Spec Gate:** approved by the human (§15 de drafts/10-estol-malla-equips.md, pas 0
demanat explícitament) → in_progress

## Batches (evidence in harness/logs/cli_entry_point/)

| Batch | Tasks | Log |
|---|---|---|
| 1 | T1 (test de contracte RED) + T2 (pyproject GREEN) + T3 (regressió `python3 -m`) + T4 (gate + instal·lació) | batch-1.log (515 tests OK, skipped=1) |

Decisió respecte al pla original (§15): `py_modules` és inviable — els mòduls s'importen
relativament (`from . import config`). L'arrel del repo ÉS el paquet: mapping
`package-dir {ggufbench = "."}` + `packages = ["ggufbench"]`, i el target del script és
`ggufbench.run:main` (no `run:main`).

## Traceability

| Requirement | Test(s) | Implementation file(s) | Status |
|-------------|---------|------------------------|--------|
| R1 | TestConsoleScript.test_script_is_declared_and_target_resolves | pyproject.toml `[project.scripts]` | done |
| R1 | TestConsoleScript.test_package_is_declared_with_an_explicit_root_mapping | pyproject.toml `[tool.setuptools]` | done |
| R2 | TestModuleInvocation.test_scoreboard_runs_from_the_workspace_root | run.py main (sense canvis) | done |
| R3 | verificació manual (uv tool install --editable del checkout de bench; sortida a batch-1.log) | checkout de bench `~/ia/llama/ggufbench` | done |
| R4 | gate complet: harness/init.sh verd, sense GPU | harness/logs/cli_entry_point/batch-1.log | done |
