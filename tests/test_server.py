import json
import tempfile
import unittest
from pathlib import Path

from benchmark import server, config

class TestBuildArgs(unittest.TestCase):
    def test_fixed_context(self):
        a = server.build_args("/p/m.gguf", "fixed", 8999)
        self.assertIn("-m", a)
        i = a.index("-m"); self.assertEqual(a[i+1], "/p/m.gguf")
        self.assertIn("-c", a)
        i = a.index("-c"); self.assertEqual(a[i+1], str(config.CONTEXT_FIXED))
        self.assertIn("--port", a)
        i = a.index("--port"); self.assertEqual(a[i+1], "8999")
    def test_explicit_context_int(self):
        a = server.build_args("/p/m.gguf", 4096, 8000)
        i = a.index("-c"); self.assertEqual(a[i+1], "4096")
    def test_flags_all_present(self):
        a = server.build_args("/p/m.gguf", "fixed", 8999)
        for flag in ["-ngl", "--flash-attn", "--no-mmap", "--jinja", "--temp", "--seed"]:
            self.assertIn(flag, a)

class TestModelConfigTxt(unittest.TestCase):
    """models/<model>.txt s'aplica al final (pot sobreescriure defaults)."""
    def _args_with_txt(self, txt_body, name="m.gguf"):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / Path(name).with_suffix(".txt").name).write_text(txt_body)
            return server.build_args(str(Path(d) / name), "fixed", 8999)
    def test_parser_skips_comments_blanks_and_joins(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "m.txt").write_text(
                "# comentari de capçalera\n\n-md /ruta/draft.gguf \\\n--mmproj /ruta/mm.gguf\n")
            self.assertEqual(config.load_model_config_args(Path(d) / "m.gguf"),
                             ["-md", "/ruta/draft.gguf", "--mmproj", "/ruta/mm.gguf"])
        # sense .txt al costat del gguf: cap flag extra
        self.assertEqual(server.describe_config("/p/sense_txt.gguf"), None)
    def test_txt_overrides_context(self):
        a = self._args_with_txt("-c 32000\n")
        self.assertEqual(a[a.index("-c") + 1], "32000")
        self.assertEqual(a.count("-c"), 1)  # el -c del harness no es duplica
    def test_txt_overrides_cache_k_only(self):
        a = self._args_with_txt("--cache-type-k q8_0\n")
        self.assertEqual(a.count("--cache-type-k"), 1)
        self.assertEqual(a[a.index("--cache-type-k") + 1], "q8_0")
        # la v del baseline es conserva
        self.assertIn("--cache-type-v", a)
        i = a.index("--cache-type-v"); self.assertEqual(a[i + 1], "q4_0")
    def test_txt_spec_type_appended_last(self):
        a = self._args_with_txt("--spec-type draft-mtp\n")
        self.assertIn("draft-mtp", a)
        self.assertGreater(a.index("--spec-type"), a.index("--jinja"))
    def test_infra_flags_filtered(self):
        a = self._args_with_txt("--port 1234 --host 0.0.0.0\n--spec-type draft-mtp\n")
        self.assertNotIn("1234", a)
        self.assertNotIn("0.0.0.0", a)
        self.assertIn("draft-mtp", a)
    def test_equals_form_and_comments(self):
        a = self._args_with_txt("# comentari\n\n--ctx-size=65536\n--cache-type-v=q8_0\n")
        # el -c del harness desapareix (el .txt defineix context) i no hi ha duplicats
        self.assertNotIn("-c", a)
        self.assertIn("--ctx-size=65536", a)
        self.assertIn("--cache-type-v=q8_0", a)
        self.assertEqual(a.count("--cache-type-k"), 1)  # només el del baseline

if __name__ == "__main__":
    unittest.main()