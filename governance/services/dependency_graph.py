"""Dependency Graph — DFS cycle detection and transitive resolution.

Generic graph operations used by rule dependency analysis.
Per SRP: Graph algorithms are separate from rule CRUD/query logic.
Per DRY: Reusable for any entity type with dependency relations.

Created: 2026-03-25 (EPIC-RULES-V3-P2)
"""
from typing import Dict, List, Set


class DependencyGraph:
    """Directed graph with DFS-based cycle detection.

    Args:
        adjacency: Mapping of node → set of direct dependencies.
    """

    def __init__(self, adjacency: Dict[str, Set[str]]):
        self._adj: Dict[str, Set[str]] = {
            k: set(v) for k, v in adjacency.items()
        }

    def detect_cycles(self) -> List[List[str]]:
        """Find all cycles using DFS with coloring.

        Returns:
            List of cycles, each cycle is a list of node IDs forming the loop.
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {}
        # Initialize all nodes (including those only appearing as targets)
        all_nodes = set(self._adj.keys())
        for deps in self._adj.values():
            all_nodes.update(deps)
        for node in all_nodes:
            color[node] = WHITE

        path: List[str] = []
        cycles: List[List[str]] = []

        def dfs(node: str) -> None:
            color[node] = GRAY
            path.append(node)
            for neighbor in self._adj.get(node, set()):
                if color.get(neighbor, WHITE) == GRAY:
                    # Found back edge — extract cycle
                    idx = path.index(neighbor)
                    cycles.append(list(path[idx:]))
                elif color.get(neighbor, WHITE) == WHITE:
                    dfs(neighbor)
            path.pop()
            color[node] = BLACK

        for node in sorted(all_nodes):
            if color[node] == WHITE:
                dfs(node)

        return cycles

    def get_transitive_dependencies(self, node: str) -> Set[str]:
        """Get all transitive dependencies for a node via BFS.

        Handles cycles safely — visited set prevents infinite loops.
        """
        if node not in self._adj:
            return set()

        visited: Set[str] = set()
        stack = list(self._adj.get(node, set()))
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            stack.extend(self._adj.get(current, set()) - visited)

        return visited

    @property
    def is_acyclic(self) -> bool:
        """True if the graph has no cycles."""
        return len(self.detect_cycles()) == 0

    @property
    def circular_count(self) -> int:
        """Number of distinct cycles in the graph."""
        return len(self.detect_cycles())

    @property
    def node_count(self) -> int:
        """Total unique nodes in the graph."""
        all_nodes = set(self._adj.keys())
        for deps in self._adj.values():
            all_nodes.update(deps)
        return len(all_nodes)

    @property
    def edge_count(self) -> int:
        """Total directed edges."""
        return sum(len(deps) for deps in self._adj.values())
