# Model Benchmark — Pla d'implementació

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir un benchmark automàtic a `/home/jordi/ia/llama/benchmark/` que compari models locals (llama-server) en velocitat, tool-calling, codi (4 idiomes) i agent multi-pas, amb resultats acumulats.

**Architecture:** Harness Python (stdlib només) que per cada model arrenca `llama-server` amb flags fixos, corre una suite de tasques, les classifica, i acumula els resultats en un pool persistent (`results/models/`). El loop d'agent simula un entorn de codi en memòria amb tools `read_file/write_file/run_tests`. Els executors per llenguatge corren codi generat en sandbox (tempdir+timeout+no-xarxa).

**Tech Stack:** Python 3.12 stdlib (urllib per HTTP, unittest per tests del harness, subprocess, json, tempfile, pathlib). Toolchains presents: `python3`, `bash`, `javac/java 22`, `bun 1.3.9` (per TS). Sense deps externes (cap `requests`, cap `pytest`).

## Global Constraints

- **Ubicació:** tot sota `/home/jordi/ia/llama/benchmark/`.
- **Server binary:** `/home/jordi/ia/llama/llama-server` (symlink); models a `/home/jordi/ia/llama/models/*.gguf`.
- **Sense deps externes:** HTTP via `urllib.request`; tests del harness via `python -m unittest` (stdlib). No `pip install`.
- **Flags fixos del servidor** (de `start-dev-ai.sh`): `-ngl 999 --flash-attn auto --no-mmap --jinja --parallel 1 -b 512 --temp 0.2 --top-p 0.95 --repeat-penalty 1.1 --repeat-last-n 256 --seed 42 --cache-type-k q4_0 --cache-type-v q4_0 --host 127.0.0.1 --port <P>`.
- **Context modes:** `fixed` (16384 per defecte) o `adapted` (viable del model).
- **Sandbox codi:** tempdir nou + `timeout 30` + `unshare -n` si disponible; codi generat mai fora del tempdir.
- **Commits:** el projecte té el seu propi `git init` (Task 1).
- **Idiomes de codi/agent:** bash, python, java, typescript.
- **Pesos default:** tools=0.30, code=0.30, agent=0.25, speed=0.15.

---

## File Structure

```
benchmark/
├── run.py                 # CLI entry (argparse) + orquestració
├── config.py              # constants: paths, flags, pesos, slug()
├── client.py              # chat() HTTP + parseig de timings/tool_calls
├── server.py              # ServerManager: start/wait_ready/stop + build_args
├── executors.py           # run(lang, solution, test) -> Result; 4 idiomes + sandbox
├── code_extract.py        # extreure bloc ```lang``` de la resposta
├── agent.py               # MockEnv + run_agent() loop amb read_file/write_file/run_tests
├── graders.py             # grade_speed/grade_tools/grade_code/grade_agent
├── tasks_loader.py        # descobrir/carregar tasks/ com mòduls
├── report.py              # render(pool) taules + save_run/load_pool/normalize
├── tasks/
│   ├── speed/  tools/  code/{python,bash,java,typescript}/  agent/{python,bash,java,typescript}/
├── results/
│   ├── models/            # <slug>.json (pool,latest)
│   └── runs/              # <ts>-<slug>.json (històric)
└── tests/                 # test_*.py (unittest)
    test_config.py test_client.py test_executors.py test_code_extract.py
    test_server.py test_agent.py test_graders.py test_report.py
```

---

## Task 1: Scaffold, git init, config.py i slug()

**Files:**
- Create: `benchmark/config.py`, `benchmark/__init__.py` (buit), `benchmark/tests/__init__.py` (buit), `benchmark/tests/test_config.py`
- Create: `benchmark/.gitignore` (ignora `results/runs/`, `__pycache__/`)

**Interfaces:**
- Produces: `config.BASE_DIR`, `config.MODELS_DIR`, `config.SERVER_BIN`, `config.RESULTS_DIR`, `config.SERVER_FLAGS` (llista), `config.PORT`, `config.CONTEXT_FIXED`, `config.WEIGHTS` (dict), `config.slug(name) -> str`.

