"""Packaging contract (feature cli_entry_point): the repo installs as the
`ggufbench` package exposing a `ggufbench` console script — that binary is what
the estol nodelet's bench lane executes ($ESTOL_GGUF_BIN). At the same time,
`python3 -m ggufbench.run` from the workspace root (the bench checkout's
invocation, AGENTS.md) must keep working unchanged."""

import subprocess
import sys
import tomllib
import unittest
from importlib import import_module
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class TestConsoleScript(unittest.TestCase):
    """R1: the pyproject declares the entry point and the target resolves."""

    def test_script_is_declared_and_target_resolves(self):
        pyproject = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
        scripts = pyproject["project"]["scripts"]
        self.assertEqual(scripts.get("ggufbench"), "ggufbench.run:main")
        module_name, _, attr = scripts["ggufbench"].partition(":")
        self.assertTrue(callable(getattr(import_module(module_name), attr)),
                        f"{scripts['ggufbench']} does not resolve to a callable")

    def test_package_is_declared_with_an_explicit_root_mapping(self):
        pyproject = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
        tool = pyproject.get("tool", {}).get("setuptools", {})
        self.assertIn("ggufbench", tool.get("packages", []))
        self.assertEqual(tool.get("package-dir", {}).get("ggufbench"), ".",
                        "the repo root IS the package: it must be mapped onto '.'")


class TestModuleInvocation(unittest.TestCase):
    """R2: the bench checkout runs `python3 -m ggufbench.run` from the workspace
    root — packaging must not change that path."""

    def test_scoreboard_runs_from_the_workspace_root(self):
        proc = subprocess.run(
            [sys.executable, "-m", "ggufbench.run", "--scoreboard"],
            cwd=REPO.parent, capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])


class TestInstallGeometry(unittest.TestCase):
    """R3: the config paths derive from __file__ — inside the checkout — in this
    checkout AND in the editable tool install (the same invariant, checked where
    the code happens to live)."""

    def test_paths_resolve_inside_the_checkout(self):
        from ggufbench import config

        self.assertEqual(config.BASE_DIR, REPO.parent)
        self.assertEqual(config.RESULTS_DIR, REPO / "results")
        self.assertEqual(config.MODELS_DIR, REPO.parent / "models")

    def test_install_pulls_no_third_party_dependencies(self):
        """R4: stdlib only — the tool venv stays hermetic (no deps to resolve,
        nothing to break under uv tool install)."""
        pyproject = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(pyproject["project"].get("dependencies", []), [])


if __name__ == "__main__":
    unittest.main()
