"""HTML report of the scoreboard -> results/report.html.

Single-page SELF-CONTAINED: inline CSS, zero JS, zero dependencies, zero network
(can be opened with a double click or `xdg-open` offline). The scores are computed
by the real harness functions (report._scores / report._global_score with
config.WEIGHTS) so that this page and the CLI always say the same thing.

Also owns the model-vs-model compare page (MILLORA §4.4-4.5) -> results/compare.html:
same self-contained contract (inline CSS, zero deps, double click) plus a SMALL
inline JS picker (two selects + swap) that re-renders any pair client-side from the
embedded compact pool JSON (?a=slug,think&b=slug,think). Without JS the page still
shows the server-rendered pair; the scoreboard page keeps its zero-JS contract.

Usage:  python3 -m ggufbench.html_report   (writes results/report.html and prints the path)
        or, after any run, python3 -m ggufbench.run --html (same output, one flag)
        python3 -m ggufbench.run --compare "slug,think" "slug,think"   (results/compare.html)
"""

import datetime
import html as _html
import json
import subprocess

from . import config, report as R


def _esc(s):
    return _html.escape(str(s), quote=True)


def _gpu_chips():
    """GPU names (unique, sorted) for the header; [] when nvidia-smi is absent."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5)
        return sorted({line.split(",")[0].strip()
                       for line in out.stdout.splitlines() if line.strip()})
    except (OSError, subprocess.TimeoutExpired):
        return []


def _display_slug(slug):
    """Scoreboard display name: config.slug minus the models_/model_ path prefix
    (what _rows shows everywhere; --compare and the picker labels use it too)."""
    for prefix in ("models_", "model_"):
        if slug.startswith(prefix):
            return slug[len(prefix):]
    return slug


def _rows(pool):
    """One row per model, sorted by global desc. Same math as the CLI."""
    speed_values = [int((r.get("speed") or {}).get("speed_ms") or 0) for r in pool]
    min_speed = min((v for v in speed_values if v > 0), default=0)
    rows = []
    for r in pool:
        rows.append({
            "name": _display_slug(config.slug(r["model"])),
            "slug": config.slug(r["model"]),
            "sc": R._scores(r),
            "global": R._global_score(r, config.WEIGHTS, min_speed),
            "engine": r.get("engine", "llama"),
            "thinking": r.get("thinking") or "—",  # R4: legacy rows without key
            "code_excluded": int((r.get("code") or {}).get("excluded") or 0),  # R5
            "build": str(r.get("server_build") or "?"),
            "ts": (r.get("ts") or "")[:10],
            "by_lang": {d: (r.get(d) or {}).get("by_lang") or {} for d in ("code", "agent")},
            "code_by_level": (r.get("code") or {}).get("by_level") or {},
            "tasks": {d: len((r.get(d) or {}).get("trace") or [])
                      for d in ("tools", "code", "agent")},
            "flags": r.get("model_config_flags"),
        })
    rows.sort(key=lambda x: x["global"], reverse=True)
    return rows


def _heat(v):
    """Solid pill (no alpha): the text must read across the whole 0-1 range.
    Green blend over the card, computed in Python; the text color comes from the
    resulting luminance (threshold 0.38). Alpha over the dark background left
    illegible bands (light on mid-green, dark on dark green)."""
    k = 0.15 + 0.85 * max(0.0, min(1.0, v))
    r, g, b = (16 + (52 - 16) * k, 26 + (211 - 26) * k, 46 + (153 - 46) * k)
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    color = "#0b1220" if lum > 0.38 else "#e7eef9"
    return (f'<span class="heat" style="background:rgb({r:.0f},{g:.0f},{b:.0f});'
            f'color:{color}">{v:.2f}</span>')


def _picks(rows):
    """Category winners (from data, never hardcoded names): one card per each
    (model, mode) that wins ≥1 category, with its use cases."""
    cats = [
        ("global", "Best overall", "daily work in opencode (balance)",
         lambda r: r["global"]),
        ("code", "Best code", "hard/expert code tasks",
         lambda r: r["sc"]["code"]),
        ("agent", "Best agent", "autonomous multi-step work",
         lambda r: r["sc"]["agent"]),
        ("tools", "Best tools", "tool-calling and orchestration",
         lambda r: r["sc"]["tools"]),
        ("speed", "Fastest", "interactivity (lowest latency)",
         lambda r: -(r["sc"]["speed_ms"] or 1e9)),
        ("gen", "Highest throughput", "long generations",
         lambda r: r["sc"]["gen_tps"]),
        ("think", "Best thinking", "hard problems where thinking pays off the latency",
         lambda r: r["sc"]["code"] if r["thinking"] == "on" else -1),
    ]
    cards, seen = [], {}
    for key, label, use, metric in cats:
        cand = [r for r in rows if metric(r) > 0] or rows
        if not cand:
            continue
        best = max(cand, key=metric)
        ident = (best["name"], best["thinking"])
        if ident in seen:
            cards[seen[ident]][1].append((label, use))
        else:
            seen[ident] = len(cards)
            cards.append((best, [(label, use)]))
    return cards


def _rec_section(rows):
    """Final recommendations section: one card per winner with data and uses."""
    cards = _picks(rows)
    if not cards:
        return ""
    out = ['<section>\n  <h2>Recommendations (by use)</h2>\n  <div class="grid2">']
    for r, reasons in cards:
        think = (f' <span class="badge">think:{_esc(r["thinking"])}</span>'
                 if r["thinking"] != "—" else "")
        why = "".join(f"<li><b>{_esc(l)}</b> — {_esc(u)}</li>" for l, u in reasons)
        out.append(
            f'<section><h2>{_esc(r["name"])}{think}</h2>'
            f'<div class="kpi"><div class="v">{r["global"]:.2f}</div>'
            f'<div class="l">global · {_esc(r["engine"])} {_esc(r["build"])} · {_esc(r["ts"])}</div></div>'
            f'<div class="kpi"><div class="v">{r["sc"]["code"]:.0%} · {r["sc"]["agent"]:.0%} · '
            f'{r["sc"]["tools"]:.0%}</div><div class="l">code · agent · tools'
            f' (excluded code: {r["code_excluded"]})</div></div>'
            f'<div class="kpi"><div class="v">{r["sc"]["speed_ms"]} ms · {r["sc"]["gen_tps"]:.0f} t/s</div>'
            f'<div class="l">latency · throughput</div></div>'
            f"<ul>{why}</ul></section>")
    out.append("  </div>\n</section>")
    return "\n".join(out)


_CSS = """
:root{
  --bg:#0b1220; --card:#101a2e; --card2:#0d1526; --border:#1e2a44;
  --text:#e7eef9; --muted:#93a4be; --primary:#3b82f6; --primary2:#60a5fa;
  --accent:#f59e0b; --good:#34d399; --bad:#f87171;
  --mono:'Fira Code',ui-monospace,'Cascadia Mono','JetBrains Mono',monospace;
  --sans:'Fira Sans','Segoe UI',system-ui,-apple-system,sans-serif;
}
*{box-sizing:border-box}
html{scrollbar-color:var(--border) var(--bg)}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 var(--sans)}
a{color:var(--primary2)}
header{position:sticky;top:0;z-index:5;background:rgba(11,18,32,.94);backdrop-filter:blur(6px);
  border-bottom:1px solid var(--border);padding:14px 22px}
