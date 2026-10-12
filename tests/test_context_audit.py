"""Unit tests for harness/tools/context-audit.py: the ported KV math only.

No servers, no fleet GGUFs: the capacity functions take synthetic dims dicts, and the
header reader is exercised against a synthetic GGUF header built in memory."""

import importlib.util
import json
import os
import struct
import tempfile
import unittest
from pathlib import Path

from ggufbench import config

_MODULE_PATH = Path(__file__).resolve().parents[1] / "harness" / "tools" / "context-audit.py"
_spec = importlib.util.spec_from_file_location("context_audit", _MODULE_PATH)
ca = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ca)

GIB = 1024 ** 3

# Synthetic 28-layer GQA model (the shape of a 7-8B): 8 KV heads, 128-dim heads.
META = {
    "general.architecture": "qwen3",
    "qwen3.block_count": 28,
    "qwen3.embedding_length": 2048,
    "qwen3.attention.head_count": 16,
    "qwen3.attention.head_count_kv": 8,
    "qwen3.context_length": 131072,
}
DIMS = {
    "arch": "qwen3", "layers": 28, "heads": 16, "kv_heads": 8,
    "head_dim": 128, "k_len": 128, "v_len": 128, "arch_max_ctx": 131072,
}
VRAM = 16 * GIB
WEIGHTS = 8 * GIB


def _str(s: str) -> bytes:
    b = s.encode("utf-8")
    return struct.pack("<Q", len(b)) + b


def _kv(key: str, vtype: int, payload: bytes) -> bytes:
    return _str(key) + struct.pack("<I", vtype) + payload


class TestModelDims(unittest.TestCase):
    def test_head_dim_and_kv_heads_from_metadata(self):
        dims = ca.model_dims(META)
        self.assertEqual(dims, DIMS)

    def test_kv_heads_fall_back_to_head_count_when_absent(self):
        meta = {k: v for k, v in META.items() if not k.endswith("head_count_kv")}
        dims = ca.model_dims(meta)
        self.assertEqual(dims["kv_heads"], 16)          # MHA: KV for every head

    def test_per_layer_head_count_kv_uses_the_widest_layer(self):
        # gemma4 / nemotron_h declare head_count_kv as an array: the KV buffer is sized
        # for the widest layer, so the max is the number that must be used.
        meta = dict(META, **{"qwen3.attention.head_count_kv": [2, 4, 4, 8, 4]})
        self.assertEqual(ca.model_dims(meta)["kv_heads"], 8)

    def test_declared_key_and_value_length_win_over_head_dim(self):
        # MLA / 256-dim heads: head_dim would UNDER-count the KV and cause OOM.
        meta = dict(META, **{"qwen3.attention.key_length": 256,
                             "qwen3.attention.value_length": 256})
        dims = ca.model_dims(meta)
        self.assertEqual((dims["k_len"], dims["v_len"]), (256, 256))

    def test_llama_prefixed_metadata_is_a_fallback(self):
        meta = {"general.architecture": "unknown-arch",
                "llama.block_count": 32, "llama.embedding_length": 4096,
                "llama.attention.head_count": 32, "llama.context_length": 8192}
        dims = ca.model_dims(meta)
        self.assertEqual((dims["layers"], dims["kv_heads"], dims["head_dim"]),
                         (32, 32, 128))


class TestKvBytesPerToken(unittest.TestCase):
    def test_q8_0_and_q4_0_match_the_ported_formula(self):
        # bytes/token/layer = kv_heads * head_dim * bpe * 2 (K+V); q8_0 = 1.0625
        # (32 elements * 8 bits + one fp16 scale) / 32, q4_0 = 0.5625 (4 bits + scale).
        self.assertEqual(ca.kv_bytes_per_token(DIMS, "q8_0"), 28 * 8 * 128 * 1.0625 * 2)
        self.assertEqual(ca.kv_bytes_per_token(DIMS, "q4_0"), 28 * 8 * 128 * 0.5625 * 2)
        self.assertEqual(ca.kv_bytes_per_token(DIMS, "q8_0"), 60928.0)
        self.assertEqual(ca.kv_bytes_per_token(DIMS, "q4_0"), 32256.0)

    def test_k_and_v_are_counted_separately(self):
        dims = dict(DIMS, k_len=128, v_len=64)
        self.assertEqual(ca.kv_bytes_per_token(dims, "q4_0"),
                         28 * 8 * (128 * 0.5625 + 64 * 0.5625))

    def test_unknown_quant_raises(self):
        with self.assertRaises(ValueError) as cm:
            ca.kv_bytes_per_token(DIMS, "q9_9")
        self.assertIn("unknown KV type", str(cm.exception))

    def test_missing_metadata_raises_instead_of_guessing(self):
        with self.assertRaises(ValueError) as cm:
            ca.kv_bytes_per_token(dict(DIMS, layers=0), "q4_0")
        self.assertIn("insufficient architecture metadata", str(cm.exception))


