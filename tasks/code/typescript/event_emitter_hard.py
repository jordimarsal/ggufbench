ID = "event_emitter_hard"
LANG = "typescript"
PROMPT = """Implementa una classe EventEmitter amb on(event, cb), off(event, cb), once(event, cb) i
emit(event, ...args): emit crida els listeners amb els args i retorna true si n'hi havia,
false altrament; off elimina nomes aquella funcio; once registra un listener que es
desregistra sol despres de la primera emit."""
TEST_CODE = """import { EventEmitter } from './solution';
const seen: string[] = [];
const e = new EventEmitter();
if (e.emit('x') !== false) throw new Error('fail');
const cb = (v: number) => seen.push('cb' + v);
e.on('x', cb);
e.on('x', (v: number) => seen.push('altre' + v));
if (e.emit('x', 1) !== true) throw new Error('fail');
e.off('x', cb);
if (e.emit('x', 2) !== true) throw new Error('fail');
const onceSeen: number[] = [];
e.once('y', (v: number) => onceSeen.push(v));
e.emit('y', 7);
e.emit('y', 8);
if (onceSeen.length !== 1 || onceSeen[0] !== 7) throw new Error('fail');
if (seen.join('|') !== 'cb1|altre1|altre2') throw new Error('fail');
console.log('OK');"""
