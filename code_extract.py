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
    # 1) Bloc tancat amb l'etiqueta de l'idioma (cas normal).
    for tag in langs:
        m = re.search(r"```" + re.escape(tag) + r"[^\n]*\n(.*?)```", text, re.DOTALL)
        if m:
            return m.group(1)
    # 2) Bloc pla tancat (sense etiqueta).
    m = re.search(r"```\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1)
    # 3) Fallback: bloc obert sense tancar. Pot passar si la resposta es talla per
    #    max_tokens a mig bloc de codi (model verbós). Últim recurs: prenem tot el que
    #    hi ha després de l'obertura.
    for tag in langs:
        m = re.search(r"```" + re.escape(tag) + r"[^\n]*\n(.*)\Z", text, re.DOTALL)
        if m:
            return m.group(1).rstrip()
    m = re.search(r"```\n(.*)\Z", text, re.DOTALL)
    if m:
        return m.group(1).rstrip()
    return None
