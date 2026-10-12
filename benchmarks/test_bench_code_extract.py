"""Benchmark: code_extract.extract over representative solution+test pairs."""

import pytest
from ggufbench import code_extract


def _make_response(lang="python", size="medium"):
    """Generate a response with a code block of varying sizes."""
    if lang == "python":
        tag = "python"
        sample = ("def solve(data):\n"
                  "    result = []\n"
                  "    for item in data:\n"
                  "        if item > 0:\n"
                  "            result.append(item * 2)\n"
                  "    return sorted(result)\n")
    elif lang == "java":
        tag = "java"
        sample = ("class Solution {\n"
                  "    public int[] solve(int[] data) {\n"
                  "        java.util.List<Integer> r = new java.util.ArrayList<>();\n"
                  "        for (int x : data) { if (x > 0) r.add(x * 2); }\n"
                  "        return r.stream().mapToInt(i->i).sorted().toArray();\n"
                  "    }\n"
                  "}\n")
    else:
        tag = "bash"
        sample = "#!/bin/bash\nfor i in \"$@\"; do\n  echo $((i * 2))\ndone | sort -n\n"

    preamble = f"""I'll write the solution in {lang}:

```{tag}
{sample}```

Let me know if you need any changes!
"""
    return preamble


def _make_cut_response(lang="python"):
    """Response cut mid-code-block by max_tokens."""
    if lang == "python":
        return "Here's my attempt:\n```python\ndef solve(data):\n    result = []\n    for item in data:\n        if item > 0:\n            result.append(item * 2)\n"
    elif lang == "java":
        return "Sure, here is the Java code:\n```java\nclass Solution {\n    public int[] solve(int[] data) {\n        java.util.List<Integer> r = new java.util.ArrayList<>();\n        for (int x : data) { if (x > 0) r.add(x * 2); }\n"
    else:
        return "Bash script below:\n```sh\n#!/bin/bash\nfor i in \"$@\"; do\n  echo $((i * 2))\ndone | sort -n\n"


@pytest.mark.benchmark
def test_extract_closed_blocks(benchmark):
    """Extract from closed code blocks across languages."""
    responses = [
        _make_response("python", "medium"),
        _make_response("python", "large"),
        _make_response("java", "medium"),
        _make_response("bash", "small"),
        _make_response("typescript", "medium"),
    ]
    langs = ["python", "python", "java", "bash", "typescript"]

    def run():
        results = []
        for resp, lang in zip(responses, langs):
            results.append(code_extract.extract(resp, lang))
        return len(results)

    benchmark(run)


@pytest.mark.benchmark
def test_extract_unclosed_fallback(benchmark):
    """Extract from cut-off responses (fallback path)."""
    responses = [_make_cut_response(l) for l in ("python", "java", "bash")]
    langs = ["python", "java", "bash"]

    def run():
        results = []
        for resp, lang in zip(responses, langs):
            results.append(code_extract.extract(resp, lang))
        return len(results)

    benchmark(run)
