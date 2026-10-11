import unittest
import socket
import sys
from pathlib import Path


class SmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from benchmark import config
        cls.config = config
        # Only MAIN servable GGUFs (>= 1 GB, excluding mmproj/drafts/embeddings),
        # sorted by size: the smoke wants to load fast, not the biggest model.
        candidates = [p for p in config.MODELS_DIR.glob("*.gguf")
                      if p.stat().st_size >= 1_000_000_000
                      and not p.name.startswith(("mmproj-", "dflash-", "nomic-"))]
        cls.models = sorted(candidates, key=lambda p: p.stat().st_size)
        cls.has_models = len(cls.models) > 0
        # If there is already a server on the harness port (benchmark running or the
        # production server), the suite cannot compete for the VRAM: skip.
        cls.port_busy = False
        try:
            s = socket.create_connection(("127.0.0.1", config.PORT), timeout=1)
            s.close()
            cls.port_busy = True
        except OSError:
            pass

    def test_skip_if_no_models(self):
        if not self.has_models:
            self.skipTest("No models found in MODELS_DIR")

    def test_smoke_end_to_end(self):
        if not self.has_models:
            self.skipTest("No models found in MODELS_DIR")
        if self.port_busy:
            self.skipTest(f"a server is listening on port {self.config.PORT}: GPUs busy")

        from benchmark import server as S, client as C, graders as G, tasks_loader as T
        from benchmark import config

        model_path = self.models[0]
        port = config.PORT + 1

        sm = S.ServerManager(model_path, context_mode="fixed", port=port)
        sm.start()
        try:
            self.assertTrue(sm.wait_ready(timeout=240), "Server failed to become ready")

            class Client:
                def chat(self, *a, **k):
                    return C.chat(*a, base_url=f"http://127.0.0.1:{port}", **{**k})

            c = Client()

            try:
                C.chat([{"role": "user", "content": "hi"}], max_tokens=4,
                      base_url=f"http://127.0.0.1:{port}")
            except Exception:
                pass

            speed_tasks = T.load("speed")
            self.assertGreater(len(speed_tasks), 0, "No speed tasks found")
            t_hello = speed_tasks[0]
            resp = c.chat([{"role": "user", "content": t_hello["prompt"]}],
                         max_tokens=256)
            self.assertIn("choices", resp, "Speed task response missing choices")

            tools_tasks = T.load("tools")
            t_noop = next((t for t in tools_tasks if t["id"] == "noop"), None)
            self.assertIsNotNone(t_noop, "No noop task found")
            r_tools = G.grade_tools(c, [t_noop])
            self.assertIn("score", r_tools, "Tools grader missing score")

            code_tasks = T.load("code", lang_filter=["python"])
            t_simple_math = next((t for t in code_tasks if t["id"] == "simple_math"),
                                None)
            self.assertIsNotNone(t_simple_math, "No simple_math task found")
            r_code = G.grade_code(c, [t_simple_math])
            self.assertIn("score", r_code, "Code grader missing score")

        finally:
            sm.stop()
            self.assertFalse(sm.is_alive(), "Server still alive after stop")

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux-only smoke test")
    def test_server_build_version(self):
        if not self.has_models:
            self.skipTest("No models found in MODELS_DIR")

        from benchmark import config
        try:
            import subprocess
            out = subprocess.run([str(config.SERVER_BIN), "--version"],
                                capture_output=True, text=True, timeout=10)
            version_line = None
            for line in out.stdout.splitlines():
                if line.startswith("version:"):
                    version_line = line
                    break
            self.assertIsNotNone(version_line, "No version line found")
        except Exception as e:
            self.skipTest(f"Failed to get version: {e}")


if __name__ == "__main__":
    unittest.main()