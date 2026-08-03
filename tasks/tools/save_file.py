ID = "save_file"
PROMPT = "Crida la tool save_file amb path './test.txt' i content 'Hello!'"
TOOLS = [{"name": "save_file"}]
EXPECTED = {"name": "save_file", "arguments": {"path": "./test.txt", "content": "Hello!"}}