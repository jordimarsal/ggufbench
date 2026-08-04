ID = "get_time"
PROMPT = "Crida la tool get_time per obtenir el timestamp actual"
TOOLS = [{"type": "function", "function": {"name": "get_time", "parameters": {"type": "object", "properties": {}}}}]
EXPECTED = {"name": "get_time"}