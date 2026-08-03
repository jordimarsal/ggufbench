ID = "check_solution"
PROMPT = "Crida la tool check_solution amb solution_code 'def add(a,b): return a+b'"
TOOLS = [{"name": "check_solution"}]
EXPECTED = {"name": "check_solution", "arguments": {"solution_code": "def add(a,b): return a+b"}}