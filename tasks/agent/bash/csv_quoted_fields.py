ID = "csv_quoted_fields"
LANG = "bash"
GOAL = """El resum de vendes per categoria surt amb totals equivocats en fitxers CSV on algun
camp va entre cometes i conté comes (per exemple "Llibre, Python" és UN sol camp).

Punt d'entrada: `solution.sh FITXER` (llegeix el CSV i imprimeix una linia per categoria,
ordenades alfabeticament, amb el format `<categoria>: sum=<total>, count=<n>`).

El CSV té capcalera `Categoria,Producte,Valor,Quantitat`; les linies amb camps entre cometes
poden tenir comes a dins; les linies buides es salten. El total és la suma de la columna
`Valor` i el comptador són les linies valides de la categoria.

Esbrina on fallen les coses: el punt d'entrada no és l'únic fitxer del projecte."""
INITIAL_FILES = {
    "solution.sh": '''#!/bin/bash
# Resum de vendes per categoria
source csv_parser.sh
source aggregator.sh

main() {
  local input="${1:-data.csv}"
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    local fields
    fields=$(parse_csv_line "$line")
    if is_header "$fields"; then
      continue
    fi
    aggregate_row "$fields"
  done < "$input"
  print_totals
}

main "$@"
''',
    "csv_parser.sh": '''#!/bin/bash
# Converteix una linia CSV en camps separats per salt de linia

# BUG: parteix per totes les comes, tambe les que van DINS d'un camp entre cometes
parse_csv_line() {
  printf '%s\\n' "$1" | tr ',' '\\n'
}

# La capcalera es la linia que conte "Categoria"
is_header() {
  local first
  first=$(printf '%s\\n' "$1" | head -1)
  case "$first" in
    *Categoria*) return 0 ;;
  esac
  return 1
}
''',
    "aggregator.sh": '''#!/bin/bash
# Acumula sum/count per categoria

declare -A SUM
declare -A COUNT

aggregate_row() {
  local fields="$1"
  local cat prod valor
  cat=$(printf '%s\\n' "$fields" | sed -n 1p)
  prod=$(printf '%s\\n' "$fields" | sed -n 2p)
  valor=$(printf '%s\\n' "$fields" | sed -n 3p)
  [ -z "$cat" ] && return 0
  SUM["$cat"]=$(( ${SUM["$cat"]:-0} + valor ))
  COUNT["$cat"]=$(( ${COUNT["$cat"]:-0} + 1 ))
}

print_totals() {
  local cat
  for cat in $(printf '%s\\n' "${!SUM[@]}" | sort); do
    echo "${cat}: sum=${SUM[$cat]}, count=${COUNT[$cat]}"
  done
}
''',
    "data.csv": '''Categoria,Producte,Valor,Quantitat
"Venda","Llibre, Python",50,3
Servei,Consultoria,80,1
"Venda","Manual, Bash",45,2
Alquiler,Espai de treball,60,1
''',
    "test_solution.sh": '''#!/bin/bash
# El total ha de sortir amb el camp entre cometes tractat com UN sol camp
out=$(bash solution.sh data.csv) || exit 1

expected='Alquiler: sum=60, count=1
Servei: sum=80, count=1
Venda: sum=95, count=2'
[ "$out" = "$expected" ] || { printf 'got:\\n%s\\nexpected:\\n%s\\n' "$out" "$expected" >&2; exit 1; }

# Un fitxer amb una sola linia entre cometes tambe ha de quadrar
printf 'Categoria,Producte,Valor,Quantitat\\n"Venda","A, B",7,1\\n' > one.csv
[ "$(bash solution.sh one.csv)" = 'Venda: sum=7, count=1' ] || exit 1
echo OK
''',
}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 14
