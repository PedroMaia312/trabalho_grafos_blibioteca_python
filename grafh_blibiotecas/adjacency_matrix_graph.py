from typing import Optional, List
from grafh_blibiotecas.abstract_graph import AbstractGraph


class AdjacencyMatrixGraph(AbstractGraph):
    def __init__(self, numVertices: int):
        super().__init__(numVertices)
        self._matrix: List[List[Optional[float]]] = [
            [None for _ in range(numVertices)] for _ in range(numVertices)
        ]

    def hasEdge(self, u: int, v: int) -> bool:
        self._validate_edge_indices(u, v)
        return self._matrix[u][v] is not None

    def addEdge(self, u: int, v: int) -> None:
        self._validate_edge_indices(u, v)
        if not self.hasEdge(u, v):
            self._matrix[u][v] = 1.0
            self._increment_edge_count()

    def removeEdge(self, u: int, v: int) -> None:
        self._validate_edge_indices(u, v)
        if not self.hasEdge(u, v):
            raise ValueError("Aresta inexistente")
        self._matrix[u][v] = None
        self._decrement_edge_count()

    def getVertexInDegree(self, u: int) -> int:
        self._validate_vertex_index(u)
        count = 0
        for i in range(self._num_vertices):
            if self._matrix[i][u] is not None:
                count += 1
        return count

    def getVertexOutDegree(self, u: int) -> int:
        self._validate_vertex_index(u)
        count = 0
        for j in range(self._num_vertices):
            if self._matrix[u][j] is not None:
                count += 1
        return count

    def setEdgeWeight(self, u: int, v: int, w: float) -> None:
        self._validate_edge_indices(u, v)
        if not self.hasEdge(u, v):
            raise ValueError("Não é possível definir peso de aresta inexistente")
        self._matrix[u][v] = float(w)

    def getEdgeWeight(self, u: int, v: int) -> float:
        self._validate_edge_indices(u, v)
        if not self.hasEdge(u, v):
            raise ValueError("Aresta inexistente")
        value = self._matrix[u][v]
        if value is None:
            raise ValueError("Aresta inexistente")
        return float(value)

    def isConnected(self) -> bool:
        n = self._num_vertices
        if n == 0:
            return False
        visited = [False] * n
        stack = [0]
        visited[0] = True
        while stack:
            u = stack.pop()
            for v in range(n):
                if self._matrix[u][v] is not None or self._matrix[v][u] is not None:
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
                for v in range(self._num_vertices):
                    if self._matrix[u][v] is not None:
                        w = self._matrix[u][v]
                        f_edges.write(f"{u};{v};{w}\n")
