ID = "csv_stats_expert"
LANG = "bash"
PROMPT = """Implementa una funcio csv_stats FITXER que escrigui a stdout un informe exacte.

El fitxer te una linia per venda: `region,producte,quantitat,preu_unitari`
- quantitat: enter positiu; preu_unitari: decimal amb EXACTAMENT 2 decimals.
- Linies buides o nomes espais: es salten. Linies que comencen per # (despres d'espais
  opcionals): comentaris, es salten.
- Qualsevol altra linia es INVALIDA: es compta i es descarta (no afecta res mes).

Informe, exactament:
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
TEST_CODE = """source solution.sh
got="$(csv_stats sales.csv)"
expected='region,total_units,revenue
north,5,50.00
south,3,13.00
invalid: 4'
[ "$got" = "$expected" ] || { printf 'got:\\n%s\\nexpected:\\n%s\\n' "$got" "$expected" >&2; exit 1; }

printf '# nomes comentaris\\n\\n' > only_comments.csv
[ "$(csv_stats only_comments.csv)" = 'region,total_units,revenue
invalid: 0' ] || exit 1

printf 'north,a,1,2.5\\nnorth,b,-1,2.00\\nnorth,c,1,2.00\\n' > bad.csv
[ "$(csv_stats bad.csv)" = 'region,total_units,revenue
north,1,2.00
invalid: 2' ] || exit 1

printf 'zz,last,2,0.05\\naa,first,1,0.10\\n' > sort.csv
[ "$(csv_stats sort.csv)" = 'region,total_units,revenue
aa,1,0.10
zz,2,0.10
invalid: 0' ] || exit 1
echo OK"""
