import argparse
import datetime
import difflib
import json
import platform
import subprocess
import sys
from pathlib import Path

from . import config, server as S, client as C, graders as G, tasks_loader as T, report as R, html_report


def parse_weights(s):
    if not s:
        return dict(config.WEIGHTS)
    w = {}
    for part in s.split(","):
        k, v = part.split("=")
        w[k.strip()] = float(v)
    return w


def resolve_models(spec, engine="llama"):
    """all -> glob of the models directory. Otherwise, each item (comma-separated)
    can be:
      - an existing path (used as is),
      - a short or partial file name ('Ornith-...APEX-MTP-Quality[.gguf]'),
        resolved against models/*.gguf (same spirit as --forget);
        if it matches more than one file, a warning is printed and it is skipped (ambiguous),
      - a nonexistent path: passes through as is and llama-server will report the error.

    With ``engine='strata'`` the 'model' is a config: 'iq3_xxs' ->
    Strata/strata-iq3_xxs.json (and 'all' = every strata-*.json)."""
    if engine == "strata":
        return _resolve_strata_models(spec)
    if spec == "all":
        return sorted(str(p) for p in config.MODELS_DIR.glob("*.gguf"))
    if isinstance(spec, str):
        spec = [x.strip() for x in spec.split(",") if x.strip()]
    resolved = []
    for item in spec:
        if Path(item).is_file():
            resolved.append(item)
            continue
        matches = sorted(config.MODELS_DIR.glob(f"*{item}*"))
        if len(matches) == 1:
            resolved.append(str(matches[0]))
        elif len(matches) > 1:
            names = ", ".join(m.name for m in matches)
            print(f"⚠️  '{item}' is ambiguous ({names}); no unique match, ignored",
                  file=sys.stderr, flush=True)
        else:
            resolved.append(item)
    return resolved


def _resolve_strata_models(spec):
    """Resolves the Strata model specification against STRATA_DIR. Accepts 'all',
    the short name ('iq3_xxs'), the file name ('strata-iq3_xxs[.json]') or a full path.
    With no match it passes through as is (server.py will report the error)."""
    if spec == "all":
        return sorted(str(p) for p in config.STRATA_DIR.glob("strata-*.json"))
    if isinstance(spec, str):
        spec = [x.strip() for x in spec.split(",") if x.strip()]
    resolved = []
    for item in spec:
        if Path(item).is_file():
            resolved.append(item)
            continue
        name = item if item.endswith(".json") else item + ".json"
        if not name.startswith("strata-"):
            name = "strata-" + name
        cand = config.STRATA_DIR / name
        resolved.append(str(cand) if cand.is_file() else item)
    return resolved


def model_id(engine, model_path):
    """Model identifier in the pool (and for the scoreboard slug): the .gguf path
    as is for llama-server; for Strata, the config name without extension
    ('strata-iq3_xxs') — which is what identifies model + quantization + configuration."""
    if engine == "strata":
        return Path(model_path).stem
    return model_path


def warmup(client_mod, model_url, n=3, extra=None):
    times = []
    for i in range(n):
        start = datetime.datetime.now()
        try:
            C.chat([{"role": "user", "content": "hi"}], max_tokens=4,
                   base_url=model_url, extra=extra)
        except (OSError, ValueError):
            # Best-effort: urlopen -> OSError (URLError), json -> ValueError; we only measure time.
            pass
        elapsed = (datetime.datetime.now() - start).total_seconds()
        times.append(elapsed)
        print(f"  warmup {i + 1}/{n}: {elapsed:.2f}s", file=sys.stderr, flush=True)
    return times

def _print_task(dim, info):
    """Prints the result of a task as it completes (stderr + flush, so the terminal
    does not stay frozen during slow dimensions and --json keeps stdout clean)."""
    lang = info.get("lang") or "—"
    tid = info.get("id", "")
    if dim == "speed":
        print(f"  {dim:5} {lang:11} {tid:20} {info.get('ms', 0)}ms  {info.get('gen_tps', 0)} t/s",
              file=sys.stderr, flush=True)
        return
    mark = "✓" if info.get("passed") else "✗"
    if info.get("excluded"):
        mark = "⊘"  # truncation/format or server error: does not count toward the score
    if dim == "agent":
        extra = f"turns={info.get('turns', 0)}"
    else:
        extra = " ".join(str(info.get("detail") or "").split())[:60]
    print(f"  {dim:5} {lang:11} {tid:20} {mark} {extra}",
          file=sys.stderr, flush=True)


