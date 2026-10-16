import os
import shutil
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

# Engines the harness knows how to start. "llama" = llama-server with the
# harness' flags; "strata" = serve/server.py with a strata-<model>.json config.
ENGINES = ("llama", "strata")

# Wait for the server to answer a test chat (s). Strata loads tens of GB into
# RAM before answering the first request.
READY_TIMEOUT = {"llama": 240, "strata": config.STRATA_READY_TIMEOUT}


# Context flags. The model profile pins it (models/<model>.txt for llama,
# --max-context in the Strata json); otherwise the harness decides with the mode.
_CTX_FLAGS = ("-c", "--ctx-size")
_STRATA_CTX_FLAGS = ("--max-context",)


def _pinned_flag_value(raw_args, *names):
    """Value a profile pins as `-c 32000` or `--ctx-size=65536`; None if it does not
    pin it.  Only used for flags that are in the allow-list (-c/--ctx-size are), so it
    does not need the validated list — and must not re-run it: the drop warnings would
    be printed twice."""
    for i, a in enumerate(raw_args):
        name, sep, val = a.partition("=")
        if name in names:
            raw = val if sep else (raw_args[i + 1] if i + 1 < len(raw_args) else "")
            try:
                return int(raw)
            except ValueError:
                raise ValueError(f"profile context pin {name} has no numeric value ({raw!r})")
    return None


