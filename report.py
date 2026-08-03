import json, datetime
from pathlib import Path
from . import config

POOL_FILE = config.RESULTS_MODELS / "pool.jsonl"

def _slug_of(result):
    return config.slug(result["model"])

def save_result(result):
    config.RESULTS_MODELS.mkdir(parents=True, exist_ok=True)
    config.RESULTS_RUNS.mkdir(parents=True, exist_ok=True)
    with open(POOL_FILE, "a") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")
    slug = _slug_of(result)
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

def compute_global(pool, dims):
    stats = {d: {"total": 0, "passed": 0, "count": 0, "speed_ms": 0} for d in dims}
    for r in pool:
        for d in dims:
            stats[d]["total"] += 1
            if d == "speed":
                ms = r.get(d, {}).get("speed_ms")
                if ms:
                    stats[d]["speed_ms"] += ms
                    stats[d]["passed"] += 1
            else:
                dim_data = r.get(d, {})
                if not isinstance(dim_data, dict):
                    continue
                if dim_data.get("passed"):
                    stats[d]["passed"] += 1
                tasks = dim_data.get("trace", [])
                stats[d]["count"] += len(tasks)
    for d in dims:
        if stats[d]["total"] > 0:
            stats[d]["passed"] = stats[d]["passed"] / stats[d]["total"]
            if stats[d]["speed_ms"] > 0:
                stats[d]["speed_ms"] = stats[d]["speed_ms"] / stats[d]["total"]
    return stats

def lang_profile(pool, lang):
    prof = {"speed": {}, "tools": {}, "code": {}, "agent": {}}
    for r in pool:
        for dim in ["code", "agent"]:
            bl = r.get(dim, {}).get("by_lang", {})
            if lang in bl:
                prof[dim][lang] = bl[lang]
    return prof

def render(pool, dims, title="Benchmark Results"):
    if not pool:
        return "(no results in pool)"
    stats = compute_global(pool, dims)
    out = []
    out.append(f"=== {title} ===")
    out.append(f"{'GLOBAL':12} {'TOTAL':>6} {'PASSED':>7} {'COUNT':>6} {'SPEED_MS':>10}")
    for d in dims:
        s = stats[d]
        out.append(f"{d:12} {s['total']:>6} {s['passed']:>6.1%} {s['count']:>6} {s['speed_ms']:>10.0f}")
    return "\n".join(out)