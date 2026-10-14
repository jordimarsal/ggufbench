"""HTML report of the scoreboard -> results/report.html.

Single-page SELF-CONTAINED: inline CSS, zero dependencies, zero network (can be opened
with a double click or `xdg-open` offline). The scores are computed by the real harness
functions (report._scores / report._global_score with config.WEIGHTS) so that this page
and the CLI always say the same thing.

The scoreboard carries one small inline script: the ranking's order control (by global,
by a dimension, or by task set — MILLORA §C9). Without it the page reads correctly in the
server-side order (--sort), and every row states its test version (SET: label·task-set).

Also owns the model-vs-model compare page (MILLORA §4.4-4.5) -> results/compare.html:
same self-contained contract (inline CSS, zero deps, double click) plus a SMALL
inline JS picker (two selects + swap) that re-renders any pair client-side from the
embedded compact pool JSON (?a=slug,think&b=slug,think). Without JS the page still
shows the server-rendered pair.

Usage:  python3 -m ggufbench.html_report   (writes results/report.html and prints the path)
        or, after any run, python3 -m ggufbench.run --html (same output, one flag)
        python3 -m ggufbench.run --compare "slug,think" "slug,think"   (results/compare.html)
"""

import datetime
import html as _html
import json
import os
import re
import subprocess

from . import config, report as R


def _esc(s):
    return _html.escape(str(s), quote=True)


_RETIRED_STEMS = None


def _retired_stems():
    """Stems of the pruned fleet. Their pool rows stay as a record but render gray.
    Two sources, unioned: the tracked registry (config.RETIRED_FILE — survives the
    profiles being deleted outside the repo) and any profile still parked under
    models/retired/ (parking a profile there retires it by convention). Cached; tests
    reset html_report._RETIRED_STEMS or patch this function for determinism."""
    global _RETIRED_STEMS
    if _RETIRED_STEMS is None:
        _RETIRED_STEMS = _registry_stems() | _archived_profile_stems()
    return _RETIRED_STEMS


def _registry_stems():
    """Stems listed in the retired registry. A missing/corrupt file degrades to empty
    (the report is regenerated on machines that may not have it), never raises."""
    try:
        data = json.loads(config.RETIRED_FILE.read_text())
    except (OSError, ValueError):
        return set()
    stems = set()
    for entry in data.get("retired") or []:
        stem = entry.get("stem") if isinstance(entry, dict) else entry
        if stem:
            stems.add(str(stem))
    return stems


def _archived_profile_stems():
    """Stems of the profiles archived under models/retired/ (outside the repo: absent
    on CI checkouts, so this degrades to empty rather than failing)."""
    try:
        return {p.stem for p in (config.MODELS_DIR / "retired").glob("*.txt")}
    except OSError:
        return set()


def _is_retired(model):
    """A row is retired when its model file stem lives in models/retired/."""
    return os.path.splitext(os.path.basename(model or ""))[0] in _retired_stems()


# Sanitizer: strips sensitive local paths from user-derived text before HTML escaping.
# Only applied at render time — raw pool/results JSON files are never touched.
def _sanitize_public(text):
    """Redact absolute paths that leak local filesystem layout."""
    if not isinstance(text, str):
        return text
    # Token-level sanitizer: split on whitespace, redact paths that start with
    # /home/<user>/ or /Users/<user>/ (→ ~/subdir/basename), then any other abs path
    # (→ [local] basename).
    parts = text.split()
    out_parts = []
    for p in parts:
        if p.startswith('/home/'):
            sub = p[len('/home/'):]  # strip user dir prefix → ~/rest
            out_parts.append(f'~/{sub}')
        elif p.startswith('/Users/'):
            sub = p[len('/Users/'):]
            out_parts.append(f'~/{sub}')
        elif p.startswith('/') and '/' in p[1:]:
            out_parts.append(f'[local] {os.path.basename(p)}')
        else:
            out_parts.append(p)
    text = ' '.join(out_parts)
    return text


