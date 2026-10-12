"""HTML report of the scoreboard -> results/report.html.

Single-page SELF-CONTAINED: inline CSS, zero JS, zero dependencies, zero network
(can be opened with a double click or `xdg-open` offline). The scores are computed
by the real harness functions (report._scores / report._global_score with
config.WEIGHTS) so that this page and the CLI always say the same thing.

Usage:  python3 -m ggufbench.html_report   (writes results/report.html and prints the path)
"""

import datetime
import html as _html
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


def _rows(pool):
    """One row per model, sorted by global desc. Same math as the CLI."""
    speed_values = [int((r.get("speed") or {}).get("speed_ms") or 0) for r in pool]
    min_speed = min((v for v in speed_values if v > 0), default=0)
    rows = []
    for r in pool:
        slug = config.slug(r["model"])
        disp = slug
        for prefix in ("models_", "model_"):
            if disp.startswith(prefix):
                disp = disp[len(prefix):]
        rows.append({
            "name": disp,
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

    kpis = [("Best overall", f"{rows[0]['global']:.2f}" if rows else "—"),
            ("Fastest (gen)", f"{max((r['sc']['gen_tps'] for r in rows), default=0):.0f} t/s"),
            ("Lowest latency", f"{min((r['sc']['speed_ms'] for r in rows if r['sc']['speed_ms']), default=0)} ms"),
            ("Newest model", _esc(dates[-1]) if dates else "—")]

    ranking = []
    for i, r in enumerate(rows):
        cls = " top" if i == 0 else ""
        think = (f' <span class="badge">think:{_esc(r["thinking"])}</span>'
                 if r["thinking"] != "—" else "")
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
            f'{_esc(r["engine"])} {_esc(r["build"])}</span> <span class="miss">{_esc(r["ts"])}</span></summary>'
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
  Regenerate with <code>python3 -m ggufbench.html_report</code> from the workspace root.
  Ranking relative to this hardware and this harness: not at all comparable with
  public benchmarks (HumanEval, BFCL, SWE-bench). More: <code>docs/SPEC.md</code> ·
  <code>docs/MILLORA.md</code> · <code>AGENTS.md</code>.
</footer>
</body>
</html>
"""


def main(argv=None):
    pool = R.load_pool()
    out = config.RESULTS_DIR / "report.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(pool), encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
