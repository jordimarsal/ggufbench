import importlib.util

from . import config

_DIM_DIR = {"speed": "speed", "tools": "tools", "code": "code", "agent": "agent"}


def _load_module(path):
    spec = importlib.util.spec_from_file_location(path.stem, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _check_extra_files(task_id, extra):
    """Valida EXTRA_FILES (discriminative_tasks R2): noms plans al sandbox.

    Sense barres ni '..' i sense capturar els noms reservats (solution/test):
    l'extra mai no pot guanyar els fitxers del runner.
    """
    for name in extra:
        low = str(name).lower()
        if (not name or "/" in str(name) or "\\" in str(name)
                or str(name) in (".", "..")
                or low.startswith(("solution", "test"))):
            raise ValueError(
                f"{task_id}: EXTRA_FILES invalid (nom pla requerit, "
                f"sense solution/test): {name!r}")


def load(dimension, lang_filter=None, level=None):
    base = config.BENCH_DIR / "tasks" / _DIM_DIR[dimension]
    out = []
    files = sorted(p for p in base.rglob("*.py")
                   if not p.name.startswith("_") and p.name != "__init__.py")
    for p in files:
        if lang_filter:
            rel = p.relative_to(base)
            lang_part = rel.parts[0] if len(rel.parts) > 1 else None
            if lang_part and lang_part not in lang_filter:
                continue
        m = _load_module(p)
        # Nivell (hard_code_tier / discriminative_tasks): només code el porta;
        # el sufix _hard/_expert a l'ID el decideix.
        task_id = str(getattr(m, "ID", p.stem))
        if task_id.endswith("_expert"):
            level_value = "expert"
        elif task_id.endswith("_hard"):
            level_value = "hard"
        else:
            level_value = "easy"
        if dimension == "code" and level and level_value != level:
            continue
        if dimension == "tools":
            out.append({"id": getattr(m, "ID", p.stem), "prompt": getattr(m, "PROMPT", ""),
                        "tools": getattr(m, "TOOLS", []), "expected": getattr(m, "EXPECTED", None)})
        elif dimension == "speed":
            out.append({"id": getattr(m, "ID", p.stem), "prompt": getattr(m, "PROMPT", "")})
        elif dimension == "code":
            extra = dict(getattr(m, "EXTRA_FILES", {}) or {})
            _check_extra_files(task_id, extra)
            out.append({"id": getattr(m, "ID", p.stem), "lang": getattr(m, "LANG", "python"),
                        "prompt": getattr(m, "PROMPT", ""), "test_code": getattr(m, "TEST_CODE", ""),
                        "level": level_value, "extra_files": extra})
        elif dimension == "agent":
            out.append({"id": getattr(m, "ID", p.stem), "lang": getattr(m, "LANG", "python"),
                        "goal": getattr(m, "GOAL", ""),
                        "initial_files": getattr(m, "INITIAL_FILES", {}),
                        "test_file": getattr(m, "TEST_FILE", "test_solution.py"),
                        "max_turns": getattr(m, "MAX_TURNS", 8)})
    return out
