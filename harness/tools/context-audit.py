#!/usr/bin/env python3
"""Per-model context capacity audit (Python 3.12, pure stdlib).

Answers, for every model of the fleet:
  * the maximum REAL context one slot can hold with the KV cache at q8_0 and at q4_0;
  * how many parallel slots fit in VRAM at a reference per-slot context. llama-server's
    `-c` is the TOTAL across slots, so n slots at ref_ctx cost n * ref_ctx of KV.

--- The math, ported from bin/start-dev-ai.sh `get_context_info()` ------------------
KV bytes per token (the estimator's formula, verbatim):

    kv_bytes_per_token = n_layers * n_kv_head * (k_len * bpe(ktype) + v_len * bpe(vtype))

For a standard model (k_len == v_len == head_dim, same quant on K and V) that is the
documented form:

    bytes/token/layer = kv_heads * head_dim * bytes_per_elem * 2      # 2 = K + V

`k_len`/`v_len` come from `<arch>.attention.key_length` / `.value_length` when the GGUF
declares them (MLA and the 256-dim heads of qwen35 declare them; using head_dim there
would UNDER-count the KV and OOM), otherwise head_dim = embedding_length / head_count.
`n_kv_head` is `<arch>.attention.head_count_kv`, falling back to `attention.head_count`
(MHA). Where llama.cpp declares head_count_kv per layer (gemma4, nemotron_h) the MAX is
used: the KV buffer is sized for the widest layer.

bytes_per_elem (`bpe`) is the quant's per-element cost INCLUDING its block scale, exactly
as the estimator's table has it: a llama.cpp block is 32 elements with one fp16 scale, so
q8_0 = (32*8 bits + 16 bits) / 32 = 1.0625 B/elem and q4_0 = (32*4 + 16) / 32 = 0.5625.

Compute / activation overhead — how the estimator accounts for it (both factors ported):
  * per token:  eff_per_token = kv_bytes_per_token * 1.25   (compute buffer ~25% of KV)
  * per device: budget = (vram_total - min(weights, vram_total)) * 0.85   (headroom)
So `max_ctx = budget / eff_per_token` is the estimator's number: the VRAM headroom and
the per-token compute buffer are the same overhead, expressed once on the budget and once
on the cost. NOT ported on purpose: the estimator's RAM fallback (0.70 factor) and the
extra 0.90 margin start-dev-ai.sh applies when it picks `-c` — this tool audits capacity;
it does not choose the context a server runs with.

Estimate caps and floors (same as the estimator): the result is capped by the declared
`<arch>.context_length` and floored to a multiple of 1024 tokens.

Weights are the GGUF file size on disk (a proxy; with -ngl 999 + --no-mmap the weights
live in VRAM, which is why VRAM is the constraint). VRAM is summed across GPUs because
llama.cpp tensor-splits the model and the KV over them.

--- Output -------------------------------------------------------------------------
`results/models/context.json` (config.AUDIT_FILE): the artifact `--context adapted` reads.
It carries the metadata + a `models` map AND a flat per-slug mirror at the top level,
because config.resolve_context() looks the entry up as AUDIT_FILE[slug] (config.py is not
modified by this tool). Each entry has `ctx_max` = max(q8_0, q4_0) at its top level, which
is the number the adapted contract consumes.

Usage:
  python3 ggufbench/harness/tools/context-audit.py [--models GLOB] [--kv q8_0,q4_0]
      [--ref-ctx 32768] [--vram-gb N] [--json PATH] [--verify]

Exit codes: 0 audit written · 1 no models / no VRAM source · 2 usage error (--verify stub).
"""

from __future__ import annotations

import argparse
import datetime
import glob
import json
import struct
import subprocess
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
_PKG_DIR = _TOOLS_DIR.parent.parent                 # ggufbench/
_ROOT_DIR = _PKG_DIR.parent                         # workspace root
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from ggufbench import config

MIB = 1024 * 1024
GIB = 1024 * MIB

# bytes per element per KV-cache quant, scale overhead included (start-dev-ai.sh `bpe`).
KV_BYTES_PER_ELEM = {
    "f32": 4.0, "f16": 2.0, "bf16": 2.0,
    "q8_0": 1.0625, "q8_1": 1.125,
    "q4_0": 0.5625, "q4_1": 0.625,
    "q5_0": 0.6875, "q5_1": 0.75, "q6_0": 0.875,
    "iq4_nl": 0.5625, "iq4_xs": 0.5625,
    "q3_k": 0.40625, "q4_k": 0.5625, "q5_k": 0.6875, "q6_k": 0.84375,
}

