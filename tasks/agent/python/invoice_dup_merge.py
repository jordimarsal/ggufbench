ID = "invoice_dup_merge"
LANG = "python"
GOAL = """La facturació no quadra quan una mateixa referència apareix en més d'una línia: el
total ha de tenir en compte TOTES les línies i cada article ha de sortir una sola vegada amb
la seva quantitat acumulada.

Punt d'entrada: main(lines) de solution.py, que retorna {"items": [...], "total": int}.
`lines` és una llista de cadenes "referencia,quantitat,preu_unitari_en_cèntims"
(poden venir amb espais). Cada item ha de tenir name, qty, unit i total.

Esbrina on fallen les coses: el punt d'entrada no és l'únic fitxer del projecte."""
INITIAL_FILES = {
    "solution.py": ("from invoice import build_invoice\n"
                    "\n"
                    "\n"
                    "def main(lines):\n"
                    "    return build_invoice(lines)\n"),
    "parse.py": ('''def parse_rows(lines):
    """'name,qty,unit_cents' per linea -> un diccionari per nom."""
    out = {}
    for line in lines:
        if not line.strip():
            continue
        name, qty, unit = line.split(",")
        out[name.strip()] = {"name": name.strip(), "qty": int(qty), "unit": int(unit)}
    return out
'''),
    "invoice.py": ('''from parse import parse_rows


def build_invoice(lines):
    """Factura amb els articles i el total en centims."""
    items = []
    total = 0
    for _name, item in parse_rows(lines).items():
        line_total = item["qty"] * item["unit"]
        items.append({"name": item["name"], "qty": item["qty"], "unit": item["unit"],
                      "total": line_total})
        total += line_total
    return {"items": items, "total": total}
'''),
    "money.py": ('''def cents_to_str(cents):
    """1234 -> '12.34' (per a l'informe imprès)."""
    return f"{cents // 100}.{cents % 100:02d}"
'''),
    "report.py": ('''from money import cents_to_str


def lines(invoice):
    """Una linia de text per article."""
    out = [f"{item['name']}: {item['qty']} x {cents_to_str(item['unit'])}" for item in invoice["items"]]
    out.append(f"TOTAL {cents_to_str(invoice['total'])}")
    return out
'''),
    "test_solution.py": ('''from solution import main

lines = ["widget,3,250", "cable,2,150", "widget,1,250", "cable,3,150", "  cable , 1 , 150 "]
inv = main(lines)

assert inv["total"] == 4 * 250 + 6 * 150, inv["total"]          # totes les linies compten

by_name = {i["name"]: i for i in inv["items"]}
assert sorted(by_name) == ["cable", "widget"], sorted(by_name)   # un item per referencia
assert by_name["widget"]["qty"] == 4, by_name["widget"]
assert by_name["cable"]["qty"] == 6, by_name["cable"]
assert by_name["widget"]["total"] == 4 * 250
assert by_name["cable"]["total"] == 6 * 150

single = main(["only,2,100"])
assert single["total"] == 200 and single["items"][0]["qty"] == 2

from report import lines as report_lines                                  # el report hi ha de ser
assert report_lines(inv)[-1] == "TOTAL 19.00", report_lines(inv)

print("OK")
'''),
}
TEST_FILE = "test_solution.py"
MAX_TURNS = 14
