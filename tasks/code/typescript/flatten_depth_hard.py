ID = "flatten_depth_hard"
LANG = "typescript"
PROMPT = """Implementa flatten(arr: any[], depth: number): any[] que aplani arrays niuats fins a
depth nivells (depth 1 = un nivell, depth 0 = copia superficial, depth = Infinity =
aplanament total). No has de mutar l'entrada."""
TEST_CODE = """import { flatten } from './solution';
const src = [1, [2, [3, [4]]]];
if (JSON.stringify(flatten(src, 0)) !== '[1,[2,[3,[4]]]]') throw new Error('fail');
if (JSON.stringify(flatten(src, 1)) !== '[1,2,[3,[4]]]') throw new Error('fail');
if (JSON.stringify(flatten(src, 2)) !== '[1,2,3,[4]]') throw new Error('fail');
if (JSON.stringify(flatten(src, Infinity)) !== '[1,2,3,4]') throw new Error('fail');
if (JSON.stringify(flatten([], 3)) !== '[]') throw new Error('fail');
if (JSON.stringify(src) !== '[1,[2,[3,[4]]]]') throw new Error("no mutis l'entrada");
console.log('OK');"""
