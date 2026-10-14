ID = "stock_alert_thresholds"
LANG = "python"
GOAL = """El sistema d'alertes de stock genera alertes incorrectes quan un article arriba al límit
exactament: no ha d'alertar si el stock és igual al punt de reordre (només quan és inferior).
A més, articles amb noms diferents per majúscules/minúscules han de generar una sola alerta.

Punt d'entrada: main(items) de solution.py, que retorna una llista ordenada d'alertes.
Cada item té {"name": str, "current_stock": int, "reorder_point": int}.
Cada alerta retornada té {"item_name": str, "current": int, "threshold": int}."""
INITIAL_FILES = {
    "solution.py": ('from alerts import generate_alerts\n\n\ndef main(items):\n'
                    '    return generate_alerts(items)\n'),
    "thresholds.py": ('def is_below_threshold(current_stock, reorder_point):\n'
                      '    """Retorna True si cal alertar (stock < reordre)."""\n'
                      '    return current_stock >= reorder_point  # BUG: hauria de ser >\n'),
    "alerts.py": ('from thresholds import is_below_threshold\n\n\ndef generate_alerts(items):\n'
                  '    alerts = []\n'
                  '    for item in items:\n'
                  '        if is_below_threshold(item["current_stock"], item["reorder_point"]):\n'
                  '            alerts.append({\n'
                  '                "item_name": item["name"],\n'
                  '                "current": item["current_stock"],\n'
                  '                "threshold": item["reorder_point"],\n'
                  '            })\n'
                  '    # Dedup per nom (ignora majúscules/minúscules)\n'
                  '    seen = set()\n'
                  '    deduped = []\n'
                  '    for a in alerts:\n'
                  '        key = a["item_name"]  # BUG: no normalitza a lowercase\n'
                  '        if key not in seen:\n'
                  '            seen.add(key)\n'
                  '            deduped.append(a)\n'
                  '    return sorted(deduped, key=lambda x: x["item_name"])\n'),
    "notifier.py": ('def format_alert(alert):\n'
                    '    """Formata una alerta per imprimir."""\n'
                    '    name = alert["item_name"].upper()\n'
                    '    return f"ALERTA {name}: stock={alert[\'current\']}, reordre={alert[\'threshold\']}"\n'),
    "test_solution.py": ('from solution import main\n\n'
                         'items = [\n'
                         '    {"name": "widget", "current_stock": 5, "reorder_point": 10},\n'
                         '    {"name": "cable", "current_stock": 3, "reorder_point": 3},\n'
                         '    {"name": "Widget", "current_stock": 2, "reorder_point": 8},\n'
                         ']\n'
                         'alerts = main(items)\n\n'
                         '# cable no ha d\'alertar (stock == reorder_point)\n'
                         'names = [a["item_name"] for a in alerts]\n'
                         'assert "cable" not in names, f"cable no hauria d\'alertar: {alerts}"\n\n'
                         '# widget i Widget han de ser una sola alerta\n'
                         'assert len(alerts) == 1, f"s\'esperava 1 alerta, n\'hi ha {len(alerts)}"\n'
                         'assert alerts[0]["item_name"].lower() == "widget"\n'
                         'assert alerts[0]["current"] == 2\n'
                         'assert alerts[0]["threshold"] == 8\n\n'
                         'single = main([{"name": "x", "current_stock": 0, "reorder_point": 5}])\n'
                         'assert single[0]["current"] == 0 and single[0]["threshold"] == 5\n\n'
                         'from notifier import format_alert\n'
                         'line = format_alert(single[0])\n'
                         'assert "ALERTA X:" in line\n\n'
                         'print("OK")\n'),
}
TEST_FILE = "test_solution.py"
MAX_TURNS = 14
