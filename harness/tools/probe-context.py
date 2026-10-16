#!/usr/bin/env python3
"""Measure a model's REAL maximum context, live — the `--verify` that
`context-audit.py` still declares unimplemented.

Why it exists
-------------
`context-audit.py` is an estimator: it charges a full KV cache to every layer and reserves
15% of VRAM plus 25% of compute. Its own note says so — for arches with sliding windows or
hybrid attention the number is a LOWER bound — and even for plain attention the reserves are
conservative. Measured 2026-10-15 (models/CONTEXT-AUDIT.md has the table): the fleet reaches
193k-266k where the estimator said 78k-232k, and gemma-4-26B declared 32k against a real
262144 (3-8x short). The pins in `models/<model>.txt` came from the estimator, so they were
ceilings of an estimate, not of the card.

What it does
------------
Loads the model with the harness' OWN command line — `server.build_args()`, so the baseline,
the `--mmproj`, the `--split-mode`, the KV type and every profile flag are the ones a real
run uses — and changes nothing but `-c`. Readiness is the /health endpoint; a candidate that
raises the server, or that the CUDA allocator refuses, is the first "no", and the value just
below it is the answer. Bisection, so ~4 loads per model.

Examples
--------
    python3 ggufbench/harness/tools/probe-context.py --models "models/*.gguf"
    python3 ggufbench/harness/tools/probe-context.py \
        --models models/Qwen3.8-27B-Heretic-Q4_K_M.gguf --port 8999
    python3 ggufbench/harness/tools/probe-context.py --models "models/*.gguf" \
        --json /tmp/probe.json --kv q8_0

Exit codes: 0 ran · 1 nothing matched · 2 usage error.
"""

from __future__ import annotations

import argparse
import glob
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
_PKG_DIR = _TOOLS_DIR.parent.parent                 # ggufbench/
_ROOT_DIR = _PKG_DIR.parent                         # workspace root
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from ggufbench import server  # noqa: E402


def _argv_for(model: str, ctx: int, port: int, kv: str | None) -> list[str]:
    """The harness' own command line, with the profile's `-c` (or the baseline's) replaced."""
    args = server.build_args(model, "fixed", port)
    if kv:                                          # override the KV type of the baseline
        for i, tok in enumerate(args):
            if tok in ("--cache-type-k", "--cache-type-v") and i + 1 < len(args):
                args[i + 1] = kv
    out, replaced, i = [], False, 0
    while i < len(args):
        if args[i] in ("-c", "--ctx-size") and i + 1 < len(args):
            out += [args[i], str(ctx)]
            replaced = True
            i += 2
            continue
        out.append(args[i])
        i += 1
    if not replaced:
        out += ["-c", str(ctx)]
    return out


def _health_ok(port: int, timeout: int = 3) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=timeout) as r:
            return json.loads(r.read().decode()).get("status") == "ok"
    except Exception:
        return False


def _wait_port_free(port: int, timeout: int = 25) -> bool:
    """Block until nothing answers on the port.

    Loaded 2026-10-15: Heretic's probe reported 262144 as OK, yet the batch crashed there with
    '884 MiB on device 0: cudaMalloc failed' loading its --mmproj. A server that has not died
    yet still answers /health — the next attempt then reads the PREVIOUS load's OK and a
    context that does not fit is recorded as one that does. Terminating is not enough; wait for
    the port to go quiet before believing anything.
    """
    t0 = time.time()
    while time.time() - t0 < timeout:
        if not _health_ok(port, timeout=2):
            return True
        time.sleep(1)
    return False


def _vram() -> list[int]:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used",
                              "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=20).stdout
        return [int(x) for x in out.split()]
    except Exception:
        return []


def _vram_total() -> list[int]:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.total",
                              "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=20).stdout
        return [int(x) for x in out.split()]
    except Exception:
        return []


