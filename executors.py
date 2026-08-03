import subprocess, tempfile, os, time, shutil

def _sandbox_prefix(timeout):
    """Command prefix per aïllar: timeout + xarxa bloquejada si unshare hi és."""
    prefix = ["timeout", str(timeout)]
    # unshare -n bloqueja xarxa (requot permís de user namespace); si falla, s'omet.
    if shutil.which("unshare"):
        # Test if unshare works first
        try:
            subprocess.run(["unshare", "-n", "true"], check=True, capture_output=True, timeout=1)
            prefix += ["unshare", "-n"]
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass  # unshare not available or no permission
    return prefix

def run(lang, solution_code, test_code, timeout=30):
    """Escriu solution+test en tempdir, executa segons lang, retorna resultat."""
    if solution_code is None:
        return {"passed": False, "output": "no solution code block found", "elapsed_ms": 0}
    started = time.time()
    tmp = tempfile.mkdtemp(prefix="mbench_")
    try:
        return _run_in(tmp, lang, solution_code, test_code, timeout, started)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def _run_in(tmp, lang, solution_code, test_code, timeout, started):
    runners = {"python": _python, "bash": _bash, "java": _java, "typescript": _typescript}
    if lang not in runners:
        raise ValueError(f"lang not supported: {lang}")
    return runners[lang](tmp, solution_code, test_code, timeout, started)

def _python(tmp, solution_code, test_code, timeout, started):
    with open(os.path.join(tmp, "solution.py"), "w") as f:
        f.write(solution_code)
    with open(os.path.join(tmp, "test_solution.py"), "w") as f:
        f.write(test_code)
    cmd = _sandbox_prefix(timeout) + ["python3", "test_solution.py"]
    p = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, timeout=timeout + 5)
    out = (p.stdout + p.stderr).strip()
    return {"passed": p.returncode == 0, "output": out[-2000:],
            "elapsed_ms": int((time.time() - started) * 1000)}

def _bash(tmp, solution_code, test_code, timeout, started):
    with open(os.path.join(tmp, "solution.sh"), "w") as f:
        f.write(solution_code)
    with open(os.path.join(tmp, "test_solution.sh"), "w") as f:
        f.write(test_code)
    cmd = _sandbox_prefix(timeout) + ["bash", "test_solution.sh"]
    p = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, timeout=timeout + 5)
    out = (p.stdout + p.stderr).strip()
    return {"passed": p.returncode == 0, "output": out[-2000:],
            "elapsed_ms": int((time.time() - started) * 1000)}

def _java(tmp, solution_code, test_code, timeout, started):
    with open(os.path.join(tmp, "Solution.java"), "w") as f:
        f.write(solution_code)
    with open(os.path.join(tmp, "Test.java"), "w") as f:
        f.write(test_code)
    pre = _sandbox_prefix(timeout)
    comp = subprocess.run(pre + ["javac", "Solution.java", "Test.java"],
                          cwd=tmp, capture_output=True, text=True, timeout=timeout + 5)
    if comp.returncode != 0:
        return {"passed": False, "output": ("compile error:\n" + comp.stderr)[:2000],
                "elapsed_ms": int((time.time() - started) * 1000)}
    run = subprocess.run(pre + ["java", "Test"], cwd=tmp,
                         capture_output=True, text=True, timeout=timeout + 5)
    out = (run.stdout + run.stderr).strip()
    return {"passed": run.returncode == 0, "output": out[-2000:],
            "elapsed_ms": int((time.time() - started) * 1000)}

def _typescript(tmp, solution_code, test_code, timeout, started):
    with open(os.path.join(tmp, "solution.ts"), "w") as f:
        f.write(solution_code)
    with open(os.path.join(tmp, "test_solution.ts"), "w") as f:
        f.write(test_code)
    cmd = _sandbox_prefix(timeout) + ["bun", "test_solution.ts"]
    p = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, timeout=timeout + 5)
    out = (p.stdout + p.stderr).strip()
    return {"passed": p.returncode == 0, "output": out[-2000:],
            "elapsed_ms": int((time.time() - started) * 1000)}