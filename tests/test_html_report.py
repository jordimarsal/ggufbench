import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ggufbench import config, html_report


def _mk(name="models/foo.gguf", engine="llama", code_score=0.9, tools_score=0.75,
        thinking=None, code_excluded=0):
    """Minimal but complete result (the 4 dimensions + metadata).
    thinking=None -> no key (legacy row); "on"/"off" -> new (R4)."""
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
        self.assertIn("Weighted global", html)
        self.assertIn("90%", html)                       # code 0.9
        self.assertIn("75%", html)                       # tools 0.75
        # global = .3*.75 + .3*.9 + .25*.5 + .15*1.0 = 0.77 (speed: it is the minimum -> 1.0)
        self.assertIn("0.77", html)

    def test_self_contained_no_external_resources(self):
        """The promise of the module: double click and it works — offline, no dependency.
        It may carry the one inline script that orders the ranking, but nothing fetched:
        no src=, no external URL."""
        html = html_report.render([_mk()])
        self.assertLessEqual(html.count("<script"), 1)            # the order control
        self.assertIn('<script>', html)
        self.assertNotIn("<script src", html)
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
        html = html_report.render([_mk()])   # only python in by_lang
        self.assertIn('class="miss">—</td>', html)

    def test_code_by_level_shown_when_present(self):
        # R5 hard_code_tier / R4 discriminative_tasks: easy/hard/expert in the card
        m = _mk()
        m["code"]["by_level"] = {"easy": 1.0, "hard": 0.25, "expert": 0.0}
        html = html_report.render([m])
        self.assertIn("code by level:", html)
        self.assertIn("easy 100%", html)
        self.assertIn("hard 25%", html)
        self.assertIn("expert 0%", html)

    def test_think_badges_and_excluded_line(self):
        # R4+R5 thinking_batches: mode badge + count of excluded
        html = html_report.render([_mk(thinking="off", code_excluded=2),
                                   _mk("models/bar.gguf", thinking="on")])
        self.assertIn("think:off", html)
        self.assertIn("think:on", html)
        self.assertIn("excluded code: 2", html)

    def test_legacy_row_without_thinking_has_no_badge(self):
        html = html_report.render([_mk()])
        self.assertNotIn("think:", html)
        self.assertIn("excluded code: 0", html)

    def test_heat_cells_have_readable_solid_background(self):
        # The matrix text must read across the whole range: solid rgb background +
        # color by luminance (never alpha nor inherit).
        html = html_report.render([_mk(code_score=0.1), _mk("models/bar.gguf",
                                                           code_score=0.9)])
        self.assertNotIn("rgba(52,211,153", html)
        self.assertNotIn("color:inherit", html)
        self.assertIn("0.10", html)
        self.assertIn("0.90", html)

    def test_every_model_row_shows_think_mode(self):
        # Every per-model section (matrix + bars) marks the mode, BEFORE
        # the name (the ellipsis used to clip the badge at the end in narrow columns).
        html = html_report.render([_mk(thinking="off"), _mk("models/bar.gguf",
                                                             thinking="on")])
        base, _, rec = html.partition("Recommendations (by use)")
        # ranking + 6 dimension rows + matrix + the "by task set" block (§C9)
        self.assertEqual(base.count("think:off"), 9)
        self.assertEqual(base.count("think:on"), 9)
        self.assertIn('<span class="badge">think:off</span> foo', base)
        self.assertIn('title="foo"', base)
        self.assertIn("think:off", rec)  # also in the cards
        self.assertIn("think:on", rec)

    def test_bar_rows_align_to_four_column_grid(self):
        # No bars: rows are text (trow: name + value), no .bar/.fill
        # (the 4-column .rank grid crushed the name into the 22px track).
        html = html_report.render([_mk(thinking="off")])
        self.assertNotIn('class="bar"', html)
        self.assertNotIn('class="fill', html)
        self.assertIn('class="trow"', html)

    def test_recommendation_cards(self):
        # One card per winner (model+mode) with data, badge and use cases.
        a = _mk("models/aaa.gguf", code_score=0.5, thinking="off")
        a["speed"]["speed_ms"] = 10
        a["speed"]["gen_tps"] = 500.0
        a["tools"]["score"] = 1.0
        b = _mk("models/bbb.gguf", code_score=0.9, thinking="on")
        html = html_report.render([a, b])
        self.assertIn("Recommendations (by use)", html)
        self.assertIn("aaa", html)  # wins speed/throughput/tools
        self.assertIn("bbb", html)  # wins global/code/thinking
        self.assertIn("Fastest", html)
        self.assertIn("Best code", html)
        self.assertIn("excluded code:", html)

    def test_recommendations_empty_pool(self):
        self.assertNotIn("Recomanacions", html_report.render([]))

    def test_no_by_level_section_when_absent(self):
        html = html_report.render([_mk()])   # old pool without by_level
        self.assertNotIn("code by level", html)

    def test_escaped_flags(self):
        """model_config_flags is free text from the .txt: it must arrive escaped."""
        m = _mk()
        m["model_config_flags"] = "-c 16384 <script>alert(1)</script>"
        html = html_report.render([m])
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;", html)

    def test_banner_only_with_mixed_dates(self):
        self.assertNotIn("Mixed conditions", html_report.render([_mk()]))
        other = _mk()
        other["ts"] = "2026-09-01T10:00:00"
        self.assertIn("Mixed conditions", html_report.render([_mk(), other]))

    def test_banner_and_chip_when_the_pool_mixes_task_sets(self):
        """§C9: same date, same version — still two different measurements. The page has
        to say so (chip in the header + banner), not let 12-task and 16-task rows look
        like one experiment."""
        a, b = _mk(name="models/aaa.gguf"), _mk(name="models/bbb.gguf")
        a["task_signature"] = "16/60/60"
        b["task_signature"] = "12/60/28"
        html = html_report.render([a, b])
        self.assertIn("Mixed conditions", html)
        self.assertIn("task sets", html)
        self.assertIn("16/60/60: 1 rows", html)
        self.assertIn('task sets <a href="#set-', html)   # header chip links to the blocks

    def test_uniform_task_sets_do_not_trigger_the_banner(self):
        a, b = _mk(name="models/aaa.gguf"), _mk(name="models/bbb.gguf")
        for r in (a, b):
            r["task_signature"] = "16/60/60"
        html = html_report.render([a, b])
        self.assertNotIn("Mixed conditions", html)   # same day, same set
        self.assertNotIn('task sets <a href="#set-', html)


