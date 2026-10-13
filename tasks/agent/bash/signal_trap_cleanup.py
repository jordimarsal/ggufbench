ID = "signal_trap_cleanup"
LANG = "bash"
GOAL = "Crea solution.sh que utilitzi traps per netejar fitxers temporals en senyals EXIT i INT (SIGINT). El script ha de crear un fitxer temporal amb mktemp, simular processament (sleep), i assegurar-se que el fitxer es borra tant en sortida normal com en interrupció. Els tests verifiquen la neteja."
INITIAL_FILES = {
    "solution.sh": "#!/bin/bash\nset -euo pipefail\ntmpfile=$(mktemp)\necho 'processing data' > \"$tmpfile\"\nsleep 1\ncat \"$tmpfile\"\necho \"done\"",
    "test_solution.sh": "before=$(ls /tmp/tmp.* 2>/dev/null | sort)\noutput=$(timeout 5 bash solution.sh)\ngrep -q 'processing data' <<< \"$output\" || exit 1\ngrep -q 'done' <<< \"$output\" || exit 1\nafter=$(ls /tmp/tmp.* 2>/dev/null | sort)\n[ \"$before\" = \"$after\" ] || { echo 'temp files leaked on normal exit'; exit 1; }\nbash solution.sh & pid=$!\nsleep 0.4\nkill -INT $pid 2>/dev/null\nwait $pid 2>/dev/null\nsleep 0.2\nafterint=$(ls /tmp/tmp.* 2>/dev/null | sort)\n[ \"$before\" = \"$afterint\" ] || { echo 'temp files leaked on INT'; exit 1; }\necho OK"
}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 8
