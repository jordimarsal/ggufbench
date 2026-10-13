ID = "discriminated_union_exhaustiveness"
LANG = "typescript"
GOAL = "Arregla solution.ts perquè passi els tests. La funció describeShape no gestiona el variant 'triangle'."
INITIAL_FILES = {
    "solution.ts": "export type Shape = 'circle' | 'square' | 'triangle';\n\nexport interface Circle {\n    kind: 'circle';\n    radius: number;\n}\n\nexport interface Square {\n    kind: 'square';\n    side: number;\n}\n\nexport interface Triangle {\n    kind: 'triangle';\n    base: number;\n    height: number;\n}\n\nexport function describeShape(shape: Circle | Square | Triangle): string {\n    switch (shape.kind) {\n        case 'circle': return `Circle with radius ${shape.radius}`;\n        case 'square': return `Square with side ${shape.side}`;\n    }\n}",
    "test_solution.ts": "import { describeShape, Circle, Square, Triangle } from './solution';\nconst c: Circle = { kind: 'circle', radius: 5 };\nif (!describeShape(c).includes('radius')) throw new Error('wrong');\nconst s: Square = { kind: 'square', side: 4 };\nif (!describeShape(s).includes('side')) throw new Error('wrong');\nconst t: Triangle = { kind: 'triangle', base: 3, height: 4 };\nif (!describeShape(t).includes('base')) throw new Error('missing triangle');\nconsole.log('OK')"
}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 8
