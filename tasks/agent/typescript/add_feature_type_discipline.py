ID = "add_feature_type_discipline"
LANG = "typescript"
GOAL = "Add an area function to solution.ts that computes the area of a Circle using its radius (area = Math.PI * r * r). Update the Circle interface in solution.ts to include the area property."
INITIAL_FILES = {"solution.ts": "export type Shape = 'circle' | 'square';\n\nexport interface Circle {\n    kind: 'circle';\n    radius: number;\n}\n\nexport interface Square {\n    kind: 'square';\n    side: number;\n}\n\nexport function circumference(c: Circle): number {\n    return 2 * Math.PI * c.radius;\n}", "test_solution.ts": "import { Circle } from './solution';\nimport { circumference, area } from './solution';\nconst circle: Circle = { kind: 'circle', radius: 5 };\nif (Math.abs(area(circle) - 78.53981633974483) > 0.001) throw new Error('wrong area');\nconsole.log('OK')"}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 8
