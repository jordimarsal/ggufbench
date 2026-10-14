ID = "parse_size_hard"
LANG = "bash"
PROMPT = """Implementa una funcio parse_size TEXT que escrigui a stdout la mida en bytes com a
enter, amb aquestes regles:

- Numero decimal estricte, sense signe, amb com a maxim un punt decimal i com a minim un
  digit abans i despres del punt si el punt hi es ("0", "512", "1.5" si; ".5", "1.", "1.2.3",
  "-1", "" no).
- Sufix d'unitat opcional insensible a majuscules, amb una "B" final opcional i equivalent:
  K/KB = 1000, M/MB = 1000^2, G/GB = 1000^3, T/TB = 1000^4.
- Espais al principi i al final permesos, i com a maxim un espai entre el numero i la unitat
  (" 4 Gb " es valid).
- Qualsevol altra cosa: la funcio ha de retornar un estat diferent de zero i no escriure res.
- Si el decimal no es exacte es trunca cap a baix ("1.0005K" -> 1000)."""
TEST_CODE = """source solution.sh
[ "$(parse_size 0)" = "0" ] || exit 1
[ "$(parse_size 512)" = "512" ] || exit 1
[ "$(parse_size 1K)" = "1000" ] || exit 1
[ "$(parse_size 1k)" = "1000" ] || exit 1
[ "$(parse_size 1KB)" = "1000" ] || exit 1
[ "$(parse_size 1.5K)" = "1500" ] || exit 1
[ "$(parse_size 2.5M)" = "2500000" ] || exit 1
[ "$(parse_size 3G)" = "3000000000" ] || exit 1
[ "$(parse_size 1T)" = "1000000000000" ] || exit 1
[ "$(parse_size ' 4 Gb ')" = "4000000000" ] || exit 1
[ "$(parse_size 1.0005K)" = "1000" ] || exit 1
for bad in "" "   " K KB 1X 1.2.3K -1 .5K 1.K 1Kb2 "1 K K" "1 2K"; do
    if parse_size "$bad" >/dev/null 2>&1; then echo "hauria de fallar: [$bad]" >&2; exit 1; fi
done
echo OK"""
