import hashlib
import json
import datetime
import os
import statistics
from typing import Any

from . import config


def task_signature(result):
    """Task set a result was measured with: the graded counts per dimension
    ('tools/code/agent', e.g. '16/60/60'), from the recorded field or derived from the
    traces ('?' for a dimension that was not measured).

    The suite version (config.TASKS_VERSION) is a label and cannot describe the set: v3
    covered four different counts because the C3 additions never bumped it, so two rows
    could share a version and still be incomparable. The signature comes from the data,
    which is why the scoreboard and the compare page compare signatures."""
    stored = result.get("task_signature")
    if stored:
        return str(stored)
    counts = (len((result.get(d) or {}).get("trace") or [])
              for d in ("tools", "code", "agent"))
    return "/".join(str(n) if n else "?" for n in counts)


def signature_counts(pool):
    """{task_signature: number of rows}, most frequent first. More than one entry means
    the pool mixes task sets — the drift the report must announce instead of hiding."""
    counts: dict[str, int] = {}
    for r in pool:
        sig = task_signature(r)
        counts[sig] = counts.get(sig, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def baseline_flags() -> str:
    """The baseline a row is measured under, as text: the harness' common flags
    (`config.baseline_argv()` = SERVER_FLAGS + CACHE_FLAGS) — never the per-model profile,
    which is already recorded as `model_config_flags`. It is a CONDITION (§C10): ADR-0008
    switched the KV cache q4_0 -> q8_0, so rows measured before it are not comparable with
    rows measured after, and nothing else in the data says so."""
    return " ".join(config.baseline_argv())


def baseline_id(row) -> str:
    """Short id of the baseline recorded in a row (the flags themselves live in config; the
    id is what the board prints). '?' when the row predates the field: the baseline was
    never recorded, and inventing one would turn an unknown condition into a
    seemingly known one."""
    flags = row.get("baseline_flags")
    if not isinstance(flags, str) or not flags:
        return "?"
    return hashlib.sha1(flags.encode("utf-8")).hexdigest()[:8]


def _engine_label(row) -> str:
    """Engine and build as ONE value: the pair is the condition (a build change is what
    makes two rows incomparable), and the engine name alone would hide it."""
    return f"{row.get('engine') or 'llama'} {row.get('server_build') or '?'}"


# The condition axes the board compares, in a fixed order — every note lists them in this
# one order. A row carries all four (`task_signature`, `engine` + `server_build`,
# `baseline_flags`, the per-call caps): §C10 is the §C9 rule applied to the axes §C9 did
# not cover. The caps joined the list on 2026-10-15, when the ON batch was raised to
# 512/4096 and gemma had already been measured at 256/2048 — a difference a reader must
# see, because a row clipped by a small cap looks exactly like a weak model.
CONDITION_AXES = ("task set", "engine", "baseline", "caps")


def caps_label(row) -> str:
    """The per-call token caps a row was measured with: tool calls and agent turns. '?' for
    rows that predate the fields (the OFF runs of the v5 pass kept the harness defaults, so
    an ON row with raised caps is a different condition, not a better model)."""
    t = ((row.get("tools") or {}).get("tools_max_tokens")) or "?"
    a = ((row.get("agent") or {}).get("agent_max_tokens")) or "?"
    if t == "?" and a == "?":
        return "?"
    return f"tools {t}/agent {a}"


def condition_axes(pool) -> dict[str, dict[str, int]]:
    """axis -> {value: number of rows}, axes in CONDITION_AXES order and values most
    frequent first (the same spirit as `signature_counts`). An axis with more than one
    value is a condition the pool mixes."""
    axes: dict[str, dict[str, int]] = {axis: {} for axis in CONDITION_AXES}
    for r in pool:
        values = (task_signature(r), _engine_label(r), baseline_id(r), caps_label(r))
        for axis, value in zip(CONDITION_AXES, values):
            counts = axes[axis]
            counts[value] = counts.get(value, 0) + 1
    return {axis: dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))
            for axis, counts in axes.items()}


def mixed_axes(pool) -> list[str]:
    """The axes with MORE THAN ONE value, in CONDITION_AXES order. [] means the pool is
    homogeneous: every row was measured under the same conditions, so the board can be
    read as one experiment and no note is needed."""
    return [axis for axis, values in condition_axes(pool).items() if len(values) > 1]


