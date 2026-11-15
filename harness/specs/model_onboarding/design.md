# Design: model_onboarding

## Files to modify

| File | Change |
|---|---|
| `fetch.py` (new, repo root — same flat layout as `run.py`/`report.py`) | the CLI and the four stages: list → download/verify → header → propose; `--bench` delegates to `run.main()`. |
| `gguf_header.py` (new) | minimal stdlib GGUF header reader: magic/version, kv pairs (general.architecture, general.name, block counts), tensor-key scan for `ffn_mtp`/`nextn` presence and `clip`/vision markers. Read-only; streams, does not load tensors. |
| `tests/test_fetch.py` (new) | offline tests: header parser on a crafted tiny GGUF, hash-verify paths, resume logic, profile proposal, summary table, exit codes. Network behind `hf_client` stub. |
| `tests/test_gguf_header.py` (new) | parser tests on fixtures (a ~2 KB synthetic GGUF written by the test itself: correct magic, two kv pairs, one `ffn_mtp` tensor key). |
| `README.md` | one paragraph under Quickstart: fetching a repo. |
| `harness/feature_list.json` | feature 13 entry (this spec). |

## New signatures

```python
# fetch.py
def list_repo(repo: str) -> list[RepoFile]          # name, size, lfs_sha256|None, quant_guess
def download_verified(repo, f: RepoFile, dest_dir, resume=True) -> Outcome
def read_header(path) -> HeaderFacts                # delegates to gguf_header
def propose_profile(path, facts, mmproj_path|None) -> Path   # writes the .txt draft
def main(argv=None) -> int                          # --repo --include --bench --yes --json

# gguf_header.py
def read_header(path) -> dict    # {"arch": str, "name": str, "n_blocks": int,
                                 #  "mtp_tensors": int, "vision": bool, "size_label": str|None}
```

`hf_client.py`-shaped indirection: all HTTP goes through two functions
(`api_json(url)`, `stream(url, dest, expected_sha)`) so tests stub them without
monkeypatching urllib internals. **Stdlib only** — `urllib.request`, `hashlib`, `json`.

## Decisions

- **LFS oid = the verifier.** The tree API with `?recursive=true` returns `lfs.sha256`
  per file (the same hashes today's manual `SHA256SUMS` checks used). A file without an
  LFS oid (rare) is downloaded but flagged `unverified` in the summary and never
  auto-benched.
- **Resume by offset, trust by hash.** A partial file resumes with a `Range` header when
  the redirect target supports it; the final hash is always computed over the whole
  stream, so a resumed file that fails the hash is deleted (R3/R4), not kept.
- **Profile draft is conservative by construction** (R6): the 2026-11-14 lesson — a `-c`
  that the estimator "predicts" is a lie (the estimator undershot 193k-266k live ceilings
  by 3-8×). The draft writes `-c` only as a commented TODO pointing at
  `harness/tools/probe-context.py`.
- **Quant guess** parses the file name (`Q4_K_M`, `IQ2_XS`, `UD-…`, `BF16`…) and is
  display-only: it feeds the summary table, never a decision.
- **`--yes` skips the interactive confirmation** of the file list; without it, the tool
  prints the plan (files, sizes, destination) and asks. The bench subprocess (R7) runs
  from `_ROOT_DIR` with the same GPU-rule discipline as `run.py` (one engine at a time;
  refuses when a foreign engine is alive).

## Summary card (stdout, R8)

```
== ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF
  [ok] Qwen3.8-…-IQ3_XXS-00001-of-00002.gguf   43.8 GB  verified  92cee27a…
  [ok] mmproj-Qwen3.8-…-BF16.gguf               866 MB  verified
== header: Qwen3.8-Flash-Next · arch qwen35moe · 47 blocks · MTP: 0 tensors · vision: yes
== profile draft: models/Qwen3.8-….txt (TODO: -c via probe-context.py)
== bench (--bench): (row here when run)
NEXT: probe-context.py → mtp-sweep.py (if MTP>0) → bench → ASSIGNACIO row (human)
```

The `NEXT:` block is static text naming the human steps — fetch ends where the
measuring tools begin.
