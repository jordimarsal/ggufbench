import importlib.util, pathlib
from . import config

_DIM_DIR = {"speed": "speed", "tools": "tools", "code": "code", "agent": "agent"}

def _load_module(path):
    spec = importlib.util.spec_from_file_location(path.stem, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def load(dimension, lang_filter=None):
    base = config.BENCH_DIR / "tasks" / _DIM_DIR[dimension]
    out = []
    files = sorted(p for p in base.rglob("*.py") if not p.name.startswith("_") and p.name != "__init__.py")
    for p in files:
        if lang_filter:
            rel = p.relative_to(base)
            lang_part = rel.parts[0] if len(rel.parts) > 1 else None
            if lang_part and lang_part not in lang_filter:
                continue
        m = _load_module(p)
        if dimension == "tools":
            out.append({"id": getattr(m, "ID", p.stem), "prompt": m.PROMPT,
                        "tools": getattr(m, "TOOLS", []), "expected": getattr(m, "EXPECTED", None)})
        elif dimension == "speed":
            out.append({"id": getattr(m, "ID", p.stem), "prompt": getattr(m, "PROMPT", "")})
        elif dimension == "code":
            out.append({"id": getattr(m, "ID", p.stem), "lang": m.LANG,
                        "prompt": m.PROMPT, "test_code": m.TEST_CODE})
        elif dimension == "agent":
            out.append({"id": getattr(m, "ID", p.stem), "lang": m.LANG, "goal": m.GOAL,
                        "initial_files": getattr(m, "INITIAL_FILES", {}),
                        "test_file": getattr(m, "TEST_FILE", "test_solution.py"),
                        "max_turns": getattr(m, "MAX_TURNS", 8)})
    return out