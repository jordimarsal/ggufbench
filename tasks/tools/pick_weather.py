ID = "pick_weather"
PROMPT = "Consulta la previsió meteorològica de Barcelona per a demà. Crida l'eina correcta."
TOOLS = [
    {"type": "function", "function": {"name": "get_current_weather", "parameters": {"type": "object", "properties": {"location": {"type": "string"}, "unit": {"type": "string"}}, "required": ["location"]}}},
    {"type": "function", "function": {"name": "get_forecast", "parameters": {"type": "object", "properties": {"location": {"type": "string"}, "days": {"type": "integer"}}, "required": ["location", "days"]}}}
]
EXPECTED = {"name": "get_forecast", "arguments": {"location": "Barcelona", "days": 1}}
