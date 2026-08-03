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
    if lang == "python":
        return _python(tmp, solution_code, test_code, timeout, started)
    raise ValueError(f"lang not implemented yet: {lang}")

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