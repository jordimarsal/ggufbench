import contextlib
import json
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
# Context audit artifact (written by harness/tools/context-audit.py): what `--context
# adapted` reads. Shape: {"<slug>": {"ctx_max": int, ...}} keyed by audit_key().
AUDIT_FILE = RESULTS_MODELS / "context.json"

PORT = 8999
# Baseline context for profiles without `-c` (SPEC §2). Raised 16384 -> 32768 with the
# 32768 code budget (ADR-0002 + R3 thinking_batches): the old value could not even hold
# prompt + budget. It is a CONDITION: pool rows measured at 16384 are not comparable with
# rows measured at 32768 — the row's `ctx_resolved`/`ctx_source` is what tells them apart.
CONTEXT_FIXED = 32768

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


def audit_key(model_path) -> str:
    """Key of a model in the context-audit artifact: the same identity the pool uses
    (run.model_id -> config.slug): a .gguf path as is; a Strata config, its name
    without extension ('strata-iq3_xxs')."""
    p = Path(model_path)
    return slug(p.stem if p.suffix == ".json" else str(model_path))


def _load_context_audit() -> dict:
    """The audit artifact as a dict; {} when it does not exist yet (or is not valid
    JSON) — the caller decides what a missing audit means."""
    try:
        data = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def resolve_context(context_mode, model_path=None) -> int:
    """Context a run asks the server for.

      int      -> the number itself (a harness pin, no CLI form)
      "fixed"  -> CONTEXT_FIXED: the same KV for everyone (comparable speeds)
      "adapted"-> the model's audited viable context: AUDIT_FILE
                 ({"slug": {"ctx_max": int, ...}}), looked up by audit_key(model_path)

    There is no silent fallback: the estimator `adapted` described never existed, and a
    guessed number measured a context nobody had verified. Without the audit it raises."""
    if isinstance(context_mode, int):
        return context_mode
    if context_mode == "fixed":
        return CONTEXT_FIXED
    if context_mode == "adapted":
        if model_path is None:
            raise ValueError("adapted context needs a model path to look up its audit entry")
        key = audit_key(model_path)
        entry = _load_context_audit().get(key)
        if not isinstance(entry, dict) or not isinstance(entry.get("ctx_max"), int):
            raise ValueError(f"no context audit for {key} — "
                             f"run harness/tools/context-audit.py first")
        return entry["ctx_max"]
    raise ValueError(f"unknown context mode: {context_mode!r} (expected 'fixed' or 'adapted')")


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
