from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BENCH_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
SERVER_BIN = BASE_DIR / "llama-server"
RESULTS_DIR = BENCH_DIR / "results"
RESULTS_MODELS = RESULTS_DIR / "models"
RESULTS_RUNS = RESULTS_DIR / "runs"

PORT = 8999
CONTEXT_FIXED = 16384

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

LANG_OK_THRESHOLD = 0.75

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

def resolve_context(context_mode, model_path):
    if isinstance(context_mode, int):
        return context_mode
    if context_mode == "fixed":
        return CONTEXT_FIXED
    return 8192