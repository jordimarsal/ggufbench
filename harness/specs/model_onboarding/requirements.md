# Requirements: model_onboarding

Onboarding a model into the fleet is the most repeated workflow of the rig and the most
manual: download, verify SHA256, read the GGUF header, propose a profile, probe the
context ceiling, sweep the draft head, bench, and draft the documentation rows. The
2026-11-14 session (SC117 + Huihui) and the pruned IQ2_XS attempt each burned hours
across ad-hoc scripts (`sha256sum -c`, hand-written header greps, the pack tool for
Strata) with no shared state and no artifact trail.

This feature adds `python3 -m ggufbench.fetch`: one command that takes a Hugging Face
repo id and produces **verified GGUF files in `models/`, a header fact-sheet, and a
proposed profile draft** — with every number that requires a live measurement left as an
explicit TODO for the existing tools (`probe-context.py`, `mtp-sweep.py`, the bench
itself). It is stdlib-only like the rest of the runtime (no `huggingface_hub`).

Out of scope: Strata pack generation (`tools/iq_pack.py` stays where it is), context
probing, drafting sweeps, and any documentation write. Fetch prepares; the existing
tools and the human decide.

## R1
WHEN `ggufbench.fetch --repo <owner/name>` runs, the tool SHALL query the HF tree API
(`/api/models/<repo>/tree/main?recursive=true`) and list every `*.gguf` with size, the
LFS sha256 when present, and a quant guess parsed from the file name.

## R2
WHEN files are selected (via `--include <glob>`, default: every `*.gguf`), the tool
SHALL download them into `config.MODELS_DIR` and verify the streamed sha256 against the
LFS oid BEFORE counting the file as present.

## R3
WHEN a downloaded file fails verification, the tool SHALL delete the partial file, keep
the failure in the summary, and continue with the other files (never mark the batch as
success).

## R4
WHEN a download is interrupted and re-run, the tool SHALL resume from the byte offset
when the server supports ranges, re-verifying the completed hash; a file that cannot be
verified SHALL never be treated as verified regardless of its size on disk.

## R5
WHEN files are verified, the tool SHALL read their GGUF header and print a fact-sheet:
`general.architecture`, `general.name`, block count, MTP/nextn tensor presence (count of
`ffn_mtp` keys), and the companion `mmproj` file of the repo when one exists.

## R6
WHEN the header fact-sheet is produced, the tool SHALL write a profile draft
`models/<stem>.txt` containing only declaratively-safe flags: a commented `-c` line
marked TODO for `probe-context.py`, `--spec-type draft-mtp` only when R5 detected MTP
tensors, and `--mmproj <path>` only when a companion exists. It SHALL NOT write a
numeric context pin as if it were measured.

## R7
WHEN `--bench` is passed and every selected file verified, the tool SHALL run the
standard reference pass (`--dims` all, thinking off, `--runs 1`, fixed context) per file
and print the scoreboard row — one engine at a time, honoring the GPU golden rule.

## R8
The tool SHALL NOT write `ASSIGNACIO.md`, `retired.json`, skills or README: it prints a
summary card (verified files, fact-sheet, bench row) whose doc lines the human copies
into the docs. Documentation is a human gate.

## R9
WHEN any step fails (HF rate limit, disk full, network), the tool SHALL exit non-zero
with a per-file state table (downloaded/verified/proposed/benched/failed) reflecting
what actually completed — never a silent partial success.
