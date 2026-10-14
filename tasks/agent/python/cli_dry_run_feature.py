ID = "cli_dry_run_feature"
LANG = "python"
GOAL = """Eina CLI que processa un fitxer CSV i n'escriu el resultat en format csv o json.

Punt d'entrada: `main(argv)` de solution.py, on argv és la llista d'arguments del CLI
(com `sys.argv`, per exemple ["solution.py", "entrada.csv", "sortida.csv", "--dry-run"]).

Símptomes:
1. `main` no accepta cap argument, així que no es pot conduir l'eina des de codi.
2. L'opció `--dry-run` hauria de ser només simulació (informar sense escriure res al disc)
   i avui encara escriu el fitxer de sortida.

Esbrina on fallen les coses: el punt d'entrada no és l'únic fitxer del projecte."""

INITIAL_FILES = {
    "solution.py": ('#!/usr/bin/env python3\n'
                    'import argparse\n'
                    'from parser import parse_csv\n'
                    'from store import save_output\n'
                    'from formatter import format_csv, format_json\n'
                    '\n'
                    '\n'
                    'def main():\n'
                    '    parser = argparse.ArgumentParser(description="Processar fitxer CSV")\n'
                    '    parser.add_argument("input", help="Fitxer CSV d\'entrada")\n'
                    '    parser.add_argument("output", help="Fitxer de sortida")\n'
                    '    parser.add_argument("--format", choices=["csv", "json"], default="csv")\n'
                    '    parser.add_argument("--dry-run", action="store_true", help="Simular sense escriure")\n'
                    '    args = parser.parse_args()\n'
                    '\n'
                    '    rows = parse_csv(args.input)\n'
                    '    if args.format == "csv":\n'
                    '        formatted = format_csv(rows)\n'
                    '    else:\n'
                    '        formatted = format_json(rows)\n'
                    '\n'
                    '    save_output(args.output, formatted, dry_run=args.dry_run)\n'
                    '    print(f"OK - {len(rows)} files processades")\n'
                    '\n'
                    '\n'
                    'if __name__ == "__main__":\n'
                    '    main()\n'),
    "parser.py": ('def parse_csv(path):\n'
                  '    """Parseja un fitxer CSV i retorna una llista de dicts."""\n'
                  '    with open(path, encoding="utf-8") as f:\n'
                  '        lines = [line.strip() for line in f.readlines()]\n'
                  '\n'
                  '    header = lines[0].split(",")\n'
                  '    rows = []\n'
                  '    for line in lines[1:]:\n'
                  '        values = line.split(",")\n'
                  '        row = dict(zip(header, values))\n'
                  '        rows.append(row)\n'
                  '    return rows\n'),
    "formatter.py": ('def format_csv(rows):\n'
                     '    """Retorna el CSV amb capcalera i dades."""\n'
                     '    if not rows:\n'
                     '        return ""\n'
                     '    header = ",".join(rows[0].keys())\n'
                     '    body = "\\n".join(",".join(r.values()) for r in rows)\n'
                     '    return header + "\\n" + body\n'
                     '\n'
                     '\n'
                     'def format_json(rows):\n'
                     '    """Retorna les dades com a JSON (sense capcalera)."""\n'
                     '    import json\n'
                     '    return json.dumps(rows, indent=2, ensure_ascii=False)\n'),
    "store.py": ('def save_output(path, content, dry_run=False):\n'
                 '    """Escriu el contingut al fitxer indicat."""\n'
                 '    with open(path, "w", encoding="utf-8") as f:\n'
                 '        f.write(content)\n'
                 '    print(f"Escrit: {path}")\n'),
    "test_solution.py": ('import json\n'
                         'import os\n'
                         'import tempfile\n'
                         'from solution import main\n'
                         '\n'
                         '\n'
                         'def run(csv_text, extra):\n'
                         '    d = tempfile.mkdtemp()\n'
                         '    src = os.path.join(d, "in.csv")\n'
                         '    with open(src, "w", encoding="utf-8") as f:\n'
                         '        f.write(csv_text)\n'
                         '    out = os.path.join(d, "out")\n'
                         '    main(["solution.py", src, out] + extra)\n'
                         '    return out\n'
                         '\n'
                         '\n'
                         'def test_normal_output():\n'
                         '    out = run("nom,edat\\ncarlos,30\\naia,25\\n", [])\n'
                         '    assert os.path.exists(out), "el fitxer de sortida no existeix"\n'
                         '    lines = open(out, encoding="utf-8").read().strip().split("\\n")\n'
                         '    assert len(lines) == 3, lines\n'
                         '    assert "nom" in lines[0], lines\n'
                         '\n'
                         '\n'
                         'def test_json_format():\n'
                         '    out = run("nom,edat\\ncarlos,30\\naia,25\\n", ["--format", "json"])\n'
                         '    data = json.load(open(out, encoding="utf-8"))\n'
                         '    assert set(data[0]) == {"nom", "edat"}, data\n'
                         '\n'
                         '\n'
                         'def test_dry_run_writes_nothing():\n'
                         '    out = run("nom,edat\\ncarlos,30\\n", ["--dry-run"])\n'
                         '    assert not os.path.exists(out), "dry-run no ha d\'escriure res"\n'
                         '\n'
                         '\n'
                         'test_normal_output()\n'
                         'test_json_format()\n'
                         'test_dry_run_writes_nothing()\n'
                         'print("OK")\n'),
}
TEST_FILE = "test_solution.py"
MAX_TURNS = 14
