import statistics

from . import agent as A, client as C, code_extract, executors

SPEED_MAX_TOKENS = 128


def grade_speed(client_mod, tasks):
    results = []
    for task in tasks:
        speed_ms_values = []
        for _ in range(3):
            resp = client_mod.chat([{"role": "user", "content": task["prompt"]}],
                                   max_tokens=SPEED_MAX_TOKENS)
            t = C.parse_timings(resp)
            if t and t.get("completion_ms"):
                speed_ms_values.append(t["completion_ms"])
        avg_speed_ms = statistics.mean(speed_ms_values) if speed_ms_values else 0
        results.append({
            "passed": True,
            "turns": 0,
            "trace": [],
            "speed_ms": int(avg_speed_ms) if avg_speed_ms else 0,
        })
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

def grade_tools(client_mod, tasks, max_turns=6):
    results = []
    for t in tasks:
        resp = client_mod.chat([{"role": "user", "content": t["prompt"]}],
                               tools=t.get("tools", []), max_tokens=128)
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
    score = sum(1 for r in results if r["passed"]) / len(results) if results else 0.0
    return {"passed": score == 1.0, "turns": len(results), "trace": results, "score": score, "by_lang": {}}

def grade_code(client_mod, tasks, max_turns=8):
    results, by_lang = [], {}
    for t in tasks:
        resp = client_mod.chat([{"role": "user", "content": t["prompt"]}], max_tokens=1024)
        code = code_extract.extract(C.first_text(resp), t["lang"])
        r = executors.run(t["lang"], code, t.get("test_code"))
        results.append({"id": t["id"], "passed": r["passed"], "detail": r["output"][:160]})
        by_lang.setdefault(t["lang"], []).append(r["passed"])
    bl = {k: (sum(v) / len(v)) for k, v in by_lang.items()}
    score = sum(1 for r in results if r["passed"]) / len(results) if results else 0.0
    return {"passed": score == 1.0, "turns": len(results), "trace": results, "by_lang": bl, "score": score}

def grade_agent(client_mod, tasks, max_turns=8):
    results, by_lang = [], {}
    for t in tasks:
        r = A.run_agent(client_mod, t, max_turns=t.get("max_turns", max_turns))
        results.append({"id": t["id"], "passed": r["success"], "turns": r["turns"],
                        "detail": f"turns={r['turns']} tool_calls={r['tool_calls']}"})
        by_lang.setdefault(t["lang"], []).append(r["success"])
    bl = {k: (sum(v) / len(v)) for k, v in by_lang.items()}
    score = sum(1 for r in results if r["passed"]) / len(results) if results else 0.0
    return {"passed": score == 1.0, "turns": sum(r["turns"] for r in results), "trace": results, "by_lang": bl, "score": score}