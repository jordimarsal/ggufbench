ID = "parallel_safe_tempfiles"
LANG = "bash"
GOAL = "Crea solution.sh que utilitzi mktemp amb disciplina sota set -euo pipefail per crear fitxers temporals únics i segurs en entorns paral·lels. El script ha de crear tres fitxers temporals amb continguts diferents, escriure-hi dades, llegir-los de nou i netejar-los al final. Els tests verifiquen que s'usa mktemp, que els noms són únics i que no queden residus."
INITIAL_FILES = {
    "solution.sh": "#!/bin/bash\nset -euo pipefail\n# Crea fitxers temporals (solució trencada: noms fixos, col·lisionen en paral·lel)\necho 'data1' > /tmp/paralleltmp1\necho 'data2' > /tmp/paralleltmp2\necho 'data3' > /tmp/paralleltmp3\ncat /tmp/paralleltmp1 /tmp/paralleltmp2 /tmp/paralleltmp3\nrm -f /tmp/paralleltmp1 /tmp/paralleltmp2 /tmp/paralleltmp3",
    "test_solution.sh": "grep -qF '$(mktemp' solution.sh || { echo 'solution must call mktemp'; exit 1; }\nbefore=$(ls /tmp/tmp.* 2>/dev/null | sort)\noutput=$(bash solution.sh)\n[ \"$(echo \"$output\" | wc -l)\" = \"3\" ] || exit 1\ngrep -q 'data1' <<< \"$output\" || exit 1\ngrep -q 'data2' <<< \"$output\" || exit 1\ngrep -q 'data3' <<< \"$output\" || exit 1\nafter=$(ls /tmp/tmp.* 2>/dev/null | sort)\n[ \"$before\" = \"$after\" ] || { echo 'temp files leaked'; exit 1; }\necho OK"
}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 8
