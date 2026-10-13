ID = "retry_backoff"
LANG = "bash"
GOAL = 'Crea retry.sh que execute un comandament amb reintent exponencial: fins a MAX_RETRIES (per defecte 5), delay inicial de 1s multiplicat per 2^attempt, max_delay de 5s.'
INITIAL_FILES = {
    "solution.sh": "#!/bin/bash\n# Executa un comandament amb reintent exponencial\nmax_retries=${MAX_RETRIES:-5}\ndelay=1\nfor i in $(seq 0 $((max_retries-1))); do\n    if \"$@\"; then\n        echo \"OK\"\n        exit 0\n    fi\n    sleep $delay\n    delay=$((delay * 2))\ndone\necho \"FAILED after $max_retries retries\"",
    "test_solution.sh": "output=$(bash solution.sh bash -c 'exit 0')\n[ \"$output\" = 'OK' ] || exit 1\noutput=$(bash solution.sh bash -c 'exit 1')\n[ \"$output\" != 'OK' ] || exit 1\necho OK"
}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 8
