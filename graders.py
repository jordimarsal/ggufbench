import statistics
import urllib.error

from . import agent as A, client as C, code_extract, executors, token_budget

SPEED_MAX_TOKENS = 128
CODE_MAX_TOKENS = 2048
# Escalat de pressupost quan una tasca de codi no extreu bloc (model truncat).
CODE_LADDER = [CODE_MAX_TOKENS, 4096, 8192]

# Errors transients del servidor/xarxa (500, timeouts, connexió tombada...).
# Aïllar-los per tasca: una resposta 500 només ha de fallar aquella tasca, no avortar tota la run.
_TRANSIENT = (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError)


def grade_speed(client_mod, tasks, on_task=None):
    results = []
    for task in tasks:
        speed_ms_values, gen_tps_values, prompt_tps_values = [], [], []
        for _ in range(3):
            try:
                resp = client_mod.chat([{"role": "user", "content": task["prompt"]}],
                                       max_tokens=SPEED_MAX_TOKENS)
                t = C.parse_timings(resp)
                if not t:
                    continue
                if t.get("completion_ms"):
                    speed_ms_values.append(t["completion_ms"])
                if t.get("gen_tps"):
                    gen_tps_values.append(t["gen_tps"])
                if t.get("prompt_tps"):
                    prompt_tps_values.append(t["prompt_tps"])
            except _TRANSIENT:
                pass  # mostra descartada; una altra ho pot compensar
        avg = lambda xs: statistics.mean(xs) if xs else 0
        entry = {
            "passed": True,
            "turns": 0,
            "trace": [],
            "speed_ms": int(avg(speed_ms_values)) if speed_ms_values else 0,
            "gen_tps": round(avg(gen_tps_values), 1) if gen_tps_values else 0,
            "prompt_tps": round(avg(prompt_tps_values), 1) if prompt_tps_values else 0,
        }
        results.append(entry)
        if on_task:
            on_task("speed", {"id": task["id"], "ms": entry["speed_ms"], "gen_tps": entry["gen_tps"]})
    ms_vals = [r["speed_ms"] for r in results if r["speed_ms"]]
    total_speed_ms = statistics.mean(ms_vals) if ms_vals else 0
    def _mean_field(field):
        vals = [r[field] for r in results if r.get(field)]
        return round(statistics.mean(vals), 1) if vals else 0
    return {"passed": True, "turns": 0, "trace": results,
            "speed_ms": int(total_speed_ms) if total_speed_ms else 0,
            "gen_tps": _mean_field("gen_tps"),
            "prompt_tps": _mean_field("prompt_tps")}


def _args_equal(got, expected):
    if expected is None:
        return got is None
    if got is None:
        return False
    return got == expected


def grade_tools(client_mod, tasks, max_turns=6, on_task=None):
    results = []
    for t in tasks:
        try:
            resp = client_mod.chat([{"role": "user", "content": t["prompt"]}],
                                   tools=t.get("tools", []), max_tokens=128)
        except _TRANSIENT as e:
            results.append({"id": t["id"], "passed": False, "detail": f"server error: {e}"[:160]})
            if on_task:
                on_task("tools", {"id": t["id"], "passed": False})
            continue
        got = C.extract_tool_call(resp)
        exp = t.get("expected")
        if exp is None:
            passed = got is None
            detail = "correctly did not call a tool" if passed else f"unexpected call: {got}"
        else:
            passed = (got is not None and got.get("name") == exp.get("name")
                      and _args_equal(got.get("arguments"), exp.get("arguments")))
            detail = f"got={got} expected={exp}"
        results.append({"id": t["id"], "passed": passed, "detail": detail[:160]})
        if on_task:
            on_task("tools", {"id": t["id"], "passed": passed})
    score = sum(1 for r in results if r["passed"]) / len(results) if results else 0.0
    return {"passed": score == 1.0, "turns": len(results), "trace": results, "score": score, "by_lang": {}}


def grade_code(client_mod, tasks, max_turns=8, on_task=None, model_slug=None):
    results, by_lang = [], {}
    for t in tasks:
        stored = token_budget.get("code", model_slug, t["lang"], t["id"])
        budgets = [stored] if stored else CODE_LADDER
        text, code, server_err = "", None, None
        for budget in budgets:
            try:
                resp = client_mod.chat([{"role": "user", "content": t["prompt"]}], max_tokens=budget)
            except _TRANSIENT as e:
                server_err = str(e)
                break
            text = C.first_text(resp)
            code = code_extract.extract(text, t["lang"])
            if code is not None:
                break
        # Calibratge (una sola vegada): si no hi havia pressupost guardat i no hi ha
        # hagut error de servidor, persistim el resolt — sempre que difereixi del
        # default (si passa amb el default no cal anotar res).
        if not stored and not server_err:
            resolved = budget if code is not None else budgets[-1]
            if resolved != CODE_MAX_TOKENS:
                token_budget.put("code", model_slug, t["lang"], t["id"], resolved)
        if server_err:
            detail = f"server error: {server_err}"[:160]
            results.append({"id": t["id"], "passed": False, "detail": detail})
            by_lang.setdefault(t["lang"], []).append(False)
            if on_task:
                on_task("code", {"id": t["id"], "lang": t["lang"], "passed": False, "detail": detail})
            continue
        if code is None:
            snippet = " ".join(text.split())[:120]
            detail = f"no code block ({t['lang']}, fins a {budgets[-1]} tok); reply: {snippet}"
            results.append({"id": t["id"], "passed": False, "detail": detail[:160]})
            by_lang.setdefault(t["lang"], []).append(False)
            if on_task:
                on_task("code", {"id": t["id"], "lang": t["lang"], "passed": False, "detail": detail})
            continue
        r = executors.run(t["lang"], code, t.get("test_code"))
        results.append({"id": t["id"], "passed": r["passed"], "detail": r["output"][:160]})
        by_lang.setdefault(t["lang"], []).append(r["passed"])
        if on_task:
            on_task("code", {"id": t["id"], "lang": t["lang"],
                             "passed": r["passed"], "detail": r["output"]})
    bl = {k: (sum(v) / len(v)) for k, v in by_lang.items()}
    score = sum(1 for r in results if r["passed"]) / len(results) if results else 0.0
    return {"passed": score == 1.0, "turns": len(results), "trace": results, "by_lang": bl, "score": score}


def grade_agent(client_mod, tasks, max_turns=8, on_task=None):
    results, by_lang = [], {}
    for t in tasks:
        try:
            r = A.run_agent(client_mod, t, max_turns=t.get("max_turns", max_turns))
        except _TRANSIENT as e:
            results.append({"id": t["id"], "passed": False, "turns": 0,
                            "detail": f"server error: {e}"[:160]})
            by_lang.setdefault(t["lang"], []).append(False)
            if on_task:
                on_task("agent", {"id": t["id"], "lang": t["lang"], "passed": False, "turns": 0})
            continue
        results.append({"id": t["id"], "passed": r["success"], "turns": r["turns"],
                        "detail": f"turns={r['turns']} tool_calls={r['tool_calls']}"})
        by_lang.setdefault(t["lang"], []).append(r["success"])
        if on_task:
            on_task("agent", {"id": t["id"], "lang": t["lang"],
                              "passed": r["success"], "turns": r["turns"]})
    bl = {k: (sum(v) / len(v)) for k, v in by_lang.items()}
    score = sum(1 for r in results if r["passed"]) / len(results) if results else 0.0
    return {"passed": score == 1.0, "turns": sum(r["turns"] for r in results), "trace": results, "by_lang": bl, "score": score}