# Orderings the scoreboard accepts (--sort). 'version' is not a metric: it groups the
# pool by task set (biggest set first, global inside each group), which is how a reader
# avoids comparing scores that were not measured on the same tasks.
SORTS = ("global", "tools", "code", "agent", "speed", "version")


def ordered_signatures(pool):
    """Task sets in the pool, biggest first — the order the board uses whenever it groups
    by set (--sort version, the report's "By task set" blocks, the chip and the notes that
    announce the mix). One order everywhere, so they agree."""
    return sorted(signature_counts(pool), key=lambda s: (-_set_size(s), s))


def _set_size(sig):
    """Graded task-runs in a signature: '16/60/60' -> 136. -1 when a dimension is not
    measured ('?'), so an incomplete row sorts last instead of pretending to be big."""
    try:
        parts = [int(p) for p in sig.split("/")]
    except ValueError:
        return -1
    return sum(parts) if all(p > 0 for p in parts) else -1


def sort_key(sort, weights, min_speed):
    """Key function for the scoreboard (ascending, so the best/informative comes first).
    Unknown keys fall back to 'global' — the caller validates, this never raises."""
    def key(r):
        sc = _scores(r)
        if sort == "version":
            return (-_set_size(task_signature(r)), -_global_score(r, weights, min_speed))
        if sort == "tools":
            return (-(sc["tools"] or 0), -_global_score(r, weights, min_speed))
        if sort == "code":
            return (-(sc["code"] or 0), -_global_score(r, weights, min_speed))
        if sort == "agent":
            return (-(sc["agent"] or 0), -_global_score(r, weights, min_speed))
        if sort == "speed":
            return (sc["speed_ms"] or 1e9, -_global_score(r, weights, min_speed))
        return (-_global_score(r, weights, min_speed),)
    return key


def set_label(row):
    """How a row states its test version: the recorded label plus the real task set
    ('v3·16/60/60'). Both are shown because they disagree exactly where it matters — the
    label collided across four sets (MILLORA §C9), and the signature is the condition."""
    return f"{row.get('tasks_version') or '?'}·{task_signature(row)}"


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


def _slug_of(result):
    return config.slug(result["model"])


def _key_of(result):
    """Upsert key (R2 thinking_batches): (model, thinking), the model identified by its
    file name — never by the shape of the path it was measured with. `--models` globs the
    models directory (absolute paths) while a hand-passed 'models/x.gguf' stays relative:
    a slug-only key kept one model twice in the pool (qwen36, 2026-10-13). Legacy rows
    without `thinking` key under (model, None) and do not collide with (model, 'off')."""
    return (config.slug(_model_stem(result["model"])), result.get("thinking"))


def save_result(result):
    config.RESULTS_MODELS.mkdir(parents=True, exist_ok=True)
    config.RESULTS_RUNS.mkdir(parents=True, exist_ok=True)
    # The task set the row was measured with travels with the row (§C9): the version
    # label alone let three different sets live under "v3".
    result.setdefault("task_signature", task_signature(result))
    # Same §C9/C10 idea for the baseline: the common flags are a condition too (ADR-0008
    # changed them mid-pool), and `model_config_flags` only records the per-model profile.
    result.setdefault("baseline_flags", baseline_flags())
    slug = _slug_of(result)
    key = _key_of(result)
    # Agent conversations ride out-of-band: the full episodes live in a sidecar
    # file next to the run receipt; the pool row stays lean with only a pointer.
    convos = (result.get("agent") or {}).pop("conversations", None)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    mode = result.get("thinking") or "na"
    if convos is not None:
        sidecar = config.RESULTS_RUNS / f"{ts}-{slug}-{mode}-agent-convos.json"
        sidecar.write_text(json.dumps(convos, ensure_ascii=False))
        result["agent"]["conversations_file"] = sidecar.name
    # Upsert per (slug, thinking): the two modes coexist; re-running the same mode
    # replaces it (it used to key on the slug alone, so the second batch would overlap the first).
    pool = [r for r in load_pool() if _key_of(r) != key]
    pool.append(result)
    with open(config.POOL_FILE, "w") as f:
        for r in pool:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
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


