ID = "archive_not_delete"
PROMPT = """Arxiva './report.csv' dins la carpeta './archive' amb archive_file. El fitxer
s'ha de conservar: no facis servir delete_file."""
TOOLS = [
    {"type": "function", "function": {
        "name": "archive_file",
        "description": "Mou un fitxer a una carpeta d'arxiu, sense esborrar-lo.",
        "parameters": {"type": "object",
                       "properties": {"path": {"type": "string"},
                                      "destination": {"type": "string"}},
                       "required": ["path", "destination"]}}},
    {"type": "function", "function": {
        "name": "delete_file",
        "description": "Esborra un fitxer del disc.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}},
                       "required": ["path"]}}},
]
EXPECTED = {"name": "archive_file",
            "arguments": {"path": "./report.csv", "destination": "./archive"}}
