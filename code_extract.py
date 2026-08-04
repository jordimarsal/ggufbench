import re

from . import config

_ALIASES: dict[str, list[str]] = {
    config.Lang.PYTHON: ["python", "py"],
    config.Lang.BASH: ["bash", "sh", "shell"],
    config.Lang.JAVA: ["java"],
    config.Lang.TYPESCRIPT: ["typescript", "ts", "js"],
}


def extract(text, lang):
    if not text:
        return None
    langs = _ALIASES.get(lang, [lang])
    for tag in langs:
        m = re.search(r"```" + re.escape(tag) + r"[^\n]*\n(.*?)```", text, re.DOTALL)
        if m:
            return m.group(1)
    m = re.search(r"```\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1)
    return None
