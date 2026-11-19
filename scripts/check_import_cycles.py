"""Reject cycles among first-party Python modules without third-party dependencies."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "sentinelforge"


def dependency_graph():
    graph = {}
    for path in PACKAGE.glob("*.py"):
        name = f"sentinelforge.{path.stem}"
        imports = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom):
                if node.level and node.module:
                    imports.add(f"sentinelforge.{node.module.split('.')[0]}")
                elif node.module and node.module.startswith("sentinelforge."):
                    imports.add(".".join(node.module.split(".")[:2]))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("sentinelforge."):
                        imports.add(".".join(alias.name.split(".")[:2]))
        graph[name] = imports
    return graph


def detect_cycles(graph):
    visited, active = set(), []
    cycles = []

    def visit(node):
        if node in active:
            cycles.append(active[active.index(node):] + [node])
            return
        if node in visited:
            return
        active.append(node)
        for target in sorted(graph.get(node, ())):
            if target in graph:
                visit(target)
        active.pop()
        visited.add(node)

    for item in sorted(graph):
        visit(item)
    return cycles


if __name__ == "__main__":
    found = detect_cycles(dependency_graph())
    for cycle in found:
        print("Circular import: " + " -> ".join(cycle))
    if found:
        raise SystemExit(1)
    print("No first-party import cycles detected")
