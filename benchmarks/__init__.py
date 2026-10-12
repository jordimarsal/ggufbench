# Benchmarks for ggufbench scoring/rendering core.
# These are NOT collected by default suite discovery (tests/ dir only).
# Guard module so nothing breaks when pytest-benchmark is absent.

import pytest as _pytest
_pytest.importorskip("pytest_benchmark")
