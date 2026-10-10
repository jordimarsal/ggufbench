ID = "ledger_debug_expert"
LANG = "java"
PROMPT = """Aquesta classe analitza imports d'un llibre mayor i te 3 errors subtils.
Corregeix-los TORNANT EL FITXER COMPLET (mateixa API). Contracte del fitxer
corregit:
- new Solution(n): finestra dels n darrers imports (n >= 1).
- record(int amount): afegeix; la finestra es queda amb COM A MOLT n elements
  (els n mes recents).
- windowSum(): suma dels elements de la finestra actual.
- averageCents(): mitjana dels elements de la finestra en centims, ARRODONIDA a
  l'enter mes proper (sum * 100.0 / mida); finestra buida -> 0. Ha de ser
  exacte: mitjana de {3,4} = 350, mitjana de {1,2,4} = 233.
- windowArray(): copia DEFENSIVA de la finestra (mida exacta = elements actuals).
  Mutar el resultat NO pot tocar l'estat intern de la instancia.

```java
public class Solution {
    private final int cap;
    private int[] buf;
    private int size;

    public Solution(int n) {
        this.cap = Math.max(n, 1);
        this.buf = new int[cap + 1];   // espai per a tota la finestra
        this.size = 0;
    }

    public void record(int amount) {
        if (size < cap + 1) {
            buf[size++] = amount;
        } else {
            System.arraycopy(buf, 1, buf, 0, size - 1);
            buf[size - 1] = amount;
        }
    }

    public int windowSum() {
        int s = 0;
        for (int i = 0; i < size; i++) s += buf[i];
        return s;
    }

    public long averageCents() {
        if (size == 0) return 0;
        return windowSum() / size * 100;
    }

    public int[] windowArray() {
        return buf;
    }
}
```"""
TEST_CODE = """public class Test {
    public static void main(String[] args) {
        // (a) arrodoniment en centims
        Solution s = new Solution(4);
        s.record(3);
        s.record(4);
        if (s.windowSum() != 7) throw new RuntimeException("sum basica");
        if (s.averageCents() != 350) throw new RuntimeException("avg {3,4} -> 350, va " + s.averageCents());
        Solution q = new Solution(3);
        q.record(1);
        q.record(1);
        q.record(0);
        if (q.averageCents() != 67) throw new RuntimeException("avg {1,1,0} arrodonit -> 67, va " + q.averageCents());
        // (c) copia defensiva de windowArray
        Solution c = new Solution(4);
        c.record(3);
        c.record(4);
        int[] a = c.windowArray();
        if (a.length != 2) throw new RuntimeException("mida exacta -> 2, va " + a.length);
        a[0] = 999;
        if (c.windowSum() != 7) throw new RuntimeException("windowArray ha de ser copia defensiva");
        // (b) la finestra es queda amb com a molt n elements
        Solution t = new Solution(2);
        t.record(1);
        t.record(2);
        t.record(3);
        if (t.windowArray().length != 2) throw new RuntimeException("com a molt n -> 2, va " + t.windowArray().length);
        if (t.windowSum() != 5) throw new RuntimeException("darrers 2 -> 5, va " + t.windowSum());
        // cas buit
        Solution e = new Solution(3);
        if (e.windowSum() != 0 || e.averageCents() != 0) throw new RuntimeException("buida -> 0");
        if (e.windowArray().length != 0) throw new RuntimeException("buida -> array buit");
        System.out.println("OK");
    }
}"""