_QUALITY_DIMS = ("tools", "code", "agent")
# Base column widths of Table 1 (the widths today; a ± only widens them by its own).
_CELLS = {"tools": 5, "code": 13, "agent": 5, "global": 7}


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
    return _weighted_global(_score_parts(sc["tools"], sc["code"], sc["agent"],
                                         sc["speed_ms"], min_speed), weights)


def _score_parts(tools, code, agent, speed_ms, min_speed) -> dict[str, float]:
    """The four weighted inputs of a global. Speed is measured once per row, so a
    per-run index reuses the row's own normalized speed (same min_speed)."""
    return {"tools": tools, "code": code, "agent": agent,
            "speed": (min_speed / speed_ms) if (speed_ms and min_speed) else 0}


def _weighted_global(parts: dict[str, float], weights: dict[str, float]) -> float:
    total_w = sum(weights.values()) or 1.0
    return sum(parts.get(k, 0) * w for k, w in weights.items()) / total_w


def _row_runs(r) -> int:
    """Measurement runs recorded for a row: 1 when it predates --runs. Sections carry
    ``runs``: N (graders); a top-level key is accepted too."""
    vals = [1] + [int(r.get("runs") or 0)]
    for dim in _QUALITY_DIMS:
        vals.append(int((r.get(dim) or {}).get("runs") or 0))
    return max(vals)


def _run_scores(r):
    """{dim: [score per run index]} rebuilt from the trace ``runs`` lists ([1, 0, 'x']):
    per index, the mean over the tasks that were not excluded in that run. None where a
    run has no valid attempt. None when the row is not a multi-run measurement or no
    trace carries the per-run outcomes."""
    n = _row_runs(r)
    if n < 2:
        return None
    out: dict[str, list] = {}
    for dim in _QUALITY_DIMS:
        lists = [t["runs"] for t in (r.get(dim) or {}).get("trace") or []
                 if isinstance(t.get("runs"), list)]
        if not lists:
            continue
        per_run = []
        for i in range(n):
            attempts = [1 if t[i] == 1 else 0 for t in lists if len(t) > i and t[i] != "x"]
            per_run.append(statistics.mean(attempts) if attempts else None)
        out[dim] = per_run
    return out or None


def run_spread(r, weights: dict[str, float], min_speed: float):
    """Run-to-run spread (sample stddev) per dimension and for the weighted global —
    the ± of a mean ± spread cell (SPEC: aggregating repeated runs).

    None for single-run rows, which is every row of today's pool: they render exactly
    as before. A dimension needs at least two comparable run indexes to get its own
    spread; the global uses the per-index globals (same weights, same min_speed) and
    skips an index that is incomplete (a run with every task excluded)."""
    runs = _run_scores(r)
    if not runs:
        return None
    out: dict[str, float] = {}
    for dim, per_run in runs.items():
        vals = [v for v in per_run if v is not None]
        if len(vals) >= 2:
            out[dim] = statistics.stdev(vals)

    sc = _scores(r)
    base = _score_parts(sc["tools"], sc["code"], sc["agent"], sc["speed_ms"], min_speed)
    n = max((len(v) for v in runs.values()), default=0)
    globals_ = []
    for i in range(n):
        if any(len(v) > i and v[i] is None for v in runs.values()):
            continue
        parts = dict(base)
        for dim, per_run in runs.items():
            if len(per_run) > i:
                parts[dim] = per_run[i]
        globals_.append(_weighted_global(parts, weights))
    if len(globals_) >= 2:
        out["global"] = statistics.stdev(globals_)
    return out or None


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


def _spread_suffix(spread):
    """' ±9' — '' when the cell is a single-run measurement (the whole table renders
    as it did before). Spread is a 0..1 stddev; the cell shows it in points."""
    return "" if spread is None else f" ±{spread * 100:.0f}"


def _think_mark(result):
    """Mode marker (R4 thinking_batches): 'on'/'off'/'—' (legacy rows without key)."""
    return result.get("thinking") or "—"


# n=1: a quality gap within this margin is a tie for mode picking — the decision
# then rides on wall clock, which is structural (thinking tokens), not noise.
OPTIMAL_EPSILON = 0.02


def _mode_quality(r):
    """tools/code/agent weighted mean (speed excluded: wall_time_s already
    carries the cost side — counting speed here too would double-count it)."""
    q = sum((r.get(d) or {}).get("score", 0) * config.WEIGHTS.get(d, 0)
            for d in ("tools", "code", "agent"))
    w = sum(config.WEIGHTS.get(d, 0) for d in ("tools", "code", "agent")) or 1.0
    return q / w


