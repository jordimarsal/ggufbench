ID = "search"
PROMPT = "Crida la tool search amb pattern 'hello' per cercar al codi"
TOOLS = [{"type": "function", "function": {"name": "search", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}}, "required": ["pattern"]}}}]
EXPECTED = {"name": "search", "arguments": {"pattern": "hello"}}