import re

_ALIASES = {
    "python": ["python", "py"],
    "bash": ["bash", "sh", "shell"],
    "java": ["java"],
    "typescript": ["typescript", "ts", "js"],
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