COMPUTE_OVERHEAD = 1.25      # eff cost/token: KV + compute buffer (estimator's 1.25)
VRAM_HEADROOM = 0.85         # usable share of (VRAM - weights) (estimator's 0.85)
PIN_OK_BAND = 0.75           # a pin below 75% of the audited max is stale-low

CTX_FLOOR = 1024             # estimates are floored to a multiple of 1024 tokens
MIN_MODEL_BYTES = GIB        # the fleet audit ignores tiny files (embeddings, projectors)
EXCLUDED_ARCHS = ("dflash", "clip")   # drafts and vision projectors are not served alone

# GGUF value types: (struct fmt, size). Same table the shell script's readers use.
_SCALAR = {0: ("<b", 1), 1: ("<B", 1), 2: ("<h", 2), 3: ("<H", 2), 4: ("<I", 4),
           5: ("<i", 4), 6: ("<f", 4), 7: ("<?", 1), 10: ("<Q", 8), 11: ("<q", 8),
           12: ("<d", 8)}
# Arrays are consumed but only kept when the audit needs them (per-layer GQA / SWA).
_KEEP_ARRAYS = ("head_count_kv", "sliding_window_pattern", "full_attention_interval")


# --- GGUF header reader (metadata + tensor dims/types; never the tensor data) ---------

def read_gguf_header(path: Path) -> dict:
    """magic / version / kv-pairs + scalar metadata + the tensor-info section.

    Returns {"arch", "meta", "n_tensors", "has_vision", "has_mtp"}. A truncated header
    is not an error: whatever could be read is returned (same policy as the estimator)."""
    meta: dict = {}
    out = {"arch": "", "meta": meta, "n_tensors": 0, "has_vision": False,
           "has_mtp": False}
    with open(path, "rb") as f:
        def rd(n):
            b = f.read(n)
            if len(b) != n:
                raise EOFError
            return b

        def u32():
            return struct.unpack("<I", rd(4))[0]

        def u64():
            return struct.unpack("<Q", rd(8))[0]

        def rstr():
            return rd(u64()).decode("utf-8", "replace")

        try:
            if rd(4) != b"GGUF":
                raise ValueError("not a GGUF")
            u32()                                  # version
            n_tensors = u64()
            for _ in range(u64()):
                key = rstr()
                vt = u32()
                if vt == 8:                        # STRING
                    meta[key] = rstr()
                    if key == "general.architecture":
                        out["arch"] = meta[key]
                elif vt == 9:                      # ARRAY
                    et, n = u32(), u64()
                    if et == 8:
                        for _ in range(n):
                            rstr()
                    elif et in _SCALAR:
                        fmt, size = _SCALAR[et]
                        vals = list(struct.unpack("<" + str(n) + fmt[1:], rd(size * n)))
                        if any(k in key for k in _KEEP_ARRAYS):
                            meta[key] = vals
                    else:
                        raise ValueError("array etype %d" % et)
                elif vt in _SCALAR:                # scalars
                    fmt, size = _SCALAR[vt]
                    meta[key] = struct.unpack(fmt, rd(size))[0]
                else:
                    raise ValueError("vtype %d" % vt)
            out["arch"] = meta.get("general.architecture", "") or ""
            for _ in range(n_tensors):             # tensor info: name, dims, dtype, offset
                name = rstr()
                dims = [u64() for _ in range(u32())]
                u32()
                u64()
                low = name.lower()
                if low.startswith("clip.") or "vision" in low:
                    out["has_vision"] = True
                if "nextn" in low or "ffn_mtp" in low:
                    out["has_mtp"] = True
                out["n_tensors"] += 1
                del dims
        except (EOFError, ValueError, struct.error):
            pass
    return out


def model_dims(meta: dict) -> dict:
    """Architecture dimensions the KV formula needs (the estimator's `g()` lookups)."""
    arch = meta.get("general.architecture") or ""

    def g(name):
        for key in (f"{arch}.{name}", f"llama.{name}", name):
            if key in meta:
                return meta[key]
        return None

    def as_int(v):
        if isinstance(v, (list, tuple)):
            return max(v) if v else 0             # per-layer value: the widest one wins
        return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0

    n_embd = as_int(g("embedding_length"))
    n_head = as_int(g("attention.head_count"))
    head_dim = n_embd // n_head if n_head else 0
    return {
        "arch": arch,
        "layers": as_int(g("block_count")),
        "heads": n_head,
        "kv_heads": as_int(g("attention.head_count_kv")) or n_head,
        "head_dim": head_dim,
        "k_len": as_int(g("attention.key_length")) or head_dim,
        "v_len": as_int(g("attention.value_length")) or head_dim,
        "arch_max_ctx": as_int(g("context_length")),
    }


