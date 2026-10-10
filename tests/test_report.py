import unittest, json, tempfile, shutil
from pathlib import Path
from benchmark import report, config

POOL_FILE = config.RESULTS_MODELS / "pool.jsonl"

W = {"tools": 0.30, "code": 0.30, "agent": 0.25, "speed": 0.15}


def mk(model, speed_ms=None, gen_tps=None, prompt_tps=None,
       tools=1.0, code=1.0, agent=1.0, code_lang=None, agent_lang=None,
       thinking=None, code_excluded=0):
    # thinking=None -> sense clau (fila legacy, era pre-thinking); "on"/"off" -> nova
    r = {"model": model, "context_mode": "fixed", "ts": "2026-08-03T00:00:00",
            "tasks_version": "x", "server_build": "10250",
            "speed": {"passed": True, "turns": 0, "trace": [],
                      "speed_ms": speed_ms, "gen_tps": gen_tps or 0, "prompt_tps": prompt_tps or 0},
            "tools": {"passed": True, "turns": 0, "trace": [], "score": tools, "by_lang": {}, "tasks": []},
            "code": {"passed": True, "turns": 0, "trace": [], "score": code, "by_lang": code_lang or {}, "tasks": [],
                     "excluded": code_excluded},
            "agent": {"passed": True, "turns": 0, "trace": [], "score": agent, "by_lang": agent_lang or {}, "tasks": []}}
    if thinking is not None:
        r["thinking"] = thinking
    return r


