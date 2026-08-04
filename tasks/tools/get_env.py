ID = "get_env"
PROMPT = "Crida la tool get_env per obtenir una variable d'entorn (qualsevol)"
TOOLS = [{"type": "function", "function": {"name": "get_env", "parameters": {"type": "object", "properties": {"var_name": {"type": "string"}}, "required": ["var_name"]}}}]
EXPECTED = {"name": "get_env"}