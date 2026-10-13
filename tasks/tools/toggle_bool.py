ID = "toggle_bool"
PROMPT = "Activa el mode debug cridant toggle_debug_mode amb enabled true (booleà, no string)."
TOOLS = [{"type": "function", "function": {"name": "toggle_debug_mode", "parameters": {"type": "object", "properties": {"enabled": {"type": "boolean"}}, "required": ["enabled"]}}}]
EXPECTED = {"name": "toggle_debug_mode", "arguments": {"enabled": True}}
