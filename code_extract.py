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
    # 1) Closed block with the language tag (normal case).
    for tag in langs:
        m = re.search(r"```" + re.escape(tag) + r"[^\n]*\n(.*?)```", text, re.DOTALL)
        if m:
            return m.group(1)
    # 2) Closed plain block (no tag).
    m = re.search(r"```\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1)
    # 3) Fallback: open block, never closed. Can happen if the response is cut by
    #    max_tokens mid-code-block (verbose model). Last resort: take everything
    #    after the opening fence.
    for tag in langs:
        m = re.search(r"```" + re.escape(tag) + r"[^\n]*\n(.*)\Z", text, re.DOTALL)
        if m:
            return m.group(1).rstrip()
    m = re.search(r"```\n(.*)\Z", text, re.DOTALL)
    if m:
        return m.group(1).rstrip()
    return None
