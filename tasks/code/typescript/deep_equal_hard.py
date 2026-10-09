ID = "deep_equal_hard"
LANG = "typescript"
PROMPT = """Implementa deepEqual(a: unknown, b: unknown): boolean — igualtat profunda per a null,
numbers, strings, booleans, arrays i objectes plans. L'ordre de les claus d'un objecte NO
compte (JSON.stringify no serveix). Dos NaN es consideren iguals."""
TEST_CODE = """import { deepEqual } from './solution';
if (deepEqual({ a: 1, b: { c: 2 } }, { b: { c: 2 }, a: 1 }) !== true) throw new Error('fail');
if (deepEqual([1, [2, 3]], [1, [2, 3]]) !== true) throw new Error('fail');
if (deepEqual([1, 2], [2, 1]) !== false) throw new Error('fail');
if (deepEqual({ a: 1 }, { a: 1, b: undefined }) !== false) throw new Error('fail');
if (deepEqual(NaN, NaN) !== true) throw new Error('fail');
if (deepEqual(null, null) !== true) throw new Error('fail');
if (deepEqual(null, {}) !== false) throw new Error('fail');
if (deepEqual(1, '1') !== false) throw new Error('fail');
console.log('OK');"""