class TestTaskSetDisplay(unittest.TestCase):
    """§C9 follow-up: every row states the test version it was measured with, the board
    can be ordered by set (static blocks + the in-page control), and the section titles
    take their task counts from the data instead of a hardcoded number."""

    def _rows(self):
        a = _mk(name="models/big-set.gguf", code_score=0.9, tools_score=0.9)
        a["task_signature"] = "16/60/60"
        a["tasks_version"] = "v3"
        a["tools"]["trace"] = [{"id": "t"}] * 16
        a["code"]["trace"] = [{"id": "c"}] * 60
        a["agent"]["trace"] = [{"id": "g"}] * 60
        b = _mk(name="models/old-set.gguf", code_score=0.5, tools_score=0.5)
        b["task_signature"] = "8/60/24"
        b["tasks_version"] = "v3"
        b["tools"]["trace"] = [{"id": "t"}] * 8
        return a, b

    def test_every_row_carries_its_test_version(self):
        a, b = self._rows()
        html = html_report.render([a, b])
        self.assertIn('<span class="badge set">v3·16/60/60</span>', html)
        self.assertIn('<span class="badge set">v3·8/60/24</span>', html)
        self.assertIn("version v3·16/60/60", html)     # also in the row's detail line

    def test_static_by_set_section_and_anchors(self):
        a, b = self._rows()
        html = html_report.render([a, b])
        self.assertIn("By task set", html)
        self.assertEqual(html.count('<div class="setblock"'), 2)
        # The header chip links to the blocks, and the ids match.
        self.assertIn('href="#set-16-60-60"', html)
        self.assertIn('id="set-16-60-60"', html)
        self.assertIn("8/60/24 tasks", html)
        self.assertIn("1 row ", html)                  # each block counts its rows

    def test_order_control_lists_every_sort_and_marks_the_static_one(self):
        a, b = self._rows()
        html = html_report.render([a, b], sort="version")
        self.assertIn('id="sortkey"', html)
        for key in ("global", "tools", "code", "agent", "speed", "version"):
            self.assertIn(f'<option value="{key}"', html)
        self.assertIn('<option value="version" selected>version</option>', html)

    def test_rows_carry_the_data_for_client_side_ordering(self):
        a, b = self._rows()
        row = [l for l in html_report.render([a, b]).splitlines()
               if 'data-set="v3·16/60/60"' in l][0]
        for attr in ('data-g=', 'data-tools=', 'data-code=', 'data-agent=', 'data-speed=',
                     'data-setsize="136"', 'data-set="v3·16/60/60"'):
            self.assertIn(attr, row)

    def test_static_order_follows_the_requested_sort(self):
        a, b = self._rows()
        by_global = html_report.render([a, b])                    # a wins on global
        self.assertLess(by_global.index("big-set"), by_global.index("old-set"))
        # ordered by set: the bigger set (16/60/60) comes first even if the other row's
        # own set is older — never interleaving two conditions (that is the point).
        by_set = html_report.render([b, a], sort="version")
        self.assertLess(by_set.index("big-set"), by_set.index("old-set"))
        by_code = html_report.render([b, a], sort="code")
        self.assertLess(by_code.index("big-set"), by_code.index("old-set"))

    def test_section_titles_take_task_counts_from_the_data(self):
        a, b = self._rows()
        html = html_report.render([a, b])
        self.assertIn("Code (60 tasks · 4 languages)", html)
        self.assertIn("Multi-step agent (60 tasks)", html)
        self.assertIn("Tool-calling (16 tasks)", html)
        self.assertNotIn("Tool-calling (8 tasks)", html)   # the old hardcoded number

    def test_minor_titles_have_their_own_colour(self):
        """The by-set block header — the page's minor title — is not painted with the muted
        body colour: --label is the single knob for it (amber, same family as the
        mixed-conditions banner: the task set is a caveat, not a score)."""
        html = html_report.render([_mk()])
        self.assertIn("--label:#f59e0b", html)
        self.assertIn(".setblock h3{", html)
        self.assertIn("color:var(--label)", html)
        self.assertIn('<span class="setmeta">', html)
        self.assertNotIn('<span class="miss">· label', html)

    def test_set_named_in_the_mixed_conditions_banner(self):
        a, b = self._rows()
        static = html_report.render([a, b])
        banner = static.split('<div class="banner">')[1].split("</div>")[0]
        self.assertIn("task sets", banner)
        self.assertIn("16/60/60: 1 rows", banner)


