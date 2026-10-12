# Security Audit — ggufbench

**Date:** 2026-10-12  
**Scope:** executors.py · tasks_loader.py · server.py · client.py · html_report.py · run.py (published artifacts)  
**Method:** Static review + `bash harness/tools/audit-security.sh` (checklist-only; generic stack, no SAST tools available)

## Executive summary

The benchmark is a local-only tool with no auth or external-facing attack surface. Two issues stand out: (1) the code sandbox silently drops network isolation when `unshare -n` fails (common in containers), letting LLM-generated code make outbound HTTP calls; and (2) published HTML reports embed absolute paths to model files under `/home/jordi/ia/llama/`, revealing the operator's home directory structure and hardware details on GitHub Pages. No secrets, tokens, or credentials are exposed.

## Findings

### [MEDIUM] Sandbox loses network isolation when unshare unavailable
- **File:** `executors.py:14–20`
- **Scenario:** `unshare -n` requires user namespace permissions; on many Linux setups (and all Docker containers without `--privileged`) it fails. The prefix then omits `-n`, so every language runner executes with full network access. An adversarial task could exfiltrate data via HTTP(S).
- **Fix:** Fail open — raise an error if `unshare -n` cannot be verified, rather than silently dropping the flag. Or use seccomp/BPF as a fallback.

### [LOW] Published artifacts leak absolute filesystem paths
- **Files:** `results/report.html`, `results/compare.html` (rendered by `html_report.py:657–660`, `run.py:168`)
- **Scenario:** Both pages embed `model_config_flags` verbatim inside `<div class="mv">`. Strata configs contain paths like `/home/jordi/ia/llama/Strata-data/models/IQ3_XXS/…`; llama models include `--mmproj /home/jordi/ia/llama/models/mmproj-F16.gguf`. The environment field also leaks GPU model, driver version, and kernel string. Anyone viewing the GitHub Pages site learns the operator's home directory layout and hardware profile.
- **Fix:** Strip or redact absolute paths before embedding in HTML; replace them with relative placeholders (`models/<name>.gguf`).

### [LOW] Model `.txt` flags pass through without validation beyond infra filter
- **File:** `server.py:35–52`
- **Scenario:** `_strip_infra()` only removes `-m/--model/--port/--host`. All other flags from `models/<model>.txt` are appended to the subprocess command line unfiltered. If an attacker gains write access to a `.txt` file they could inject arbitrary llama-server arguments (e.g., `--mmproj`, `--spec-type`, `--ctx-size`).
- **Fix:** Maintain an allow-list of permitted flag prefixes rather than a deny-list of infrastructure flags.

### [INFO] Tempdir race window on cleanup
- **File:** `executors.py:54, 60`
- **Scenario:** `tempfile.mkdtemp(prefix="mbench_")` creates a predictable-ish path; `shutil.rmtree(tmp, ignore_errors=True)` runs in `finally:` but another process could read/write files between task completion and removal. Low impact because the prefix includes random characters and tasks run sequentially.
- **Fix:** Use `mkstemp` for individual files or add a brief sleep before rmtree if cross-process isolation is needed.

## Automated scan output

```
# Security Audit Report (stack: generic)

## Checklist-only audit (no automated tools for stack: generic)

## Checklist
Confirm every item of the Security Audit Checklist in docs/verification.md
(section 'Security Audit Checklist'). Record the outcome in the review file.

VERDICT: no HIGH severity findings reported by automated tools.
```

## Verification checklist (from `docs/verification.md`)

| # | Item | Status |
|---|------|--------|
| A01 | No auth required — local tool only | PASS |
| A02 | No hardcoded secrets | PASS |
| A03 | No SQL injection; subprocess args from controlled `.txt` files | PASS |
| A04 | EXTRA_FILES validated (plain names, no traversal) — see §B below | PASS |
| A05 | No debug mode / verbose traces in production config | PASS |
| HTML/XSS | `_esc()` uses `html.escape(quote=True)` on all user data | PASS |

### B. EXTRA_FILES path-traversal check (`tasks_loader.py:15–28`)

The loader rejects any name containing `/`, `\`, `.`, `..`, or starting with `solution`/`test`. Verified against four expert tasks that declare `EXTRA_FILES` (e.g., `events.jsonl`, `access.log`, `sales.csv`, `readings.csv`). **No traversal possible.**
