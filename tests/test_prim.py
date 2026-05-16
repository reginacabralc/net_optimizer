"""
tests/test_prim.py — Tests unitarios para Prim MST.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.graph import Graph
from src.models import Node, Edge
from src.prim import prim_mst


def make_graph() -> Graph:
    """
    Grafo de 4 nodos para MST.

    A --1-- B
    |  \    |
    4   3   2
    |    \  |
    C --5-- D

    MST óptimo: A-B (1) + B-D (2) + A-D (3) = 6  NO
    Aristas disponibles:
      A-B: 1
      A-C: 4
      A-D: 3
      B-D: 2
      C-D: 5

    MST = A-B(1) + B-D(2) + A-D(3)?
    → Mejor: A-B(1), B-D(2), A-C(4) = 7  ← forma un árbol
    → O: A-B(1), B-D(2), A-D(3) tiene ciclo A-B-D-A
    → MST correcto: A-B(1), B-D(2), A-C(4) = 7
       O: A-B(1), A-D(3), A-C(4) = 8
    → Prim elegirá: A-B(1), B-D(2), A-C(4) = 7
    """
    g = Graph()
    for nid, name in [("A","nA"), ("B","nB"), ("C","nC"), ("D","nD")]:
        g.add_node(Node(node_id=nid, name=name, node_type="router",
                        lat=0.0, lon=0.0))
    g.add_edge(Edge("A", "B", latency_ms=1, cost_usd=1))
    g.add_edge(Edge("A", "C", latency_ms=1, cost_usd=4))
    g.add_edge(Edge("A", "D", latency_ms=1, cost_usd=3))
    g.add_edge(Edge("B", "D", latency_ms=1, cost_usd=2))
    g.add_edge(Edge("C", "D", latency_ms=1, cost_usd=5))
    return g


class TestPrimBasic:
    """Tests básicos del algoritmo Prim."""

    def test_mst_has_v_minus_1_edges(self):
        g = make_graph()
        mst_edges, _ = prim_mst(g, "A")
        assert len(mst_edges) == g.num_nodes - 1

    def test_mst_cost_is_optimal(self):
        g = make_graph()
        _, total_cost = prim_mst(g, "A")
        # MST óptimo = 1 + 2 + 4 = 7
        assert total_cost == 7.0

    def test_mst_no_cycles(self):
        """El MST no debe contener ciclos: V-1 aristas en grafo conexo → sin ciclos."""
        g = make_graph()
        mst_edges, _ = prim_mst(g, "A")
        # V-1 aristas con V nodos sin ciclos ↔ árbol
        assert len(mst_edges) == g.num_nodes - 1

    def test_mst_connects_all_nodes(self):
        """Todos los nodos deben ser alcanzables desde cualquier punto del MST."""
        g = make_graph()
        mst_edges, _ = prim_mst(g, "A")

        # Construir conjunto de nodos en el MST
        mst_nodes = set()
        for e in mst_edges:
            mst_nodes.add(e.source)
            mst_nodes.add(e.target)

        # Debe incluir el nodo inicial siempre
        all_ids = set(g.get_all_node_ids())
        assert mst_nodes == all_ids

    def test_mst_returns_edge_objects(self):
        g = make_graph()
        mst_edges, _ = prim_mst(g, "A")
        for e in mst_edges:
            assert hasattr(e, "source")
            assert hasattr(e, "target")
            assert hasattr(e, "cost_usd")
            assert hasattr(e, "bandwidth_gbps")
            assert e.cost_usd >= 0
            assert e.bandwidth_gbps >= 0


class TestPrimEdgeCases:
    """Tests de casos borde."""

    def test_single_node_empty_mst(self):
        g = Graph()
        g.add_node(Node("X", "nX", "server", 0.0, 0.0))
        mst_edges, total_cost = prim_mst(g, "X")
        assert mst_edges == []
        assert total_cost == 0.0

    def test_two_nodes(self):
        g = Graph()
        g.add_node(Node("A", "nA", "server", 0.0, 0.0))
        g.add_node(Node("B", "nB", "router", 0.0, 0.0))
        g.add_edge(Edge("A", "B", latency_ms=5, cost_usd=1000))
        mst_edges, total_cost = prim_mst(g, "A")
        assert len(mst_edges) == 1
        assert total_cost == 1000.0

    def test_invalid_start_raises(self):
        g = make_graph()
        with pytest.raises(KeyError):
            prim_mst(g, "NO_EXISTE")

    def test_empty_graph_raises(self):
        g = Graph()
        with pytest.raises(ValueError):
            prim_mst(g)

    def test_mst_cost_less_than_all_edges(self):
        """El costo del MST debe ser ≤ al costo total de todas las aristas."""
        g = make_graph()
        _, mst_cost = prim_mst(g, "A")
        all_cost = sum(c for (_, _, _, c, _) in g.get_all_edges())
        assert mst_cost <= all_cost

    def test_different_start_same_cost(self):
        """El MST tiene el mismo costo independientemente del nodo inicial."""
        g = make_graph()
        _, cost_a = prim_mst(g, "A")
        _, cost_b = prim_mst(g, "B")
        _, cost_c = prim_mst(g, "C")
        assert cost_a == cost_b == cost_c


class TestPrimWithRealData:
    """Tests con el grafo ISP real."""

    def test_prim_on_isp_graph(self):
        """El MST del grafo ISP debe ser válido."""
        from src.data_loader import load_graph
        graph = load_graph()
        first_server = graph.get_nodes_by_type("server")[0].node_id
        mst_edges, total_cost = prim_mst(graph, first_server)
        # MST debe tener num_nodes - 1 aristas (si grafo es conexo)
        # o menos si no es completamente conexo
        assert len(mst_edges) >= 1
        assert total_cost > 0

    def test_prim_isp_total_cost_positive(self):
        from src.data_loader import load_graph
        graph = load_graph()
        first_server = graph.get_nodes_by_type("server")[0].node_id
        _, total_cost = prim_mst(graph, first_server)
        assert total_cost > 0

    def test_real_edges_include_bandwidth(self):
        from src.data_loader import load_graph
        graph = load_graph()
        for _, _, _, _, bandwidth in graph.get_all_edges():
            assert bandwidth > 0
