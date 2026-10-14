# ggufbench — Design document

**Date:** 2026-08-03 (evolving; see `harness/progress/history.md`)
**Location:** `/home/jordi/ia/llama/ggufbench/`
**Status:** In production — harness v3, 6 features delivered (see `harness/feature_list.json`)

## 1. Goal

Automatic benchmark to compare local models (served by `llama-server`) under
**the same conditions**, with a scoreboard grading 4 dimensions:

1. **Speed** — raw throughput.
2. **Tool-calling** — reliability producing structured tool calls.
3. **Code with tests** — correctness implementing/fixing code (4 languages).
4. **Multi-step agent** — ability to read → understand → edit → verify.

The end goal is picking the best model for **opencode** (coding agent).

## 2. Principle: "same conditions" (revised 2026-10: common baselines + per-model profile)

- **Common flags** for all models (baseline in `config.SERVER_FLAGS`):
  `temp 0.2`, `top-p 0.95`, `seed 42`, `repeat-penalty 1.1`, **`top-k 40`**, **`min-p 0.05`**,
  **`xtc-probability 0.0`** (the three pinned explicitly at llama.cpp's defaults: see the
  sampler note below), `-ngl 999`, `--flash-attn auto`, `--load-mode none` (0.6.0+; was
  `--no-mmap`), `--jinja`, KV cache `q8_0/q8_0` (`config.CACHE_FLAGS`), `--parallel 1`.
- **Sampler metadata is a condition too**: llama.cpp applies a GGUF's `general.sampling.*`
  keys to every sampler parameter the command line does *not* set explicitly, so an unpinned
  parameter is a per-model value, not a harness default. Measured 2026-10-14: the fleet
  shipped `top_k` 20 (MiniCPM-V, Ornith, the three Qwen3.8-27B), 64 (gemma) and none at all
  (qwen36) — three samplers inside one table. The baseline pins all three at the engine's
  defaults (40 / 0.05 / 0.0), which is the neutral choice and leaves no parameter to the
  metadata (MILLORA §C11).
- **Sampling (n=1)**: one graded attempt per task (`temp 0.2`, `seed 42`).
  Single-sample noise is real: the scoreboard is a *ranking on this
  harness*, not a certification — close rows (±0.01 global) are ties in
  practice. `--runs N` (seed 42+idx per run) aggregates repeated runs as mean ± spread,
  and every row carries the ± it was measured with.
- **Task set (`task_signature`)**: the graded counts per dimension
  (`tools/code/agent`, e.g. `16/60/60`), derived from the traces, recorded in every
  result since 2026-10-14 and shown by the report. `tasks_version` is a suite *label*
  (v1 base, v2 hard, v3 expert, v4 the C3 counts) and cannot describe the set on its
  own: v3 ended up covering four different counts because the C3 additions never bumped
  it, so two rows could share a version and still be incomparable. The scoreboard and the
  compare page compare signatures and announce the mix (MILLORA §C9).
- **Baseline (`baseline_flags`)**: the common flags above are a *condition*, and until
  2026-10-14 no row recorded which one it ran with — ADR-0008 switched the KV cache
  `q4_0`→`q8_0` mid-pool. `config.baseline_argv()` (`SERVER_FLAGS + CACHE_FLAGS`) is now
  recorded in every result by `report.save_result`; the report shows it as a short id
  (`report.baseline_id` = sha1[:8], `?` for rows that predate the field — a baseline is
  never invented). Together with `task_signature` and `engine`/`server_build` it forms the
  three **condition axes** (`report.condition_axes` / `mixed_axes`): the CLI note, the
  HTML banner/chips and the compare banner fire when any of them mixes (MILLORA §C10).
