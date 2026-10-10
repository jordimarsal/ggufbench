ID = "csv_index_expert"
LANG = "java"
PROMPT = """Implementa un metode estatic de la classe Solution:

    public static String process(String path)

que resumeix el fitxer `sales.csv` (a la feina de test; l'hauras de processar en
temps d'execucio, no el pots veure ara). Format d'una linia: `store,amount,tag`

Regles:
- Linies buides o que comencen per `#` (despres d'espais): es salten.
- El camp `store` pot venir entre cometes dobles: el contingut (amb comes) es UN
  SOL camp i les cometes exteriors s'eliminen. La resta es parteixen per comes.
- Si un camp obre cometes i NO les tanca, la linia es INVALIDA.
- Cada camp es recolza de espais per fora.
- Una linia es valida si te EXACTAMENT 3 camps, `amount` es un decimal amb PUNT
  (signe opcional, sense notacio cientifica: `1E2` NO val) mes gran o igual que
  0, i `tag` es exactament NEW, RET o VIP (sensibles a majuscules).
- Qualsevol altra cosa es INVALIDA: es compta i es descarta.

Retorna una linia exactament amb aquest format:

    "<valid> <invalid> <cents> <stores>"

on `<cents>` es la suma dels amount dels valides convertits a centims (arrodonits
a l'enter mes proper) i `<stores>` son els `store` dels valides, sense duplicats,
ordenats per ordre lexicografic i units per comes (sense espais)."""
TEST_CODE = """public class Test {
    public static void main(String[] args) {
        String got = Solution.process("sales.csv");
        String want = "7 6 4977 EU,EU, North,US,ca";
        if (!want.equals(got)) throw new RuntimeException("want [" + want + "] got [" + got + "]");
        System.out.println("OK");
    }
}"""
EXTRA_FILES = {"sales.csv": """# vendes setembre 2026
EU,10.00,NEW
US,20.50,VIP
"EU, North",5.25,NEW
EU,0.75,RET
US,3.00,BAD
EU,10.00
"EU, North",2.20,vip
ca,1.50,NEW
 EU ,4.00,VIP
US,1E2,NEW
EU,-5.00,NEW
"Broken, quote,4.00,NEW
US,7.77,VIP
"""}
