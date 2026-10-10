ID = "interval_codec_expert"
LANG = "java"
PROMPT = """Implementa la classe Solution com un registre d' intervals d'enters, amb
constructor buit i aquests metodes d'instancia:

- boolean add(int lo, int hi): afegeix l'interval [lo, hi] al registre. Els
  intervals se solapen o es toquen (inclouen punts adjacents: [1,6] i [7,10] es
  toquen) es FUSIONEN en un de sol. Retorna true si algo ha canviat; false si
  l'interval ja estava cobert totalment, o si lo > hi (en aquest cas no toca res).
- boolean remove(int lo, int hi): treu els punts de [lo, hi] del registre. Pot
  PARTIR un interval en dos (p.ex. treure [5,7] de [1,10] deixa [1,4] i [8,10]).
  Retorna true si algo ha canviat; false si no hi havia res a treure (o lo > hi).
  Mai no deixis intervals buits (lo > hi) al registre.
- List<int[]> toList(): els intervals actuals, ordenats per lo, disjunts i ja
  fusionats (cada un {lo, hi}).

El registre es aïllat per instància: dos Solution no comparteixen estat."""
TEST_CODE = """import java.util.*;

public class Test {
    static void check(Solution s, int[][] want, String tag) {
        List<int[]> got = s.toList();
        if (got.size() != want.length)
            throw new RuntimeException(tag + ": size " + got.size() + " != " + want.length);
        for (int i = 0; i < want.length; i++) {
            if (got.get(i)[0] != want[i][0] || got.get(i)[1] != want[i][1])
                throw new RuntimeException(tag + " @" + i + ": [" + got.get(i)[0] + "," + got.get(i)[1] + "]");
        }
    }

    public static void main(String[] args) {
        Solution s = new Solution();
        s.add(1, 5);
        s.add(8, 10);
        s.add(4, 6);
        check(s, new int[][]{{1, 6}, {8, 10}}, "solapa i toca");
        if (!s.add(7, 8)) throw new RuntimeException("add(7,8) cobre el 7 (forat) -> true");
        check(s, new int[][]{{1, 10}}, "fusiona en cadena");
        if (s.add(2, 3)) throw new RuntimeException("cobert totalment -> false");
        check(s, new int[][]{{1, 10}}, "invariants despres de add redundant");
        if (!s.add(13, 15)) throw new RuntimeException("add nou -> true");
        if (s.add(9, 1)) throw new RuntimeException("lo > hi -> false");
        check(s, new int[][]{{1, 10}, {13, 15}}, "dos intervals");
        if (!s.remove(5, 7)) throw new RuntimeException("remove interior -> true");
        check(s, new int[][]{{1, 4}, {8, 10}, {13, 15}}, "remove parteix");
        if (s.remove(5, 6)) throw new RuntimeException("res a treure -> false");
        if (!s.remove(0, 20)) throw new RuntimeException("ho trau tot -> true");
        check(s, new int[][]{}, "buit");
        if (s.remove(1, 2)) throw new RuntimeException("buit -> false");
        Solution u = new Solution();
        u.add(20, 30);
        if (!u.remove(25, 25)) throw new RuntimeException("punt al mig -> true");
        check(u, new int[][]{{20, 24}, {26, 30}}, "forat d'un punt");
        Solution v = new Solution();
        check(v, new int[][]{}, "instancia nova");
        if (v.add(0, 0) == false) throw new RuntimeException("add(0,0) -> true");
        check(v, new int[][]{{0, 0}}, "interval puntual");
        System.out.println("OK");
    }
}"""
