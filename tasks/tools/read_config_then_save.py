ID = "read_config_then_save"
PROMPT = "Llegeix el fitxer './config.env' amb la tool read_file. Conté 'DB_HOST=localhost'. Després crida get_env amb var_name='DB_HOST'"
TOOLS = [
    {"type": "function", "function": {"name": "read_file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "get_env", "parameters": {"type": "object", "properties": {"var_name": {"type": "string"}}, "required": ["var_name"]}}}
]
EXPECTED = {"name": "read_file", "arguments": {"path": "./config.env"}}
