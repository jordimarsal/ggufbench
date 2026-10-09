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

PORT = 8999
CONTEXT_FIXED = 16384

# Mateixes condicions per a tots els models: temp/seed fixos. El client també els
# envia per petició (vegeu client.chat) per garantir repetibilitat encara que el
# servidor canviï de configuració.
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

# Cache KV separada de SERVER_FLAGS perquè models/<model>.txt la pot
# sobreescriure (aleshores cal no duplicar el flag: llama-server avisa).
CACHE_FLAGS = ["--cache-type-k", "q4_0", "--cache-type-v", "q4_0"]

def load_model_config_args(model_path) -> list:
    """Llegeix models/<model>.txt: flags extra del servidor, un per línia,
    mateixa convenció que bin/start-dev-ai.sh (on també s'apliquen al final).

    - Salta línies buides i comentaris (# ...).
    - Continuació de línia amb \\ final, com al script shell.
    - No filtra res: el filtratge de flags d'infraestructura (port, host, model)
      és feina de server.build_args, que sap com connecta el harness."""
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

LANG_OK_THRESHOLD = 0.75


class Lang(str, Enum):
    """Llenguatges suportats. Hereta de str per interoperar amb els strings
    que emeten els fitxers de tasques (``LANG = "python"``): ``Lang.PYTHON == "python"``
    i es pot fer servir com a clau de dict indistintiblement."""

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
