# AGENTS.md — Navigation map for AI agents

> This file is the **entry point** for any agent working in this repository.
> It is NOT a rule bible — it is a **map**. Read only what you need, when you need it (progressive disclosure).

---

## 1. Before you start (mandatory)

1. Run `harness/init.sh` and verify it finishes without errors. If it fails, **stop** and fix the environment before touching code.
2. Read `harness/progress/current.md` to understand where the last session left off.
3. Read `harness/feature_list.json`. ALL features follow **Spec Driven Development** — see §4 of this file.
4. Read `docs/specs.md` before touching any spec or feature.

## 2. Repository map

| File / folder               | What it contains                                                           | When to read it                  |
|-----------------------------|-----------------------------------------------------------------------------|----------------------------------|
| `harness/feature_list.json`         | Feature list with status (`pending` / `spec_ready` / `in_progress` / `done` / `blocked`) | Always, at start                 |
| `harness/progress/current.md`       | Current session state                                                       | Always, at start                 |
| `harness/progress/history.md`       | Append-only log of previous sessions                                        | When you need historical context |
| `harness/specs/<feature>/`          | `requirements.md` + `design.md` + `tasks.md` (Kiro-style)                  | Before implementing any feature  |
| `docs/architecture.md`      | What "doing a good job" means in this project                               | Before implementing              |
| `docs/conventions.md`       | Style rules, naming, structure, and **Sonar/code-quality rules** (logging, resources, AssertJ, Docker) | Before writing code              |
| `docs/specs.md`             | SDD process: EARS notation, 3 files, human approval gate                   | Before writing or reading a spec |
| `docs/verification.md`      | How to verify your work works (including requirement traceability)          | Before marking a task as `done`  |
| `harness/CHECKPOINTS.md`            | Objective criteria for "correct final state"                                | For self-assessment              |
| `.opencode/agent/`           | Subagent definitions (`leader`, `spec-author`, `implementer`, `reviewer`)   | If you orchestrate work          |
| `src/`                      | Application code                                                            | To implement                     |
| `tests/`                    | Automated tests                                                             | To verify                        |
| `docs/architecture-options.md` | Architecture pattern catalog (module: architecture-catalog) | When filling design.md Architectural Decisions |
| `docs/iteration-protocol.md`   | Adaptive iteration + adversarial review protocol (module: iterative-refinement) | During implementer refinement rounds |
| `docs/log-reader-protocol.md`  | Delegate big-log reading to a cheap read-only subagent + verify evidence (module: log-reader) | When a file under `harness/logs/` is too big to read in session |
| `harness/tools/`               | Module tools: `audit-security.sh`, `bench.sh`, `scan.py` (if present) | On review (audits) or session start (scan) |
| `harness/decisions/`           | ADRs worth remembering beyond a feature (if present) | Before proposing a new architectural decision |
| `harness/wekan.json`           | Wekan ticket-mirror config (if present) | When syncing workflow state to the board |

> Module files are conditional: if a file above exists, its module was installed —
> follow it. If absent, ignore references to it.

## 3. Hard rules (non-negotiable)

- **One feature at a time.** Never pull a task from another feature into the same session; inside a feature, work in batches of 2–4 tasks (§4).
- **Do not mark a task `done` without green tests.** Run `harness/init.sh` and ensure the test block passes 100%.
- **Do not skip the spec phase.** Every feature must go through `spec-author` and obtain human approval before touching code.
- **Do not skip the human approval gate.** The leader stops the flow at `spec_ready` and waits.
- **Commits follow Conventional Commits** (`<type>(<scope>)!: <summary>`) — `.git/hooks/commit-msg` enforces it; `--no-verify` is not a way around the rule.
- **Document what you do** in `harness/progress/current.md` while working, not at the end.
- **Leave the repository clean** before closing the session (see §5).
- **If you don't know something, look in `docs/`** before inventing it.

<!-- harness:workflow:start -->
## 4. Workflow (SDD — hybrid: one in-session agent, same gates)

Same discipline as the full flow, executed by a single in-session agent. Roles
become modes you play sequentially; evidence replaces dispatches. The two human
gates are NOT negotiable — hybrid changes who executes, never who approves.

```
pending → [spec mode] → spec_ready → ⏈ HUMAN → in_progress → [batch mode → verify]×n → ⏈ HUMAN → done
```

1. **Spec mode.** Write `harness/specs/<name>/{requirements,design,tasks.md}`
   exactly as `spec-author` would — follow `.opencode/agent/spec-author.md` as
   a script. Mark the feature `spec_ready` and STOP for the human Spec Gate.
2. **Batch mode.** After approval, implement one batch at a time (2–4
   consecutive `T<n>` tasks), following `.opencode/agent/implementer.md`.
   Never a whole feature in one sitting.
3. **Evidence rule (the core of hybrid).** After every batch:
   - run the gates yourself (`harness/init.sh` / TEST_CMD) and save the full
     output to `harness/logs/<feature>/batch-<n>.log`;
   - tick tasks `[x]` only with that log in place, referencing it in tasks.md;
   - verify on disk: files present, no task done without green gates.
   A claim without a log is not evidence — the rule the leader applies to
   subagents, applied to yourself.
