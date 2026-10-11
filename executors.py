import subprocess
import tempfile
import os
import time
import shutil

from . import config


def _sandbox_prefix(timeout: int) -> list[str]:
    """Sandboxing command prefix: timeout + network blocked when unshare is available."""
    prefix = ["timeout", str(timeout)]
    # unshare -n blocks the network (needs user namespace permission); if it fails, it's omitted.
    if shutil.which("unshare"):
        try:
            subprocess.run(["unshare", "-n", "true"], check=True,
                           capture_output=True, timeout=1)
            prefix += ["unshare", "-n"]
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
    return prefix


def _safe_run(cmd: list[str], cwd: str, timeout: int):
    """Runs subprocess.run without propagating TimeoutExpired: returns None on timeout."""
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True,
                              text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None


def _result(passed: bool, output: str, started: float) -> dict:
    return {"passed": passed, "output": output[-2000:],
            "elapsed_ms": int((time.time() - started) * 1000)}


def _write(tmp: str, files: dict[str, str]) -> None:
    for name, content in files.items():
        with open(os.path.join(tmp, name), "w") as f:
            f.write(content)


def run(lang: str, solution_code, test_code, timeout: int = 30,
        extra_files=None) -> dict:
    """Writes solution+test (+support extra_files) to a tempdir, runs according to lang.

    extra_files are written FIRST: if one of them collided with solution/test,
    the runner's files win (the loader already validates this).
    """
    if solution_code is None:
        return {"passed": False, "output": "no solution code block found", "elapsed_ms": 0}
    started = time.time()
    tmp = tempfile.mkdtemp(prefix="mbench_")
    try:
        if extra_files:
            _write(tmp, dict(extra_files))
        return _run_in(tmp, lang, solution_code, test_code, timeout, started)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _run_in(tmp: str, lang: str, solution_code: str, test_code: str,
            timeout: int, started: float) -> dict:
    runners = {config.Lang.PYTHON: _python, config.Lang.BASH: _bash,
               config.Lang.JAVA: _java, config.Lang.TYPESCRIPT: _typescript}
    if lang not in runners:
        raise ValueError(f"lang not supported: {lang}")
    return runners[lang](tmp, solution_code, test_code, timeout, started)


def _python(tmp, solution_code, test_code, timeout, started):
    _write(tmp, {"solution.py": solution_code, "test_solution.py": test_code})
    p = _safe_run(_sandbox_prefix(timeout) + ["python3", "test_solution.py"], tmp, timeout + 5)
    if p is None:
        return _result(False, "timed out", started)
    return _result(p.returncode == 0, (p.stdout + p.stderr).strip(), started)


def _bash(tmp, solution_code, test_code, timeout, started):
    _write(tmp, {"solution.sh": solution_code, "test_solution.sh": test_code})
    p = _safe_run(_sandbox_prefix(timeout) + ["bash", "test_solution.sh"], tmp, timeout + 5)
    if p is None:
        return _result(False, "timed out", started)
    return _result(p.returncode == 0, (p.stdout + p.stderr).strip(), started)


def _java(tmp, solution_code, test_code, timeout, started):
    _write(tmp, {"Solution.java": solution_code, "Test.java": test_code})
    pre = _sandbox_prefix(timeout)
    # Compiles all .java in the sandbox: solution + test + extra_files (support classes)
    srcs = sorted(f for f in os.listdir(tmp) if f.endswith(".java"))
    comp = _safe_run(pre + ["javac"] + srcs, tmp, timeout + 5)
    if comp is None:
        return _result(False, "compile timed out", started)
    if comp.returncode != 0:
        return _result(False, "compile error:\n" + comp.stderr, started)
    run = _safe_run(pre + ["java", "Test"], tmp, timeout + 5)
    if run is None:
        return _result(False, "timed out", started)
    return _result(run.returncode == 0, (run.stdout + run.stderr).strip(), started)


def _typescript(tmp, solution_code, test_code, timeout, started):
    _write(tmp, {"solution.ts": solution_code, "test_solution.ts": test_code})
    p = _safe_run(_sandbox_prefix(timeout) + ["bun", "test_solution.ts"], tmp, timeout + 5)
    if p is None:
        return _result(False, "timed out", started)
    return _result(p.returncode == 0, (p.stdout + p.stderr).strip(), started)
