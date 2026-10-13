ID = "config_file_parser"
LANG = "bash"
GOAL = "Crea solution.sh que llegeixi un fitxer de configuració INI (sections amb [nom], clau=valor dins cada secció) i imprimeixi les seccions en format 'section:key=value', una per línia, ordenades alfabèticament per secció i després per clau."
INITIAL_FILES = {
    "solution.sh": "#!/bin/bash\nset -euo pipefail\n# Parseja fitxers INI (solució trencada: ignora les seccions)\nif [[ $# -lt 1 ]]; then\n    echo \"Usage: $0 <file>\"\n    exit 1\nfi\nfile=\"$1\"\nwhile IFS= read -r line || [[ -n \"$line\" ]]; do\n    if [[ \"$line\" =~ ^([a-zA-Z_][a-zA-Z0-9_]*)=(.*)$ ]]; then\n        echo \"${BASH_REMATCH[1]}=${BASH_REMATCH[2]}\"\n    fi\ndone < \"$file\"",
    "test_solution.sh": "cat > config.ini << 'EOF'\n[database]\nhost=localhost\nport=5432\nname=mydb\n\n[logging]\nlevel=info\npath=/var/log/app.log\n\n[app]\ndebug=false\nversion=1.0\nEOF\noutput=$(bash solution.sh config.ini)\necho \"$output\" | grep -q '^app:debug=false' || exit 1\necho \"$output\" | grep -q '^app:version=1.0' || exit 1\necho \"$output\" | grep -q '^database:host=localhost' || exit 1\necho \"$output\" | grep -q '^database:name=mydb' || exit 1\necho \"$output\" | grep -q '^database:port=5432' || exit 1\necho \"$output\" | grep -q '^logging:level=info' || exit 1\necho \"$output\" | grep -q '^logging:path=/var/log/app.log' || exit 1\nlines=$(echo \"$output\" | wc -l)\n[ \"$lines\" = \"7\" ] || exit 1\n[ \"$(echo \"$output\")\" = \"$(echo \"$output\" | sort)\" ] || { echo 'output not sorted'; exit 1; }\necho OK"
}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 8
