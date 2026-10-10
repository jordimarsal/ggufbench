"""Informe HTML del scoreboard -> results/report.html.

Pàgina única AUTO-CONTINGUDA: CSS inline, zero JS, zero dependències, zero xarxa
(es pot obrir amb doble clic o `xdg-open` sense connexió). Les puntuacions les
calculen les funcions reals del harness (report._scores / report._global_score
amb config.WEIGHTS) perquè aquesta pàgina i el CLI diguin sempre el mateix.

Ús:  python3 -m benchmark.html_report   (escriu results/report.html i imprimeix la ruta)
"""

import datetime
import html as _html
import subprocess

from . import config, report as R


def _esc(s):
    return _html.escape(str(s), quote=True)


def _gpu_chips():
    """Noms de GPU (únics, ordenats) per al capçaler; [] si no hi ha nvidia-smi."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5)
        return sorted({line.split(",")[0].strip()
                       for line in out.stdout.splitlines() if line.strip()})
    except (OSError, subprocess.TimeoutExpired):
        return []


def _rows(pool):
    """Una fila per model, ordenada per global desc. Mateixa matemàtica que el CLI."""
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
            "thinking": r.get("thinking") or "—",  # R4: legacy sense clau
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
.bar{position:relative;height:16px;background:var(--card2);border:1px solid var(--border);
  border-radius:6px;overflow:hidden;min-width:110px}
.fill{height:100%;background:linear-gradient(90deg,var(--primary),var(--primary2))}
.fill.acc{background:linear-gradient(90deg,#b45309,var(--accent))}
.fill.good{background:linear-gradient(90deg,#0f766e,var(--good))}
.rank{display:grid;grid-template-columns:22px minmax(140px,260px) 1fr 120px;gap:10px;
  align-items:center;padding:7px 4px;border-bottom:1px solid var(--border)}
.rank:last-child{border-bottom:0}
.rank:hover{background:rgba(59,130,246,.07)}
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
  .fill{transition:width .25s ease}
  tr:hover td,.rank:hover,summary:hover{transition:background .18s ease}
}
@media print{header{position:static}body{background:#fff;color:#000}}
"""


