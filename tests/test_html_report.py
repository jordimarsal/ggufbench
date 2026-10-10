import shutil
import tempfile
import unittest
from pathlib import Path

from benchmark import config, html_report, report


def _mk(name="models/foo.gguf", engine="llama", code_score=0.9, tools_score=0.75,
        thinking=None, code_excluded=0):
    """Resultat mínim però complert (les 4 dimensions + metadades).
    thinking=None -> sense clau (fila legacy); "on"/"off" -> nova (R4)."""
    r = {"model": name, "engine": engine, "ts": "2026-10-09T10:00:00",
            "context_mode": "fixed", "tasks_version": "v1", "server_build": "b1234",
            "model_config_flags": "-c 16384 --flash-attn auto",
            "speed": {"passed": True, "turns": 0, "trace": [], "score": 0,
                      "speed_ms": 100, "gen_tps": 100.0, "prompt_tps": 300.0},
            "tools": {"passed": True, "turns": 0, "trace": [], "score": tools_score,
                      "by_lang": {}},
            "code": {"passed": True, "turns": 0, "trace": [], "score": code_score,
                     "by_lang": {"python": code_score}, "excluded": code_excluded},
            "agent": {"passed": True, "turns": 0, "trace": [], "score": 0.5,
                      "by_lang": {"python": 0.5}}}
    if thinking is not None:
        r["thinking"] = thinking
    return r


class TestRender(unittest.TestCase):
    def test_contains_model_dims_and_global(self):
        html = html_report.render([_mk()])
        self.assertIn("foo", html)
        self.assertIn("Global ponderat", html)
        self.assertIn("90%", html)                       # code 0.9
        self.assertIn("75%", html)                       # tools 0.75
        # global = .3*.75 + .3*.9 + .25*.5 + .15*1.0 = 0.77 (speed: és el mínim -> 1.0)
        self.assertIn("0.77", html)

    def test_self_contained_no_js_no_network(self):
        """La promesa del mòdul: doble clic i funciona. Cap script, cap recurs extern."""
        html = html_report.render([_mk()])
        self.assertNotIn("<script", html)
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)

    def test_sorted_by_global_desc(self):
        html = html_report.render([_mk(name="models/zzz-second.gguf", code_score=0.1, tools_score=0.1),
                                   _mk(name="models/aaa-first.gguf")])
        self.assertLess(html.index("aaa-first"), html.index("zzz-second"))

    def test_engine_badge_for_strata(self):
        html = html_report.render([_mk(name="strata-iq3_xxs", engine="strata")])
        self.assertIn("badge strata", html)

    def test_missing_lang_cell(self):
        html = html_report.render([_mk()])   # només python a by_lang
        self.assertIn('class="miss">—</td>', html)

    def test_code_by_level_shown_when_present(self):
        # R5 hard_code_tier / R4 discriminative_tasks: easy/hard/expert a la fitxa
        m = _mk()
        m["code"]["by_level"] = {"easy": 1.0, "hard": 0.25, "expert": 0.0}
        html = html_report.render([m])
        self.assertIn("code per nivell:", html)
        self.assertIn("easy 100%", html)
        self.assertIn("hard 25%", html)
        self.assertIn("expert 0%", html)

    def test_think_badges_and_excluded_line(self):
        # R4+R5 thinking_batches: badge de mode + recompte d'excloses
        html = html_report.render([_mk(thinking="off", code_excluded=2),
                                   _mk("models/bar.gguf", thinking="on")])
        self.assertIn("think:off", html)
        self.assertIn("think:on", html)
        self.assertIn("excloses code: 2", html)

    def test_legacy_row_without_thinking_has_no_badge(self):
        html = html_report.render([_mk()])
        self.assertNotIn("think:", html)
        self.assertIn("excloses code: 0", html)

    def test_heat_cells_have_readable_solid_background(self):
        # El text de la matriu s'ha de llegir a tot el rang: fons sòlid rgb +
        # color per lluminància (mai alfa ni inherit).
        html = html_report.render([_mk(code_score=0.1), _mk("models/bar.gguf",
                                                           code_score=0.9)])
        self.assertNotIn("rgba(52,211,153", html)
        self.assertNotIn("color:inherit", html)
        self.assertIn("0.10", html)
        self.assertIn("0.90", html)

    def test_every_model_row_shows_think_mode(self):
        # Totes les seccions per model (matriu + barres) marquen el mode, DAVANT
        # del nom (l'ellipsis retallava el badge al final en columnes estretes).
        html = html_report.render([_mk(thinking="off"), _mk("models/bar.gguf",
                                                             thinking="on")])
        self.assertEqual(html.count("think:off"), 8)  # ranking + 6 barres + matriu
        self.assertEqual(html.count("think:on"), 8)
        self.assertIn('<span class="badge">think:off</span> foo', html)
        self.assertIn('title="foo"', html)

    def test_no_by_level_section_when_absent(self):
        html = html_report.render([_mk()])   # pool vell sense by_level
        self.assertNotIn("code per nivell", html)

    def test_escaped_flags(self):
        """model_config_flags és text lliure del .txt: ha d'arribar escapament."""
        m = _mk()
        m["model_config_flags"] = "-c 16384 <script>alert(1)</script>"
        html = html_report.render([m])
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;", html)

    def test_banner_only_with_mixed_dates(self):
        self.assertNotIn("Condicions barrejades", html_report.render([_mk()]))
        other = _mk()
        other["ts"] = "2026-09-01T10:00:00"
        self.assertIn("Condicions barrejades", html_report.render([_mk(), other]))


class TestMain(unittest.TestCase):
    def test_writes_report_html(self):
        import json
        tmp = Path(tempfile.mkdtemp())
        old_results, old_pool = config.RESULTS_DIR, report.POOL_FILE
        config.RESULTS_DIR = tmp / "results"
        report.POOL_FILE = tmp / "pool.jsonl"
        try:
            report.POOL_FILE.write_text(json.dumps(_mk()) + "\n")
            rc = html_report.main()
            self.assertEqual(rc, 0)
            out = config.RESULTS_DIR / "report.html"
            self.assertTrue(out.is_file())
            self.assertTrue(out.read_text(encoding="utf-8").startswith("<!doctype html>"))
        finally:
            shutil.rmtree(tmp)
            config.RESULTS_DIR = old_results
            report.POOL_FILE = old_pool


if __name__ == "__main__":
    unittest.main()
