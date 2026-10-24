import argparse
import datetime
import urllib.request
import difflib
import json
import platform
import re
import subprocess
import sys
import time
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
    ('strata-iq3_xxs') — which is what identifies model + quantization + configuration.

    A .gguf path inside the workspace is stored relative to it: `--models` globs the
    models directory and hands out absolute paths, while the same model passed by hand
    ('models/x.gguf') stays relative. Identity must not depend on that — it put the same
    model twice in the pool (qwen36, 2026-10-13). Models outside the workspace keep the
    path as given, relative or absolute."""
    if engine == "strata":
        return Path(model_path).stem
    if engine == "bmoe":
        # Prefix so a bmoe row can never be mistaken for the llama.cpp baseline of
        # the very same .gguf file: the engines differ in everything but the weights.
        return "bmoe-" + Path(model_path).stem
    return _stable_model_path(model_path)


def _stable_model_path(model_path):
    """Absolute path inside the workspace -> relative to it; anything else, as given."""
    p = Path(str(model_path))
    if not p.is_absolute():
        return str(model_path)
    try:
        return str(p.relative_to(config.BASE_DIR))
    except ValueError:
        return str(model_path)


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


class ClientWrapper:
    """Wraps client.chat and injects per-run seeds for --runs > 1.

    When run_index is set (≥ 0), the request body gets ``{"seed": SEED + run_index}``.
    For engine=strata this field is harmless — strata simply ignores unknown body keys.
    When run_index is unset (the default, runs==1), extra passes through unchanged."""
    def __init__(self, base_url, extra=None):
        self.base_url, self.extra = base_url, extra
        self.run_index = None  # None = no seed injection (N==1 compat)

    def chat(self, *a, **k):
        if self.extra:
            k.setdefault("extra", dict(self.extra))
        elif self.run_index is not None:
            # No thinking body but we need extra for the seed (N==1 compat: never reaches here).
            k["extra"] = {}
        if self.run_index is not None:
            k["extra"]["seed"] = config.SEED + self.run_index
        return C.chat(*a, base_url=self.base_url, **k)


def _check_thinking_applied(model_url, engine, thinking):
    """Was the requested thinking mode actually applied? `off` travels as a chat-template
    argument (`config.thinking_body`), and a template without that switch ignores it silently:
    the row then says `think: off` while the model reasons (LFM2.5-24B-A2B, 2026-10-14: its
    template always opens a <think> block, the model spent 1615 tokens of a 512-token agent
    turn reasoning and answered empty — the run looked like a weak model instead of a broken
    measurement). Read-only check against `/props`: the template must mention the switch.
    Returns (True/False/None, note): None = could not tell (no template exposed, engine
    unknown), never a claim."""
    if thinking != "off":
        return None, None
    try:
        with urllib.request.urlopen(f"{model_url}/props", timeout=5) as r:  # pragma: no cover
            props = json.loads(r.read().decode("utf-8", "replace"))
    except (OSError, ValueError):
        return None, "could not read /props to verify the off switch"
    tpl = props.get("chat_template") or ""
    if not tpl:
        return None, "server exposes no chat template to verify the off switch"
    if "enable_thinking" in tpl:
        return True, None
    return False, ("chat template has no `enable_thinking` switch: the off request was ignored, "
                   "the model may reason anyway (MILLORA §C13)")


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
               level=None, thinking=None, runs=1, context_mode="fixed",
               tools_max_tokens=None, agent_max_tokens=None):
    if thinking is None:
        thinking = config.THINKING_DEFAULT
    # C5: hardware/OS snapshot captured once per model run, before anything else.
    env = _probe_environment()
    # D1: the context is resolved once, before the server starts (an `adapted` run
    # without its audit stops here instead of booting a server for nothing), and the
    # same values are what build_args puts on the command line and what the receipt
    # records: the row says which number it was measured with.
    ctx, ctx_source = S.resolve_context_and_source(model_path, context_mode, engine=engine)
    sm = S.ServerManager(model_path, context_mode=context_mode, port=port, engine=engine,
                         thinking=thinking)
    mid = model_id(engine, model_path)
    slug = config.slug(mid)
    print(f"→ {slug}: starting server ({engine})...", file=sys.stderr, flush=True)
    print(f"  context: {ctx if ctx is not None else 'engine default'} ({ctx_source})",
          file=sys.stderr, flush=True)
    sm.start()
    if not sm.wait_ready():
        sm.stop(); return {"model": mid, "engine": engine, "serve_failed": True}
    try:
        model_url = f"http://127.0.0.1:{port}"
        # Thinking (R1 thinking_batches): `off` disables it in the body (same channel for
        # both engines); `on` leaves it free. The protocol (dims, tasks, prompts) is untouched.
        extra = config.thinking_body(engine, thinking)

        c = ClientWrapper(model_url, extra)
        times = warmup(c, model_url, n=3, extra=extra)
        applied, note = _check_thinking_applied(model_url, engine, thinking)
        result = {"model": mid, "engine": engine, "thinking": thinking,
                  "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                  "thinking_mode_applied": applied, "thinking_mode_note": note,
                  "context_mode": context_mode,
                  "ctx_resolved": ctx, "ctx_source": ctx_source,
                  "tasks_version": config.TASKS_VERSION,
                  "server_build": _server_build(engine), "warmup_times": times,
                  "model_config_flags": S.describe_config(model_path, engine=engine),
                  "environment": env}
        lf = set(lang_filter) if lang_filter else None
        # C8 wall clock: the measured phase only (server boot and warmup are
        # setup, not the benchmark). Per-dimension too, so a mode comparison
        # shows where the extra time goes (e.g. thinking inside code/agent).
        t0 = time.monotonic()
        if "speed" in dims:
            t = time.monotonic()
            result["speed"] = G.grade_speed(c, _limit(T.load("speed"), quick), on_task=_print_task)
            result["speed"]["wall_time_s"] = round(time.monotonic() - t, 1)
        if "tools" in dims:
            t = time.monotonic()
            result["tools"] = G.grade_tools(c, _limit(T.load("tools"), quick), on_task=_print_task,
                                            runs=runs, max_tokens=tools_max_tokens)
            result["tools"]["wall_time_s"] = round(time.monotonic() - t, 1)
        if "code" in dims:
            code_tasks = _limit(T.load("code", lang_filter=lf, level=level), quick)
            if level and not code_tasks:
                print(f"⚠️  no code task at level={level}", file=sys.stderr, flush=True)
            t = time.monotonic()
            result["code"] = G.grade_code(c, code_tasks,
                                          on_task=_print_task, model_slug=slug,
                                          gen_tps=result["speed"]["gen_tps"] if "speed" in result else None,
                                          thinking=thinking, runs=runs)
            result["code"]["wall_time_s"] = round(time.monotonic() - t, 1)
        if "agent" in dims:
            t = time.monotonic()
            result["agent"] = G.grade_agent(c, _limit(T.load("agent", lang_filter=lf), quick),
                                            on_task=_print_task, runs=runs,
                                            max_tokens=agent_max_tokens)
            result["agent"]["wall_time_s"] = round(time.monotonic() - t, 1)
        result["wall_time_s"] = round(time.monotonic() - t0, 1)
        return result
    finally:
        sm.stop()


def _limit(tasks, quick):
    """--quick: only the first task of each dimension (harness smoke test)."""
    return tasks[:1] if quick else tasks

def _server_build(engine="llama"):
    """Engine version: llama-server's for 'llama'; Strata's is read from
    strata/engine/BUILD.json (version of the compiled executable); bmoe-server
    prints its own to stdout."""
    if engine == "bmoe":
        try:
            out = subprocess.run([str(config.BMOE_SERVER_BIN), "--version"],
                                 capture_output=True, text=True, timeout=10)
            return (out.stdout + out.stderr).strip().splitlines()[0]
        except (OSError, subprocess.TimeoutExpired, IndexError):
            return "unknown"
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
        # The commit is part of the identity: two rebuilds can share the version
        # ("0.4.0-dev") while differing in behavior — receipts must tell them apart.
        for line in (out.stdout + out.stderr).splitlines():
            if line.startswith("version:"):
                ver = line.split()[1]
                m = re.search(r"commit ([0-9a-f]{7,40})", line)
                return f"{ver}+{m.group(1)[:7]}" if m else ver
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
    ap.add_argument("--context", default="fixed", choices=["fixed", "adapted"],
                    help=f"server context, only when the model profile does not pin -c "
                         f"(a pinned -c always wins): fixed = {config.CONTEXT_FIXED} for "
                         f"everyone (default, same KV -> comparable speeds); adapted = the "
                         f"audited ctx_max in {config.AUDIT_FILE} — without the audit the "
                         f"run raises (run harness/tools/context-audit.py first). "
                         f"Whatever is used is recorded in every row (ctx_resolved, "
                         f"ctx_source).")
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
    def _valid_runs(v):
        n = int(v)
        if n < 1:
            raise argparse.ArgumentTypeError(f"runs must be >= 1, got {n}")
        return n
    ap.add_argument("--runs", type=_valid_runs, default=1, metavar="N",
                    help="repeat each task N times and aggregate results (default: 1)")
    ap.add_argument("--tools-max-tokens", type=int, default=config.TOOLS_MAX_TOKENS, metavar="N",
                    help="max tokens per tool-call request (a condition: recorded in the row)")
    ap.add_argument("--agent-max-tokens", type=int, default=config.AGENT_MAX_TOKENS, metavar="N",
                    help="max tokens per agent turn (a condition: recorded in the row)")
    ap.add_argument("-v", "--verbose", action="store_true",
                   help="granularity: Table 1 + per-language (Table 2); does NOT include tasks")
    ap.add_argument("--task", action="store_true",
                   help="per-task detail (Table 3): shows where each model succeeds/fails; composes with --verbose")
    ap.add_argument("--info", action="store_true",
                   help="Table 1 + Table 3 (per-task detail)")
    ap.add_argument("--scoreboard", action="store_true")
    ap.add_argument("--sort", choices=R.SORTS, default="global", metavar="KEY",
                    help="scoreboard ordering: global (default) | tools | code | agent | "
                         "speed | version (grouped by task set; see MILLORA §C9)")
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


def _write_html_report(pool=None, sort="global"):
    """--html: regenerate the HTML report from the accumulated pool (the same
    source --scoreboard reads, not just this run's rows). One line of feedback on
    stderr either way, so --json keeps stdout parseable. `sort` is only the ordering
    the static ranking (and the no-JS fallback) uses: the page's own control reorders
    it client-side."""
    out = html_report.write_default_report(pool, sort=sort)
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
        print(R.render(pool, weights, title="Scoreboard", level=level, show_tasks=args.task,
                       sort=args.sort))
        # --scoreboard --html = "refresh everything": read-only render + report
        # regenerated from the same accumulated pool.
        if args.html:
            _write_html_report(pool, sort=args.sort)
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
                             engine=args.engine, level=level, thinking=args.thinking,
                             runs=args.runs, context_mode=args.context,
                             tools_max_tokens=args.tools_max_tokens,
                             agent_max_tokens=args.agent_max_tokens)
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