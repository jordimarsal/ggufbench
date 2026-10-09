ID = "memo_fib_hard"
LANG = "typescript"
PROMPT = """Implementa fib(n: number): number amb memoitzacio (un Map intern o similar): fib(0)=0,
fib(1)=1. Ha de respondre instantaniament fins a n=50: la recursio nua no passa el test."""
TEST_CODE = """import { fib } from './solution';
if (fib(0) !== 0) throw new Error('fail');
if (fib(1) !== 1) throw new Error('fail');
if (fib(10) !== 55) throw new Error('fail');
const t0 = Date.now();
if (fib(50) !== 12586269025) throw new Error('fail');
if (Date.now() - t0 > 2000) throw new Error('massa lent: cal memoitzacio');
console.log('OK');"""
