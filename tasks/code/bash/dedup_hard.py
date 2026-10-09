ID = "dedup_hard"
LANG = "bash"
PROMPT = """Implementa una funcio dedup que rebi paraules com a arguments i escrigui a stdout les
mateixes paraules sense repetits, conservant l'ordre de la primera aparicio, separades per
un espai. Sense arguments, sortida buida."""
TEST_CODE = 'source solution.sh\n[ "$(dedup a b a c a)" = "a b c" ] || exit 1\n[ "$(dedup x y z)" = "x y z" ] || exit 1\n[ "$(dedup a a a)" = "a" ] || exit 1\n[ "$(dedup 2 1 2 1 3)" = "2 1 3" ] || exit 1\n[ "$(dedup)" = "" ] || exit 1\necho OK'
