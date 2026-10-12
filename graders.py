from typing import Any

import statistics
import urllib.error

from . import agent as A, client as C, code_extract, executors, token_budget

SPEED_MAX_TOKENS = 128
# A single generous budget (ADR-0002; R3 thinking_batches: starts at 32768 by the
# reviewer's decision — the expert tasks need it). With fixed seed/temp, max_tokens is a
# ceiling, not a target: it does not penalize concise models (they stop at EOS anyway).
# Environment precondition: every model in the pool must have context for prompt + 32768
# (profiles without -c fall back to CONTEXT_FIXED=16384 and would not fit; see T4 in impl).
# Output tokens are recorded in the trace (out_tokens) as an efficiency
# metric, not a penalty.
CODE_MAX_TOKENS = 32768
CODE_LADDER = [CODE_MAX_TOKENS]

# Transient server/network errors (500, timeouts, dropped connection...).
# Isolate them per task: a 500 response must only fail that task, not abort the whole run.
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
                pass  # sample discarded; another one can compensate
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


def _args_equal(got: Any, expected: Any) -> bool:
    """Compare two JSON-parsed arguments for equality.

    Both ``got`` and ``expected`` are values extracted from parsed JSON
    (strings, numbers, lists, dicts, booleans, or ``None``). The function
    returns ``True`` when they match via Python's ``==``, handling the
    common case where one side is ``None`` (no argument present) and the
    other is not.
    """
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
            # 'arguments' absent in EXPECTED -> only the tool name is checked:
            # the task author does not fix them (get_env asks for 'any variable').
            # Requiring them absent was impossible when the schema marks them required and
            # no model had ever passed it. 'arguments': {} does require a
            # call with no arguments.
            passed = (got is not None and got.get("name") == exp.get("name")
                      and ("arguments" not in exp
                           or _args_equal(got.get("arguments"), exp["arguments"])))
            detail = f"got={got} expected={exp}"
        results.append({"id": t["id"], "passed": passed, "detail": detail[:160]})
        if on_task:
            on_task("tools", {"id": t["id"], "passed": passed})
    score = sum(1 for r in results if r["passed"]) / len(results) if results else 0.0
    return {"passed": score == 1.0, "turns": len(results), "trace": results, "score": score, "by_lang": {}}


def _code_system_prompt(lang):
    """Format instruction shared by all code tasks. Centralized here
    so it does not have to be repeated in every task file and to give all models
    the same conditions (we test 'can implement the function?', not 'guesses
    our extraction format')."""
    extra = ""
    if lang == "typescript":
        extra = " You MUST export it (e.g. `export function add(...)`)."
    elif lang == "java":
        extra = " Provide the full class with the required method."
    return ("Reply with ONLY a single fenced ```{l} code block implementing the requested "
            "function. No prose, no explanation, no text outside the code block.{e}"
            ).format(l=lang, e=extra)


def code_timeout(budget, gen_tps):
    """Max time (s) for one code chat attempt: the real budget is in tokens
    (same for all models) and the clock is only kept as an anti-hang guard, derived
    from the model's measured speed (ADR-0001). Without gen_tps -> fixed 90 s.
    The ceiling covers 32768 tokens at the slowest model observed (44 t/s -> 991 s)."""
    if not gen_tps:
        return 90
    return int(min(1000, max(90, 60 + (budget / gen_tps) * 1.25)))


def grade_code(client_mod, tasks, max_turns=8, on_task=None, model_slug=None, gen_tps=None,
             thinking=None):
    results, by_lang = [], {}
    for t in tasks:
        stored = token_budget.get("code", model_slug, thinking, t["lang"], t["id"])
        budgets = [stored] if stored else CODE_LADDER
        msgs = [{"role": "system", "content": _code_system_prompt(t["lang"])},
                {"role": "user", "content": t["prompt"]}]
        text, code, server_err = "", None, None
        for budget in budgets:
            try:
                resp = client_mod.chat(msgs, max_tokens=budget,
                                       timeout=code_timeout(budget, gen_tps))
            except _TRANSIENT as e:
                server_err = str(e)
                break
            text = C.first_text(resp)
            code = code_extract.extract(text, t["lang"])
            if code is not None:
                break
        # Calibration (once only): if there was no stored budget and no
        # server error, we persist the resolved one — as long as it differs from
        # the default (if it resolves with the default, nothing to record).
        if not stored and not server_err:
            resolved = budget if code is not None else budgets[-1]
            if resolved != CODE_MAX_TOKENS:
                token_budget.put("code", model_slug, thinking, t["lang"], t["id"], resolved)
        if server_err:
            detail = f"server error: {server_err}"[:160]
            results.append({"id": t["id"], "lang": t["lang"], "level": t.get("level", "easy"),
                            "passed": False, "excluded": True, "detail": detail})
            if on_task:
                on_task("code", {"id": t["id"], "lang": t["lang"], "passed": False,
                                 "excluded": True, "detail": detail})
            continue
        out_tokens = (resp.get("usage") or {}).get("completion_tokens")
        if code is None:
            # Truncated output or a format with no extractable block: this does NOT
            # demonstrate the model's ability, so it is excluded from the score
            # (marked excluded=True).
            snippet = " ".join(text.split())[:120]
            detail = f"no code block ({t['lang']}, not counted); reply: {snippet}"[:160]
            results.append({"id": t["id"], "lang": t["lang"], "level": t.get("level", "easy"),
                            "passed": False, "excluded": True, "detail": detail,
                            "out_tokens": out_tokens})
            if on_task:
                on_task("code", {"id": t["id"], "lang": t["lang"], "passed": False,
                                 "excluded": True, "detail": detail})
            continue
        r = executors.run(t["lang"], code, t.get("test_code"),
                          extra_files=t.get("extra_files"))
        results.append({"id": t["id"], "lang": t["lang"], "level": t.get("level", "easy"),
                        "passed": r["passed"], "excluded": False, "detail": r["output"][:160],
                        "out_tokens": out_tokens})
        by_lang.setdefault(t["lang"], []).append(r["passed"])
        if on_task:
            on_task("code", {"id": t["id"], "lang": t["lang"], "excluded": False,
                             "passed": r["passed"], "detail": r["output"]})
    # Score over the tasks that DID produce executable code: truncations
    # and server errors (excluded=True) count neither in the numerator nor the denominator.
    # by_level (hard_code_tier R4): easy/hard breakdown over the same scored tasks.
    scored = [r for r in results if not r["excluded"]]
    bl = {k: (sum(v) / len(v)) for k, v in by_lang.items()}
    by_level = {}
    for r in scored:
        by_level.setdefault(r["level"], []).append(r["passed"])
    blv = {k: sum(v) / len(v) for k, v in by_level.items()}
    score = sum(1 for r in scored if r["passed"]) / len(scored) if scored else 0.0
    return {"passed": score == 1.0, "turns": len(results), "trace": results,
            "by_lang": bl, "by_level": blv, "score": score,
            "excluded": len(results) - len(scored)}


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