def _level_for_code(dims, level):
    """--level only affects the code dimension; if code is absent, warn and drop it."""
    if not level:
        return None
    if "code" not in dims:
        print(f"⚠️  --level {level}: code is not in --dims, ignored",
              file=sys.stderr, flush=True)
        return None
    return level


def _bench_one(model_path, pool, dims, lang_filter, port, quick=False, engine="llama",
               level=None, thinking=None):
    if thinking is None:
        thinking = config.THINKING_DEFAULT
    # C5: hardware/OS snapshot captured once per model run, before anything else.
    env = _probe_environment()
    sm = S.ServerManager(model_path, context_mode="fixed", port=port, engine=engine,
                         thinking=thinking)
    mid = model_id(engine, model_path)
    slug = config.slug(mid)
    print(f"→ {slug}: starting server ({engine})...", file=sys.stderr, flush=True)
    sm.start()
    if not sm.wait_ready():
        sm.stop(); return {"model": mid, "engine": engine, "serve_failed": True}
    try:
        model_url = f"http://127.0.0.1:{port}"
        # Thinking (R1 thinking_batches): `off` disables it in the body (same channel for
        # both engines); `on` leaves it free. The protocol (dims, tasks, prompts) is untouched.
        extra = config.thinking_body(engine, thinking)

        class ClientWrapper:
            def __init__(self, base_url, extra=None):
                self.base_url, self.extra = base_url, extra

            def chat(self, *a, **k):
                if self.extra:
                    k.setdefault("extra", self.extra)
                return C.chat(*a, base_url=self.base_url, **k)
        c = ClientWrapper(model_url, extra)
        times = warmup(c, model_url, n=3, extra=extra)
        result = {"model": mid, "engine": engine, "thinking": thinking,
                  "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                  "context_mode": "fixed", "tasks_version": config.TASKS_VERSION,
                  "server_build": _server_build(engine), "warmup_times": times,
                  "model_config_flags": S.describe_config(model_path, engine=engine),
                  "environment": env}
        lf = set(lang_filter) if lang_filter else None
        if "speed" in dims:
            result["speed"] = G.grade_speed(c, _limit(T.load("speed"), quick), on_task=_print_task)
        if "tools" in dims:
            result["tools"] = G.grade_tools(c, _limit(T.load("tools"), quick), on_task=_print_task)
        if "code" in dims:
            code_tasks = _limit(T.load("code", lang_filter=lf, level=level), quick)
            if level and not code_tasks:
                print(f"⚠️  no code task at level={level}", file=sys.stderr, flush=True)
            result["code"] = G.grade_code(c, code_tasks,
                                          on_task=_print_task, model_slug=slug,
                                          gen_tps=result["speed"]["gen_tps"] if "speed" in result else None,
                                          thinking=thinking)
        if "agent" in dims:
            result["agent"] = G.grade_agent(c, _limit(T.load("agent", lang_filter=lf), quick), on_task=_print_task)
        return result
    finally:
        sm.stop()


def _limit(tasks, quick):
    """--quick: only the first task of each dimension (harness smoke test)."""
    return tasks[:1] if quick else tasks

def _server_build(engine="llama"):
    """Engine version: llama-server's for 'llama'; Strata's is read from
    strata/engine/BUILD.json (version of the compiled executable)."""
    if engine == "strata":
        try:
            return str(json.loads((config.STRATA_DIR / "engine" / "BUILD.json")
                                  .read_text(encoding="utf-8"))["version"])
        except (OSError, ValueError, KeyError):
            return "unknown"
    try:
        out = subprocess.run([str(config.SERVER_BIN), "--version"],
                             capture_output=True, text=True, timeout=10)
        # llama-server writes the version to stderr, not stdout: both must be checked.
        for line in (out.stdout + out.stderr).splitlines():
            if line.startswith("version:"):
                return line.split()[1]
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "unknown"


def _compact_gpu_name(name):
    """'NVIDIA GeForce RTX 5080' -> 'RTX 5080': strips the vendor prefix but keeps
    the rest of the name faithful ('NVIDIA A100-SXM4-40GB' keeps its suffixes)."""
    for prefix in ("NVIDIA GeForce ", "NVIDIA "):
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def _meminfo_ram_gb():
    """MemTotal from /proc/meminfo as integer GiB (None off-Linux or unreadable)."""
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                return round(int(line.split()[1]) / 1024 / 1024)  # kB -> GiB
    except (OSError, ValueError, IndexError):
        pass
    return None


