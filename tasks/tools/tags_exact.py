ID = "tags_exact"
PROMPT = "Crida la tool search_tags amb tags ['python', 'machine-learning'] exactament en aquest ordre."
TOOLS = [{"type": "function", "function": {"name": "search_tags", "parameters": {"type": "object", "properties": {"tags": {"type": "array", "items": {"type": "string"}}}, "required": ["tags"]}}}]
EXPECTED = {"name": "search_tags", "arguments": {"tags": ["python", "machine-learning"]}}
