#!/usr/bin/env python3
"""Reconstrueix results/models/pool.jsonl des del report publicat a gh-pages
(2026-10-21), quan el pool gitignored es va perdre en el moviment del repo
~/ia/llama/ggufbench -> ~/Documents/CV/projects/ggufbench (i la volta enrere).

El report incrusta cada fila com a .trow amb data-* a 4 decimals: són els
means exactes del pool original. El ± per fila NO es recupera (el spread es
recalcula de les runs individuals, que el HTML no té): les files recuperades
renderitzen sense ±.  Source: results/models/recovery/gh-pages-index-20261021.html
"""
import re, json, sys
from pathlib import Path

SRC = Path(__file__).parent / "gh-pages-index-20261021.html"
OUT = Path(__file__).parent.parent / "pool.jsonl"

html = SRC.read_text()
rows, seen = [], {}
for m in re.finditer(r'<div class="trow( retired)?"([^>]*)>(.*?)</div></div>', html, re.S):
    retired, attrs, body = bool(m.group(1)), m.group(2), m.group(3)
    d = dict(re.findall(r'data-([a-z]+)="([^"]*)"', attrs))
    if not d:
        continue
    slug = (re.search(r'title="([^"]+)"', body) or [None, "?"])[1]
    date_m = re.search(r'<small>(\d{4}-\d{2}-\d{2})', body)
    excl_m = re.search(r'excluded code:\s*(\d+)', body)
    eng_m = re.search(r'<span class="badge">(llama|strata|bmoe) ([^<]+)</span>', body)
    think_m = re.search(r'<span class="badge">think:(on|off)</span>', body)
    row = {
        "model": slug,
        "thinking": think_m.group(1) if think_m else None,
        "tools": {"score": float(d["tools"]), "excluded": 0},
        "code": {"score": float(d["code"]),
                 "excluded": int(excl_m.group(1)) if excl_m else 0},
        "agent": {"score": float(d["agent"]), "excluded": 0},
        "speed": {"speed_ms": int(d["speed"])},
        "tasks_version": d["set"].split("·")[0],
        "task_signature": d["set"].split("·")[1],
        "engine": eng_m.group(1) if eng_m else "llama",
        "server_build": eng_m.group(2) if eng_m else "?",
        "date": date_m.group(1) if date_m else "?",
        "baseline_flags": "recovered from gh-pages 2026-10-21 (means; no per-run spread)",
        "recovered": True,
        "retired": retired,
        "_g": float(d["g"]),
    }
    key = (slug, row["thinking"])
    size = int(d.get("setsize", 0))
    if key not in seen or size > seen[key][0]:
        seen[key] = (size, row)

pool = [r for _, r in seen.values()]
with OUT.open("w") as f:
    for r in pool:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"{len(pool)} files -> {OUT}")
