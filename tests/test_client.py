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

if __name__ == "__main__":
    unittest.main()