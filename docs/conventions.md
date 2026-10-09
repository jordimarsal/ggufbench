# Conventions

Aquest document defineix les convencions del projecte. L'objectiu és l'homogeneïtat:
qualsevol persona (o agent) pot obrir qualsevol fitxer i entendre'n l'estructura, el
nom i la intenció sense aprendre un estil nou.

---

## Llengües

- **Codi i identificadors:** anglès.
- **Comentaris, specs de tasques i docs del projecte (SPEC, MILLORA):** català.
- Els comentaris expliquen el **per què** d'una decisió de mesurament o un compromís;
  el *què* l'ha de dir el codi.

---

## Style Rules

- **Python 3.12, stdlib pur:** cap dependència externa (ni pytest, ni requests, ni
  pyproject). La suite corre amb `python3 -m unittest discover -s benchmark/tests -t .`
  des de l'arrel del workspace (`/home/jordi/ia/llama/`), mai des de dins del paquet.
- **Format:** PEP 8, línies ~100 col., indentació 4 espais. Sense formatter configurat:
  l'homogeneïtat la marca el codi existent (obré un mòdul i imita'l).
- **Complexitat:** funcions curtes, early returns, sense `try/except` niuats. Els
  `except` capturen tuplets explícits (`_TRANSIENT` a `graders.py`) i mai a seques.
- **Type hints:** graduals (MILLORA §D3). Obligatoris a les funcions de puntuació
  (`report._scores`, `report._global_score`, `client.parse_timings`, `graders._args_equal`);
  opcionals a la resta fins que `mypy` entri a CI.

---

## Naming Rules

- Mòduls i funcions: `snake_case`. Classes: `CapWords`. Constants: `MAJUSCULES_AMB_GUIONS`.
- Tests: `tests/test_<modul>.py` mirant el mòdul; mètodes `test_<comportament>`.
- Un concepte, un nom: `pool` (les entrades), `run` (una execució), `task` (una tasca),
  `dim` (una de les 4 dimensions). No usar sinònims.
- Els booleans es llegeixen com a predicats: `passed`, `excluded`, `lower_is_better`.

---

## File Structure

- **Paquet pla:** els mòduls (`run.py`, `server.py`, `client.py`, `graders.py`,
  `agent.py`, `executors.py`, `tasks_loader.py`, `report.py`, `html_report.py`,
  `token_budget.py`, `code_extract.py`, `config.py`) a l'arrel del paquet — no `src/`.
- **Tasques:** `tasks/<dim>/...` com a fitxers de constants; `code/` i `agent/` niats per
  llengua. El loader salta `_prefix` i `__init__.py`.
- **Resultats (gitignored):** `results/models/pool.jsonl` (upsert per slug),
  `results/runs/` (històric append-only), `results/token_budgets.json`,
  `results/report.html` (generat).

---

## Testing Rules

- **unittest stdlib** (no pytest al projecte). Els tests no han de tocar GPU ni xarxa:
  serveis fake (`FakeClient`), i `config.override()`-style amb `setUp`/`tearDown` mentre
  no existeixi (MILLORA §D1).
- Cada bug fix inclou el test que l'hauria encertat.
- Un test que només comprova que no llança excepcions no és un test.

---

## Commit Rules

- **Conventional Commits**, enforcing per `.git/hooks/commit-msg`
  (`harness/tools/commit-msg`): `feat(engine): ...`, `fix(tools): ...`,
  `chore(harness): ...`. Commits granulars: una intenció per commit.
