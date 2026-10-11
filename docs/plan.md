# Model Benchmark — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an automatic benchmark at `/home/jordi/ia/llama/benchmark/` that compares local models (llama-server) on speed, tool-calling, code (4 languages) and multi-step agent, with accumulated results.

**Architecture:** Python harness (stdlib only) that for each model launches `llama-server` with fixed flags, runs a task suite, classifies the tasks, and accumulates the results in a persistent pool (`results/models/`). The agent loop simulates an in-memory code environment with `read_file/write_file/run_tests` tools. The per-language executors run generated code in a sandbox (tempdir+timeout+no-network).

**Tech Stack:** Python 3.12 stdlib (urllib for HTTP, unittest for harness tests, subprocess, json, tempfile, pathlib). Toolchains present: `python3`, `bash`, `javac/java 22`, `bun 1.3.9` (for TS). No external deps (no `requests`, no `pytest`).

## Global Constraints

- **Location:** everything under `/home/jordi/ia/llama/benchmark/`.
- **Server binary:** `/home/jordi/ia/llama/llama-server` (symlink); models at `/home/jordi/ia/llama/models/*.gguf`.
- **No external deps:** HTTP via `urllib.request`; harness tests via `python -m unittest` (stdlib). No `pip install`.
- **Fixed server flags** (from `start-dev-ai.sh`): `-ngl 999 --flash-attn auto --no-mmap --jinja --parallel 1 -b 512 --temp 0.2 --top-p 0.95 --repeat-penalty 1.1 --repeat-last-n 256 --seed 42 --cache-type-k q4_0 --cache-type-v q4_0 --host 127.0.0.1 --port <P>`.
- **Context modes:** `fixed` (16384 by default) or `adapted` (the model's viable).
- **Code sandbox:** new tempdir + `timeout 30` + `unshare -n` if available; generated code never outside the tempdir.
- **Commits:** the project has its own `git init` (Task 1).
- **Code/agent languages:** bash, python, java, typescript.
- **Default weights:** tools=0.30, code=0.30, agent=0.25, speed=0.15.

---

## File Structure

```
benchmark/
├── run.py                 # CLI entry (argparse) + orchestration
├── config.py              # constants: paths, flags, weights, slug()
├── client.py              # chat() HTTP + parsing of timings/tool_calls
├── server.py              # ServerManager: start/wait_ready/stop + build_args
├── executors.py           # run(lang, solution, test) -> Result; 4 languages + sandbox
├── code_extract.py        # extract ```lang``` block from the response
├── agent.py               # MockEnv + run_agent() loop with read_file/write_file/run_tests
├── graders.py             # grade_speed/grade_tools/grade_code/grade_agent
├── tasks_loader.py        # discover/load tasks/ as modules
├── report.py              # render(pool) tables + save_run/load_pool/normalize
├── tasks/
│   ├── speed/  tools/  code/{python,bash,java,typescript}/  agent/{python,bash,java,typescript}/
├── results/
│   ├── models/            # <slug>.json (pool,latest)
│   └── runs/              # <ts>-<slug>.json (history)
└── tests/                 # test_*.py (unittest)
    test_config.py test_client.py test_executors.py test_code_extract.py
    test_server.py test_agent.py test_graders.py test_report.py
```

---

## Task 1: Scaffold, git init, config.py and slug()

**Files:**
- Create: `benchmark/config.py`, `benchmark/__init__.py` (empty), `benchmark/tests/__init__.py` (empty), `benchmark/tests/test_config.py`
- Create: `benchmark/.gitignore` (ignora `results/runs/`, `__pycache__/`)

**Interfaces:**
- Produces: `config.BASE_DIR`, `config.MODELS_DIR`, `config.SERVER_BIN`, `config.RESULTS_DIR`, `config.SERVER_FLAGS` (list), `config.PORT`, `config.CONTEXT_FIXED`, `config.WEIGHTS` (dict), `config.slug(name) -> str`.

- [ ] **Step 1: git init + structure**

```bash
cd /home/jordi/ia/llama/benchmark
git init -q
mkdir -p tasks/{speed,tools,code/{python,bash,java,typescript},agent/{python,bash,java,typescript}} results/{models,runs} tests
touch __init__.py tests/__init__.py
```

- [ ] **Step 2: .gitignore**

Create `benchmark/.gitignore`:
```
__pycache__/
*.pyc
results/runs/
results/models/
```
(Results are not committed — they are regenerated; the pool is local.)

- [ ] **Step 3: failing test for config + slug**

`benchmark/tests/test_config.py`:
```python
import unittest
from benchmark import config

class TestConfig(unittest.TestCase):
    def test_paths_exist(self):
        self.assertTrue(config.BASE_DIR.is_dir())
        self.assertTrue(config.MODELS_DIR.is_dir())
    def test_server_flags_includes_ngl(self):
        self.assertIn("-ngl", config.SERVER_FLAGS)
        self.assertIn(999, config.SERVER_FLAGS)
    def test_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(config.WEIGHTS.values()), 1.0, places=6)
    def test_slug_sanitizes(self):
        self.assertEqual(config.slug("Qwen3-VL-8B-Instruct-1M-Q6_K.gguf"),
                         "Qwen3-VL-8B-Instruct-1M-Q6_K")
        self.assertEqual(config.slug("Model Foo (v2)"), "Model_Foo__v2_")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: verify that it fails**

Run: `cd /home/jordi/ia/llama && python -m unittest benchmark.tests.test_config -v`
Expected: FAIL (`ModuleNotFoundError` or `AttributeError`).

- [ ] **Step 5: implement config.py**

`benchmark/config.py`:
```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent          # /home/jordi/ia/llama
BENCH_DIR = Path(__file__).resolve().parent                # .../benchmark
MODELS_DIR = BASE_DIR / "models"
SERVER_BIN = BASE_DIR / "llama-server"
RESULTS_DIR = BENCH_DIR / "results"
RESULTS_MODELS = RESULTS_DIR / "models"
RESULTS_RUNS = RESULTS_DIR / "runs"

PORT = 8999
CONTEXT_FIXED = 16384

# Fixed flags (same conditions for all). The model, -c, -m, --tensor-split are added in server.py.
SERVER_FLAGS = [
    "-ngl", "999",
    "--flash-attn", "auto",
    "--no-mmap",
    "--jinja",
    "--parallel", "1",
    "-b", "512",
    "--temp", "0.2",
    "--top-p", "0.95",
    "--repeat-penalty", "1.1",
    "--repeat-last-n", "256",
    "--seed", "42",
    "--cache-type-k", "q4_0",
    "--cache-type-v", "q4_0",
    "--host", "127.0.0.1",
]

WEIGHTS = {"tools": 0.30, "code": 0.30, "agent": 0.25, "speed": 0.15}

# Threshold (fraction 0..1) for the "reliable per language" profile.
LANG_OK_THRESHOLD = 0.75

def slug(name: str) -> str:
    """Sanitize a model name to use it as a file name (strips .gguf)."""
    s = name
    for ext in (".gguf", ".GGUF"):
        if s.endswith(ext):
            s = s[: -len(ext)]
            break
    return s.replace("/", "_")
```

- [ ] **Step 6: verify pass**

Run: `cd /home/jordi/ia/llama && python -m unittest benchmark.tests.test_config -v`
Expected: 4 PASS.

- [ ] **Step 7: commit**

```bash
cd /home/jordi/ia/llama/benchmark
git add -A && git commit -m "feat: scaffold + config.py (paths, flags, weights, slug)"
```

---

## Task 2: client.py — HTTP chat + parsing

**Files:**
- Create: `benchmark/client.py`, `benchmark/tests/test_client.py`

**Interfaces:**
- Produces: `client.chat(messages, tools=None, tool_choice=None, max_tokens=256, base_url=..., timeout=60) -> dict` (complete response JSON); `client.parse_timings(resp) -> dict|None`; `client.extract_tool_call(resp) -> dict|None` (returns `{"name":..., "arguments": <parsed json or None>}` or None); `client.first_text(resp) -> str`.

- [ ] **Step 1: failing test**

`benchmark/tests/test_client.py`:
```python
import unittest
from benchmark import client

SAMPLE = {
    "choices": [{"finish_reason": "tool_calls", "message": {
        "role": "assistant", "content": "",
        "tool_calls": [{"type": "function", "function": {
            "name": "get_weather", "arguments": '{"city": "Paris"}'}}]}}],
    "usage": {"completion_tokens": 20, "prompt_tokens": 50},
    "timings": {"predicted_per_second": 97.7, "predicted_n": 20,
                "predicted_ms": 204.9, "prompt_per_second": 500.0},
}

class TestClient(unittest.TestCase):
    def test_parse_timings(self):
        t = client.parse_timings(SAMPLE)
        self.assertAlmostEqual(t["gen_tps"], 97.7)
        self.assertAlmostEqual(t["prompt_tps"], 500.0)
    def test_parse_timings_missing(self):
        self.assertIsNone(client.parse_timings({"choices": []}))
    def test_extract_tool_call(self):
        tc = client.extract_tool_call(SAMPLE)
        self.assertEqual(tc["name"], "get_weather")
        self.assertEqual(tc["arguments"], {"city": "Paris"})
    def test_extract_tool_call_none(self):
        no_tc = {"choices": [{"message": {"content": "hola"}}]}
        self.assertIsNone(client.extract_tool_call(no_tc))
    def test_extract_tool_call_bad_json_args(self):
        bad = {"choices": [{"message": {"tool_calls": [
            {"function": {"name": "f", "arguments": "no-json"}}]}}]}
        tc = client.extract_tool_call(bad)
        self.assertEqual(tc["name"], "f")
        self.assertIsNone(tc["arguments"])  # unparseable arguments -> None
    def test_first_text(self):
        self.assertEqual(client.first_text(SAMPLE), "")
        self.assertEqual(client.first_text({"choices":[{"message":{"content":"x"}}]}), "x")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: verify that it fails**

Run: `python -m unittest benchmark.tests.test_client -v` → FAIL (ImportError).

- [ ] **Step 3: implement client.py**

`benchmark/client.py`:
```python
import json
import urllib.request
import urllib.error

def chat(messages, tools=None, tool_choice=None, max_tokens=256,
         base_url="http://127.0.0.1:8999", timeout=60):
    """POST /v1/chat/completions and return the complete JSON. Raises an exception on error/timeout."""
    body = {"messages": messages, "max_tokens": max_tokens, "temperature": 0.2, "seed": 42}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = tool_choice or "auto"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(f"{base_url}/v1/chat/completions", data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def parse_timings(resp):
    t = (resp or {}).get("timings") or {}
    if not t:
        return None
    tps = t.get("predicted_per_second")
    if tps is None:
        n = t.get("predicted_n") or (resp.get("usage", {}) or {}).get("completion_tokens") or 0
        ms = t.get("predicted_ms") or 0
        tps = (n / (ms / 1000.0)) if (n and ms) else None
    ptps = t.get("prompt_per_second")
    return {"gen_tps": tps, "prompt_tps": ptps,
            "predicted_ms": t.get("predicted_ms")}

def extract_tool_call(resp):
    try:
        m = resp["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        return None
    tcs = m.get("tool_calls") or []
    fr = (resp.get("choices", [{}])[0]).get("finish_reason")
    if not tcs and fr != "tool_calls":
        return None
    if not tcs:
        return None
    fn = tcs[0].get("function", tcs[0])
    args = fn.get("arguments")
    try:
        args_parsed = json.loads(args) if isinstance(args, str) else args
    except Exception:
        args_parsed = None
    return {"name": fn.get("name"), "arguments": args_parsed}

def first_text(resp):
    try:
        return resp["choices"][0]["message"].get("content") or ""
    except (KeyError, IndexError, TypeError):
        return ""
```

- [ ] **Step 4: verify pass**

Run: `python -m unittest benchmark.tests.test_client -v` → 6 PASS.

- [ ] **Step 5: commit**

```bash
git add -A && git commit -m "feat: client.py (HTTP chat + parse timings/tool_calls)"
```

---

## Task 3: code_extract.py — extract code block per language

**Files:**
- Create: `benchmark/code_extract.py`, `benchmark/tests/test_code_extract.py`

**Interfaces:**
- Produces: `code_extract.extract(text, lang) -> str|None`. `lang` one of `python|bash|java|typescript`. Returns the code of the first ` ```lang ` block (or alias: `py`, `sh`, `ts`, `js`). None if there is none.

- [ ] **Step 1: failing test**

`benchmark/tests/test_code_extract.py`:
```python
import unittest
from benchmark import code_extract

class TestExtract(unittest.TestCase):
    def test_python_block(self):
        txt = "Sure:\n```python\ndef f():\n    return 1\n```\ndone"
        self.assertEqual(code_extract.extract(txt, "python"), "def f():\n    return 1\n")
    def test_alias_py(self):
        self.assertEqual(code_extract.extract("```py\nx=1\n```", "python"), "x=1\n")
    def test_typescript_ts(self):
        self.assertEqual(code_extract.extract("```ts\nconst x=1\n```", "typescript"), "const x=1\n")
    def test_bash_sh(self):
        self.assertEqual(code_extract.extract("```sh\necho hi\n```", "bash"), "echo hi\n")
    def test_java(self):
        self.assertEqual(code_extract.extract("```java\nclass A{}\n```", "java"), "class A{}\n")
    def test_none(self):
        self.assertIsNone(code_extract.extract("no code here", "python"))
    def test_plain_block_fallback(self):
        # if there is only a ``` block without lang and python is requested, take it
        self.assertEqual(code_extract.extract("```\nx=1\n```", "python"), "x=1\n")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: verify it fails**

Run: `python -m unittest benchmark.tests.test_code_extract -v` → FAIL.

- [ ] **Step 3: implement code_extract.py**

`benchmark/code_extract.py`:
```python
import re

_ALIASES = {
    "python": ["python", "py"],
    "bash": ["bash", "sh", "shell"],
    "java": ["java"],
    "typescript": ["typescript", "ts", "js"],
}

def extract(text, lang):
    if not text:
        return None
    langs = _ALIASES.get(lang, [lang])
    # first a block with a known tag
    for tag in langs:
        m = re.search(r"```" + re.escape(tag) + r"[^\n]*\n(.*?)```", text, re.DOTALL)
        if m:
            return m.group(1)
    # fallback: block without tag
    m = re.search(r"```\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1)
    return None
