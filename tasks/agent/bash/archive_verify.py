ID = "archive_verify"
LANG = "bash"
GOAL = 'Crea archive.sh que comprimeixi el directori mydata amb tar.gz, generi checksums SHA256 de cada fitxer original a manifest.txt, i després verifiqui que l\'arxiu es pot extreure correctament.'
INITIAL_FILES = {
    "solution.sh": "#!/bin/bash\n# Comprimeix mydata/, genera manifest.txt amb checksums SHA256, verifica l'extracció\ntar czf archive.tar.gz mydata/\nsha256sum mydata/* > manifest.txt\ntmpdir=$(mktemp -d)\ntar xzf archive.tar.gz -C $tmpdir\nfor f in $(cat manifest.txt | awk '{print $2}'); do\n    orig_hash=$(grep \"$f\" manifest.txt | awk '{print $1}')\n    ext_hash=$(sha256sum \"$tmpdir/$f\" | awk '{print $1}')\n    [ \"$orig_hash\" = \"$ext_hash\" ] || exit 1\ndone\nrm -rf $tmpdir\necho \"OK\"",
    "test_solution.sh": "mkdir -p mydata\necho 'hello' > mydata/a.txt\necho 'world' > mydata/b.txt\nbash solution.sh | grep -q '^OK$' || exit 1\n[ -f archive.tar.gz ] || exit 1\n[ -f manifest.txt ] || exit 1\nlines=$(wc -l < manifest.txt)\n[ \"$lines\" = \"2\" ] || exit 1\necho OK"
}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 8
