# Architecture

This document defines the project's architectural standards: the principles that
guide every design decision, the data flows, and the lines that must not be
crossed. Full design: `docs/SPEC.md` · improvement roadmap: `docs/MILLORA.md`.

---

## Principles

1. **Same conditions for every model.** The value of the bench is comparability:
   common base flags (`config.SERVER_FLAGS` + `CACHE_FLAGS`), per-model profile
   (`models/<model>.txt`, applied last), fixed temp/seed, identical prompts.
2. **Honesty of the result.** A task can FAIL (the model couldn't do it) or be
   EXCLUDED (transient server/network error, non-extractable code). Never confused:
   exclusions don't lower the score but are recorded in the trace.
3. **Zero dependencies.** Python 3.12 stdlib. The full suite must run in a bare
   runner without a GPU in under 60 s. That is a feature, not a limitation.
4. **Data-as-code.** One task = one Python file with constants (`ID`, `PROMPT`,
   `TEST_CODE`, `EXPECTED`...). No registry, no JSON: drop a file and done.
5. **Reproducibility.** Every result carries `ts`, `tasks_version`, `server_build`,
   `engine` and `model_config_flags`: any scoreboard row can be explained.
6. **Two engines, never at once.** llama-server (port 8999) and Strata (port 8080)
   compete for the same GPUs. The harness starts whichever server is needed and
   stops it with the whole process group (`start_new_session` + `killpg`).

---

## Data Flow

```
tasks/<dim>/**.py ──tasks_loader──▶ run._bench_one
                                      │  server.ServerManager (starts llama | strata)
                                      │  client.chat  ──▶ /v1/chat/completions
                                      ▼
                                   graders (speed · tools · code · agent)
                                      │  executors: sandbox (fresh tempdir, timeout, unshare -n)
                                      ▼
                                   report (upsert results/models/pool.jsonl
                                           + history results/runs/<ts>-<slug>.json)
                                      ▼
                         CLI (tables) · html_report (results/report.html)
```

Calibration: code tasks whose answer has no extractable block are escalated through
`CODE_LADDER` and the working budget is persisted in `results/token_budgets.json`.

---

## Do Not

- **Do not introduce external dependencies** (no pytest, no requests): the promise is
  "clean checkout + python3" and CI takes advantage of it.
- **Do not change tasks, weights or base flags without a pool re-measure** (upsert per slug:
  a row with old conditions next to new conditions is a lie).
- **Never run a llama run and a Strata run concurrently.**
- **Do not trust the model's output:** only the graders (real execution in the sandbox)
  decide the score; a pretty answer without passing tests is not a pass.
- **Port/host/model are fixed by the harness** (`server._INFRA_FLAGS`): a model's
  `.txt` cannot change them (a different port would break the ready-check).
- **No bug fix without the test that would have caught it** (precedents: `ef48e76`,
  `5a6903b` — two impossible tasks and a broken java agent no model had ever
  passed).