- **Per-model profile**: `models/<model>.txt` is applied LAST and can
  override the baseline (same convention as `start-dev-ai.sh`; `#` comments
  are skipped). Automatic dedup: if the `.txt` defines
  `-c`/`--ctx-size`, the harness `-c` is dropped; if it defines `--cache-type-k/v`
  the corresponding common one is dropped. Infrastructure flags (`-m`, `--port`,
  `--host`) are filtered: the harness fixes them. MTP/DFlash (`--spec-type`,
  `-md`, `--mmproj`) do arrive as you have them in the `.txt` — models
  compete with their real best configuration, not in a lab.
  Applied flags are printed to stderr and recorded in the result
  (`model_config_flags`) to know how each model was measured.
- **Context (`-c`)**: two modes via the `--context` flag (only if the `.txt`
  does not define it):
  - `fixed` (default): `32768` for everyone → same KV → comparable speeds.
  - `adapted`: each model's audited viable context — `results/models/context.json`
    (`{"<slug>": {"ctx_max": int, ...}}`, written by `harness/tools/context-audit.py`).
    Without the audit the run raises: the estimator this mode described never existed,
    and a guessed number measures a context nobody verified.
  The decision lives in one place (`server.resolve_context_and_source`) and every result
  records it: `context_mode` (what was asked), `ctx_resolved` (the number the server
  actually got) and `ctx_source` (`profile` = the `.txt`/Strata config pinned it,
  `baseline` = the harness' `CONTEXT_FIXED`, `audit` = the audited value). Rows from
  before these fields exist lack them; a row measured at 16384 and one measured at
  32768 are different conditions — the field is what tells them apart.
- `--tensor-split` does adapt (multi-GPU, free-VRAM proportion).
- **Second engine (2026-10): `--engine strata`** — same conditions, different
  runner. The non-identical points:
  - `--models` takes **config names**: `iq3_xxs` -> `Strata/strata-iq3_xxs.json`
    (`all` = all `strata-*.json`; an explicit path passes through as-is). The
    pool identity is the config root (`strata-iq3_xxs`), which is also the
    scoreboard slug; the result carries `engine` and `server_build` = binary
    version (`strata/engine/BUILD.json`).
  - Default port 8080 (`config.STRATA_PORT`); `--port` changes it.
  - **No thinking chain by default**: the model thinks in HIGH by default and with the
    small task `max_tokens` (128-512) it would eat the budget without
    answering; the client sends `chat_template_kwargs: enable_thinking=false` (same
    policy as Strata's `bench/bench_vs_llama.py`). Since `thinking_batches` this
    is the `--thinking off` mode (default, for both engines); `--thinking on` leaves it
    free and the pool distinguishes both modes.
  - **Readiness**: `/health` must report `loaded` before the chat probe (probes
    would queue behind the 34-43 GB load); waits `STRATA_READY_TIMEOUT`
    (600 s).
  - **Lifecycle**: starts with `start_new_session` and `stop()` kills the whole
    process group — the `engine/strata` child would outlive the parent
    `serve/server.py` and keep holding VRAM. Server output
    is saved to `/tmp/ggufbench-strata-server-<port>.log` (never /dev/null).
  - **The two engines never run at once**: they compete for the same GPUs.
- **Warmup** of 1 generation before measuring/any task.
- Same prompts/tests for all models.

## 3. Architecture

```
ggufbench/
├── run.py            # CLI / entry point
├── config.py         # weights, defaults, paths, server flags
├── server.py         # llama-server lifecycle (start/stop/ready)
├── client.py         # HTTP client to /v1/chat/completions
├── executors.py      # per-language runners (py/bash/java/ts) + sandbox
├── graders.py        # scoring per dimension
├── agent.py          # multi-step agent loop + mock environment
├── report.py         # scoreboard (terminal table + JSON)
├── tasks/
│   ├── speed/
│   ├── tools/
│   ├── code/{python,bash,java,typescript}/
│   └── agent/{python,bash,java,typescript}/
├── results/
│   ├── models/        # <slug>.json — latest result per model (the POOL)
│   └── runs/          # <ts>-<slug>.json — append-only history of every run
└── docs/SPEC.md
```

### Main flow (run.py)
```
if --scoreboard:                      # read-only mode
    report(results/models/*.json)     # show accumulated tables and exit

models = resolve_models(args)
for each model:
    server.start(model)               # starts with config.py flags
    wait_ready()                      # real inference (not /v1/models)
    warmup()
    result = {}
    for each enabled dimension:
        result[dim] = run_dimension(dim, model)   # run tasks + grade
    server.stop()
    save result/models/<slug>.json      # updates the pool (overwrites)
    save result/runs/<ts>-<slug>.json   # append-only history
report(results/models/*.json)           # ACCUMULATED scoreboard of all models
```

## 4. Components

### 4.1 server.py — llama-server manager
- `start(model)`: launches `llama-server` (subprocess) with the flags from
  `config.py` + `-c` (per mode) + `--tensor-split` (per VRAM).
- `wait_ready()`: polls until a test chat returns `"choices"`
  (not just `/v1/models`, which answers before being ready for inference).
- `stop()`: SIGKILL + wait.
- One model at a time (fixed port, e.g. 8999).

### 4.2 client.py — HTTP client
- `chat(messages, tools=None, max_tokens=..., temperature=...)` → dict.
- Captures `timings` (gen_tps, prompt_tps, predicted_ms) for speed.
- Configurable timeout (default 60s).
- Readable by the agent loop (supports multi-turn).

### 4.3 executors.py — multi-language execution + sandbox
One executor per language. All share the same interface:
`run(lang, solution_code, test_code) -> (passed: bool, output: str)`.

| Lang | Solution | Test (grader) | Command |
|---|---|---|---|
| python | `solution.py` | `test.py` (import + asserts) | `python3 test.py` |
| bash | `solution.sh` (functions) | `test.sh` (source + asserts) | `bash test.sh` |
| java | `Solution.java` (class+method) | `Test.java` (main + asserts) | `javac *.java && java Test` |
| typescript | `solution.ts` | `test.ts` (import + asserts) | `bun test.ts` |

**Code extraction**: from the model's response, take the first
` ```lang ... ``` ` block matching the task language. If none → excluded
(does not count toward the score; the reason stays in the trace).

**Code budget**: a single attempt with `CODE_MAX_TOKENS = 32768`, same for all
models (reviewer decision: expert tasks need it). The clock is
only an anti-hang guard (derived from measured `gen_tps`, up to 1000 s). Precondition: every
profile must allow context for prompt + 32768 (profiles without `-c` fall to
`CONTEXT_FIXED = 32768` — the whole budget with no room for the prompt, so they do not
meet it: they need their own `-c` or the context audit).

**Sandbox** (per execution):
- fresh, exclusive tempdir.
- `timeout 30s` (kills the process if exceeded).
- network blocked: `unshare -n` if available; otherwise `env -i` + no network PATH.
- `ulimit` (CPU/memory).
- Never runs outside the tempdir.

Toolchains verified on the system: Python 3.12, Bash 5.2, Java 22 (jdk+javac),
Bun 1.3.9 (TS). No pytest → Python tests use bare `assert`.

### 4.4 graders.py — scoring per dimension

**speed**: 1 task. Takes `timings.predicted_per_second` (or computes
`predicted_n / (predicted_ms/1000)`). 3 samples, median. Metrics:
`gen_tps`, `prompt_tps`, `ttft_ms`.

**tools**: per task, `{prompt, tools, expected}`. Scoring:
- `pass` if `message.tool_calls[0].function.name == expected.name` **and**
  `arguments` (parsed as JSON) == `expected.arguments`.
- "no-op" case: `pass` if there are **no** `tool_calls` (it must not invent one).

**code**: per task `{lang, prompt, test_code}`. Extract code → executor →
`pass` if exit 0.

**agent**: delegates to `agent.py` (4.5).

Score per dimension = `passed / total` (0..1). Speed = normalized
against the best tps in the set (fastest → 1.0).

**Per-language aggregation**: the `code` and `agent` dimensions compute, besides
the global dimension score, `by_lang` = score per present language
(`python|bash|java|typescript`). The `tools` and `speed` dimensions are not
per-language (they are language-agnostic). `report.py` uses this `by_lang` for
Table 2 and the per-language profile. An *excluded* run (server error, no code
block) is not an attempt: it never enters `by_lang`/`by_level` and it does not
count as a failure.

**Task identity is `(dimension, language, id)`**: ids are unique *per dimension*,
not per language — the easy code tier deliberately mirrors the same id across the
four languages (`bubble_sort`, `fibonacci`…) and so do most agent ids (`debug`,
`refactor`, `fix_bug`…). Every consumer must key on the pair: the multi-run
aggregation walks the per-run results **by position** (one entry per task, in task
order) precisely because looking an entry up by `id` alone attributed a bash task's
outcome to the python task with the same id (found and fixed 2026-10-14, MILLORA
§D10 — it skewed every multi-language row measured before that date).

### 4.5 agent.py — multi-step agent loop
In-memory mini code environment. An agent task defines:
`{lang, goal, initial_files, max_turns}` (`MAX_TURNS` is per task: the task files set it,
the loader maps it and the grader honours it).

Tools available to the model: `list_files()`, `read_file(path)`, `write_file(path, content)`,
`run_tests()`. The loop:
```
env = dict(initial_files)
history = [user(goal)]
for turn in 1..max_turns:
    resp = client.chat(history, tools=[list_files, read_file, write_file, run_tests])
    if no tool_calls: break
    for each tool_call:
        result = execute_tool(tool_call, env, lang)   # mutates env / runs tests
        history.append(tool(result))
success = check_goal(env, lang)   # final run_tests passes?
```
`run_tests()` uses `executors.py` with the task language: it writes the **whole project**
(the solution, the test and every other file in `env`, passed as `extra_files`) to the
tempdir, runs the test, returns pass/fail + output. That is what makes a multi-file task
measurable: the bug can live in a module the test never names, and editing it changes the
verdict (`java` compiles every `.java`, so support classes travel too). The sandbox is
**flat**: `write_file` rejects names with a directory part or `..`.
`check_goal` = final `run_tests()` with exit 0.

The test file is **read-only** and grading always uses the pristine copy: several tasks say
in their goal "fix the code without touching the tests", and before 2026-10-14 nothing
enforced it (a model could rewrite the test and pass). Files with a directory part are
refused for the same reason the loader refuses `EXTRA_FILES` paths.

### 4.6 report.py — scoreboard and detail
Reporting has **3 granularity levels**:

**Table 1 — Global** (always; `--sort` orders it — `global` by default, a dimension, or
`version`: grouped by task set, biggest first, global inside each group). Every row states
its test version in `SET` (label·task-set, §2):
```
MODEL                    THINK SET          tools   code   agent   speed   GLOBAL
qwen36-35b-distill-moe    off  v4·16/60/60   94% ±0  76% ±2  77% ±3   18ms   0.81 ±0
gemma-4-26b-a4b-it        off  v3·12/60/28   92% ±0  91% ±3  93% ±0   32ms   0.84 ±1
```

**Table 2 — Per language** (always; code and agent broken down):
```
MODEL                          code:py bas java ts    agent:py bas java ts
qwen3-14b                          100% 100%  50% 100%        100%  —  50% 100%
qwen3-vl-8b                        100%  50%   0% 100%         50%  —   0% 100%
```
A `—` cell = no tasks in that language for that dimension.

**Table 3 — Task detail** (with `--task`):
```
MODEL            DIM     LANG   TASK              PASS   DETAIL
qwen3-14b        tools   —      multi-arg         ✓      get_weather(city=Paris)
qwen3-14b        code    java   implementa-stack  ✗      AssertionError line 12
qwen3-14b        agent   py     fix-bug-fib       ✓      tests pass (2/2)
qwen3-vl-8b      code    java   implementa-stack  ✗      no code block found
...
```

**Granularity levels** (`report.render(level=...)`, `run.py --info/--verbose/--task`):
- **default**: Table 1 (global scores) + tokens-per-second section.
- **`--info`**: Table 1 + Table 3 (task detail). Answers "what each model is good/bad at" showing ✓/✗ and the detail of every tools/code/agent task.
- **`--verbose` (-v)**: Table 1 + Table 2 (per language). Does NOT include task detail; it is the finest level without per-task rows.
- **`--task`**: adds task detail (Table 3) to any level. Granularity composes: you can combine `--verbose` (per-language) with `--task` for Table 1 + Table 2 + Table 3.

The render is tolerant: a model missing a dimension or trace (partial run or models
without that granularity yet) does not fail; empty cells show `—`.

**JSON + incremental storage** — tables grow model by model without
re-running the others. Two layers:
- `results/models/<slug>.json` → **latest result per model** (current pool,
  overwrites when re-running that model). `<slug>` = sanitized model name.
- `results/runs/<timestamp>-<slug>.json` → **append-only history** (audit,
  compare later runs).

Every result carries condition metadata to mix runs fairly:
`context_mode`, `ctx_resolved` + `ctx_source` (the context the server really got and
where it came from: `profile` / `baseline` / `audit` — §2), `tasks_version` (suite label:
"v1" base, "v2" with the hard level, "v3" with the expert level, "v4" the current C3
counts) together with `task_signature` (the graded counts the row really ran: the label
alone let three sets live under "v3" — §2, MILLORA §C9), `thinking` (`on`/`off`: thinking
chain, pool key together with the slug), `weights`, `ts`,
`server_build` (llama.cpp version), `code_budget` + `code_budget_stored` (the code token
cap the tasks ran under, and any per-task calibration from the `token_budgets` artifact
that was in play: caps are conditions like context — a 4096-token cap and a 32768 one do
not measure the same thing, and before 2026-10-14 the row did not say which it used,
MILLORA §C12) and `model_config_flags` (flags extracted from
`models/<model>.txt`, or null — remember that since 2026-10 every model runs
with its profile). The scoreboard warns (or filters) when results with
different conditions are mixed.

The per-model JSON is:
```json
{
  "model": "qwen3-14b",
  "ts": "2026-08-03T20:30:00",
  "context_mode": "fixed",
  "ctx_resolved": 32768,
  "ctx_source": "baseline",
  "thinking": "off",
  "tasks_version": "v4",
  "task_signature": "16/60/60",
  "server_build": "10250",
  "global": 0.91,
  "speed": {"gen_tps": 48.0, "prompt_tps": 2600.0, "ttft_ms": 220},
  "tools": {"score": 1.0, "tasks": [
    {"name":"multi-arg","pass":true,"got":{"name":"get_weather","arguments":{"city":"Paris"}},"expected":{...}},
    ...]},
  "code": {
    "score": 0.88,
    "by_lang": {"python":1.0, "bash":1.0, "java":0.5, "typescript":1.0},
    "by_level": {"easy":0.92, "hard":0.75, "expert":0.4},
    "tasks": [{"name":"stack","lang":"java","pass":false,"output":"AssertionError...","elapsed_ms":1240}, ...]
  },
  "agent": {
    "score": 0.83,
    "by_lang": {"python":1.0, "typescript":1.0, "java":0.5, "bash":null},
    "tasks": [{"name":"fix-fib","lang":"python","pass":true,"turns":3,"tool_calls":4,"final_tests":"pass"}, ...]
  }
}
```
Previous runs are preserved (history). Supports `--compare <ts1> <ts2>` (future).

**Accumulated scoreboard**: speed normalization (best tps → 1.0) and the
percentages are recomputed at display time, over the loaded model pool (not stored
normalized) — so adding a faster model fairly rescales the rest.

**Per-language profile** (quick summary): the report extracts, per model, the
languages where it exceeds the threshold (e.g. ≥75%) and the ones it doesn't — to answer
directly "in which languages is this model reliable for me".

## 5. Global score

Weighted sum (in `config.py`, configurable):
- Tools: **0.30**
- Code: **0.30**
- Agent: **0.25**
- Speed: **0.15**

Speed normalized (best tps → 1.0) so raw t/s doesn't dominate.

## 6. Task suite (~23)

| Dimension | # | Detail |
|---|---:|---|
| speed | 1 | fixed prompt, language-agnostic |
| tools | 8 | 1-arg, multi-arg, pick-tool, no-op, wrong-args, chaining, dependencies, refactor |
| code | 8 | 2 per language (bash, python, java, typescript): implement-function + fix-bug |
| agent | 6 | python×2, typescript×2, java×1, bash×1 |

Format of each task: Python file with descriptive constants
(`PROMPT`, `LANG`, `TEST_CODE`, `EXPECTED`, etc.) — test code as a string.
One task = one file, self-contained and describable.

## 7. CLI

```
ggufbench/run.py [options]
  --models all|<list>          # default: all (models/*.gguf; with --engine strata: strata-*.json)
  --engine llama|strata        # engine serving the model (default: llama)
  --context fixed|adapted      # default: fixed (32768). adapted reads the context audit
                               # (results/models/context.json) and raises without it. A
                               # profile that pins -c always wins; the resolved value and
                               # its source are recorded in every row (ctx_resolved,
                               # ctx_source).
  --dims speed,tools,code,agent  # subset; default: all
  --lang python,java,...       # filters code/agent tasks by language
  --level easy|hard|expert     # filters ONLY code tasks by level (suffix _hard or
                               # _expert; without --level all three run and the code score is folded)
  --thinking on|off            # thinking chain (default off, via chat_template_kwargs);
                               # recorded in every result; the pool keys by (slug, thinking)
  --quick                      # 1 task per dimension (harness smoke test)
   -v, --verbose                # Table 1 + per-language (Table 2); NO tasks
   --task                       # Table 3 (task detail): shows where each model succeeds/fails; composes with --verbose
   --info                       # Table 1 + Table 3 (task detail)
  --scoreboard                 # ONLY shows the accumulated tables (runs nothing)
  --sort KEY                   # Table 1 ordering: global (default) | tools | code | agent
                               # | speed | version (grouped by task set — §2, MILLORA §C9)
  --forget <model>             # removes a model from the pool
  --json                       # only dumps the final JSON (for scripts)
  --port N                     # default 8999
  --weights tools=0.3,code=0.3,agent=0.25,speed=0.15
```
**Incremental workflow**:
- `run.py --models qwen3-vl` → runs and saves; shows scoreboard with all
  models in the pool (initially only this one).
- `run.py --models qwen3-14b` → adds to the pool; scoreboard with both.
- `run.py --scoreboard` → re-prints the tables without re-running anything.
- `run.py --models qwen3-vl` (another day) → re-runs and **updates** that
  model (overwrites); the rest stays.

## 8. Error handling

- Model fails to load (OOM, crash) → marked `serve_failed`, skipped, continue.
- Task with error/timeout → recorded as `error`, **does not** kill the whole run.
- Hung server → hard `stop()` + continue with the next one.

## 9. Out of scope (v2+)

- **Approach C** (real mini-opencode end-to-end with a true agent).
- Direct opencode (CLI) integration for real-world tests.
- Multimodal support (images).
- Visual comparison between runs (`--compare` with HTML).
- Sandbox with firejail/bwrap (now: tempdir+timeout+unshare).

## 10. Pending decisions

None — all key decisions are resolved:
- Languages: bash, python, java, typescript (confirmed).
- Tasks: ~23, extensible (confirmed).
- Context: both modes via flag (confirmed).
- Orchestration: automatic (confirmed).
