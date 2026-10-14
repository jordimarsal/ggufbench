ID = "ledger_fifo_expert"
LANG = "python"
PROMPT = """Implementa portfolio(path): llegeix un CSV de moviments de cartera i retorna
l'estat resultant aplicant FIFO (primer lot comprat, primer consumit) en l'ORDRE DE LES
LÍNIES (no per dates).

El fitxer `movements.csv` (a la feina de test; no el veus ara) té una línia per moviment:
`symbol,action,qty,price` amb valors com `AAPL,buy,10,100.00`.

Regles:
- symbol: text no buit, sense comes ni espais als extrems.
- action: exactament `buy` o `sell` (minúscules).
- qty: enter positiu (sense signe ni decimals).
- price: decimal positiu amb exactament 2 decimals.
- Una línia que no compleix TOT això és invàlida: es compta i es descarta (no afecta la
  resta). També és invàlida una `sell` de més quantitat de la que es té del símbol.
- Una compra crea un lot (qty, price). Una venda consumeix lots de més antic a més nou i
  acumula el benefici realitzat sumant (preu de venda - preu del lot) * quantitat consumida.

Retorna exactament:
    {"profit": {symbol: float},      # benefici realitzat, arrodonit a 2 decimals
     "holdings": {symbol: {"qty": int, "cost": float}},  # lots vius; cost arrodonit a 2
     "invalid": int}                 # línies descartades
Els símbols que queden a zero surten a holdings amb qty 0 i cost 0.0 (no pas absents)."""
EXTRA_FILES = {
    "movements.csv": (
        "AAPL,buy,10,100.00\n"
        "AAPL,buy,10,120.00\n"
        "AAPL,sell,10,130.00\n"
        "MSFT,buy,5,300.00\n"
        "MSFT,sell,7,310.00\n"
        "GOOG,buy,2,1000.00\n"
        "GOOG,sell,2,900.00\n"
        "AAPL,buy,1,140.00\n"
        "AAPL,sell,3,150.00\n"
        "bogus,hold,1,2.00\n"
        "AAPL,buy,,100.00\n"
    ),
}
TEST_CODE = """from solution import *
import os
assert os.path.exists("movements.csv")
out = portfolio("movements.csv")

# FIFO: la venda de 10 surt del lot de 100.00 (300.00), i la de 3 del lot de 120.00 (90.00).
assert out["profit"]["AAPL"] == 390.00, out["profit"]
assert out["profit"]["GOOG"] == -200.00, out["profit"]
# 10@120 quedaven despres de la primera venda; +1@140 de la linia 8; la venda de 3
# consumeix del lot antic -> queden 7@120 + 1@140.
assert out["holdings"]["AAPL"] == {"qty": 8, "cost": 980.00}, out["holdings"]
# La venda invalida no consumeix res: MSFT conserva el lot.
assert out["holdings"]["MSFT"] == {"qty": 5, "cost": 1500.00}, out["holdings"]
# Zero posicio viva -> present, no absent.
assert out["holdings"]["GOOG"] == {"qty": 0, "cost": 0.0}, out["holdings"]
# 3 linies invalides: action desconeguda, qty buida, sobrevenda.
assert out["invalid"] == 3, out["invalid"]

# L'ordre de les linies mana (FIFO per linia, no per data ni LIFO): una segona passada
# amb l'ordre invertit ha de donar un benefici diferent.
with open("movements2.csv", "w") as f:
    f.write("X,buy,1,10.00\\nX,buy,1,20.00\\nX,sell,1,30.00\\n")
o2 = portfolio("movements2.csv")
assert o2["profit"]["X"] == 20.00, o2          # FIFO: consumeix el lot de 10.00
assert o2["holdings"]["X"] == {"qty": 1, "cost": 20.00}, o2
print('OK')"""
