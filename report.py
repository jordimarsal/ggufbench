import json
import datetime

from . import config

POOL_FILE = config.RESULTS_MODELS / "pool.jsonl"


def _slug_of(result):
    return config.slug(result["model"])


def save_result(result):
    config.RESULTS_MODELS.mkdir(parents=True, exist_ok=True)
    config.RESULTS_RUNS.mkdir(parents=True, exist_ok=True)
    slug = _slug_of(result)
    # Upsert per slug: reescriu pool.jsonl substituint l'entrada prèvia d'aquest model
    # (abans era append-only i re-executar inflava el scoreboard amb duplicats).
    pool = [r for r in load_pool() if _slug_of(r) != slug]
    pool.append(result)
    with open(POOL_FILE, "w") as f:
        for r in pool:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    (config.RESULTS_RUNS / f"{ts}-{slug}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))


def load_pool():
    if not POOL_FILE.exists():
        return []
    pool = []
    with open(POOL_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                pool.append(json.loads(line))
    return pool


def forget(model_name):
    if not POOL_FILE.exists():
        return
    pool = load_pool()
    slug = config.slug(model_name)
    pool = [r for r in pool if config.slug(r["model"]) != slug]
    with open(POOL_FILE, "w") as f:
        for r in pool:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _scores(r):
    """Score 0..1 per dimensió d'un model. Falta una dimensió (run parcial) -> 0."""
    sp = r.get("speed") or {}
    return {
        "tools": (r.get("tools") or {}).get("score", 0),
        "code": (r.get("code") or {}).get("score", 0),
        "agent": (r.get("agent") or {}).get("score", 0),
        "speed_ms": sp.get("speed_ms", 0),
        "gen_tps": sp.get("gen_tps", 0),
        "prompt_tps": sp.get("prompt_tps", 0),
    }


def _global_score(r, weights, min_speed):
    """Suma ponderada 0..1. Velocitat normalitzada: el model més ràpid (menys ms) -> 1.0."""
    sc = _scores(r)
    speed_score = (min_speed / sc["speed_ms"]) if (sc["speed_ms"] and min_speed) else 0
    parts = {"tools": sc["tools"], "code": sc["code"],
             "agent": sc["agent"], "speed": speed_score}
    total_w = sum(weights.values()) or 1.0
    return sum(parts.get(k, 0) * w for k, w in weights.items()) / total_w


def lang_profile(pool, lang):
    prof = {"speed": {}, "tools": {}, "code": {}, "agent": {}}
    for r in pool:
        for dim in ["code", "agent"]:
            bl = r.get(dim, {}).get("by_lang", {})
            if lang in bl:
                prof[dim][lang] = bl[lang]
    return prof


def render(pool, weights, title="Benchmark Results"):
    """Marcador per model (SPEC, Taula 1): una fila per model amb el score de cada
    dimensió i un global ponderat, ordenat de millor a pitjor."""
    if not pool:
        return "(no results in pool)"
    speed_values = [(r.get("speed") or {}).get("speed_ms", 0) for r in pool]
    min_speed = min((v for v in speed_values if v > 0), default=0)
    rows = []
    for r in pool:
        sc = _scores(r)
        rows.append((config.slug(r["model"]), sc, _global_score(r, weights, min_speed)))
    rows.sort(key=lambda x: x[2], reverse=True)
    out = [f"=== {title} ===",
           f"{'MODEL':40} {'tools':>6} {'code':>6} {'agent':>6} {'speed':>9} {'GLOBAL':>7}",
           "-" * 74]
    for name, sc, g in rows:
        sp = f"{sc['speed_ms']}ms" if sc["speed_ms"] else "—"
        out.append(f"{name:40.40} {sc['tools']:>5.0%} {sc['code']:>5.0%} "
                   f"{sc['agent']:>5.0%} {sp:>9} {g:>7.2f}")
    # Epígraf de tokens per segon (output i input).
    out.append("")
    out.append("=== Tokens per segon (t/s) ===")
    out.append(f"{'MODEL':40} {'gen (out)':>10} {'prompt (in)':>12}")
    out.append("-" * 64)
    for name, sc, g in rows:
        gen = f"{sc['gen_tps']:.1f}" if sc["gen_tps"] else "—"
        prom = f"{sc['prompt_tps']:.1f}" if sc["prompt_tps"] else "—"
        out.append(f"{name:40.40} {gen:>10} {prom:>12}")
    return "\n".join(out)
