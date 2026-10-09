# Design: discriminative_tasks

Cobreix R1-R6. El nivell expert reutilitza tota la maquinària del nivell hard
(`_hard`→`_expert`, `--level`, `by_level`); la peça realment nova és `EXTRA_FILES`
(R2) — suport multi-fitxer al sandbox de code.

---

## Files to create or modify

| Fitxer | Canvi |
|---|---|
| `tasks_loader.py` | El mapa de nivells guanya `_expert` → `"expert"`; cada task dict de code guanya `extra_files` (dict buit per defecte) |
| `run.py` | `--level` choices += `expert`; `tasks_version = "v3"` |
| `executors.py` | `run(lang, solution_code, test_code, timeout=30, extra_files=None)`: escriu `extra_files` al tempdir abans de solution+test (tots els 4 runners) |
| `graders.py` | `grade_code` passa `t.get("extra_files")` a `executors.run`; `by_level` ja és genèric (claus noves gratis) |
| `tasks/code/<lang>/*_expert.py` (x12) | 3 tasques per llengua (R3) |
| `html_report.py` | `by_level` ja es renderitza genèric — verificar que expert hi apareix (test) |
| `docs/SPEC.md`, `AGENTS.md` | Convenció `_expert`, `--level expert`, tasks_version v3 |
| `tests/` | loader/--level/executors-extra-files/by_level/html/estructura (patró hard_code_tier) |

---

## Public signatures

```python
# executors.py
def run(lang: str, solution_code, test_code, timeout: int = 30,
        extra_files: dict[str, str] | None = None) -> dict: ...

# tasks_loader.py  (task dict de code)
#   {..., "level": "easy|hard|expert", "extra_files": dict[str, str]}
```

---

## Exceptions and error cases

| Cas | Comportament | Req |
|---|---|---|
| `--level expert` sense tasques expert (repo antic) | Avís a stderr i dimensió sense tasques (patró hard) | R1 |
| `EXTRA_FILES` amb ruta amb `..` o absoluta | Rebutjada en carregar la tasca (loader valida claus de dict, mai rutes) — el sandbox escriu només noms plans | R2 |
| Col·lisió extra_file vs solution/test | `solution.*`/`test_*` guarden sempre (l'extra no pot anomenar-se així: validat al loader) | R2 |
| Tasca expert que un model resolt parcialment | TEST_CODE multi-part → falla (mai exclusió): la partial-solution resistance és el criteri de qualitat | R3 |

---

## Discarded alternatives

1. **Pujar el pes de code** — amaga la manca de discriminació, no la resol: descartat.
2. **Nivell expert a l'agent (repos més grans, més turns)** — valuós però és una altra
   dimensió i un altre sandbox: feature separada (segueix a MILLORA §C4).
3. **Puntuar l'eficiència de tokens** — ja registrada (`out_tokens`); puntuar-la seria
   una dimensió nova (R7 jubilat): descartat.
4. **Tasques amb sortida no determinista** (creativitat, disseny) — no verificables amb
   TEST_CODE: contradiu el principi data-as-code verificable: descartat.

---

## Criteri de contingut expert (R3)

Per llengua, 3 patrons — tots multi-part i amb context proveït:

1. **Mòdul sencer**: implementar 2-3 classes/funcions coordinades (~80-150 línies de
   solució esperada) amb TEST_CODE que prova les tres peces i les seves interaccions.
2. **Depuració sobre context real**: un fitxer de ~100 línies amb 3 bugs subtils
   (of-by-one, aliasing, estat compartit) incrustat al PROMPT o a EXTRA_FILES; el test
   falla amb qualsevol dels tres sense arreglar.
3. **Dades + robustesa**: processar un fitxer de dades lleig (EXTRA_FILES: CSV/logs amb
   casos vora, cometes, línies parcialment vàlides) amb contracte de sortida estricta.

La resistència a solucions parcials és el criteri d'acceptació: cada tasca s'valida
amb la solució de referència (OK) i amb solucions que resolen només 2 de 3 parts
(FALLA), abans de commitejar-la.
