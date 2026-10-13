ID = "check_then_read"
PROMPT = "Verifica que existeix './data.json' amb check_file abans de llegir-lo amb read_file."
TOOLS = [
    {"type": "function", "function": {"name": "check_file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "read_file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}}
]
EXPECTED = {"name": "check_file", "arguments": {"path": "./data.json"}}
