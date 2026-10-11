# Design: lora_eval

## Files to modify

| File | Change |
|---|---|
| `config.py` | `load_model_config_args`/`_strip_infra`: the `.txt`'s `--lora <file>` line leaves the "free flags" set and becomes metadata (not duplicated with the CLI; CLI wins). `LORA_DEFAULT = None`. |
| `server.py` | `build_args` adds `["--lora", <path>]` when present (after base flags, before the `.txt` extra); `ServerManager.__init__` validates the file exists (`ValueError` if not) and records `self.lora`. Strata: explicit `ValueError` ("LoRA out of scope in Strata"). |
| `run.py` | `--lora <gguf>` (default: the profile's, if any); passes the path to `_bench_one` → `ServerManager`; `result["lora"] = <stem>` when present. |
| `report.py` | `_key_of`: `(slug, thinking, lora)`; legacy without `lora` = `(slug, thinking, None)` — same as today. `save_result`: filenames with a `-lora` suffix when present. |
| `html_report.py` | `_rows`: displayed name with a ` [+LoRA <stem>]` suffix when present; `lora:<stem>` badge in the ranking and card (same pattern as think). |

## New signatures

```python
# server.py
ServerManager(model_path, context_mode, port, engine, thinking="off", lora=None)
# run.py
ap.add_argument("--lora", default=None,
                help="GGUF LoRA adapter for llama-server (default: the profile's)")
```

`result["lora"]` is the file's **stem** (not the path): the meta must be stable and
comparable. The full path stays in `model_config_flags` already recorded by the server
script via stderr (no duplication needed).

## Error cases

- `--lola` (typo) → argparse dies (file choices not applicable; validated in
  `ServerManager`).
- Non-existent LoRA file → `ValueError` before starting any server.
- `--engine strata --lora x` → clear `ValueError` (R1).
- Legacy rows: no migration; the new upsert does not touch them (same pattern as thinking).

## Discarded alternative

**Identifying model+LoRA as a new slug** (`<model>-<lora>`): no profile or flag
duplication, but it breaks per-slug comparability (the scoreboard would not know it is
the same base model) and `--forget` of the base model would orphan the LoRA rows.

## Tests

`test_lora_rejected_on_strata`, `test_lora_file_must_exist`, `test_lora_reaches_build_args`,
`test_lora_recorded_in_result`, `test_upsert_keeps_lora_rows`,
`test_legacy_lora_none_coexists`, `test_render_labels_lora_rows` (new names, nothing
renamed: no old traceability affected).

## Architectural Decisions

### ADR-1: the LoRA is a pool condition, not part of the slug
**Context:** comparing bare-vs-adapter requires rows of the same base model to coexist.
**Decision:** key `(slug, thinking, lora)`; badge/suffix visual only.
**Alternatives considered:** synthetic slug (discarded: see above).
**Consequences:** same extension pattern as `thinking`; `forget` of the base model
also deletes its LoRA rows (desired behaviour).

### ADR-2: the LoRA source is the `.txt` profile or the CLI, never hardcoded
**Context:** each model may want a default adapter.
**Decision:** same convention as mmproj: profile if no CLI.
**Alternatives considered:** conventional `models/lora/` directory with auto-detection
(discarded: implicit magic; the profile is the single source of truth for flags).
**Consequences:** no changes to serving scripts; the `.txt` still applies LAST.
