# Design: hard_code_tier

Cobreix R1-R8 de `requirements.md`. Principi guia: el nivell hard són **més tasques de
code**, no una dimensió nova — la mínima superfície possible.

---

## Files to create or modify

| Fitxer | Canvi |
|---|---|
| `tasks_loader.py` | Cada task dict guanya la clau `level` (R1); `load(dim, level=None)` filtra per nivell (R2) |
| `run.py` | Nou flag `--level {easy,hard}` aplicat només a code (R2); `tasks_version = "v2"` (R7) |
| `graders.py` | Les entrades de traça de code guanyen `level`; el resultat de code guanya `by_level` (R3, R4) |
| `tasks/code/<lang>/*_hard.py` (x16) | 4 tasques noves per llengua, `ID` acabat en `_hard` (R6) |
| `html_report.py` | La fitxa de condicions de cada model mostra `code easy/hard` quan n'hi ha (R5) |
| `docs/SPEC.md`, `AGENTS.md` | Documentar la convenció `_hard` i el flag `--level` (R1, R2) |
| `tests/test_tasks_loader.py`, `tests/test_run_cli.py`, `tests/test_graders.py`, `tests/test_html_report.py`, `tests/test_hard_tasks.py` (nou) | Tests de tots els requisits |

---

## Public signatures

```python
# tasks_loader.py
def load(dim: str, level: str | None = None) -> list[dict]:
    """Com abans; amb level=("easy"|"hard") filtra per la clau level del task dict.
    Els task dicts de code porten level: "hard" si ID acaba en _hard, sinó "easy"."""


# graders.py  (canvi dins del dict de retorn de grade_code)
#   trace[i]["level"] -> "easy" | "hard"
#   resultat["by_level"] -> {"easy": float, "hard": float}   # només nivells presents

# run.py
#   ap.add_argument("--level", choices=["easy", "hard"], default=None)
#   aplica el filtre NOMÉS a la dimensió code (abans de _limit)
#   result["tasks_version"] = "v2"
```

---

## Exceptions and error cases

| Cas | Comportament | Req |
|---|---|---|
| `--level hard` i zero tasques hard carregables | Print d'avís a stderr i dimensió code sense tasques (score 0, `excluded` no aplicable) | R2 |
| `--level` donat sense `code` a `--dims` | Ignorat amb un avís únic a stderr | R2 |
| Task file sense `ID` (fallback per defecte del loader) | `level = "easy"` | R1 |
| Model antic del pool sense `by_level` | `html_report` mostra només el score agregat, sense secció easy/hard | R5 |
| Tasca hard amb TEST_CODE que no compila/executa | La mateixa mecànica d'exclusió de code (CODE_LADDER, transient) — cap tracte especial | R3 |

---

## Discarded alternatives

1. **Sub-dimensions `code_easy`/`code_hard` amb pesos propis** — canvia el GLOBAL i
   trencaria la comparabilitat del pool: descartada (decisió de l'usuari: plegades).
2. **Runs separades amb slug `-hard`** — duplica el temps de re-mesura i parteix el
   marcador en dos: descartada.
3. **Nivell com a directori (`tasks/code/hard/<lang>/`)** — la convenció de niat és
   per-llengua i el loader és de nivell únic; el sufix `_hard` a l'ID manté "un fitxer =
   una tasca" i fa el filtre trivial: descartada.
4. **No pujar `tasks_version`** — el pool no podria distingir condicions pre/post
   (MILLORA §C7): descartada.
5. **Solution de referència dins de cada tasca hard per testar-la en unitaris** — posaria
   la solució a maniga dels models (el PROMPT i el TEST_CODE són dades que alguns
   servidors enregistraran); la validació d'una tasca hard és manual en crear-la +
   test estructural del loader: descartada.

---

## Tasques hard: criteri de contingut (R6)

Per llengua, un per patró — el naive falla per disseny:

1. **Fix d'un bug subtil** (off-by-one, mutabilitat, condició de cursa simple).
2. **Optimització amb test de màxim d'operacions/temps** (el TEST_CODE inclou una cota).
3. **Implementació d'algorisme no-trivial especificat** (parsing, estat, memoització).
4. **Refactor amb tests que fixen comportament** (API donada, no negociable).

Cada fitxer: `ID = "<nom>_hard"`, `PROMPT` en català, `TEST_CODE` auto-contingut que
imprimeix `OK` només si tot passa (la mecànica actual dels executors).
