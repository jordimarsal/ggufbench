ID = "read_file"
PROMPT = "Crida la tool read_file amb path './hello.py' per llegir el contingut"
TOOLS = [{"name": "read_file"}]
EXPECTED = {"name": "read_file", "arguments": {"path": "./hello.py"}}