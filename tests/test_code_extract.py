import unittest
from benchmark import code_extract

class TestExtract(unittest.TestCase):
    def test_python_block(self):
        txt = "Sure:\n```python\ndef f():\n    return 1\n```\ndone"
        self.assertEqual(code_extract.extract(txt, "python"), "def f():\n    return 1\n")
    def test_alias_py(self):
        self.assertEqual(code_extract.extract("```py\nx=1\n```", "python"), "x=1\n")
    def test_typescript_ts(self):
        self.assertEqual(code_extract.extract("```ts\nconst x=1\n```", "typescript"), "const x=1\n")
    def test_bash_sh(self):
        self.assertEqual(code_extract.extract("```sh\necho hi\n```", "bash"), "echo hi\n")
    def test_java(self):
        self.assertEqual(code_extract.extract("```java\nclass A{}\n```", "java"), "class A{}\n")
    def test_none(self):
        self.assertIsNone(code_extract.extract("no code here", "python"))
    def test_plain_block_fallback(self):
        self.assertEqual(code_extract.extract("```\nx=1\n```", "python"), "x=1\n")
    def test_unclosed_block_fallback(self):
        # Response cut by max_tokens mid-code-block (no closing ```);
        # the extractor must still recover the code as a last resort.
        txt = "Here you go:\n```python\ndef f():\n    return 1\n"
        self.assertEqual(code_extract.extract(txt, "python"), "def f():\n    return 1")
    def test_unclosed_plain_block_fallback(self):
        self.assertEqual(code_extract.extract("```\nx=1\n", "python"), "x=1")

if __name__ == "__main__":
    unittest.main()