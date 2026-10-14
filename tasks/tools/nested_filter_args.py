ID = "nested_filter_args"
PROMPT = """Crida query_logs per consultar els registres d'error amb aquests requisits exactes:
nivell ERROR, etiquetes ['db', 'net'] i com a màxim 5 resultats."""
TOOLS = [
    {"type": "function", "function": {
        "name": "query_logs",
        "description": "Consulta registres de logs amb un filtre i un límit.",
        "parameters": {"type": "object",
                       "properties": {
                           "filter": {"type": "object",
                                      "properties": {"level": {"type": "string"},
                                                     "tags": {"type": "array",
                                                              "items": {"type": "string"}}},
                                      "required": ["level"]},
                           "limit": {"type": "integer"}},
                       "required": ["filter", "limit"]}}},
    {"type": "function", "function": {
        "name": "get_all_logs",
        "description": "Retorna tots els registres, sense filtre.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
]
EXPECTED = {"name": "query_logs",
            "arguments": {"filter": {"level": "ERROR", "tags": ["db", "net"]}, "limit": 5}}
