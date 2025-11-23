from abc import ABC, abstractmethod


class AbstractGraph(ABC):
    def __init__(self, numVertices: int):
        if not isinstance(numVertices, int):
            raise TypeError("Número de vértices deve ser inteiro")
        if numVertices < 0:
            raise ValueError("Número de vértices não pode ser negativo")
        self._num_vertices = numVertices
        self._vertex_weights = [0.0 for _ in range(numVertices)]
        self._edge_count = 0

    def _validate_vertex_index(self, v: int):
        if not isinstance(v, int):
            raise TypeError("Índice de vértice deve ser inteiro")
        if v < 0 or v >= self._num_vertices:
            raise IndexError("Índice de vértice fora dos limites")

    def _validate_edge_indices(self, u: int, v: int):
        self._validate_vertex_index(u)
        self._validate_vertex_index(v)
        if u == v:
            raise ValueError("Grafo simples não permite laços")

    def _increment_edge_count(self):
        self._edge_count += 1

    def _decrement_edge_count(self):
        if self._edge_count == 0:
            raise ValueError("Não há arestas para remover")
        self._edge_count -= 1

    def getVertexCount(self) -> int:
        return self._num_vertices

    def getEdgeCount(self) -> int:
        return self._edge_count

    @abstractmethod
    def hasEdge(self, u: int, v: int) -> bool:
        ...

    @abstractmethod
    def addEdge(self, u: int, v: int) -> None:
        ...

    @abstractmethod
    def removeEdge(self, u: int, v: int) -> None:
        ...

    def isSucessor(self, u: int, v: int) -> bool:
        self._validate_edge_indices(u, v)
        return self.hasEdge(u, v)

    def isPredessor(self, u: int, v: int) -> bool:
        self._validate_edge_indices(u, v)
        return self.hasEdge(v, u)

    def isDivergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        self._validate_edge_indices(u1, v1)
        self._validate_edge_indices(u2, v2)
        if not self.hasEdge(u1, v1) or not self.hasEdge(u2, v2):
            return False
        return u1 == u2 and v1 != v2

    def isConvergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        self._validate_edge_indices(u1, v1)
        self._validate_edge_indices(u2, v2)
        if not self.hasEdge(u1, v1) or not self.hasEdge(u2, v2):
            return False
        return v1 == v2 and u1 != u2

    def isIncident(self, u: int, v: int, x: int) -> bool:
        self._validate_edge_indices(u, v)
        self._validate_vertex_index(x)
        if not self.hasEdge(u, v):
            return False
        return x == u or x == v

    @abstractmethod
    def getVertexInDegree(self, u: int) -> int:
        ...

    @abstractmethod
    def getVertexOutDegree(self, u: int) -> int:
        ...

    def setVertexWeight(self, v: int, w: float) -> None:
        self._validate_vertex_index(v)
        self._vertex_weights[v] = float(w)

    def getVertexWeight(self, v: int) -> float:
        self._validate_vertex_index(v)
        return self._vertex_weights[v]

    @abstractmethod
    def setEdgeWeight(self, u: int, v: int, w: float) -> None:
        ...

    @abstractmethod
    def getEdgeWeight(self, u: int, v: int) -> float:
        ...

    @abstractmethod
    def isConnected(self) -> bool:
        ...

    def isEmptyGraph(self) -> bool:
        return self._edge_count == 0

    def isCompleteGraph(self) -> bool:
        n = self._num_vertices
        expected_edges = n * (n - 1)
        return self._edge_count == expected_edges

    @abstractmethod
    def exportToGEPHI(self, path: str) -> None:
        ...
