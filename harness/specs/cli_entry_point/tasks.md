# cli_entry_point — Tasks

> Batches: un de sol (feature petita). Evidència: `harness/logs/cli_entry_point/batch-1.log`.

- [x] T1: `tests/test_packaging.py` amb el test de contracte del script (R1) — RED
      primer: el pyproject encara no té `[project.scripts]`.
- [x] T2: `pyproject.toml` amb `[project.scripts]` + mapping de paquet — GREEN.
- [x] T3: regressió `python3 -m ggufbench.run --scoreboard` (R2) dins el mateix fitxer
      de tests.
- [ ] T4: `harness/init.sh` verd (R4) + verificació d'instal·lació al checkout de bench
      (R3, sortida al log del batch).