def _probe_environment():
    """Hardware/OS snapshot stored with every result (C5): an old result must be
    interpretable months later. Best-effort by design — with no nvidia-smi
    (CPU-only machine, CI) or on any failure it degrades to an empty GPU list
    while os/ram_gb stay filled, and it never crashes nor stalls a run
    (subprocess timeout)."""
    env = {"gpu": [], "driver": None, "os": platform.platform(),
           "ram_gb": _meminfo_ram_gb()}
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
                              "--format=csv,noheader"],
                             capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return env
    if out.returncode != 0:
        return env
    gpus, drivers = [], set()
    for line in out.stdout.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 3:
            continue
        name, mib, driver = parts
        try:
            vram = f"{round(int(mib.split()[0]) / 1024)}GB"  # '16311 MiB' -> '16GB'
        except (ValueError, IndexError):
            vram = ""  # e.g. '[N/A]': keep the bare name rather than invent a figure
        gpus.append((_compact_gpu_name(name) + " " + vram).strip())
        drivers.add(driver)
    if gpus:
        env["gpu"] = gpus
        env["driver"] = ", ".join(sorted(drivers))  # one driver per machine; joined just in case
    return env


def _parse_args(argv=None):
    """Pure CLI parsing (testable without a GPU): every option, including
    --thinking. main() only runs it."""
    ap = argparse.ArgumentParser(prog="ggufbench")
    ap.add_argument("--models", default="all",
                    help="all | .gguf path | name (short or partial) — comma-separated "
                         "(with --engine strata: all | config name, ex. iq3_xxs)")
    ap.add_argument("--engine", choices=list(S.ENGINES), default="llama",
                    help="engine that serves the model: llama = llama-server (default); "
                         "strata = serve/server.py with a strata-<model>.json config")
    ap.add_argument("--context", default="fixed", choices=["fixed", "adapted"])
    ap.add_argument("--dims", default="speed,tools,code,agent")
    ap.add_argument("--lang", default=None)
    ap.add_argument("--level", choices=["easy", "hard", "expert"], default=None,
                    help="filters ONLY the code tasks by level "
                         "(ID suffix _hard or _expert)")
    ap.add_argument("--thinking", choices=["on", "off"], default=config.THINKING_DEFAULT,
                    help="chain of thought of the model: off disables it via "
                         "chat_template_kwargs (default); on leaves it free. "
                         "It is recorded in every result.")
    ap.add_argument("--quick", action="store_true",
                    help="1 task per dimension (harness smoke test)")
    ap.add_argument("-v", "--verbose", action="store_true",
                   help="granularity: Table 1 + per-language (Table 2); does NOT include tasks")
    ap.add_argument("--task", action="store_true",
                   help="per-task detail (Table 3): shows where each model succeeds/fails; composes with --verbose")
    ap.add_argument("--info", action="store_true",
                   help="Table 1 + Table 3 (per-task detail)")
    ap.add_argument("--scoreboard", action="store_true")
    ap.add_argument("--html", action="store_true",
                    help="after the run (or together with --scoreboard), regenerate "
                         "the HTML report from the accumulated pool")
    ap.add_argument("--compare", nargs=2, metavar="SLUG,THINK",
                    help="head-to-head page of two pool rows ('slug[,think]', think "
                         "defaults to off): writes results/compare.html")
    ap.add_argument("--forget")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--port", type=int, default=None,
                    help=f"default {config.PORT} (llama) / {config.STRATA_PORT} (strata)")
    ap.add_argument("--weights", default=None)
    return ap.parse_args(argv)


def _write_html_report(pool=None):
    """--html: regenerate the HTML report from the accumulated pool (the same
    source --scoreboard reads, not just this run's rows). One line of feedback on
    stderr either way, so --json keeps stdout parseable."""
    out = html_report.write_default_report(pool)
    if out is None:
        print("pool is empty: no HTML report written", file=sys.stderr, flush=True)
    else:
        print(f"→ report: {out}", file=sys.stderr, flush=True)


def _parse_compare_arg(spec):
    """--compare item: 'slug[,think]' — think optional, defaults to off. The slug
    never contains a comma (config.slug strips them), so rpartition is safe."""
    slug, sep, think = spec.rpartition(",")
    if not sep:
        return spec.strip(), config.THINKING_DEFAULT
    slug, think = slug.strip(), think.strip().lower()
    if think not in ("on", "off"):
        raise ValueError(f"thinking must be on|off, got '{think}' in '{spec}'")
    return slug, think


def _compare_row(pool, slug, think):
    """The (slug, thinking) pool row. Matches the raw slug (config.slug of the
    model field) or the display form the scoreboard shows (models_/model_ prefix
    stripped) — the user should not need to know which one the pool stores."""
    for r in pool:
        raw = config.slug(r["model"])
        if think == (r.get("thinking") or "—") and slug in (raw, html_report._display_slug(raw)):
            return r
    return None