def optimal_mode(model_rows):
    """'off'/'on' when one thinking mode dominates the other, else None.

    Dominance (C8) needs both rows to carry wall_time_s: quality (tools/code/
    agent, speed excluded) not worse by more than OPTIMAL_EPSILON AND wall
    clock not higher. Anything else (missing wall clock on either row, quality
    collapse beyond the margin even when faster) -> None: no invented winner.
    An exact tie resolves deterministically to 'off' (same result in the same
    time — no reason to pay for thinking tokens).
    """
    by = {r.get("thinking"): r for r in model_rows if r.get("thinking") in ("off", "on")}
    off, on = by.get("off"), by.get("on")
    if not off or not on:
        return None
    wall_off, wall_on = off.get("wall_time_s"), on.get("wall_time_s")
    if not wall_off or not wall_on:
        return None
    q_off, q_on = _mode_quality(off), _mode_quality(on)
    if wall_off <= wall_on and q_off >= q_on - OPTIMAL_EPSILON:
        return "off"
    if wall_on <= wall_off and q_on >= q_off - OPTIMAL_EPSILON:
        return "on"
    return None


def optimal_by_slug(pool):
    """{slug: 'off'|'on'} per model with a dominant thinking mode (see optimal_mode)."""
    by_model: dict[str, list[dict[str, Any]]] = {}
    for r in pool:
        by_model.setdefault(r.get("model"), []).append(r)
    out: dict[str, str] = {}
    for model, rs in by_model.items():
        mode = optimal_mode(rs)
        if mode:
            out[config.slug(model)] = mode
    return out


def _render_global_rows(pool, weights, title, sort="global"):
    """Table 1 + tokens section (SPEC 4.6). One row per model with the score of each
    dimension, its test version (`SET`: label·task-set) and a weighted global.

    `sort` (--sort, report.SORTS) orders the table: by the weighted global (default), by
    one dimension, or by task set — 'version' groups the pool by set so scores measured on
    different tasks are never interleaved (MILLORA §C9).

    A multi-run row (--runs N, traces carrying the per-run outcomes) shows its spread
    next to the mean: '83% ±29' and '0.84 ±26' (see run_spread). Single-run rows —
    every row of a pool measured without --runs — render exactly as before."""
    # Coerce None -> 0 so a model without speed (partial run) does not break the render.
    speed_values = [int((r.get("speed") or {}).get("speed_ms") or 0) for r in pool]
    min_speed = min((v for v in speed_values if v > 0), default=0)
    key = sort_key(sort if sort in SORTS else "global", weights, min_speed)
    rows = []
    for r in pool:
        sc = _scores(r)
        excl = int((r.get("code") or {}).get("excluded") or 0)
        spread = run_spread(r, weights, min_speed) or {}
        g = _global_score(r, weights, min_speed)
        # Base text exactly as before; the ± only rides on multi-run rows, and the
        # columns widen by the width of the ± so a mixed pool stays aligned.
        suffixes = {k: _spread_suffix(spread.get(k)) for k in _CELLS}
        cells = {"tools": f"{sc['tools']:>5.0%}" + suffixes["tools"],
                 "code": f"{sc['code']:>5.0%}" + suffixes["code"]
                         + (f" ({excl} excl.)" if excl else ""),
                 "agent": f"{sc['agent']:>5.0%}" + suffixes["agent"],
                 "global": f"{g:.2f}" + suffixes["global"]}
        rows.append({"name": config.slug(r["model"]), "mode": _think_mark(r), "excl": excl,
                     "sc": sc, "g": g, "cells": cells, "suffixes": suffixes,
                     "set": set_label(r), "key": key(r)})
    rows.sort(key=lambda row: row["key"])
    nw = max((len(row["name"]) for row in rows), default=5)
    sw = max([len("SET")] + [len(row["set"]) for row in rows])
    widths = dict(_CELLS)
    for row in rows:
        for k, sfx in row["suffixes"].items():
            widths[k] = max(widths[k], _CELLS[k] + len(sfx))
    optimal = optimal_by_slug(pool)
    header = (f"{'MODEL':{nw}} {'THINK':>5} {'SET':{sw}} {'tools':>{widths['tools'] + 1}} "
              f"{'code':>{widths['code']}} {'agent':>{widths['agent'] + 1}} "
              f"{'speed':>9} {'GLOBAL':>{widths['global']}}")
    out = [f"=== {title} ===", header, "-" * len(header)]
    for row in rows:
        sc = row["sc"]
        sp = f"{sc['speed_ms']}ms" if sc["speed_ms"] else "—"
        think = f"{row['mode']:>4} ★" if optimal.get(row["name"]) == row["mode"] else f"{row['mode']:>5}"
        out.append(f"{row['name']:{nw}} {think:>5} {row['set']:{sw}} "
                   f"{row['cells']['tools']:>{widths['tools']}} "
                   f"{row['cells']['code']:>{widths['code']}} "
                   f"{row['cells']['agent']:>{widths['agent']}} "
                   f"{sp:>9} {row['cells']['global']:>{widths['global']}}")
    # Tokens-per-second heading (output and input).
    out.append("")
    out.append("=== Tokens per second (t/s) ===")
    theader = f"{'MODEL':{nw}} {'gen (out)':>10} {'prompt (in)':>12}"
    out.append(theader)
    out.append("-" * len(theader))
    for row in rows:
        gen = f"{row['sc']['gen_tps']:.1f}" if row["sc"]["gen_tps"] else "—"
        prom = f"{row['sc']['prompt_tps']:.1f}" if row["sc"]["prompt_tps"] else "—"
        out.append(f"{row['name']:40.40} {gen:>10} {prom:>12}")
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


