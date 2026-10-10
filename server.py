import os
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import json
from pathlib import Path

from . import config

# Motors que el harness sap arrencar. "llama" = llama-server amb els flags del
# harness; "strata" = serve/server.py amb un config strata-<model>.json.
ENGINES = ("llama", "strata")

# Espera perquè el servidor respongui a un chat de prova (s). Strata carrega
# desenes de GB a RAM abans de respondre la primera petició.
READY_TIMEOUT = {"llama": 240, "strata": config.STRATA_READY_TIMEOUT}


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


def describe_config(model_path, engine="llama"):
    """Descripció llegible dels flags que aporta el perfil del model (per al
    progrés a stderr i com a metadada del resultat). None si no en té."""
    if engine == "strata":
        return describe_strata_config(model_path)
    extra = config.load_model_config_args(model_path)
    return " ".join(extra) if extra else None


def describe_strata_config(config_path):
    """Resum del config de Strata: model_name + args del motor (és el que diu
    'com es va mesurar' per aquest motor). None si no es pot llegir (la run en
    tindrà igualment l'error a l'arrencada)."""
    try:
        cfg = json.loads(Path(config_path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    args = " ".join(str(a) for a in cfg.get("args", []))
    return (str(cfg.get("model_name") or Path(config_path).stem) + (" " + args if args else "")).strip()


def strata_command(config_path, port):
    """Comanda d'arrancada d'Strata: <venv de Strata> serve/server.py --engine strata
    --config <json> --port N. El config ja porta pack/model/context/GPUs; el port el
    fixa el harness (mateix contracte que amb llama-server, perquè el client no ha de
    saber de quin motor es tracta)."""
    return [strata_python(), str(config.STRATA_DIR / "serve" / "server.py"),
            "--engine", "strata", "--config", str(config_path), "--port", str(port)]


def strata_python():
    """Intèrpret per a serve/server.py: el .venv que crea setup.sh (el servidor
    depèn de jinja2/numpy/... que el python del sistema NO té — provat: ImportError
    immediata). Si no n'hi ha, el del harness: l'arrencada fallarà i el log dirà per què."""
    venv = config.STRATA_DIR / ".venv" / "bin" / "python"
    return str(venv) if venv.is_file() else sys.executable


class ServerManager:
    def __init__(self, model_path, context_mode="fixed", port=None, engine="llama",
                 thinking="off"):
        if engine not in ENGINES:
            raise ValueError(f"engine desconegut: {engine!r} (esperat un de {ENGINES})")
        if thinking not in ("on", "off"):
            raise ValueError(f"thinking desconegut: {thinking!r} (esperat 'on' o 'off')")
        self.engine = engine
        self.thinking = thinking  # només registre (R1): el control va pel cos (ADR-4)
        self.model_path = str(model_path)
        self.context_mode = context_mode
        self.port = port or (config.STRATA_PORT if engine == "strata" else config.PORT)
        self.ready_timeout = READY_TIMEOUT[engine]
        self.proc = None
        self.pgid = None
        self._logfh = None

    @property
    def log_path(self):
        """On es desa la sortida del servidor (Strata només): un error d'arrencada
        ha de ser llegible, no invisible enmig d'un DEVNULL."""
        return Path(tempfile.gettempdir()) / f"benchmark-{self.engine}-server-{self.port}.log"

    def start(self):
        out = subprocess.DEVNULL
        if self.engine == "strata":
            args = strata_command(self.model_path, self.port)
            cwd = str(config.STRATA_DIR)
            self._logfh = open(self.log_path, "w", encoding="utf-8")
            out = self._logfh
            print(f"  log del servidor: {self.log_path}", file=sys.stderr, flush=True)
        else:
            args = build_args(self.model_path, self.context_mode, self.port)
            cwd = None
            extra = describe_config(self.model_path)
            if extra:
                print(f"  config {Path(self.model_path).stem}.txt: {extra}",
                      file=sys.stderr, flush=True)
        # Grup de processos propi (start_new_session): stop() ha d'arribar també al
        # fill d'Strata (engine/strata), que sinó queda orfe, i mai a un altre procés.
        self.proc = subprocess.Popen(args, stdout=out, stderr=subprocess.STDOUT,
                                     cwd=cwd, start_new_session=True)
        try:
            self.pgid = os.getpgid(self.proc.pid)
        except OSError:
            self.pgid = self.proc.pid
        return self.proc

    def is_alive(self):
        return self.proc is not None and self.proc.poll() is None

    def wait_ready(self, timeout=None):
        """Llest quan un chat de prova retorna 'choices' (no només /v1/models).
        `timeout` per defecte depèn del motor (STRATA_READY_TIMEOUT per a Strata).
        Strata: primer esperem que /health digui 'loaded' — sense això, les sondes
        de chat quedarien a la cua durant la càrrega de desenes de GB."""
        deadline = time.time() + (self.ready_timeout if timeout is None else timeout)
        while time.time() < deadline:
            if not self.is_alive():
                return False
            if self.engine == "strata" and not self._health_loaded():
                time.sleep(1)
                continue
            if self._chat_probe():
                return True
            time.sleep(1)
        return False

    def _health_loaded(self):
        """Strata: True si el motor té el model carregat. Qualsevol error (encara
        no escolta, resposta estranya) compta com a 'no encara'."""
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/health", timeout=5) as r:
                data = json.loads(r.read().decode("utf-8", "replace"))
            # clau absent en versions velles: no bloquejar, deixa provar el chat
            return data.get("loaded", True) is True
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return False

    def _chat_probe(self):
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{self.port}/v1/chat/completions",
                data=json.dumps({"messages": [{"role": "user", "content": "hi"}],
                                 "max_tokens": 1}).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return '"choices"' in r.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError, OSError):
            # Servidor encara no escolta o connecta; el caller torna a intentar.
            return False

    def stop(self):
        proc, pgid, logfh = self.proc, self.pgid, self._logfh
        self.proc, self.pgid, self._logfh = None, None, None
        if proc is None:
            return
        if proc.poll() is None:
            # SIGTERM primer (aturada neta); si no surt en 15s, baixulla a baix.
            try:
                proc.terminate()
            except OSError:
                pass
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                pass
        # Grup de processos sencer: amb Strata el pare pot morir i deixar viu el fill
        # engine/strata, que sinó continuaria retinguent la VRAM. Grup buit ->
        # ProcessLookupError (el cas normal amb llama-server, sense fills).
        if pgid:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except OSError:
                pass
        if logfh:
            logfh.close()
        time.sleep(2)