def _write_compare(specs):
    """--compare: head-to-head page of two pool rows, rendered read-only from the
    accumulated pool (the same source --scoreboard reads). One line of feedback on
    stderr either way (same voice as --html); a missing row is a clear error that
    lists the available slug,think keys and the closest slugs."""
    pool = R.load_pool()
    rows = []
    for spec in specs:
        try:
            slug, think = _parse_compare_arg(spec)
        except ValueError as e:
            print(f"✗ --compare: {e}", file=sys.stderr, flush=True)
            return
        row = _compare_row(pool, slug, think)
        if row is None:
            available = "  ".join(
                f'{html_report._display_slug(config.slug(r["model"]))},{r.get("thinking") or "—"}'
                for r in sorted(pool, key=lambda r: (config.slug(r["model"]),
                                                     r.get("thinking") or "")))
            names = sorted({html_report._display_slug(config.slug(r["model"])) for r in pool})
            closest = ", ".join(difflib.get_close_matches(slug, names, n=3, cutoff=0.3)) or "none"
            print(f"✗ --compare: no pool row for '{slug},{think}'", file=sys.stderr, flush=True)
            print(f"  available: {available}", file=sys.stderr, flush=True)
            print(f"  closest: {closest}", file=sys.stderr, flush=True)
            return
        rows.append(row)
    out = html_report.write_default_compare(rows[0], rows[1], pool=pool)
    if out is None:
        print("pool is empty: no compare page written", file=sys.stderr, flush=True)
        return
    print(f"→ compare: {out}", file=sys.stderr, flush=True)


def main(argv=None):
    args = _parse_args(argv)
    weights = parse_weights(args.weights)
    port = args.port or (config.STRATA_PORT if args.engine == "strata" else config.PORT)
    # Granularity: --verbose adds Table 2 (per-language); --task adds the task
    # detail (Table 3). They are independent and can be combined (--verbose +
    # --task = Table 1 + Table 2 + Table 3).
    level = "verbose" if args.verbose else ("info" if args.info else "default")

    if args.forget:
        removed = R.forget(args.forget)
        if removed:
            print(f"removed {removed} model(s) from the pool", file=sys.stderr, flush=True)
        else:
            print(f"no model matching '{args.forget}' found",
                  file=sys.stderr, flush=True)
        return
    if args.compare:
        _write_compare(args.compare)
        return
    if args.scoreboard:
        pool = R.load_pool()
        print(R.render(pool, weights, title="Scoreboard", level=level, show_tasks=args.task))
        # --scoreboard --html = "refresh everything": read-only render + report
        # regenerated from the same accumulated pool.
        if args.html:
            _write_html_report(pool)
        return

    dims = [d.strip() for d in args.dims.split(",") if d.strip()]
    lang_filter = args.lang.split(",") if args.lang else None
    level = _level_for_code(dims, args.level)
    models = resolve_models(args.models, engine=args.engine)
    if not models:
        print("no model to run (check --models)", file=sys.stderr, flush=True)
        return
    for mp in models:
        try:
            res = _bench_one(mp, [], dims, lang_filter, port, quick=args.quick,
                             engine=args.engine, level=level, thinking=args.thinking)
            if res.get("serve_failed"):
                print(f"✗ {mp}: failed to load", file=sys.stderr, flush=True); continue
            R.save_result(res)
            slug = config.slug(model_id(args.engine, mp))
            speed = res.get("speed", {}).get("speed_ms", 0)
            gen_tps = res.get("speed", {}).get("gen_tps", 0)
            tools = res.get("tools", {}).get("score", 0)
            code = res.get("code", {}).get("score", 0)
            code_excl = res.get("code", {}).get("excluded", 0)
            agent = res.get("agent", {}).get("score", 0)
            code_lbl = f"{code:.2f}" + (f" ({code_excl} excluded)" if code_excl else "")
            print(f"✓ {slug}: speed={speed}ms ({gen_tps} t/s) "
                  f"tools={tools:.2f} code={code_lbl} agent={agent:.2f}",
                  file=sys.stderr, flush=True)
        except Exception as e:
            # Safety net of the batch: isolates one model's failure so it does not take down the whole run.
            print(f"✗ {mp}: {e}", file=sys.stderr, flush=True)
    pool = R.load_pool()
    if args.json:
        print(json.dumps(pool, indent=2, ensure_ascii=False))
    else:
        print(R.render(pool, weights, title="Benchmark Results", level=level, show_tasks=args.task))
    if args.html:
        _write_html_report(pool)

if __name__ == "__main__":
    main()