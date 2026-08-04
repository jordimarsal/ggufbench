ID = "check_solution"
PROMPT = "Crida la tool check_solution amb solution_code 'def add(a,b): return a+b'"
TOOLS = [{"type": "function", "function": {"name": "check_solution", "parameters": {"type": "object", "properties": {"solution_code": {"type": "string"}}, "required": ["solution_code"]}}}]
EXPECTED = {"name": "check_solution", "arguments": {"solution_code": "def add(a,b): return a+b"}}