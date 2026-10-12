"""Token budget memory per (model, thinking, language, task).

The idea: when a code task fails with 'no code block' because the model runs
out of tokens mid-block, the grader scales up (we try higher budgets).
To avoid repeating that scaling every run, we persist here the resolved
budget for each (model, thinking, language, task). With the 16384 era over
(R3 thinking_batches: the budget starts at 32768), entries without
`_schema == 2` are ignored and the file is regenerated on the next put.
"""
import json

from . import config

_SCHEMA = 2
_cache = None


def _load() -> dict:
    global _cache
    if _cache is None:
        raw = (json.loads(config.TOKEN_BUDGETS.read_text())
               if config.TOKEN_BUDGETS.exists() else {})
        _cache = raw if raw.get("_schema") == _SCHEMA else {}
    return _cache


def _key(dim, model_slug, thinking, lang, task_id) -> str:
    return f"{dim}/{model_slug or '_'}/{thinking or 'na'}/{lang}/{task_id}"


def get(dim, model_slug, thinking, lang, task_id):
    """Stored budget for this task and mode, or None if not calibrated."""
    return _load().get(_key(dim, model_slug, thinking, lang, task_id))


def put(dim, model_slug, thinking, lang, task_id, value) -> None:
    data = _load()
    data[_key(dim, model_slug, thinking, lang, task_id)] = value
    data["_schema"] = _SCHEMA
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    config.TOKEN_BUDGETS.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


def reset_cache() -> None:
    """For tests: invalidates the cache so the next read re-reads disk."""
    global _cache
    _cache = None
