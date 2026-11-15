"""Offline tests for gguf_header.read_header — a synthetic GGUF written by the test.

The parser is stdlib-only and read-only: magic/version, kv pairs (strings and the
scalar types it must skip), tensor names (for MTP detection) — tensors are NEVER
loaded. A truncated or foreign-magic file is a clear error, not a traceback."""

import struct
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ggufbench import gguf_header

VSTRING = 8
VUINT32 = 4
VUINT64 = 10


def _wstr(buf: bytearray, s: str) -> None:
    b = s.encode()
    buf += struct.pack("<Q", len(b))
    buf += b


def build_gguf(kv: list[tuple[str, int, object]], tensors: list[str]) -> bytes:
    """GGUF v3 with the given metadata and one 1-dim tensor per name (no data)."""
    out = bytearray(b"GGUF")
    out += struct.pack("<I", 3)                 # version
    out += struct.pack("<Q", len(tensors))      # tensor_count
    out += struct.pack("<Q", len(kv))           # kv_count
    for key, vtype, val in kv:
        _wstr(out, key)
        out += struct.pack("<I", vtype)
        if vtype == VSTRING:
            _wstr(out, str(val))
        elif vtype == VUINT32:
            out += struct.pack("<I", int(val))
        elif vtype == VUINT64:
            out += struct.pack("<Q", int(val))
        elif vtype == 6:  # float32
            out += struct.pack("<f", float(val))
        elif vtype == 9:  # array: (elem_type, list_of_elems)
            et, elems = val
            out += struct.pack("<I", et)
            out += struct.pack("<Q", len(elems))
            for el in elems:
                if et == VSTRING:
                    _wstr(out, str(el))
                elif et == 4:
                    out += struct.pack("<I", int(el))
                elif et == 6:
                    out += struct.pack("<f", float(el))
                else:  # pragma: no cover
                    raise AssertionError(f"array elem type {et} not supported")
        else:  # pragma: no cover — the tests only use these
            raise AssertionError(f"fixture does not support vtype {vtype}")
    for name in tensors:
        _wstr(out, name)
        out += struct.pack("<I", 1)             # n_dims
        out += struct.pack("<Q", 4)             # dim0
        out += struct.pack("<I", 0)             # ggml type (F32)
        out += struct.pack("<Q", 0)             # offset
    return bytes(out)


class TestReadHeader(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def _write(self, data: bytes, name: str = "model.gguf") -> Path:
        p = self.dir / name
        p.write_bytes(data)
        return p

    def test_parses_arch_name_and_blocks(self) -> None:
        p = self._write(build_gguf(
            [("general.architecture", VSTRING, "qwen35moe"),
             ("general.name", VSTRING, "Test-Model"),
             ("qwen35moe.block_count", VUINT32, 47)],
            tensors=["output.weight", "blk.0.attn_norm.weight"]))
        facts = gguf_header.read_header(p)
        self.assertEqual(facts["arch"], "qwen35moe")
        self.assertEqual(facts["name"], "Test-Model")
        self.assertEqual(facts["n_blocks"], 47)
        self.assertEqual(facts["mtp_tensors"], 0)

    def test_detects_nextn_mtp_tensors(self) -> None:
        p = self._write(build_gguf(
            [("general.architecture", VSTRING, "qwen35moe")],
            tensors=["output.weight", "blk.40.nextn.ffn_norm.weight",
                     "blk.40.nextn.e_proj.weight"]))
        facts = gguf_header.read_header(p)
        self.assertEqual(facts["mtp_tensors"], 2)

    def test_detects_ffn_mtp_key_spelling(self) -> None:
        p = self._write(build_gguf(
            [("general.architecture", VSTRING, "qwen35")],
            tensors=["blk.63.ffn_mtp.proj.weight"]))
        self.assertEqual(gguf_header.read_header(p)["mtp_tensors"], 1)

    def test_size_label_when_present(self) -> None:
        p = self._write(build_gguf(
            [("general.architecture", VSTRING, "qwen35moe"),
             ("general.size_label", VSTRING, "35B-A3B")],
            tensors=["output.weight"]))
        self.assertEqual(gguf_header.read_header(p)["size_label"], "35B-A3B")

    def test_real_world_kv_shapes_parse_through(self) -> None:
        """Regression from the first real file (unsloth Llama-3.2-1B, 2026-11-15):
        the kv set carries float32 scalars (rope.freq_base = 500000.0) and the big
        tokenizer arrays. skip_payload must read the VALUE payload only — the loop
        already consumed the type — or the stream desynchronizes and a float's bytes
        come back as a bogus value type."""
        tokens = ["t%d" % i for i in range(200)]
        p = self._write(build_gguf(
            [("general.architecture", VSTRING, "llama"),
             ("llama.rope.freq_base", 6, 500000.0),          # float32
             ("llama.attention.key_length", 6, 64.0),         # float32
             ("tokenizer.ggml.tokens", 9, (VSTRING, tokens)),
             ("tokenizer.ggml.token_type", 9, (4, [1] * 200))],
            tensors=["output.weight", "blk.0.nextn.ffn_norm.weight"]))
        facts = gguf_header.read_header(p)
        self.assertEqual(facts["arch"], "llama")
        self.assertEqual(facts["mtp_tensors"], 1)

    def test_missing_optionals_are_none(self) -> None:
        p = self._write(build_gguf([], tensors=[]))
        facts = gguf_header.read_header(p)
        self.assertIsNone(facts["arch"])
        self.assertIsNone(facts["name"])
        self.assertIsNone(facts["n_blocks"])
        self.assertIsNone(facts["size_label"])
        self.assertEqual(facts["mtp_tensors"], 0)

    def test_foreign_magic_is_a_clear_error(self) -> None:
        p = self._write(b"NOPE" + b"\x00" * 32)
        with self.assertRaisesRegex(ValueError, "not a GGUF"):
            gguf_header.read_header(p)

    def test_truncated_file_is_a_clear_error(self) -> None:
        good = build_gguf(
            [("general.architecture", VSTRING, "qwen35moe")],
            tensors=["output.weight"])
        p = self._write(good[: len(good) // 2])
        with self.assertRaisesRegex(ValueError, "truncated"):
            gguf_header.read_header(p)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