```

- [ ] **Step 4: verify pass**

Run: `python -m unittest benchmark.tests.test_code_extract -v` → 7 PASS.

- [ ] **Step 5: commit**

```bash
git add -A && git commit -m "feat: code_extract.py (extreure bloc per llenguatge)"
```

---

## Task 4: executors.py — Python executor + sandbox

**Files:**
- Create: `benchmark/executors.py`, `benchmark/tests/test_executors.py`

**Interfaces:**
- Produces: `executors.run(lang, solution_code, test_code, timeout=30) -> dict` with `{"passed": bool, "output": str, "elapsed_ms": int}`. For now only `lang=="python"`. Uses `executors.SANDBOX_PREFIX` (list to block the network).

- [ ] **Step 1: failing test**

`benchmark/tests/test_executors.py`:
```python
import unittest
from benchmark import executors

PY_TEST_PASS = "from solution import *\nassert add(2,3)==5\nprint('OK')\n"
PY_TEST_FAIL = "from solution import *\nassert add(2,3)==6\n"
PY_SOL = "def add(a,b):\n    return a+b\n"
PY_SOL_BAD = "def add(a,b):\n    return a-b\n"

class TestPyExecutor(unittest.TestCase):
    def test_pass(self):
        r = executors.run("python", PY_SOL, PY_TEST_PASS)
        self.assertTrue(r["passed"])
        self.assertIn("OK", r["output"])
    def test_fail(self):
        r = executors.run("python", PY_SOL_BAD, PY_TEST_FAIL)
        self.assertFalse(r["passed"])
        self.assertIn("AssertionError", r["output"])
    def test_no_solution_code(self):
        r = executors.run("python", None, PY_TEST_PASS)
        self.assertFalse(r["passed"])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: verify it fails** → FAIL.

- [ ] **Step 3: implement executors.py (python + base sandbox)**

