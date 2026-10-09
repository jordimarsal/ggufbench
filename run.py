import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

from . import config, server as S, client as C, graders as G, tasks_loader as T, report as R


def parse_weights(s):
    if not s:
        return dict(config.WEIGHTS)
    w = {}
    for part in s.split(","):
        k, v = part.split("=")
        w[k.strip()] = float(v)
    return w


def resolve_models(spec, engine="llama"):
    """all -> glob del directori de models. Altrament, cada item (separat per
    comes) pot ser:
      - un camí existent (s'usa tal qual),
      - un nom de fitxer curt o parcial ('Ornith-...APEX-MTP-Quality[.gguf]'),
        que es resol contra models/*.gguf (mateix esperit que --forget);
        si coincideix amb més d'un fitxer, s'avisa i s'ignora (ambigu),
      - un camí inexistent: passa tal qual i llama-server en donarà l'error.

    Amb ``engine='strata'`` el 'model' és un config: 'iq3_xxs' ->
    Strata/strata-iq3_xxs.json (i 'all' = tots els strata-*.json)."""
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
            print(f"⚠️  '{item}' és ambigu ({names}); cap coincidència única, s'ignora",
                  file=sys.stderr, flush=True)
        else:
            resolved.append(item)
    return resolved


def _resolve_strata_models(spec):
    """Resol l'especificació de models d'Strata contra STRATA_DIR. Accepta 'all',
    el nom curt ('iq3_xxs'), el nom del fitxer ('strata-iq3_xxs[.json]') o un camí
    complet. Sense cap coincidència passa tal qual (server.py en donarà l'error)."""
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
    """Identificador del model al pool (i per al slug del marcador): el camí .gguf
    tal qual per a llama-server; per a Strata, el nom del config sense extensió
    ('strata-iq3_xxs') — que és el que identifica model + pack + configuració."""
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
        print(f"  {dim:5} {lang:11} {tid:20} {info.get('ms', 0)}ms  {info.get('gen_tps', 0)} t/s",
              file=sys.stderr, flush=True)
        return
    mark = "✓" if info.get("passed") else "✗"
    if info.get("excluded"):
        mark = "⊘"  # truncament/format o error de servidor: no compta al score
    if dim == "agent":
        extra = f"turns={info.get('turns', 0)}"
    else:
        extra = " ".join(str(info.get("detail") or "").split())[:60]
    print(f"  {dim:5} {lang:11} {tid:20} {mark} {extra}",
          file=sys.stderr, flush=True)


def _level_for_code(dims, level):
    """--level només afecta la dimensió code; si code no hi és, avisa i el descarta."""
    if not level:
        return None
    if "code" not in dims:
        print(f"⚠️  --level {level}: code no és a --dims, s'ignora",
              file=sys.stderr, flush=True)
        return None
    return level


def _bench_one(model_path, pool, dims, lang_filter, port, quick=False, engine="llama",
               level=None):
    sm = S.ServerManager(model_path, context_mode="fixed", port=port, engine=engine)
    mid = model_id(engine, model_path)
    slug = config.slug(mid)
    print(f"→ {slug}: arrencant servidor ({engine})...", file=sys.stderr, flush=True)
    sm.start()
    if not sm.wait_ready():
        sm.stop(); return {"model": mid, "engine": engine, "serve_failed": True}
    try:
        model_url = f"http://127.0.0.1:{port}"
        # Strata: sense aquest cos, el model pensa (HIGH) i amb els max_tokens petits
        # de les tasques no arriba a respondre (config.STRATA_EXTRA_BODY).
        extra = config.STRATA_EXTRA_BODY if engine == "strata" else None

        class ClientWrapper:
            def __init__(self, base_url, extra=None):
                self.base_url, self.extra = base_url, extra

            def chat(self, *a, **k):
                if self.extra:
                    k.setdefault("extra", self.extra)
                return C.chat(*a, base_url=self.base_url, **k)
        c = ClientWrapper(model_url, extra)
        times = warmup(c, model_url, n=3, extra=extra)
        result = {"model": mid, "engine": engine,
                  "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                  "context_mode": "fixed", "tasks_version": config.TASKS_VERSION,
                  "server_build": _server_build(engine), "warmup_times": times,
                  "model_config_flags": S.describe_config(model_path, engine=engine)}
        lf = set(lang_filter) if lang_filter else None
        if "speed" in dims:
            result["speed"] = G.grade_speed(c, _limit(T.load("speed"), quick), on_task=_print_task)
        if "tools" in dims:
            result["tools"] = G.grade_tools(c, _limit(T.load("tools"), quick), on_task=_print_task)
        if "code" in dims:
            code_tasks = _limit(T.load("code", lang_filter=lf, level=level), quick)
            if level and not code_tasks:
                print(f"⚠️  cap tasca code level={level}", file=sys.stderr, flush=True)
            result["code"] = G.grade_code(c, code_tasks,
                                          on_task=_print_task, model_slug=slug,
                                          gen_tps=result["speed"]["gen_tps"] if "speed" in result else None)
        if "agent" in dims:
            result["agent"] = G.grade_agent(c, _limit(T.load("agent", lang_filter=lf), quick), on_task=_print_task)
        return result
    finally:
        sm.stop()


