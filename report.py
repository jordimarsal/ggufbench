import json
import datetime
import os
from typing import Any

from . import config


def _slug_of(result):
    return config.slug(result["model"])


def _key_of(result):
    """Upsert key (R2 thinking_batches): (slug, thinking). Legacy rows without
    `thinking` key under (slug, None) and do not collide with (slug, 'off'). The slug
    alone still identifies the model (forget, visualization)."""
    return (_slug_of(result), result.get("thinking"))


def save_result(result):
    config.RESULTS_MODELS.mkdir(parents=True, exist_ok=True)
    config.RESULTS_RUNS.mkdir(parents=True, exist_ok=True)
    slug = _slug_of(result)
    key = _key_of(result)
    # Upsert per (slug, thinking): the two modes coexist; re-running the same mode
    # replaces it (it used to key on the slug alone, so the second batch would overlap the first).
    pool = [r for r in load_pool() if _key_of(r) != key]
    pool.append(result)
    with open(config.POOL_FILE, "w") as f:
        for r in pool:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    mode = result.get("thinking") or "na"
    (config.RESULTS_RUNS / f"{ts}-{slug}-{mode}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))


def load_pool():
    if not config.POOL_FILE.exists():
        return []
    # Dedup by (slug, thinking) keeping the last occurrence (the most recent one:
    # the file is chronological). Isolates duplicates inherited from the append-only era.
    by_key = {}
    with open(config.POOL_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            by_key[_key_of(r)] = r
    return list(by_key.values())


def _model_stem(model_field):
    """Model file name without path or extension (.gguf/.GGUF).
    'models/foo.gguf' -> 'foo'; 'foo' -> 'foo'. Robust against names with internal dots
    ('Qwen3.8', 'Ornith-1.5'): only the model's extension is stripped, never a dot from
    the name. Lets us identify the same model even though the 'model' field is stored as
    a relative or absolute path, and to forget it by the bare name."""
    base = os.path.basename(str(model_field))
    for ext in (".gguf", ".GGUF"):
        if base.endswith(ext):
            return base[:-len(ext)]
    return base


def _forget_matches(r, term):
    # Match by slug (as before) OR by file name, because the 'model' field may be stored
    # as a relative/absolute path while the user passes the bare name.
    return (config.slug(r["model"]) == config.slug(term)
            or _model_stem(r["model"]) == _model_stem(term))


def forget(model_name):
    """Deletes from the pool every entry matching ``model_name``.

    Returns the number of deleted entries (0 when there is no match), so the caller can
    report it honestly to the user. It used to return ``None`` and stay silent when
    nothing was found, which made the CLI falsely say "deleted"."""
    if not config.POOL_FILE.exists():
        return 0
    pool = load_pool()
    keep = [r for r in pool if not _forget_matches(r, model_name)]
    removed = len(pool) - len(keep)
    if removed:
        with open(config.POOL_FILE, "w") as f:
            for r in keep:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return removed


def _scores(r: dict[str, Any]) -> dict[str, float]:
    """Score 0..1 per dimension of a model. A missing dimension (partial run) -> 0."""
    sp = r.get("speed") or {}
    return {
        "tools": (r.get("tools") or {}).get("score", 0),
        "code": (r.get("code") or {}).get("score", 0),
        "agent": (r.get("agent") or {}).get("score", 0),
        "speed_ms": sp.get("speed_ms", 0),
        "gen_tps": sp.get("gen_tps", 0),
        "prompt_tps": sp.get("prompt_tps", 0),
    }


def _global_score(r: dict[str, Any], weights: dict[str, float],
                  min_speed: float) -> float:
    """Weighted sum 0..1. Normalized speed: the fastest model (fewest ms) -> 1.0."""
    sc = _scores(r)
    speed_score = (min_speed / sc["speed_ms"]) if (sc["speed_ms"] and min_speed) else 0
    parts = {"tools": sc["tools"], "code": sc["code"],
             "agent": sc["agent"], "speed": speed_score}
    total_w = sum(weights.values()) or 1.0
    return sum(parts.get(k, 0) * w for k, w in weights.items()) / total_w


def lang_profile(pool, lang):
    prof: dict[str, dict[str, Any]] = {"speed": {}, "tools": {}, "code": {}, "agent": {}}
    for r in pool:
        for dim in ["code", "agent"]:
            bl = r.get(dim, {}).get("by_lang", {})
            if lang in bl:
                prof[dim][lang] = bl[lang]
    return prof


def _fmt_pct(x):
    """Formats a percentage (0..1 -> %) or '—' when there is no data."""
    return f"{x:.0%}" if x is not None else "—"


def _think_mark(result):
    """Mode marker (R4 thinking_batches): 'on'/'off'/'—' (legacy rows without key)."""
    return result.get("thinking") or "—"


def _render_global_rows(pool, weights, title):
    """Table 1 + tokens section (SPEC 4.6). One row per model with the score of each
    dimension and a weighted global, sorted from best to worst."""
    # Coerce None -> 0 so a model without speed (partial run) does not break the render.
    speed_values = [int((r.get("speed") or {}).get("speed_ms") or 0) for r in pool]
    min_speed = min((v for v in speed_values if v > 0), default=0)
    rows = []
    for r in pool:
        sc = _scores(r)
        excl = int((r.get("code") or {}).get("excluded") or 0)
        rows.append((config.slug(r["model"]), _think_mark(r), excl, sc,
                     _global_score(r, weights, min_speed)))
    rows.sort(key=lambda x: x[4], reverse=True)
    nw = max((len(r[0]) for r in rows), default=5)
    header = f"{'MODEL':{nw}} {'THINK':>5} {'tools':>6} {'code':>13} {'agent':>6} {'speed':>9} {'GLOBAL':>7}"
    out = [f"=== {title} ===", header, "-" * len(header)]
    for name, mode, excl, sc, g in rows:
        sp = f"{sc['speed_ms']}ms" if sc["speed_ms"] else "—"
        code = f"{sc['code']:>5.0%}" + (f" ({excl} excl.)" if excl else "")
        out.append(f"{name:{nw}} {mode:>5} {sc['tools']:>5.0%} {code:>13} "
                   f"{sc['agent']:>5.0%} {sp:>9} {g:>7.2f}")
    # Tokens-per-second heading (output and input).
    out.append("")
    out.append("=== Tokens per second (t/s) ===")
    theader = f"{'MODEL':{nw}} {'gen (out)':>10} {'prompt (in)':>12}"
    out.append(theader)
    out.append("-" * len(theader))
    for name, _mode, _excl, sc, _g in rows:
        gen = f"{sc['gen_tps']:.1f}" if sc["gen_tps"] else "—"
        prom = f"{sc['prompt_tps']:.1f}" if sc["prompt_tps"] else "—"
        out.append(f"{name:40.40} {gen:>10} {prom:>12}")
    return out


def _render_tasks(pool):
    """Table 3 — per-task detail (SPEC 4.6). One row per (model, dimension, task).
    Tolerant: a model without a dimension or a dimension without a trace does not fail."""
    nw = max((len(config.slug(r["model"])) for r in pool), default=5)
    header = f"{'MODEL':{nw}} {'THINK':>5} {'DIM':8} {'LANG':12} {'TASK':20} {'OK':4} DETAIL"
    out = ["", "=== Per-task detail ===", header, "-" * len(header)]
    for r in pool:
        name = config.slug(r["model"])
        mode = _think_mark(r)
        for dim in ("tools", "code", "agent"):
            d = r.get(dim) or {}
            for t in d.get("trace") or []:
                lang = str(t.get("lang") or "—")[:11]
                tid = str(t.get("id") or "")[:20]
                mark = "✓" if t.get("passed") else "✗"
                detail = " ".join(str(t.get("detail") or "").split())[:30]
                if t.get("excluded"):
                    detail += " [excluded]"
                out.append(f"{name:40.40} {mode:>5} {dim:8} {lang:12} {tid:20} {mark} {detail}")
    return out


def _render_by_lang(pool):
    """Table 2 — per-language breakdown of code/agent (SPEC 4.6). Cell '—' when that
    language has no tasks for that dimension."""
    langs = ["python", "bash", "java", "typescript"]
    dims = ["code", "agent"]
    nw = max((len(config.slug(r["model"])) for r in pool), default=5)
    header = f"{'MODEL':{nw}} {'THINK':>5}"
    for dim in dims:
        for lang in langs:
            header += f" {dim}:{lang:>11}"
    out = ["", "=== By language (code/agent) ===", header, "-" * len(header)]
    for r in pool:
        name = config.slug(r["model"])
        row = f"{name:{nw}} {_think_mark(r):>5}"
        for dim in dims:
            bl = (r.get(dim) or {}).get("by_lang") or {}
            for lang in langs:
                row += f" {_fmt_pct(bl.get(lang)):>11}"
        out.append(row)
    return out


def render(pool, weights, title="Benchmark Results", level="default", show_tasks=False):
    """Scoreboard per model with granularity decomposed into independent axes (SPEC 4.6):

    - ``level='default'`` : Table 1 (global scores) + tokens section.
    - ``level='info'``    : Table 1 + Table 3 (per-task detail). Answers "what is a
      model good/bad at".
    - ``level='verbose'`` : Table 1 + Table 2 (per language). Does NOT include the task
      detail; it is the finest level without per-task.

    The task detail (Table 3) is shown when `show_tasks=True` (via `--task`) or when the
    level already includes it (`info`). That way `--verbose` never shows it on its own
    and `--task` is needed to see it; the two options compose: `--verbose` (per-language)
    can be used together with `--task`. Dimensions or tasks missing from a model (partial
    runs, models that do not yet have this granularity) cause no errors: every cell is
    computed with default values."""
    if not pool:
        return "(no results in pool)"
    out = _render_global_rows(pool, weights, title)
    if level == "verbose":
        out += _render_by_lang(pool)
    if show_tasks or level == "info":
        out += _render_tasks(pool)
    return "\n".join(out)
