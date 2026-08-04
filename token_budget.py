"""Memòria de pressupost de tokens per (model, dim, llenguatge, tasca).

La idea: quan una tasca de codi falla amb 'no code block' perquè el model es
queda sense tokens a mig bloc, el grader fa un escalat (provem pressupostos més
alts). Per no repetir aquest escalat cada run, persistim aquí el pressupost
resolt per cada (model, llenguatge, tasca). Així, un cop calibrat, les properes
runs fan una sola crida amb el pressupost guardat.
"""
import json

from . import config

BUDGET_FILE = config.TOKEN_BUDGETS
_cache = None


def _load() -> dict:
    global _cache
    if _cache is None:
        _cache = json.loads(BUDGET_FILE.read_text()) if BUDGET_FILE.exists() else {}
    return _cache


def _key(dim, model_slug, lang, task_id) -> str:
    return f"{dim}/{model_slug or '_'}/{lang}/{task_id}"


def get(dim, model_slug, lang, task_id):
    """Pressupost guardat per a aquesta tasca, o None si no està calibrat."""
    return _load().get(_key(dim, model_slug, lang, task_id))


def put(dim, model_slug, lang, task_id, value) -> None:
    data = _load()
    data[_key(dim, model_slug, lang, task_id)] = value
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    BUDGET_FILE.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


def reset_cache() -> None:
    """Per tests: invalida la cache perquè la propera lectura torni a llegir disc."""
    global _cache
    _cache = None