h1{margin:0;font-size:19px;letter-spacing:.2px}
h1 small{color:var(--muted);font-weight:400}
.sub{color:var(--muted);font-size:12.5px;margin-top:3px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.chip{font:11.5px/1 var(--mono);color:var(--muted);border:1px solid var(--border);
  border-radius:999px;padding:5px 9px;background:var(--card2)}
.chip b{color:var(--text);font-weight:600}
a.chip{background:var(--primary);color:#fff;border-color:transparent;font-weight:600}
a.chip:hover{background:var(--primary2);border-color:transparent}
main{max-width:1180px;margin:0 auto;padding:18px 22px 40px;display:grid;gap:16px}
.banner{border:1px solid #6b4b0a;background:#1c1503;color:#fcd34d;border-radius:10px;
  padding:10px 14px;font-size:13px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.kpi{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 14px}
.kpi .v{font:600 22px/1.15 var(--mono);color:var(--primary2)}
.kpi .l{color:var(--muted);font-size:12px;margin-top:2px}
section{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px 16px}
h2{margin:0 0 10px;font-size:14px;text-transform:uppercase;letter-spacing:.8px;color:var(--muted)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{color:var(--muted);text-align:left;font-weight:600;font-size:11.5px;text-transform:uppercase;
  letter-spacing:.5px;padding:6px 8px;border-bottom:1px solid var(--border)}
td{padding:6px 8px;border-bottom:1px solid var(--border)}
tr:hover td{background:rgba(59,130,246,.07)}
.num{font-family:var(--mono);text-align:right;white-space:nowrap}
.trow{display:flex;gap:10px;align-items:baseline;padding:5px 4px;border-bottom:1px solid var(--border)}
.trow:last-child{border-bottom:0}
.trow:hover{background:rgba(59,130,246,.07)}
.trow .name{flex:1;min-width:0}
.trow .num,.trow .gval{margin-left:auto}
.pos{font:600 13px var(--mono);color:var(--muted);text-align:right}
.pos.top{color:var(--accent)}
.name{font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.name small{display:block;color:var(--muted);font-weight:400;font:11px var(--mono)}
.badge{display:inline-block;font:10.5px/1 var(--mono);border-radius:5px;padding:3px 6px;
  border:1px solid var(--border);color:var(--muted)}
.badge.strata{color:#0b1220;background:var(--accent);border-color:var(--accent);font-weight:700}
.gval{font:600 15px var(--mono);text-align:right;color:var(--primary2)}
.gval.top{color:var(--accent)}
.heat{font:600 12px var(--mono);text-align:center;border-radius:6px;padding:4px 6px}
.miss{color:var(--muted);font-family:var(--mono)}
details{border:1px solid var(--border);border-radius:9px;background:var(--card2);
  margin-bottom:8px;overflow:hidden}
summary{cursor:pointer;padding:9px 12px;font-weight:600;list-style:none;display:flex;
  gap:10px;align-items:center;flex-wrap:wrap}
summary::-webkit-details-marker{display:none}
summary::after{content:'+';margin-left:auto;color:var(--muted);font-family:var(--mono)}
details[open] summary::after{content:'–'}
summary:hover,summary:focus-visible{background:rgba(59,130,246,.09)}
pre{margin:0;padding:10px 12px;border-top:1px solid var(--border);white-space:pre-wrap;
  word-break:break-word;font:11.5px/1.55 var(--mono);color:var(--muted)}
footer{color:var(--muted);font-size:12.5px;max-width:1180px;margin:0 auto;padding:0 22px 40px}
code{font-family:var(--mono);color:var(--primary2)}
:where(a,summary):focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:6px}
@media (max-width:900px){.grid2{grid-template-columns:1fr}}
@media (prefers-reduced-motion:no-preference){
  tr:hover td,.trow:hover,summary:hover{transition:background .18s ease}
}
@media print{header{position:static}body{background:#fff;color:#000}}
"""


def render(pool):
    """Complete HTML (str) for the given pool. No JS, no external resources."""
    rows = _rows(pool)
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    rec_section = _rec_section(rows)
    # C8 optimal thinking mode per model (needs wall_time_s on both rows of a
    # pair; rows from before it simply get no marker).
    optimal = R.optimal_by_slug(pool)
    gpus = _gpu_chips()
    w = config.WEIGHTS
    dates = sorted({r["ts"] for r in rows if r["ts"]})
    langs = ["python", "bash", "java", "typescript"]

    chips = [f'<span class="chip"><b>{len(rows)}</b> models</span>',
             f'<span class="chip"><b>{sum(max(r["tasks"].values()) for r in rows)}</b> tasks</span>',
             '<span class="chip">weights <b>tools {:.2f} · code {:.2f} · agent {:.2f} · speed {:.2f}</b></span>'.format(
                 w["tools"], w["code"], w["agent"], w["speed"])]
    chips += [f'<span class="chip"><b>{_esc(g)}</b></span>' for g in gpus]
    if len(dates) > 1:
        chips.append(f'<span class="chip">measured <b>{_esc(dates[0])} → {_esc(dates[-1])}</b></span>')
    # Pointer to the sibling compare page (results/compare.html, same dir both
    # locally and on gh-pages): the report keeps its zero-JS contract, the link
    # is the whole integration.
    chips.append('<a class="chip" href="compare.html">head-to-head compare →</a>')

    kpis = [("Best overall", f"{rows[0]['global']:.2f}" if rows else "—"),
            ("Fastest (gen)", f"{max((r['sc']['gen_tps'] for r in rows), default=0):.0f} t/s"),
            ("Lowest latency", f"{min((r['sc']['speed_ms'] for r in rows if r['sc']['speed_ms']), default=0)} ms"),
            ("Newest model", _esc(dates[-1]) if dates else "—")]

    ranking = []
    for i, r in enumerate(rows):
        cls = " top" if i == 0 else ""
        think = (f' <span class="badge">think:{_esc(r["thinking"])}</span>'
                 if r["thinking"] != "—" else "")
        if optimal.get(r["slug"]) == r["thinking"]:
            think += ' <span class="badge strata">★ optimal</span>'
        ranking.append(
            f'<div class="trow"><div class="pos{cls}">{i + 1}</div>'
            f'<div class="name" title="{_esc(r["name"])}">{_esc(r["name"])}<small>{_esc(r["ts"])} · {r["tasks"]["tools"]}+'
            f'{r["tasks"]["code"]}+{r["tasks"]["agent"]} tasks · excluded code: {r["code_excluded"]}</small></div>'
            f'<div class="gval{cls}">{r["global"]:.2f} <span class="badge{" strata" if r["engine"] == "strata" else ""}">'
            f'{_esc(r["engine"])} {_esc(r["build"])}</span>{think}</div></div>')

    def dim_bars(key, fmt):
        out = []
        for r in sorted(rows, key=lambda x: -(x["sc"][key] or 1e9) if key == "speed_ms" else (x["sc"][key] or 0)):
            v = r["sc"][key]
            # Badge BEFORE the name: .name uses ellipsis (nowrap) so the badge at the end
            # was clipped in narrow columns. title = full name as tooltip.
            think = (f'<span class="badge">think:{_esc(r["thinking"])}</span> '
                     if r["thinking"] != "—" else "")
            out.append(f'<div class="trow">'
                       f'<div class="name" title="{_esc(r["name"])}">{think}{_esc(r["name"])}</div>'
                       f'<div class="num" style="text-align:right">{fmt(v)}</div></div>')
        return "".join(out)

    matrix_rows = []
    for r in rows:
        cells = []
        for dim in ("code", "agent"):
            for lang in langs:
                v = r["by_lang"][dim].get(lang)
                if v is None:
                    cells.append('<td class="miss">—</td>')
                else:
                    cells.append(f"<td>{_heat(v)}</td>")
        think = (f'<span class="badge">think:{_esc(r["thinking"])}</span> '
                 if r["thinking"] != "—" else "")
        matrix_rows.append(f'<tr><td class="name" title="{_esc(r["name"])}">{think}{_esc(r["name"])}</td>'
                           f'{"".join(cells)}</tr>')
    matrix_head = "".join(f'<th>{dim}:{lang}</th>' for dim in ("code", "agent") for lang in langs)

    details = []
    for r in rows:
        flags = _esc(r["flags"]) if r["flags"] else "harness default flags"
        bl = r["code_by_level"]
        by_level_line = ""
        if bl:
            by_level_line = "code by level: " + " · ".join(
                f"{k} {v:.0%}" for k, v in sorted(bl.items())) + "\n"
        think_line = (f"think: {r['thinking']}\n" if r["thinking"] != "—" else "")
        details.append(
            f'<details><summary>{_esc(r["name"])} <span class="badge{" strata" if r["engine"] == "strata" else ""}">'
            f'{_esc(r["engine"])} {_esc(r["build"])}</span>'
            f'{" <span class='badge strata'>★ optimal</span>" if optimal.get(r["slug"]) == r["thinking"] else ""}'
            f' <span class="miss">{_esc(r["ts"])}</span></summary>'
            f'<pre>{by_level_line}{think_line}excluded code: {r["code_excluded"]}\n{flags}</pre></details>')

    banner = ""
    if len(dates) > 1:
        banner = ('<div class="banner"><b>Mixed conditions.</b> The entries in this pool were '
                  'measured on different dates and the harness evolves (tasks fixed, second engine, '
                  'per-model flags): compare with care and check <code>docs/MILLORA.md §C7</code> before '
                  'drawing conclusions from the whole table.</div>')

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bench Board — local model benchmark</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <h1>Bench Board <small>· local model benchmark for opencode</small></h1>
  <div class="sub">Generated {_esc(now)} · scores computed with the harness functions (same math as the CLI)</div>
  <div class="chips">{''.join(chips)}</div>
</header>
<main>
{banner}
<div class="kpis">{''.join(f'<div class="kpi"><div class="v">{v}</div><div class="l">{_esc(l)}</div></div>' for l, v in kpis)}</div>

<section>
  <h2>Weighted global</h2>
  {chr(10).join(ranking)}
</section>

<div class="grid2">
<section><h2>Code (32 tasks · 4 languages)</h2>{dim_bars("code", lambda v: f"{v:.0%}")}</section>
<section><h2>Multi-step agent (24 tasks)</h2>{dim_bars("agent", lambda v: f"{v:.0%}")}</section>
<section><h2>Tool-calling (8 tasks)</h2>{dim_bars("tools", lambda v: f"{v:.0%}")}</section>
<section><h2>Speed (generation ms · lower is better)</h2>{dim_bars("speed_ms", lambda v: f"{v} ms")}</section>
</div>

<section>
  <h2>Tokens per second</h2>
  <div class="grid2">
    <div><h2>gen (output)</h2>{dim_bars("gen_tps", lambda v: f"{v:.0f} t/s")}</div>
    <div><h2>prompt (input)</h2>{dim_bars("prompt_tps", lambda v: f"{v:.0f} t/s")}</div>
  </div>
</section>

<section>
  <h2>By language (code / agent)</h2>
  <table><thead><tr><th>Model</th>{matrix_head}</tr></thead>
  <tbody>{''.join(matrix_rows)}</tbody></table>
</section>

<section>
  <h2>Conditions per model</h2>
  {''.join(details)}
</section>
{rec_section}
</main>
<footer>
  Regenerate with <code>python3 -m ggufbench.run --scoreboard --html</code> (or
  <code>python3 -m ggufbench.html_report</code>) from the workspace root.
  Ranking relative to this hardware and this harness: not at all comparable with
  public benchmarks (HumanEval, BFCL, SWE-bench). More: <code>docs/SPEC.md</code> ·
  <code>docs/MILLORA.md</code> · <code>AGENTS.md</code>.
</footer>
</body>
</html>
"""


def write_default_report(pool=None):
    """Render the pool to results/report.html (config.RESULTS_DIR) and return the
    path written. Single owner of the render+path logic: run.py --html calls this
    instead of duplicating it. The pool is read at call time via report.load_pool()
    (the same accumulated source --scoreboard uses) unless one is passed in.
    Returns None when the pool is empty: nothing to render, no file touched."""
    if pool is None:
        pool = R.load_pool()
    if not pool:
        return None
    out = config.RESULTS_DIR / "report.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(pool), encoding="utf-8")
    return out


# --- Model-vs-model compare view (MILLORA §4.4-4.5, UserBenchmark layout) ---------------

# Head-to-head metric table: (label, description, pack value key, pack exclusion
# key, lower_is_better, format, verdict phrase). "Better" direction per metric:
# lower wins for latency and pool rank; higher wins for every score and
# throughput. Exclusion counts ride along inside the value cell so a green win
# on fewer graded tasks never reads as a clean win. The inline JS picker mirrors
# this exact table (keep both in sync).
_COMPARE_SECTIONS = [
    ("Global", [
        ("Weighted global", "tools .30 · code .30 · agent .25 · speed .15",
         "g", None, False, "score2", "Higher weighted global."),
        ("Pool rank", "position in the accumulated scoreboard; lower wins",
         "r", None, True, "rank", "Higher pool rank."),
        ("Wall clock (total run)", "time to complete the whole benchmark in this mode (C8); lower wins",
         "w", None, True, "secs", "Less wall clock."),
    ]),
    ("Speed", [
        ("Prompt + reply latency", "speed-task round trip; lower is better",
         "ms", None, True, "ms", "Faster prompt + reply latency."),
        ("Generation throughput", "output tokens/s",
         "gt", None, False, "tps", "Faster generation."),
        ("Prompt processing", "input tokens/s",
         "pt", None, False, "tps", "Faster prompt processing."),
    ]),
    ("Tools", [
        ("Tool-calling score", "8 graded tasks: arguments, multi-call, error handling",
         "tools", None, False, "pct", "Better tool-calling."),
    ]),
    ("Code", [
        ("Code overall", "all levels; (N excl.) = excluded with a recorded reason",
         "code", "cex", False, "pct", "Better code overall."),
        ("Easy tier", "base tasks",
         "lv.easy", "lv.easy.x", False, "pct", "Better on easy code."),
        ("Hard tier", "_hard tasks",
         "lv.hard", "lv.hard.x", False, "pct", "Better on hard code."),
        ("Expert tier", "_expert tasks (multi-file)",
         "lv.expert", "lv.expert.x", False, "pct", "Better on expert code."),
    ]),
    ("Agent", [
        ("Agent score", "turn + tool-call accounting over the agent tasks",
         "agent", None, False, "pct", "Better agent work."),
    ]),
]


def _level_excluded(r):
    """Excluded task count per code level, computed from the trace (the summary
    only stores the total): exclusions stay visible next to each tier score."""
    out = {}
    for t in (r.get("code") or {}).get("trace") or []:
        if t.get("excluded"):
            lvl = str(t.get("level") or "easy")
            out[lvl] = out.get(lvl, 0) + 1
    return out


def _fmt_env(env):
    """environment dict (C5) -> one line ('RTX 5080 16GB × 2 · driver … · os ·
    60 GB RAM'). None when the row predates the field (pre-C5): the card says so
    instead of inventing hardware."""
    if not isinstance(env, dict):
        return None
    parts = []
    seen = {}
    for g in env.get("gpu") or []:
        seen[g] = seen.get(g, 0) + 1
    if seen:
        parts.append(" + ".join(f"{g} × {n}" if n > 1 else g for g, n in seen.items()))
    if env.get("driver"):
        parts.append(f"driver {env['driver']}")
    if env.get("os"):
        parts.append(str(env["os"]))
    if env.get("ram_gb"):
        parts.append(f"{env['ram_gb']} GB RAM")
    return " · ".join(parts) or None


def _ranked(pool):
    """(min_speed, {report._key_of(row): rank}, ordered_rows) with the scoreboard's
    math: rows sorted by global desc — rank #1 is the same top model the report
    page shows. The pool is read-only: ranks are derived, never stored."""
    speed_values = [int((r.get("speed") or {}).get("speed_ms") or 0) for r in pool]
    min_speed = min((v for v in speed_values if v > 0), default=0)
    ordered = sorted(pool, key=lambda r: R._global_score(r, config.WEIGHTS, min_speed),
                     reverse=True)
    return min_speed, {R._key_of(r): i + 1 for i, r in enumerate(ordered)}, ordered


def _pack(r, rank, total, min_speed):
    """Compact compare row, shared by the static render and the picker JSON
    embedded in the page (short keys: the whole pool rides inline)."""
    sc = R._scores(r)
    code = r.get("code") or {}
    bl = code.get("by_level") or {}
    lex = _level_excluded(r)
    return {
        "s": _display_slug(config.slug(r["model"])),
        "t": r.get("thinking") or "—",
        "e": r.get("engine", "llama"),
        "b": str(r.get("server_build") or "?"),
        "d": (r.get("ts") or "")[:10],
        "f": r.get("model_config_flags") or "",
        "v": str(r.get("tasks_version") or "?"),
        "env": _fmt_env(r.get("environment")) or "",
        "g": R._global_score(r, config.WEIGHTS, min_speed),
        "r": rank,
        "n": total,
        "ms": int(sc["speed_ms"] or 0),
        "gt": sc["gen_tps"] or 0,
        "pt": sc["prompt_tps"] or 0,
        "w": r.get("wall_time_s"),
        "tools": sc["tools"],
        "code": sc["code"],
        "cex": int(code.get("excluded") or 0),
        "lv": {k: [bl.get(k), lex.get(k, 0)] for k in ("easy", "hard", "expert")},
        "agent": sc["agent"],
    }


def _pack_get(p, key):
    """Metric value from a packed row; None = not measured (renders as '—', never
    judged). 0 latency/throughput means the same: a partial run has no timing."""
    if key.startswith("lv."):
        v = p["lv"].get(key[3:])
        return v[0] if v and v[0] is not None else None
    v = p.get(key)
    if key in ("ms", "gt", "pt", "r", "w"):
        return v or None
    return None if v is None else v


def _pack_excl(p, key):
    """Exclusion count for a metric key (0 when the metric has none)."""
    if not key:
        return 0
    if key == "cex":
        return p.get("cex") or 0
    v = p["lv"].get(key[3:-2])  # 'lv.easy.x' -> 'easy'
    return (v[1] if v else 0) or 0


def _judge(x, y, lower_better):
    """Head-to-head judgement of one metric. Returns (winner, delta) where winner
    is 0 (A), 1 (B) or None. delta = the winner's improvement over the loser in %
    (the loser's value is the baseline); None for a tie, a missing value, or a win
    without a baseline (loser = 0: any % would be infinite, so the verdict keeps
    its phrase but shows no number)."""
    if x is None or y is None or x == y:
        return None, None
    a_wins = x < y if lower_better else x > y
    w, l = (x, y) if a_wins else (y, x)
    if not l:
        return (0 if a_wins else 1), None
    delta = (l - w) if lower_better else (w - l)
    return (0 if a_wins else 1), delta / l * 100


def _fmt_delta(d):
    """'+24%' (UserBenchmark voice). One decimal under 10 so a small real win does
    not round into a fake '+0%'."""
    if d is None:
        return ""
    return f"{d:+.0f}%" if abs(d) >= 10 else f"{d:+.1f}%"


def _fmt_value(kind, v, excl=0):
    """Cell text for a compare value; '—' when the metric was not measured.
    Exclusions ride along inline ('82% (4 excl.)' — MILLORA §4.4)."""
    if v is None:
        return "—"
    if kind == "score2":
        s = f"{v:.2f}"
    elif kind == "rank":
        s = f"#{v}"
    elif kind == "ms":
        s = f"{v} ms"
    elif kind == "secs":
        m, s = divmod(int(round(v)), 60)
        s = f"{m}m {s:02d}s" if m else f"{v:.0f}s"
    elif kind == "tps":
        s = f"{v:.0f} t/s"
    else:  # pct
        s = f"{v:.0%}"
    if excl:
        s += f' <small>({excl} excl.)</small>'
    return s


def _cmp_row(pa, pb, metric):
    """One metric row: label | value A | value B | verdict. Better green, worse
    red, ties neutral (no color, no %), missing values neutral too."""
    label, desc, vkey, xkey, lower, kind, phrase = metric
    va, vb = _pack_get(pa, vkey), _pack_get(pb, vkey)
    ea, eb = _pack_excl(pa, xkey), _pack_excl(pb, xkey)
    winner, delta = _judge(va, vb, lower)
    cells = []
    for i, (v, e) in enumerate(((va, ea), (vb, eb))):
        if v is None:
            cls = "mval miss"
        elif winner is not None:
            cls = "mval good" if i == winner else "mval bad"
        elif va is not None and vb is not None:
            cls = "mval tie"  # exact tie: neutral, no color
        else:
            cls = "mval"  # single-sided: nothing to judge, stays neutral
        cells.append(f'<div class="{cls}">{_fmt_value(kind, v, e)}</div>')
    if winner is None:
        verdict = ('<div class="verdict"><span class="tie">tie</span></div>'
                   if va is not None and vb is not None
                   else '<div class="verdict"><span class="miss">—</span></div>')
    else:
        d = _fmt_delta(delta)
        verdict = f'<div class="verdict good">{_esc(phrase)}{(" " + d) if d else ""}</div>'
    return (f'<div class="mrow"><div class="mlabel"><b>{_esc(label)}</b>'
            f'<small>{_esc(desc)}</small></div>{"".join(cells)}{verdict}</div>')


def _cmp_section(title, metrics, pa, pb):
    """One compare section. The summary badge is the MEAN of the per-metric deltas
    won inside the section, shown for the side that wins more metrics (ties and
    unjudgeable rows are excluded; a section that splits evenly gets no badge).
    Mean-of-deltas rather than any weighted aggregate: the metrics in a section
    mix units (ms, t/s, %), so a weighting would be an invented constant — the
    mean needs none and stays defensible."""
    rows, wins, deltas = [], {0: 0, 1: 0}, {0: [], 1: []}
    for metric in metrics:
        rows.append(_cmp_row(pa, pb, metric))
        winner, delta = _judge(_pack_get(pa, metric[2]), _pack_get(pb, metric[2]), metric[4])
        if winner is not None:
            wins[winner] += 1
            if delta is not None:
                deltas[winner].append(delta)
    badge = ""
    if wins[0] != wins[1]:
        side = 0 if wins[0] > wins[1] else 1
        if deltas[side]:
            mean = sum(deltas[side]) / len(deltas[side])
            w = pa if side == 0 else pb
            badge = (f' <span class="secbadge good" title="mean of the metric deltas '
                     f'won by {_esc(w["s"])} (think:{_esc(w["t"])}) in this section">'
                     f'{_fmt_delta(mean)}</span>')
    return (f"<section>\n  <h2>{_esc(title)}{badge}</h2>\n  "
            + "\n  ".join(rows) + "\n</section>")


def _cmp_card(p):
    """Header card (UserBenchmark-style product card): name, global, pool rank,
    think mode, engine/build, model_config_flags, environment."""
    think = f' <span class="badge">think:{_esc(p["t"])}</span>' if p["t"] != "—" else ""
    eng = (f' <span class="badge{" strata" if p["e"] == "strata" else ""}">'
           f'{_esc(p["e"])} {_esc(p["b"])}</span>')
    rank = f'rank #{p["r"]} of {p["n"]}' if p["r"] else "unranked (row not in pool)"
    env = _esc(p["env"]) if p["env"] else '<span class="miss">not recorded (pre-C5 row)</span>'
    flags = _esc(p["f"]) if p["f"] else "harness default flags"
    return (f'<section class="card"><h2>{_esc(p["s"])}{think}{eng}</h2>'
            f'<div class="kpi"><div class="v">{p["g"]:.2f}</div>'
            f'<div class="l">global · {rank} · measured {_esc(p["d"])}</div></div>'
            f'<div class="meta"><div class="l">model_config_flags</div>'
            f'<div class="mv">{flags}</div></div>'
            f'<div class="meta"><div class="l">environment</div>'
            f'<div class="mv">{env}</div></div></section>')


_COMPARE_CSS = """
.cards{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.card h2{font-size:15px;text-transform:none;letter-spacing:0;color:var(--text)}
.meta{margin-top:10px}
.meta .l{color:var(--muted);font-size:10.5px;text-transform:uppercase;letter-spacing:.5px}
.meta .mv{font:12px/1.5 var(--mono);word-break:break-word;margin-top:2px}
.mrow{display:grid;grid-template-columns:minmax(190px,1.3fr) 120px 120px minmax(170px,1fr);
  gap:10px;align-items:baseline;padding:7px 4px;border-bottom:1px solid var(--border)}
.mrow:last-child{border-bottom:0}
.mrow:hover{background:rgba(59,130,246,.07)}
.mlabel{min-width:0}
.mlabel b{font-weight:600}
.mlabel small{display:block;color:var(--muted);font-size:11px;font-weight:400}
.mval{font:600 14px var(--mono);text-align:right;white-space:nowrap}
.mval small{font:400 10.5px var(--mono);color:var(--muted)}
.mval.good{color:var(--good)}
.mval.bad{color:var(--bad)}
.mval.tie,.mval.miss{color:var(--muted);font-weight:400}
.verdict{font-size:12.5px;color:var(--muted);min-width:0}
.verdict.good{color:var(--good);font-weight:600}
.tie{color:var(--muted)}
.good{color:var(--good)}
.bad{color:var(--bad)}
.secbadge{font:600 11.5px var(--mono);border:1px solid var(--border);border-radius:999px;
  padding:3px 9px;margin-left:10px;vertical-align:2px}
.secbadge.good{color:var(--good);border-color:var(--good)}
.picker{display:flex;gap:6px;align-items:center;margin-top:10px;flex-wrap:wrap}
.picker .l{color:var(--muted);font-size:12px}
.picker select{background:#16233d;color:var(--text);border:1px solid var(--border);
  border-radius:8px;padding:6px 8px;font:12px var(--mono);max-width:330px}
.picker select option{background:var(--card);color:var(--text)}
.picker button{background:var(--card2);color:var(--text);border:1px solid var(--border);
  border-radius:8px;padding:6px 10px;cursor:pointer;font:12px var(--mono)}
.picker button:hover,.picker select:hover{border-color:var(--primary)}
@media (max-width:900px){.cards{grid-template-columns:1fr}
  .mrow{grid-template-columns:1fr 96px 96px}
  .mrow .verdict{grid-column:1/-1}}
"""


_PICKER_JS = """
(function () {
  "use strict";
  var POOL = JSON.parse(document.getElementById("cmp-data").textContent);
  // Mirror of _COMPARE_SECTIONS in html_report.py — keep both in sync.
  // [label, description, valueKey, exclKey, lowerIsBetter, fmt, verdictPhrase]
  var SECTIONS = [
    ["Global", [
      ["Weighted global", "tools .30 · code .30 · agent .25 · speed .15", "g", null, false, "score2", "Higher weighted global."],
      ["Pool rank", "position in the accumulated scoreboard; lower wins", "r", null, true, "rank", "Higher pool rank."],
      ["Wall clock (total run)", "time to complete the whole benchmark in this mode (C8); lower wins", "w", null, true, "secs", "Less wall clock."]]],
    ["Speed", [
      ["Prompt + reply latency", "speed-task round trip; lower is better", "ms", null, true, "ms", "Faster prompt + reply latency."],
      ["Generation throughput", "output tokens/s", "gt", null, false, "tps", "Faster generation."],
      ["Prompt processing", "input tokens/s", "pt", null, false, "tps", "Faster prompt processing."]]],
    ["Tools", [
      ["Tool-calling score", "8 graded tasks: arguments, multi-call, error handling", "tools", null, false, "pct", "Better tool-calling."]]],
    ["Code", [
      ["Code overall", "all levels; (N excl.) = excluded with a recorded reason", "code", "cex", false, "pct", "Better code overall."],
      ["Easy tier", "base tasks", "lv.easy", "lv.easy.x", false, "pct", "Better on easy code."],
      ["Hard tier", "_hard tasks", "lv.hard", "lv.hard.x", false, "pct", "Better on hard code."],
      ["Expert tier", "_expert tasks (multi-file)", "lv.expert", "lv.expert.x", false, "pct", "Better on expert code."]]],
    ["Agent", [
      ["Agent score", "turn + tool-call accounting over the agent tasks", "agent", null, false, "pct", "Better agent work."]]]
  ];
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c];
    });
  }
  function getv(p, k) {
    if (k.slice(0, 3) === "lv.") {
      var e = p.lv[k.slice(3)];
      return (e && e[0] != null) ? e[0] : null;
    }
    var v = p[k];
    if (k === "ms" || k === "gt" || k === "pt" || k === "r" || k === "w") return v ? v : null;
    return (v == null) ? null : v;
  }
  function getx(p, k) {
    if (!k) return 0;
    if (k === "cex") return p.cex || 0;
    var e = p.lv[k.slice(3, -2)]; // "lv.easy.x" -> "easy"
    return (e && e[1]) || 0;
  }
  function fmt(kind, v, ex) {
    var s;
    if (kind === "score2") s = v.toFixed(2);
    else if (kind === "rank") s = "#" + v;
    else if (kind === "ms") s = v + " ms";
    else if (kind === "secs") { var t = Math.round(v), m = Math.floor(t / 60);
      s = m ? m + "m " + String(t % 60).padStart(2, "0") + "s" : t + "s"; }
    else if (kind === "tps") s = Math.round(v) + " t/s";
    else s = Math.round(v * 100) + "%";
    return ex ? s + " <small>(" + ex + " excl.)</small>" : s;
  }
  function sign(d) {
    var s = Math.abs(d) >= 10 ? d.toFixed(0) : d.toFixed(1);
    return (d >= 0 ? "+" : "") + s + "%";
  }
  function card(p) {
    var think = p.t === "—" ? "" : ' <span class="badge">think:' + esc(p.t) + "</span>";
    var eng = ' <span class="badge' + (p.e === "strata" ? " strata" : "") + '">'
      + esc(p.e) + " " + esc(p.b) + "</span>";
    var rank = p.r ? "rank #" + p.r + " of " + p.n : "unranked (row not in pool)";
    var env = p.env ? esc(p.env) : '<span class="miss">not recorded (pre-C5 row)</span>';
    var flags = p.f ? esc(p.f) : "harness default flags";
    return '<section class="card"><h2>' + esc(p.s) + think + eng + "</h2>"
      + '<div class="kpi"><div class="v">' + p.g.toFixed(2) + "</div>"
      + '<div class="l">global · ' + rank + " · measured " + esc(p.d) + "</div></div>"
      + '<div class="meta"><div class="l">model_config_flags</div><div class="mv">' + flags + "</div></div>"
      + '<div class="meta"><div class="l">environment</div><div class="mv">' + env + "</div></div></section>";
  }
  function mixedBanner(a, b) {
    if (a.d === b.d && a.v === b.v) return "";
    return '<div class="banner"><b>Mixed conditions.</b> These two rows were not measured under '
      + "identical conditions (" + esc(a.d) + " · tasks " + esc(a.v) + " vs " + esc(b.d)
      + " · tasks " + esc(b.v) + "): the harness evolves, compare with care (docs/MILLORA.md §C7).</div>";
  }
  function sections(A, B) {
    var out = "";
    for (var s = 0; s < SECTIONS.length; s++) {
      var metrics = SECTIONS[s][1], rows = "", wins = [0, 0], ds = [[], []];
      for (var j = 0; j < metrics.length; j++) {
        var m = metrics[j];
        var va = getv(A, m[2]), vb = getv(B, m[2]);
        var ca = "mval", cb = "mval", vcls = "", verdict;
        if (va == null || vb == null) {
          if (va == null) ca = "mval miss";
          if (vb == null) cb = "mval miss";
          verdict = '<span class="miss">—</span>';
        } else if (va === vb) {
          ca = cb = "mval tie";
          verdict = '<span class="tie">tie</span>';
        } else {
          var aWins = m[4] ? va < vb : va > vb, w = aWins ? 0 : 1;
          var wval = aWins ? va : vb, lval = aWins ? vb : va;
          ca = aWins ? "mval good" : "mval bad";
          cb = aWins ? "mval bad" : "mval good";
          wins[w]++;
          var dtxt = "";
          if (lval !== 0) {
            var d = (m[4] ? (lval - wval) : (wval - lval)) / lval * 100;
            ds[w].push(d);
            dtxt = " " + sign(d);
          }
          vcls = " good";
          verdict = esc(m[6]) + dtxt;
        }
        rows += '<div class="mrow"><div class="mlabel"><b>' + esc(m[0]) + "</b><small>" + esc(m[1])
          + '</small></div><div class="' + ca + '">' + (va == null ? "—" : fmt(m[5], va, getx(A, m[3])))
          + '</div><div class="' + cb + '">' + (vb == null ? "—" : fmt(m[5], vb, getx(B, m[3])))
          + '</div><div class="verdict' + vcls + '">' + verdict + "</div></div>";
      }
      var badge = "";
      if (wins[0] !== wins[1]) {
        var side = wins[0] > wins[1] ? 0 : 1;
        if (ds[side].length) {
          var mean = ds[side].reduce(function (acc, d) { return acc + d; }, 0) / ds[side].length;
          var wp = side === 0 ? A : B;
          badge = ' <span class="secbadge good" title="mean of the metric deltas won by '
            + esc(wp.s) + " (think:" + esc(wp.t) + ') in this section">' + sign(mean) + "</span>";
        }
      }
      out += "<section><h2>" + esc(SECTIONS[s][0]) + badge + "</h2>" + rows + "</section>";
    }
    return out;
  }
  var selA = document.getElementById("sel-a"),
      selB = document.getElementById("sel-b");
  function render() {
    var A = POOL[selA.value], B = POOL[selB.value];
    document.getElementById("cmp-body").innerHTML =
      mixedBanner(A, B) + '<div class="cards">' + card(A) + card(B) + "</div>" + sections(A, B);
  }
  POOL.forEach(function (p, i) {
    var o = document.createElement("option");
    o.value = String(i);
    o.textContent = p.s + " · think:" + p.t;
    selA.appendChild(o);
    selB.appendChild(o.cloneNode(true));
  });
  function byLabel(lab) {
    if (!lab) return -1;
    var kv = lab.split(",");
    for (var i = 0; i < POOL.length; i++)
      if (POOL[i].s === kv[0] && POOL[i].t === kv[1]) return i;
    return -1;
  }
  function sync() {
    try {
      history.replaceState(null, "",
        "?a=" + encodeURIComponent(POOL[selA.value].s + "," + POOL[selA.value].t)
        + "&b=" + encodeURIComponent(POOL[selB.value].s + "," + POOL[selB.value].t));
    } catch (e) { /* file:// may refuse URL rewrites: the page still re-renders */ }
  }
  function changed() { render(); sync(); }
  selA.addEventListener("change", changed);
  selB.addEventListener("change", changed);
  document.getElementById("swap").addEventListener("click", function () {
    var t = selA.value;
    selA.value = selB.value;
    selB.value = t;
    changed();
  });
  var params = new URLSearchParams(location.search);
  var qa = byLabel(params.get("a")), qb = byLabel(params.get("b"));
  if (qa >= 0 && qb >= 0 && qa !== qb) {
    selA.value = String(qa);
    selB.value = String(qb);
    render();
  }
})();
"""


def _pool_json(packs):
    """Compact pool JSON, safe to embed inside <script type="application/json">:
    '<' etc. become \\u003c-style escapes, which JSON.parse reads back unchanged
    and the HTML parser can never mistake for a closing tag."""
    s = json.dumps(packs, ensure_ascii=False, separators=(",", ":"))
    return s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _find_or_append(packs, p):
    """Index of the pack matching (slug, think); appends it when the compared row
    is not part of the pool (possible when callers pass rows directly)."""
    for i, q in enumerate(packs):
        if q["s"] == p["s"] and q["t"] == p["t"]:
            return i
    packs.append(p)
    return len(packs) - 1


def render_compare(row_a, row_b, pool=None):
    """Head-to-head HTML (str) of two pool rows (MILLORA §4.4, UserBenchmark
    layout): two header cards, then sections where every metric shows both values
    side by side — better green, worse red, ties neutral — with the winner's
    delta % as a verdict line and a mean-of-deltas badge per section. Mixed-
    conditions pairs get the banner; the n=1 caveat is always visible.

    Self-contained like the report (inline CSS/JS, zero deps, double click) plus
    a small inline JS picker: the compact pool JSON is embedded so any pair can
    be re-rendered client-side (?a=slug,think&b=slug,think honored); WITHOUT JS
    the page still shows the server-rendered pair correctly."""
    if pool is None:
        pool = R.load_pool()
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    min_speed, ranks, _ordered = _ranked(pool)
    pa = _pack(row_a, ranks.get(R._key_of(row_a)), len(pool), min_speed)
    pb = _pack(row_b, ranks.get(R._key_of(row_b)), len(pool), min_speed)
    packs = [_pack(r, ranks.get(R._key_of(r)), len(pool), min_speed) for r in pool]
    ia, ib = _find_or_append(packs, pa), _find_or_append(packs, pb)

    def _options(selected):
        return "".join(
            f'<option value="{i}"{" selected" if i == selected else ""}>'
            f'{_esc(p["s"])} · think:{_esc(p["t"])}</option>'
            for i, p in enumerate(packs))

    banner = ""
    if pa["d"] != pb["d"] or pa["v"] != pb["v"]:
        banner = (f'<div class="banner"><b>Mixed conditions.</b> These two rows were not '
                  f'measured under identical conditions ({_esc(pa["d"])} · tasks {_esc(pa["v"])} '
                  f'vs {_esc(pb["d"])} · tasks {_esc(pb["v"])}): the harness evolves, compare '
                  f'with care (docs/MILLORA.md §C7).</div>')
    cards = f'<div class="cards">{_cmp_card(pa)}{_cmp_card(pb)}</div>'
    sections_html = "".join(
        _cmp_section(title, metrics, pa, pb) for title, metrics in _COMPARE_SECTIONS)
    w = config.WEIGHTS
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Head-to-head — ggufbench compare</title>
<style>{_CSS + _COMPARE_CSS}</style>
</head>
<body>
<header>
  <h1>Head-to-head <small>· ggufbench model-vs-model compare</small></h1>
  <div class="sub">Generated {_esc(now)} · scores from the harness functions (same math as the CLI) ·
single sample per task (<b>n=1</b>, fixed seed/temp): this page orders, it does not certify close calls</div>
  <div class="chips"><span class="chip">weights <b>tools {w['tools']} · code {w['code']} · agent {w['agent']} · speed {w['speed']}</b></span>
  <span class="chip">better <b><span class="good">green</span></b> / worse <b><span class="bad">red</span></b> · ties stay neutral</span></div>
  <div class="picker">
    <span class="l">pick a pair</span>
    <select id="sel-a" aria-label="model A">{_options(ia)}</select>
    <button id="swap" type="button" title="swap A ⇄ B">⇄ swap</button>
    <select id="sel-b" aria-label="model B">{_options(ib)}</select>
    <noscript><span class="l">(static page: regenerate with <code>--compare</code> for another pair)</span></noscript>
  </div>
</header>
<main>
<div id="cmp-body">
{banner}
{cards}
{sections_html}
</div>
</main>
<footer>
  Regenerate with <code>python3 -m ggufbench.run --compare "slug,think" "slug,think"</code>
  (think defaults to off) from the workspace root. Section badges are the mean of the metric
  deltas won inside the section. Ranking relative to this hardware and this harness: not at all
  comparable with public benchmarks (HumanEval, BFCL, SWE-bench). More: <code>docs/SPEC.md</code> ·
  <code>docs/MILLORA.md</code>.
</footer>
<script id="cmp-data" type="application/json">{_pool_json(packs)}</script>
<script>{_PICKER_JS}</script>
</body>
</html>
"""


def _default_pair(pool):
    """Default head-to-head when no pair is given: the top of the scoreboard vs
    the same model in the other thinking mode (the think on/off question is the
    most common one), otherwise vs the runner-up."""
    ranked = _ranked(pool)[2]
    top = ranked[0]
    top_key = R._key_of(top)
    for r in ranked[1:]:
        k = R._key_of(r)
        if k[0] == top_key[0] and k[1] != top_key[1]:
            return top, r
    return top, ranked[1]


def write_default_compare(row_a=None, row_b=None, pool=None):
    """Render the head-to-head page to results/compare.html (config.RESULTS_DIR)
    and return the path written. Same contract as write_default_report: the pool
    is read at call time via report.load_pool() unless one is passed in, and
    nothing is written when there is no pair (empty pool or a single row without
    an explicit pair). Without an explicit pair: top of the scoreboard vs the
    same model in the other thinking mode (or the runner-up)."""
    if pool is None:
        pool = R.load_pool()
    if row_a is None or row_b is None:
        if len(pool) < 2:
            return None
        row_a, row_b = _default_pair(pool)
    out = config.RESULTS_DIR / "compare.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_compare(row_a, row_b, pool=pool), encoding="utf-8")
    return out


def main(argv=None):
    out = write_default_report()
    if out is None:
        print("pool is empty: no HTML report written")
        return 0
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
