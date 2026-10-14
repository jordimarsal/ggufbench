#!/usr/bin/env python3
"""check-task.py — prove a task is (a) solvable and (b) discriminating, without a model.

A task is data, so a typo can ship a task nobody can pass (or one that passes by itself).
Both are invisible in the scoreboard. This tool runs the real executors on the task:

  agent tasks:  the initial files MUST fail, and an external REFERENCE overlay MUST pass
                (the reference is a directory with the fixed/added files; it is never
                committed — reference solutions do not travel with the repo)
  code tasks:   the REFERENCE solution file MUST pass; an optional BROKEN file MUST fail
  tools tasks:  nothing to run — prints the expected call so the author checks it by eye

Usage (from the workspace root):
  python3 harness/tools/check-task.py --task tasks/agent/python/invoice_dup_expert.py \
      --reference /tmp/opencode/refs/invoice_dup
  python3 harness/tools/check-task.py --task tasks/code/python/report_hard.py \
      --reference /tmp/opencode/refs/report_hard.py --broken /tmp/opencode/refs/report_hard_naive.py
Exit code 0 only when every requested check passes.
"""

import argparse
import importlib.util
import json
import pathlib
import sys

from ggufbench import agent as A          # noqa: E402
from ggufbench import executors as E      # noqa: E402


def load_module(path):
    # Ensure the task file's parent is on sys.path so its module can be loaded
    p = pathlib.Path(path)
    if str(p.parent) not in sys.path:
        sys.path.insert(0, str(p.parent))
    spec = importlib.util.spec_from_file_location(p.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_agent(mod, reference):
    files = dict(getattr(mod, "INITIAL_FILES", {}) or {})
    lang = getattr(mod, "LANG", "python")
    test_file = getattr(mod, "TEST_FILE", "test_solution.py")
    env = A.MockEnv(files, lang, test_file)
    ok, out = env.run_tests()
    print(f"  initial state   : {'PASS' if ok else 'FAIL'} (must FAIL)")
    verdict = not ok
    if reference:
        ref_dir = pathlib.Path(reference)
        overlay = {p.name: p.read_text() for p in sorted(ref_dir.iterdir()) if p.is_file()}
        fixed = dict(files)
        fixed.update(overlay)
        env2 = A.MockEnv(fixed, lang, test_file)
        ok2, out2 = env2.run_tests()
        print(f"  reference ({len(overlay)} file(s)): {'PASS' if ok2 else 'FAIL'} (must PASS)")
        if not ok2:
            print("    " + (out2 or "")[-600:].replace("\n", "\n    "))
        verdict = verdict and ok2
    print(f"  files: {len(files)} | test: {test_file} | max_turns: {getattr(mod, 'MAX_TURNS', '?')}")
    return verdict


def check_code(mod, reference, broken, tmp_extra=("EXTRA_FILES", "extra_files")):
    lang = getattr(mod, "LANG", "python")
    test = getattr(mod, "TEST_CODE", "")
    extra = getattr(mod, "EXTRA_FILES", None) or None
    verdict = True
    for label, path, expect in (("reference", reference, True), ("broken", broken, False)):
        if not path:
            continue
        code = pathlib.Path(path).read_text()
        r = E.run(lang, code, test, extra_files=extra)
        good = (r["passed"] is expect)
        print(f"  {label:15} : {'PASS' if r['passed'] else 'FAIL'} "
              f"(must {'PASS' if expect else 'FAIL'}) {'ok' if good else 'WRONG'}")
        if not good:
            print("    " + (r["output"] or "")[-500:].replace("\n", "\n    "))
        verdict = verdict and good
    return verdict


def check_tools(mod):
    print(f"  expected call   : {json.dumps(getattr(mod, 'EXPECTED', None), ensure_ascii=False)}")
    print("  (data-only task: the call is compared with ==, nothing to execute)")
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", required=True, help="path to the task file")
    ap.add_argument("--reference", help="fixed/expected files (dir for agent, file for code)")
    ap.add_argument("--broken", help="code tasks: a naive solution that must FAIL")
    args = ap.parse_args(argv)

    path = pathlib.Path(args.task)
    mod = load_module(path)
    print(f"== {path.name} ==")
    if "GOAL" in dir(mod) or getattr(mod, "INITIAL_FILES", None) is not None:
        verdict = check_agent(mod, args.reference)
    elif getattr(mod, "TEST_CODE", None) is not None:
        verdict = check_code(mod, args.reference, args.broken)
    else:
        verdict = check_tools(mod)
    print("  VERDICT:", "ok" if verdict else "REJECTED")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