class TestMain(unittest.TestCase):
    def test_writes_report_html(self):
        import json
        tmp = Path(tempfile.mkdtemp())
        try:
            with config.override(RESULTS_DIR=tmp / "results",
                                 POOL_FILE=tmp / "pool.jsonl"):
                config.POOL_FILE.write_text(json.dumps(_mk()) + "\n")
                rc = html_report.main()
                self.assertEqual(rc, 0)
                out = config.RESULTS_DIR / "report.html"
                self.assertTrue(out.is_file())
                self.assertTrue(out.read_text(encoding="utf-8").startswith("<!doctype html>"))
        finally:
            shutil.rmtree(tmp)


class TestCompare(unittest.TestCase):
    """MILLORA §4.5: the compare view — winner coloring per metric, delta math,
    tie handling (neutral, no color), mixed-conditions banner, exclusions visible,
    header cards and the self-contained + picker contract."""

    def _pair(self):
        """aaa wins code (+80%) and throughput (+25%); bbb wins latency (+20%);
        tools/agent/prompt-tps are exact ties; code levels missing on both sides."""
        a = _mk("models/aaa.gguf", code_score=0.9, thinking="off")
        b = _mk("models/bbb.gguf", code_score=0.5, thinking="off")
        a["speed"].update(speed_ms=100, gen_tps=125.0, prompt_tps=300.0)
        b["speed"].update(speed_ms=80, gen_tps=100.0, prompt_tps=300.0)
        return a, b

    def _render(self, **kw):
        a, b = self._pair()
        return html_report.render_compare(a, b, pool=[a, b], **kw)

    def _static(self, html):
        """Server-rendered body only: the inline JS source builds the same markup,
        so literal counting must skip the script blocks."""
        return html.split('<div id="cmp-body">', 1)[1].split("</main>", 1)[0]

    def test_winner_coloring_and_verdict(self):
        # better green, worse red, and the winner's delta % in the verdict line
        html = self._render()
        self.assertIn('<div class="mval good">90%</div>', html)      # aaa code wins
        self.assertIn('<div class="mval bad">50%</div>', html)       # bbb code loses
        self.assertIn('<div class="verdict good">Better code overall. +80%</div>', html)
        self.assertIn('<div class="mval good">80 ms</div>', html)    # bbb latency wins (lower)
        self.assertIn('<div class="mval bad">100 ms</div>', html)
        self.assertIn('<div class="verdict good">Faster prompt + reply latency. +20%</div>', html)
        self.assertIn('<div class="verdict good">Faster generation. +25%</div>', html)
        self.assertIn('<div class="verdict good">Higher weighted global. +14%</div>', html)
        self.assertIn('<div class="verdict good">Higher pool rank. +50%</div>', html)

    def test_wall_clock_metric(self):
        """C8: total wall clock as a first-class compare metric (lower wins,
        human format, verdict with the winner's delta)."""
        a, b = self._pair()
        a["wall_time_s"], b["wall_time_s"] = 246.0, 2077.0
        html = self._static(html_report.render_compare(a, b, pool=[a, b]))
        self.assertIn("Wall clock (total run)", html)
        self.assertIn('<div class="mval good">4m 06s</div>', html)
        self.assertIn('<div class="mval bad">34m 37s</div>', html)
        self.assertIn('<div class="verdict good">Less wall clock. +88%</div>', html)

    def test_wall_clock_missing_is_neutral(self):
        """Pre-C8 rows: the wall row renders '—' on both sides, never judged."""
        pa = html_report._pack(self._pair()[0], 1, 2, 80)
        pb = html_report._pack(self._pair()[1], 2, 2, 80)
        wall = html_report._COMPARE_SECTIONS[0][1][2]
        row = html_report._cmp_row(pa, pb, wall)
        self.assertIn('<div class="mval miss">—</div>', row)
        self.assertIn('<span class="miss">—</span>', row)
        self.assertNotIn("mval good", row)

    def test_judge_delta_math(self):
        # exact winner/delta pairs; delta is the winner's improvement over the loser
        self.assertEqual(html_report._judge(125.0, 100.0, False), (0, 25.0))
        self.assertEqual(html_report._judge(100.0, 125.0, False), (1, 25.0))
        self.assertEqual(html_report._judge(80, 100, True)[0], 0)
        self.assertAlmostEqual(html_report._judge(80, 100, True)[1], 20.0)
        self.assertEqual(html_report._judge(5.0, 5.0, False), (None, None))   # tie
        self.assertEqual(html_report._judge(None, 5.0, False), (None, None))  # missing
        self.assertEqual(html_report._judge(3.0, 0.0, False), (0, None))      # no baseline

    def test_fmt_delta(self):
        self.assertEqual(html_report._fmt_delta(24.0), "+24%")
        self.assertEqual(html_report._fmt_delta(9.46), "+9.5%")   # small wins stay visible
        self.assertEqual(html_report._fmt_delta(None), "")

    def test_tie_neutral_no_verdict(self):
        # equal values -> neutral class, no color, no % verdict
        static = self._static(self._render())
        self.assertIn('<div class="mval tie">75%</div>', static)        # tools 0.75 both
        self.assertIn('<div class="mval tie">300 t/s</div>', static)    # prompt tps both
        self.assertEqual(static.count('<span class="tie">tie</span>'), 3)
        self.assertNotIn("Better tool-calling.", static)

    def test_split_section_gets_no_badge(self):
        # Speed splits 1-1 (aaa: gen t/s; bbb: latency) -> no summary badge there
        static = self._static(self._render())
        self.assertIn("<h2>Speed</h2>", static)
        self.assertIn("<h2>Tools</h2>", static)      # all ties -> no badge
        self.assertIn("<h2>Agent</h2>", static)
        # Global and Code are won outright: badge = mean of the won deltas
        self.assertIn('<h2>Global <span class="secbadge good"', static)
        self.assertIn("+32%</span></h2>", static)    # mean(+14%, +50%)
        self.assertIn('<h2>Code <span class="secbadge good"', static)
        self.assertIn("+80%</span></h2>", static)

    def test_missing_metric_is_neutral_dash(self):
        static = self._static(self._render())
        self.assertEqual(static.count('<div class="mval miss">—</div>'), 8)  # 3 levels x 2 sides + wall x 2 (pre-C8 rows)
        self.assertEqual(static.count('<div class="verdict"><span class="miss">—</span></div>'), 4)  # 3 missing code-level rows + 1 wall-clock row

    def test_exclusions_visible_per_metric(self):
        a, b = self._pair()
        a["code"]["excluded"] = 4
        a["code"]["by_level"] = {"hard": 0.25}
        a["code"]["trace"] = [{"id": "x", "level": "hard", "excluded": True},
                              {"id": "y", "level": "hard", "excluded": True}]
        html = html_report.render_compare(a, b, pool=[a, b])
        # 90% with 4 exclusions must not read as a clean win
        self.assertIn('<div class="mval good">90% <small>(4 excl.)</small></div>', html)
        # single-sided tier (bbb has no by_level): neutral, no winner coloring
        self.assertIn('<div class="mval">25% <small>(2 excl.)</small></div>', html)

    def test_mixed_conditions_banner(self):
        self.assertNotIn("Mixed conditions", self._static(self._render()))  # same ts + version
        a, b = self._pair()
        b["ts"] = "2026-09-01T10:00:00"
        static = self._static(html_report.render_compare(a, b, pool=[a, b]))
        self.assertIn("Mixed conditions", static)
        self.assertIn("2026-10-09 · tasks v1 vs 2026-09-01", static)
        a2, b2 = self._pair()
        b2["tasks_version"] = "v2"                    # same day, older tasks -> also mixed
        self.assertIn("Mixed conditions",
                      self._static(html_report.render_compare(a2, b2, pool=[a2, b2])))

    def test_mixed_conditions_when_only_the_task_set_differs(self):
        """§C9: same day, same version label, different task counts. The label cannot
        tell them apart; the signature can, and the page must say it."""
        a, b = self._pair()
        a["task_signature"], b["task_signature"] = "16/60/60", "12/60/28"
        static = self._static(html_report.render_compare(a, b, pool=[a, b]))
        self.assertIn("Mixed conditions", static)
        self.assertIn("the task sets differ (16/60/60 vs 12/60/28 tasks)", static)

    def test_same_set_and_day_no_banner(self):
        a, b = self._pair()
        a["task_signature"] = b["task_signature"] = "16/60/60"
        self.assertNotIn("Mixed conditions",
                         self._static(html_report.render_compare(a, b, pool=[a, b])))

    def test_picker_pack_carries_the_task_signature(self):
        """The client-side banner re-renders from the embedded packs: a signature they
        do not carry would silently disable the §C9 warning on the JS path."""
        r = _mk()
        r["task_signature"] = "16/60/60"
        self.assertEqual(html_report._pack(r, 1, 1, 100)["sig"], "16/60/60")

    def test_header_cards_content(self):
        a, b = self._pair()
        a["environment"] = {"gpu": ["RTX 5080 16GB", "RTX 5080 16GB"],
                            "driver": "580.82.09", "os": "Linux-test", "ram_gb": 60}
        html = html_report.render_compare(a, b, pool=[a, b])
        self.assertIn("rank #1 of 2", html)
        self.assertIn("rank #2 of 2", html)
        self.assertIn("RTX 5080 16GB × 2", html)
        self.assertNotIn("driver 580.82.09", html)            # driver dropped by sanitizer
        self.assertIn("60 GB RAM", html)
        self.assertIn("-c 16384 --flash-attn auto", html)     # model_config_flags
        self.assertIn("not recorded (pre-C5 row)", html)      # bbb predates the env field

    def _fixture_home_path(self):
        """Row with absolute path under home dir in flags."""
        m = _mk(name="models/foo.gguf")
        m["model_config_flags"] = "-c 16384 --mmproj /home/someone/x/mmproj-F16.gguf"
        return m

    def _fixture_other_abs_path(self):
        """Row with absolute path outside home dir in flags."""
        m = _mk(name="models/bar.gguf")
        m["model_config_flags"] = "--config /opt/secret/thing -c 8192"
        return m

    def test_sanitize_home_path_in_render_and_compare(self):
        """Absolute paths under home → ~/basename; other abs paths → [local] basename."""
        a = self._fixture_home_path()
        html = html_report.render([a])
        self.assertIn("~/someone/x/mmproj-F16.gguf", html)
        self.assertNotIn("/home/someone/", html)
        a2, b2 = self._pair()
        a2["model_config_flags"] = "-c 16384 --mmproj /home/someone/x/mmproj-F16.gguf"
        html_c = html_report.render_compare(a2, b2, pool=[a2, b2])
        self.assertIn("~/someone/x/mmproj-F16.gguf", html_c)
        self.assertNotIn("/home/someone/", html_c)

    def test_sanitize_other_abs_path(self):
        """Paths not under home → [local] basename."""
        a = self._fixture_other_abs_path()
        html = html_report.render([a])
        self.assertIn("[local] thing", html)
        self.assertNotIn("/opt/secret/", html)

    def test_picker_embedded_json_sanitized(self):
        """cmp-data block carries sanitized flags/env, not raw ones."""
        a = _mk("models/foo.gguf")
        a["model_config_flags"] = "/home/user/a/b.gguf"
        a["environment"] = {"gpu": ["RTX 5080"], "driver": "99.99", "os": "Linux-test", "ram_gb": 32}
        html = html_report.render_compare(a, a, pool=[a])
        # embedded JSON must have redacted path and no driver string
        self.assertIn('"f":"~/user/a/b.gguf"', html)
        self.assertNotIn('/home/user/', html)
        self.assertNotIn('driver', html.split('<script id="cmp-data')[1].split('</script>')[0])

    def test_environment_line_sanitized(self):
        """Driver version dropped; OS family only (via platform.system()); GPU+RAM kept."""
        import platform as _platform
        a = _mk()
        a["environment"] = {"gpu": ["RTX 5080 16GB", "RTX 5080 16GB"],
                            "driver": "580.82.09", "os": "Linux-test", "ram_gb": 60}
        b = _mk("models/bar.gguf")
        html = html_report.render_compare(a, b, pool=[a, b])
        self.assertNotIn("driver", html)
        self.assertIn(_platform.system(), html)
        self.assertIn("RTX 5080 16GB × 2", html)
        self.assertIn("60 GB RAM", html)

    def test_n1_caveat_visible(self):
        self.assertIn("n=1", self._render())

    def test_self_contained_with_picker(self):
        html = self._render()
        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)
        # inline picker: two selects + swap + embedded compact pool JSON
        self.assertIn('<select id="sel-a"', html)
        self.assertIn('<select id="sel-b"', html)
        self.assertIn('id="swap"', html)
        self.assertIn('id="cmp-data"', html)
        self.assertIn('"s":"aaa"', html)
        self.assertIn('"s":"bbb"', html)

    def test_escaped_flags(self):
        a, b = self._pair()
        a["model_config_flags"] = "-c 16384 <script>alert(1)</script>"
        html = html_report.render_compare(a, b, pool=[a, b])
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;", html)


