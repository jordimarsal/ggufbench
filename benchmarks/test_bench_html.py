"""Benchmark: html_report.render over a synthetic pool (~24 rows)."""

import json
from pathlib import Path

import pytest
from ggufbench import config, html_report


def _mk(name="models/foo.gguf", engine="llama", code_score=0.9, tools_score=0.75,
        thinking=None, code_excluded=0):
    """Minimal but complete result — same shape as the test helper."""
    r = {"model": name, "engine": engine, "ts": "2026-10-09T10:00:00",
         "context_mode": "fixed", "tasks_version": "v3", "server_build": "b1234",
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


def _make_pool(n=24):
    """Build a pool of n synthetic rows with varied scores and modes."""
    pool = []
    for i in range(n):
        engine = "strata" if i % 3 == 0 else "llama"
        thinking = ("on" if i % 2 == 0 else "off") if i < n - 2 else None
        pool.append(_mk(
            name=f"models/model-{i:03d}.gguf",
            engine=engine,
            code_score=round(0.1 + (i * 0.8) / max(n - 1, 1), 2),
            tools_score=round(0.2 + (i * 0.6) / max(n - 1, 1), 2),
            thinking=thinking,
            code_excluded=i % 5,
        ))
    # Add by_level on some rows to exercise that path
    for m in pool[::3]:
        m["code"]["by_level"] = {"easy": round(m["code"]["score"], 2),
                                  "hard": round(m["code"]["score"] * 0.7, 2),
                                  "expert": round(m["code"]["score"] * 0.4, 2)}
    return pool


@pytest.mark.benchmark
def test_render_pool_24(benchmark):
    """html_report.render over ~24 synthetic model rows."""
    pool = _make_pool(24)
    benchmark(html_report.render, pool)
