"""Benchmark: tasks_loader.load of the real tasks tree."""

import pytest
from ggufbench import tasks_loader


@pytest.mark.benchmark
def test_load_tools(benchmark):
    """Load all tools-dimension tasks."""
    benchmark(tasks_loader.load, "tools")


@pytest.mark.benchmark
def test_load_speed(benchmark):
    """Load speed-dimension tasks."""
    benchmark(tasks_loader.load, "speed")


@pytest.mark.benchmark
def test_load_code_all_levels(benchmark):
    """Load code-dimension tasks (all levels)."""
    benchmark(tasks_loader.load, "code")


@pytest.mark.benchmark
def test_load_agent(benchmark):
    """Load agent-dimension tasks."""
    benchmark(tasks_loader.load, "agent")
