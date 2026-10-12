ID = "schedule_event"
PROMPT = "Crida la tool schedule_event amb title 'Reunió setmanal', date '2026-10-15T14:00:00Z' i recurrence amb interval=7, days=['monday','wednesday'], end_date='2026-12-31'"
TOOLS = [{"type": "function", "function": {"name": "schedule_event", "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "date": {"type": "string"}, "recurrence": {"type": "object", "properties": {"interval": {"type": "integer"}, "days": {"type": "array", "items": {"type": "string"}}, "end_date": {"type": "string"}}}}, "required": ["title", "date"]}}}]
EXPECTED = {"name": "schedule_event", "arguments": {"title": "Reunió setmanal", "date": "2026-10-15T14:00:00Z", "recurrence": {"interval": 7, "days": ["monday", "wednesday"], "end_date": "2026-12-31"}}}
