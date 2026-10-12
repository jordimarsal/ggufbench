ID = "save_no_optional"
PROMPT = "Crida la tool save_file amb path './note.txt' i content 'Recordatori important'. No cal l'argument optional metadata."
TOOLS = [{"type": "function", "function": {"name": "save_file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}, "metadata": {"type": "string"}}, "required": ["path", "content"], "optional": ["metadata"]}}}]
EXPECTED = {"name": "save_file", "arguments": {"path": "./note.txt", "content": "Recordatori important"}}