def _sanitize_env(env):
    """Environment dict → one line WITHOUT driver version; OS family only."""
    import platform as _platform  # lazy so the module imports without it
    if not isinstance(env, dict):
        return None
    parts = []
    seen = {}
    for g in env.get("gpu") or []:
        seen[g] = seen.get(g, 0) + 1
    if seen:
        parts.append(" + ".join(f"{g} × {n}" if n > 1 else g for g, n in seen.items()))
    # Drop driver; keep GPU names (+VRAM if present) and RAM.
    os_family = _platform.system()  # "Linux" / "macOS" / "Windows"
    parts.append(os_family)
    if env.get("ram_gb"):
        parts.append(f"{env['ram_gb']} GB RAM")
    return " · ".join(parts) or None


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


def _order_rows(rows, sort):
    """Rows in the requested order (the same semantics as the CLI --sort). 'global' is the
    order _rows already produced; 'version' groups by task set — biggest set first, global
    inside each group — so scores measured on different tasks are never interleaved
    (MILLORA §C9)."""
    if sort == "tools":
        return sorted(rows, key=lambda r: (-(r["sc"]["tools"] or 0), -r["global"]))
    if sort == "code":
        return sorted(rows, key=lambda r: (-(r["sc"]["code"] or 0), -r["global"]))
    if sort == "agent":
        return sorted(rows, key=lambda r: (-(r["sc"]["agent"] or 0), -r["global"]))
    if sort == "speed":
        return sorted(rows, key=lambda r: (r["sc"]["speed_ms"] or 1e9, -r["global"]))
    if sort == "version":
        return sorted(rows, key=lambda r: (-r["set_size"], -r["global"]))
    return sorted(rows, key=lambda r: -r["global"])


def _set_badge(r):
    """The test version as a badge: label + real task set ('v3·16/60/60'), in every row."""
    return f'<span class="badge set">{_esc(r["set"])}</span>'


def _n_tasks(rows, dim):
    """Tasks graded in a dimension, for a section title. Data-driven, never hardcoded:
    the pool holds rows from different task sets, so a fixed number would be a lie for
    some of them (the row itself states its exact SET)."""
    return max((r["tasks"][dim] for r in rows), default=0)


def _rows_phrase(n):
    """Counting phrase for the notes: '1 row' / '2 rows' — a benchmark whose whole point is
    reading numbers should not print '1 rows'."""
    return f"{n} row" + ("" if n == 1 else "s")


def _by_set_section(rows):
    """Static 'by task set' view (MILLORA §C9): one block per task set, its rows ordered by
    global inside the block, so a reader can pick a set and compare only inside it. It is
    the no-JS answer to 'order by test version' — the ranking control does it in place."""
    groups = {}
    for r in rows:
        groups.setdefault(r["sig"], []).append(r)
    if not groups:
        return ""
    out = ['<section>\n  <h2>By task set</h2>',
           '  <p class="miss">A score is comparable only inside a set: the pool may hold rows '
           'measured with different task counts (the <code>SET</code> badge). '
           'See <code>docs/MILLORA.md §C9</code>.</p>']
    for sig, group in sorted(groups.items(), key=lambda kv: (-R._set_size(kv[0]), kv[0])):
        group = sorted(group, key=lambda r: -r["global"])
        dates = sorted({r["ts"] for r in group if r["ts"]})
        span = f'{dates[0]} → {dates[-1]}' if len(dates) > 1 else (dates[0] if dates else "—")
        labels = sorted({r["set"].split("·")[0] for r in group})
        out.append(f'  <div class="setblock" id="set-{_esc(sig.replace("/", "-"))}">'
                   f'<h3>{_esc(sig)} tasks '
                   f'<span class="setmeta">· label {" / ".join(_esc(l) for l in labels)} · '
                   f'{len(group)} row{"s" if len(group) != 1 else ""} · measured {_esc(span)}</span></h3>')
        for r in group:
            think = (f' <span class="badge">think:{_esc(r["thinking"])}</span>'
                     if r["thinking"] != "—" else "")
            if r["retired"]:
                think += ' <span class="badge">retired</span>'
            out.append(
                f'    <div class="trow{" retired" if r["retired"] else ""}">'
                f'<div class="name" title="{_esc(r["name"])}">{_esc(r["name"])}'
                f'<small>{_esc(r["ts"])} · tools {r["sc"]["tools"]:.0%} · code {r["sc"]["code"]:.0%} · '
                f'agent {r["sc"]["agent"]:.0%}</small></div>'
                f'<div class="gval">{r["global"]:.2f}{think}{_set_badge(r)}</div></div>')
        out.append("  </div>")
    out.append("</section>")
    return "\n".join(out)


