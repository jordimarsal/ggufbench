ID = "log_level_filter"
LANG = "bash"
GOAL = """Els registres d'ERROR s'escriuen per stdout en lloc de stderr quan es filtren
per nivell — el sistema espera que els errors surtin per stderr i la monitorització no
els detecta.

Punt d'entrada: main() de solution.sh (llegeix stdin, filtra per NIVELL, imprimeix).
`NIVELL` és una variable d'entorn amb valor per defecte INFO.
Cada linia del fitxer té format: DATA HORA NIVELL MISSATGE.

Esbrina on fallen les coses: el punt d'entrada no és l'únic fitxer del projecte."""
INITIAL_FILES = {
    "solution.sh": '''#!/bin/bash
# Filtra registres per nivell
source utils.sh
source parse_log.sh
source log_level_filter.sh

main() {
  local level="${NIVELLS:-INFO}"
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    local parsed=$(parse_line "$line")
    if is_match "$parsed" "$level"; then
      format_output "$parsed"
    fi
  done
}

main''',
    "utils.sh": '''#!/bin/bash
# Utilitats comunes
log_info() { echo "[INFO] $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }''',
    "parse_log.sh": '''#!/bin/bash
# Parseja una linia de registre: DATA HORA NIVELL MISSATGE
parse_line() {
  local line="$1"
  # Treu la data i hora (primers dos camps)
  local rest="${line#* }"
  rest="${rest#* }"
  local level="${rest%% *}"
  local msg="${rest#* }"
  echo "$level|$msg"
}''',
    "log_level_filter.sh": '''#!/bin/bash
# Filtra per nivell de registre
is_match() {
  local parsed="$1"
  local target="$2"
  local level="${parsed%%|*}"
  if [ "$level" = "$target" ]; then
    return 0
  fi
  return 1
}

# BUG: ERROR s'escriu per stdout en lloc de stderr
format_output() {
  local parsed="$1"
  local level="${parsed%%|*}"
  local msg="${parsed#*|}"
  if [ "$level" = "ERROR" ]; then
    echo "[FATAL] $msg"   # BUG: hauria de ser >&2
  else
    echo "$msg"
  fi
}''',
    "config.env": '''#!/bin/bash
# Configuració del sistema de registres
LOG_FORMAT="DATA HORA NIVELL MISSATGE"
DEFAULT_LEVEL="INFO"''',
    "test_solution.sh": '''#!/bin/bash
tmpfile=$(mktemp)
cat > "$tmpfile" <<EOF
2024-01-15 10:00:01 INFO Starting service
2024-01-15 10:00:02 ERROR Connection refused
2024-01-15 10:00:03 WARN High memory usage
2024-01-15 10:00:04 ERROR Timeout exceeded
2024-01-15 10:00:05 DEBUG Request received
2024-01-15 10:00:06 INFO Processing complete
EOF

# Test 1: filtrar només ERROR — tots han d'anar a stderr
stderr_output=$(cat "$tmpfile" | NIVELLS=ERROR bash solution.sh 2>&1 >/dev/null)
[ -z "$stderr_output" ] && exit 1
echo "$stderr_output" | grep -q 'Connection refused' || exit 1
echo "$stderr_output" | grep -q 'Timeout exceeded' || exit 1

# Test 2: filtrar INFO — ha de sortir per stdout, no per stderr
stdout_output=$(cat "$tmpfile" | NIVELLS=INFO bash solution.sh 2>/dev/null)
[ -z "$stdout_output" ] && exit 1
echo "$stdout_output" | grep -q 'Starting service' || exit 1
echo "$stdout_output" | grep -q 'Processing complete' || exit 1

# Test 3: filtrar WARN — una sola linia
warn_output=$(cat "$tmpfile" | NIVELLS=WARN bash solution.sh 2>/dev/null)
echo "$warn_output" | grep -c 'High memory usage' | grep -q '^1$' || exit 1

# Test 4: la llibreria format_output tambe ha de manar ERROR a stderr (es una funcio,
# no un script: s'ha de carregar)
error_fmt=$( (source log_level_filter.sh; format_output "ERROR|Something broke") 2>&1 >/dev/null )
echo "$error_fmt" | grep -q 'Something broke' || exit 1
info_fmt=$( (source log_level_filter.sh; format_output "INFO|tot be") 2>/dev/null )
echo "$info_fmt" | grep -q 'tot be' || exit 1
rm -f "$tmpfile"
echo "OK"''',
}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 14
