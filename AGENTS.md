# AGENTS.md

Local model benchmark for comparing `llama-server`-served models across 4 dimensions
(speed, tools, code, agent) under identical conditions. Goal: pick the best model for opencode.
Design spec lives in `docs/SPEC.md` (written in Catalan — code comments and task prompts are too;
keep that language when editing task content).

## Run from the parent directory, not from here

`benchmark/` is a Python package (relative imports `from . import …`, tests do `from benchmark import …`).
All commands run from `/home/jordi/ia/llama/`, one level up. Running from inside `benchmark/` fails with
`ModuleNotFoundError: No module named 'benchmark'`.

```sh
# benchmark CLI
python3 -m benchmark.run [opts]

# full test suite (stdlib unittest — no pytest in the project)
python3 -m unittest discover -s benchmark/tests -t .

# single test module (dotted path, not a file path)
python3 -m unittest benchmark.tests.test_agent

# single test method
python3 -m unittest benchmark.tests.test_agent.TestMockEnv.test_read_write
```

Python 3.12. A venv exists at `../.venv` but everything is pure stdlib (`urllib.request`, not
`requests`/`httpx`); system `python3` works fine. There is no `requirements.txt`, `pyproject.toml`,
or build/codegen step. The smoke test picks the **smallest servable main model** (≥1 GB, excluding
mmproj/draft/embedding files) and **skips when a server is already listening on the harness port**
(it cannot compete for VRAM with a running instance).

## External runtime requirements

The harness shells out to system binaries; absence causes specific failures, not a clean skip:

- `../llama-server` — the llama.cpp server (symlink to `../llama.cpp/build/bin/llama-server`). Path is
  fixed in `config.SERVER_BIN`; `--models all` globs `../models/*.gguf`.
- Language toolchains for the **code** and **agent** dimensions: `python3`, `bash`, `javac`+`java`,
  and `bun` (TypeScript). The speed and tools dimensions don't need them.
- Linux expected. The end-to-end smoke test is gated on `sys.platform` and auto-skips if no
  `*.gguf` models are present, so `discover` passes on a bare checkout.

## Architecture notes that aren't obvious from filenames

- **Package layout is flat.** Source modules (`run.py`, `server.py`, `client.py`, `executors.py`,
  `graders.py`, `agent.py`, `tasks_loader.py`, `report.py`, `config.py`) sit directly at the package
  root, not under `src/`.
- **Tasks are data-as-code.** `tasks/<dim>/...` files are plain Python modules exporting module-level
  constants (`ID`, `PROMPT`, `LANG`, `TEST_CODE`, `EXPECTED`, …). `tasks_loader.py` imports them
  dynamically via `importlib`. Files starting with `_` or named `__init__.py` are skipped. `code/` and
  `agent/` are nested one level per language (`python|bash|java|typescript`); `speed/` and `tools/` are
  flat. Add a task by dropping in one such file — no registry to update. Note: the loader looks up
  **uppercase** `ID`/`PROMPT` (lowercase silently falls back to defaults), and for the tools dimension
  `TOOLS` must be a full OpenAI function schema (`{"type":"function","function":{...}}`) — the client
  passes it straight to the API, so a shorthand like `{"name": ...}` is invalid.
- **Language strings are centralized** in `config.Lang` (a `str`-based enum, so `Lang.PYTHON == "python"`
  and it interops with task-file strings). It backs the executor dispatch table in `executors.py` and
  `Lang.exts()` (used by the agent's `run_tests`). Add a new language there, not as a bare string.
- **Server readiness** (`server.py`) is probed via a real `/v1/chat/completions` call, **not**
  `/v1/models` (the latter answers before inference is ready). One model per run; fixed port (8999).
  A 3-shot warmup precedes measurement.
- **Code execution is sandboxed** in a fresh tempdir with `timeout 30s` and best-effort network
  isolation via `unshare -n` (silently skipped if user namespaces aren't permitted).
- **Token-budget calibration.** Code tasks whose response has no extractable code block (a verbose
  model truncated mid-block) are retried with a larger `max_tokens` ladder
  (`CODE_LADDER` in `graders.py`). The budget that worked for each (model, lang, task) is persisted
  to `results/token_budgets.json` (gitignored) via `token_budget.py`, so later runs use it directly
  instead of re-escalating. Keys are per-model; deleting the file forces a fresh calibration.
- **Per-model server config (2026-10)**: `models/<model>.txt` is applied **last** in
  `server.build_args` and may override the baseline (same convention as `bin/start-dev-ai.sh`;
  `#` comments and blank lines are skipped). Dedup is automatic: a `-c`/`--ctx-size` in the .txt
  drops the harness `-c`; a `--cache-type-k/v` drops the matching baseline one; infra flags
  (`-m`, `--port`, `--host`) are filtered out. Speculation (`--spec-type draft-mtp`/`draft-dflash`),
  `-md`, and `--mmproj` pass through as written — models compete with their real best config.
  Applied flags are printed to stderr at server start and stored in results as
  `model_config_flags`.
- **Baseline flags** live in `config.SERVER_FLAGS` (+ `config.CACHE_FLAGS` for the q4_0 KV cache;
  split out so the .txt can override one side without duplicate-flag warnings). Context mode
  `--context fixed` (default, 16384) vs `adapted` only applies when the .txt doesn't set `-c`.

## Results storage

`report.save_result` does an **upsert by slug** on `results/models/pool.jsonl` — re-running a
model overwrites its previous entry rather than duplicating it. `--forget <model>` rewrites
`pool.jsonl` without that model. Per-run JSON snapshots are appended to
`results/runs/<ts>-<slug>.json` (history). Both directories are gitignored.

## Workflow

- `python3 -m benchmark.run --scoreboard` — read-only, reprints accumulated tables from the pool.
- `python3 -m benchmark.run --models <name>` — run one model, append to pool, print scoreboard.
- `--dims`, `--lang`, `--quick` (1 task per dim, harness smoke), `-v` (per-task detail), `--json`
  (machine-readable pool dump) are all available; see `--help`.
- Weights default to `{tools:0.30, code:0.30, agent:0.25, speed:0.15}` in `config.py`; override via
  `--weights tools=0.3,…`.
- Progress (server start, warmup, per-task results, per-model ✓/✗) is streamed to **stderr** as it
  happens; only the final scoreboard — or the JSON dump with `--json` — goes to **stdout**. So
  `run --json > out.json` keeps stdout clean while still showing live progress on the terminal.