def _strata_pinned_context(config_path):
    """Context a strata-<model>.json pins in its engine args (--max-context)."""
    try:
        cfg = json.loads(Path(config_path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    args = [str(a) for a in cfg.get("args", [])] if isinstance(cfg, dict) else []
    return _pinned_flag_value(args, *_STRATA_CTX_FLAGS)


def resolve_context_and_source(model_path, context_mode, engine="llama"):
    """Returns (ctx_resolved: int | None, ctx_source: str): the ONE place that decides
    the context.  build_args appends exactly what this returns and the receipt records
    it, so the command line and the row cannot drift.

      "profile"       the model's profile pins it (.txt -c/--ctx-size, or the Strata
                      config's --max-context) — the profile always wins (SPEC §2)
      "baseline"      fixed mode (or an explicit int): config.CONTEXT_FIXED
      "audit"         adapted mode: the audited ctx_max (config.resolve_context)
      "engine-default" a Strata config that pins no context: the engine chooses its own
                      number and the harness cannot know it — ctx_resolved is None, and
                      the row says so instead of inventing a figure.

    adapted without the audit artifact raises (config.resolve_context): there is no
    silent fallback."""
    if engine == "strata":
        pinned = _strata_pinned_context(model_path)
        return (pinned, "profile") if pinned is not None else (None, "engine-default")
    pinned = _pinned_flag_value(config.load_model_config_args(model_path), *_CTX_FLAGS)
    if pinned is not None:
        return pinned, "profile"
    return (config.resolve_context(context_mode, model_path),
            "audit" if context_mode == "adapted" else "baseline")


# Harness infrastructure flags: run.py/client.py wire them and the model's
# .txt cannot change them (a different --port would break the ready-check).
_INFRA_FLAGS = {"-m", "--model", "--port", "--host"}


def _strip_infra(args):
    """Removes --port/--host/-m/--model from a flag list (forms '--flag value'
    and '--flag=value')."""
    out, skip = [], False
    for a in args:
        if skip:
            skip = False
            continue
        name = a.split("=", 1)[0]
        if name in _INFRA_FLAGS:
            if "=" not in a:
                skip = True  # the value comes as a separate token: skip it
            continue
        out.append(a)
    return out


def _has_flag(args, *names):
    """True if args contains any of the flags ('--flag' or '--flag=...' form)."""
    return any(a.split("=", 1)[0] in names for a in args)


def _validate_model_flags(raw_args):
    """Filter raw model-profile flags through ALLOWED_MODEL_FLAGS.

    One pass, no index arithmetic and no mutation of the iterated list: a token
    starting with "-" is a flag name, and any other token is the value of the
    flag that precedes it.  Unknown flag names are dropped with one stderr
    warning each, and their value goes with them (a value is never kept without
    the flag that carries it).  A value that starts with "-" is a flag-shaped
    token: it is judged as a flag of its own — dropped and warned when it is
    not allow-listed — instead of being swallowed as the value of the flag
    before it, which is what used to shift every pair after a dropped flag.
    Returns (valid_args, [dropped_names]).
    """
    from . import config
    valid, dropped = [], []
    # the flag kept on the previous step takes its value as a separate token
    # ('--flag value'); '--flag=value' already carries its value inline
    keeps_next_token = False
    for token in raw_args:
        if not token.startswith("-"):
            if keeps_next_token:
                valid.append(token)  # value of a flag that passed the allow-list
            keeps_next_token = False
            continue
        name = token.split("=", 1)[0]
        if name in config.ALLOWED_MODEL_FLAGS:
            valid.append(token)
            keeps_next_token = "=" not in token
        else:
            dropped.append(name)
            keeps_next_token = False  # its value is dropped together with it
    for name in dropped:
        print(f"\u26a0\ufe0f profile flag not in allow-list, dropped: {name}", file=sys.stderr, flush=True)
    return valid, dropped


def build_args(model_path, context_mode, port):
    """Composes the server command line.

    'Runs at home as it runs here' policy: the default flags (SERVER_FLAGS +
    CACHE_FLAGS) provide the baseline, and models/<model>.txt is applied LAST
    (same convention as bin/start-dev-ai.sh), so it can override them.
    Controlled duplicates:
      - .txt with -c/--ctx-size  -> drop the harness' -c
      - .txt with --cache-type-k/v -> drop the corresponding CACHE_FLAGS entry
      - the rest (--spec-type, -md, --mmproj, ...) are simply appended."""
    raw = config.load_model_config_args(model_path)
    extra, _dropped = _validate_model_flags(_strip_infra(raw))
    # Same call the receipt uses: the decision and the args come from one place.
    ctx, ctx_source = resolve_context_and_source(model_path, context_mode)
    args = [str(config.SERVER_BIN), "-m", str(model_path)]
    if ctx_source != "profile":
        args += ["-c", str(ctx)]
    args += ["--port", str(port), *config.SERVER_FLAGS]
    if not _has_flag(extra, "--cache-type-k"):
        args += [config.CACHE_FLAGS[0], config.CACHE_FLAGS[1]]
    if not _has_flag(extra, "--cache-type-v"):
        args += [config.CACHE_FLAGS[2], config.CACHE_FLAGS[3]]
    args += extra
    return args


def describe_config(model_path, engine="llama"):
    """Readable description of the flags the model profile provides (for
    progress on stderr and as result metadata).  Unknown/dropped flags are
    appended so receipts show what was rejected.  None if no flags at all."""
    if engine == "strata":
        return describe_strata_config(model_path)
    raw = config.load_model_config_args(model_path)
    valid, dropped = _validate_model_flags(raw)
    parts = [" ".join(valid)] if valid else []
    if dropped:
        parts.append("dropped: " + ", ".join(dropped))
    return " | ".join(parts) if parts else None


def describe_strata_config(config_path):
    """Summary of the Strata config: model_name + engine args (this is what states
    'how it was measured' for this engine). None if it cannot be read (the run will
    still get the error at startup)."""
    try:
        cfg = json.loads(Path(config_path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    args = " ".join(str(a) for a in cfg.get("args", []))
    return (str(cfg.get("model_name") or Path(config_path).stem) + (" " + args if args else "")).strip()


def strata_command(config_path, port):
    """Strata startup command: <Strata venv> serve/server.py --engine strata
    --config <json> --port N. The config already carries pack/model/context/GPUs; the
    port is set by the harness (same contract as with llama-server, so the client
    does not need to know which engine it is)."""
    return [strata_python(), str(config.STRATA_DIR / "serve" / "server.py"),
            "--engine", "strata", "--config", str(config_path), "--port", str(port)]


def strata_python():
    """Interpreter for serve/server.py: the .venv setup.sh creates (the server
    depends on jinja2/numpy/... that the system python does NOT have — tested: an
    immediate ImportError). If absent, the harness' own: the startup will fail and the log will say why."""
    venv = config.STRATA_DIR / ".venv" / "bin" / "python"
    return str(venv) if venv.is_file() else sys.executable


class ServerManager:
    def __init__(self, model_path, context_mode="fixed", port=None, engine="llama",
                 thinking="off", extra_args=None):
        if engine not in ENGINES:
            raise ValueError(f"unknown engine: {engine!r} (expected one of {ENGINES})")
        if thinking not in ("on", "off"):
            raise ValueError(f"unknown thinking mode: {thinking!r} (expected 'on' or 'off')")
        self.engine = engine
        self.thinking = thinking  # record only (R1): the control goes via the body (ADR-4)
        self.model_path = str(model_path)
        self.context_mode = context_mode
        # Appended AFTER the model profile — same convention as the profile itself, so the
        # last word on a flag is the caller's. The smoke test uses it to load with a small
        # -c: the fleet's pins (256k+ with --mmproj and native MTP) only fit an otherwise
        # idle card, and a test must not fail for the desk's VRAM.
        self.extra_args = [str(a) for a in (extra_args or [])]
        self.port = port or (config.STRATA_PORT if engine == "strata" else config.PORT)
        self.ready_timeout = READY_TIMEOUT[engine]
        self.proc = None
        self.pgid = None
        self._logfh = None

    @property
    def log_path(self):
        """Where the server output is saved (Strata only): a startup
        error must be readable, not lost inside a DEVNULL."""
        return Path(tempfile.gettempdir()) / f"ggufbench-{self.engine}-server-{self.port}.log"

    def start(self):
        # Server output always lands in the log file (both engines): a crash
        # mid-run must leave its last words behind, not vanish into DEVNULL.
        # (Before: only Strata logged; llama crashes were undebuggable.)
        if self.engine == "strata":
            args = strata_command(self.model_path, self.port)
            cwd = str(config.STRATA_DIR)
        else:
            args = build_args(self.model_path, self.context_mode, self.port) + self.extra_args
            cwd = None
            extra = describe_config(self.model_path)
            if extra:
                print(f"  config {Path(self.model_path).stem}.txt: {extra}",
                      file=sys.stderr, flush=True)
        self._logfh = open(self.log_path, "w", encoding="utf-8")
        out = self._logfh
        print(f"  server log: {self.log_path}", file=sys.stderr, flush=True)
        # Own process group (start_new_session): stop() must also reach Strata's
        # child (engine/strata), which would otherwise be orphaned, and never another process.
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
        """Ready when a test chat returns 'choices' (not just /v1/models).
        The default `timeout` depends on the engine (STRATA_READY_TIMEOUT for Strata).
        Strata: first we wait for /health to say 'loaded' — otherwise the chat
        probes would queue up during the tens-of-GB load."""
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
        """Strata: True if the engine has the model loaded. Any error (not
        listening yet, weird response) counts as 'not yet'."""
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/health", timeout=5) as r:
                data = json.loads(r.read().decode("utf-8", "replace"))
            # key absent in old versions: do not block, let the chat probe try
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
            # Server not listening or connecting yet; the caller retries.
            return False

    def stop(self):
        proc, pgid, logfh = self.proc, self.pgid, self._logfh
        self.proc, self.pgid, self._logfh = None, None, None
        if proc is None:
            return
        # A server that already died on its own (nonzero exit) is the case worth
        # keeping evidence for: archive its log next to the run receipts instead
        # of letting the next start() truncate it away.
        died_rc = proc.poll()
        if proc.poll() is None:
            # SIGTERM first (clean stop); if it does not exit within 15s, escalate.
            try:
                proc.terminate()
            except OSError:
                pass
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                pass
        # Whole process group: with Strata the parent can die and leave the
        # engine/strata child alive, which would keep holding the VRAM. Empty group ->
        # ProcessLookupError (the normal case with llama-server, no children).
        if pgid:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except OSError:
                pass
        if logfh:
            logfh.close()
        if died_rc is not None and died_rc != 0:
            config.RESULTS_RUNS.mkdir(parents=True, exist_ok=True)
            ts = time.strftime("%Y%m%d-%H%M%S", time.localtime())
            dest = (config.RESULTS_RUNS /
                    f"{ts}-server-{self.engine}-{self.port}-CRASH.log")
            try:
                shutil.copy(self.log_path, dest)
            except OSError:
                dest = None
            print(f"  server died on its own (rc={died_rc}): log preserved at {dest}",
                  file=sys.stderr, flush=True)
        time.sleep(2)