# --- The capacity math (pure: no IO, no server) --------------------------------------

def kv_bytes_per_token(dims: dict, quant: str) -> float:
    """KV bytes per token across all layers, for one cache quant type."""
    bpe = KV_BYTES_PER_ELEM.get(quant)
    if bpe is None:
        raise ValueError(f"unknown KV type: {quant!r} (known: "
                         f"{', '.join(sorted(KV_BYTES_PER_ELEM))})")
    if not (dims["layers"] and dims["kv_heads"] and dims["k_len"] and dims["v_len"]):
        raise ValueError("insufficient architecture metadata")
    return dims["layers"] * dims["kv_heads"] * (dims["k_len"] * bpe + dims["v_len"] * bpe)


def _budget_bytes(vram_bytes: int, weights_bytes: int) -> int:
    """VRAM left for KV + compute buffers, with the estimator's headroom factor."""
    return int((vram_bytes - min(weights_bytes, vram_bytes)) * VRAM_HEADROOM)


def max_ctx_one_slot(vram_bytes: int, weights_bytes: int, kv_bpt: float,
                     arch_max_ctx: int) -> int:
    """Largest context ONE slot can hold: capped by the declared context_length, floored
    to a multiple of 1024. 0 when the model does not even fit in VRAM."""
    if weights_bytes >= vram_bytes:
        return 0
    budget = _budget_bytes(vram_bytes, weights_bytes)
    est = int(budget // (kv_bpt * COMPUTE_OVERHEAD))
    if arch_max_ctx:
        est = min(est, arch_max_ctx)
    return max(0, (est // CTX_FLOOR) * CTX_FLOOR)


def slots_at_ref(vram_bytes: int, weights_bytes: int, kv_bpt: float, ref_ctx: int) -> int:
    """How many parallel slots fit when each one is given `ref_ctx` (`-c` is the TOTAL).

    Never 0 for a model that loads: one slot is always the practical minimum (its context
    is what the budget allows, not ref_ctx). 0 only when the weights do not fit."""
    if weights_bytes >= vram_bytes:
        return 0
    per_slot = ref_ctx * kv_bpt * COMPUTE_OVERHEAD
    return max(1, int(_budget_bytes(vram_bytes, weights_bytes) // per_slot))


def ctx_max(entry_q_results: list[int]) -> int:
    """The number the `adapted` contract consumes: the best audited context of the model."""
    return max(entry_q_results) if entry_q_results else 0


# --- Model profile: weights, pins, verdicts -------------------------------------------

def parse_pinned_ctx(tokens: list[str]) -> int | None:
    """The `-c`/`--ctx-size` a models/<model>.txt pins ('-c N' or '--ctx-size=N')."""
    pinned = None
    i = 0
    while i < len(tokens):
        name, sep, inline = tokens[i].partition("=")
        if name in ("-c", "--ctx-size"):
            value = inline if sep else (tokens[i + 1] if i + 1 < len(tokens) else "")
            try:
                pinned = int(value)
            except ValueError:
                pass
        i += 1
    return pinned


def model_notes(header: dict, dims: dict) -> list[str]:
    """Caveats that make the ported estimate a LOWER bound for this architecture."""
    meta = header["meta"]
    notes = []
    arch = dims["arch"]
    interval = meta.get(f"{arch}.full_attention_interval")
    if isinstance(interval, int) and interval > 1:
        notes.append(f"hybrid attention: only 1 of {interval} layers holds a KV cache "
                     f"(the ported estimator counts every layer)")
    pattern = meta.get(f"{arch}.attention.sliding_window_pattern")
    if isinstance(pattern, list):
        notes.append(f"sliding-window layers declared ({len(pattern)} layers): the "
                     f"estimator counts full KV for all of them")
    if any(k.startswith(f"{arch}.ssm.") for k in meta):
        notes.append("hybrid SSM architecture: only the attention layers hold a KV "
                     "cache, the estimator counts every layer")
    if header["has_vision"]:
        notes.append("vision weights in the same file: they count as weights")
    return notes


def audit_model(path: Path, vram_bytes: int, kv_types: list[str], ref_ctx: int) -> dict:
    """One model entry: weights, architecture dims, and per-quant max context / slots."""
    header = read_gguf_header(path)
    dims = model_dims(header["meta"])
    weights = path.stat().st_size
    entry = {
        "file": path.name,
        "weights_gb": round(weights / GIB, 2),
        "arch_max_ctx": dims["arch_max_ctx"],
        "dims": {k: dims[k] for k in ("arch", "layers", "kv_heads", "head_dim",
                                      "k_len", "v_len")},
    }
    per_quant = []
    for quant in kv_types:
        try:
            bpt = kv_bytes_per_token(dims, quant)
        except ValueError as exc:
            entry[quant] = {"error": str(exc)}
            continue
        max_ctx = max_ctx_one_slot(vram_bytes, weights, bpt, dims["arch_max_ctx"])
        entry[quant] = {
            "kv_bytes_per_token": round(bpt, 1),
            "max_ctx_1slot": max_ctx,
            "slots_at_ref": slots_at_ref(vram_bytes, weights, bpt, ref_ctx),
        }
        per_quant.append(max_ctx)
    entry["ctx_max"] = ctx_max(per_quant)
    notes = model_notes(header, dims)
    if notes:
        entry["notes"] = notes
    return entry


def pin_verdict(pin: int | None, audited_max: int) -> str:
    """Is the models/<model>.txt pin safe against the audited capacity?"""
    if pin is None:
        return "no pin"
    if audited_max <= 0:
        return "unknown (no estimate)"
    if pin > audited_max:
        return "OVER (OOM risk)"
    if pin < audited_max * PIN_OK_BAND:
        return "stale-low (headroom)"
    return "OK"


# --- Inputs: fleet + VRAM ------------------------------------------------------------

def default_model_glob() -> str:
    return str(config.MODELS_DIR / "*.gguf")


def select_models(pattern: str) -> list[Path]:
    """Fleet files: >= 1 GiB, no mmproj/clip projectors, no draft models, no embeddings."""
    out = []
    for p in sorted(Path(g) for g in glob.glob(pattern)):
        name = p.name.lower()
        if not p.is_file():
            continue
        if p.stat().st_size < MIN_MODEL_BYTES:
            continue
        if name.startswith("mmproj") or "dflash" in name or "draft" in name \
                or "embed" in name:
            continue
        out.append(p)
    return out


def vram_bytes_from_nvidia() -> int:
    """Sum of `memory.total` over every GPU (MiB, nounits), as start-dev-ai.sh sums free."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            text=True, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return 0
    return sum(int(x) for x in out.replace(",", " ").split() if x.strip().isdigit()) * MIB


# --- Reporting -----------------------------------------------------------------------

def fmt_ctx(n: int) -> str:
    if n <= 0:
        return "—"
    if n >= 1_000_000:
        return "%.1fM" % (n / 1_000_000)
    if n >= 1000:
        return "%dk" % (n // 1000)
    return str(n)


def print_table(rows: list[dict], kv_types: list[str], ref_ctx: int, vram_gib: float,
                json_path: Path) -> None:
    ref_k = f"{ref_ctx // 1024}K"
    head = ["model"]
    for q in kv_types:
        head += [f"{q} max@1", f"{q} slots@{ref_k}"]
    head += [".txt pin", "pin verdict"]
    body = []
    for row in rows:
        cells = [row["slug"]]
        for q in kv_types:
            res = row["entry"].get(q, {})
            cells += [fmt_ctx(res.get("max_ctx_1slot", 0)),
                      str(res.get("slots_at_ref", 0))]
        cells += [fmt_ctx(row["pin"]) if row["pin"] else "—", row["verdict"]]
        body.append(cells)
    widths = [max(len(head[i]), *(len(r[i]) for r in body)) if body else len(head[i])
              for i in range(len(head))]
    line = "  ".join(h.rjust(w) if i else h.ljust(w) for i, (h, w) in enumerate(zip(head, widths)))
    print(f"\nVRAM {vram_gib:.2f} GiB · ref per-slot ctx {ref_ctx} · KV {', '.join(kv_types)}"
          f" · estimate = (VRAM-weights)*{VRAM_HEADROOM} / (kv_bytes_per_token*"
          f"{COMPUTE_OVERHEAD})")
    print(line)
    print("-" * len(line))
    for cells in body:
        print("  ".join(c.rjust(w) if i else c.ljust(w)
                        for i, (c, w) in enumerate(zip(cells, widths))))
    print(f"\nWrote {json_path}")
    print("Note: the ported estimator counts a full KV cache for every layer. Arches that "
          "declare hybrid attention (full_attention_interval) or sliding windows are a "
          "LOWER bound: their real capacity is higher (see each entry's `notes`).")


def artifact_keys(path: Path) -> tuple[str, list[str]]:
    """(canonical slug, alias keys). The canonical key is config.slug of the FILE NAME.

    The aliases are the other identities run.py can hand to resolve_context(): the
    relative path the pool stores ('models/<file>.gguf') and the absolute path
    `--models all` / a name glob resolve to. config.audit_key() slugs whatever path it
    is given, so an audit keyed only by the file name would not be found by a run."""
    canonical = config.slug(path.name)
    aliases = []
    for form in (f"{config.MODELS_DIR.name}/{path.name}",
                 str(config.MODELS_DIR / path.name)):
        key = config.audit_key(form)
        if key != canonical and key not in aliases:
            aliases.append(key)
    return canonical, aliases


def build_artifact(entries: dict, aliases: dict[str, list[str]], vram_gib: float,
                   ref_ctx: int) -> dict:
    """Metadata + `models` map + a flat per-slug mirror: config.resolve_context() reads
    AUDIT_FILE[slug] directly, so the slugs must also live at the top level. Alias keys
    carry only ctx_max (what the contract consumes) and point back to the full entry."""
    artifact = {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "vram_gb": vram_gib,
        "ref_ctx": ref_ctx,
        "note": "top-level slug keys mirror models[] because config.resolve_context() "
                "looks the entry up as AUDIT_FILE[audit_key(model_path)]; alias_of "
                "marks the same model under another path form.",
        "models": entries,
    }
    artifact.update(entries)
    for canonical, keys in aliases.items():
        for key in keys:
            artifact[key] = {"ctx_max": entries[canonical]["ctx_max"],
                             "alias_of": canonical}
    return artifact


# --- CLI -----------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="context-audit.py",
        description="Audit the real context capacity of each model (1 slot) and how many "
                    "slots fit at a reference per-slot context.")
    ap.add_argument("--models", default=default_model_glob(),
                    help="GGUF glob (default: %(default)s, >=1GiB, no mmproj/draft/embed)")
    ap.add_argument("--kv", default="q8_0,q4_0",
                    help="KV cache types to audit, comma separated (default: %(default)s)")
    ap.add_argument("--ref-ctx", type=int, default=config.CONTEXT_FIXED,
                    help="reference per-slot context for the slots count (default: %(default)s)")
    ap.add_argument("--vram-gb", type=float, default=None,
                    help="VRAM budget in GiB instead of asking nvidia-smi")
    ap.add_argument("--json", default=str(config.AUDIT_FILE),
                    help="where to write the audit artifact (default: %(default)s)")
    ap.add_argument("--verify", action="store_true",
                    help="verify the estimates against a live server (NOT IMPLEMENTED YET)")
    args = ap.parse_args(argv)

    if args.verify:
        print("not implemented yet")
        return 2

    kv_types = [k.strip().lower() for k in args.kv.split(",") if k.strip()]
    try:
        for q in kv_types:
            if q not in KV_BYTES_PER_ELEM:
                raise ValueError(f"unknown KV type: {q!r} (known: "
                                 f"{', '.join(sorted(KV_BYTES_PER_ELEM))})")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.vram_gb is not None:
        vram = int(args.vram_gb * GIB)
    else:
        vram = vram_bytes_from_nvidia()
        if vram <= 0:
            print("error: no GPU reported by nvidia-smi — pass --vram-gb", file=sys.stderr)
            return 1
    if args.ref_ctx < CTX_FLOOR:
        print(f"error: --ref-ctx must be >= {CTX_FLOOR}", file=sys.stderr)
        return 2

    models = select_models(args.models)
    if not models:
        print(f"error: no model files matched {args.models}", file=sys.stderr)
        return 1

    entries: dict = {}
    aliases: dict[str, list[str]] = {}
    rows: list[dict] = []
    for path in models:
        entry = audit_model(path, vram, kv_types, args.ref_ctx)
        slug, alias_keys = artifact_keys(path)
        entries[slug] = entry
        aliases[slug] = alias_keys
        pin = parse_pinned_ctx(config.load_model_config_args(path))
        rows.append({"slug": slug, "entry": entry, "pin": pin,
                     "verdict": pin_verdict(pin, entry["ctx_max"])})

    json_path = Path(args.json)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    artifact = build_artifact(entries, aliases, round(vram / GIB, 2), args.ref_ctx)
    json_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    print_table(rows, kv_types, args.ref_ctx, vram / GIB, json_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
