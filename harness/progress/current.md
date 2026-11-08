# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** _none_ (10 features `done`; `lora_eval` = feature 7
  `spec_ready`, waiting on its Spec Gate; `grammar_toolcalls_ab` and
  `kv_cache_f16_ab` = features 10/11 `pending`)
- **Started:** 2026-11-08
- **Agent:** in-session

## Plan

_Describe in 3-5 bullets what you will do before touching code._

- `cli_entry_point` (feature 12): exposable com a paquet amb script de consola
  `ggufbench` — pas 0 de la fase 4b d'estol (el nodelet executa el binari).
  TDD: contracte del pyproject + regressió `python3 -m`, instal·lació editable
  verificada al checkout de bench.

## Log

_Note each significant step: files created, decisions, blockers._

- **2026-11-08 — cli_entry_point shipped (feature 12, done):** `pyproject.toml`
  amb `[project.scripts] ggufbench = "ggufbench.run:main"` + mapping
  `packages=["ggufbench"]`/`package-dir {ggufbench="."}` (el pla original de
  py_modules era inviable: imports relatius). 5 tests nous a
  `tests/test_packaging.py` (contracte, mapping, regressió `-m`, geometria,
  sense dependències). Instal·lat `uv tool install --editable` des del checkout
  de bench: `ggufbench --scoreboard` llegeix el pool real i la geometria
  (BASE_DIR/MODELS_DIR/RESULTS_DIR/SERVER_BIN) queda al lloc de sempre.
  Traceability 4/4 PASS; gate verd (517 tests). Commit `0ccc4b0` + tancament.
- Session 2026-11-05 closed: `context_receipts` shipped and marked `done`
  (full summary in `history.md`).
- **2026-11-06 — glossary + scoreboard sync:** «la Banu» written into `AGENTS.md`
  (project section) = the bench machine, the other active checkout — decided with
  the human after using the nickname undefined in session. Same session: README
  scoreboard refreshed with the 0.9.0 re-measure + recovered pool, 2 `model`
  fields normalized, `results/compare.html` back in `.gitignore` (summary in
  `history.md` at close).

## Next step

_If the session is interrupted, this is what the next session should do first._

_Pending: `lora_eval` waits on its Spec Gate; `grammar_toolcalls_ab` and
`kv_cache_f16_ab` wait in `pending` (spec mode is their next step). Inherited
from earlier sessions: gemma ON + Strata ON caps pass, Heretic ON re-measure at
147456, and the stale traceability identifiers in `discriminative_tasks` /
`hard_code_tier` impl tables (see `history.md` tail)._
