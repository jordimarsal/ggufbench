import json
import datetime
import os

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
    # Dedup per slug mantenint l'última ocurrència (la més recent: el fitxer és
    # cronològic). Aïsla entrades duplicades llegades de l'època append-only.
    by_slug = {}
    with open(POOL_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            by_slug[_slug_of(r)] = r
    return list(by_slug.values())


def _model_stem(model_field):
    """Nom del fitxer del model sense camí ni l'extensió (.gguf/.GGUF).
    'models/foo.gguf' -> 'foo'; 'foo' -> 'foo'. Robust davant noms amb punts interns
    ('Qwen3.8', 'Ornith-1.5'): només s'estira l'extensió del model, mai un punt del nom.
    Permet identificar el mateix model encara que el camp 'model' s'emmagitzema com a
    camí relatiu o absolut, i per oblid-lo pel nom net."""
    base = os.path.basename(str(model_field))
    for ext in (".gguf", ".GGUF"):
        if base.endswith(ext):
            return base[:-len(ext)]
    return base


def _forget_matches(r, term):
    # Encaixa pel slug (com abans) O pel nom del fitxer, perquè el camp 'model' pot estar
    # emmagatzemat com a camí relatiu/absolut mentre l'usuari passi el nom net.
    return (config.slug(r["model"]) == config.slug(term)
            or _model_stem(r["model"]) == _model_stem(term))


def forget(model_name):
    """Borra del pool totes les entrades que coincideixen amb ``model_name``.

    Retorna el nombre d'entrades borrades (0 si no hi ha cap coincidència), de manera
    que el caller pot informar correctament l'usuari. Abans retornava ``None`` i feia
    silenci quan no trobava res, cosa que feia que el CLI digués falsament "esborrat"."""
    if not POOL_FILE.exists():
        return 0
    pool = load_pool()
    keep = [r for r in pool if not _forget_matches(r, model_name)]
    removed = len(pool) - len(keep)
    if removed:
        with open(POOL_FILE, "w") as f:
            for r in keep:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return removed


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


def _fmt_pct(x):
    """Formata un percentatge (0..1 -> %) o '—' si no hi ha dada."""
    return f"{x:.0%}" if x is not None else "—"


def _render_global_rows(pool, weights, title):
    """Taula 1 + secció de tokens (SPEC 4.6). Una fila per model amb el score de cada
    dimensió i un global ponderat, ordenat de millor a pitjor."""
    # Coerceix None -> 0 perquè un model sense velocitat (run parcial) no tombi el render.
    speed_values = [int((r.get("speed") or {}).get("speed_ms") or 0) for r in pool]
    min_speed = min((v for v in speed_values if v > 0), default=0)
    rows = []
    for r in pool:
        sc = _scores(r)
        rows.append((config.slug(r["model"]), sc, _global_score(r, weights, min_speed)))
    rows.sort(key=lambda x: x[2], reverse=True)
    nw = max((len(r[0]) for r in rows), default=5)
    header = f"{'MODEL':{nw}} {'tools':>6} {'code':>6} {'agent':>6} {'speed':>9} {'GLOBAL':>7}"
    out = [f"=== {title} ===", header, "-" * len(header)]
    for name, sc, g in rows:
        sp = f"{sc['speed_ms']}ms" if sc["speed_ms"] else "—"
        out.append(f"{name:{nw}} {sc['tools']:>5.0%} {sc['code']:>5.0%} "
                   f"{sc['agent']:>5.0%} {sp:>9} {g:>7.2f}")
    # Epígraf de tokens per segon (output i input).
    out.append("")
    out.append("=== Tokens per segon (t/s) ===")
    theader = f"{'MODEL':{nw}} {'gen (out)':>10} {'prompt (in)':>12}"
    out.append(theader)
    out.append("-" * len(theader))
    for name, sc, g in rows:
        gen = f"{sc['gen_tps']:.1f}" if sc["gen_tps"] else "—"
        prom = f"{sc['prompt_tps']:.1f}" if sc["prompt_tps"] else "—"
        out.append(f"{name:40.40} {gen:>10} {prom:>12}")
    return out


def _render_tasks(pool):
    """Taula 3 — detall per tasca (SPEC 4.6). Una fila per (model, dimensió, tasca).
    Tolerant: un model sense dimensió o una dimensió sense trace no falla."""
    nw = max((len(config.slug(r["model"])) for r in pool), default=5)
    header = f"{'MODEL':{nw}} {'DIM':8} {'LANG':12} {'TASK':20} {'OK':4} DETALL"
    out = ["", "=== Detall per tasca ===", header, "-" * len(header)]
    for r in pool:
        name = config.slug(r["model"])
        for dim in ("tools", "code", "agent"):
            d = r.get(dim) or {}
            for t in d.get("trace") or []:
                lang = str(t.get("lang") or "—")[:11]
                tid = str(t.get("id") or "")[:20]
                mark = "✓" if t.get("passed") else "✗"
                detail = " ".join(str(t.get("detail") or "").split())[:30]
                if t.get("excluded"):
                    detail += " [exclo]"
                out.append(f"{name:40.40} {dim:8} {lang:12} {tid:20} {mark} {detail}")
    return out


def _render_by_lang(pool):
    """Taula 2 — desglossament per llenguatge de code/agent (SPEC 4.6). Cel·la '—'
    quan no hi ha tasques d'aquell idioma per aquella dimensió."""
    langs = ["python", "bash", "java", "typescript"]
    dims = ["code", "agent"]
    nw = max((len(config.slug(r["model"])) for r in pool), default=5)
    header = f"{'MODEL':{nw}}"
    for dim in dims:
        for lang in langs:
            header += f" {dim}:{lang:>11}"
    out = ["", "=== Per llenguatge (code/agent) ===", header, "-" * len(header)]
    for r in pool:
        name = config.slug(r["model"])
        row = f"{name:{nw}}"
        for dim in dims:
            bl = (r.get(dim) or {}).get("by_lang") or {}
            for lang in langs:
                row += f" {_fmt_pct(bl.get(lang)):>11}"
        out.append(row)
    return out


def render(pool, weights, title="Benchmark Results", level="default", show_tasks=False):
    """Marcador per model amb granularitat descomposta en eixos independents (SPEC 4.6):

    - ``level='default'`` : Taula 1 (scores globals) + secció de tokens.
    - ``level='info'``    : Taula 1 + Taula 3 (detall per tasca). Respon "en què un
      model és bo/malament".
    - ``level='verbose'`` : Taula 1 + Taula 2 (per llenguatge). NO inclou el detall
      de tasques; és el nivell més fi sense per-tasca.

    El detall de tasques (Taula 3) es mostra si `show_tasks=True` (via `--task`) o si
    el nivell ja l'inclou (`info`). Així `--verbose` no el mai sol i cal `--task` per
    veure'l; les dues opcions es composen: es pot fer servir `--verbose` (per-llenguatge)
    juntament amb `--task`. Les dimensions o les tasques que faltin a un model (runs
    parcials, models sense encara aquesta granularitat) no provoquen errors: totes
    les cells es calculen amb valors per defecte."""
    if not pool:
        return "(no results in pool)"
    out = _render_global_rows(pool, weights, title)
    if level == "verbose":
        out += _render_by_lang(pool)
    if show_tasks or level == "info":
        out += _render_tasks(pool)
    return "\n".join(out)