def render(pool, weights, title="Benchmark Results", level="default", show_tasks=False,
           sort="global"):
    """Scoreboard per model with granularity decomposed into independent axes (SPEC 4.6):

    - ``level='default'`` : Table 1 (global scores) + tokens section.
    - ``level='info'``    : Table 1 + Table 3 (per-task detail). Answers "what is a
      model good/bad at".
    - ``level='verbose'`` : Table 1 + Table 2 (per language). Does NOT include the task
      detail; it is the finest level without per-task.
    - ``sort``            : Table 1 ordering — ``global`` (default), a dimension
      (``tools``/``code``/``agent``/``speed``) or ``version`` (grouped by task set, so
      scores measured on different tasks are never interleaved; MILLORA §C9). Every row
      always shows its ``SET`` (label·task-set).

    The task detail (Table 3) is shown when `show_tasks=True` (via `--task`) or when the
    level already includes it (`info`). That way `--verbose` never shows it on its own
    and `--task` is needed to see it; the two options compose: `--verbose` (per-language)
    can be used together with `--task`. Dimensions or tasks missing from a model (partial
    runs, models that do not yet have this granularity) cause no errors: every cell is
    computed with default values."""
    if not pool:
        return "(no results in pool)"
    out = _render_global_rows(pool, weights, title, sort=sort)
    if level == "verbose":
        out += _render_by_lang(pool)
    if show_tasks or level == "info":
        out += _render_tasks(pool)
    out += _render_conditions(pool)
    return "\n".join(out)


def _render_conditions(pool):
    """Footer note (only when the pool mixes conditions): the version label cannot tell rows
    with different task counts apart, and the engine build and the baseline flags were never
    compared at all — so the scoreboard says it out loud instead of letting a 12-task 92%
    tools sit next to a 16-task 94% one, or a q4_0 row next to a q8_0 one, as if they were
    the same measurement (docs/MILLORA.md §C9/C10)."""
    axes = condition_axes(pool)
    mixed = [axis for axis in CONDITION_AXES if len(axes[axis]) > 1]
    if not mixed:
        return []
    width = max(len(axis) for axis in mixed)
    out = ["", "NOTE: this pool mixes conditions — a score is comparable only within one "
               "set (docs/MILLORA.md §C9/C10)"]
    for axis in mixed:
        counts = axes[axis]
        # One order everywhere: task sets biggest first (ordered_signatures, the same order
        # the --sort version grouping and the report blocks use); the other axes most
        # frequent first.
        values = ordered_signatures(pool) if axis == "task set" else list(counts)
        suffix = " tasks" if axis == "task set" else ""
        for i, value in enumerate(values):
            n = counts[value]
            out.append(f"  {axis if i == 0 else '':{width}}   {value}{suffix} — "
                       f"{n} row{'s' if n != 1 else ''}")
    return out
