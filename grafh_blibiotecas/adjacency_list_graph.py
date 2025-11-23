from typing import Dict, List
from grafh_blibiotecas.abstract_graph import AbstractGraph


class AdjacencyListGraph(AbstractGraph):
    def __init__(self, numVertices: int):
        super().__init__(numVertices)
        self._adjacency: List[Dict[int, float]] = [{} for _ in range(numVertices)]

    def hasEdge(self, u: int, v: int) -> bool:
        self._validate_edge_indices(u, v)
        return v in self._adjacency[u]

    def addEdge(self, u: int, v: int) -> None:
        self._validate_edge_indices(u, v)
        if not self.hasEdge(u, v):
            self._adjacency[u][v] = 1.0
            self._increment_edge_count()

    def removeEdge(self, u: int, v: int) -> None:
        self._validate_edge_indices(u, v)
        if not self.hasEdge(u, v):
            raise ValueError("Aresta inexistente")
        del self._adjacency[u][v]
        self._decrement_edge_count()

    def getVertexInDegree(self, u: int) -> int:
        self._validate_vertex_index(u)
        count = 0
        for i in range(self._num_vertices):
            if u in self._adjacency[i]:
                count += 1
        return count

    def getVertexOutDegree(self, u: int) -> int:
        self._validate_vertex_index(u)
        return len(self._adjacency[u])

    def setEdgeWeight(self, u: int, v: int, w: float) -> None:
        self._validate_edge_indices(u, v)
        if not self.hasEdge(u, v):
            raise ValueError("Não é possível definir peso de aresta inexistente")
        self._adjacency[u][v] = float(w)

    def getEdgeWeight(self, u: int, v: int) -> float:
        self._validate_edge_indices(u, v)
        if not self.hasEdge(u, v):
            raise ValueError("Aresta inexistente")
        return float(self._adjacency[u][v])

    def isConnected(self) -> bool:
        n = self._num_vertices
        if n == 0:
            return False
        reverse_adj: List[List[int]] = [[] for _ in range(n)]
        for u in range(n):
            for v in self._adjacency[u].keys():
                reverse_adj[v].append(u)
        visited = [False] * n
        stack = [0]
        visited[0] = True
        while stack:
            u = stack.pop()
            for v in self._adjacency[u].keys():
                if not visited[v]:
                    visited[v] = True
                    stack.append(v)
            for v in reverse_adj[u]:
                if not visited[v]:
                    visited[v] = True
                    stack.append(v)
        return all(visited)

    def exportToGEPHI(self, path: str) -> None:
        if not path:
            raise ValueError("Caminho inválido")
        nodes_path = f"{path}_nodes.csv"
        edges_path = f"{path}_edges.csv"
        with open(nodes_path, "w", encoding="utf-8") as f_nodes:
            f_nodes.write("id;label;weight\n")
            for i in range(self._num_vertices):
                f_nodes.write(f"{i};{i};{self._vertex_weights[i]}\n")
        with open(edges_path, "w", encoding="utf-8") as f_edges:
            f_edges.write("source;target;weight\n")
            for u in range(self._num_vertices):
                for v, w in self._adjacency[u].items():
                    f_edges.write(f"{u};{v};{w}\n")
