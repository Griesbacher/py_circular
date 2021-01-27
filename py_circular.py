#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from typing import Set, List, Dict, FrozenSet, TypeVar, Optional, Pattern

import grimp  # type: ignore
from grimp.application.ports.graph import AbstractImportGraph  # type: ignore

T = TypeVar('T')


class ImportAST:
    @dataclass(frozen=True)
    class Module:
        name: str
        imports: FrozenSet[str]

    def __init__(self, modules: Set[ImportAST.Module]) -> None:
        self._modules: Dict[str, ImportAST.Module] = dict()
        for module in modules:
            self._modules[module.name] = module

    @classmethod
    def build_from_abstract_import_graph(cls, graph):
        return cls({
            ImportAST.Module(name=module, imports=frozenset(graph.find_modules_that_directly_import(module)))
            for module in graph.modules
        })

    def __repr__(self):
        return os.linesep.join(
            f"{name} -> {', '.join(i for i in self._modules[name].imports)}" for name in sorted(self._modules.keys())
        )

    def find_circular_imports(self) -> List[List[str]]:
        graph = {name: list(module.imports) for name, module in self._modules.items()}
        return [scc for scc in ImportAST.strongly_connected_components(graph) if len(scc) > 1]

    @staticmethod
    def print_circular_imports(imports: List[List[str]]) -> None:
        if imports:
            print("The following circular imports exist:")
            for i in imports:
                print(" - " + ", ".join(i))

    @staticmethod
    def strongly_connected_components(graph: Dict[T, List[T]]) -> List[List[T]]:
        """
        based on:
        - http://www.logarithmic.net/pfh/blog/01208083168
        - https://en.wikipedia.org/wiki/Tarjan%27s_strongly_connected_components_algorithm
        """

        index_counter = [0]
        stack = []
        low_link = {}
        index = {}
        result = []

        def _strong_connect(n: T):
            index[n] = index_counter[0]
            low_link[n] = index_counter[0]
            index_counter[0] += 1
            stack.append(n)

            successors = graph[n]
            for successor in successors:
                if successor not in index:
                    _strong_connect(successor)
                    low_link[n] = min(low_link[n], low_link[successor])
                elif successor in stack:
                    low_link[n] = min(low_link[n], index[successor])

            if low_link[n] == index[n]:
                connected_component = []

                while True:
                    successor = stack.pop()
                    connected_component.append(successor)
                    if successor == n:
                        break
                result.append(connected_component[:])

        for node in graph:
            if node not in index:
                _strong_connect(node)

        return result


def build_graph(package_name: List[str], exclude_regex: Optional[Pattern]) -> AbstractImportGraph:
    graph = grimp.build_graph(*package_name)
    if exclude_regex:
        for module in graph.modules:
            if re.search(exclude_regex, module):
                graph.squash_module(module)
    return graph


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--packages", help="packages to search for circular imports", nargs='+', required=True)
    parser.add_argument("-e", "--exclude", help="regex to exclude modules", nargs='?')
    args = parser.parse_args()

    re_exclude = re.compile(args.exclude) if args.exclude else None

    ast = ImportAST.build_from_abstract_import_graph(build_graph(args.packages, re_exclude))
    circular_imports = ast.find_circular_imports()
    ImportAST.print_circular_imports(circular_imports)
    if circular_imports:
        exit(1)
