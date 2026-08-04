import subprocess
import time
import urllib.error
import urllib.request
import json

from . import config


def resolve_context(context_mode, model_path=None):
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