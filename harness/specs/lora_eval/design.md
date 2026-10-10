# Design: lora_eval

## Fitxers a modificar

| Fitxer | Canvi |
|---|---|
| `config.py` | `load_model_config_args`/`_strip_infra`: la línia `--lora <fitxer>` del `.txt` surt de "flags lliures" i passa a tractar-se com a metadada (no duplicable amb la CLI; la CLI guanya). `LORA_DEFAULT = None`. |
| `server.py` | `build_args` afegeix `["--lora", <path>]` quan n'hi ha (després dels base flags, abans de l'extra del `.txt`); `ServerManager.__init__` valida que el fitxer existeix (`ValueError` si no) i registra `self.lora`. Strata: `ValueError` explícit ("LoRA fora d'abast a Strata"). |
| `run.py` | `--lora <gguf>` (default: el del perfil, si n'hi ha); passa la ruta a `_bench_one` → `ServerManager`; `result["lora"] = <stem>` quan n'hi ha. |
| `report.py` | `_key_of`: `(slug, thinking, lora)`; legacy sense `lora` = `(slug, thinking, None)` — igual que avui. `save_result`: filenames amb sufix `-lora` quan n'hi ha. |
| `html_report.py` | `_rows`: nom mostrat amb sufix ` [+LoRA <stem>]` quan n'hi ha; badge `lora:<stem>` al ranking i targeta (mateix patró que think). |

## Signatures noves

```python
# server.py
ServerManager(model_path, context_mode, port, engine, thinking="off", lora=None)
# run.py
ap.add_argument("--lora", default=None,
                help="adaptador LoRA GGUF per a llama-server (default: el del perfil)")
```

`result["lora"]` és el **stem** del fitxer (no la ruta): la meta ha de ser estable i
comparable. La ruta completa queda al `model_config_flags` que ja registra l'script
del servidor via stderr (no cal duplicar).

## Casos d'error

- `--lola` (typo) → argparse mor (choices de fitxer no aplicable; es valida a
  `ServerManager`).
- Fitxer LoRA inexistent → `ValueError` abans d'arrencar cap servidor.
- `--engine strata --lora x` → `ValueError` clar (R1).
- Files legacy: cap migració; l'upsert nou no les toca (mateix patró que thinking).

## Alternativa descartada

**Identificar el model+LoRA com a slug nou** (`<model>-<lora>`): sense duplicació de
perfil ni de flag, però trenca la comparabilitat per slug (el marcador no sabria que
és el mateix base model) i `--forget` del model base deixaria orfes les files LoRA.

## Tests

`test_lora_rejected_on_strata`, `test_lora_file_must_exist`, `test_lora_reaches_build_args`,
`test_lora_recorded_in_result`, `test_upsert_keeps_lora_rows`,
`test_legacy_lora_none_coexists`, `test_render_labels_lora_rows` (noms nous, cap renomenat:
cap traçabilitat antiga afectada).

## Architectural Decisions

### ADR-1: el LoRA és condició del pool, no part del slug
**Context:** comparar nu-vs-adapter exigeix que convigin files del mateix model base.
**Decision:** clau `(slug, thinking, lora)`; badge/sufix només visual.
**Alternatives considered:** slug sintètic (descartada: vegeu a dalt).
**Consequences:** mateix patró d'extensió que `thinking`; `forget` del base model
esborra també les seves files LoRA (comportament desitjat).

### ADR-2: la font del LoRA és el `.txt` del perfil o la CLI, mai hardcoded
**Context:** cada model pot voler un adaptador per defecte.
**Decision:** mateixa convenció que mmproj: perfil si no hi ha CLI.
**Alternatives considered:** directori convencional `models/lora/` amb auto-detecció
(descartada: màgia implícita; el perfil és l'única font de veritat de flags).
**Consequences:** cap canvi a scripts de serving; el `.txt` continua aplicant-se AL FINAL.
