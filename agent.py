import json

from . import config, executors

# Schema of the tools passed to the model.
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
        "name": "list_files", "description": "List the project's files (one name per line).",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {
        "name": "run_tests", "description": "Run the project's tests.",
        "parameters": {"type": "object", "properties": {},
                       "required": []}}},
]


def _resolve_name(files, name):
    """The key in 'files' that 'name' resolves to, or None: exact first, then
    case-insensitive — java names its files Solution.java/Test.java (javac requires the file
    to be named after the public class) and an exact 'solution.java' lookup left the solution
    empty, so no java agent task had ever passed. The agent needs the NAME (to keep the
    runner's files out of the project it hands to the executor); `read_file` needs the content."""
    if name in files:
        return name
    low = str(name).lower()
    for k in files:
        if k.lower() == low:
            return k
    return None


class MockEnv:
    """The sandbox the agent works on: the task's files in memory.

    Two files are the runner's (`solution.<ext>` and the task's TEST_FILE): the solution is
    what the model edits, the test is what grades. Every OTHER file is a project file — the
    model may read and edit it, and `run_tests` hands all of them to the executor, so a fix
    that spans files (a module the test imports) changes the verdict: that is what makes the
    multi-file tasks (MILLORA §C4) measurable.

    The test file is READ-ONLY, and grading always uses the pristine copy. Several tasks
    state it in their goal ("fix solution.py ... without ever modifying the test file") and
    nothing enforced it: a model could rewrite the test and turn "make the tests pass" into
    "delete the tests".
    """

    def __init__(self, files, lang, test_file="test_solution.py"):
        self.files = dict(files)
        self.initial = dict(files)      # pristine: what the test file is resolved against
        self.lang = lang
        self.test_file = test_file

    def _names(self):
        """(solution, test) as the executor will name them: exact, then case-insensitive
        (java: Solution.java/Test.java), then the task's TEST_FILE. None when absent."""
        ext = config.Lang.exts()[self.lang]
        sol = _resolve_name(self.files, f"solution{ext}") or _resolve_name(self.initial, f"solution{ext}")
        tst = (_resolve_name(self.initial, f"test_solution{ext}")
               or _resolve_name(self.initial, self.test_file)
               or _resolve_name(self.files, f"test_solution{ext}")
               or _resolve_name(self.files, self.test_file))
        return sol, tst

    def read_file(self, path):
        if path in self.files:
            return self.files[path]
        return f"error: no such file: {path}"

    def list_files(self):
        """The project's file names, sorted — the cheap first move of a real agent before
        reading anything, and the reason a task can ask for a fix without naming the file."""
        return "\n".join(sorted(self.files)) if self.files else "(no files)"

    def write_file(self, path, content):
        name = str(path or "").strip()
        if not name or "/" in name or "\\" in name or name in (".", ".."):
            return (f"error: '{path}' is not a plain file name — the sandbox is flat, "
                    f"write e.g. 'utils.py'")
        _sol, tst = self._names()
        if tst and name.lower() == str(tst).lower():
            return f"error: {name} is read-only (the task's tests cannot be modified)"
        self.files[name] = content
        return f"wrote {len(content)} bytes to {name}"

    def run_tests(self):
        # Unified convention across languages: solution.<ext> + test_solution.<ext>
        # (with fallback to self.test_file). Python used to be special-cased; now
        # everything goes through the same path because the convention is consistent.
        # The lookup is case-insensitive (see _resolve_name: java uses Solution.java/Test.java).
        sol, tst = self._names()
        # The PRISTINE test grades (self.initial): an edit the model made to it is ignored,
        # never silently used. The rest of the project travels with its current content.
        test = self.initial.get(tst, "") if tst else ""
        project = {k: v for k, v in self.files.items() if k not in (sol, tst)}
        r = executors.run(self.lang, self.files.get(sol), test, extra_files=project)
        return (r["passed"], r["output"])


def _exec_tool(name, args, env):
    if name == "read_file":
        return env.read_file(args.get("path", ""))
    if name == "write_file":
        return env.write_file(args.get("path", ""), args.get("content", ""))
    if name == "list_files":
        return env.list_files()
    if name == "run_tests":
        ok, out = env.run_tests()
        return ("TESTS PASS" if ok else "TESTS FAIL") + f"\n{out[-1500:]}"
    return f"error: unknown tool {name}"


def run_agent(client_mod, task, max_turns=8, max_tokens=None):
    env = MockEnv(task["initial_files"], task["lang"], task.get("test_file", "test_solution.py"))
    history = [{"role": "system", "content":
                "You solve coding tasks using tools. When done, reply with a short summary."},
               {"role": "user", "content": task["goal"]}]
    tool_calls = 0
    actual_turns = 0
    empty_replies = 0
    for _turn in range(max_turns):
        actual_turns = _turn + 1
        resp = client_mod.chat(history, tools=TOOLS, tool_choice="auto",
                               max_tokens=max_tokens or config.AGENT_MAX_TOKENS)
        msg = (resp.get("choices", [{}])[0]).get("message", {})
        tcs = msg.get("tool_calls") or []
        history.append(msg)
        if not tcs:
            # END of the episode. An assistant turn with neither content nor a tool call is the
            # signature of a turn budget spent entirely on reasoning (probe, MILLORA §C13):
            # counted here, warned about in grade_agent, recorded in the row.
            if not str(msg.get("content") or "").strip():
                empty_replies += 1
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
    return {"success": ok, "turns": actual_turns, "tool_calls": tool_calls,
            "empty_replies": empty_replies, "history": history}