def _spread_html(spread):
    """' <small>±26</small>' — '' when the row is a single-run measurement (every row
    of a pool measured without --runs): the page renders exactly as before. Same math
    as the CLI (report.run_spread)."""
    return "" if spread is None else f' <small>±{spread * 100:.0f}</small>'


def _rows(pool):
    """One row per model, sorted by global desc. Same math as the CLI."""
    speed_values = [int((r.get("speed") or {}).get("speed_ms") or 0) for r in pool]
    min_speed = min((v for v in speed_values if v > 0), default=0)
    rows = []
    for r in pool:
        rows.append({
            "name": _display_slug(config.slug(r["model"])),
            "slug": config.slug(r["model"]),
            "retired": _is_retired(r.get("model")),
            "sc": R._scores(r),
            "global": R._global_score(r, config.WEIGHTS, min_speed),
            "spread": R.run_spread(r, config.WEIGHTS, min_speed),
            "engine": r.get("engine", "llama"),
            "thinking": r.get("thinking") or "—",  # R4: legacy rows without key
            "code_excluded": int((r.get("code") or {}).get("excluded") or 0),  # R5
            "build": str(r.get("server_build") or "?"),
            "ts": (r.get("ts") or "")[:10],
            # §C9: the test version, label and real task set ('v3·16/60/60'), shown in
            # every row and used to group/order the board by set.
            "set": R.set_label(r),
            "sig": R.task_signature(r),
            # §C10: the other two conditions a row carries — the engine build (already
            # displayed) and the baseline digest (never recorded before, '?' if legacy).
            "base": R.baseline_id(r),
            "set_size": R._set_size(R.task_signature(r)),
            "by_lang": {d: (r.get(d) or {}).get("by_lang") or {} for d in ("code", "agent")},
            "code_by_level": (r.get("code") or {}).get("by_level") or {},
            # §C12: the code token cap and any per-task calibration that was in play.
            "code_budget": (r.get("code") or {}).get("code_budget"),
            "code_budget_stored": (r.get("code") or {}).get("code_budget_stored") or {},
            # §C13 run-time probes: ceilings that were touched, and whether the requested
            # thinking mode could be applied at all.
            "code_budget_hits": (r.get("code") or {}).get("code_budget_hits") or 0,
            "agent_empty_replies": (r.get("agent") or {}).get("agent_empty_replies") or 0,
            "tools_capped": (r.get("tools") or {}).get("tools_capped") or 0,
            "thinking_applied": r.get("thinking_mode_applied"),
            "thinking_note": r.get("thinking_mode_note"),
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
    """Final recommendations section: one card per winner with data and uses.
    Retired models never appear here — you cannot run what you deleted."""
    cards = _picks([r for r in rows if not r["retired"]])
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
  /* Minor titles / metadata headings (task-set block headers). Amber, because in this
     page that is already the "condition / caveat" colour of the mixed-conditions banner:
     the set of tasks a row ran is a caveat, not a score. One variable to retune it. */
  --label:#f59e0b;
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
.retired .name,.retired .num,.retired .gval,.retired td,.retired small,.retired summary,.retired .pos{color:var(--muted)!important;font-weight:400}
.retired .heat{background:#232f45!important;color:var(--muted)!important}
.retired .badge{background:transparent!important;color:var(--muted)!important;border-color:var(--border)!important;font-weight:400}
.badge.strata{color:#0b1220;background:var(--accent);border-color:var(--accent);font-weight:700}
.badge.set{color:var(--primary2);border-color:#2b4a7a}
.sortbar{display:flex;gap:8px;align-items:center;margin:0 0 8px;font-size:12px;color:var(--muted)}
.sortbar select{background:var(--card2);color:var(--text);border:1px solid var(--border);
  border-radius:7px;padding:4px 6px;font:12px var(--mono)}
.sortbar select:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.setblock{border:1px solid var(--border);border-radius:9px;background:var(--card2);
  padding:8px 10px;margin-bottom:8px}
.setblock h3{margin:0 0 6px;font:600 12px var(--mono);letter-spacing:.3px;color:var(--label)}
.setblock h3 .setmeta{color:var(--label);opacity:.75;font-weight:400}
.gval{font:600 15px var(--mono);text-align:right;color:var(--primary2)}
.gval.top{color:var(--accent)}
.gval small,.kpi .v small{color:var(--muted);font-weight:400;font-size:11px}
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


def render(pool, sort="global"):
    """Complete HTML (str) for the given pool. Self-contained: inline CSS + one small
    inline script (the ranking's order control), no external resource, no network.

    `sort` is the order the static ranking is rendered in (report.SORTS): the page reads
    correctly without JS from that order, and the control reorders it in place."""
    rows = _order_rows(_rows(pool), sort)
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    rec_section = _rec_section(rows)
    # C8 optimal thinking mode per model (needs wall_time_s on both rows of a
    # pair; rows from before it simply get no marker).
    optimal = R.optimal_by_slug(pool)
    # Conditions in the pool (§C9/C10): any axis with more than one value means the rows
    # were not measured under the same conditions and the page must say so (header chip +
    # banner). The version label cannot tell task sets apart, and the baseline was not
    # recorded at all before 2026-10-14.
    axes = R.condition_axes(pool)
    mixed = R.mixed_axes(pool)
    set_section = _by_set_section(rows)
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
    # locally and on gh-pages): one link, no embed — the page stays offline-first.
    chips.append('<a class="chip" href="compare.html">head-to-head compare →</a>')
    if any(r["retired"] for r in rows):
        chips.append('<span class="chip">gray = retired model (record only)</span>')
    if "task set" in mixed:
        links = " · ".join(f'<a href="#set-{_esc(sig.replace("/", "-"))}">{_esc(sig)}</a>'
                           for sig in R.ordered_signatures(pool))
        chips.append(f'<span class="chip">task sets {links}</span>')
    # §C10: the other two axes have no blocks to link to, so the chip names the values —
    # a reader must see the mix before reading a single row of the table.
    for axis, label in (("engine", "engines"), ("baseline", "baselines")):
        if axis in mixed:
            chips.append(f'<span class="chip">{label} <b>{_esc(" · ".join(axes[axis]))}</b></span>')

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
        if r["retired"]:
            think += ' <span class="badge">retired</span>'
        # data-* feeds the in-page order control (no server round trip): the same values
        # the static order uses. Values, not text, so the JS never parses the display.
        data = (f' data-g="{r["global"]:.4f}" data-tools="{r["sc"]["tools"] or 0:.4f}"'
                f' data-code="{r["sc"]["code"] or 0:.4f}" data-agent="{r["sc"]["agent"] or 0:.4f}"'
                f' data-speed="{r["sc"]["speed_ms"] or 0}" data-setsize="{r["set_size"]}"'
                f' data-set="{_esc(r["set"])}"')
        ranking.append(
            f'<div class="trow{" retired" if r["retired"] else ""}"{data}>'
            f'<div class="pos{cls}">{i + 1}</div>'
            f'<div class="name" title="{_esc(r["name"])}">{_esc(r["name"])}<small>{_esc(r["ts"])} · '
            f'{r["tasks"]["tools"]}+{r["tasks"]["code"]}+{r["tasks"]["agent"]} tasks · '
            f'version {_esc(r["set"])} · excluded code: {r["code_excluded"]}</small></div>'
            f'<div class="gval{cls}">{r["global"]:.2f}{_spread_html((r["spread"] or {}).get("global"))} '
            f'{_set_badge(r)} '
            f'<span class="badge{" strata" if r["engine"] == "strata" else ""}">'
            f'{_esc(r["engine"])} {_esc(r["build"])}</span>{think}</div></div>')

    sortbar = ('<div class="sortbar">'
               '<label for="sortkey">order by</label>'
               f'<select id="sortkey" aria-label="ranking order">'
               + "".join(f'<option value="{k}"{" selected" if k == sort else ""}>{k}</option>'
                         for k in R.SORTS)
               + '</select>'
               '<span class="miss" id="sorted">'
               + _esc("static order: " + sort + " — the control reorders in place, no network")
               + '</span></div>')

    def dim_bars(key, fmt):
        out = []
        for r in sorted(rows, key=lambda x: -(x["sc"][key] or 1e9) if key == "speed_ms" else (x["sc"][key] or 0)):
            v = r["sc"][key]
            # Badge BEFORE the name: .name uses ellipsis (nowrap) so the badge at the end
            # was clipped in narrow columns. title = full name as tooltip.
            think = (f'<span class="badge">think:{_esc(r["thinking"])}</span> '
                     if r["thinking"] != "—" else "")
            if r["retired"]:
                think += '<span class="badge">retired</span> '
            out.append(f'<div class="trow{" retired" if r["retired"] else ""}">'
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
        if r["retired"]:
            think += '<span class="badge">retired</span> '
        matrix_rows.append(f'<tr{" class=\"retired\"" if r["retired"] else ""}><td class="name" title="{_esc(r["name"])}">{think}{_esc(r["name"])}</td>'
                           f'{"".join(cells)}</tr>')
    matrix_head = "".join(f'<th>{dim}:{lang}</th>' for dim in ("code", "agent") for lang in langs)

    details = []
    for r in rows:
        flags = _esc(_sanitize_public(r["flags"])) if r["flags"] else "harness default flags"
        bl = r["code_by_level"]
        by_level_line = ""
        if bl:
            by_level_line = "code by level: " + " · ".join(
                f"{k} {v:.0%}" for k, v in sorted(bl.items())) + "\n"
        think_line = (f"think: {r['thinking']}\n" if r["thinking"] != "—" else "")
        # §C10: the baseline id, next to the per-model flags. The flags themselves are
        # config.SERVER_FLAGS + config.CACHE_FLAGS (docs/SPEC.md §2); the id says which
        # version of them the row ran under ('?' = the row predates the field).
        base_line = f"baseline {r['base']}" + ("" if r["base"] != "?" else " (not recorded)")
        # §C12: the token cap the code tasks ran under (rows before it simply omit the line).
        budget_line = ""
        if r["code_budget"]:
            stored = r["code_budget_stored"]
            extra = (f" · {sum(stored.values())} task(s) at "
                     + ", ".join(f"{cap}" for cap in stored) + " (stored calibration)"
                     ) if stored else ""
            budget_line = f"\ncode budget {r['code_budget']}{extra}"
        # §C13 probes: say out loud what the run hit, instead of leaving it in a receipt.
        probes = []
        if r["code_budget_hits"]:
            probes.append(f"{r['code_budget_hits']} code task(s) at the token cap ({r['code_budget']})")
        if r["agent_empty_replies"]:
            probes.append(f"{r['agent_empty_replies']} agent turn(s) answered empty (turn cap?)")
        if r["tools_capped"]:
            probes.append(f"{r['tools_capped']} tool call(s) at the cap")
        if r["thinking_applied"] is False:
            probes.append("thinking-off requested but the template has no switch"
                          + (f" — {r['thinking_note']}" if r["thinking_note"] else ""))
        probe_line = ("\nprobes: " + " · ".join(probes)) if probes else ""
        details.append(
            f'<details{" class=\"retired\"" if r["retired"] else ""}><summary>{_esc(r["name"])} <span class="badge{" strata" if r["engine"] == "strata" else ""}">'
            f'{_esc(r["engine"])} {_esc(r["build"])}</span>'
            f'{" <span class='badge strata'>★ optimal</span>" if optimal.get(r["slug"]) == r["thinking"] else ""}'
            f'{" <span class=\"badge\">retired</span>" if r["retired"] else ""}'
            f' <span class="miss">{_esc(r["ts"])}</span></summary>'
            f'<pre>{by_level_line}{think_line}excluded code: {r["code_excluded"]}\n'
            f'{base_line}{budget_line}{probe_line}\n{flags}</pre></details>')

    banner = ""
    if len(dates) > 1 or mixed:
        # One clause per mixed axis (§C10): the page names WHICH conditions differ instead
        # of only warning that something differs — the same axis list the CLI footer prints.
        notes = []
        if "task set" in mixed:
            counts = axes["task set"]
            notes.append('<b>task sets</b> ('
                         + _esc(", ".join(f"{sig}: {_rows_phrase(counts[sig])}"
                                          for sig in R.ordered_signatures(pool)))
                         + ") — the version label alone cannot tell them apart")
        if "engine" in mixed:
            notes.append('<b>engine builds</b> ('
                         + _esc(", ".join(f"{v}: {_rows_phrase(n)}"
                                          for v, n in axes["engine"].items()))
                         + ") — the server build is part of the measurement")
        if "baseline" in mixed:
            notes.append('<b>baseline flags</b> ('
                         + _esc(", ".join(f"{v}: {_rows_phrase(n)}"
                                          for v, n in axes["baseline"].items()))
                         + ") — the harness' common flags changed (ADR-0008: KV q4_0 → q8_0); "
                           "'?' is a row measured before the field existed")
        diff = (" — what differs here: " + " · ".join(notes)) if notes else ""
        banner = ('<div class="banner"><b>Mixed conditions.</b> The entries in this pool were '
                  'measured on different dates and the harness evolves (tasks fixed, second '
                  'engine, per-model flags)' + diff
                  + ': a score is comparable only inside one set of conditions; compare with '
                    'care and check <code>docs/MILLORA.md §C7/C9/C10</code> before drawing '
                    'conclusions from the whole table.</div>')

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
</header><main>
{banner}
<div class="kpis">{''.join(f'<div class="kpi"><div class="v">{v}</div><div class="l">{_esc(l)}</div></div>' for l, v in kpis)}</div>

<section>
  <h2>Weighted global</h2>
  {sortbar}
  <div id="ranking">
  {chr(10).join(ranking)}
  </div>
</section>

{set_section}

<div class="grid2">
<section><h2>Code ({_n_tasks(rows, "code")} tasks · 4 languages)</h2>{dim_bars("code", lambda v: f"{v:.0%}")}</section>
<section><h2>Multi-step agent ({_n_tasks(rows, "agent")} tasks)</h2>{dim_bars("agent", lambda v: f"{v:.0%}")}</section>
<section><h2>Tool-calling ({_n_tasks(rows, "tools")} tasks)</h2>{dim_bars("tools", lambda v: f"{v:.0%}")}</section>
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
<script>{_SORT_JS}</script>
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


def write_default_report(pool=None, sort="global"):
    """Render the pool to results/report.html (config.RESULTS_DIR) and return the
    path written. Single owner of the render+path logic: run.py --html calls this
    instead of duplicating it. The pool is read at call time via report.load_pool()
    (the same accumulated source --scoreboard uses) unless one is passed in; `sort`
    is the static order the ranking is rendered in (report.SORTS).
    Returns None when the pool is empty: nothing to render, no file touched."""
    if pool is None:
        pool = R.load_pool()
    if not pool:
        return None
    out = config.RESULTS_DIR / "report.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(pool, sort=sort), encoding="utf-8")
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
    gspread = (R.run_spread(r, config.WEIGHTS, min_speed) or {}).get("global")
    pack = {
        "s": _display_slug(config.slug(r["model"])),
        "t": r.get("thinking") or "—",
        "e": r.get("engine", "llama"),
        "b": str(r.get("server_build") or "?"),
        "d": (r.get("ts") or "")[:10],
        "f": _sanitize_public(r.get("model_config_flags") or ""),
        "v": str(r.get("tasks_version") or "?"),
        "sig": R.task_signature(r),
        "base": R.baseline_id(r),   # §C10: the picker's banner compares it like `sig`
        "env": _sanitize_env(r.get("environment")) or "",
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
    if gspread is not None:  # only a multi-run row carries a spread (kept out of the JSON)
        pack["gs"] = gspread
    return pack


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
            f'<div class="kpi"><div class="v">{p["g"]:.2f}{_spread_html(p.get("gs"))}</div>'
            f'<div class="l">global · {rank} · measured {_esc(p["d"])} · '
            f'set {_esc(p["sig"])}</div></div>'
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


_SORT_JS = """
/* Ranking order control (MILLORA §C9). Reorders the rows already in the page: no fetch,
   no storage, no third party — the page still reads correctly with JS off, from the
   server-side order. Same semantics as the CLI --sort: scores descending, speed
   ascending, 'version' groups by task set (biggest set first) and orders by global
   inside each group. */
(function () {
  var sel = document.getElementById("sortkey");
  var box = document.getElementById("ranking");
  var note = document.getElementById("sorted");
  if (!sel || !box) { return; }
  function num(el, key) {
    var v = el.getAttribute("data-" + key);
    if (v === null || v === "") { return null; }
    var n = parseFloat(v);
    return isNaN(n) ? null : n;
  }
  function key(el, k) {
    var g = num(el, "g");
    g = (g === null ? -1 : g);
    if (k === "speed") {
      var s = num(el, "speed");
      return [s === null || s === 0 ? Infinity : s, -g];
    }
    if (k === "version") {
      var n = num(el, "setsize");
      return [-(n === null ? -1 : n), -g];
    }
    if (k === "global") { return [-g]; }
    var v = num(el, k);
    return [-(v === null ? -1 : v), -g];
  }
  function cmp(a, b, k) {
    var ka = key(a, k), kb = key(b, k);
    for (var i = 0; i < ka.length; i++) {
      if (ka[i] !== kb[i]) { return ka[i] - kb[i]; }
    }
    return 0;
  }
  sel.addEventListener("change", function () {
    var k = sel.value;
    var list = Array.prototype.slice.call(box.querySelectorAll(".trow"));
    list.sort(function (a, b) { return cmp(a, b, k); });
    list.forEach(function (el, i) {
      var pos = el.querySelector(".pos");
      if (pos) {
        pos.textContent = String(i + 1);
        pos.className = "pos" + (i === 0 ? " top" : "");
      }
      var gv = el.querySelector(".gval");
      if (gv) { gv.className = "gval" + (i === 0 ? " top" : ""); }
      box.appendChild(el);
    });
    if (note) {
      note.textContent = "ordered by " + k + " (client-side; the exported page keeps its "
        + "static order)";
    }
  });
})();
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
      + '<div class="kpi"><div class="v">' + p.g.toFixed(2)
      + (p.gs == null ? "" : " <small>±" + Math.round(p.gs * 100) + "</small>") + "</div>"
      + '<div class="l">global · ' + rank + " · measured " + esc(p.d)
      + " · set " + esc(p.sig) + "</div></div>"
      + '<div class="meta"><div class="l">model_config_flags</div><div class="mv">' + flags + "</div></div>"
      + '<div class="meta"><div class="l">environment</div><div class="mv">' + env + "</div></div></section>";
  }
  function axisClauses(a, b) {
    // Mirror of _cmp_axis_clauses in html_report.py — keep both in sync (§C9/C10).
    var out = [];
    if (a.sig !== b.sig) {
      out.push("the task sets differ (" + esc(a.sig) + " vs " + esc(b.sig)
        + " tasks), which the version label alone cannot tell apart");
    }
    if (a.e !== b.e || a.b !== b.b) {
      out.push("the engine builds differ (" + esc(a.e) + " " + esc(a.b) + " vs "
        + esc(b.e) + " " + esc(b.b) + ")");
    }
    if (a.base !== b.base) {
      out.push("the baseline flags differ (" + esc(a.base) + " vs " + esc(b.base) + ")");
    }
    return out;
  }
  function mixedBanner(a, b) {
    var clauses = axisClauses(a, b);
    if (a.d === b.d && a.v === b.v && !clauses.length) return "";
    var diff = "";
    for (var i = 0; i < clauses.length; i++) {
      diff += (i === 0 ? " — and " : ", and ") + clauses[i];
    }
    return '<div class="banner"><b>Mixed conditions.</b> These two rows were not measured under '
      + "identical conditions (" + esc(a.d) + " · tasks " + esc(a.v) + " vs " + esc(b.d)
      + " · tasks " + esc(b.v) + ")" + diff + ": the harness evolves, compare with care"
      + " (docs/MILLORA.md §C7/C9/C10).</div>";
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
  // NOTE: options are server-rendered into the selects (same POOL order as the
  // JSON below), so the picker must NOT append them again — that doubled every
  // entry in JS-enabled browsers.
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


def _cmp_axis_clauses(pa, pb):
    """Which condition axes differ between two packed rows (§C9/C10): the task set, the
    engine build, the baseline flags. `mixedBanner` in _PICKER_JS mirrors this list — the
    JS path must not lose a warning the static page gives, so keep both in sync."""
    out = []
    if pa["sig"] != pb["sig"]:
        out.append('the task sets differ '
                   f'({_esc(pa["sig"])} vs {_esc(pb["sig"])} tasks), which the version label '
                   'alone cannot tell apart')
    if (pa["e"], pa["b"]) != (pb["e"], pb["b"]):
        out.append('the engine builds differ '
                   f'({_esc(pa["e"])} {_esc(pa["b"])} vs {_esc(pb["e"])} {_esc(pb["b"])})')
    if pa["base"] != pb["base"]:
        out.append('the baseline flags differ '
                   f'({_esc(pa["base"])} vs {_esc(pb["base"])})')
    return out


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
    # Picker list: non-retired rows only (retired models stay out of the way,
    # but an explicitly compared retired pair still renders via _find_or_append
    # below), deduped by (slug, think) so stale key variants never double up,
    # ordered by (slug, think): each model's off/on pair adjacent, off first.
    packs = []
    _seen = set()
    for r in pool:
        if _is_retired(r.get("model")):
            continue
        p = _pack(r, ranks.get(R._key_of(r)), len(pool), min_speed)
        if (p["s"], p["t"]) not in _seen:
            _seen.add((p["s"], p["t"]))
            packs.append(p)
    packs.sort(key=lambda p: (p["s"], p["t"]))
    ia, ib = _find_or_append(packs, pa), _find_or_append(packs, pb)

    def _options(selected):
        return "".join(
            f'<option value="{i}"{" selected" if i == selected else ""}>'
            f'{_esc(p["s"])} · think:{_esc(p["t"])}</option>'
            for i, p in enumerate(packs))

    banner = ""
    clauses = _cmp_axis_clauses(pa, pb)
    if pa["d"] != pb["d"] or pa["v"] != pb["v"] or clauses:
        diff = ""
        for i, clause in enumerate(clauses):
            diff += (" — and " if i == 0 else ", and ") + clause
        banner = (f'<div class="banner"><b>Mixed conditions.</b> These two rows were not '
                  f'measured under identical conditions ({_esc(pa["d"])} · tasks {_esc(pa["v"])} '
                  f'vs {_esc(pb["d"])} · tasks {_esc(pb["v"])}){diff}: the harness evolves, '
                  f'compare with care (docs/MILLORA.md §C7/C9/C10).</div>')
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