`benchmark/executors.py`:
```python
import subprocess, tempfile, os, time, shutil

def _sandbox_prefix(timeout):
    """Command prefix to isolate: timeout + blocked network if unshare is available."""
    prefix = ["timeout", str(timeout)]
    # unshare -n blocks the network (requires user namespace permission); if it fails, it is omitted.
    if shutil.which("unshare"):
        prefix += ["unshare", "-n"]
    return prefix

def run(lang, solution_code, test_code, timeout=30):
    """Write solution+test into a tempdir, run according to lang, return the result."""
    if solution_code is None:
        return {"passed": False, "output": "no solution code block found", "elapsed_ms": 0}
    started = time.time()
    tmp = tempfile.mkdtemp(prefix="mbench_")
    try:
        return _run_in(tmp, lang, solution_code, test_code, timeout, started)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def _run_in(tmp, lang, solution_code, test_code, timeout, started):
    if lang == "python":
        return _python(tmp, solution_code, test_code, timeout, started)
    raise ValueError(f"lang not implemented yet: {lang}")

def _python(tmp, solution_code, test_code, timeout, started):
    with open(os.path.join(tmp, "solution.py"), "w") as f:
        f.write(solution_code)
    with open(os.path.join(tmp, "test_solution.py"), "w") as f:
        f.write(test_code)
    cmd = _sandbox_prefix(timeout) + ["python3", "test_solution.py"]
    p = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, timeout=timeout + 5)
    out = (p.stdout + p.stderr).strip()
    return {"passed": p.returncode == 0, "output": out[-2000:],
            "elapsed_ms": int((time.time() - started) * 1000)}
```

- [ ] **Step 4: verify pass**

Run: `python -m unittest benchmark.tests.test_executors -v` → 3 PASS.

- [ ] **Step 5: commit**

```bash
git add -A && git commit -m "feat: executors.py (python runner + sandbox)"
```

---

## Task 5: executors.py — bash, java, typescript

**Files:**
- Modify: `benchmark/executors.py` (add `_bash`, `_java`, `_typescript` and dispatch them in `_run_in`)
- Modify: `benchmark/tests/test_executors.py` (add tests)

**Interfaces:**
- Extends: `executors.run(lang, ...)` supports `bash|java|typescript` in addition to `python`.

- [ ] **Step 1: add tests**

Add to `tests/test_executors.py`:
```python
    def test_bash_pass(self):
        sol = 'add() { echo $(($1+$2)); }\n'
        tst = 'source solution.sh\n[ "$(add 2 3)" = "5" ] || { echo FAIL; exit 1; }\necho OK\n'
        r = executors.run("bash", sol, tst)
        self.assertTrue(r["passed"])
    def test_bash_fail(self):
        sol = 'add() { echo $(($1-$2)); }\n'
        tst = 'source solution.sh\n[ "$(add 2 3)" = "5" ] || exit 1\n'
        r = executors.run("bash", sol, tst)
        self.assertFalse(r["passed"])
    def test_java_pass(self):
        sol = 'public class Solution { public static int add(int a,int b){ return a+b; } }\n'
        tst = ('public class Test { public static void main(String[] a){\n'
               ' if (Solution.add(2,3)!=5) throw new RuntimeException("FAIL");\n'
               ' System.out.println("OK"); } }\n')
        r = executors.run("java", sol, tst)
        self.assertTrue(r["passed"], r["output"])
    def test_java_fail(self):
        sol = 'public class Solution { public static int add(int a,int b){ return a-b; } }\n'
        tst = ('public class Test { public static void main(String[] a){\n'
               ' if (Solution.add(2,3)!=5) throw new RuntimeException("FAIL"); } }\n')
        r = executors.run("java", sol, tst)
        self.assertFalse(r["passed"])
    def test_typescript_pass(self):
        sol = 'export function add(a:number,b:number):number { return a+b; }\n'
        tst = 'import { add } from "./solution";\nif (add(2,3)!==5) throw new Error("FAIL");\nconsole.log("OK");\n'
        r = executors.run("typescript", sol, tst)
        self.assertTrue(r["passed"], r["output"])
```

- [ ] **Step 2: verify it fails** (4 new FAILs: bash/java/ts not implemented).

- [ ] **Step 3: implement the 3 languages**

Dispatch and add to `executors.py` (`_run_in`):
```python
def _run_in(tmp, lang, solution_code, test_code, timeout, started):
    runners = {"python": _python, "bash": _bash, "java": _java, "typescript": _typescript}
    if lang not in runners:
        raise ValueError(f"lang not supported: {lang}")
    return runners[lang](tmp, solution_code, test_code, timeout, started)

def _bash(tmp, solution_code, test_code, timeout, started):
    with open(os.path.join(tmp, "solution.sh"), "w") as f:
        f.write(solution_code)
    with open(os.path.join(tmp, "test_solution.sh"), "w") as f:
        f.write(test_code)
    cmd = _sandbox_prefix(timeout) + ["bash", "test_solution.sh"]
    p = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, timeout=timeout + 5)
    out = (p.stdout + p.stderr).strip()
    return {"passed": p.returncode == 0, "output": out[-2000:],
            "elapsed_ms": int((time.time() - started) * 1000)}

def _java(tmp, solution_code, test_code, timeout, started):
    with open(os.path.join(tmp, "Solution.java"), "w") as f:
        f.write(solution_code)
    with open(os.path.join(tmp, "Test.java"), "w") as f:
        f.write(test_code)
    pre = _sandbox_prefix(timeout)
    comp = subprocess.run(pre + ["javac", "Solution.java", "Test.java"],
                          cwd=tmp, capture_output=True, text=True, timeout=timeout + 5)
    if comp.returncode != 0:
        return {"passed": False, "output": ("compile error:\n" + comp.stderr)[:2000],
                "elapsed_ms": int((time.time() - started) * 1000)}
    run = subprocess.run(pre + ["java", "Test"], cwd=tmp,
                         capture_output=True, text=True, timeout=timeout + 5)
    out = (run.stdout + run.stderr).strip()
    return {"passed": run.returncode == 0, "output": out[-2000:],
            "elapsed_ms": int((time.time() - started) * 1000)}

def _typescript(tmp, solution_code, test_code, timeout, started):
    with open(os.path.join(tmp, "solution.ts"), "w") as f:
        f.write(solution_code)
    with open(os.path.join(tmp, "test_solution.ts"), "w") as f:
        f.write(test_code)
    cmd = _sandbox_prefix(timeout) + ["bun", "test_solution.ts"]
    p = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, timeout=timeout + 5)
    out = (p.stdout + p.stderr).strip()
    return {"passed": p.returncode == 0, "output": out[-2000:],
            "elapsed_ms": int((time.time() - started) * 1000)}
```

- [ ] **Step 4: verify pass** (all 8 tests)

Run: `python -m unittest benchmark.tests.test_executors -v` → 8 PASS.

- [ ] **Step 5: commit**

```bash
git add -A && git commit -m "feat: executors per bash, java, typescript"
```

---

## Task 6: server.py — build_args + ServerManager

**Files:**
- Create: `benchmark/server.py`, `benchmark/tests/test_server.py`

**Interfaces:**
- Produces: `server.build_args(model_path, context_mode, port) -> list[str]` (all the args, model included); `server.ServerManager(model_path, context_mode, port)` with `.start()`, `.wait_ready(timeout=180) -> bool`, `.stop()`, `.is_alive() -> bool`. `context_mode` is `"fixed"` or `adapted` or an integer.

- [ ] **Step 1: failing test**

`benchmark/tests/test_server.py`:
```python
import unittest
from benchmark import server, config

class TestBuildArgs(unittest.TestCase):
    def test_fixed_context(self):
        a = server.build_args("/p/m.gguf", "fixed", 8999)
        self.assertIn("-m", a)
        i = a.index("-m"); self.assertEqual(a[i+1], "/p/m.gguf")
        self.assertIn("-c", a)
        i = a.index("-c"); self.assertEqual(a[i+1], str(config.CONTEXT_FIXED))
        self.assertIn("--port", a)
        i = a.index("--port"); self.assertEqual(a[i+1], "8999")
    def test_explicit_context_int(self):
        a = server.build_args("/p/m.gguf", 4096, 8000)
        i = a.index("-c"); self.assertEqual(a[i+1], "4096")
    def test_flags_all_present(self):
        a = server.build_args("/p/m.gguf", "fixed", 8999)
        for flag in ["-ngl", "--flash-attn", "--no-mmap", "--jinja", "--temp", "--seed"]:
            self.assertIn(flag, a)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: verify it fails** → FAIL.

- [ ] **Step 3: implement server.py**

`benchmark/server.py`:
```python
import subprocess, time, urllib.request, json
from . import config

def resolve_context(context_mode, model_path):
    """fixed -> CONTEXT_FIXED; int -> int; adapted -> estimate viable (fallback 8192)."""
    if isinstance(context_mode, int):
        return context_mode
    if context_mode == "fixed":
        return config.CONTEXT_FIXED
    # adapted: delegate to an external estimator when available; safe fallback
    return 8192

