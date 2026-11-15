"""ggufbench.fetch — onboarding: HF repo → verified download → header → profile draft.

The measuring stays where it lives: the profile draft NEVER writes a numeric context
pin (the estimator lies; only probe-context.py measures), documentation is a human
gate, and the bench delegation honors the GPU golden rule — llama.cpp here, Strata
nowhere."""

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from typing import Any, Iterator
from dataclasses import dataclass
from pathlib import Path

from ggufbench import config, gguf_header
from ggufbench import run as _run

# Indirection so tests (and callers) can substitute the bench entry point without a
# server ever being started by this module.
_run_main = _run.main

EXIT_OK = 0
EXIT_NO_MATCH = 1
EXIT_GPU_BUSY = 65

_HF = "https://huggingface.co"
_USER_AGENT = "ggufbench-fetch"

_QUANT = re.compile(
    r"(?<![A-Za-z0-9])(UD-)?(IQ\d_[A-Z0-9]+|Q\d_[A-Z0-9_]+|BF16|F16|FP16|F32)(?![A-Za-z0-9])")


@dataclass
class RepoFile:
    name: str
    size: int
    lfs_sha256: str | None
    quant_guess: str | None


@dataclass
class Outcome:
    file: RepoFile
    verdict: str          # verified / unverified / failed / skipped
    bytes_written: int = 0
    sha: str | None = None
    expected: str | None = None
    note: str = ""


def quant_guess(name: str) -> str | None:
    m = _QUANT.search(name)
    return m.group(0) if m else None


def api_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={
        "Accept": "application/json", "User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _open(req: urllib.request.Request) -> Any:
    """The one network read path; tests stub this, never urllib internals."""
    return urllib.request.urlopen(req, timeout=120)


def list_repo(repo: str) -> tuple[list[RepoFile], RepoFile | None]:
    """(gguf files, mmproj companion) from the repo tree API. Non-GGUF files are
    ignored; the first mmproj*.gguf is flagged as the vision companion."""
    url = f"{_HF}/api/models/{repo}/tree/main?recursive=true"
    entries = api_json(url)
    files: list[RepoFile] = []
    mmproj: RepoFile | None = None
    for e in entries:
        if e.get("type") != "file" or not str(e.get("path", "")).endswith(".gguf"):
            continue
        lfs = e.get("lfs") or {}
        oid = lfs.get("oid") or e.get("lfs_sha256")
        if isinstance(oid, str) and oid.startswith("sha256:"):
            oid = oid.split(":", 1)[1]
        f = RepoFile(name=e["path"], size=int(e.get("size") or 0),
                     lfs_sha256=oid, quant_guess=quant_guess(e["path"]))
        files.append(f)
        if mmproj is None and Path(f.name).name.lower().startswith("mmproj"):
            mmproj = f
    return files, mmproj


def _strata_alive() -> bool:
    """The GPU golden rule: if the Strata engine is alive, llama.cpp must not start."""
    try:
        r = subprocess.run(["pgrep", "-f", "engine/strata"], capture_output=True)
        return r.returncode == 0
    except OSError:
        return False


def _stream(url: str, part: Path, resume: bool) -> tuple[int, str]:
    """Streaming adapter over _open."""
    """Stream url into `part` (appending from the resume offset when asked), hashing
    every byte including the prefix we already had. Returns (bytes_total, sha256)."""
    part.parent.mkdir(parents=True, exist_ok=True)
    start = part.stat().st_size if (resume and part.exists()) else 0
    h = hashlib.sha256()
    if start:
        h.update(part.read_bytes())
    headers = {"Range": f"bytes={start}-"} if start else {}
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT, **headers})
    with _open(req) as resp, open(part, "ab" if start else "wb") as fh:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
            h.update(chunk)
            start += len(chunk)
    return start, h.hexdigest()


def download_verified(repo: str, f: RepoFile, dest_dir: Path, resume: bool = True) -> Outcome:
    """Download → verify BEFORE the file counts. A hash mismatch deletes the partial
    file; a file without an LFS oid lands as `unverified` (never auto-benched)."""
    dest = Path(dest_dir) / Path(f.name).name
    part = dest.with_name(dest.name + ".part")
    url = f"{_HF}/{repo}/resolve/main/{f.name}"
    try:
        written, sha = _stream(url, part, resume)
    except Exception as e:                    # noqa: BLE001 — the state table is the contract
        part.unlink(missing_ok=True)
        return Outcome(f, "failed", note=f"{type(e).__name__}: {e}")
    if f.lfs_sha256 and sha != f.lfs_sha256:
        part.unlink(missing_ok=True)
        return Outcome(f, "failed", written, sha, f.lfs_sha256,
                       note="sha256 mismatch — partial deleted")
    verdict = "verified" if f.lfs_sha256 else "unverified"
    part.replace(dest)
    return Outcome(f, verdict, written, sha, f.lfs_sha256)


