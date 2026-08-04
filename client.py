import json
import urllib.error
import urllib.request

from . import config


def chat(messages, tools=None, tool_choice=None, max_tokens=256,
         base_url="http://127.0.0.1:8999", timeout=60):
    body = {"messages": messages, "max_tokens": max_tokens,
            "temperature": config.TEMPERATURE, "seed": config.SEED}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = tool_choice or "auto"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(f"{base_url}/v1/chat/completions", data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def parse_timings(resp):
    t = (resp or {}).get("timings") or {}
    if not t:
        return None
    tps = t.get("predicted_per_second")
    if tps is None:
        n = t.get("predicted_n") or (resp.get("usage", {}) or {}).get("completion_tokens") or 0
        ms = t.get("predicted_ms") or 0
        tps = (n / (ms / 1000.0)) if (n and ms) else None
    ptps = t.get("prompt_per_second")
    p_ms = t.get("prompt_ms")
    c_ms = t.get("predicted_ms")
    return {"gen_tps": tps, "prompt_tps": ptps,
            "prompt_ms": p_ms, "completion_ms": c_ms, "total_ms": p_ms + c_ms if p_ms and c_ms else None}


def extract_tool_call(resp):
    try:
        m = resp["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        return None
    tcs = m.get("tool_calls") or []
    fr = (resp.get("choices", [{}])[0]).get("finish_reason")
    if not tcs and fr != "tool_calls":
        return None
    if not tcs:
        return None
    fn = tcs[0].get("function", tcs[0])
    args = fn.get("arguments")
    try:
        args_parsed = json.loads(args) if isinstance(args, str) else args
    except (json.JSONDecodeError, ValueError):
        args_parsed = None
    return {"name": fn.get("name"), "arguments": args_parsed}


def first_text(resp):
    try:
        return resp["choices"][0]["message"].get("content") or ""
    except (KeyError, IndexError, TypeError):
        return ""
