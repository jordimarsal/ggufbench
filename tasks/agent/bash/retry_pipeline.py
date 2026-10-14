ID = "retry_pipeline"
LANG = "bash"
GOAL = """El pipeline d'operacions no reintenta prou: una operació que falla el primer intent
hauria de tornar-ho a provar fins a `RETRY_MAX` intents abans de donar-se per vençuda, i
avui s'atura al primer fracas.

Punt d'entrada: `solution.sh OPERACIO` (executa l'operacio i imprimeix `SUCCESS` o `FAILURE`;
retorna 0 nomes si ha acabat be).

Contracte:
- `RETRY_MAX` ve de `config.env` (valor per defecte 3) i es pot sobreescriure per entorn.
- Cada intent crida `run_attempt OPERACIO`, que compta l'intent a `state/<operacio>.count`
  (comença a 1) i falla mentre el comptador sigui mes petit que 2.
- Cal fer com a maxim `RETRY_MAX` intents; si un intent te exit, s'imprimeix `SUCCESS` i el
  proces acaba amb 0. Si s'esgoten els intents, `FAILURE` i exit diferent de zero.

Esbrina on fallen les coses: el punt d'entrada no és l'únic fitxer del projecte."""
INITIAL_FILES = {
    "solution.sh": '''#!/bin/bash
# Executa una operacio amb reintents
source config.env
source attempt.sh
source status_tracker.sh

main() {
  local op="${1:-default}"
  # BUG: s'atura al primer fracas en lloc de reintentar fins a RETRY_MAX
  if run_attempt "$op"; then
    mark_success "$op"
    return 0
  fi
  mark_failure "$op"
  return 1
}

main "$@"
''',
    "attempt.sh": '''#!/bin/bash
# Simulador de l'operacio: falla mentre el comptador sigui < 2

STATE_DIR="${STATE_DIR:-state}"

run_attempt() {
  local op="$1" count
  mkdir -p "$STATE_DIR"
  count=$(cat "$STATE_DIR/$op.count" 2>/dev/null || echo 0)
  count=$((count + 1))
  printf '%s\\n' "$count" > "$STATE_DIR/$op.count"
  [ "$count" -ge 2 ] && return 0
  return 1
}
''',
    "status_tracker.sh": '''#!/bin/bash
# Marcador d'estat de l'operacio

STATE_DIR="${STATE_DIR:-state}"

mark_success() {
  local op="$1"
  printf '%s\\n' "SUCCESS"
  printf '%s\\n' "success" > "$STATE_DIR/$op.status"
}

mark_failure() {
  local op="$1"
  printf '%s\\n' "FAILURE"
  printf '%s\\n' "failure" > "$STATE_DIR/$op.status"
}
''',
    "config.env": '''#!/bin/bash
# Limits del pipeline
RETRY_MAX="${RETRY_MAX:-3}"
''',
    "test_solution.sh": '''#!/bin/bash
rm -rf state
mkdir -p state

# Amb el limit per defecte (3), l'operacio passa al segon intent
out=$(STATE_DIR=state bash solution.sh deploy 2>&1)
rc=$?
[ "$rc" -eq 0 ] || { echo "exit=$rc out=$out" >&2; exit 1; }
echo "$out" | grep -q 'SUCCESS' || { echo "sense SUCCESS: $out" >&2; exit 1; }
[ "$(cat state/deploy.count)" = "2" ] || { echo "count=$(cat state/deploy.count)" >&2; exit 1; }

# Amb RETRY_MAX=1 nomes es pot fer un intent: ha de fallar
rm -rf state
mkdir -p state
out=$(RETRY_MAX=1 STATE_DIR=state bash solution.sh fast 2>&1)
rc=$?
[ "$rc" -ne 0 ] || { echo "hauria de fallar" >&2; exit 1; }
echo "$out" | grep -q 'FAILURE' || { echo "sense FAILURE: $out" >&2; exit 1; }
[ "$(cat state/fast.count)" = "1" ] || { echo "count=$(cat state/fast.count)" >&2; exit 1; }
echo OK
''',
}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 14
