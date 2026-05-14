"""
tests/test_dijkstra.py — Tests unitarios para Dijkstra.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.graph import Graph
from src.models import Node, Edge
from src.dijkstra import dijkstra, reconstruct_path, shortest_path


def make_simple_graph() -> Graph:
    """
    Construye un grafo simple de 5 nodos para pruebas.

          A --2-- B
          |       |
          4       1
          |       |
          C --3-- D --5-- E

    Ruta A→E con menor latencia: A→B→D→E = 2+1+5 = 8
    Ruta A→D: A→B→D = 3, A→C→D = 7
    """
    g = Graph()
    for nid, name in [("A","nA"),("B","nB"),("C","nC"),("D","nD"),("E","nE")]:
        g.add_node(Node(node_id=nid, name=name, node_type="router",
                        lat=0.0, lon=0.0))
    edges = [
        Edge("A", "B", latency_ms=2, cost_usd=100),
        Edge("A", "C", latency_ms=4, cost_usd=100),
        Edge("B", "D", latency_ms=1, cost_usd=100),
        Edge("C", "D", latency_ms=3, cost_usd=100),
        Edge("D", "E", latency_ms=5, cost_usd=100),
    ]
    for e in edges:
        g.add_edge(e)
    return g


class TestDijkstraBasic:
    """Tests básicos del algoritmo."""

    def test_distance_to_self_is_zero(self):
        g = make_simple_graph()
        dist, _ = dijkstra(g, "A")
        assert dist["A"] == 0.0

    def test_direct_edge_distance(self):
        g = make_simple_graph()
        dist, _ = dijkstra(g, "A")
        assert dist["B"] == 2.0

    def test_optimal_path_found(self):
        """A→E debe ser 8 (A→B→D→E), no 14 (A→C→D→E)."""
        g = make_simple_graph()
        dist, _ = dijkstra(g, "A")
        assert dist["E"] == 8.0

    def test_intermediate_optimal(self):
        """A→D debe ser 3 (A→B→D), no 7 (A→C→D)."""
        g = make_simple_graph()
        dist, _ = dijkstra(g, "A")
        assert dist["D"] == 3.0

    def test_all_distances_from_a(self):
        g = make_simple_graph()
        dist, _ = dijkstra(g, "A")
        assert dist["A"] == 0.0
        assert dist["B"] == 2.0
        assert dist["C"] == 4.0
        assert dist["D"] == 3.0
        assert dist["E"] == 8.0


class TestDijkstraPath:
    """Tests de reconstrucción de caminos."""

    def test_reconstruct_path_a_to_e(self):
        g = make_simple_graph()
        dist, prev = dijkstra(g, "A", "E")
        path = reconstruct_path(prev, "A", "E")
        assert path == ["A", "B", "D", "E"]

    def test_reconstruct_path_a_to_d(self):
        g = make_simple_graph()
        dist, prev = dijkstra(g, "A", "D")
        path = reconstruct_path(prev, "A", "D")
        assert path == ["A", "B", "D"]

    def test_reconstruct_path_to_self(self):
        g = make_simple_graph()
        dist, prev = dijkstra(g, "A", "A")
        path = reconstruct_path(prev, "A", "A")
        assert path == ["A"]

    def test_shortest_path_convenience(self):
        g = make_simple_graph()
        latency, path = shortest_path(g, "A", "E")
        assert latency == 8.0
        assert path == ["A", "B", "D", "E"]


class TestDijkstraEdgeCases:
    """Tests de casos borde."""

    def test_no_path_returns_inf(self):
        """Grafo con nodo aislado — no hay camino."""
        g = make_simple_graph()
        # Agregar nodo aislado
        g.add_node(Node(node_id="Z", name="nZ", node_type="user",
                        lat=0.0, lon=0.0))
        dist, _ = dijkstra(g, "A")
        assert dist["Z"] == float("inf")

    def test_shortest_path_no_path(self):
        g = make_simple_graph()
        g.add_node(Node(node_id="Z", name="nZ", node_type="user",
                        lat=0.0, lon=0.0))
        latency, path = shortest_path(g, "A", "Z")
        assert latency == float("inf")
        assert path == []

    def test_invalid_source_raises(self):
        g = make_simple_graph()
        with pytest.raises(KeyError):
            dijkstra(g, "NO_EXISTE")

    def test_invalid_target_raises(self):
        g = make_simple_graph()
        with pytest.raises(KeyError):
            dijkstra(g, "A", "NO_EXISTE")

    def test_single_node_graph(self):
        g = Graph()
        g.add_node(Node("X", "nX", "server", 0.0, 0.0))
        dist, _ = dijkstra(g, "X")
        assert dist["X"] == 0.0

    def test_symmetric_distances(self):
        """En grafo no dirigido, dist(A,B) == dist(B,A)."""
        g = make_simple_graph()
        dist_from_a, _ = dijkstra(g, "A")
        dist_from_b, _ = dijkstra(g, "B")
        assert dist_from_a["B"] == dist_from_b["A"]

    def test_early_termination_with_target(self):
        """Dijkstra con target debe dar el mismo resultado que sin target."""
        g = make_simple_graph()
        dist_full, _ = dijkstra(g, "A")
        dist_target, _ = dijkstra(g, "A", "E")
        assert dist_target["E"] == dist_full["E"]
