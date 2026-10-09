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

# --- Segon motor: Strata (Qwen3.8-Flash-Next) ----------------------------------------
# Strata no és llama-server: motor propi (engine/strata) servit per serve/server.py,
# amb un config JSON per model (strata-<model>.json: pack, context, GPUs, MTP...) i un
# sol model carregat alhora. Parla el mateix contracte OpenAI i emet `timings` amb els
# noms de llama.cpp, així que les 4 dimensions li serveixen tal qual (SPEC §2).
STRATA_DIR = BASE_DIR / "Strata"
STRATA_PORT = 8080            # el seu port habitual; --port el pot canviar
# Arrencada: carrega 34-43 GB a RAM (1-3 min), molt més lent que un llama-server
STRATA_READY_TIMEOUT = 600
# Strata pensa en HIGH per defecte: amb els max_tokens petits de les tasques (128/256)
# es menja el pressupost de generació i no arriba a escriure res. Mesurem sense cadena
# de pensament, igual que la resta de models i que el bench_vs_llama.py d'Strata.
STRATA_EXTRA_BODY = {"chat_template_kwargs": {"enable_thinking": False}}

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

# Versió de la suite de tasques: puja quan canvia el conjunt (hard_code_tier R7:
# v2 = +16 tasques hard). El pool la guarda per distingir condicions pre/post.
TASKS_VERSION = "v2"

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
