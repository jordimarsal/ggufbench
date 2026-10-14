ID = "order_merge_duplicates"
LANG = "typescript"
GOAL = """El resum de comandes no suma les linies repetides del mateix article: quan un SKU surt
diverses vegades al fitxer, el resum nomes en conserva una linia i el total surt curt.

Punt d'entrada: `main(lines: string[]): Order[]` de solution.ts, on cada linia és
`sku,qty,unit_cents` i el resultat és un array d'articles (un per SKU, ordenat per SKU) amb
`{ sku, qty, unit, total }`, on `qty` és la suma de quantitats i `total` la suma de
`qty * unit` de totes les linies d'aquell SKU.

Esbrina on fallen les coses: el punt d'entrada no és l'únic fitxer del projecte."""
INITIAL_FILES = {
    "solution.ts": '''import { parseRows } from "./parse.js";
import { mergeOrders } from "./orders.js";


export function main(lines: string[]): Array<{ sku: string; qty: number; unit: number; total: number }> {
    return mergeOrders(parseRows(lines));
}
''',
    "parse.ts": '''import type { Row } from "./types.js";


export function parseRows(lines: string[]): Row[] {
    const out: Row[] = [];
    for (const line of lines) {
        if (line.trim() === "") continue;
        const [sku, qty, unit] = line.split(",");
        const q = Number(sku.trim() === "" ? NaN : qty);
        const u = Number(unit);
        if (!sku || !Number.isInteger(q) || q <= 0 || !Number.isInteger(u) || u < 0) continue;
        out.push({ sku: sku.trim(), qty: q, unit: u });
    }
    return out;
}
''',
    "orders.ts": '''import type { Order, Row } from "./types.js";


export function mergeOrders(rows: Row[]): Order[] {
    // BUG: un map per SKU que es queda amb l'ultima linia en lloc d'acumular
    const bySku = new Map<string, Order>();
    for (const row of rows) {
        bySku.set(row.sku, {
            sku: row.sku,
            qty: row.qty,
            unit: row.unit,
            total: row.qty * row.unit,
        });
    }
    return [...bySku.values()].sort((a, b) => a.sku.localeCompare(b.sku));
}
''',
    "types.ts": '''export interface Row {
    sku: string;
    qty: number;
    unit: number;
}

export interface Order {
    sku: string;
    qty: number;
    unit: number;
    total: number;
}
''',
    "money.ts": '''export function formatCents(cents: number): string {
    const sign = cents < 0 ? "-" : "";
    const abs = Math.abs(cents);
    return `${sign}${Math.trunc(abs / 100)}.${String(abs % 100).padStart(2, "0")}`;
}
''',
    "test_solution.ts": '''import { main } from "./solution.js";
import { formatCents } from "./money.js";

const lines = ["widget,3,250", "cable,2,150", "widget,1,250", "cable,3,150", "  cable , 1 , 150 "];
const orders = main(lines);

if (orders.length !== 2) throw new Error(`escombraries: ${orders.length}`);
if (orders[0].sku !== "cable" || orders[1].sku !== "widget") throw new Error("ordre incorrecte");
if (orders[1].qty !== 4 || orders[1].total !== 4 * 250) throw new Error(`widget: ${JSON.stringify(orders[1])}`);
if (orders[0].qty !== 6 || orders[0].total !== 6 * 150) throw new Error(`cable: ${JSON.stringify(orders[0])}`);
if (formatCents(orders[0].total) !== "9.00") throw new Error("format");

// Linies invalides: es descarten i no alteren res
const mixed = main(["a,1,100", "b,x,50", "a,2,100"]);
if (mixed.length !== 1 || mixed[0].qty !== 3 || mixed[0].total !== 300) {
    throw new Error(`invalides: ${JSON.stringify(mixed)}`);
}
console.log("OK");
''',
}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 14
