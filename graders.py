import statistics
import urllib.error

from . import agent as A, client as C, code_extract, executors

SPEED_MAX_TOKENS = 128
CODE_MAX_TOKENS = 2048

# Errors transients del servidor/xarxa (500, timeouts, connexió tombada...).
# Aïllar-los per tasca: una resposta 500 només ha de fallar aquella tasca, no avortar tota la run.
_TRANSIENT = (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError)


def grade_speed(client_mod, tasks, on_task=None):
    results = []
    for task in tasks:
        speed_ms_values = []
        for _ in range(3):
            try:
                resp = client_mod.chat([{"role": "user", "content": task["prompt"]}],
                                       max_tokens=SPEED_MAX_TOKENS)
                t = C.parse_timings(resp)
                if t and t.get("completion_ms"):
                    speed_ms_values.append(t["completion_ms"])
            except _TRANSIENT:
                pass  # mostra descartada; una altra ho pot compensar
        avg_speed_ms = statistics.mean(speed_ms_values) if speed_ms_values else 0
        results.append({
            "passed": True,
            "turns": 0,
            "trace": [],
            "speed_ms": int(avg_speed_ms) if avg_speed_ms else 0,
        })
        if on_task:
            on_task("speed", {"id": task["id"], "ms": results[-1]["speed_ms"]})
    if results and any(r["speed_ms"] for r in results):
        total_speed_ms = statistics.mean(r["speed_ms"] for r in results if r["speed_ms"])
    else:
        total_speed_ms = 0
    return {"passed": True, "turns": 0, "trace": results,
            "speed_ms": int(total_speed_ms) if total_speed_ms else 0}


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


def grade_code(client_mod, tasks, max_turns=8, on_task=None):
    results, by_lang = [], {}
    for t in tasks:
        try:
            resp = client_mod.chat([{"role": "user", "content": t["prompt"]}], max_tokens=CODE_MAX_TOKENS)
        except _TRANSIENT as e:
            results.append({"id": t["id"], "passed": False, "detail": f"server error: {e}"[:160]})
            by_lang.setdefault(t["lang"], []).append(False)
            if on_task:
                on_task("code", {"id": t["id"], "lang": t["lang"], "passed": False, "detail": f"server error: {e}"})
            continue
        text = C.first_text(resp)
        code = code_extract.extract(text, t["lang"])
        if code is None:
            snippet = " ".join(text.split())[:120]
            detail = f"no code block ({t['lang']}); reply: {snippet}"
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
