ID = "feature_flag_end_to_end"
LANG = "typescript"
GOAL = """El sistema de flags mostra funcionalitats que estan desactivades: el validador
identifica un flag com a actiu quan en realitat és inactiu perquè compara l'índex del
flag amb la seva posició al llistat en lloc de verificar si el camp 'enabled' és true.
Això fa que els usuaris vegin funcionalitats que no haurien de veure.

Punt d'entrada: main(flags) de solution.ts, retorna [{name, enabled}] per a cada flag
vàlid (format JSON). Sols els flags amb enabled=true han de sortir al resultat final.

Esbrina on fallen les coses: el punt d'entrada no és l'únic fitxer del projecte."""
INITIAL_FILES = {
    "solution.ts": ('import { parseFlags } from "./parser.js";\n'
                    '\n\n'
                    'export function main(flags: string[]): Array<{ name: string; enabled: boolean }> {\n'
                    '    return parseFlags(flags);\n'
                    '}'),
    "config.ts": ('export const DEFAULT_FLAGS = [\n'
                  '    { name: "dark_mode", enabled: false },\n'
                  '    { name: "beta_features", enabled: true },\n'
                  '    { name: "new_ui", enabled: false },\n'
                  '];\n'
                  '\n\n'
                  'export function getDefaults(): Array<{ name: string; enabled: boolean }> {\n'
                  '    return [...DEFAULT_FLAGS];\n'
                  '}'),
    "parser.ts": ('import type { Flag } from "./types.js";\n'
                  '\n\n'
                  'export function parseFlag(line: string): Flag | null {\n'
                  '    try {\n'
                  '        const parsed = JSON.parse(line);\n'
                  '        if (!parsed.name || typeof parsed.enabled !== "boolean") return null;\n'
                  '        return { name: parsed.name, enabled: parsed.enabled };\n'
                  '    } catch {\n'
                  '        return null;\n'
                  '    }\n'
                  '}'),
    "validator.ts": ('import type { Flag } from "./types.js";\n'
                     '\n\n'
                     'export function validateFlags(flags: Flag[]): Flag[] {\n'
                     '    // BUG: compara l\'índex amb la posició al llistat en lloc de verificar el valor\n'
                     '    return flags.filter((flag, index) => flag.enabled === (index % 2 === 0));\n'
                     '}'),
    "renderer.ts": ('import type { Flag } from "./types.js";\n'
                    '\n\n'
                    'export function renderFlags(flags: Flag[]): string {\n'
                    '    return flags.map(f => `${f.name}: ${f.enabled ? "ACTIU" : "INACTIU"}`).join("\\n");\n'
                    '}'),
    "types.ts": ('export interface Flag {\n'
                 '    name: string;\n'
                 '    enabled: boolean;\n'
                 '}'),
    "test_solution.ts": ('import { main } from "./solution.js";\n'
                         '\n\n'
                         '(async () => {\n'
                         '    const flags = [\n'
                         '        \'{"name":"dark_mode","enabled":false}\',\n'
                         '        \'{"name":"beta_features","enabled":true}\',\n'
                         '        \'{"name":"new_ui","enabled":false}\',\n'
                         '        \'{"name":"experimental","enabled":true}\',\n'
                         '        \'invalid-json\',\n'
                         '    ];\n'
                         '    const result = main(flags);\n'
                         '\n'
                         '    // Sols els flags amb enabled=true han de sortir\n'
                         '    if (result.length !== 2) throw new Error(`wrong count ${result.length}`);\n'
                         '\n'
                         '    // beta_features i experimental han d\'aparèixer, dark_mode i new_ui no\n'
                         '    const names = result.map(r => r.name).sort();\n'
                         '    if (names.join(",") !== "beta_features,experimental") throw new Error("wrong flags");\n'
                         '\n'
                         '    // Tots els resultats han de ser habilitats\n'
                         '    for (const flag of result) {\n'
                         '        if (!flag.enabled) throw new Error(`${flag.name} should be enabled`);\n'
                         '    }\n'
                         '\n'
                         '    console.log("OK");\n'
                         '})();'),
}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 14
