from typing import Any

import statistics
import urllib.error

from . import agent as A, client as C, code_extract, executors, token_budget

SPEED_MAX_TOKENS = 128
# A single generous budget (ADR-0002; R3 thinking_batches: starts at 32768 by the
# reviewer's decision — the expert tasks need it). With fixed seed/temp, max_tokens is a
# ceiling, not a target: it does not penalize concise models (they stop at EOS anyway).
# Environment precondition: every model in the pool must have context for prompt + 32768.
# CONTEXT_FIXED is 32768 (the whole budget, no room for the prompt), so a profile without
# -c does NOT meet this precondition: it needs its own -c or the context audit (SPEC §2).
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


def grade_tools(client_mod, tasks, max_turns=6, on_task=None, runs=1):
    """Grade tool-call tasks across N independent runs.

    Each run makes a fresh model call and grades the result independently.
    Per-task trace entry gains ``runs``: [1, 0, x] where 1=pass, 0=fail, x=excluded.
    Excluded runs (server errors) do NOT count as attempts.
    Aggregate ``passed`` is True only when all non-excluded runs pass AND at least one
    non-excluded run exists.
    Section score = mean over tasks of (non-excluded passes / non-excluded attempts);
    a task with ALL runs excluded is excluded from the mean entirely.
    """
    section_runs = []
    for _run_idx in range(runs):
        results = []
        for t in tasks:
            try:
                resp = client_mod.chat([{"role": "user", "content": t["prompt"]}],
                                       tools=t.get("tools", []), max_tokens=128)
            except _TRANSIENT as e:
                results.append({"id": t["id"], "passed": False, "detail": f"server error: {e}"[:160],
                                "_excluded": True})
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
            results.append({"id": t["id"], "passed": passed, "detail": detail[:160],
                            "_excluded": False})
            if on_task:
                on_task("tools", {"id": t["id"], "passed": passed})
        section_runs.append(results)

    # N==1: byte-compatible — return original trace without aggregation.
    if runs == 1:
        trace = [dict(e) for e in section_runs[0]]
        total_excluded_tasks = sum(1 for e in trace if e.pop("_excluded", False))
        score = statistics.mean([e["passed"] for e in trace]) if trace else 0.0
        result = {"passed": score == 1.0, "turns": len(trace), "trace": trace,
                  "score": score, "by_lang": {}}
        if total_excluded_tasks:
            result["excluded"] = total_excluded_tasks
        return result

    # Aggregate per-task across runs (N>1).
    trace = []
    by_lang = {}  # tools has no by_lang; kept for API compat
    total_excluded_tasks = 0
    scored_tasks = []
    for t in tasks:
        run_outcomes = []
        all_excluded = True
        for sr in section_runs:
            entry = next((e for e in sr if e["id"] == t["id"]), None)
            if entry is None:
                continue
            excluded = entry.pop("_excluded", False)
            if excluded:
                run_outcomes.append("x")
            else:
                run_outcomes.append(1 if entry["passed"] else 0)
                all_excluded = False
        if not run_outcomes:
            continue
        aggregate_passed = all(o != 0 and o != "x" for o in run_outcomes) and len(run_outcomes) > 0
        trace_entry = {k: v for k, v in entry.items() if k != "_excluded"}
        trace_entry["runs"] = run_outcomes
        trace_entry["passed"] = aggregate_passed
        trace_entry["excluded"] = any(o == "x" for o in run_outcomes)
        trace.append(trace_entry)
        if all_excluded:
            total_excluded_tasks += 1
        else:
            scored_tasks.append(trace_entry)

    # Section score = mean over scored tasks of (non-excluded passes / non-excluded attempts).
    def _task_score(te):
        outcomes = te["runs"]
        attempts = [o for o in outcomes if o != "x"]
        passed = sum(1 for o in attempts if o == 1)
        return passed / len(attempts) if attempts else 0.0

    task_scores = [_task_score(te) for te in scored_tasks]
    score = statistics.mean(task_scores) if task_scores else 0.0
    result = {"passed": score == 1.0, "turns": len(results), "trace": trace,
              "score": score, "by_lang": {}, "runs": runs}
    if total_excluded_tasks:
        result["excluded"] = total_excluded_tasks
    return result


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
             thinking=None, runs=1):
    """Grade code tasks across N independent runs.

    Each run makes fresh model calls and grades independently. Per-task trace entry gains
    ``runs``: [1, 0, x] where 1=pass, 0=fail, x=excluded (server error or truncation).
    Excluded runs do NOT count as attempts. Aggregate ``passed`` is True only when all
    non-excluded runs pass AND at least one non-excluded run exists.
    Section score = mean over tasks of (non-excluded passes / non-excluded attempts);
    a task with ALL runs excluded is excluded from the mean entirely.
    """
    section_runs = []
    for _run_idx in range(runs):
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
                                "passed": False, "_excluded": True, "detail": detail})
                if on_task:
                    on_task("code", {"id": t["id"], "lang": t["lang"], "passed": False,
                                     "excluded": True, "detail": detail})
                continue
            out_tokens = (resp.get("usage") or {}).get("completion_tokens")
            if code is None:
                snippet = " ".join(text.split())[:120]
                detail = f"no code block ({t['lang']}, not counted); reply: {snippet}"[:160]
                results.append({"id": t["id"], "lang": t["lang"], "level": t.get("level", "easy"),
                                "passed": False, "_excluded": True, "detail": detail,
                                "out_tokens": out_tokens})
                if on_task:
                    on_task("code", {"id": t["id"], "lang": t["lang"], "passed": False,
                                     "excluded": True, "detail": detail})
                continue
            r = executors.run(t["lang"], code, t.get("test_code"),
                              extra_files=t.get("extra_files"))
            results.append({"id": t["id"], "lang": t["lang"], "level": t.get("level", "easy"),
                            "passed": r["passed"], "_excluded": False, "detail": r["output"][:160],
                            "out_tokens": out_tokens})
            by_lang.setdefault(t["lang"], []).append(r["passed"])
            if on_task:
                on_task("code", {"id": t["id"], "lang": t["lang"], "excluded": False,
                                 "passed": r["passed"], "detail": r["output"]})

        section_runs.append((results, dict(by_lang)))

    # Aggregate per-task across runs.
    trace = []
    total_excluded_tasks = 0
    scored_tasks = []
    by_level = {}
    by_lang = {}
    for t in tasks:
        run_outcomes = []
        all_excluded = True
        for sr_results, _sr_by_lang in section_runs:
            entry = next((e for e in sr_results if e["id"] == t["id"]), None)
            if entry is None:
                continue
            excluded = entry.pop("_excluded", False)
            level = entry.get("level", "easy")
            lang = entry.get("lang", "unknown")
            if excluded:
                run_outcomes.append("x")
            else:
                run_outcomes.append(1 if entry["passed"] else 0)
                by_level.setdefault(level, []).append(entry["passed"])
                by_lang.setdefault(lang, []).append(entry["passed"])
                all_excluded = False
        if not run_outcomes:
            continue
        aggregate_passed = all(o != 0 and o != "x" for o in run_outcomes) and len(run_outcomes) > 0
        trace_entry = {k: v for k, v in entry.items() if k != "_excluded"}
        trace_entry["runs"] = run_outcomes
        trace_entry["passed"] = aggregate_passed
        trace_entry["excluded"] = any(o == "x" for o in run_outcomes)
        trace.append(trace_entry)
        if all_excluded:
            total_excluded_tasks += 1
        else:
            scored_tasks.append(trace_entry)

    # Section score = mean over scored tasks of (non-excluded passes / non-excluded attempts).
    def _task_score(te):
        outcomes = te["runs"]
        attempts = [o for o in outcomes if o != "x"]
        passed = sum(1 for o in attempts if o == 1)
        return passed / len(attempts) if attempts else 0.0

    task_scores = [_task_score(te) for te in scored_tasks]
    score = statistics.mean(task_scores) if task_scores else 0.0
    result = {"passed": score == 1.0, "turns": len(results), "trace": trace,
              "by_lang": {l: round(sum(ps)/len(ps), 2) for l, ps in by_lang.items()},
              "by_level": {l: round(sum(ps)/len(ps), 2) for l, ps in by_level.items()},
              "score": score, "excluded": total_excluded_tasks}
    if runs > 1:
        result["runs"] = runs
    return result


