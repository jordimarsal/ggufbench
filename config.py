import contextlib
from enum import Enum
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BENCH_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
SERVER_BIN = BASE_DIR / "llama-server"
RESULTS_DIR = BENCH_DIR / "results"
RESULTS_MODELS = RESULTS_DIR / "models"
RESULTS_RUNS = RESULTS_DIR / "runs"
TOKEN_BUDGETS = RESULTS_DIR / "token_budgets.json"
POOL_FILE = RESULTS_MODELS / "pool.jsonl"

PORT = 8999
CONTEXT_FIXED = 16384

# --- Second engine: Strata (Qwen3.8-Flash-Next) ----------------------------------------
# Strata is not llama-server: its own engine (engine/strata) served by serve/server.py,
# with one JSON config per model (strata-<model>.json: pack, context, GPUs, MTP...) and a
# single model loaded at a time. It speaks the same OpenAI contract and emits `timings` with the
# llama.cpp field names, so the 4 dimensions work as-is (SPEC §2).
STRATA_DIR = BASE_DIR / "Strata"
STRATA_PORT = 8080            # its usual port; --port can change it
# Startup: loads 34-43 GB into RAM (1-3 min), much slower than a llama-server
STRATA_READY_TIMEOUT = 600
# Thinking: hybrid models (Qwen3) can burn the budget thinking while other
# setups measure without a thinking chain. `--thinking on|off` controls it
# via the request body (the same channel the old STRATA_EXTRA_BODY used,
# for both engines): no model .txt can override it, unlike a server
# flag (ADR-4 thinking_batches).
THINKING_DEFAULT = "off"

def thinking_body(engine, mode):
    """Extra body for thinking mode (R1 thinking_batches).
    `off` -> disabled via chat_template_kwargs; `on` -> {} (free). Only touches the
    `extra` channel: prompts, dims and tasks are identical in both modes (R6)."""
    if engine not in ("llama", "strata"):
        raise ValueError(f"unknown engine: {engine!r}")
    if mode == "off":
        return {"chat_template_kwargs": {"enable_thinking": False}}
    if mode == "on":
        return {}
    raise ValueError(f"unknown thinking mode: {mode!r} (expected 'on' or 'off')")

# Same conditions for all models: fixed temp/seed. The client also sends them
# per request (see client.chat) to guarantee repeatability even if the
# server changes configuration.
TEMPERATURE = 0.2
SEED = 42

SERVER_FLAGS = [
    "-ngl", "999",
    "--flash-attn", "auto",
    "--no-mmap",
    "--jinja",
    "--parallel", "1",
    "-b", "512",
    "--temp", str(TEMPERATURE),
    "--top-p", "0.95",
    "--repeat-penalty", "1.1",
    "--repeat-last-n", "256",
    "--seed", str(SEED),
    "--host", "127.0.0.1",
]

# KV cache kept separate from SERVER_FLAGS because models/<model>.txt can
# override it (then the flag must not be duplicated: llama-server warns).
CACHE_FLAGS = ["--cache-type-k", "q4_0", "--cache-type-v", "q4_0"]

# Per-model profile flags that are allowed through from models/<model>.txt.
# Values pass unvalidated EXCEPT: a value starting with "-" looks like a flag
# mis-pairing → drop the pair with a warning.  Unknown flag names are also
# dropped (with a warning).  Infra flags (-m/--model, --port, --host) are
# handled separately by _strip_infra in server.py.
ALLOWED_MODEL_FLAGS = {
    # context / batching
    "-c", "--ctx-size", "-b", "--batch-size",
    "--threads",
    # GPU / layers
    "--n-gpu-layers", "-ngl",
    "--tensor-split", "--split-mode",
    "--main-gpu",
    # attention / cache
    "--flash-attn", "--no-mmap",
    "--cache-bias", "--cache-type-k", "--cache-type-v",
    "--no-prompt-cache",
    # sampling
    "--temp", "--top-p", "--repeat-penalty",
    "--repeat-last-n", "--presence-penalty", "--frequency-penalty",
    "--mirostat", "--mirostat-tau", "--mirostat-eta",
    "--penalize-nl", "--ignore-eos",
    # model loading
    "--mmproj", "-md",
    "--spec-type", "--spec-draft-n-max",
    "--draft-min-p",
    # misc
    "--jinja", "--parallel",
    "--mlock", "--mmap",
    "--log-disable", "--log-prefix",
}

def load_model_config_args(model_path) -> list:
    """Reads models/<model>.txt: extra server flags, one per line, same
    convention as bin/start-dev-ai.sh (where they are also applied last).

    - Skips blank lines and comments (# ...).
    - Line continuation with trailing \\, like in the shell script.
    - Filters nothing: filtering infrastructure flags (port, host, model)
      is server.build_args' job, which knows how the harness connects."""
    txt = Path(model_path).with_suffix(".txt")
    if not txt.is_file():
        return []
    args = []
    for line in txt.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith("\\"):
            line = line[:-1].rstrip()
            if not line or line.startswith("#"):
                continue
        args.extend(line.split())
    return args

WEIGHTS = {"tools": 0.30, "code": 0.30, "agent": 0.25, "speed": 0.15}

# Task suite version: bump when the set changes (hard_code_tier R7:
# v2 = +16 hard tasks). The pool stores it to tell pre/post conditions apart.
TASKS_VERSION = "v3"

LANG_OK_THRESHOLD = 0.75


class Lang(str, Enum):
    """Supported languages. Inherits from str to interoperate with the strings
    emitted by task files (``LANG = "python"``): ``Lang.PYTHON == "python"``
    and it can be used as a dict key interchangeably."""

    PYTHON = "python"
    BASH = "bash"
    JAVA = "java"
    TYPESCRIPT = "typescript"

    @classmethod
    def exts(cls) -> dict[str, str]:
        return {cls.PYTHON: ".py", cls.BASH: ".sh",
                cls.JAVA: ".java", cls.TYPESCRIPT: ".ts"}


def slug(name: str) -> str:
    s = name
    for ext in (".gguf", ".GGUF"):
        if s.endswith(ext):
            s = s[: -len(ext)]
            break
    s = s.lower()
    s = s.replace(" ", "-")
    s = s.replace("/", "_")
    s = s.replace(".", "_")
    s = s.replace("(", "")
    s = s.replace(")", "")
    s = s.replace(",", "")
    return s


def resolve_context(context_mode, model_path=None) -> int:
    if isinstance(context_mode, int):
        return context_mode
    if context_mode == "fixed":
        return CONTEXT_FIXED
    return 8192


@contextlib.contextmanager
def override(**kw):
    """Replaces config constants inside a with block and restores them on exit.
    Tests must use this instead of touching globals by hand."""
    saved = {k: globals()[k] for k in kw}
    globals().update(kw)
    try:
        yield
    finally:
        globals().update(saved)
