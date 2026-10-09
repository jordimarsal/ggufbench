ID = "sum_col_hard"
LANG = "bash"
PROMPT = """Implementa una funcio sum_col N file que escrigui a stdout la suma de la columna N d'un
fitxer CSV (separat per comes). Les linies que comencen per # son comentaris i es salten;
les linies buides valen 0. El resultat es un enter."""
TEST_CODE = 'source solution.sh\ntmp=$(mktemp)\nprintf \'10,20,30\\n# antic: 999,999,999\\n1,2,3\\n\\n4,5,6\\n\' > "$tmp"\n[ "$(sum_col 1 "$tmp")" = "15" ] || exit 1\n[ "$(sum_col 2 "$tmp")" = "27" ] || exit 1\n[ "$(sum_col 3 "$tmp")" = "39" ] || exit 1\nprintf \'# nomes comentaris\\n\' > "$tmp"\n[ "$(sum_col 2 "$tmp")" = "0" ] || exit 1\nrm -f "$tmp"\necho OK'
