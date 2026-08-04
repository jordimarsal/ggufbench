ID = "list_files"
PROMPT = "Crida la tool list_files per llistar els fitxers al directori actual"
TOOLS = [{"type": "function", "function": {"name": "list_files", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}}]
EXPECTED = {"name": "list_files", "arguments": {"path": "."}}