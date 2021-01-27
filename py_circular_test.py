import unittest
from dataclasses import dataclass
from typing import List

from py_circular import ImportAST


class TestImportAST(unittest.TestCase):
    def test_find_circular_imports_simple(self):
        @dataclass
        class TestCase:
            name: str
            input: ImportAST
            expected: List[List[str]]

        test_cases: List[TestCase] = [
            TestCase(
                name="simple single circle",
                input=ImportAST({
                    ImportAST.Module(name="a", imports=frozenset({"b"})),
                    ImportAST.Module(name="b", imports=frozenset({"c", "d"})),
                    ImportAST.Module(name="c", imports=frozenset()),
                    ImportAST.Module(name="d", imports=frozenset({"c", "b"})),
                }),
                expected=[["d", "b"]],
            ), TestCase(
                name="no circle",
                input=ImportAST({
                    ImportAST.Module(name="a", imports=frozenset({"b"})),
                    ImportAST.Module(name="b", imports=frozenset({"c"})),
                    ImportAST.Module(name="c", imports=frozenset({})),
                }),
                expected=[],
            ),
        ]

        for test in test_cases:
            with self.subTest(test.name):
                self.assertEqual(test.input.find_circular_imports(), test.expected)


if __name__ == '__main__':
    unittest.main()