def probe(model: str, ctx: int, port: int, kv: str | None, log_dir: Path,
          timeout: int, margin_mib: int = 0) -> tuple[str, list[int], Path]:
    """Status of loading this context: 'ok', 'tight' or 'fail'; plus VRAM and the log path.

    'tight' exists because of Heretic, 2026-10-15: the probe said 262144 loaded and the batch
    then died there with '884 MiB on device 0: cudaMalloc failed' loading its --mmproj. A
    context that loads with almost nothing to spare is not usable in a real run — the desk's
    own VRAM drifts up and down through the day. With a margin, such a load counts as too big.
    """
    log = log_dir / f"ctxprobe-{Path(model).stem[:24]}-{ctx}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "w") as fh:
        proc = subprocess.Popen(_argv_for(model, ctx, port, kv), stdout=fh,
                                stderr=subprocess.STDOUT, start_new_session=True,
                                cwd=str(_ROOT_DIR))
    t0, ok = time.time(), False
    while time.time() - t0 < timeout:
        if proc.poll() is not None:                 # it gave up on its own
            break
        if _health_ok(port):
            ok = True
            break
        txt = open(log, errors="ignore").read().lower()
        if any(s in txt for s in ("out of memory", "failed to allocate", "not enough",
                                  "cuda error", "unknown argument", "error: ")):
            break
        time.sleep(3)
    used = _vram() if ok else []
    status = "fail"
    if ok:
        free = [t - u for t, u in zip(_vram_total(), used)] if used else []
        status = "tight" if (margin_mib and free and min(free) < margin_mib) else "ok"
    proc.terminate()
    try:
        proc.wait(timeout=40)
    except subprocess.TimeoutExpired:
        proc.kill()
    if not _wait_port_free(port):
        print(f"  ! the server on port {port} did not go quiet — results from here are suspect",
              file=sys.stderr, flush=True)
    time.sleep(2)
    return status, used, log


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Measure the maximum context a model really loads with (live).")
    ap.add_argument("--models", required=True,
                    help="comma-separated paths and/or globs, e.g. 'models/*.gguf'")
    ap.add_argument("--port", type=int, default=8999, help="port to test on (default 8999)")
    ap.add_argument("--kv", default=None, help="force a KV type (default: the model's own)")
    ap.add_argument("--floor", type=int, default=32768, help="known-good starting point")
    ap.add_argument("--ceiling", type=int, default=1048576, help="upper bound to try first")
    ap.add_argument("--timeout", type=int, default=240, help="seconds to wait per load")
    ap.add_argument("--margin-mib", type=int, default=1200,
                    help="free VRAM a load must leave to count as usable (default 1200)")
    ap.add_argument("--log-dir", default="/tmp/opencode", help="where the load logs go")
    ap.add_argument("--json", default=None, help="write the table as JSON here")
    args = ap.parse_args(argv)

    models: list[str] = []
    for spec in args.models.split(","):
        spec = spec.strip()
        if not spec:
            continue
        hits = sorted(glob.glob(spec)) if any(c in spec for c in "*?[") else [spec]
        models += [str(Path(h)) for h in hits]
    if not models:
        print("no model files matched", file=sys.stderr)
        return 1

    def show(ctx, status, used):
        verdict = {"ok": "OK", "tight": "TIGHT", "fail": "NO"}[status]
        free = [t - u for t, u in zip(_vram_total(), used)] if used else []
        extra = f"{used} free {free}" if used else ""
        print(f"  {ctx // 1024:>5}k → {verdict:5s} {extra}", flush=True)

    rows = {}
    for model in models:
        t0 = time.time()
        print(f"\n=== {Path(model).stem}", flush=True)
        status, used, _ = probe(model, args.ceiling, args.port, args.kv, Path(args.log_dir),
                                args.timeout, args.margin_mib)
        show(args.ceiling, status, used)
        lo, best = args.floor, None
        hi = args.ceiling
        if status == "ok":
            best = args.ceiling
        else:
            while hi - lo > 8192:
                mid = (((lo + hi) // 2) // 1024) * 1024
                if mid <= lo or mid >= hi:
                    break
                status, used, _ = probe(model, mid, args.port, args.kv, Path(args.log_dir),
                                        args.timeout, args.margin_mib)
                show(mid, status, used)
                if status == "ok":
                    lo, best = mid, mid
                else:
                    hi = mid
            if best is None:
                # 2026-10-16: with a window no wider than the 8k grid the loop above never runs
                # (`hi - lo > 8192` is false) and the tool answered "none" — true of the grid,
                # misleading about the model, since the declared floor may load fine. Verify it
                # once, so "none" comes to mean "not even the floor loads".
                status, used, _ = probe(model, args.floor, args.port, args.kv, Path(args.log_dir),
                                        args.timeout, args.margin_mib)
                show(args.floor, status, used)
                if status == "ok":
                    best = args.floor
        rows[Path(model).stem] = {"max_ctx": best, "seconds": round(time.time() - t0, 1)}
        print(f"  → max measured: {best if best else 'none'}  ({time.time() - t0:.0f}s)", flush=True)

    print("\n" + "=" * 60)
    for name, r in rows.items():
        print(f"{name:52s} {str(r['max_ctx'] or '?'):>9}")
    if args.json:
        Path(args.json).write_text(json.dumps(rows, indent=1))
        print(f"\nWrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
