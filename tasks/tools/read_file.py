ID = "read_file"
PROMPT = "Crida la tool read_file amb path './hello.py' per llegir el contingut"
TOOLS = [{"type": "function", "function": {"name": "read_file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}}]
EXPECTED = {"name": "read_file", "arguments": {"path": "./hello.py"}}