4. **Review mode.** Before requesting the Completion Gate: run
   `python3 harness/tools/check-traceability.py --feature <name>` (or `--all`
   for the whole portfolio — never pass `feature_list.json` as a positional:
   the tool treats it as `--root` and hard-rejects it with exit 2; a verdict
   without per-feature `## <name>: n/n` lines is a vacuous PASS),
   save its output to `harness/specs/<name>/review.md`, and walk
   `.opencode/agent/reviewer.md` as a checklist. Reject your own work if any
   `R<n>` lacks evidence.
   - **Suite assertions stay relative to the manifest**: use `indexOf`
     ordering or existence checks, never global positions or counts
     (e.g. the quoted example strings «últim tema», «N kates») — appending
     new themes/files must not break previous features' suites.
5. **Escalate to the full dispatch flow when any of these hold:** the feature
   has more than ~12 tasks; it touches files marked critical in
   `docs/conventions.md`; a batch stalls twice; or verification is subjective
   (no mechanical gate covers it). Then act as leader and dispatch a real
   reviewer subagent — fresh context is the value you are trading away for
   speed.

Trade-off, stated plainly: hybrid trades independent-context review for
velocity. The evidence logs and the traceability check are what keep that
trade honest.
<!-- harness:workflow:end -->
## 5. Session lifecycle (closure)

Before finishing:

1. Run `harness/init.sh` — all green.
2. If the task is done: mark `status: "done"` in `harness/feature_list.json`.
3. Move the summary from `harness/progress/current.md` to the end of `harness/progress/history.md`.
4. Clear `harness/progress/current.md` leaving only the template.
5. Do not leave temporary files, debug prints, or context-free TODOs.

## 6. If you get stuck

- Re-read the relevant section of `docs/`.
- If a tool doesn't behave as expected, **do not invent a workaround**: document the block in `harness/progress/current.md` and stop the session.

<!-- harness:project:start -->
## Project: local model benchmark (llama.cpp + Strata)

Compare local models served by **llama-server** (GGUF, port 8999) or **Strata**
(`--engine strata`, config `strata-<name>.json`, port 8080) across 4 dimensions — speed,
tools, code, agent — to pick the best model for opencode.
Design: `docs/SPEC.md` · improvement roadmap: `docs/MILLORA.md` · architecture:
`docs/architecture.md`.

### Commands — ALWAYS from the workspace root (`/home/jordi/ia/llama/`)

The package is imported as `ggufbench`; running from inside the directory fails with
`ModuleNotFoundError`. Notes: the git repo IS `ggufbench/`; the servers and the models
(40+ GB) live outside.

```sh
python3 -m unittest discover -s ggufbench/tests -t .    # full suite (~6 s, NO GPU)
python3 -m ggufbench.run --scoreboard                   # accumulated scoreboard (read-only)
python3 -m ggufbench.run --scoreboard --html            # refresh scoreboard + report (results/report.html)
python3 -m ggufbench.run --models <name> [--quick]      # llama run (starts the server itself)
python3 -m ggufbench.run --engine strata --models iq3_xxs [--quick]
python3 -m ggufbench.html_report                        # writes ggufbench/results/report.html
```

### Non-negotiable rules

1. **Never llama-server and Strata at the same time** (same GPUs, 2× RTX 5080). The harness
   starts and stops the server itself (`ServerManager`, killpg included): do not run
   either manually during a run.
2. **No task, weight or base-flag changes without a pool re-measure** (upsert per
   slug in `results/models/pool.jsonl`; history in `results/runs/`).
3. **One task = one file** in `tasks/<dim>/...` (UPPERCASE constants; the loader reads
   `ID`/`PROMPT` uppercase). `EXPECTED` without `arguments` = tool name only;
   `arguments: {}` = empty call. The agent resolves files case-insensitively (java:
   `Solution.java`).
   **Code levels:** `ID` ending in `_hard` → hard level; ending in `_expert` →
   expert level (multi-file: they can declare `EXTRA_FILES`, a dict of support files
   written into the sandbox before the solution and the test; plain names, no paths).
   `--level easy|hard|expert` filters them; without `--level` all run and the code
   score stays folded. `tasks_version` = "v3" since the expert level exists
   (v2 = hard, v1 = base). Reference solutions for hard and expert are NOT
   committed (do not leak them to the models).
   **Thinking:** `--thinking on|off` (default `off`, via `chat_template_kwargs` for both
   engines; no `.txt` overrides it). Recorded in every result and the pool keys
   by `(slug, thinking)` — both modes coexist; the scoreboard splits them into rows
   with a `THINK` column and exclusions are counted (`100% (7 excl.)`). Code budget:
   a single attempt of **32768** tokens; every profile must allow context for prompt +
   32768 (without `-c` it falls to `CONTEXT_FIXED = 16384`).
4. **Per-model profile:** `models/<model>.txt` (free flags except infra). Strata: one
   config per model in `Strata/strata-<name>.json`, python from ITS `.venv`.
5. Strata results identify the model by the config root
   (`strata-iq3_xxs`) and carry `engine` + `server_build`.
<!-- harness:project:end -->
