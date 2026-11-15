"""Offline tests for ggufbench.fetch — the network layer is stubbed at `_open` and
`api_json`, so no test touches the network. The rules under test: verify-before-present,
mismatch deletes, resume re-verifies, the profile draft never writes a numeric -c,
the GPU golden rule for --bench, and explicit per-file states (R9)."""

import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from ggufbench import fetch
from ggufbench.tests.test_gguf_header import VSTRING, build_gguf

# El cos descarregat ha de ser un GGUF vàlid: el pas de capçalera el parseja de debò.
BODY = [build_gguf([("general.architecture", VSTRING, "qwen35moe")], ["output.weight"])]
BODY_BYTES = b"".join(BODY)
SHA_OK = hashlib.sha256(BODY_BYTES).hexdigest()
SHA_OTHER = "bb" * 32


def tree_entry(path: str, size: int, sha: str | None = SHA_OK) -> dict:
    e = {"type": "file", "path": path, "size": size}
    if sha:
        e["lfs"] = {"oid": f"sha256:{sha}", "size": size}
    return e


class FakeResp:
    """Stand-in for the urlopen response: yields the given bytes then b""."""

    def __init__(self, chunks: list[bytes], headers: dict | None = None):
        self._chunks = list(chunks)
        self.headers = headers or {}

    def __enter__(self) -> "FakeResp":
        return self

    def __exit__(self, *exc) -> None:
        self._chunks.clear()

    def read(self, n: int = -1) -> bytes:
        return self._chunks.pop(0) if self._chunks else b""


class TestQuantGuess(unittest.TestCase):
    def test_common_names(self) -> None:
        cases = {
            "Qwen3.8-27B-UD-Q3_K_XL.gguf": "UD-Q3_K_XL",
            "Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00001-of-00002.gguf": "IQ2_XS",
            "model-Q4_K_M.gguf": "Q4_K_M",
            "model-BF16.gguf": "BF16",
        }
        for name, want in cases.items():
            self.assertEqual(fetch.quant_guess(name), want, name)

    def test_unknown_is_none(self) -> None:
        self.assertIsNone(fetch.quant_guess("some-weights.gguf"))


class TestListRepo(unittest.TestCase):
    def test_filters_gguf_and_flags_companion(self) -> None:
        api = [tree_entry("Qwen3.8-27B-Q4_K_M.gguf", 15000),
               tree_entry("mmproj-F16.gguf", 885),
               tree_entry("README.md", 100),
               tree_entry("data/tokenizer.json", 500)]
        with mock.patch.object(fetch, "api_json", return_value=api):
            files, mmproj = fetch.list_repo("org/repo")
        names = [f.name for f in files]
        self.assertEqual(names, ["Qwen3.8-27B-Q4_K_M.gguf", "mmproj-F16.gguf"])
        self.assertEqual(mmproj, files[1])
        self.assertEqual(files[0].lfs_sha256, SHA_OK)

    def test_empty_repo_ggufless_is_not_an_error_here(self) -> None:
        with mock.patch.object(fetch, "api_json", return_value=[tree_entry("x.txt", 1)]):
            files, mmproj = fetch.list_repo("org/repo")
        self.assertEqual(files, [])
        self.assertIsNone(mmproj)


