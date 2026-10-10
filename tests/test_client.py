import unittest
from benchmark import client

SAMPLE = {
    "choices": [{"finish_reason": "tool_calls", "message": {
        "role": "assistant", "content": "",
        "tool_calls": [{"type": "function", "function": {
            "name": "get_weather", "arguments": '{"city": "Paris"}'}}]}}],
    "usage": {"completion_tokens": 20, "prompt_tokens": 50},
    "timings": {"predicted_per_second": 97.7, "predicted_n": 20,
                "predicted_ms": 204.9, "prompt_per_second": 500.0,
                "prompt_ms": 100.0, "prompt_n": 50},
}

class TestClient(unittest.TestCase):
    def test_parse_timings(self):
        t = client.parse_timings(SAMPLE)
        self.assertAlmostEqual(t["gen_tps"], 97.7)
        self.assertAlmostEqual(t["prompt_tps"], 500.0)
    def test_parse_timings_missing(self):
        self.assertIsNone(client.parse_timings({"choices": []}))
    def test_extract_tool_call(self):
        tc = client.extract_tool_call(SAMPLE)
        self.assertEqual(tc["name"], "get_weather")
        self.assertEqual(tc["arguments"], {"city": "Paris"})
    def test_extract_tool_call_none(self):
        no_tc = {"choices": [{"message": {"content": "hola"}}]}
        self.assertIsNone(client.extract_tool_call(no_tc))
    def test_extract_tool_call_bad_json_args(self):
        bad = {"choices": [{"message": {"tool_calls": [
            {"function": {"name": "f", "arguments": "no-json"}}]}}]}
        tc = client.extract_tool_call(bad)
        self.assertEqual(tc["name"], "f")
        self.assertIsNone(tc["arguments"])
    def test_first_text(self):
        self.assertEqual(client.first_text(SAMPLE), "")
        self.assertEqual(client.first_text({"choices":[{"message":{"content":"x"}}]}), "x")

class TestChatExtra(unittest.TestCase):
    """`extra` afegeix/sobreescriu camps del cos (config.thinking_body)."""

    def _capture(self, **kwargs):
        import json as _json
        captured = {}

        class _Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return b'{"choices": [{"message": {"content": "hola"}}]}'

        def fake_urlopen(req, timeout=None):
            captured["body"] = _json.loads(req.data.decode("utf-8"))
            captured["timeout"] = timeout
            return _Resp()

        orig = client.urllib.request.urlopen
        client.urllib.request.urlopen = fake_urlopen
        try:
            client.chat([{"role": "user", "content": "hola"}], **kwargs)
        finally:
            client.urllib.request.urlopen = orig
        return captured["body"]

    def test_defaults_without_extra(self):
        from benchmark import config
        body = self._capture()
        self.assertEqual(body["temperature"], config.TEMPERATURE)
        self.assertEqual(body["seed"], config.SEED)
        self.assertNotIn("chat_template_kwargs", body)

    def test_extra_merges_into_body(self):
        from benchmark import config
        from benchmark import config as cfg
        body = self._capture(extra=cfg.thinking_body("strata", "off"))
        # el camp nou hi és...
        self.assertEqual(body["chat_template_kwargs"], {"enable_thinking": False})
        # ...i els camps base es conserven (el cos s'ha de seguir essent complet)
        self.assertEqual(body["temperature"], config.TEMPERATURE)
        self.assertEqual(body["max_tokens"], 256)
        self.assertIn("messages", body)


if __name__ == "__main__":
    unittest.main()