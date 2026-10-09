ID = "count_lines_hard"
LANG = "bash"
PROMPT = """Implementa una funcio count_lines file que escrigui a stdout el nombre de linies del
fitxer. Trampes: el fitxer pot no acabar amb salt de linia (la darrera linia tambe compta)
i si el fitxer no existeix el resultat ha de ser 0 (cap text d'error a stdout)."""
TEST_CODE = 'source solution.sh\ntmp=$(mktemp)\nprintf \'a\\nb\\nc\' > "$tmp"\n[ "$(count_lines "$tmp")" = "3" ] || exit 1\nprintf \'x\\ny\\n\' > "$tmp"\n[ "$(count_lines "$tmp")" = "2" ] || exit 1\n[ "$(count_lines /no/existeix/mai_$$)" = "0" ] || exit 1\n: > "$tmp"\n[ "$(count_lines "$tmp")" = "0" ] || exit 1\nrm -f "$tmp"\necho OK'