class TestDownloadVerified(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dest_dir = Path(self._tmp.name)

    def test_verified_file_lands_at_destination(self) -> None:
        f = fetch.RepoFile("m-Q4_K_M.gguf", len(BODY_BYTES), SHA_OK, "Q4_K_M")
        with mock.patch.object(fetch, "_open", return_value=FakeResp(BODY)):
            out = fetch.download_verified("org/repo", f, self.dest_dir, resume=True)
        self.assertEqual(out.verdict, "verified")
        self.assertTrue((self.dest_dir / f.name).exists())
        self.assertFalse((self.dest_dir / (f.name + ".part")).exists())

    def test_mismatch_deletes_and_fails(self) -> None:
        f = fetch.RepoFile("m-Q4_K_M.gguf", len(BODY_BYTES), SHA_OTHER, "Q4_K_M")
        with mock.patch.object(fetch, "_open", return_value=FakeResp(BODY)):
            out = fetch.download_verified("org/repo", f, self.dest_dir, resume=True)
        self.assertEqual(out.verdict, "failed")
        self.assertFalse((self.dest_dir / f.name).exists())

    def test_resume_hashes_the_prefix_and_sends_range(self) -> None:
        f = fetch.RepoFile("m.gguf", len(BODY_BYTES), SHA_OK, "Q4_K_M")
        part = self.dest_dir / (f.name + ".part")
        part.write_bytes(BODY_BYTES[:6])       # prefix already here
        seen: dict = {}

        def fake_open(req, **kw):
            seen["range"] = req.headers.get("Range")
            return FakeResp([BODY_BYTES[6:]])

        with mock.patch.object(fetch, "_open", side_effect=fake_open):
            out = fetch.download_verified("org/repo", f, self.dest_dir, resume=True)
        self.assertEqual(out.verdict, "verified")
        self.assertEqual(seen["range"], "bytes=6-")
        self.assertEqual(out.bytes_written, len(BODY_BYTES))

    def test_no_lfs_oid_is_unverified_never_benched_ready(self) -> None:
        f = fetch.RepoFile("m.gguf", 6, None, None)
        with mock.patch.object(fetch, "_open", return_value=FakeResp([b"model!"])):
            out = fetch.download_verified("org/repo", f, self.dest_dir, resume=False)
        self.assertEqual(out.verdict, "unverified")


class TestProposeProfile(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dest = Path(self._tmp.name)

    def test_mtp_adds_spec_flag_and_c_is_never_active(self) -> None:
        model = self.dest / "m.gguf"
        model.write_bytes(b"GGUF")
        facts = {"arch": "qwen35moe", "mtp_tensors": 4, "name": "m"}
        mmproj = self.dest / "mmproj-F16.gguf"
        mmproj.write_bytes(b"GGUF")
        p = fetch.propose_profile(model, facts, mmproj)
        text = p.read_text()
        self.assertIn("--spec-type draft-mtp", text)
        self.assertIn(f"--mmproj {mmproj}", text)
        for line in text.splitlines():
            if line.strip().startswith("-c"):
                self.fail(f"an active -c leaked into the draft: {line!r}")
        self.assertIn("probe-context", text)          # the TODO names the measuring tool

    def test_without_mtp_and_without_mmproj(self) -> None:
        model = self.dest / "m.gguf"
        model.write_bytes(b"GGUF")
        p = fetch.propose_profile(model, {"arch": "qwen35", "mtp_tensors": 0, "name": "m"}, None)
        text = p.read_text()
        self.assertNotIn("--spec-type", text)
        self.assertNotIn("--mmproj", text)


class TestMain(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dest = Path(self._tmp.name)
        self.api = [tree_entry("m-Q4_K_M.gguf", len(BODY_BYTES))]
        self.body = BODY

    def _patch_happy(self) -> None:
        p1 = mock.patch.object(fetch, "api_json", return_value=self.api)
        p2 = mock.patch.object(fetch, "_open", return_value=FakeResp(self.body))
        p3 = mock.patch.object(fetch, "_strata_alive", return_value=False)
        for pm in (p1, p2, p3):
            pm.start()
            self.addCleanup(pm.stop)

    def test_happy_path_writes_files_and_profile(self) -> None:
        self._patch_happy()
        rc = fetch.main(["--repo", "org/repo", "--dest", str(self.dest), "--yes"])
        self.assertEqual(rc, 0)
        self.assertTrue((self.dest / "m-Q4_K_M.gguf").exists())
        profiles = list(self.dest.glob("*.txt"))
        self.assertEqual(len(profiles), 1)

    def test_bench_delegates_with_the_fetched_models(self) -> None:
        self._patch_happy()
        with mock.patch.object(fetch, "_run_main", return_value=0) as run_main:
            rc = fetch.main(["--repo", "org/repo", "--dest", str(self.dest),
                             "--yes", "--bench"])
        self.assertEqual(rc, 0)
        argv = run_main.call_args[0][0]
        self.assertIn("--thinking off", " ".join(argv))
        self.assertIn("--context fixed", " ".join(argv))
        self.assertIn("m-Q4_K_M.gguf", " ".join(argv))

    def test_bench_refuses_while_strata_is_alive(self) -> None:
        self._patch_happy()
        with mock.patch.object(fetch, "_strata_alive", return_value=True), \
             mock.patch.object(fetch, "_run_main") as run_main:
            rc = fetch.main(["--repo", "org/repo", "--dest", str(self.dest),
                             "--yes", "--bench"])
        self.assertEqual(rc, fetch.EXIT_GPU_BUSY)
        run_main.assert_not_called()

    def test_repo_without_ggufs_exits_no_match(self) -> None:
        with mock.patch.object(fetch, "api_json",
                               return_value=[tree_entry("README.md", 1)]):
            rc = fetch.main(["--repo", "org/repo", "--dest", str(self.dest), "--yes"])
        self.assertEqual(rc, fetch.EXIT_NO_MATCH)

    def test_summary_json_records_per_file_states(self) -> None:
        self._patch_happy()
        out = self.dest.parent / "summary.json"
        rc = fetch.main(["--repo", "org/repo", "--dest", str(self.dest),
                         "--yes", "--json", str(out)])
        self.assertEqual(rc, 0)
        data = json.loads(out.read_text())
        states = {f["name"]: f["state"] for f in data["files"]}
        self.assertEqual(states, {"m-Q4_K_M.gguf": "verified"})

    def test_listing_failure_is_clean(self) -> None:
        import urllib.error
        with mock.patch.object(
            fetch, "api_json",
            side_effect=lambda url: (_ for _ in ()).throw(
                urllib.error.HTTPError(url, 401, "Unauthorized", {}, None)
            ),
        ):
            rc = fetch.main(["--repo", "org/repo", "--dest", str(self.dest), "--yes"])
        self.assertNotEqual(rc, 0)

    def test_listing_network_failure_is_clean_too(self) -> None:
        import urllib.error
        with mock.patch.object(
            fetch, "api_json",
            side_effect=urllib.error.URLError("connection reset by peer"),
        ):
            rc = fetch.main(["--repo", "org/repo", "--dest", str(self.dest), "--yes"])
        self.assertNotEqual(rc, 0)



if __name__ == "__main__":  # pragma: no cover
    unittest.main()
