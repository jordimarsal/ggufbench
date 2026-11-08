# cli_entry_point — Design

## Decisió: paquet, no `py_modules`

El pla original (§15) proposava `[tool.setuptools] py_modules=[…]`, però els mòduls
s'importen **relativament** (`from . import config` a run.py i tots els altres): com a
mòduls de nivell superior trencarien. L'arrel del repo ÉS el paquet (`__init__.py`
buit a l'arrel): el mapping correcte és declarar `ggufbench` com a paquet i mapar-lo
a `.`.

```toml
[project.scripts]
ggufbench = "ggufbench.run:main"

[tool.setuptools]
packages = ["ggufbench"]        # explícit: l'auto-descoberta veuria layout pla i dubtaria

[tool.setuptools.package-dir]
ggufbench = "."
```

Conseqüències:

- Només s'empaqueten els `.py` de l'arrel; subdirs (`tests/`, `tasks/`, `harness/`,
  `results/`) queden fora — són dades del checkout, no del paquet.
- El target del script és `ggufbench.run:main` (el pla deia `run:main`, que presumia
  py_modules).

## Instal·lació al checkout de bench

`uv tool install --editable <checkout>`: l'editable fa que `ggufbench/config.py`
resolveixi `__file__` al checkout, i per tant `BASE_DIR = <pare>` / `MODELS_DIR =
<pare>/models` / `RESULTS_DIR = <checkout>/results` — exactament la mateixa geometria
que `python3 -m ggufbench.run` avui (regla de l'arrel del workspace, AGENTS.md).
Una instal·lació NO editable treuria els paths a site-packages: es descarta.

Amb `--editable`, els `git pull` futurs del checkout es reflecteixen sense reinstal·lar.

## Tests

`tests/test_packaging.py`:

1. **Contracte del script** (R1): llegeix `pyproject.toml` amb `tomllib`, comprova que
   `project.scripts.ggufbench == "ggufbench.run:main"` i que el mòdul+atribut resolen
   via `importlib`. Guarda contra typos al string del pyproject.
2. **Regressió `python -m`** (R2): subprocess `[sys.executable, "-m", "ggufbench.run",
   "--scoreboard"]` amb `cwd = pare del repo`, rc 0. És la invocació que el checkout de
   bench fa servir avui.

R3 es verifica manualment després d'instal·lar (`ggufbench --scoreboard` contra el pool
real); R4 amb `harness/init.sh`.

## Riscos

- setuptools >68 i el mapping `package-dir {ggufbench = "."}` amb editable (PEP 660):
  suportat; si fallés, el fallback seria una gitignore shim — però no cal provar-ho
  fins que falli.
- El suite té un subprocess nou (~1–2 s): assumible sobre els ~17 s actuals.