- [ ] **Step 1: git init + estructura**

```bash
cd /home/jordi/ia/llama/benchmark
git init -q
mkdir -p tasks/{speed,tools,code/{python,bash,java,typescript},agent/{python,bash,java,typescript}} results/{models,runs} tests
touch __init__.py tests/__init__.py
```

- [ ] **Step 2: .gitignore**

Crea `benchmark/.gitignore`:
```
__pycache__/
*.pyc
results/runs/
results/models/
```
(Results no es commiten — es regeneren; el pool és local.)

- [ ] **Step 3: test fallider per config + slug**

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

- [ ] **Step 4: verifica que falla**

Run: `cd /home/jordi/ia/llama && python -m unittest benchmark.tests.test_config -v`
Expected: FAIL (`ModuleNotFoundError` o `AttributeError`).

- [ ] **Step 5: implementa config.py**

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

# Flags fixos (mateixes condicions per tots). El model, -c, -m, --tensor-split s'afegeixen al server.py.
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

# Llindar (fracció 0..1) per al perfil "fiable per idioma".
LANG_OK_THRESHOLD = 0.75

def slug(name: str) -> str:
    """Saneja un nom de model per usar-lo com a nom de fitxer (treu .gguf)."""
    s = name
    for ext in (".gguf", ".GGUF"):
        if s.endswith(ext):
            s = s[: -len(ext)]
            break
    return s.replace("/", "_")
```

- [ ] **Step 6: verifica pass**

Run: `cd /home/jordi/ia/llama && python -m unittest benchmark.tests.test_config -v`
Expected: 4 PASS.

- [ ] **Step 7: commit**

```bash
cd /home/jordi/ia/llama/benchmark
git add -A && git commit -m "feat: scaffold + config.py (paths, flags, weights, slug)"
```

---

## Task 2: client.py — chat HTTP + parseig

**Files:**
- Create: `benchmark/client.py`, `benchmark/tests/test_client.py`

**Interfaces:**
- Produces: `client.chat(messages, tools=None, tool_choice=None, max_tokens=256, base_url=..., timeout=60) -> dict` (JSON complet de la resposta); `client.parse_timings(resp) -> dict|None`; `client.extract_tool_call(resp) -> dict|None` (retorna `{"name":..., "arguments": <parsed json or None>}` o None); `client.first_text(resp) -> str`.

- [ ] **Step 1: test fallider**

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
        self.assertIsNone(tc["arguments"])  # arguments no parsejables -> None
    def test_first_text(self):
        self.assertEqual(client.first_text(SAMPLE), "")
        self.assertEqual(client.first_text({"choices":[{"message":{"content":"x"}}]}), "x")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: verifica que falla**

Run: `python -m unittest benchmark.tests.test_client -v` → FAIL (ImportError).

- [ ] **Step 3: implementa client.py**

`benchmark/client.py`:
```python
import json
import urllib.request
import urllib.error

def chat(messages, tools=None, tool_choice=None, max_tokens=256,
         base_url="http://127.0.0.1:8999", timeout=60):
    """POST /v1/chat/completions i retorna el JSON complet. Llença excepció si error/timeout."""
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

- [ ] **Step 4: verifica pass**

Run: `python -m unittest benchmark.tests.test_client -v` → 6 PASS.

- [ ] **Step 5: commit**

```bash
git add -A && git commit -m "feat: client.py (HTTP chat + parse timings/tool_calls)"
```

---

## Task 3: code_extract.py — extreure bloc de codi per llenguatge

**Files:**
- Create: `benchmark/code_extract.py`, `benchmark/tests/test_code_extract.py`

**Interfaces:**
- Produces: `code_extract.extract(text, lang) -> str|None`. `lang` un de `python|bash|java|typescript`. Retorna el codi del primer bloc ` ```lang ` (o alias: `py`, `sh`, `ts`, `js`). None si no n'hi ha.

- [ ] **Step 1: test fallider**

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
        # si només hi ha bloc ``` sense lang i es demana python, l'agafa
        self.assertEqual(code_extract.extract("```\nx=1\n```", "python"), "x=1\n")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: verifica falla**

