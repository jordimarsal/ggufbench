ID = "readings_etl_expert"
LANG = "python"
PROMPT = """Implementa process(path): analitza un fitxer CSV de sensors i retorna un resum.

A la feina de test hi ha el fitxer `readings.csv` (l'hauras de processar en temps
d'execucio; no el pots veure ara). Format i regles:

- Un registre per linia: `name,qty,price` (separat per comes).
- Linies buides o que nomes son espais: es salten.
- Linies que comencen per `#` (despres d'espais opcions): comentarios, es salten.
- Els camps poden venir entre cometes dobles: un camp que DESPRES d'espais opcions
  comenca per `"` acaba a la seva `"` de tancament i el seu contingut pot contenir
  comes (es UN sol camp); les cometes exteriors s'eliminen. Les cometes que no
  obren un camp son literals. Despres tretze espais al voltant de cada camp.
- Els finals de linia poden ser LF o CRLF.
- Un registre es valid si te EXACTAMENT 3 camps (name, qty, price), qty es un enter
  (signe opcional) i price es un numero decimal. Qualsevol altra cosa es INVALIDA
  (es compta i es descarta; no toca res mes).

Exemple de linies:
    # id, qty, preu
    sensor-a,10,2.50
     sensor-b , 5 , 3.00
    "sensor-x",4,1.00

Retorna exactament aquest diccionari:
    {"valid": int,        # registres vàlids
     "invalid": int,      # linies no saltables que no parsegen
     "revenue": float,    # suma de qty*price dels vàlids, rodada a 2 decimals
     "names": list}       # noms dels vàlids, sense duplicats, ordenats"""
TEST_CODE = """from solution import *
r = process('readings.csv')
assert r['valid'] == 12, r
assert r['invalid'] == 4, r
assert r['revenue'] == 96.65, r
assert r['names'] == ['Doe, John', 'Hall, Rita', 'sen"sor', 'sensor-a',
                      'sensor-b', 'sensor-d', 'sensor-f', 'sensor-h',
                      'sensor-j', 'sensor-k', 'sensor-x'], r['names']
print('OK')"""
EXTRA_FILES = {"readings.csv": """# Lectures del mes — export 2026-09-30
sensor-a,10,2.50
 sensor-b , 5 , 3.00
# migjorn

"Doe, John",3,10.00
sensor-d,2,4.50
sensor-a,1,2.50
bad-row-with-no-commas
sensor-e,xyz,1.50
sensor-f,4,0.75
sensor-g,2,notaprice
"Hall, Rita",1,6.40
sensor-h,8,0.50
sensor-i,1,2.00,extra
"sensor-x",4,1.00
sen"sor,1,1.00
sensor-k,-2,5.00
sensor-j,3,2.25   \r
"""}