def grade_agent(client_mod, tasks, max_turns=8, on_task=None, runs=1):
    """Grade agent tasks across N independent runs.

    Each run makes fresh model calls and grades independently. Per-task trace entry gains
    ``runs``: [1, 0, x] where 1=pass, 0=fail, x=excluded (server error).
    Excluded runs do NOT count as attempts. Aggregate ``passed`` is True only when all
    non-excluded runs pass AND at least one non-excluded run exists.
    Section score = mean over tasks of (non-excluded passes / non-excluded attempts);
    a task with ALL runs excluded is excluded from the mean entirely.
    """
    section_runs = []
    for _run_idx in range(runs):
        results, by_lang = [], {}
        for t in tasks:
            try:
                r = A.run_agent(client_mod, t, max_turns=t.get("max_turns", max_turns))
            except _TRANSIENT as e:
                results.append({"id": t["id"], "passed": False, "turns": 0,
                                "_excluded": True,
                                "detail": f"server error: {e}"[:160]})
                by_lang.setdefault(t["lang"], []).append(False)
                if on_task:
                    on_task("agent", {"id": t["id"], "lang": t["lang"], "passed": False, "turns": 0})
                continue
            results.append({"id": t["id"], "passed": r["success"], "turns": r["turns"],
                            "_excluded": False,
                            "detail": f"turns={r['turns']} tool_calls={r['tool_calls']}"})
            by_lang.setdefault(t["lang"], []).append(r["success"])
            if on_task:
                on_task("agent", {"id": t["id"], "lang": t["lang"],
                                  "passed": r["success"], "turns": r["turns"]})
        section_runs.append((results, dict(by_lang)))

    # Aggregate per-task across runs.
    trace = []
    total_excluded_tasks = 0
    scored_tasks = []
    for t in tasks:
        run_outcomes = []
        all_excluded = True
        for sr_results, _sr_by_lang in section_runs:
            entry = next((e for e in sr_results if e["id"] == t["id"]), None)
            if entry is None:
                continue
            excluded = entry.pop("_excluded", False)
            if excluded:
                run_outcomes.append("x")
            else:
                run_outcomes.append(1 if entry["passed"] else 0)
                all_excluded = False
        if not run_outcomes:
            continue
        aggregate_passed = all(o != 0 and o != "x" for o in run_outcomes) and len(run_outcomes) > 0
        trace_entry = {k: v for k, v in entry.items() if k != "_excluded"}
        trace_entry["runs"] = run_outcomes
        trace_entry["passed"] = aggregate_passed
        trace_entry["excluded"] = any(o == "x" for o in run_outcomes)
        trace.append(trace_entry)
        if all_excluded:
            total_excluded_tasks += 1
        else:
            scored_tasks.append(trace_entry)

    # Section score = mean over scored tasks of (non-excluded passes / non-excluded attempts).
    def _task_score(te):
        outcomes = te["runs"]
        attempts = [o for o in outcomes if o != "x"]
        passed = sum(1 for o in attempts if o == 1)
        return passed / len(attempts) if attempts else 0.0

    task_scores = [_task_score(te) for te in scored_tasks]
    score = statistics.mean(task_scores) if task_scores else 0.0
    total_turns = sum(
        sum(r["turns"] for r in sr_results)
        for sr_results, _sr_by_lang in section_runs
    ) if section_runs else 0
    result = {"passed": score == 1.0, "turns": total_turns,
              "trace": trace, "by_lang": {}, "score": score}
    if runs > 1:
        result["runs"] = runs
    return result