def render(pool):
    """HTML complet (str) per al pool donat. Sense JS, sense recursos externs."""
    rows = _rows(pool)
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    gpus = _gpu_chips()
    w = config.WEIGHTS
    top = rows[0]["global"] if rows else 1
    dates = sorted({r["ts"] for r in rows if r["ts"]})
    langs = ["python", "bash", "java", "typescript"]

    chips = [f'<span class="chip"><b>{len(rows)}</b> models</span>',
             f'<span class="chip"><b>{sum(max(r["tasks"].values()) for r in rows)}</b> tasques</span>',
             '<span class="chip">pesos <b>tools {:.2f} · code {:.2f} · agent {:.2f} · speed {:.2f}</b></span>'.format(
                 w["tools"], w["code"], w["agent"], w["speed"])]
    chips += [f'<span class="chip"><b>{_esc(g)}</b></span>' for g in gpus]
    if len(dates) > 1:
        chips.append(f'<span class="chip">mesurat <b>{_esc(dates[0])} → {_esc(dates[-1])}</b></span>')

    kpis = [("Millor global", f"{rows[0]['global']:.2f}" if rows else "—"),
            ("Més ràpid (gen)", f"{max((r['sc']['gen_tps'] for r in rows), default=0):.0f} t/s"),
            ("Latència mínima", f"{min((r['sc']['speed_ms'] for r in rows if r['sc']['speed_ms']), default=0)} ms"),
            ("Model més nou", _esc(dates[-1]) if dates else "—")]

    ranking = []
    for i, r in enumerate(rows):
        cls = " top" if i == 0 else ""
        width = (r["global"] / top * 100) if top else 0
        think = (f' <span class="badge">think:{_esc(r["thinking"])}</span>'
                 if r["thinking"] != "—" else "")
        ranking.append(
            f'<div class="rank"><div class="pos{cls}">{i + 1}</div>'
            f'<div class="name">{_esc(r["name"])}<small>{_esc(r["ts"])} · {r["tasks"]["tools"]}+'
            f'{r["tasks"]["code"]}+{r["tasks"]["agent"]} tasques · excloses code: {r["code_excluded"]}</small></div>'
            f'<div class="bar"><div class="fill{cls}" style="width:{width:.1f}%"></div></div>'
            f'<div class="gval{cls}">{r["global"]:.2f} <span class="badge{" strata" if r["engine"] == "strata" else ""}">'
            f'{_esc(r["engine"])} {_esc(r["build"])}</span>{think}</div></div>')

    def dim_bars(key, fmt, lower_is_better=False, acc=False):
        best = min((r["sc"][key] for r in rows if r["sc"][key]), default=0) if lower_is_better \
            else max((r["sc"][key] for r in rows), default=1)
        out = []
        for r in sorted(rows, key=lambda x: x["sc"][key] if not lower_is_better else -(x["sc"][key] or 1e9)):
            v = r["sc"][key]
            pct = (best / v * 100 if v else 0) if lower_is_better else (v / best * 100 if best else 0)
            out.append(f'<div class="rank"><div class="name">{_esc(r["name"])}</div>'
                       f'<div class="bar"><div class="fill{" acc" if acc else ""}" style="width:{pct:.1f}%"></div></div>'
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
                    alpha = 0.10 + 0.55 * v
                    color = "#0b1220" if v > 0.55 else "inherit"
                    cells.append(f'<td><span class="heat" style="background:rgba(52,211,153,{alpha:.2f};'
                                 f'color:{color}">{v:.2f}</span></td>')
        matrix_rows.append(f'<tr><td class="name">{_esc(r["name"])}</td>{"".join(cells)}</tr>')
    matrix_head = "".join(f'<th>{dim}:{lang}</th>' for dim in ("code", "agent") for lang in langs)

    details = []
    for r in rows:
        flags = _esc(r["flags"]) if r["flags"] else "flags per defecte del harness"
        bl = r["code_by_level"]
        by_level_line = ""
        if bl:
            by_level_line = "code per nivell: " + " · ".join(
                f"{k} {v:.0%}" for k, v in sorted(bl.items())) + "\n"
        think_line = (f"think: {r['thinking']}\n" if r["thinking"] != "—" else "")
        details.append(
            f'<details><summary>{_esc(r["name"])} <span class="badge{" strata" if r["engine"] == "strata" else ""}">'
            f'{_esc(r["engine"])} {_esc(r["build"])}</span> <span class="miss">{_esc(r["ts"])}</span></summary>'
            f'<pre>{by_level_line}{think_line}excloses code: {r["code_excluded"]}\n{flags}</pre></details>')

    banner = ""
    if len(dates) > 1:
        banner = ('<div class="banner"><b>Condicions barrejades.</b> Les entrades d\'aquest pool es van '
                  'mesurar en dates diferents i el harness evoluciona (tasques arreglades, segon motor, '
                  'flags per model): compara amb cura i revisa <code>docs/MILLORA.md §C7</code> abans de '
                  'treure conclusions de la taula sencera.</div>')

    return f"""<!doctype html>
<html lang="ca">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bench Board — benchmark local de models</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <h1>Bench Board <small>· benchmark local de models per a opencode</small></h1>
  <div class="sub">Generat {_esc(now)} · puntuacions calculades amb les funcions del harness (mateixa matemàtica que el CLI)</div>
  <div class="chips">{''.join(chips)}</div>
</header>
<main>
{banner}
<div class="kpis">{''.join(f'<div class="kpi"><div class="v">{v}</div><div class="l">{_esc(l)}</div></div>' for l, v in kpis)}</div>

<section>
  <h2>Global ponderat</h2>
  {chr(10).join(ranking)}
</section>

<div class="grid2">
<section><h2>Codi (32 tasques · 4 llenguatges)</h2>{dim_bars("code", lambda v: f"{v:.0%}")}</section>
<section><h2>Agent multi-pas (24 tasques)</h2>{dim_bars("agent", lambda v: f"{v:.0%}")}</section>
<section><h2>Tool-calling (8 tasques)</h2>{dim_bars("tools", lambda v: f"{v:.0%}")}</section>
<section><h2>Velocitat (ms de generació · menys és millor)</h2>{dim_bars("speed_ms", lambda v: f"{v} ms", lower_is_better=True, acc=True)}</section>
</div>

<section>
  <h2>Tokens per segon</h2>
  <div class="grid2">
    <div><h2>gen (output)</h2>{dim_bars("gen_tps", lambda v: f"{v:.0f} t/s", acc=True)}</div>
    <div><h2>prompt (input)</h2>{dim_bars("prompt_tps", lambda v: f"{v:.0f} t/s")}</div>
  </div>
</section>

<section>
  <h2>Per llenguatge (code / agent)</h2>
  <table><thead><tr><th>Model</th>{matrix_head}</tr></thead>
  <tbody>{''.join(matrix_rows)}</tbody></table>
</section>

<section>
  <h2>Condicions per model</h2>
  {''.join(details)}
</section>
</main>
<footer>
  Regenera amb <code>python3 -m benchmark.html_report</code> des de l'arrel del workspace.
  Ranking relatiu en aquest hardware i amb aquest harness: no és comparable en absolut amb
  benchmarks públics (HumanEval, BFCL, SWE-bench). Més: <code>docs/SPEC.md</code> ·
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
