ID = "log_filter_debug_expert"
LANG = "bash"
PROMPT = """Aquest script d'analisi de logs te 3 errors subtils. Corregeix-los TORNANT EL
SCRIPT COMPLET (mateixes funcions, mateixa API). Contracte del script corregit:
- count_matches PATTERN FILE: linies del fitxer que contenen el patro (subcadre
  literal); 0 si cap.
- unique_words FILE: paraules (separades per qualsevol espai) sense repetir,
  ordenades amb LC_ALL=C, una per linia.
- last_match PATTERN FILE: ultima linia que conte el patro (buida si cap).
IMPORTANT: el contingut dels logs pot contenir `*` i espais: han de tractar-se
com a text, mai com a comodins ni com a paraules separades.

```bash
#!/usr/bin/env bash
# utilitats d'analisi de logs de desplegament

count_matches() {
    # quantes linies contenen el patro (subcadre literal)
    local pattern="$1" file="$2" count=0
    grep -F -- "$pattern" "$file" | while IFS= read -r line; do
        count=$((count + 1))
    done
    echo "$count"
}

unique_words() {
    # paraules uniques ordenades (LC_ALL=C), una per linia
    local file="$1" word out=""
    for word in $(cat "$file"); do
        case " $out " in
            *" $word "*) ;;
            *) out="$out $word" ;;
        esac
    done
    printf '%s\\n' $out | LC_ALL=C sort
}

last_match() {
    # ultima linia que conte el patro
    local pattern="$1" file="$2" line last=""
    while IFS= read -r line; do
        last="$line"
    done < <(grep -F -- "$pattern" "$file" | head -n -1)
    printf '%s\\n' "$last"
}
```"""
TEST_CODE = """source solution.sh
a=$(mktemp); b=$(mktemp)
printf 'foo\\nbar foo\\nbaz foo\\nqux\\n' > "$a"
[ "$(count_matches foo "$a")" = "3" ] || { echo "count: $(count_matches foo "$a")"; exit 1; }
[ "$(count_matches zzz "$a")" = "0" ] || { echo "count zzz"; exit 1; }
[ "$(last_match foo "$a")" = "baz foo" ] || { echo "last: $(last_match foo "$a")"; exit 1; }
printf 'beta alpha beta * alpha\\n' > "$b"
[ "$(unique_words "$b")" = "$(printf '*\\nalpha\\nbeta')" ] || { echo "uniq: $(unique_words "$b")"; exit 1; }
rm -f "$a" "$b"
echo OK"""