class TestCompareWrite(unittest.TestCase):
    """write_default_compare: same render+path ownership as write_default_report."""

    def test_writes_compare_html_with_default_pair(self):
        import json
        tmp = Path(tempfile.mkdtemp())
        try:
            with config.override(RESULTS_DIR=tmp / "results",
                                 POOL_FILE=tmp / "pool.jsonl"):
                off = _mk("models/top.gguf", thinking="off")
                on = _mk("models/top.gguf", thinking="on")
                on["code"]["score"] = 0.7
                config.POOL_FILE.write_text(
                    json.dumps(off) + "\n" + json.dumps(on) + "\n", encoding="utf-8")
                out = html_report.write_default_compare()
                self.assertTrue(out.is_file())
                self.assertEqual(out.name, "compare.html")
                self.assertTrue(out.read_text(encoding="utf-8").startswith("<!doctype html>"))
        finally:
            shutil.rmtree(tmp)

    def test_default_pair_prefers_same_model_other_mode(self):
        top_off = _mk("models/top.gguf", thinking="off")
        top_on = _mk("models/top.gguf", thinking="on")
        other = _mk("models/other.gguf", thinking="off")
        top_off["code"]["score"] = 0.99                     # clearly the top row
        a, b = html_report._default_pair([other, top_on, top_off])
        self.assertEqual(config.slug(a["model"]), config.slug(b["model"]))
        self.assertEqual({a.get("thinking"), b.get("thinking")}, {"off", "on"})

    def test_no_pair_no_write(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            with config.override(RESULTS_DIR=tmp):
                self.assertIsNone(html_report.write_default_compare(pool=[]))
                self.assertIsNone(html_report.write_default_compare(pool=[_mk()]))
        finally:
            shutil.rmtree(tmp)


class TestOptimalBadge(unittest.TestCase):
    """C8: the dominant thinking mode carries the ★ optimal badge in the
    ranking and the model card; rows without wall_time_s get no marker."""

    @staticmethod
    def pair(with_wall=True):
        a = _mk(thinking="off")
        b = _mk(thinking="on")
        if with_wall:
            a["wall_time_s"] = 450.0
            b["wall_time_s"] = 2100.0
        return [a, b]

    def test_badge_on_dominant_row(self):
        html = html_report.render(self.pair())
        self.assertIn("★ optimal", html)
        # exactly twice per winning model: once in the ranking, once in its card
        self.assertEqual(html.count("★ optimal"), 2)

    def test_no_badge_without_wall(self):
        html = html_report.render(self.pair(with_wall=False))
        self.assertNotIn("★ optimal", html)


class TestRunSpreadCells(unittest.TestCase):
    """--runs N: the ranking row and the model card carry the spread of the global
    ('0.84 <small>±26</small>'). Single-run rows — every row of today's pool — do not."""

    @staticmethod
    def _multi(name="models/foo.gguf"):
        """Same row measured 3 times: traces carry the per-run outcomes and the section
        scores are what graders aggregate (mean over tasks of passes/attempts)."""
        r = _mk(name=name, tools_score=5 / 6, code_score=7 / 9)
        r["agent"]["score"] = 5 / 6
        r["tools"]["runs"] = 3
        r["tools"]["trace"] = [{"id": "t1", "passed": True, "runs": [1, 1, 1]},
                               {"id": "t2", "passed": False, "runs": [1, 1, 0]}]
        r["code"]["runs"] = 3
        r["code"]["trace"] = [{"id": "c1", "lang": "python", "passed": True, "runs": [1, 1, 1]},
                              {"id": "c2", "lang": "python", "passed": True, "runs": [1, 1, 1]},
                              {"id": "c3", "lang": "python", "passed": False, "runs": [1, 0, 0]}]
        r["agent"]["runs"] = 3
        r["agent"]["trace"] = [{"id": "a1", "lang": "python", "passed": True, "runs": [1, 1, "x"]},
                               {"id": "a2", "lang": "python", "passed": False, "runs": [1, 1, 0]}]
        return r

    def test_ranking_row_shows_the_spread(self):
        html = html_report.render([self._multi()])
        self.assertIn('class="gval top">0.84 <small>±26</small>', html)

    def test_model_card_shows_the_spread(self):
        a = self._multi("models/aaa.gguf")
        b = self._multi("models/bbb.gguf")
        html = html_report.render_compare(a, b, pool=[a, b])
        self.assertEqual(html.count('<div class="v">0.84 <small>±26</small>'), 2)  # both cards
        self.assertIn('"gs":0.264575131106459', html)   # the picker JSON mirrors the pack

    def test_single_run_rows_show_no_spread(self):
        html = html_report.render([_mk()])
        self.assertNotIn("±", html)
        self.assertNotIn('"gs"', html)
        a, b = _mk("models/aaa.gguf"), _mk("models/bbb.gguf")
        html = html_report.render_compare(a, b, pool=[a, b])
        self.assertNotIn('<div class="v">0.77 <small>', html)   # both cards stay bare
        self.assertNotIn('"gs"', html)


class TestRetiredGray(unittest.TestCase):
    """Retired models (stems in the tracked registry or in models/retired/) render gray
    as a record and never appear in Recommendations (by use)."""

    def _render_foo_retired(self, **kw):
        with mock.patch.object(html_report, "_retired_stems", return_value={"foo"}):
            return html_report.render([_mk()], **kw)

    def test_retired_row_is_gray_with_badge(self):
        html = self._render_foo_retired()
        static = html.split('<div id="cmp-body">', 1)[0] if '<div id="cmp-body">' in html else html
        self.assertIn('<div class="trow retired">', static)
        self.assertIn('<span class="badge">retired</span>', static)
        self.assertIn("gray = retired model (record only)", static)
        self.assertIn(".retired .heat", static)

    def test_retired_excluded_from_recommendations(self):
        html = self._render_foo_retired()
        self.assertNotIn("Recommendations (by use)", html)

    def test_non_retired_unchanged(self):
        with mock.patch.object(html_report, "_retired_stems", return_value=set()):
            html = html_report.render([_mk()])
        self.assertNotIn("trow retired", html)
        self.assertNotIn(">retired</span>", html)
        self.assertNotIn("gray = retired", html)
        self.assertIn("Recommendations (by use)", html)

    def test_retired_dir_missing_is_empty(self):
        # models/retired/ and the registry live outside the repo (absent on CI
        # checkouts). The lookup must degrade to "nothing retired", never crash.
        self._isolated(models_dir=Path("/nonexistent-xyz"),
                       retired_file=Path("/nonexistent-xyz/retired.json"))
        self.assertEqual(html_report._retired_stems(), set())

    def test_registry_greys_rows_without_archived_profiles(self):
        """The regression this fixes: the profiles under models/retired/ were deleted
        (they duplicated the registry), and the gray marking vanished with them."""
        with tempfile.TemporaryDirectory() as d:
            reg = Path(d) / "retired.json"
            reg.write_text('{"retired": [{"stem": "foo", "date": "2026-10-13"}]}')
            self._isolated(models_dir=Path(d), retired_file=reg)
            self.assertEqual(html_report._retired_stems(), {"foo"})
            html = html_report.render([_mk()])
        self.assertIn('<div class="trow retired">', html)
        self.assertIn("gray = retired model (record only)", html)

    def test_registry_and_archived_profiles_are_unioned(self):
        with tempfile.TemporaryDirectory() as d:
            reg = Path(d) / "retired.json"
            reg.write_text('{"retired": [{"stem": "foo"}]}')
            (Path(d) / "retired").mkdir()
            (Path(d) / "retired" / "bar.txt").write_text("-c 4096")
            self._isolated(models_dir=Path(d), retired_file=reg)
            self.assertEqual(html_report._retired_stems(), {"foo", "bar"})

    def test_broken_registry_degrades_to_empty(self):
        for payload in ("{not json", '{"retired": []}', '{"retired": null}'):
            with tempfile.TemporaryDirectory() as d:
                reg = Path(d) / "retired.json"
                reg.write_text(payload)
                self._isolated(models_dir=Path(d), retired_file=reg)
                self.assertEqual(html_report._retired_stems(), set())

    def test_bare_string_registry_entries_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            reg = Path(d) / "retired.json"
            reg.write_text('{"retired": ["foo"]}')
            self._isolated(models_dir=Path(d), retired_file=reg)
            self.assertEqual(html_report._retired_stems(), {"foo"})

    def test_shipped_registry_is_wellformed(self):
        """The registry that ships with the repo parses and greys by file stem (the
        pool row's identity), so models/ can be re-pruned without touching the code."""
        self.addCleanup(setattr, html_report, "_RETIRED_STEMS", None)
        html_report._RETIRED_STEMS = None
        stems = html_report._retired_stems()
        self.assertIn("Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL", stems)
        self.assertIn("NVIDIA-Nemotron-3.5-Lightning-30B-A3B-IQ4_XS", stems)
        self.assertTrue(html_report._is_retired(
            "models/Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf"))
        self.assertFalse(html_report._is_retired("models/qwen36-35b-distill-mxfp4_moe.gguf"))

    def _isolated(self, models_dir, retired_file):
        """Points the two paths the registry reads at test data (config.override, the
        D1 pattern) and resets the stems cache — the cache is deliberate: the report
        asks for the same set once per row."""
        html_report._RETIRED_STEMS = None
        self.addCleanup(setattr, html_report, "_RETIRED_STEMS", None)
        self.enterContext(config.override(MODELS_DIR=models_dir, RETIRED_FILE=retired_file))


class TestComparePicker(unittest.TestCase):
    """Pick-a-pair list: unique (slug, think) options, retired models out
    (unless explicitly compared)."""

    def _pool3(self):
        a = _mk("models/aaa.gguf", thinking="off")
        b = _mk("models/bbb.gguf", thinking="off")
        c = _mk("models/ccc.gguf", thinking="on")
        return a, b, c

    @staticmethod
    def _options(html):
        import re
        body = html.split('<select id="sel-a"', 1)[1].split("</select>", 1)[0]
        return re.findall(r">([^<]+)</option>", body)

    def test_picker_excludes_retired(self):
        a, b, c = self._pool3()
        with mock.patch.object(html_report, "_retired_stems", return_value={"aaa"}):
            html = html_report.render_compare(b, c, pool=[a, b, c])
        opts = self._options(html)
        self.assertEqual(len(opts), 2)
        self.assertTrue(any("bbb" in o for o in opts))
        self.assertTrue(any("ccc" in o for o in opts))
        self.assertFalse(any("aaa" in o for o in opts))

    def test_picker_dedupes_duplicate_rows(self):
        # Stale pool states appended the same (model, thinking) twice: the
        # picker must still list the pair once.
        a, b, _c = self._pool3()
        with mock.patch.object(html_report, "_retired_stems", return_value=set()):
            html = html_report.render_compare(b, b, pool=[a, dict(a), b])
        opts = self._options(html)
        aaa = [o for o in opts if o.startswith("aaa")]
        self.assertEqual(len(aaa), 1)

    def test_explicit_retired_pair_still_renders(self):
        a, b, _c = self._pool3()
        with mock.patch.object(html_report, "_retired_stems", return_value={"aaa"}):
            html = html_report.render_compare(a, b, pool=[a, b])
        static = html.split('<div id="cmp-body">', 1)[1].split("</main>", 1)[0]
        self.assertIn("aaa", static)
        self.assertIn("bbb", static)

    def test_picker_ordered_by_slug_then_think(self):
        a, b, c = self._pool3()  # aaa/off, bbb/off, ccc/on
        a_on = _mk("models/aaa.gguf", thinking="on")
        with mock.patch.object(html_report, "_retired_stems", return_value=set()):
            html = html_report.render_compare(b, c, pool=[c, b, a_on, a])
        opts = self._options(html)
        self.assertEqual(
            [o.split(" · ")[0] for o in opts],
            ["aaa", "aaa", "bbb", "ccc"])
        self.assertTrue(opts[0].endswith("think:off"))
        self.assertTrue(opts[1].endswith("think:on"))

    def test_picker_js_does_not_append_options(self):
        # Regression: the inline JS re-appended every server-rendered option,
        # doubling the whole list in JS-enabled browsers (curl never saw it).
        self.assertNotIn("appendChild", html_report._PICKER_JS)


if __name__ == "__main__":
    unittest.main()
