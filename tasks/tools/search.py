ID = "search"
PROMPT = "Crida la tool search amb pattern 'hello' per cercar al codi"
TOOLS = [{"name": "search"}]
EXPECTED = {"name": "search", "arguments": {"pattern": "hello"}}