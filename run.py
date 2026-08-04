import argparse
import datetime
import json
import subprocess
import sys

from . import config, server as S, client as C, graders as G, tasks_loader as T, report as R


def parse_weights(s):
    if not s:
        return dict(config.WEIGHTS)
    w = {}
    for part in s.split(","):
        k, v = part.split("=")
        w[k.strip()] = float(v)
    return w


def resolve_models(spec):
    if spec == "all":
        return sorted(str(p) for p in config.MODELS_DIR.glob("*.gguf"))
    if isinstance(spec, str):
        spec = [x.strip() for x in spec.split(",")]
    return spec


def warmup(client_mod, model_url, n=3):
    times = []
    for i in range(n):
        start = datetime.datetime.now()
        try:
            C.chat([{"role": "user", "content": "hi"}], max_tokens=4, base_url=model_url)
        except (OSError, ValueError):
            # Best-effort: urlopen -> OSError (URLError), json -> ValueError; només mesurem temps.
            pass
        elapsed = (datetime.datetime.now() - start).total_seconds()
        times.append(elapsed)
        print(f"  warmup {i + 1}/{n}: {elapsed:.2f}s", file=sys.stderr, flush=True)
    return times

def _print_task(dim, info):
    """Mostra el resultat d'una tasca a mida que es completa (stderr + flush, perquè
    la terminal no es quedi congelada durant les dimensions lentes i --json mantingui
    stdout net)."""
    lang = info.get("lang") or "—"
    tid = info.get("id", "")
    if dim == "speed":
        print(f"  {dim:5} {lang:11} {tid:20} {info.get('ms', 0)}ms",
              file=sys.stderr, flush=True)
        return
    mark = "✓" if info.get("passed") else "✗"
    if dim == "agent":
        extra = f"turns={info.get('turns', 0)}"
    else:
        extra = " ".join(str(info.get("detail") or "").split())[:60]
    print(f"  {dim:5} {lang:11} {tid:20} {mark} {extra}",
          file=sys.stderr, flush=True)


def _bench_one(model_path, pool, dims, lang_filter, port, quick=False):
    sm = S.ServerManager(model_path, context_mode="fixed", port=port)
    slug = config.slug(model_path)
    print(f"→ {slug}: arrencant servidor...", file=sys.stderr, flush=True)
    sm.start()
    if not sm.wait_ready(timeout=240):
        sm.stop(); return {"model": model_path, "serve_failed": True}
    try:
        model_url = f"http://127.0.0.1:{port}"
        class ClientWrapper:
            def __init__(self, base_url):
                self.base_url = base_url
            def chat(self, *a, **k):
                return C.chat(*a, base_url=self.base_url, **k)
        c = ClientWrapper(model_url)
        times = warmup(c, model_url, n=3)
        result = {"model": model_path, "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                  "context_mode": "fixed", "tasks_version": "v1",
                  "server_build": _server_build(), "warmup_times": times}
        lf = set(lang_filter) if lang_filter else None
        if "speed" in dims:
            result["speed"] = G.grade_speed(c, _limit(T.load("speed"), quick), on_task=_print_task)
        if "tools" in dims:
            result["tools"] = G.grade_tools(c, _limit(T.load("tools"), quick), on_task=_print_task)
        if "code" in dims:
            result["code"] = G.grade_code(c, _limit(T.load("code", lang_filter=lf), quick), on_task=_print_task)
        if "agent" in dims:
            result["agent"] = G.grade_agent(c, _limit(T.load("agent", lang_filter=lf), quick), on_task=_print_task)
        return result
    finally:
        sm.stop()


def _limit(tasks, quick):
    """--quick: només la primera tasca de cada dimensió (smoke test del harness)."""
    return tasks[:1] if quick else tasks

def _server_build():
    try:
        out = subprocess.run([str(config.SERVER_BIN), "--version"],
                             capture_output=True, text=True, timeout=10)
        for line in out.stdout.splitlines():
            if line.startswith("version:"):
                return line.split()[1]
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "unknown"

def main(argv=None):
    ap = argparse.ArgumentParser(prog="benchmark")
    ap.add_argument("--models", default="all")
    ap.add_argument("--context", default="fixed", choices=["fixed", "adapted"])
    ap.add_argument("--dims", default="speed,tools,code,agent")
    ap.add_argument("--lang", default=None)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--scoreboard", action="store_true")
    ap.add_argument("--forget")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--port", type=int, default=config.PORT)
    ap.add_argument("--weights", default=None)
    args = ap.parse_args(argv)
    weights = parse_weights(args.weights)

    if args.forget:
        R.forget(args.forget); print(f"esborrat {args.forget} del pool"); return
    if args.scoreboard:
        pool = R.load_pool()
        print(R.render(pool, weights, title="Scoreboard"))
        return

    dims = [d.strip() for d in args.dims.split(",") if d.strip()]
    lang_filter = args.lang.split(",") if args.lang else None
    models = resolve_models(args.models)
    for mp in models:
        try:
            res = _bench_one(mp, [], dims, lang_filter, args.port, quick=args.quick)
            if res.get("serve_failed"):
                print(f"✗ {mp}: no carrega", file=sys.stderr, flush=True); continue
            R.save_result(res)
            slug = config.slug(mp)
            speed = res.get("speed", {}).get("speed_ms", 0)
            tools = res.get("tools", {}).get("score", 0)
            code = res.get("code", {}).get("score", 0)
            agent = res.get("agent", {}).get("score", 0)
            print(f"✓ {slug}: speed={speed}ms tools={tools:.2f} code={code:.2f} agent={agent:.2f}",
                  file=sys.stderr, flush=True)
        except Exception as e:
            # Xarxa de seguretat del batch: aïlla la fallada d'un model per no tomba tota la run.
            print(f"✗ {mp}: {e}", file=sys.stderr, flush=True)
    pool = R.load_pool()
    if args.json:
        print(json.dumps(pool, indent=2, ensure_ascii=False))
    else:
        print(R.render(pool, weights, title="Benchmark Results"))

if __name__ == "__main__":
    main()