def propose_profile(model_path: Path, facts: dict, mmproj_path: Path | None) -> Path:
    """Profile draft: only declaratively-safe flags. The context pin is a commented
    TODO for probe-context.py — the estimator lies by 3-8x, so a numeric -c here would
    be a lie in a config file."""
    p = model_path.with_suffix(".txt")
    if p.exists():
        return p                              # conservative: fetch never overwrites
    lines = [
        f"# draft de perfil generat per ggufbench.fetch (capçalera verificada: "
        f"arch {facts.get('arch')} · blocs {facts.get('n_blocks')} · "
        f"MTP tensors {facts.get('mtp_tensors')})",
        "# TODO -c: el sostre real es mesura EN VIU amb",
        "#   ggufbench/harness/tools/probe-context.py  (marge 2000 MiB, despatx actiu).",
        "# Descomenta i escriu el valor mesurat — mai el de l'estimador:",
        "# -c <mesurat>",
    ]
    if facts.get("mtp_tensors"):
        lines.append("--spec-type draft-mtp")
    if mmproj_path is not None:
        lines.append(f"--mmproj {mmproj_path.resolve()}")
    p.write_text("\n".join(lines) + "\n")
    return p


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="ggufbench.fetch",
        description="Onboarding: HF repo → verified GGUFs in models/ → header "
                    "fact-sheet → profile draft (→ --bench). Docs stay a human gate.")
    ap.add_argument("--repo", required=True, help="HF repo id, e.g. 'org/model-GGUF'")
    ap.add_argument("--include", default="*.gguf",
                    help="glob over the repo's file names (default: every *.gguf)")
    ap.add_argument("--dest", default=str(config.MODELS_DIR),
                    help="download directory (default: the workspace models/)")
    ap.add_argument("--yes", action="store_true",
                    help="skip the plan confirmation (required when stdin is not a TTY)")
    ap.add_argument("--bench", action="store_true",
                    help="run the reference pass on every verified non-mmproj file")
    ap.add_argument("--json", default=None, help="write the per-file state table here")
    args = ap.parse_args(argv)

    try:
        files, mmproj = list_repo(args.repo)
    except urllib.error.HTTPError as e:
        print(f"{args.repo}: listing failed ({e.code} {e.reason})", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"{args.repo}: listing failed ({type(e.reason).__name__})", file=sys.stderr)
        return 1

    selected = [f for f in files if fnmatch.fnmatch(Path(f.name).name, args.include)]
    if not selected:
        print(f"no GGUF matches {args.include!r} in {args.repo}", file=sys.stderr)
        return EXIT_NO_MATCH

    dest_dir = Path(args.dest)
    print(f"== {args.repo}: {len(selected)} file(s) → {dest_dir}")
    for f in selected:
        print(f"    {f.name}  {f.size / 1e9:.1f} GB  {f.quant_guess or '?'}  "
              f"{'(LFS sha256 ok)' if f.lfs_sha256 else '(NO LFS hash: unverified)'}")
    if not args.yes:
        if sys.stdin.isatty():
            if input(f"download {len(selected)} file(s)? [y/N] ").strip().lower() \
                    not in ("y", "yes"):
                print("declined")
                return EXIT_OK
        else:
            print("non-interactive: re-run with --yes", file=sys.stderr)
            return 2

    states: dict[str, str] = {}
    outcomes: list[Outcome] = []
    for f in selected:
        out = download_verified(args.repo, f, dest_dir, resume=True)
        outcomes.append(out)
        states[Path(f.name).name] = out.verdict
        mark = {"verified": "[ok]", "unverified": "[??]", "failed": "[!!]",
                "skipped": "[--]"}[out.verdict]
        print(f"  {mark} {Path(f.name).name}  {out.verdict}"
              + (f" — {out.note}" if out.note else ""), flush=True)

    fact_sheets: dict[str, dict] = {}
    profiles: list[str] = []
    for out in outcomes:
        if out.verdict not in ("verified", "unverified"):
            states[Path(out.file.name).name] = out.verdict
            continue
        dest = dest_dir / Path(out.file.name).name
        if Path(out.file.name).name.lower().startswith("mmproj"):
            continue                            # the projector gets no profile
        try:
            facts = gguf_header.read_header(dest)
        except ValueError as e:
            states[Path(out.file.name).name] = f"header_failed ({e})"
            continue
        fact_sheets[Path(out.file.name).name] = facts
        p = propose_profile(dest, facts,
                            dest_dir / Path(mmproj.name).name
                            if mmproj and (dest_dir / Path(mmproj.name).name).exists()
                            else None)
        profiles.append(str(p))
        print(f"  header {Path(out.file.name).name}: arch {facts['arch']} · "
              f"blocs {facts['n_blocks']} · MTP {facts['mtp_tensors']} · "
              f"profile draft {p.name}")

    if args.bench:
        models = [str(dest_dir / Path(o.file.name).name) for o in outcomes
                  if o.verdict == "verified"
                  and not Path(o.file.name).name.lower().startswith("mmproj")]
        if len(models) != len([o for o in outcomes if o.verdict == "verified"]):
            print("  ! bench skipped: some files did not verify", file=sys.stderr)
            return EXIT_NO_MATCH
        if _strata_alive():
            print("  ! the Strata engine is alive: the GPU golden rule forbids "
                  "starting llama.cpp now (stop it, then re-run)", file=sys.stderr)
            return EXIT_GPU_BUSY
        print(f"  → reference pass on {len(models)} model(s)…", flush=True)
        rc = _run_main(["--models", ",".join(models), "--thinking", "off",
                        "--runs", "1", "--context", "fixed"])
        if rc != 0:
            return rc

    if args.json:
        Path(args.json).write_text(json.dumps(
            {"repo": args.repo, "files": [
                {"name": Path(o.file.name).name,
                 "state": states.get(Path(o.file.name).name, o.verdict),
                 "bytes": o.bytes_written,
                 "sha256": o.sha, "expected": o.expected, "note": o.note}
                for o in outcomes],
             "profiles": profiles},
            indent=1, ensure_ascii=False))

    failed = [s for s in states.values() if s.startswith("failed") or "header_failed" in s]
    print(f"\n== states: " + ", ".join(f"{k}={v}" for k, v in sorted(states.items())))
    return EXIT_OK if not failed and states else EXIT_NO_MATCH


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