def _limit(tasks, quick):
    """--quick: només la primera tasca de cada dimensió (smoke test del harness)."""
    return tasks[:1] if quick else tasks

def _server_build(engine="llama"):
    """Versió del motor: la de llama-server per a 'llama'; la de Strata la llegeix
    d'strata/engine/BUILD.json (versió de l'executable compilat)."""
    if engine == "strata":
        try:
            return str(json.loads((config.STRATA_DIR / "engine" / "BUILD.json")
                                  .read_text(encoding="utf-8"))["version"])
        except (OSError, ValueError, KeyError):
            return "unknown"
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
    ap.add_argument("--models", default="all",
                    help="all | camí .gguf | nom (curt o parcial) — separats per comes "
                         "(amb --engine strata: all | nom del config, ex. iq3_xxs)")
    ap.add_argument("--engine", choices=list(S.ENGINES), default="llama",
                    help="motor que serveix el model: llama = llama-server (default); "
                         "strata = serve/server.py amb un config strata-<model>.json")
    ap.add_argument("--context", default="fixed", choices=["fixed", "adapted"])
    ap.add_argument("--dims", default="speed,tools,code,agent")
    ap.add_argument("--lang", default=None)
    ap.add_argument("--level", choices=["easy", "hard"], default=None,
                    help="filtra NOMÉS les tasques de code per nivell (sufix _hard a l'ID)")
    ap.add_argument("--quick", action="store_true",
                    help="1 tasca per dimensió (smoke test del harness)")
    ap.add_argument("-v", "--verbose", action="store_true",
                   help="granularitat: Taula 1 + per-llenguatge (Taula 2); NO inclou tasques")
    ap.add_argument("--task", action="store_true",
                   help="detall de tasca (Taula 3): mostra on acerta/falla cada model; es composa amb --verbose")
    ap.add_argument("--info", action="store_true",
                   help="Taula 1 + Taula 3 (detall de tasca)")
    ap.add_argument("--scoreboard", action="store_true")
    ap.add_argument("--forget")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--port", type=int, default=None,
                    help=f"default {config.PORT} (llama) / {config.STRATA_PORT} (strata)")
    ap.add_argument("--weights", default=None)
    args = ap.parse_args(argv)
    weights = parse_weights(args.weights)
    port = args.port or (config.STRATA_PORT if args.engine == "strata" else config.PORT)
    # Granularitat: --verbose afegix la Taula 2 (per-llenguatge); --task l'afegiment del
    # detall de tasques (Taula 3). Són independents i es poden combinar (--verbose +
    # --task = Taula 1 + Taula 2 + Taula 3).
    level = "verbose" if args.verbose else ("info" if args.info else "default")

    if args.forget:
        removed = R.forget(args.forget)
        if removed:
            print(f"esborrat {removed} model(s) del pool", file=sys.stderr, flush=True)
        else:
            print(f"no s'ha trobat cap model coincident amb '{args.forget}'",
                  file=sys.stderr, flush=True)
        return
    if args.scoreboard:
        pool = R.load_pool()
        print(R.render(pool, weights, title="Scoreboard", level=level, show_tasks=args.task))
        return

    dims = [d.strip() for d in args.dims.split(",") if d.strip()]
    lang_filter = args.lang.split(",") if args.lang else None
    level = _level_for_code(dims, args.level)
    models = resolve_models(args.models, engine=args.engine)
    if not models:
        print("cap model a executar (revisa --models)", file=sys.stderr, flush=True)
        return
    for mp in models:
        try:
            res = _bench_one(mp, [], dims, lang_filter, port, quick=args.quick,
                             engine=args.engine, level=level)
            if res.get("serve_failed"):
                print(f"✗ {mp}: no carrega", file=sys.stderr, flush=True); continue
            R.save_result(res)
            slug = config.slug(model_id(args.engine, mp))
            speed = res.get("speed", {}).get("speed_ms", 0)
            gen_tps = res.get("speed", {}).get("gen_tps", 0)
            tools = res.get("tools", {}).get("score", 0)
            code = res.get("code", {}).get("score", 0)
            code_excl = res.get("code", {}).get("excluded", 0)
            agent = res.get("agent", {}).get("score", 0)
            code_lbl = f"{code:.2f}" + (f" ({code_excl} excloses)" if code_excl else "")
            print(f"✓ {slug}: speed={speed}ms ({gen_tps} t/s) "
                  f"tools={tools:.2f} code={code_lbl} agent={agent:.2f}",
                  file=sys.stderr, flush=True)
        except Exception as e:
            # Xarxa de seguretat del batch: aïlla la fallada d'un model per no tomba tota la run.
            print(f"✗ {mp}: {e}", file=sys.stderr, flush=True)
    pool = R.load_pool()
    if args.json:
        print(json.dumps(pool, indent=2, ensure_ascii=False))
    else:
        print(R.render(pool, weights, title="Benchmark Results", level=level, show_tasks=args.task))

if __name__ == "__main__":
    main()