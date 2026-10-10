ID = "access_agg_expert"
LANG = "bash"
PROMPT = """Implementa agg(FILE): resume un fitxer d'accés HTTP. A la feina de test hi ha el
fitxer `access.log` (l'hauras de processar en temps d'execucio; no el pots veure
ara). Format de cada linia (camps separats per un o mes espais/tabs):

    METHOD PATH STATUS BYTES

Regles:
- PATH pot venir entre cometes dobles: el contingut (amb espais) es UN SOL camp i
  les cometes exteriors s'eliminen. La resta de camps es parteixen per espais.
- Linies buides o que comencen per `#` (despres d'espais): es salten.
- Finals de linia LF o CRLF.
- Una linia es valida si te EXACTAMENT 4 camps, STATUS es un enter de 3 digits
  entre 100 i 599, i BYTES es un enter >= 0 o `-` (que val 0). Qualsevol altre
  cosa es una linia INVALIDA (es compta i prou).

El resultat es UNA linia a stdout: `VALID INVALID BYTES ERRORS` — BYTES es la
suma dels bytes de les valides; ERRORS es el nombre de valides amb STATUS >= 500."""
TEST_CODE = """source solution.sh
t=$(mktemp)
printf 'GET /a 200 10\\n#c\\n\\nGET "/b c/d" 404 -\\nGET /e 500 3\\nGET /f 99 4\\nGET /g 200 x\\nGET /h 200 5 6\\n' > "$t"
[ "$(agg "$t")" = "3 3 13 1" ] || { echo "inline: $(agg "$t")"; exit 1; }
rm -f "$t"
[ "$(agg access.log)" = "12 4 14626 2" ] || { echo "access.log: $(agg access.log)"; exit 1; }
echo OK"""
EXTRA_FILES = {"access.log": """# acces 2026-09-29 — prod
GET /api/v1/users 200 512
GET "/app/static/main.js" 200 12400
POST /api/v1/login 302 89
GET /api/v1/items 404 198
  GET   /api/v1/items   503   77
PUT /api/v1/items/9 200 -
DELETE /api/v1/items/9 204 0
GET /api/v1/users?age=99 500 1024
get /lower 200 10
GET /bad/status 99 10
GET /bad/bytes abc 10
GET /bad/bytes 200 12.5
THIS LINE HAS TOO MANY TOKENS HERE NOW
GET "/path with spaces/x" 201 42
POST /api/v1/login 200 210

GET /trailing 200 64\r
"""}
