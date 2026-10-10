"""Memòria de pressupost de tokens per (model, thinking, llenguatge, tasca).

La idea: quan una tasca de codi falla amb 'no code block' perquè el model es
queda sense tokens a mig bloc, el grader fa un escalat (provem pressupostos més
alts). Per no repetir aquest escalat cada run, persistim aquí el pressupost
resolt per cada (model, thinking, llenguatge, tasca). Amb l'era 16384 finida
(R3 thinking_batches: el pressupost inicia a 32768), les entrades sense
`_schema == 2` s'ignoren i el fitxer es regenera al pròxim put.
"""
import json

from . import config

BUDGET_FILE = config.TOKEN_BUDGETS
_SCHEMA = 2
_cache = None


def _load() -> dict:
    global _cache
    if _cache is None:
        raw = json.loads(BUDGET_FILE.read_text()) if BUDGET_FILE.exists() else {}
        _cache = raw if raw.get("_schema") == _SCHEMA else {}
    return _cache


def _key(dim, model_slug, thinking, lang, task_id) -> str:
    return f"{dim}/{model_slug or '_'}/{thinking or 'na'}/{lang}/{task_id}"


def get(dim, model_slug, thinking, lang, task_id):
    """Pressupost guardat per a aquesta tasca i mode, o None si no està calibrat."""
    return _load().get(_key(dim, model_slug, thinking, lang, task_id))


def put(dim, model_slug, thinking, lang, task_id, value) -> None:
    data = _load()
    data[_key(dim, model_slug, thinking, lang, task_id)] = value
    data["_schema"] = _SCHEMA
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    BUDGET_FILE.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


def reset_cache() -> None:
    """Per tests: invalida la cache perquè la propera lectura torni a llegir disc."""
    global _cache
    _cache = None
