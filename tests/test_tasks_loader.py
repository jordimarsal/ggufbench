import unittest, os, textwrap
from benchmark import tasks_loader

class TestLoad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = os.path.join(os.path.dirname(__file__), "..", "tasks", "tools")
        open(os.path.join(d, "_tmpexample.py"), "w").write(textwrap.dedent('''
            ID = "tmp"
            PROMPT = "hi"
            TOOLS = []
            EXPECTED = None
        '''))
    @classmethod
    def tearDownClass(cls):
        p = os.path.join(os.path.dirname(__file__), "..", "tasks", "tools", "_tmpexample.py")
        if os.path.exists(p): os.remove(p)
    def test_load_returns_list(self):
        ts = tasks_loader.load("tools")
        self.assertIsInstance(ts, list)
    def test_skips_underscore(self):
        ts = tasks_loader.load("tools")
        self.assertFalse(any(t["id"] == "tmp" for t in ts))

if __name__ == "__main__":
    unittest.main()