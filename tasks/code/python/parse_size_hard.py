ID = "parse_size_hard"
LANG = "python"
PROMPT = """Implementa parse_size(text) -> int: converteix una mida humana en bytes.

Regles exactes:
- Número decimal estricte, sense signe, amb com a màxim un punt decimal i com a mínim
  un dígit abans i després del punt si el punt hi és ("0", "512", "1.5" sí; ".5", "1.",
  "1.2.3", "-1", "" no).
- Sufix d'unitat opcional, insensible a majúscules, amb una "B" final opcional i
  equivalent: K/KB = 1000, M/MB = 1000^2, G/GB = 1000^3, T/TB = 1000^4.
- Espais al principi i al final permesos, i com a molt un espai entre el número i la
  unitat (" 4 Gb " és vàlid).
- Qualsevol altra cosa llança ValueError.
- El resultat és un int: si el decimal no és exacte es trunca cap a baix
  ("1.0005K" -> 1000).
"""
TEST_CODE = """from solution import *
assert parse_size("0") == 0
assert parse_size("512") == 512
assert parse_size("1K") == 1000
assert parse_size("1k") == 1000
assert parse_size("1KB") == 1000
assert parse_size("1.5K") == 1500
assert parse_size("2.5M") == 2500000
assert parse_size("3G") == 3000000000
assert parse_size("1T") == 1000000000000
assert parse_size(" 4 Gb ") == 4000000000
assert parse_size("1.0005K") == 1000
assert isinstance(parse_size("1.5K"), int)
for bad in ("", "   ", "K", "KB", "1X", "1.2.3K", "-1", ".5K", "1.K", "1Kb2", "1 K K", "1 2K"):
    try:
        parse_size(bad)
    except ValueError:
        continue
    raise AssertionError("hauria de fallar: %r" % bad)
print('OK')"""
