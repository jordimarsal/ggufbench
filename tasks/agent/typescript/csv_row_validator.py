ID = "csv_row_validator"
LANG = "typescript"
GOAL = """El validador de fitxers CSV accepta files amb menys camps dels esperats i les
propaga al sistema sense avisar: un registre que li falta el camp 'preu' acaba amb valor
null i la factura final dona resultats incorrectes.

Punt d'entrada: main(rows) de solution.ts, retorna [{id, nom, preu}] per a cada fila
vàlida del CSV (format: "id,nom,preu"). Les files amb menys de 3 camps s'haurien de
descartar silenciosament.

Esbrina on fallen les coses: el punt d'entrada no és l'únic fitxer del projecte."""
INITIAL_FILES = {
    "solution.ts": ('import { validateRows } from "./validator.js";\n'
                    '\n\n'
                    'export function main(rows: string[]): Array<{ id: number; nom: string; preu: number }> {\n'
                    '    return validateRows(rows);\n'
                    '}'),
    "parser.ts": ('export function parseRow(row: string): Array<string> | null {\n'
                  '    const parts = row.split(",");\n'
                  '    // BUG: no verifica que hi hagi exactament 3 camps\n'
                  '    if (parts.length === 0) return null;\n'
                  '    return parts.map(p => p.trim());\n'
                  '}'),
    "validator.ts": ('import { parseRow } from "./parser.js";\n'
                     '\n\n'
                     'const EXPECTED_FIELDS = 3;\n'
                     '\n\n'
                     'export function validateRows(rows: string[]): Array<{ id: number; nom: string; preu: number }> {\n'
                     '    const results: Array<{ id: number; nom: string; preu: number }> = [];\n'
                     '    for (const row of rows) {\n'
                     '        const fields = parseRow(row);\n'
                     '        if (!fields) continue;\n'
                     '        // BUG: usa la longitud de fields en lloc d\'EXPECTED_FIELDS\n'
                     '        if (fields.length < 1) continue;\n'
                     '        results.push({\n'
                     '            id: Number(fields[0]),\n'
                     '            nom: fields[1],\n'
                     '            preu: Number(fields[2]) || 0,\n'
                     '        });\n'
                     '    }\n'
                     '    return results;\n'
                     '}'),
    "formatter.ts": ('import type { Record } from "./types.js";\n'
                     '\n\n'
                     'export function formatRecord(r: Record): string {\n'
                     '    return `${r.id}: ${r.nom} — ${r.preu.toFixed(2)}€`;\n'
                     '}'),
    "report.ts": ('import type { Record } from "./types.js";\n'
                  '\n\n'
                  'export function buildReport(records: Record[]): string {\n'
                  '    const lines = records.map(formatRecord);\n'
                  '    return lines.join("\\n");\n'
                  '}'),
    "types.ts": ('export interface Record {\n'
                 '    id: number;\n'
                 '    nom: string;\n'
                 '    preu: number;\n'
                 '}'),
    "test_solution.ts": ('import { main } from "./solution.js";\n'
                         '\n\n'
                         '(async () => {\n'
                         '    const rows = [\n'
                         '        "1,producte_a,450",\n'
                         '        "2,producte_b,300",\n'
                         '        "3,producte_c,600",\n'
                         '        "4,incompleta",\n'
                         '        "5,producte_e,750",\n'
                         '    ];\n'
                         '    const result = main(rows);\n'
                         '\n'
                         '    // Sols les files completes (3 camps) han de sortir\n'
                         '    if (result.length !== 4) throw new Error(`wrong count ${result.length}`);\n'
                         '\n'
                         '    // La fila incompleta ("4,incompleta") no ha d\'aparèixer\n'
                         '    const ids = result.map(r => r.id).sort();\n'
                         '    if (ids.join(",") !== "1,2,3,5") throw new Error("incomplete row leaked");\n'
                         '\n'
                         '    // Els valors han de ser correctes\n'
                         '    const byId = Object.fromEntries(result.map(r => [r.id, r]));\n'
                         '    if (byId[1].preu !== 450) throw new Error("bad preu for id=1");\n'
                         '    if (byId[3].nom !== "producte_c") throw new Error("bad nom for id=3");\n'
                         '\n'
                         '    console.log("OK");\n'
                         '})();'),
}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 14
