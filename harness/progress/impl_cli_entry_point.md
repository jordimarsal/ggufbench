# Implementation: cli_entry_point

feature: cli_entry_point

**Session:** 2026-11-08 (hybrid — one agent, sequential roles)
**Spec Gate:** approved by the human (§15 de drafts/10-estol-malla-equips.md, pas 0
demanat explícitament) → in_progress

## Batches (evidence in harness/logs/cli_entry_point/)

| Batch | Tasks | Log |
|---|---|---|
| 1 | T1 (test de contracte RED) + T2 (pyproject GREEN) + T3 (regressió `python3 -m`) + T4 (gate + instal·lació) | batch-1.log (517 tests OK, skipped=1; traceability 4/4 PASS) |

Decisió respecte al pla original (§15): `py_modules` és inviable — els mòduls s'importen
relativament (`from . import config`). L'arrel del repo ÉS el paquet: mapping
`package-dir {ggufbench = "."}` + `packages = ["ggufbench"]`, i el target del script és
`ggufbench.run:main` (no `run:main`).

## Traceability

| Requirement | Test(s) | Implementation file(s) | Status |
|-------------|---------|------------------------|--------|
| R1 | test_script_is_declared_and_target_resolves test_package_is_declared_with_an_explicit_root_mapping | pyproject.toml `[project.scripts]` + `[tool.setuptools]` | done |
| R2 | test_scoreboard_runs_from_the_workspace_root | run.py main (sense canvis) | done |
| R3 | test_paths_resolve_inside_the_checkout | config.py (sense canvis); verificació manual del venv de l'eina al checkout de bench → BASE_DIR/MODELS_DIR/RESULTS_DIR/SERVER_BIN correctes (batch-1.log) | done |
| R4 | test_install_pulls_no_third_party_dependencies | pyproject.toml (cap `[project] dependencies`); gate complet harness/init.sh verd sense GPU (batch-1.log) | done |