class TestReport(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.old_pool_file = report.POOL_FILE
        report.POOL_FILE = self.tmpdir / "pool.jsonl"

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        report.POOL_FILE = self.old_pool_file

    def test_save_and_load(self):
        r = mk("m", speed_ms=100)
        report.save_result(r)
        pool = report.load_pool()
        self.assertEqual(len(pool), 1)
        self.assertEqual(pool[0]["model"], "m")

    def test_upsert_replaces_same_model(self):
        report.save_result(mk("m", speed_ms=50, tools=0.4))
        report.save_result(mk("m", speed_ms=99, tools=0.8))  # re-run -> upsert
        pool = report.load_pool()
        self.assertEqual(len(pool), 1)
        self.assertEqual(pool[0]["speed"]["speed_ms"], 99)

    def test_load_pool_dedups_stale_duplicates(self):
        # Entrades llegades de l'època append-only: vàries línies amb el mateix slug.
        path = report.POOL_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(json.dumps(mk("m", speed_ms=10, tools=0.1)) + "\n")
            f.write(json.dumps(mk("m", speed_ms=20, tools=0.2)) + "\n")
            f.write(json.dumps(mk("m", speed_ms=30, tools=0.3)) + "\n")  # última -> guanya
        pool = report.load_pool()
        self.assertEqual(len(pool), 1)              # colapsades a una
        self.assertEqual(pool[0]["speed"]["speed_ms"], 30)  # l'última (més recent)

    def test_render_shows_per_model_scores(self):
        report.save_result(mk("alpha", speed_ms=100, tools=0.5, code=1.0, agent=0.0))
        out = report.render(report.load_pool(), W)
        self.assertIn("MODEL", out)
        self.assertIn("GLOBAL", out)
        self.assertIn("alpha", out)
        self.assertIn("50%", out)   # tools
        self.assertIn("100%", out)  # code

    def test_global_score_weighted(self):
        r = mk("m", speed_ms=100, tools=1.0, code=1.0, agent=1.0)
        # model únic -> min_speed = el seu -> speed_score = 1.0 -> global = 1.0
        g = report._global_score(r, W, 100)
        self.assertAlmostEqual(g, 1.0)

    def test_global_score_missing_speed(self):
        r = mk("m", speed_ms=None, tools=1.0, code=1.0, agent=1.0)
        # sense speed_ms -> speed_score = 0; la resta suma 0.85
        g = report._global_score(r, W, 100)
        self.assertAlmostEqual(g, 0.85)

    def test_speed_normalization_fastest_is_best(self):
        a = mk("a", speed_ms=100, tools=1.0, code=1.0, agent=1.0)  # ràpid
        b = mk("b", speed_ms=200, tools=1.0, code=1.0, agent=1.0)  # lent
        report.save_result(a)
        report.save_result(b)
        ga = report._global_score(a, W, 100)
        gb = report._global_score(b, W, 100)
        self.assertAlmostEqual(ga, 1.0)     # el més ràpid -> speed_score 1.0
        self.assertAlmostEqual(gb, 0.925)   # speed_score 0.5
        self.assertGreater(ga, gb)

    def test_render_sorted_by_global_desc(self):
        report.save_result(mk("slow", speed_ms=300, tools=0.2, code=0.2, agent=0.2))
        report.save_result(mk("fast", speed_ms=50, tools=1.0, code=1.0, agent=1.0))
        out = report.render(report.load_pool(), W)
        i_fast = out.index("fast")
        i_slow = out.index("slow")
        self.assertLess(i_fast, i_slow)  # fast (millor global) apareix abans

    def test_render_has_tokens_per_second_section(self):
        report.save_result(mk("alpha", speed_ms=100, gen_tps=48.5, prompt_tps=2600.0))
        out = report.render(report.load_pool(), W)
        self.assertIn("Tokens per segon", out)
        self.assertIn("gen (out)", out)
        self.assertIn("prompt (in)", out)
        self.assertIn("48.5", out)     # gen_tps
        self.assertIn("2600.0", out)   # prompt_tps

    def test_lang_profile(self):
        r = mk("m", code_lang={"python": 1.0, "java": 0.0}, agent_lang={"python": 0.5})
        prof = report.lang_profile(pool=[r], lang="python")
        self.assertEqual(prof["speed"], {})
        self.assertEqual(prof["tools"], {})
        self.assertIn("python", prof["code"])
        self.assertIn("python", prof["agent"])

    def test_forget(self):
        r = mk("m")
        report.save_result(r)
        self.assertEqual(len(report.load_pool()), 1)
        report.forget("m")
        self.assertEqual(len(report.load_pool()), 0)

    def test_upsert_keeps_both_thinking_modes(self):
        # R2 thinking_batches: la clau és (slug, thinking); els dos modes conviuen
        report.save_result(mk("m", speed_ms=50, thinking="off"))
        report.save_result(mk("m", speed_ms=60, thinking="on"))
        self.assertEqual(len(report.load_pool()), 2)
        report.save_result(mk("m", speed_ms=99, thinking="off"))  # re-run off -> upsert
        pool = report.load_pool()
        self.assertEqual(len(pool), 2)
        off = [r for r in pool if r.get("thinking") == "off"][0]
        self.assertEqual(off["speed"]["speed_ms"], 99)

    def test_legacy_row_without_thinking_coexists_with_off(self):
        # (m, None) no col·lisiona amb (m, 'off'): el legacy sobreviu fins re-mesurar
        report.save_result(mk("m", speed_ms=10))
        report.save_result(mk("m", speed_ms=20, thinking="off"))
        self.assertEqual(len(report.load_pool()), 2)

    def test_runs_filenames_distinguish_mode(self):
        runs = self.tmpdir / "runs"
        old_runs = config.RESULTS_RUNS
        config.RESULTS_RUNS = runs
        try:
            report.save_result(mk("m", thinking="off"))
            report.save_result(mk("m", thinking="on"))
            names = sorted(p.name for p in runs.glob("*.json"))
            self.assertEqual(len(names), 2)
            self.assertTrue(any(n.endswith("-m-off.json") for n in names), names)
            self.assertTrue(any(n.endswith("-m-on.json") for n in names), names)
        finally:
            config.RESULTS_RUNS = old_runs

    def test_forget_removes_both_modes(self):
        report.save_result(mk("m", thinking="off"))
        report.save_result(mk("m", thinking="on"))
        report.save_result(mk("other", thinking="off"))
        self.assertEqual(report.forget("m"), 2)
        self.assertEqual(len(report.load_pool()), 1)

    def test_render_tolerates_rows_without_thinking(self):
        report.save_result(mk("m", thinking="off"))
        report.save_result(mk("m2"))  # legacy: sense clau
        out = report.render(report.load_pool(), W)
        self.assertIn("m", out)
        self.assertIn("m2", out)

    def test_table1_labels_think_and_excluded(self):
        # R4+R5 thinking_batches: columna THINK + recompte d'excloses al score
        # (asserts per fila: "on"/"—" sols apareixerien d'altres columnes)
        report.save_result(mk("m", code=1.0, code_excluded=2, thinking="off"))
        report.save_result(mk("n", code=0.5, thinking="on"))
        report.save_result(mk("o", speed_ms=100))  # legacy (speed amb valor)
        out = report.render(report.load_pool(), W)
        self.assertIn("THINK", out)
        block = out.split("\n\n")[0].splitlines()  # Taula 1 (abans del bloc de tokens)
        rows = {l.split()[0]: l for l in block if l[:1].isalpha()}
        self.assertIn("off", rows["m"])
        self.assertIn("on", rows["n"])
        self.assertIn("100% (2 excl.)", rows["m"])
        self.assertIn("50%", rows["n"])
        self.assertIn("—", rows["o"])  # legacy: mode — (l'speed mostra 100ms)

    def test_table2_labels_rows_with_mode(self):
        report.save_result(mk("m", thinking="off"))
        out = report.render(report.load_pool(), W, level="verbose")
        self.assertIn("THINK", out)
        self.assertIn("off", out)

    def test_table3_marks_mode(self):
        r = mk("m", thinking="on")
        r["code"]["trace"] = [{"id": "t1", "lang": "python", "passed": True,
                               "detail": "OK"}]
        report.save_result(r)
        out = report.render(report.load_pool(), W, show_tasks=True)
        self.assertIn("THINK", out)
        self.assertIn("on", out)

    def test_forget_by_bare_name_when_stored_as_relative_path(self):
        # El camp 'model' s'emmagatzema com a camí relatiu; oblidar pel nom net ha de funcionar.
        report.save_result(mk("models/foo.gguf"))
        self.assertEqual(len(report.load_pool()), 1)
        report.forget("foo")
        self.assertEqual(len(report.load_pool()), 0)

    def test_forget_by_absolute_path_when_stored_as_relative_path(self):
        report.save_result(mk("models/bar.gguf"))
        report.forget("/home/jordi/ia/llama/models/bar.gguf")
        self.assertEqual(len(report.load_pool()), 0)

    def test_forget_by_full_relative_path(self):
        report.save_result(mk("models/baz.gguf"))
        report.forget("models/baz.gguf")
        self.assertEqual(len(report.load_pool()), 0)

    def test_forget_bare_name_when_model_name_has_dots(self):
        # Regressió: noms amb punts interns ('Qwen3.8', 'Ornith-1.5') han de funcionar.
        # _model_stem ha de treure NOMÉS l'extensió .gguf, no un punt del nom.
        report.save_result(mk("models/Qwen3.8-27B-Heretic-Q4_K_M.gguf"))
        self.assertEqual(len(report.load_pool()), 1)
        report.forget("Qwen3.8-27B-Heretic-Q4_K_M")   # nom net del fitxer
        self.assertEqual(len(report.load_pool()), 0)

    def test_forget_returns_removed_count(self):
        # El caller ha de poder saber si s'ha esbarrat res: retorna el nº d'entrades
        # borrades (0 quan no coincideix). Evita el fals "esborrat" del CLI.
        report.save_result(mk("m"))
        report.save_result(mk("other"))
        self.assertEqual(len(report.load_pool()), 2)
        self.assertEqual(report.forget("m"), 1)          # borra 1
        self.assertEqual(len(report.load_pool()), 1)     # en queda un altre
        self.assertEqual(report.forget("noexistent"), 0)  # no coincideix -> 0
        self.assertEqual(len(report.load_pool()), 1)      # no canvia

    # --- Granularitat: --info (per-tasca) / --verbose (+per-llenguatge) ----------
    def _with_traces(self, model="m", tools=True, code=True, agent=True):
        r = mk(model, speed_ms=100, tools=1.0 if tools else 0.5,
               code=1.0 if code else 0.5, agent=1.0 if agent else 0.0)
        if tools:
            r["tools"]["trace"] = [{"id": "multi-arg", "passed": True,
                                    "detail": "got=get_weather expected=get_weather"}]
        if code:
            r["code"]["trace"] = [{"id": "stack", "lang": "java", "passed": False,
                                   "detail": "AssertionError line 12"},
                                  {"id": "func", "lang": "python", "passed": True,
                                   "detail": "ok"}]
            r["code"]["by_lang"] = {"java": 0.0, "python": 1.0}
        if agent:
            r["agent"]["trace"] = [{"id": "fix-fib", "lang": "python", "passed": True,
                                    "turns": 3}]
            r["agent"]["by_lang"] = {"python": 1.0}
        return r

    def test_info_shows_per_task_detail(self):
        report.save_result(self._with_traces())
        out = report.render(report.load_pool(), W, level="info")
        self.assertIn("Detall per tasca", out)
        self.assertIn("✓", out)   # fix-fib / func passats
        self.assertIn("✗", out)   # stack falla
        self.assertIn("multi-arg", out)

    def test_default_level_has_no_task_detail(self):
        report.save_result(self._with_traces())
        out = report.render(report.load_pool(), W)  # level default
        self.assertNotIn("Detall per tasca", out)

    def test_verbose_adds_by_lang_table(self):
        report.save_result(self._with_traces())
        out_info = report.render(report.load_pool(), W, level="info")
        out_verbose = report.render(report.load_pool(), W, level="verbose")
        # verbose inclou Taula 2 (per llengua), info no la té
        self.assertIn("Per llengua", out_verbose)
        self.assertNotIn("Per llengua", out_info)
        # verbose JA NO inclou el detall de tasca; cal show_tasks=True per veure'l.
        self.assertNotIn("Detall per tasca", out_verbose)
        out_verbose_task = report.render(report.load_pool(), W, level="verbose",
                                         show_tasks=True)
        self.assertIn("Detall per tasca", out_verbose_task)

    def test_render_robust_to_missing_granularity(self):
        # Model parcial: sense dimensions/code/agent, o directament sense trace.
        report.save_result({"model": "partial1"})                       # gairebé res
        report.save_result(mk("partial2", tools=0.0))                   # sense code/agent
        report.save_result(mk("partial3", tools=1.0, code=1.0, agent=1.0,
                              code_lang={}, agent_lang={}))              # traces buides
        # Ni --info ni --verbose han de fallar.
        for lvl in ("info", "verbose"):
            out = report.render(report.load_pool(), W, level=lvl)
            self.assertIn("MODEL", out)


if __name__ == "__main__":
    unittest.main()