def build_args(model_path, context_mode, port):
    ctx = resolve_context(context_mode, model_path)
    return [config.SERVER_BIN,
            "-m", str(model_path),
            "-c", str(ctx),
            "--port", str(port),
            *config.SERVER_FLAGS]

class ServerManager:
    def __init__(self, model_path, context_mode="fixed", port=None):
        self.model_path = str(model_path)
        self.context_mode = context_mode
        self.port = port or config.PORT
        self.proc = None

    def start(self):
        args = build_args(self.model_path, self.context_mode, self.port)
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return self.proc

    def is_alive(self):
        return self.proc is not None and self.proc.poll() is None

    def wait_ready(self, timeout=180):
        """Ready when a test chat returns 'choices' (not just /v1/models)."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if not self.is_alive():
                return False
            try:
                req = urllib.request.Request(
                    f"http://127.0.0.1:{self.port}/v1/chat/completions",
                    data=json.dumps({"messages":[{"role":"user","content":"hi"}],"max_tokens":1}).encode(),
                    headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    if '"choices"' in r.read().decode("utf-8", "replace"):
                        return True
            except Exception:
                pass
            time.sleep(1)
        return False

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.kill()
            try: self.proc.wait(timeout=10)
            except Exception: pass
        self.proc = None
```

- [ ] **Step 4: verify pass**

Run: `python -m unittest benchmark.tests.test_server -v` → 3 PASS.

- [ ] **Step 5: commit**

```bash
git add -A && git commit -m "feat: server.py (build_args + ServerManager lifecycle)"
```

---

## Task 7: agent.py — MockEnv + tools + run_agent loop

**Files:**
- Create: `benchmark/agent.py`, `benchmark/tests/test_agent.py`

**Interfaces:**
- Produces: `agent.MockEnv(files: dict[str,str], lang: str)` with `.read_file(path)`, `.write_file(path, content)`, `.run_tests(test_filename)`; `agent.run_agent(client_mod, task, max_turns=8) -> dict` where `task` is `{"lang","goal","initial_files","test_file"}` and the result is `{"success": bool, "turns": int, "tool_calls": int}`. Uses `executors.run` for `run_tests`.

- [ ] **Step 1: failing test**

`benchmark/tests/test_agent.py`:
```python
import unittest
from benchmark import agent

class TestMockEnv(unittest.TestCase):
    def test_read_write(self):
        e = agent.MockEnv({"a.py": "x=1"}, "python")
        self.assertEqual(e.read_file("a.py"), "x=1")
        e.write_file("a.py", "x=2")
        self.assertEqual(e.read_file("a.py"), "x=2")
    def test_read_missing(self):
        e = agent.MockEnv({}, "python")
        self.assertIn("no such file", e.read_file("nope.py").lower())
    def test_run_tests_pass(self):
        e = agent.MockEnv({"solution.py": "def add(a,b):\n    return a+b\n",
                           "test_solution.py": "from solution import *\nassert add(1,2)==3\n"},
                          "python")
        ok, out = e.run_tests()
        self.assertTrue(ok)
    def test_run_tests_fail(self):
        e = agent.MockEnv({"solution.py": "def add(a,b):\n    return a-b\n",
                           "test_solution.py": "from solution import *\nassert add(1,2)==3\n"},
                          "python")
        ok, out = e.run_tests()
        self.assertFalse(ok)

class TestRunAgentScripted(unittest.TestCase):
    def test_scripted_success(self):
        # fake client: first calls write_file with the correct solution, then stops
        calls = {"n": 0}
        class FakeClient:
            def chat(self, messages, tools=None, tool_choice=None, max_tokens=256):
                calls["n"] += 1
                if calls["n"] == 1:
                    return {"choices":[{"finish_reason":"tool_calls","message":{
                        "tool_calls":[{"function":{"name":"write_file",
                        "arguments":'{"path":"solution.py","content":"def add(a,b):\\n    return a+b\\n"}'}]}}]}}
                return {"choices":[{"finish_reason":"stop","message":{"content":"done"}}]}
        task = {"lang":"python","goal":"fix add",
                "initial_files":{"solution.py":"def add(a,b):\n    return a-b\n",
                                 "test_solution.py":"from solution import *\nassert add(1,2)==3\n"},
                "test_file":"test_solution.py"}
        r = agent.run_agent(FakeClient(), task, max_turns=4)
        self.assertTrue(r["success"])
        self.assertEqual(r["tool_calls"], 1)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: verify it fails** → FAIL.

- [ ] **Step 3: implement agent.py**

`benchmark/agent.py`:
```python
import json
from . import executors

# Schema of the tools passed to the model.
TOOLS = [
    {"type": "function", "function": {
        "name": "read_file", "description": "Read a file from the project.",
        "parameters": {"type": "object",
                       "properties": {"path": {"type": "string"}},
                       "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "write_file", "description": "Write content to a file (create or overwrite).",
        "parameters": {"type": "object",
                       "properties": {"path": {"type": "string"},
                                      "content": {"type": "string"}},
                       "required": ["path", "content"]}}},
    {"type": "function", "function": {
        "name": "run_tests", "description": "Run the project's tests.",
        "parameters": {"type": "object", "properties": {},
                       "required": []}}},
]

class MockEnv:
    def __init__(self, files, lang, test_file="test_solution.py"):
        self.files = dict(files)
        self.lang = lang
        self.test_file = test_file

    def read_file(self, path):
        if path in self.files:
            return self.files[path]
        return f"error: no such file: {path}"

    def write_file(self, path, content):
        self.files[path] = content
        return f"wrote {len(content)} bytes to {path}"

    def run_tests(self):
        # Run all the files in a tempdir via the language executor.
        # For simplicity: join solution+test according to the language.
        if self.lang == "python":
            sol = self.files.get("solution.py", "")
            tst = self.files.get(self.test_file, "")
            r = executors.run("python", sol, tst)
        else:
            # other langs: delegate to executors with the solution+test convention
            r = self._run_other()
        return (r["passed"], r["output"])

    def _run_other(self):
        # Convention: solution.<ext> + test_solution.<ext>
        ext = {"bash": ".sh", "java": ".java", "typescript": ".ts"}[self.lang]
        sol = self.files.get("solution" + ext, "")
        tst = self.files.get("test_solution" + ext, self.files.get(self.test_file, ""))
        return executors.run(self.lang, sol, tst)

def _exec_tool(name, args, env):
    if name == "read_file":
        return env.read_file(args.get("path", ""))
    if name == "write_file":
        return env.write_file(args.get("path", ""), args.get("content", ""))
    if name == "run_tests":
        ok, out = env.run_tests()
        return ("TESTS PASS" if ok else "TESTS FAIL") + f"\n{out[-1500:]}"
    return f"error: unknown tool {name}"

def run_agent(client_mod, task, max_turns=8):
    env = MockEnv(task["initial_files"], task["lang"], task.get("test_file", "test_solution.py"))
    history = [{"role": "system", "content":
                "You solve coding tasks using tools. When done, reply with a short summary."},
               {"role": "user", "content": task["goal"]}]
    tool_calls = 0
    for _turn in range(max_turns):
        resp = client_mod.chat(history, tools=TOOLS, tool_choice="auto", max_tokens=512)
        msg = (resp.get("choices", [{}])[0]).get("message", {})
        tcs = msg.get("tool_calls") or []
        history.append(msg)
        if not tcs:
            break
        for tc in tcs:
            fn = tc.get("function", tc)
            name = fn.get("name")
            try:
                args = json.loads(fn.get("arguments", "{}")) if isinstance(fn.get("arguments"), str) else (fn.get("arguments") or {})
            except Exception:
                args = {}
            tool_calls += 1
            result = _exec_tool(name, args, env)
            history.append({"role": "tool", "tool_call_id": tc.get("id", "x"), "content": result})
    ok, _ = env.run_tests()
    return {"success": ok, "turns": _turn + 1 if not tcs else _turn + 1,
            "tool_calls": tool_calls}
```

- [ ] **Step 4: verify pass**

Run: `python -m unittest benchmark.tests.test_agent -v` → 5 PASS.

- [ ] **Step 5: commit**

```bash
git add -A && git commit -m "feat: agent.py (MockEnv + multi-step loop + tools)"
```

---

## Task 8: graders.py — speed, tools, code, agent

**Files:**
- Create: `benchmark/graders.py`, `benchmark/tests/test_graders.py`

**Interfaces:**
- Consumes: `client`, `code_extract`, `executors`, `agent`, `config`.
- Produces: `graders.grade_speed(client_mod, n=3) -> dict`; `graders.grade_tools(client_mod, tasks) -> dict`; `graders.grade_code(client_mod, tasks) -> dict`; `graders.grade_agent(client_mod, tasks) -> dict`. Each dict has `score` (0..1); code and agent also `by_lang` and `tasks`.

- [ ] **Step 1: failing test**

`benchmark/tests/test_graders.py`:
```python
import unittest
from benchmark import graders

class FakeClient:
    """Client that can be scripted with a sequence of responses per task."""
    def __init__(self, responses):
        self.responses = list(responses); self.i = 0
    def chat(self, *a, **k):
        r = self.responses[self.i % len(self.responses)]; self.i += 1
        return r

class TestToolsGrader(unittest.TestCase):
    def test_pass_and_fail(self):
        tasks = [
            {"name":"t1","prompt":"x","tools":[],"expected":{"name":"f","arguments":{"a":1}}},
            {"name":"t2","prompt":"y","tools":[],"expected":{"name":"g","arguments":{}}},
        ]
        resp_pass = {"choices":[{"finish_reason":"tool_calls","message":{"tool_calls":[
            {"function":{"name":"f","arguments":'{"a":1}'}}]}}]}
        resp_fail = {"choices":[{"finish_reason":"tool_calls","message":{"tool_calls":[
            {"function":{"name":"g","arguments":'{"b":2}'}}]}}], "timings":{}}
        r = graders.grade_tools(FakeClient([resp_pass, resp_fail]), tasks)
        self.assertEqual(r["score"], 0.5)
        self.assertEqual(r["by_lang"], {})  # tools has no by_lang
    def test_noop_case(self):
        tasks = [{"name":"noop","prompt":"hola","tools":[],"expected":None}]  # None = must not call
        resp = {"choices":[{"finish_reason":"stop","message":{"content":"hola!"}}]}
        r = graders.grade_tools(FakeClient([resp]), tasks)
        self.assertEqual(r["score"], 1.0)

class TestCodeGrader(unittest.TestCase):
    def test_extract_and_run(self):
        tasks = [{"name":"add","lang":"python","prompt":"implement add",
                  "test_code":"from solution import *\nassert add(1,2)==3\n"}]
        resp = {"choices":[{"message":{"content":"```python\ndef add(a,b):\n    return a+b\n```"}}]}
        r = graders.grade_code(FakeClient([resp]), tasks)
        self.assertEqual(r["score"], 1.0)
        self.assertEqual(r["by_lang"], {"python": 1.0})

class TestSpeedGrader(unittest.TestCase):
    def test_median(self):
        def make(tps): return {"timings":{"predicted_per_second":tps}}
        r = graders.grade_speed(FakeClient([make(10), make(20), make(30)]), n=3)
        self.assertAlmostEqual(r["gen_tps"], 20.0)  # median of [10,20,30]

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: verify it fails** → FAIL.

- [ ] **Step 3: implement graders.py**

`benchmark/graders.py`:
```python
import statistics
from . import client as C, code_extract, executors, agent as A

SPEED_PROMPT = "Write a short poem about the sea."
SPEED_MAX_TOKENS = 128

def grade_speed(client_mod, n=3):
    tps_list, ptps_list = [], []
    for _ in range(n):
        resp = client_mod.chat([{"role": "user", "content": SPEED_PROMPT}],
                               max_tokens=SPEED_MAX_TOKENS)
        t = C.parse_timings(resp)
        if t and t.get("gen_tps"):
            tps_list.append(t["gen_tps"])
            if t.get("prompt_tps"):
                ptps_list.append(t["prompt_tps"])
    return {"gen_tps": statistics.median(tps_list) if tps_list else None,
            "prompt_tps": statistics.median(ptps_list) if ptps_list else None,
            "_raw_tps": tps_list}

def _args_equal(got, expected):
    if expected is None:
        return got is None
    if got is None:
        return False
    return got == expected

def grade_tools(client_mod, tasks):
    results = []
    for t in tasks:
        resp = client_mod.chat([{"role": "user", "content": t["prompt"]}],
                               tools=t.get("tools", []), max_tokens=128)
        got = C.extract_tool_call(resp)
        exp = t.get("expected")
        if exp is None:
            passed = got is None
            detail = "correctly did not call a tool" if passed else f"unexpected call: {got}"
        else:
            passed = (got is not None and got.get("name") == exp.get("name")
                      and _args_equal(got.get("arguments"), exp.get("arguments")))
            detail = f"got={got} expected={exp}"
        results.append({"name": t["name"], "lang": None, "pass": passed, "detail": detail[:160]})
    score = sum(1 for r in results if r["pass"]) / len(results) if results else 0.0
    return {"score": score, "by_lang": {}, "tasks": results}

def grade_code(client_mod, tasks):
    results, by_lang = [], {}
    for t in tasks:
        resp = client_mod.chat([{"role": "user", "content": t["prompt"]}], max_tokens=1024)
        code = code_extract.extract(C.first_text(resp), t["lang"])
        r = executors.run(t["lang"], code, t["test_code"])
        results.append({"name": t["name"], "lang": t["lang"], "pass": r["passed"],
                        "detail": r["output"][:160], "elapsed_ms": r["elapsed_ms"]})
        by_lang.setdefault(t["lang"], []).append(r["passed"])
    bl = {k: (sum(v) / len(v)) for k, v in by_lang.items()}
    score = sum(1 for r in results if r["pass"]) / len(results) if results else 0.0
    return {"score": score, "by_lang": bl, "tasks": results}

def grade_agent(client_mod, tasks):
    results, by_lang = [], {}
    for t in tasks:
        r = A.run_agent(client_mod, t, max_turns=t.get("max_turns", 8))
        results.append({"name": t["name"], "lang": t["lang"], "pass": r["success"],
                        "detail": f"turns={r['turns']} tool_calls={r['tool_calls']}"})
        by_lang.setdefault(t["lang"], []).append(r["success"])
    bl = {k: (sum(v) / len(v)) for k, v in by_lang.items()}
    score = sum(1 for r in results if r["pass"]) / len(results) if results else 0.0
    return {"score": score, "by_lang": bl, "tasks": results}
```

- [ ] **Step 4: verify pass**

Run: `python -m unittest benchmark.tests.test_graders -v` → 4 PASS (classes).

- [ ] **Step 5: commit**

```bash
git add -A && git commit -m "feat: graders.py (speed/tools/code/agent + by_lang)"
```

---

## Task 9: tasks_loader.py — discover tasks

**Files:**
- Create: `benchmark/tasks_loader.py`, `benchmark/tests/test_tasks_loader.py`
- Create: example task: `tasks/tools/_example.py` (deleted at the end of the task), to test loading.

**Interfaces:**
- Produces: `tasks_loader.load(dimension, lang_filter=None) -> list[dict]`. Loads all the `tasks/<dim>/**/*.py` (each file defines constants), ignoring those starting with `_`. Each module becomes a dict according to the dimension.

- [ ] **Step 1: failing test**

`benchmark/tests/test_tasks_loader.py`:
```python
import unittest, os, textwrap
from benchmark import tasks_loader

class TestLoad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # create a temporary tools task
        d = os.path.join(os.path.dirname(__file__), "..", "tasks", "tools")
        open(os.path.join(d, "_tmpexample.py"), "w").write(textwrap.dedent('''
            NAME = "tmp"
            PROMPT = "hi"
            TOOLS = []
            EXPECTED = None
        '''))
    @classmethod
    def tearDownClass(cls):
        p = os.path.join(os.path.dirname(__file__), "..", "tasks", "tools", "_tmpexample.py")
        if os.path.exists(p): os.remove(p)
    def test_load_returns_list(self):
        # _tmpexample starts with _ -> ignored; only real tasks
        ts = tasks_loader.load("tools")
        self.assertIsInstance(ts, list)
    def test_skips_underscore(self):
        ts = tasks_loader.load("tools")
        self.assertFalse(any(t["name"] == "tmp" for t in ts))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: verify it fails** → FAIL.

- [ ] **Step 3: implement tasks_loader.py**

`benchmark/tasks_loader.py`:
```python
import importlib.util, pathlib
from . import config

_DIM_DIR = {"speed": "speed", "tools": "tools", "code": "code", "agent": "agent"}

def _load_module(path):
    spec = importlib.util.spec_from_file_location(path.stem, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def load(dimension, lang_filter=None):
    base = config.BENCH_DIR / "tasks" / _DIM_DIR[dimension]
    out = []
    files = sorted(p for p in base.rglob("*.py") if not p.name.startswith("_") and p.name != "__init__.py")
    for p in files:
        # filter by language (subfolder for code/agent)
        if lang_filter:
            rel = p.relative_to(base)
            lang_part = rel.parts[0] if len(rel.parts) > 1 else None
            if lang_part and lang_part not in lang_filter:
                continue
        m = _load_module(p)
        if dimension == "tools":
            out.append({"name": getattr(m, "NAME", p.stem), "prompt": m.PROMPT,
                        "tools": getattr(m, "TOOLS", []), "expected": getattr(m, "EXPECTED", None)})
        elif dimension == "speed":
            out.append({"name": getattr(m, "NAME", p.stem), "prompt": getattr(m, "PROMPT", "")})
        elif dimension == "code":
            out.append({"name": getattr(m, "NAME", p.stem), "lang": m.LANG,
                        "prompt": m.PROMPT, "test_code": m.TEST_CODE})
        elif dimension == "agent":
            out.append({"name": getattr(m, "NAME", p.stem), "lang": m.LANG, "goal": m.GOAL,
                        "initial_files": getattr(m, "INITIAL_FILES", {}),
                        "test_file": getattr(m, "TEST_FILE", "test_solution.py"),
                        "max_turns": getattr(m, "MAX_TURNS", 8)})
    return out
```

- [ ] **Step 4: verify pass**

Run: `python -m unittest benchmark.tests.test_tasks_loader -v` → 2 PASS.

- [ ] **Step 5: commit**

```bash
git add -A && git commit -m "feat: tasks_loader.py (descobrir/carregar tasks per dimensió)"
```

---

## Task 10: report.py — tables, persistence, normalization

**Files:**
- Create: `benchmark/report.py`, `benchmark/tests/test_report.py`

**Interfaces:**
- Consumes: `config`.
- Produces: `report.save_result(result_dict)` (to `results/models/<slug>.json` + `results/runs/<ts>-<slug>.json`); `report.load_pool() -> list[dict]`; `report.compute_global(result, weights, pool) -> float` (speed normalized over the pool); `report.render(pool, weights, verbose=False) -> str` (returns the formatted tables); `report.lang_profile(result, threshold) -> dict`.

- [ ] **Step 1: failing test**

`benchmark/tests/test_report.py`:
```python
import unittest
from benchmark import report, config

def mk(model, gen_tps=None, tools=1.0, code=1.0, agent=1.0,
       code_lang=None, agent_lang=None):
    return {"model": model, "context_mode":"fixed", "ts":"2026-08-03T00:00:00",
            "tasks_version":"x", "server_build":"10250",
            "speed":{"gen_tps":gen_tps},
            "tools":{"score":tools,"by_lang":{},"tasks":[]},
            "code":{"score":code,"by_lang":code_lang or {},"tasks":[]},
            "agent":{"score":agent,"by_lang":agent_lang or {},"tasks":[]}}

class TestReport(unittest.TestCase):
    def test_global_no_speed(self):
        r = mk("m", gen_tps=None)
        # without speed, normalize over the rest
        g = report.compute_global(r, config.WEIGHTS, [r])
        self.assertAlmostEqual(g, 0.30+0.30+0.25)  # speed 0
    def test_global_speed_normalized(self):
        a = mk("a", gen_tps=50); b = mk("b", gen_tps=100)
        pool=[a,b]
        ga = report.compute_global(a, config.WEIGHTS, pool)
        gb = report.compute_global(b, config.WEIGHTS, pool)
        self.assertGreater(gb, ga)  # the faster one (b) has a higher global
    def test_lang_profile(self):
        r = mk("m", code_lang={"python":1.0,"java":0.0}, agent_lang={"python":0.5})
        prof = report.lang_profile(r, threshold=0.75)
        self.assertIn("python", prof["strong"])
        self.assertIn("java", prof["weak"])
    def test_render_has_headers(self):
        pool=[mk("a"), mk("b")]
        out = report.render(pool, config.WEIGHTS)
        self.assertIn("GLOBAL", out)
        self.assertIn("code:py", out)  # per-language header

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: verify it fails** → FAIL.

- [ ] **Step 3: implement report.py**

`benchmark/report.py`:
```python
import json, datetime
from pathlib import Path
from . import config

_LANGS = ["python", "bash", "java", "typescript"]
_LANG_HEAD = {"python":"py", "bash":"bas", "java":"java", "typescript":"ts"}

def _slug_of(result):
    return config.slug(result["model"])

def save_result(result):
    config.RESULTS_MODELS.mkdir(parents=True, exist_ok=True)
    config.RESULTS_RUNS.mkdir(parents=True, exist_ok=True)
    slug = _slug_of(result)
    (config.RESULTS_MODELS / f"{slug}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    (config.RESULTS_RUNS / f"{ts}-{slug}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))

def load_pool():
    files = sorted(config.RESULTS_MODELS.glob("*.json"))
    return [json.loads(f.read_text()) for f in files]

def forget(model_name):
    p = config.RESULTS_MODELS / f"{config.slug(model_name)}.json"
    if p.exists(): p.unlink()

def _max_tps(pool):
    return max((r.get("speed", {}).get("gen_tps") or 0) for r in pool) if pool else 0

def compute_global(result, weights, pool):
    s = result.get("speed", {}).get("gen_tps")
    mx = _max_tps(pool) or 1
    speed_norm = (s / mx) if s else 0.0
    tools = result.get("tools", {}).get("score", 0.0)
    code = result.get("code", {}).get("score", 0.0)
    agent = result.get("agent", {}).get("score", 0.0)
    return (weights["tools"]*tools + weights["code"]*code +
            weights["agent"]*agent + weights["speed"]*speed_norm)

def lang_profile(result, threshold=None):
    threshold = threshold if threshold is not None else config.LANG_OK_THRESHOLD
    strong, weak = [], []
    for dim in ("code", "agent"):
        for lang, sc in result.get(dim, {}).get("by_lang", {}).items():
            if sc is None: continue
            (strong if sc >= threshold else weak).append(f"{dim}:{lang}")
    return {"strong": strong, "weak": weak}

def _fmt_pct(x):
    return "  — " if x is None else f"{int(round(x*100)):3d}%"

def render(pool, weights, verbose=False):
    if not pool:
        return "(sense resultats al pool)"
    rows = sorted(pool, key=lambda r: -compute_global(r, weights, pool))
    out = []
    # Table 1 — global
    out.append("=== Global ===")
    out.append(f"{'MODEL':30} {'gen_tps':>8} {'tools':>6} {'code':>6} {'agent':>6} {'GLOBAL':>7}")
    for r in rows:
        tps = r.get("speed", {}).get("gen_tps")
        out.append(f"{r['model'][:30]:30} {(f'{tps:.1f}' if tps else '  —'):>8} "
                   f"{_fmt_pct(r.get('tools',{}).get('score')):>6} "
                   f"{_fmt_pct(r.get('code',{}).get('score')):>6} "
                   f"{_fmt_pct(r.get('agent',{}).get('score')):>6} "
                   f"{compute_global(r, weights, pool):>7.2f}")
    # Table 2 — per language
    out.append("\n=== Per llenguatge ===")
    head = f"{'MODEL':30} " + " ".join(f"code:{_LANG_HEAD[l]:>4}" for l in _LANGS) \
           + "  " + " ".join(f"agent:{_LANG_HEAD[l]:>4}" for l in _LANGS)
    out.append(head)
    for r in rows:
        c = r.get("code", {}).get("by_lang", {})
        a = r.get("agent", {}).get("by_lang", {})
        cells = [_fmt_pct(c.get(l)) for l in _LANGS] + [_fmt_pct(a.get(l)) for l in _LANGS]
        out.append(f"{r['model'][:30]:30} " + " ".join(f"{x:>9}" for x in cells))
    # Profile
    out.append("\n=== Perfil (≥{:.0%}) ===".format(config.LANG_OK_THRESHOLD))
    for r in rows:
        p = lang_profile(r)
        out.append(f"{r['model'][:30]:30} fort: {', '.join(p['strong']) or '—'} | fluix: {', '.join(p['weak']) or '—'}")
    # Detail
    if verbose:
        out.append("\n=== Detall per tasca ===")
        out.append(f"{'MODEL':24} {'DIM':6} {'LANG':10} {'TASK':18} {'PASS':5} DETALL")
        for r in rows:
            for dim in ("tools", "code", "agent"):
                for t in r.get(dim, {}).get("tasks", []):
                    out.append(f"{r['model'][:24]:24} {dim:6} {(t.get('lang') or '—'):10} "
                               f"{t['name'][:18]:18} {'✓' if t['pass'] else '✗':5} {t.get('detail','')[:60]}")
    return "\n".join(out)
```

- [ ] **Step 4: verify pass**

Run: `python -m unittest benchmark.tests.test_report -v` → 4 PASS.

- [ ] **Step 5: commit**

```bash
git add -A && git commit -m "feat: report.py (taules global/per-lleng+perfil, pool, normalització)"
```

---

## Task 11: run.py — CLI and orchestration

**Files:**
- Create: `benchmark/run.py`, `benchmark/tests/test_run_cli.py` (args test, no network)

**Interfaces:**
- Consumes: all the above.
- Produces: executable `python -m benchmark.run` o `python benchmark/run.py`.

- [ ] **Step 1: failing test (CLI parsing)**

`benchmark/tests/test_run_cli.py`:
```python
import unittest
from benchmark import run

class TestParseWeights(unittest.TestCase):
    def test_parse_weights(self):
        w = run.parse_weights("tools=0.4,code=0.3,agent=0.2,speed=0.1")
        self.assertAlmostEqual(w["tools"], 0.4)
        self.assertAlmostEqual(sum(w.values()), 1.0)
    def test_resolve_models_explicit(self):
        ms = run.resolve_models(["a.gguf","b.gguf"])
        self.assertEqual(ms, ["a.gguf", "b.gguf"])
    def test_resolve_models_all(self):
        ms = run.resolve_models("all")
        self.assertIsInstance(ms, list)
        self.assertTrue(all(str(m).endswith(".gguf") for m in ms))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: verify it fails** → FAIL.

- [ ] **Step 3: implement run.py**

`benchmark/run.py`:
```python
import argparse, json, sys, datetime
from . import config, server as S, client as C, graders as G, tasks_loader as T, report as R

def parse_weights(s):
    if not s: return dict(config.WEIGHTS)
    w = {}
    for part in s.split(","):
        k, v = part.split("="); w[k.strip()] = float(v)
    return w

def resolve_models(spec):
    if spec == "all":
        return sorted(str(p) for p in config.MODELS_DIR.glob("*.gguf"))
    if isinstance(spec, str):
        spec = [x.strip() for x in spec.split(",")]
    return spec

def _bench_one(model_path, dims, context_mode, lang_filter, port):
    sm = S.ServerManager(model_path, context_mode=context_mode, port=port)
    print(f"→ arrencant {model_path}...", flush=True)
    sm.start()
    if not sm.wait_ready(timeout=240):
        sm.stop(); return {"model": model_path, "serve_failed": True}
    try:
        class Client: pass
        c = Client(); c.chat = lambda *a, **k: C.chat(*a, base_url=f"http://127.0.0.1:{port}", **{**k})
        # warmup
        try: C.chat([{"role":"user","content":"hi"}], max_tokens=4, base_url=f"http://127.0.0.1:{port}")
        except Exception: pass
        result = {"model": model_path, "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                  "context_mode": context_mode, "tasks_version": "v1",
                  "server_build": _server_build()}
        lf = set(lang_filter) if lang_filter else None
        if "speed" in dims:
            result["speed"] = G.grade_speed(c)
        if "tools" in dims:
            result["tools"] = G.grade_tools(c, T.load("tools"))
        if "code" in dims:
            result["code"] = G.grade_code(c, T.load("code", lang_filter=lf))
        if "agent" in dims:
            result["agent"] = G.grade_agent(c, T.load("agent", lang_filter=lf))
        return result
    finally:
        sm.stop()

def _server_build():
    try:
        import subprocess
        out = subprocess.run([str(config.SERVER_BIN), "--version"], capture_output=True, text=True, timeout=10)
        for line in out.stdout.splitlines():
            if line.startswith("version:"): return line.split()[1]
    except Exception: pass
    return "unknown"

def main(argv=None):
    ap = argparse.ArgumentParser(prog="benchmark")
    ap.add_argument("--models", default="all")
    ap.add_argument("--context", default="fixed", choices=["fixed", "adapted"])
    ap.add_argument("--dims", default="speed,tools,code,agent")
    ap.add_argument("--lang", default=None)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--scoreboard", action="store_true")
    ap.add_argument("--forget")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--port", type=int, default=config.PORT)
    ap.add_argument("--weights", default=None)
    args = ap.parse_args(argv)
    weights = parse_weights(args.weights)

    if args.forget:
        R.forget(args.forget); print(f"esborrat {args.forget} del pool"); return
    if args.scoreboard:
        pool = R.load_pool()
        print(R.render(pool, weights, verbose=args.verbose))
        return

    dims = [d.strip() for d in args.dims.split(",") if d.strip()]
    lang_filter = args.lang.split(",") if args.lang else None
    models = resolve_models(args.models)
    for mp in models:
        res = _bench_one(mp, dims, args.context, lang_filter, args.port)
        if res.get("serve_failed"):
            print(f"✗ {mp}: no carrega"); continue
        R.save_result(res)
    pool = R.load_pool()
    if args.json:
        print(json.dumps(pool, indent=2, ensure_ascii=False))
    else:
        print(R.render(pool, weights, verbose=args.verbose))

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: verify pass**

Run: `python -m unittest benchmark.tests.test_run_cli -v` → 3 PASS.

- [ ] **Step 5: commit**

```bash
git add -A && git commit -m "feat: run.py (CLI + orquestració per model)"
```

---

## Task 12: Task suite — speed + tools (8)

**Files:**
- Create: `tasks/speed/speed.py`, and 8 files in `tasks/tools/`.

**Schema of each tools task** (file `tasks/tools/<name>.py`):
```python
NAME = "<name>"
PROMPT = "<statement for the model>"
TOOLS = [ { ... definition of the tool(s)... } ]
EXPECTED = {"name": "<fn>", "arguments": {<expected args>}}   # or None for the no-op case
```

- [ ] **Step 1: speed task**

`tasks/speed/speed.py`:
```python
NAME = "speed"
PROMPT = "Write a short vivid poem about the sea and a lighthouse."
```
(The speed grader uses `graders.SPEED_PROMPT` internally; this task is a placeholder for consistent loading.)

- [ ] **Step 2: 8 tools tasks** — create the following files with `NAME/PROMPT/TOOLS/EXPECTED`:

1. `tasks/tools/single_arg.py` — asks for the weather in Paris; tool `get_weather(city)`; EXPECTED `get_weather({"city":"Paris"})`.
2. `tasks/tools/multi_arg.py` — asks to create an event; tool `create_event(title, date, location)`; EXPECTED with the 3 args (extracted from the statement: title="Standup", date="2026-09-01", location="Remote").
3. `tasks/tools/pick_right.py` — offers 3 tools (`get_weather`, `search_docs`, `send_email`); asks for "email the report to ana@x.com"; EXPECTED `send_email({"to":"ana@x.com","subject":"report"})` (must pick the right tool).
4. `tasks/tools/noop.py` — asks "explain what recursion is"; with tool `get_weather` available; EXPECTED `None` (must not call).
5. `tasks/tools/wrong_args.py` — asks for the weather in Tokyo; tool `get_weather(city)`; EXPECTED `get_weather({"city":"Tokyo"})` (checks that the argument is correct, not "Paris").
6. `tasks/tools/typed_number.py` — tool `set_volume(level: int)`; asks "set volume to 50"; EXPECTED `set_volume({"level":50})` (checks numeric type).
7. `tasks/tools/optional_arg.py` — tool `list_files(path="/")`; asks "list files"; EXPECTED `list_files({"path":"/"})` or `{}` (accepts the default).
8. `tasks/tools/chain_hint.py` — asks "get weather for Paris then save it"; tools `get_weather` and `save(key,value)`; EXPECTED the FIRST call = `get_weather({"city":"Paris"})` (checks that it starts with the right one).

Each file defines `TOOLS` with the full JSON schema of each function (type/description/parameters). The author fills in `PROMPT` and `TOOLS` following the schemas.

- [ ] **Step 3: loading smoke**

Run:
```bash
cd /home/jordi/ia/llama && python -c "from benchmark import tasks_loader as T; \
print('tools:', len(T.load('tools')), '| speed:', len(T.load('speed')))"
```
Expected: `tools: 8 | speed: 1`.

- [ ] **Step 4: commit**

```bash
git add -A && git commit -m "feat: tasques speed + 8 tools"
```

---

## Task 13: Task suite — code (8: 2 per language)

**Files:**
- Create: 2 files for `tasks/code/{python,bash,java,typescript}/`.

**Schema** (`tasks/code/<lang>/<name>.py`):
```python
NAME = "<name>"
LANG = "<python|bash|java|typescript>"
PROMPT = "<statement: asks the model to implement X, in a ```lang``` block>"
TEST_CODE = "<test code that imports/sources the solution and makes asserts>"
```

- [ ] **Step 1: define the 8 tasks** (2 per language):

| Lang | Task 1 (implement) | Task 2 (fix bug) |
|---|---|---|
| python | `stack.py`: implement `Stack` with `push/pop/peek` | `fib_fix.py`: fix fib (the given one returns n-1) |
| bash | `math.sh`: functions `sum` and `max2` | `reverse_fix.sh`: fix `reverse` (reversed wrongly) |
| java | `Solution.java`: static method `isPalindrome(String)` | `Solution.java`: fix `factorial` (overflow off-by-one) |
| typescript | `solution.ts`: `fizzbuzz(n)` returns string[] | `solution.ts`: fix `dedupe` (kept duplicates) |

Each `TEST_CODE` is a standalone test (imports/sources the solution, asserts, `exit 1`/throw on failure). Conventions:
- python: `from solution import *` + asserts.
- bash: `source solution.sh` + `[ ... ] || exit 1`.
- java: `public class Test { public static void main(...){ ... throw RuntimeException ... } }`.
- typescript: `import { ... } from "./solution"` + asserts (bun).

The `PROMPT` must explicitly ask for the block with the correct tag and the expected signature (e.g.: java asks for `public class Solution { ... }`).

- [ ] **Step 2: loading smoke**

Run:
```bash
cd /home/jordi/ia/llama && python -c "from benchmark import tasks_loader as T; \
import collections; c=T.load('code'); print(len(c), collections.Counter(t['lang'] for t in c))"
```
Expected: `8 Counter({'python': 2, 'bash': 2, 'java': 2, 'typescript': 2})`.

- [ ] **Step 3: validate the tests with known correct solutions**

For each task, run `executors.run(lang, <correct solution you write>, TEST_CODE)` and verify `passed==True`. Quick check script:
```bash
cd /home/jordi/ia/llama && python -c "
from benchmark import tasks_loader as T, executors
for t in T.load('code'):
    print(t['name'], t['lang'], '-> crea solució correcta manualment i verifica abans de commit')
"
```
(Manual authoring of the correct solutions to validate each `TEST_CODE`.)

- [ ] **Step 4: commit**

```bash
git add -A && git commit -m "feat: 8 tasques code (2 per idioma)"
```

---

## Task 14: Task suite — agent (6)

**Files:**
- Create: `tasks/agent/{python×2, typescript×2, java×1, bash×1}.py`.

**Schema** (`tasks/agent/<lang>/<name>.py`):
```python
NAME = "<name>"
LANG = "<python|bash|java|typescript>"
GOAL = "<goal for the model: what it must achieve>"
INITIAL_FILES = { "<path>": "<initial content (with bug)>" , "test_solution.<ext>": "<test>" }
TEST_FILE = "test_solution.<ext>"     # what run_tests executes
MAX_TURNS = 8
```

- [ ] **Step 1: define the 6 agent tasks**:

1. `agent/python/fix_offbyone.py` — `solution.py` has `def fib(n)` with an off-by-one bug; test checks `fib(10)==55`. Goal: "Fix solution.py so tests pass."
2. `agent/python/add_feature.py` — `solution.py` has `Calculator` with `add`; add `multiply` that the test requires.
3. `agent/typescript/fix_return.py` — `solution.ts` returns `a-b` instead of `a+b`; test.
4. `agent/typescript/add_method.ts` — add `last()` to a `Stack`.
5. `agent/java/fix_method.py` (lang java) — `Solution.java` method `double(int)` multiplies by 3; fix it.
6. `agent/bash/fix_func.py` (lang bash) — `solution.sh` `greet()` returns without a name; fix it.

Each `INITIAL_FILES` includes the `test_solution.<ext>` that validates the goal. The model only sees `GOAL` (and discovers the code via `read_file`).

- [ ] **Step 2: loading smoke**

Run:
```bash
cd /home/jordi/ia/llama && python -c "from benchmark import tasks_loader as T; \
import collections; a=T.load('agent'); print(len(a), collections.Counter(t['lang'] for t in a))"
```
Expected: `6 Counter({'python': 2, 'typescript': 2, 'java': 1, 'bash': 1})`.

- [ ] **Step 3: validate that the initial tests fail and the correct ones pass**

For each task: with the original `INITIAL_FILES`, `MockEnv(...).run_tests()` must be FAIL; with the correct solution applied, PASS. Script:
```bash
cd /home/jordi/ia/llama && python -c "
from benchmark import tasks_loader as T
from benchmark.agent import MockEnv
for t in T.load('agent'):
    e = MockEnv(dict(t['initial_files']), t['lang'], t['test_file'])
    ok,_ = e.run_tests(); print(t['name'], 'initial:', 'PASS(!'+')' if ok else 'fail(ok)')
"
```
Expected: all `fail(ok)` (the initial ones fail).

- [ ] **Step 4: commit**

```bash
git add -A && git commit -m "feat: 6 tasques agent multi-pas"
```

---

## Task 15: Smoke test end-to-end against a real model

**Files:**
- Modify: nothing (execution only).

- [ ] **Step 1: quick run (--quick) against the Qwen3-VL**

Make sure no `llama-server` is running on port 8999:
```bash
ps -eo pid,cmd | grep '[l]lama-server' | awk '{print $1}' | xargs -r kill -9
```
Run (quick mode, 1 task per dimension):
```bash
cd /home/jordi/ia/llama && python -m benchmark.run --models /home/jordi/ia/llama/models/Qwen3-VL-8B-Instruct-1M-Q6_K.gguf --quick
```
Expected: starts the server, runs 1 task per dimension, saves `results/models/<slug>.json`, and prints the scoreboard (1 model).

- [ ] **Step 2: verify the pool JSON**

```bash
ls /home/jordi/ia/llama/benchmark/results/models/
cat /home/jordi/ia/llama/benchmark/results/models/*.json | python -m json.tool | head -40
```
Expected: a file with `model`, `speed.gen_tps`, `tools.score`, `code.score/by_lang`, `agent.score/by_lang`.

- [ ] **Step 3: scoreboard read-only**

```bash
cd /home/jordi/ia/llama && python -m benchmark.run --scoreboard
```
Expected: re-prints the tables without re-running.

- [ ] **Step 4: second model to test accumulation** (optional, slow)

```bash
python -m benchmark.run --models /home/jordi/ia/llama/models/SkyRL-Agent-WebResearch-8B.Q8_0.gguf --quick --scoreboard 2>/dev/null || \
python -m benchmark.run --models /home/jordi/ia/llama/models/SkyRL-Agent-WebResearch-8B.Q8_0.gguf --quick
python -m benchmark.run --scoreboard
```
Expected: scoreboard with 2 accumulated models.

- [ ] **Step 5: commit final**

```bash
cd /home/jordi/ia/llama/benchmark
echo "results/models/" >> .gitignore  # already there; confirm
git add -A && git commit -m "chore: smoke e2e verificat contra models reals" --allow-empty
```

---

## Implementation notes

- **Order**: Tasks 1→11 are the components (TDD, each independently testable). Tasks 12→14 are content (tasks). Task 15 is the e2e validation.
- **No network in the sandbox**: `unshare -n` can fail if user namespaces are disabled; the prefix only adds it if `shutil.which("unshare")`. If it fails at runtime, execution will proceed without network blocking (acceptable in a trusted environment like this).
- **Long run**: a full run (`--models all`, without `--quick`) over 6 models can take 30-50 min; for day-to-day use `--quick` or `--dims tools,code` to iterate.
- **adapted context**: `server.resolve_context("adapted")` returns 8192 as fallback (Task 6). Connecting the real estimator from `start-dev-ai.sh` is left as a future refactor (reading GGUF and VRAM metadata); it does not block operation.
