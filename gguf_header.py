"""Minimal stdlib GGUF header reader for ggufbench.fetch.

Reads ONLY the header: magic/version, the metadata kv pairs the fact-sheet needs, and
the tensor names (for MTP detection). Tensors are never loaded; a 13 GB file costs one
sequential pass over its first bytes plus a few bytes per tensor entry. A truncated or
foreign-magic file is a clear ValueError, never a traceback."""

import struct
from pathlib import Path

_MAGIC = b"GGUF"

# gguf metadata value kinds we must at least SKIP correctly (arrays recurse).
_VSCALAR = {
    0: ("<B", 1), 1: ("<b", 1), 2: ("<H", 2), 3: ("<h", 2),
    4: ("<I", 4), 5: ("<i", 4), 6: ("<f", 4), 7: ("<?", 1),
    10: ("<Q", 8), 11: ("<q", 8), 12: ("<d", 8),
}
_VSTRING = 8
_VARRAY = 9
_VUINT32 = 4


def read_header(path: Path) -> dict:
    """Fact-sheet dict: arch, name, n_blocks, size_label (each None when absent) and
    mtp_tensors (count of tensor names carrying a nextn/ffn_mtp draft head)."""
    p = Path(path)

    with p.open("rb") as fh:
        def take(n: int) -> bytes:
            b = fh.read(n)
            if len(b) != n:
                raise ValueError(f"{p.name}: truncated GGUF header")
            return b

        def rstr() -> str:
            (n,) = struct.unpack("<Q", take(8))
            return take(n).decode("utf-8", errors="replace")

        if take(4) != _MAGIC:
            raise ValueError(f"{p.name}: not a GGUF file")
        (version,) = struct.unpack("<I", take(4))
        if version < 2:
            raise ValueError(f"{p.name}: GGUF version {version} not supported")
        tensor_count, kv_count = struct.unpack("<QQ", take(16))

        def skip_payload(vt: int) -> None:
            """Skip the VALUE payload of a metadata kv — the type is already read by
            the caller (reading it twice desynchronizes the stream: a float32 like
            rope.freq_base = 500000.0 then parses as a bogus value type)."""
            if vt == _VSTRING:
                rstr()
            elif vt == _VARRAY:
                (et,) = struct.unpack("<I", take(4))
                (n,) = struct.unpack("<Q", take(8))
                for _ in range(n):
                    skip_payload(et)
            elif vt in _VSCALAR:
                take(_VSCALAR[vt][1])
            else:
                raise ValueError(
                    f"{p.name}: unsupported GGUF metadata type {vt} (hex {vt:#x}) "
                    f"at byte {fh.tell()}")

        kv: dict[str, object] = {}
        for _ in range(kv_count):
            key = rstr()
            (vt,) = struct.unpack("<I", take(4))
            if vt == _VSTRING:
                kv[key] = rstr()
            elif vt == _VUINT32:
                kv[key] = struct.unpack("<I", take(4))[0]
            else:
                skip_payload(vt)

        mtp = 0
        for _ in range(tensor_count):
            name = rstr()
            if "nextn" in name or "ffn_mtp" in name:
                mtp += 1
            (n_dims,) = struct.unpack("<I", take(4))
            take(8 * n_dims)          # dims
            take(12)                  # ggml type (uint32) + data offset (uint64)

    arch = kv.get("general.architecture")
    return {
        "arch": arch,
        "name": kv.get("general.name"),
        "n_blocks": kv.get(f"{arch}.block_count") if arch else None,
        "size_label": kv.get("general.size_label"),
        "mtp_tensors": mtp,
    }
