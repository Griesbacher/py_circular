from __future__ import annotations

import importlinter
from grimp.adaptors.graph import ImportGraph
from importlinter import ContractCheck
from importlinter.application import output

from py_circular import ImportAST


class PyCircularContract(importlinter.Contract):
    def check(self, graph: ImportGraph) -> ContractCheck:
        circular_imports = ImportAST.build_from_abstract_import_graph(graph).find_circular_imports()
        return ContractCheck(kept=len(circular_imports) == 0, metadata=circular_imports)

    def render_broken_contract(self, check: ContractCheck) -> None:
        output.print_error(ImportAST.print_circular_imports(check.metadata), bold=True)
