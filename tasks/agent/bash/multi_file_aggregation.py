ID = "multi_file_aggregation"
LANG = "bash"
GOAL = 'Compta les línies ERROR a cada fitxer de registre i imprimeix el total de tots els fitxers junts. Format: un número per línia.'
INITIAL_FILES = {
    "solution.sh": "#!/bin/bash\n# Compta els ERRORs en tots els fitxers\ntotal=0\nfor f in *.log; do\n    count=$(grep -c ERROR \"$f\")\n    echo $count\n    total=$((total + count))\ndone\necho $total",
    "test_solution.sh": "echo 'INFO Starting service\nERROR Connection refused\nERROR Timeout exceeded\nINFO Processing request\nERROR Connection refused\nERROR Disk full\nERROR Connection refused' > error_day1.log\necho 'INFO Service started\nERROR Timeout exceeded\nERROR Permission denied\nERROR Timeout exceeded\nERROR Connection refused\nINFO Request complete' > error_day2.log\necho 'INFO Health check OK\nERROR Connection refused\nERROR Disk full\nERROR Connection refused\nINFO Shutdown' > error_day3.log\noutput=$(bash solution.sh)\necho \"$output\" | grep -q '^5$' || exit 1\necho \"$output\" | grep -q '^4$' || exit 1\necho \"$output\" | grep -q '^3$' || exit 1\ntotal=$(echo \"$output\" | tail -1)\n[ \"$total\" = \"12\" ] || exit 1\necho OK"
}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 8
