ID = "save_file"
PROMPT = "Crida la tool save_file amb path './test.txt' i content 'Hello!'"
TOOLS = [{"type": "function", "function": {"name": "save_file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}}]
EXPECTED = {"name": "save_file", "arguments": {"path": "./test.txt", "content": "Hello!"}}