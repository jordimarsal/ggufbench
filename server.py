import subprocess
import sys
import time
import urllib.error
import urllib.request
import json
from pathlib import Path

from . import config


def resolve_context(context_mode, model_path=None):
    """fixed -> CONTEXT_FIXED; int -> int; adapted -> estima viable (fallback 8192)."""
    if isinstance(context_mode, int):
        return context_mode
    if context_mode == "fixed":
        return config.CONTEXT_FIXED
    # adapted: delegem a un estimator extern quan estigui; fallback segur
    return 8192


# Flags d'infraestructura del harness: els connecta run.py/client.py i el .txt
# del model no els pot canviar (un --port diferent trencaria el ready-check).
_INFRA_FLAGS = {"-m", "--model", "--port", "--host"}


def _strip_infra(args):
    """Treu --port/--host/-m/--model d'una llista de flags ( formes '--flag valor'
    i '--flag=valor')."""
    out, skip = [], False
    for a in args:
        if skip:
            skip = False
            continue
        name = a.split("=", 1)[0]
        if name in _INFRA_FLAGS:
            if "=" not in a:
                skip = True  # el valor va com a token separat: salta'l
            continue
        out.append(a)
    return out


def _has_flag(args, *names):
    """True si args conté qualsevol dels flags (forma '--flag' o '--flag=...')."""
    return any(a.split("=", 1)[0] in names for a in args)


def build_args(model_path, context_mode, port):
    """Composa la línia de comandes del servidor.

    Politica 'tal com corre a casa': els flags per defecte (SERVER_FLAGS +
    CACHE_FLAGS) donen el baseline, i models/<model>.txt s'aplica AL FINAL
    (mateixa convenció que bin/start-dev-ai.sh), així que pot sobreescriure'ls.
    Duplicats controlats:
      - .txt amb -c/--ctx-size  -> fora el -c del harness
      - .txt amb --cache-type-k/v -> fora el corresponent de CACHE_FLAGS
      - la resta (--spec-type, -md, --mmproj, ...) simplement s'afegeixen."""
    extra = _strip_infra(config.load_model_config_args(model_path))
    args = [str(config.SERVER_BIN), "-m", str(model_path)]
    if not _has_flag(extra, "-c", "--ctx-size"):
        args += ["-c", str(resolve_context(context_mode, model_path))]
    args += ["--port", str(port), *config.SERVER_FLAGS]
    if not _has_flag(extra, "--cache-type-k"):
        args += [config.CACHE_FLAGS[0], config.CACHE_FLAGS[1]]
    if not _has_flag(extra, "--cache-type-v"):
        args += [config.CACHE_FLAGS[2], config.CACHE_FLAGS[3]]
    args += extra
    return args


def describe_config(model_path):
    """Descripció llegible dels flags que aporta models/<model>.txt (per al
    progrés a stderr). None si el model no en té."""
    extra = config.load_model_config_args(model_path)
    return " ".join(extra) if extra else None


class ServerManager:
    def __init__(self, model_path, context_mode="fixed", port=None):
        self.model_path = str(model_path)
        self.context_mode = context_mode
        self.port = port or config.PORT
        self.proc = None

    def start(self):
        args = build_args(self.model_path, self.context_mode, self.port)
        extra = describe_config(self.model_path)
        if extra:
            print(f"  config {Path(self.model_path).stem}.txt: {extra}",
                  file=sys.stderr, flush=True)
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
                    data=json.dumps({"messages": [{"role": "user", "content": "hi"}],
                                     "max_tokens": 1}).encode(),
                    headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    if '"choices"' in r.read().decode("utf-8", "replace"):
                        return True
            except (urllib.error.URLError, TimeoutError, OSError):
                # Servidor encara no escolta o connecta; torna a intentar.
                pass
            time.sleep(1)
        return False

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.kill()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
        self.proc = None