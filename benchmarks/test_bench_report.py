"""Benchmark: report._global_score loop (×1000)."""

import pytest
from ggufbench import config, report


def _mk(code_score=0.9, tools_score=0.75, agent_score=0.5, speed_ms=100):
    r = {"model": "models/foo.gguf",
         "speed": {"passed": True, "turns": 0, "trace": [], "score": 0,
                   "speed_ms": speed_ms, "gen_tps": 100.0, "prompt_tps": 300.0},
         "tools": {"passed": True, "turns": 0, "trace": [], "score": tools_score,
                   "by_lang": {}},
         "code": {"passed": True, "turns": 0, "trace": [], "score": code_score,
                  "by_lang": {"python": code_score}, "excluded": 0},
         "agent": {"passed": True, "turns": 0, "trace": [], "score": agent_score,
                   "by_lang": {"python": agent_score}}}
    return r


@pytest.mark.benchmark
def test_global_score_loop_1k(benchmark):
    """Loop _global_score ×1000 with a fixed pool."""
    weights = config.WEIGHTS.copy()
    min_speed = 80.0
    pool = [_mk(code_score=round(0.5 + i * 0.01, 2), tools_score=0.75) for i in range(10)]

    def run():
        scores = []
        for r in pool:
            s = report._global_score(r, weights, min_speed)
            scores.append(s)
        return sum(scores) / len(scores)

    benchmark(run)
