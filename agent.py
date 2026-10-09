import json

from . import config, executors

# Esquema de les tools que es passen al model.
TOOLS = [
    {"type": "function", "function": {
        "name": "read_file", "description": "Read a file from the project.",
        "parameters": {"type": "object",
                       "properties": {"path": {"type": "string"}},
                       "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "write_file", "description": "Write content to a file (create or overwrite).",
        "parameters": {"type": "object",
                       "properties": {"path": {"type": "string"},
                                      "content": {"type": "string"}},
                       "required": ["path", "content"]}}},
    {"type": "function", "function": {
        "name": "run_tests", "description": "Run the project's tests.",
        "parameters": {"type": "object", "properties": {},
                       "required": []}}},
]


def _get_file(files, name, default=""):
    """Cerca 'name' a files; si no hi és exacte, prova sense distingir majúscules:
    java anomena els seus fitxers Solution.java/Test.java (javac exigeix que el
    fitxer es digui com la classe pública) i cercar-hi 'solution.java' exacte
    deixava la solució buida: cap tasca d'agent java havia passat mai."""
    if name in files:
        return files[name]
    low = name.lower()
    for k, v in files.items():
        if k.lower() == low:
            return v
    return default


class MockEnv:
    def __init__(self, files, lang, test_file="test_solution.py"):
        self.files = dict(files)
        self.lang = lang
        self.test_file = test_file

    def read_file(self, path):
        if path in self.files:
            return self.files[path]
        return f"error: no such file: {path}"

    def write_file(self, path, content):
        self.files[path] = content
        return f"wrote {len(content)} bytes to {path}"

    def run_tests(self):
        # Conveni unificat per tots els llenguatges: solution.<ext> + test_solution.<ext>
        # (amb fallback a self.test_file). Abans python estava especialitzat; ara tot
        # passa pel mateix camí perquè la convenció és coherent. La cerca no distingeix
        # majúscules (vegeu _get_file: les tasques de java usen Solution.java/Test.java).
        ext = config.Lang.exts()[self.lang]
        sol = _get_file(self.files, f"solution{ext}")
        tst = _get_file(self.files, f"test_solution{ext}",
                        _get_file(self.files, self.test_file))
        r = executors.run(self.lang, sol, tst)
        return (r["passed"], r["output"])


def _exec_tool(name, args, env):
    if name == "read_file":
        return env.read_file(args.get("path", ""))
    if name == "write_file":
        return env.write_file(args.get("path", ""), args.get("content", ""))
    if name == "run_tests":
        ok, out = env.run_tests()
        return ("TESTS PASS" if ok else "TESTS FAIL") + f"\n{out[-1500:]}"
    return f"error: unknown tool {name}"


def run_agent(client_mod, task, max_turns=8):
    env = MockEnv(task["initial_files"], task["lang"], task.get("test_file", "test_solution.py"))
    history = [{"role": "system", "content":
                "You solve coding tasks using tools. When done, reply with a short summary."},
               {"role": "user", "content": task["goal"]}]
    tool_calls = 0
    actual_turns = 0
    for _turn in range(max_turns):
        actual_turns = _turn + 1
        resp = client_mod.chat(history, tools=TOOLS, tool_choice="auto", max_tokens=512)
        msg = (resp.get("choices", [{}])[0]).get("message", {})
        tcs = msg.get("tool_calls") or []
        history.append(msg)
        if not tcs:
            break
        for tc in tcs:
            fn = tc.get("function", tc)
            name = fn.get("name")
            raw = fn.get("arguments", "{}")
            try:
                args = json.loads(raw) if isinstance(raw, str) else (raw or {})
            except json.JSONDecodeError:
                args = {}
            tool_calls += 1
            result = _exec_tool(name, args, env)
            history.append({"role": "tool", "tool_call_id": tc.get("id", "x"), "content": result})
    ok, _ = env.run_tests()
    return {"success": ok, "turns": actual_turns, "tool_calls": tool_calls}
