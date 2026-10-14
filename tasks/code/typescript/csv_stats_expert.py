ID = "csv_stats_expert"
LANG = "typescript"
PROMPT = """Implementa report(path: string): string que retorni un informe de vendes.

El fitxer te una linia per venda: `region,producte,quantitat,preu_unitari`
- quantitat: enter positiu; preu_unitari: decimal amb EXACTAMENT 2 decimals.
- Linies buides o nomes espais: es salten. Linies que comencen per # (despres d'espais
  opcionals): comentaris, es salten.
- Qualsevol altra linia es INVALIDA: es compta i es descarta (no afecta res mes).

Informe, exactament (separat per \\n i sense salt final):
  region,total_units,revenue
  <region>,<unitats>,<ingressos>
  ...
  invalid: <n>
- Una linia per regio, ordenades alfabeticament; unitats = suma de quantitats;
  ingressos = suma de quantitat*preu amb 2 decimals i punt decimal.
- Si no hi ha cap linia valida, nomes la capcalera i la linia `invalid`."""
EXTRA_FILES = {
    "sales.csv": (
        "# setmana 12\n"
        "north,widget,3,10.00\n"
        "south,cable,2,4.50\n"
        "\n"
        "north,widget,2,10.00\n"
        "south,cable,1,4.00\n"
        "east,gizmo,0,9.99\n"
        "west,thing,x,2.00\n"
        "north,thing,1,1.5\n"
        "south,cable,1,4.50,extra\n"
    ),
}
TEST_CODE = """import { report } from './solution';
import { writeFileSync } from 'node:fs';

function eq(got: string, expected: string, label: string) {
  if (got !== expected) {
    throw new Error(label + '\\n--- got:\\n' + got + '\\n--- expected:\\n' + expected);
  }
}

eq(report('sales.csv'),
   ['region,total_units,revenue', 'north,5,50.00', 'south,3,13.00', 'invalid: 4'].join('\\n'),
   'sales.csv');

writeFileSync('only_comments.csv', '# res\\n\\n');
eq(report('only_comments.csv'),
   ['region,total_units,revenue', 'invalid: 0'].join('\\n'), 'nomes comentaris');

writeFileSync('bad.csv', 'north,a,1,2.5\\nnorth,b,-1,2.00\\nnorth,c,1,2.00\\n');
eq(report('bad.csv'),
   ['region,total_units,revenue', 'north,1,2.00', 'invalid: 2'].join('\\n'), 'invalides');

writeFileSync('sort.csv', 'zz,last,2,0.05\\naa,first,1,0.10\\n');
eq(report('sort.csv'),
   ['region,total_units,revenue', 'aa,1,0.10', 'zz,2,0.10', 'invalid: 0'].join('\\n'), 'ordenacio');
console.log('OK');"""