class TestMaxContextOneSlot(unittest.TestCase):
    def test_estimate_is_the_budget_over_the_effective_cost_per_token(self):
        # budget = (16 GiB - 8 GiB) * 0.85; cost = kv * 1.25 (compute buffer).
        budget = int((VRAM - WEIGHTS) * ca.VRAM_HEADROOM)
        expected = min(int(budget // (32256.0 * ca.COMPUTE_OVERHEAD)), 131072)
        got = ca.max_ctx_one_slot(VRAM, WEIGHTS, 32256.0, 131072)
        self.assertEqual(got, (expected // 1024) * 1024)
        self.assertEqual(got, 131072)          # the declared context_length caps it

    def test_result_is_floored_to_a_multiple_of_1024(self):
        got = ca.max_ctx_one_slot(VRAM, WEIGHTS, 60928.0, 131072)
        self.assertEqual(got % 1024, 0)
        self.assertEqual(got, 95232)

    def test_declared_context_length_is_a_cap(self):
        self.assertEqual(ca.max_ctx_one_slot(VRAM, WEIGHTS, 32256.0, 32768), 32768)

    def test_weights_that_do_not_fit_leave_no_context(self):
        self.assertEqual(ca.max_ctx_one_slot(VRAM, VRAM + 1, 32256.0, 131072), 0)

    def test_q4_0_always_reaches_at_least_q8_0(self):
        # the audit must never claim q8_0 holds more context than q4_0.
        for weights in (2 * GIB, 8 * GIB, 14 * GIB):
            self.assertGreaterEqual(
                ca.max_ctx_one_slot(VRAM, weights, ca.kv_bytes_per_token(DIMS, "q4_0"), 131072),
                ca.max_ctx_one_slot(VRAM, weights, ca.kv_bytes_per_token(DIMS, "q8_0"), 131072))


class TestSlotsAtRef(unittest.TestCase):
    def test_slots_count_the_total_context_the_server_pins(self):
        # -c is the TOTAL across slots: n slots at 32768 each cost n * 32768 of KV.
        budget = int((VRAM - WEIGHTS) * ca.VRAM_HEADROOM)
        self.assertEqual(ca.slots_at_ref(VRAM, WEIGHTS, 32256.0, 32768),
                         int(budget // (32768 * 32256.0 * ca.COMPUTE_OVERHEAD)))
        self.assertEqual(ca.slots_at_ref(VRAM, WEIGHTS, 60928.0, 32768), 2)

    def test_more_kv_always_means_fewer_or_equal_slots(self):
        self.assertGreaterEqual(
            ca.slots_at_ref(VRAM, WEIGHTS, ca.kv_bytes_per_token(DIMS, "q4_0"), 32768),
            ca.slots_at_ref(VRAM, WEIGHTS, ca.kv_bytes_per_token(DIMS, "q8_0"), 32768))

    def test_one_slot_is_the_practical_minimum(self):
        # A huge per-slot context does not fit, but the model still runs with one slot.
        self.assertEqual(ca.slots_at_ref(VRAM, WEIGHTS, 32256.0, 1_000_000), 1)

    def test_weights_that_do_not_fit_give_zero_slots(self):
        self.assertEqual(ca.slots_at_ref(VRAM, VRAM + 1, 32256.0, 32768), 0)

    def test_slots_are_consistent_with_the_one_slot_estimate(self):
        # n slots at ref_ctx must not exceed what one slot at the audited max allows.
        kv = ca.kv_bytes_per_token(DIMS, "q8_0")
        one = ca.max_ctx_one_slot(VRAM, WEIGHTS, kv, 131072)
        n = ca.slots_at_ref(VRAM, WEIGHTS, kv, 32768)
        self.assertLessEqual(n * 32768, one)


class TestCtxMax(unittest.TestCase):
    def test_ctx_max_is_the_best_audited_context(self):
        self.assertEqual(ca.ctx_max([95232, 131072]), 131072)
        self.assertEqual(ca.ctx_max([]), 0)


class TestPinnedContext(unittest.TestCase):
    def test_reads_dash_c_and_the_equals_form(self):
        self.assertEqual(ca.parse_pinned_ctx(["-c", "160000"]), 160000)
        self.assertEqual(ca.parse_pinned_ctx(["--ctx-size=131072"]), 131072)
        self.assertEqual(ca.parse_pinned_ctx(["--ctx-size", "65536"]), 65536)

    def test_last_pin_wins_like_the_server_parses_args(self):
        self.assertEqual(ca.parse_pinned_ctx(["-c", "1000", "--ctx-size", "2000"]), 2000)

    def test_no_pin_is_none_and_a_bad_value_is_ignored(self):
        self.assertIsNone(ca.parse_pinned_ctx(["--temp", "0.2"]))
        self.assertIsNone(ca.parse_pinned_ctx([]))
        self.assertIsNone(ca.parse_pinned_ctx(["-c", "not-a-number"]))


class TestPinVerdict(unittest.TestCase):
    def test_pin_within_the_band_is_ok(self):
        self.assertEqual(ca.pin_verdict(131072, 131072), "OK")
        self.assertEqual(ca.pin_verdict(int(131072 * ca.PIN_OK_BAND), 131072), "OK")

    def test_pin_above_the_audited_max_is_an_oom_risk(self):
        self.assertEqual(ca.pin_verdict(131073, 131072), "OVER (OOM risk)")

    def test_pin_far_below_the_audited_max_is_stale(self):
        self.assertEqual(ca.pin_verdict(16000, 131072), "stale-low (headroom)")

    def test_no_pin_and_no_estimate_are_reported_as_such(self):
        self.assertEqual(ca.pin_verdict(None, 131072), "no pin")
        self.assertEqual(ca.pin_verdict(4096, 0), "unknown (no estimate)")


class TestModelNotes(unittest.TestCase):
    def test_hybrid_and_swa_architectures_are_flagged_as_a_lower_bound(self):
        header = {"meta": {"qwen35moe.full_attention_interval": 4,
                           "qwen35moe.attention.sliding_window_pattern": [1, 0, 1]},
                  "has_vision": False, "has_mtp": False, "n_tensors": 0, "arch": "qwen35moe"}
        dims = {"arch": "qwen35moe"}
        notes = ca.model_notes(header, dims)
        self.assertEqual(len(notes), 2)
        self.assertIn("1 of 4 layers", notes[0])

    def test_plain_architectures_get_no_notes(self):
        header = {"meta": dict(META), "has_vision": False, "has_mtp": False,
                  "n_tensors": 0, "arch": "qwen3"}
        self.assertEqual(ca.model_notes(header, DIMS), [])


class TestSelectModels(unittest.TestCase):
    def test_filters_small_files_projectors_and_drafts(self):
        with tempfile.TemporaryDirectory() as d:
            keep = Path(d) / "Qwen3.8-27B-UD-Q4_K_M.gguf"
            keep.touch()
            os.truncate(keep, 2 * GIB)                   # sparse: no real data written
            for name in ("mmproj-F16.gguf", "dflash-Muse-30B.gguf", "nomic-embed.gguf",
                         "tiny.gguf"):
                p = Path(d) / name
                p.touch()
                os.truncate(p, 1024 if name == "tiny.gguf" else 2 * GIB)
            got = [p.name for p in ca.select_models(str(Path(d) / "*.gguf"))]
            self.assertEqual(got, ["Qwen3.8-27B-UD-Q4_K_M.gguf"])


class TestGgufHeaderReader(unittest.TestCase):
    """A synthetic GGUF header (metadata + one tensor record): the reader must get the
    dims the formula needs without ever touching tensor data."""

    def _write_synthetic_gguf(self, path: Path) -> None:
        body = b"GGUF" + struct.pack("<I", 3) + struct.pack("<Q", 1) + struct.pack("<Q", 7)
        body += _kv("general.architecture", 8, _str("qwen3"))
        body += _kv("qwen3.block_count", 4, struct.pack("<I", 28))
        body += _kv("qwen3.embedding_length", 4, struct.pack("<I", 2048))
        body += _kv("qwen3.attention.head_count", 4, struct.pack("<I", 16))
        body += _kv("qwen3.attention.head_count_kv", 9,
                    struct.pack("<I", 4) + struct.pack("<Q", 3)
                    + struct.pack("<3i", 4, 8, 8))
        body += _kv("qwen3.context_length", 4, struct.pack("<I", 131072))
        body += _kv("tokenizer.ggml.tokens", 9,
                    struct.pack("<I", 8) + struct.pack("<Q", 2) + _str("a") + _str("b"))
        body += _str("blk.0.ffn_mtp") + struct.pack("<I", 2) + struct.pack("<2Q", 2048, 2048)
        body += struct.pack("<I", 8) + struct.pack("<Q", 0)
        path.write_bytes(body)

    def test_reads_metadata_and_tensor_info(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "synthetic.gguf"
            self._write_synthetic_gguf(p)
            header = ca.read_gguf_header(p)
            dims = ca.model_dims(header["meta"])
            self.assertEqual(dims, DIMS)
            self.assertEqual(dims["kv_heads"], 8)        # max of the per-layer array
            self.assertEqual(header["n_tensors"], 1)
            self.assertTrue(header["has_mtp"])
            self.assertFalse(header["has_vision"])
            self.assertNotIn("tokenizer.ggml.tokens", header["meta"])   # not kept

    def test_a_truncated_header_is_not_fatal(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "partial.gguf"
            self._write_synthetic_gguf(p)
            p.write_bytes(p.read_bytes()[:120])
            header = ca.read_gguf_header(p)
            self.assertEqual(header["meta"].get("general.architecture"), "qwen3")


class TestArtifactContract(unittest.TestCase):
    """D1: the artifact `--context adapted` reads. config.resolve_context() looks the
    entry up as AUDIT_FILE[audit_key(model_path)], so every path form run.py can hand
    it must resolve to the same audited ctx_max."""

    FILE = "Qwen3.8-27B-UD-Q4_K_M.gguf"

    def _entry(self, q8=95232, q4=131072):
        return {
            "weights_gb": 15.7, "arch_max_ctx": 262144, "ctx_max": max(q8, q4),
            "q8_0": {"max_ctx_1slot": q8, "slots_at_ref": 2},
            "q4_0": {"max_ctx_1slot": q4, "slots_at_ref": 5},
        }

    def test_artifact_keys_cover_the_identities_the_run_cli_can_produce(self):
        canonical, alias_keys = ca.artifact_keys(config.MODELS_DIR / self.FILE)
        self.assertEqual(canonical, config.slug(self.FILE))
        # the identity the pool stores, and the absolute path `--models all` resolves to
        self.assertIn(config.audit_key(f"models/{self.FILE}"), alias_keys)
        self.assertIn(config.audit_key(str(config.MODELS_DIR / self.FILE)), alias_keys)

    def test_adapted_reads_the_audited_ctx_max_under_every_path_form(self):
        canonical, alias_keys = ca.artifact_keys(config.MODELS_DIR / self.FILE)
        artifact = ca.build_artifact({canonical: self._entry()}, {canonical: alias_keys},
                                     31.84, 32768)
        with tempfile.TemporaryDirectory() as d:
            audit = Path(d) / "context.json"
            audit.write_text(json.dumps(artifact), encoding="utf-8")
            with config.override(AUDIT_FILE=audit):
                for model_path in (self.FILE, f"models/{self.FILE}",
                                   str(config.MODELS_DIR / self.FILE)):
                    with self.subTest(model_path=model_path):
                        self.assertEqual(
                            config.resolve_context("adapted", model_path), 131072)

    def test_artifact_keeps_the_metadata_and_the_models_map(self):
        canonical, alias_keys = ca.artifact_keys(config.MODELS_DIR / self.FILE)
        artifact = ca.build_artifact({canonical: self._entry()}, {canonical: alias_keys},
                                     31.84, 32768)
        self.assertEqual(artifact["vram_gb"], 31.84)
        self.assertEqual(artifact["ref_ctx"], 32768)
        self.assertIn("generated", artifact)
        self.assertEqual(artifact["models"][canonical]["ctx_max"], 131072)
        self.assertEqual(artifact[canonical]["ctx_max"], 131072)      # the flat mirror
        for key in alias_keys:
            self.assertEqual(artifact[key], {"ctx_max": 131072, "alias_of": canonical})

    def test_fmt_ctx_is_compact(self):
        self.assertEqual(ca.fmt_ctx(0), "—")
        self.assertEqual(ca.fmt_ctx(999), "999")
        self.assertEqual(ca.fmt_ctx(32768), "32k")
        self.assertEqual(ca.fmt_ctx(1_500_000), "1.5M")


if __name__ == "__main__":
    unittest.main()
