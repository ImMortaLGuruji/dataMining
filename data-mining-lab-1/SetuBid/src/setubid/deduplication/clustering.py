"""Opportunity Clustering and Graph Union-Find Module for SetuBid.

Clusters candidate pairs into connected components of deduplicated procurement opportunities.
"""

from __future__ import annotations
from typing import Dict, List, Set, Tuple, Any, Optional


class DisjointSetUnion:
    """Disjoint Set Union (Union-Find) with path compression and union by rank."""

    def __init__(self):
        self.parent: Dict[str, str] = {}
        self.rank: Dict[str, int] = {}

    def find(self, x: str) -> str:
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
            return x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str) -> bool:
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x == root_y:
            return False

        # Deterministic union: higher rank wins, tie-break by lexicographical order of root
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            # Deterministic tie-breaker
            if root_x < root_y:
                self.parent[root_y] = root_x
                self.rank[root_x] += 1
            else:
                self.parent[root_x] = root_y
                self.rank[root_y] += 1
        return True

    def get_clusters(self) -> Dict[str, List[str]]:
        """Returns map from root -> list of member elements (sorted for determinism)."""
        clusters = {}
        for elem in self.parent:
            root = self.find(elem)
            if root not in clusters:
                clusters[root] = []
            clusters[root].append(elem)
        for root in clusters:
            clusters[root].sort()
        return clusters


def cluster_verified_pairs(notice_ids: List[str], verified_pairs: List[Tuple[str, str]]) -> Dict[str, List[str]]:
    """Clusters notices based on verified duplicate pairwise edges."""
    dsu = DisjointSetUnion()
    for nid in notice_ids:
        dsu.find(nid)

    # Sort pairs for complete determinism
    sorted_pairs = sorted(verified_pairs)
    for a, b in sorted_pairs:
        dsu.union(a, b)

    return dsu.get_clusters()