Run: `python -m unittest benchmark.tests.test_code_extract -v` → FAIL.

- [ ] **Step 3: implementa code_extract.py**

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
    # primer un bloc amb tag conegut
    for tag in langs:
        m = re.search(r"```" + re.escape(tag) + r"[^\n]*\n(.*?)```", text, re.DOTALL)
        if m:
            return m.group(1)
    # fallback: bloc sense tag
    m = re.search(r"```\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1)
    return None
```

- [ ] **Step 4: verifica pass**

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
- Produces: `executors.run(lang, solution_code, test_code, timeout=30) -> dict` amb `{"passed": bool, "output": str, "elapsed_ms": int}`. Per ara només `lang=="python"`. Usa `executors.SANDBOX_PREFIX` (llista per bloquejar xarxa).

- [ ] **Step 1: test fallider**

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

- [ ] **Step 2: verifica falla** → FAIL.

- [ ] **Step 3: implementa executors.py (python + sandbox base)**

`benchmark/executors.py`:
```python
import subprocess, tempfile, os, time, shutil

def _sandbox_prefix(timeout):
    """Command prefix per aïllar: timeout + xarxa bloquejada si unshare hi és."""
    prefix = ["timeout", str(timeout)]
    # unshare -n bloqueja xarxa (requot permís de user namespace); si falla, s'omet.
    if shutil.which("unshare"):
        prefix += ["unshare", "-n"]
    return prefix

def run(lang, solution_code, test_code, timeout=30):
    """Escriu solution+test en tempdir, executa segons lang, retorna resultat."""
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

- [ ] **Step 4: verifica pass**

Run: `python -m unittest benchmark.tests.test_executors -v` → 3 PASS.

- [ ] **Step 5: commit**

```bash
git add -A && git commit -m "feat: executors.py (python runner + sandbox)"
```

---

## Task 5: executors.py — bash, java, typescript

**Files:**
- Modify: `benchmark/executors.py` (afegeix `_bash`, `_java`, `_typescript` i els despatxa a `_run_in`)
- Modify: `benchmark/tests/test_executors.py` (afegir tests)

**Interfaces:**
- Extends: `executors.run(lang, ...)` suporta `bash|java|typescript` a més de `python`.

- [ ] **Step 1: afegeix tests**

Afegeix a `tests/test_executors.py`:
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

- [ ] **Step 2: verifica falla** (4 nous FAIL: bash/java/ts no implementats).

- [ ] **Step 3: implementa els 3 idiomes**

Despatxa i afegeix a `executors.py` (`_run_in`):
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

- [ ] **Step 4: verifica pass** (tots 8 tests)

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
- Produces: `server.build_args(model_path, context_mode, port) -> list[str]` (tots els args, model inclosa); `server.ServerManager(model_path, context_mode, port)` amb `.start()`, `.wait_ready(timeout=180) -> bool`, `.stop()`, `.is_alive() -> bool`. `context_mode` és `"fixed"` o `adapted` o un enter.

- [ ] **Step 1: test fallider**

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

- [ ] **Step 2: verifica falla** → FAIL.

- [ ] **Step 3: implementa server.py**

`benchmark/server.py`:
```python
import subprocess, time, urllib.request, json
from . import config

def resolve_context(context_mode, model_path):
    """fixed -> CONTEXT_FIXED; int -> int; adapted -> estima viable (fallback 8192)."""
    if isinstance(context_mode, int):
        return context_mode
    if context_mode == "fixed":
        return config.CONTEXT_FIXED
    # adapted: delegem a un estimator extern quan estigui; fallback segur
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
        """Llest quan un chat de prova retorna 'choices' (no només /v1/models)."""
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

- [ ] **Step 4: verifica pass**

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
- Produces: `agent.MockEnv(files: dict[str,str], lang: str)` amb `.read_file(path)`, `.write_file(path, content)`, `.run_tests(test_filename)`; `agent.run_agent(client_mod, task, max_turns=8) -> dict` on `task` és `{"lang","goal","initial_files","test_file"}` i el resultat és `{"success": bool, "turns": int, "tool_calls": int}`. Usa `executors.run` per `run_tests`.

- [ ] **Step 1: test fallider**

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
        # client fake: primer crida write_file amb la solució correcta, després atura
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

- [ ] **Step 2: verifica falla** → FAIL.

- [ ] **Step 3: implementa agent.py**

`benchmark/agent.py`:
```python
import json
from . import executors

# Esquema de les tools que es passen al model.
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
        # Executa tots els fitxers en tempdir via executor del llenguatge.
        # Per simplicitat: junta solució+test segons llenguatge.
        if self.lang == "python":
            sol = self.files.get("solution.py", "")
            tst = self.files.get(self.test_file, "")
            r = executors.run("python", sol, tst)
        else:
            # altres langs: delega a executors amb solució+test convenció
            r = self._run_other()
        return (r["passed"], r["output"])

    def _run_other(self):
        # Conveni: solution.<ext> + test_solution.<ext>
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

- [ ] **Step 4: verifica pass**

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
- Produces: `graders.grade_speed(client_mod, n=3) -> dict`; `graders.grade_tools(client_mod, tasks) -> dict`; `graders.grade_code(client_mod, tasks) -> dict`; `graders.grade_agent(client_mod, tasks) -> dict`. Cada dict té `score` (0..1); code i agent també `by_lang` i `tasks`.

- [ ] **Step 1: test fallider**

`benchmark/tests/test_graders.py`:
```python
import unittest
from benchmark import graders

class FakeClient:
    """Client que pot ser programat amb una seqüència de respostes per tasca."""
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
        self.assertEqual(r["by_lang"], {})  # tools no té by_lang
    def test_noop_case(self):
        tasks = [{"name":"noop","prompt":"hola","tools":[],"expected":None}]  # None = no ha de cridar
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
        self.assertAlmostEqual(r["gen_tps"], 20.0)  # mediana de [10,20,30]

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: verifica falla** → FAIL.

- [ ] **Step 3: implementa graders.py**

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

- [ ] **Step 4: verifica pass**

Run: `python -m unittest benchmark.tests.test_graders -v` → 4 PASS (classes).

- [ ] **Step 5: commit**

```bash
git add -A && git commit -m "feat: graders.py (speed/tools/code/agent + by_lang)"
```

---

## Task 9: tasks_loader.py — descobrir tasques

**Files:**
- Create: `benchmark/tasks_loader.py`, `benchmark/tests/test_tasks_loader.py`
- Create: tasques d'exemple: `tasks/tools/_example.py` (esborrat al final del task), per testejar càrrega.

**Interfaces:**
- Produces: `tasks_loader.load(dimension, lang_filter=None) -> list[dict]`. Carrega tots els `tasks/<dim>/**/*.py` (cada fitxer defineix constants), ignorant els que comencen per `_`. Cada mòdul es converteix en un dict segons la dimensió.

- [ ] **Step 1: test fallider**

`benchmark/tests/test_tasks_loader.py`:
```python
import unittest, os, textwrap
from benchmark import tasks_loader

class TestLoad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # crea una tasca tools temporal
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
        # _tmpexample comença per _ -> ignorat; només tasques reals
        ts = tasks_loader.load("tools")
        self.assertIsInstance(ts, list)
    def test_skips_underscore(self):
        ts = tasks_loader.load("tools")
        self.assertFalse(any(t["name"] == "tmp" for t in ts))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: verifica falla** → FAIL.

- [ ] **Step 3: implementa tasks_loader.py**

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
        # filtra per idioma (subcarpeta per code/agent)
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

- [ ] **Step 4: verifica pass**

Run: `python -m unittest benchmark.tests.test_tasks_loader -v` → 2 PASS.

- [ ] **Step 5: commit**

```bash
git add -A && git commit -m "feat: tasks_loader.py (descobrir/carregar tasks per dimensió)"
```

---

## Task 10: report.py — taules, persistència, normalització

**Files:**
- Create: `benchmark/report.py`, `benchmark/tests/test_report.py`

**Interfaces:**
- Consumes: `config`.
- Produces: `report.save_result(result_dict)` (a `results/models/<slug>.json` + `results/runs/<ts>-<slug>.json`); `report.load_pool() -> list[dict]`; `report.compute_global(result, weights, pool) -> float` (velocitat normalitzada sobre el pool); `report.render(pool, weights, verbose=False) -> str` (retorna les taules formatejades); `report.lang_profile(result, threshold) -> dict`.

- [ ] **Step 1: test fallider**

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
        # sense speed, normalitza sobre la resta
        g = report.compute_global(r, config.WEIGHTS, [r])
        self.assertAlmostEqual(g, 0.30+0.30+0.25)  # speed 0
    def test_global_speed_normalized(self):
        a = mk("a", gen_tps=50); b = mk("b", gen_tps=100)
        pool=[a,b]
        ga = report.compute_global(a, config.WEIGHTS, pool)
        gb = report.compute_global(b, config.WEIGHTS, pool)
        self.assertGreater(gb, ga)  # el més ràpid (b) té global major
    def test_lang_profile(self):
        r = mk("m", code_lang={"python":1.0,"java":0.0}, agent_lang={"python":0.5})
        prof = report.lang_profile(r, threshold=0.75)
        self.assertIn("python", prof["strong"])
        self.assertIn("java", prof["weak"])
    def test_render_has_headers(self):
        pool=[mk("a"), mk("b")]
        out = report.render(pool, config.WEIGHTS)
        self.assertIn("GLOBAL", out)
        self.assertIn("code:py", out)  # capçalera per-llenguatge

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: verifica falla** → FAIL.

- [ ] **Step 3: implementa report.py**

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
    # Taula 1 — global
    out.append("=== Global ===")
    out.append(f"{'MODEL':30} {'gen_tps':>8} {'tools':>6} {'code':>6} {'agent':>6} {'GLOBAL':>7}")
    for r in rows:
        tps = r.get("speed", {}).get("gen_tps")
        out.append(f"{r['model'][:30]:30} {(f'{tps:.1f}' if tps else '  —'):>8} "
                   f"{_fmt_pct(r.get('tools',{}).get('score')):>6} "
                   f"{_fmt_pct(r.get('code',{}).get('score')):>6} "
                   f"{_fmt_pct(r.get('agent',{}).get('score')):>6} "
                   f"{compute_global(r, weights, pool):>7.2f}")
    # Taula 2 — per llenguatge
    out.append("\n=== Per llenguatge ===")
    head = f"{'MODEL':30} " + " ".join(f"code:{_LANG_HEAD[l]:>4}" for l in _LANGS) \
           + "  " + " ".join(f"agent:{_LANG_HEAD[l]:>4}" for l in _LANGS)
    out.append(head)
    for r in rows:
        c = r.get("code", {}).get("by_lang", {})
        a = r.get("agent", {}).get("by_lang", {})
        cells = [_fmt_pct(c.get(l)) for l in _LANGS] + [_fmt_pct(a.get(l)) for l in _LANGS]
        out.append(f"{r['model'][:30]:30} " + " ".join(f"{x:>9}" for x in cells))
    # Perfil
    out.append("\n=== Perfil (≥{:.0%}) ===".format(config.LANG_OK_THRESHOLD))
    for r in rows:
        p = lang_profile(r)
        out.append(f"{r['model'][:30]:30} fort: {', '.join(p['strong']) or '—'} | fluix: {', '.join(p['weak']) or '—'}")
    # Detall
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

- [ ] **Step 4: verifica pass**

Run: `python -m unittest benchmark.tests.test_report -v` → 4 PASS.

- [ ] **Step 5: commit**

```bash
git add -A && git commit -m "feat: report.py (taules global/per-lleng+perfil, pool, normalització)"
```

---

## Task 11: run.py — CLI i orquestració

**Files:**
- Create: `benchmark/run.py`, `benchmark/tests/test_run_cli.py` (test d'args, sense xarxa)

**Interfaces:**
- Consumes: tots els anteriors.
- Produces: executable `python -m benchmark.run` o `python benchmark/run.py`.

- [ ] **Step 1: test fallider (parsing CLI)**

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

- [ ] **Step 2: verifica falla** → FAIL.

- [ ] **Step 3: implementa run.py**

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

- [ ] **Step 4: verifica pass**

Run: `python -m unittest benchmark.tests.test_run_cli -v` → 3 PASS.

- [ ] **Step 5: commit**

```bash
git add -A && git commit -m "feat: run.py (CLI + orquestració per model)"
```

---

## Task 12: Suite de tasques — speed + tools (8)

**Files:**
- Create: `tasks/speed/speed.py`, i 8 fitxers a `tasks/tools/`.

**Esquema de cada tasca tools** (fitxer `tasks/tools/<name>.py`):
```python
NAME = "<name>"
PROMPT = "<enunciat per al model>"
TOOLS = [ { ... definició de la/les tools... } ]
EXPECTED = {"name": "<fn>", "arguments": {<args esperats>}}   # o None pel cas no-op
```

- [ ] **Step 1: speed task**

`tasks/speed/speed.py`:
```python
NAME = "speed"
PROMPT = "Write a short vivid poem about the sea and a lighthouse."
```
(El grader de speed fa servir `graders.SPEED_PROMPT` internament; aquesta tasca és placeholder per consistent loading.)

- [ ] **Step 2: 8 tasques tools** — crea els següents fitxers amb `NAME/PROMPT/TOOLS/EXPECTED`:

1. `tasks/tools/single_arg.py` — demana temps de París; tool `get_weather(city)`; EXPECTED `get_weather({"city":"Paris"})`.
2. `tasks/tools/multi_arg.py` — demana crear esdeveniment; tool `create_event(title, date, location)`; EXPECTED amb els 3 args (extretes de l'enunciat: title="Standup", date="2026-09-01", location="Remote").
3. `tasks/tools/pick_right.py` — dóna 3 tools (`get_weather`, `search_docs`, `send_email`); demana "email the report to ana@x.com"; EXPECTED `send_email({"to":"ana@x.com","subject":"report"})` (ha de triar l'eina correcta).
4. `tasks/tools/noop.py` — demana "explain what recursion is"; amb tool `get_weather` disponible; EXPECTED `None` (no ha de cridar).
5. `tasks/tools/wrong_args.py` — demana temps de Tòquio; tool `get_weather(city)`; EXPECTED `get_weather({"city":"Tokyo"})` (prova que l'argument sigui correcte, no "Paris").
6. `tasks/tools/typed_number.py` — tool `set_volume(level: int)`; demana "set volume to 50"; EXPECTED `set_volume({"level":50})` (prova tipus numèric).
7. `tasks/tools/optional_arg.py` — tool `list_files(path="/")`; demana "list files"; EXPECTED `list_files({"path":"/"})` o `{}` (accepta default).
8. `tasks/tools/chain_hint.py` — demana "get weather for Paris then save it"; tool `get_weather` i `save(key,value)`; EXPECTED el PRIMER call = `get_weather({"city":"Paris"})` (prova que comenci pel correcte).

Cada fitxer defineix `TOOLS` amb l'esquema JSON complet de cada funció (type/description/parameters). L'autor omple `PROMPT` i `TOOLS` seguint els esquemes.

- [ ] **Step 3: smoke de càrrega**

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

## Task 13: Suite de tasques — code (8: 2 per idioma)

**Files:**
- Create: 2 fitxers per a `tasks/code/{python,bash,java,typescript}/`.

**Esquema** (`tasks/code/<lang>/<name>.py`):
```python
NAME = "<name>"
LANG = "<python|bash|java|typescript>"
PROMPT = "<enunciat: demana al model que implementi X, en un bloc ```lang```>"
TEST_CODE = "<codi del test que importa/crída la solution i fa asserts>"
```

- [ ] **Step 1: defineix les 8 tasques** (2 per idioma):

| Lang | Task 1 (implementa) | Task 2 (arregla bug) |
|---|---|---|
| python | `stack.py`: implementa `Stack` amb `push/pop/peek` | `fib_fix.py`: arregla fib (el donat retorna n-1) |
| bash | `math.sh`: funcions `sum` i `max2` | `reverse_fix.sh`: arregla `reverse` (invertia malament) |
| java | `Solution.java`: mètode estàtic `isPalindrome(String)` | `Solution.java`: arregla `factorial` (overflow off-by-one) |
| typescript | `solution.ts`: `fizzbuzz(n)` retorna string[] | `solution.ts`: arregla `dedupe` (mantenia duplicats) |

Cada `TEST_CODE` és un test autònom (import/source la solution, asserts, `exit 1`/throw si falla). Convencions:
- python: `from solution import *` + asserts.
- bash: `source solution.sh` + `[ ... ] || exit 1`.
- java: `public class Test { public static void main(...){ ... throw RuntimeException ... } }`.
- typescript: `import { ... } from "./solution"` + asserts (bun).

El `PROMPT` ha de demanar explícitament el bloc amb el tag correcte i la signatura esperada (per ex: java demana `public class Solution { ... }`).

- [ ] **Step 2: smoke de càrrega**

Run:
```bash
cd /home/jordi/ia/llama && python -c "from benchmark import tasks_loader as T; \
import collections; c=T.load('code'); print(len(c), collections.Counter(t['lang'] for t in c))"
```
Expected: `8 Counter({'python': 2, 'bash': 2, 'java': 2, 'typescript': 2})`.

- [ ] **Step 3: valida els tests amb solucions correctes conegudes**

Per cada tasca, executa `executors.run(lang, <solució correcta que escriguis>, TEST_CODE)` i verifica `passed==True`. Script de comprovació ràpid:
```bash
cd /home/jordi/ia/llama && python -c "
from benchmark import tasks_loader as T, executors
for t in T.load('code'):
    print(t['name'], t['lang'], '-> crea solució correcta manualment i verifica abans de commit')
"
```
(Authoring manual de les solucions correctes per validar cada `TEST_CODE`.)

- [ ] **Step 4: commit**

```bash
git add -A && git commit -m "feat: 8 tasques code (2 per idioma)"
```

---

## Task 14: Suite de tasques — agent (6)

**Files:**
- Create: `tasks/agent/{python×2, typescript×2, java×1, bash×1}.py`.

**Esquema** (`tasks/agent/<lang>/<name>.py`):
```python
NAME = "<name>"
LANG = "<python|bash|java|typescript>"
GOAL = "<objectiu pel model: què ha d'aconseguir>"
INITIAL_FILES = { "<path>": "<contingut inicial (amb bug)>" , "test_solution.<ext>": "<test>" }
TEST_FILE = "test_solution.<ext>"     # el que run_tests executa
MAX_TURNS = 8
```

- [ ] **Step 1: defineix les 6 tasques agent**:

1. `agent/python/fix_offbyone.py` — `solution.py` té `def fib(n)` amb bug off-by-one; test comprova `fib(10)==55`. Goal: "Fix solution.py so tests pass."
2. `agent/python/add_feature.py` — `solution.py` té `Calculator` amb `add`; afegeix-hi `multiply` que el test demana.
3. `agent/typescript/fix_return.py` — `solution.ts` retorna `a-b` en lloc de `a+b`; test.
4. `agent/typescript/add_method.ts` — afegeix `last()` a una `Stack`.
5. `agent/java/fix_method.py` (lang java) — `Solution.java` mètode `double(int)` multiplica per 3; arregla.
6. `agent/bash/fix_func.py` (lang bash) — `solution.sh` `greet()` retorna sense nom; arregla.

Cada `INITIAL_FILES` inclou el `test_solution.<ext>` que valida l'objectiu. El model només veu `GOAL` (i descobreix el codi via `read_file`).

- [ ] **Step 2: smoke de càrrega**

Run:
```bash
cd /home/jordi/ia/llama && python -c "from benchmark import tasks_loader as T; \
import collections; a=T.load('agent'); print(len(a), collections.Counter(t['lang'] for t in a))"
```
Expected: `6 Counter({'python': 2, 'typescript': 2, 'java': 1, 'bash': 1})`.

- [ ] **Step 3: valida que els tests inicials fallen i els correctes passen**

Per cada tasca: amb la `INITIAL_FILES` original, `MockEnv(...).run_tests()` ha de ser FAIL; amb la solució correcta aplicada, PASS. Script:
```bash
cd /home/jordi/ia/llama && python -c "
from benchmark import tasks_loader as T
from benchmark.agent import MockEnv
for t in T.load('agent'):
    e = MockEnv(dict(t['initial_files']), t['lang'], t['test_file'])
    ok,_ = e.run_tests(); print(t['name'], 'initial:', 'PASS(!'+')' if ok else 'fail(ok)')
"
```
Expected: totes `fail(ok)` (les inicials fallen).

- [ ] **Step 4: commit**

```bash
git add -A && git commit -m "feat: 6 tasques agent multi-pas"
```

---

## Task 15: Smoke test end-to-end contra un model real

**Files:**
- Modify: res (només execució).

- [ ] **Step 1: run ràpida (--quick) contra el Qwen3-VL**

Assegura't que no hi ha cap `llama-server` corrent al port 8999:
```bash
ps -eo pid,cmd | grep '[l]lama-server' | awk '{print $1}' | xargs -r kill -9
```
Executa (mode quick, 1 tasca per dimensió):
```bash
cd /home/jordi/ia/llama && python -m benchmark.run --models /home/jordi/ia/llama/models/Qwen3-VL-8B-Instruct-1M-Q6_K.gguf --quick
```
Expected: arrenca el server, corre 1 tasca per dimensió, guarda `results/models/<slug>.json`, i imprimeix el scoreboard (1 model).

- [ ] **Step 2: verifica el JSON del pool**

```bash
ls /home/jordi/ia/llama/benchmark/results/models/
cat /home/jordi/ia/llama/benchmark/results/models/*.json | python -m json.tool | head -40
```
Expected: un fitxer amb `model`, `speed.gen_tps`, `tools.score`, `code.score/by_lang`, `agent.score/by_lang`.

- [ ] **Step 3: scoreboard read-only**

```bash
cd /home/jordi/ia/llama && python -m benchmark.run --scoreboard
```
Expected: re-imprimeix les taules sense re-executar.

- [ ] **Step 4: segon model per provar acumulació** (opcional, lent)

```bash
python -m benchmark.run --models /home/jordi/ia/llama/models/SkyRL-Agent-WebResearch-8B.Q8_0.gguf --quick --scoreboard 2>/dev/null || \
python -m benchmark.run --models /home/jordi/ia/llama/models/SkyRL-Agent-WebResearch-8B.Q8_0.gguf --quick
python -m benchmark.run --scoreboard
```
Expected: scoreboard amb 2 models acumulats.

- [ ] **Step 5: commit final**

```bash
cd /home/jordi/ia/llama/benchmark
echo "results/models/" >> .gitignore  # ja hi és; confirma
git add -A && git commit -m "chore: smoke e2e verificat contra models reals" --allow-empty
```

---

## Notes d'implementació

- **Ordre**: Tasks 1→11 son els components (TDD, cadascun testable independentment). Tasks 12→14 són contingut (tasques). Task 15 és la validació e2e.
- **Sense xarxa al sandbox**: `unshare -n` pot fallar si els user namespaces hi són desactivats; el prefix només l'afegeix si `shutil.which("unshare")`. En ara falla en runtime, l'execució es farà sense bloqueig de xarxa (acceptable per un entorn de confiança com aquest).
- **Run llarga**: una run completa (`--models all`, sense `--quick`) sobre 6 models pot tardar 30-50 min; per dia a dia usar `--quick` o `--dims tools,code` per iterar.
- **adapted context**: `server.resolve_context("adapted")` retorna 8192 de fallback (Task 6). Connectar-hi l'estimador real de `start-dev-ai.sh` queda com a refactor futur (llegir metadades GGUF i VRAM); no bloqueja el funcionament.
