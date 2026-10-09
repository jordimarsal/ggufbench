ID = "fix_apply_discount_hard"
LANG = "python"
PROMPT = """La funció següent té un bug subtil: muta la llista d'entrada.

    def apply_discount(prices, discount=0.10):
        for i in range(len(prices)):
            prices[i] = round(prices[i] * (1 - discount), 2)
        return prices

Corregeix-la: ha de retornar una NOVA llista amb cada preu amb el descompte aplicat
(arrodonit a 2 decimals) i no ha de modificar la llista rebuda."""
TEST_CODE = """from solution import *
assert apply_discount([100.0, 250.5, 19.99]) == [90.0, 225.45, 17.99]
original = [10.0, 20.0]
out = apply_discount(original)
assert original == [10.0, 20.0], "no ha de mutar l'entrada"
assert out == [9.0, 18.0]
assert apply_discount([]) == []
assert apply_discount([200.0], 0.5) == [100.0]
print('OK')"""
