ID = "invoice_dup_merge"
LANG = "java"
GOAL = "Arregla Solution.java perquè la classe Store no sobreescriu els articles duplicats: quan hi ha dues línies amb el mateix nom cal acumular-los en un sol ítem i calcular el total correctament."
INITIAL_FILES = {
    "Solution.java": """import java.util.*;

public class Solution {
    public static Invoice parseAndBuild(List<String> lines) {
        List<String> parsed = Parse.readLines(lines);
        Store store = new Store();
        for (String line : parsed) {
            String[] parts = line.split(",");
            String name = parts[0].trim();
            int qty = Integer.parseInt(parts[1].trim());
            int unitCents = Integer.parseInt(parts[2].trim());
            Item item = new Item(name, qty, unitCents);
            store.add(item);
        }
        return new Invoice(store.getItems());
    }
}""",
    "Parse.java": """import java.util.*;

public class Parse {
    public static List<String> readLines(List<String> raw) {
        List<String> result = new ArrayList<>();
        for (String s : raw) {
            if (!s.trim().isEmpty()) result.add(s);
        }
        return result;
    }
}""",
    "Item.java": """class Item {
    final String name;
    final int qty;
    final int unitCents;
    Item(String n, int q, int u) { name=n; qty=q; unitCents=u; }
    int total() { return qty * unitCents; }
}""",
    "Store.java": """import java.util.*;

class Store {
    private Map<String, Item> items = new HashMap<>();
    void add(Item item) {
        // BUG: put() overwrites previous entry with same key
        items.put(item.name, item);
    }
    List<Item> getItems() {
        List<Item> list = new ArrayList<>(items.values());
        Collections.sort(list, Comparator.comparing(i -> i.name));
        return list;
    }
}""",
    "Invoice.java": """import java.util.*;

class Invoice {
    final List<Item> items;
    Invoice(List<Item> it) { items=it; }
    int total() { int s=0; for(Item i:items) s+=i.total(); return s; }
}""",
    "Test.java": """import java.io.*;
import java.nio.file.*;
import java.util.*;

public class Test {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("input.txt"),
            "Rice,2,500\\nBeans,1,300\\nRice,3,500\\nMilk,1,400\\nBeans,2,300\\n");
        List<String> lines = Parse.readLines(Files.readAllLines(Path.of("input.txt")));
        Invoice inv = Solution.parseAndBuild(lines);
        if (inv.items.size() != 3)
            throw new RuntimeException("fail: expected 3 unique items");
        // Sorted by name: Beans(3,300), Milk(1,400), Rice(5,500)
        Item beans = inv.items.get(0); // B < M < R alphabetically
        if (!beans.name.equals("Beans") || beans.qty != 3 || beans.unitCents != 300)
            throw new RuntimeException("fail: beans wrong");
        Item rice = inv.items.get(2); // Rice last
        if (!rice.name.equals("Rice") || rice.qty != 5 || rice.unitCents != 500)
            throw new RuntimeException("fail: rice wrong");
        if (inv.total() != 2500+900+400)
            throw new RuntimeException("fail: total=" + inv.total());
        System.out.println("OK");
    }
}""",
}
TEST_FILE = "Test.java"
MAX_TURNS = 14
