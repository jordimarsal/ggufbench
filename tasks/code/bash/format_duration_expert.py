ID = "format_duration_expert"
LANG = "bash"
PROMPT = """Implementa una funcio format_duration SEGONS [MODE] que escrigui a stdout una durada
humana. SEGONS es un enter >= 0; qualsevol altra cosa (negatiu, decimals, text, buit) ha de
retornar un estat diferent de zero i no escriure res. MODE es opcional i nomes pot ser
`short` (per defecte) o `clock`.

MODE `short`: parts d'unitat `d`, `h`, `m`, `s`, separades per un espai, ometent les parts
que valen zero. Si el total es 0 -> exactament `0s`.
  59 -> 59s | 60 -> 1m | 61 -> 1m 1s | 3600 -> 1h | 3661 -> 1h 1m 1s
  86400 -> 1d | 90061 -> 1d 1h 1m 1s | 172800 -> 2d

MODE `clock`: `HH:MM:SS` amb zeros a l'esquerra i les hores sense limit (els dies es
dobleguen dins de les hores).
  0 -> 00:00:00 | 61 -> 00:01:01 | 3661 -> 01:01:01 | 90061 -> 25:01:01"""
TEST_CODE = """source solution.sh
[ "$(format_duration 0)" = "0s" ] || exit 1
[ "$(format_duration 59)" = "59s" ] || exit 1
[ "$(format_duration 60)" = "1m" ] || exit 1
[ "$(format_duration 61)" = "1m 1s" ] || exit 1
[ "$(format_duration 3600)" = "1h" ] || exit 1
[ "$(format_duration 3661)" = "1h 1m 1s" ] || exit 1
[ "$(format_duration 86400)" = "1d" ] || exit 1
[ "$(format_duration 90061)" = "1d 1h 1m 1s" ] || exit 1
[ "$(format_duration 172800)" = "2d" ] || exit 1
[ "$(format_duration 86399)" = "23h 59m 59s" ] || exit 1

[ "$(format_duration 0 clock)" = "00:00:00" ] || exit 1
[ "$(format_duration 61 clock)" = "00:01:01" ] || exit 1
[ "$(format_duration 3661 clock)" = "01:01:01" ] || exit 1
[ "$(format_duration 90061 clock)" = "25:01:01" ] || exit 1

for bad in -1 1.5 abc ""; do
    if format_duration "$bad" >/dev/null 2>&1; then echo "hauria de fallar: [$bad]" >&2; exit 1; fi
done
if format_duration 60 fortnight >/dev/null 2>&1; then echo "mode invalid" >&2; exit 1; fi
echo OK"""
