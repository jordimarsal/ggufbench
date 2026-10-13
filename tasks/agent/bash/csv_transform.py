ID = "csv_transform"
LANG = "bash"
GOAL = 'Crea solution.sh que llegeixi data.csv i imprimeixi el primer camp de cada línia (sense les cometes si és un camp citat).'
INITIAL_FILES = {
    "solution.sh": "#!/bin/bash\n# Transforma CSV: imprimeix només el primer camp per línia\nwhile IFS= read -r line; do\n    echo \"$line\"\ndone < data.csv",
    "test_solution.sh": "echo '\"Alice\",Bob,42' > data.csv\necho 'Charlie,\"Diana\",30' >> data.csv\necho '\"Eve,Frank\",George,50' >> data.csv\necho 'Hank,Ivy,60' >> data.csv\noutput=$(bash solution.sh)\n[ \"$(echo \"$output\" | sed -n '1p')\" = 'Alice' ] || exit 1\n[ \"$(echo \"$output\" | sed -n '2p')\" = 'Charlie' ] || exit 1\n[ \"$(echo \"$output\" | sed -n '3p')\" = 'Eve,Frank' ] || exit 1\n[ \"$(echo \"$output\" | sed -n '4p')\" = 'Hank' ] || exit 1\necho OK"
}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 8
