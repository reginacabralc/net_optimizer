"""
tests/test_kdtree.py — Tests unitarios para KD-tree 2D.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
import pytest
from src.kdtree import KDTree, _euclidean_dist, _haversine_dist
from src.models import Node


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_server(node_id: str, lat: float, lon: float) -> Node:
    """Crea un nodo tipo server con coordenadas dadas."""
    return Node(
        node_id=node_id,
        name=f"Servidor-{node_id}",
        node_type="server",
        lat=lat,
        lon=lon,
    )


def make_cdmx_servers() -> list:
    """
    Retorna los 5 servidores simulados de la red ISP CDMX.
    Mismas coordenadas que data/nodes.csv.
    """
    return [
        make_server("S01", 19.3984, -99.1587),  # Central
        make_server("S02", 19.4844, -99.1120),  # Norte
        make_server("S03", 19.2571, -99.1032),  # Sur
        make_server("S04", 19.3592, -99.0574),  # Oriente
        make_server("S05", 19.3614, -99.2097),  # Poniente
    ]


# ── Tests de funciones auxiliares ─────────────────────────────────────────────

class TestDistanceFunctions:
    """Tests para las funciones de distancia."""

    def test_euclidean_same_point(self):
        assert _euclidean_dist(10.0, 20.0, 10.0, 20.0) == 0.0

    def test_euclidean_known_value(self):
        # Triángulo 3-4-5: dist((0,0),(3,4)) = 5
        assert abs(_euclidean_dist(0, 0, 3, 4) - 5.0) < 1e-9

    def test_euclidean_symmetric(self):
        d1 = _euclidean_dist(1, 2, 5, 6)
        d2 = _euclidean_dist(5, 6, 1, 2)
        assert abs(d1 - d2) < 1e-9

    def test_haversine_same_point(self):
        assert _haversine_dist(19.43, -99.13, 19.43, -99.13) == 0.0

    def test_haversine_known_distance(self):
        # CDMX (19.43, -99.13) → Guadalajara (20.66, -103.35) ≈ 460 km
        dist = _haversine_dist(19.43, -99.13, 20.66, -103.35)
        assert 400 < dist < 520

    def test_haversine_symmetric(self):
        d1 = _haversine_dist(19.43, -99.13, 20.66, -103.35)
        d2 = _haversine_dist(20.66, -103.35, 19.43, -99.13)
        assert abs(d1 - d2) < 1e-6

    def test_haversine_nonnegative(self):
        dist = _haversine_dist(10.0, -80.0, 15.0, -75.0)
        assert dist >= 0


# ── Tests de construcción ─────────────────────────────────────────────────────

class TestKDTreeBuild:
    """Tests de construcción del KD-tree."""

    def test_build_single_node(self):
        tree = KDTree()
        tree.build([make_server("S01", 19.0, -99.0)])
        assert len(tree) == 1

    def test_build_multiple_nodes(self):
        tree = KDTree()
        servers = make_cdmx_servers()
        tree.build(servers)
        assert len(tree) == 5

    def test_build_empty_raises(self):
        tree = KDTree()
        with pytest.raises(ValueError):
            tree.build([])

    def test_repr(self):
        tree = KDTree()
        tree.build(make_cdmx_servers())
        assert "KDTree" in repr(tree)
        assert "5" in repr(tree)


# ── Tests de búsqueda ─────────────────────────────────────────────────────────

class TestKDTreeNearestNeighbor:
    """Tests del algoritmo de vecino más cercano."""

    def test_empty_tree_returns_none(self):
        tree = KDTree()
        # Árbol sin construir
        result, dist = tree.nearest_neighbor(19.43, -99.13)
        assert result is None
        assert dist == float("inf")

    def test_single_server_always_nearest(self):
        tree = KDTree()
        server = make_server("S01", 19.3984, -99.1587)
        tree.build([server])
        nearest, dist = tree.nearest_neighbor(0.0, 0.0)  # Punto muy lejano
        assert nearest.node_id == "S01"
        assert dist > 0

    def test_exact_location_match(self):
        """Buscar exactamente en las coordenadas de un servidor."""
        servers = make_cdmx_servers()
        tree = KDTree()
        tree.build(servers)
        # Buscar en la ubicación exacta de S01
        nearest, dist = tree.nearest_neighbor(19.3984, -99.1587)
        assert nearest.node_id == "S01"
        assert dist < 0.001  # Prácticamente 0 km

    def test_nearest_to_norte(self):
        """Punto cerca del Servidor-Norte debe retornar S02."""
        servers = make_cdmx_servers()
        tree = KDTree()
        tree.build(servers)
        # Punto muy cerca del servidor norte (S02: 19.4844, -99.1120)
        nearest, dist = tree.nearest_neighbor(19.490, -99.115)
        assert nearest.node_id == "S02"

    def test_nearest_to_sur(self):
        """Punto cerca del Servidor-Sur debe retornar S03."""
        servers = make_cdmx_servers()
        tree = KDTree()
        tree.build(servers)
        # Punto muy cerca del servidor sur (S03: 19.2571, -99.1032)
        nearest, dist = tree.nearest_neighbor(19.260, -99.100)
        assert nearest.node_id == "S03"

    def test_nearest_to_oriente(self):
        """Punto al oriente debe retornar S04."""
        servers = make_cdmx_servers()
        tree = KDTree()
        tree.build(servers)
        # S04: 19.3592, -99.0574
        nearest, dist = tree.nearest_neighbor(19.360, -99.060)
        assert nearest.node_id == "S04"

    def test_nearest_to_poniente(self):
        """Punto al poniente debe retornar S05."""
        servers = make_cdmx_servers()
        tree = KDTree()
        tree.build(servers)
        # S05: 19.3614, -99.2097
        nearest, dist = tree.nearest_neighbor(19.362, -99.215)
        assert nearest.node_id == "S05"

    def test_distance_is_positive(self):
        servers = make_cdmx_servers()
        tree = KDTree()
        tree.build(servers)
        nearest, dist = tree.nearest_neighbor(19.43, -99.18)
        assert dist > 0

    def test_result_is_always_closest(self):
        """
        Verificar contra búsqueda lineal que el KD-tree
        siempre retorna el servidor realmente más cercano.
        """
        servers = make_cdmx_servers()
        tree = KDTree()
        tree.build(servers)

        # Lista de coordenadas de prueba
        test_points = [
            (19.50, -99.15),
            (19.30, -99.10),
            (19.40, -99.20),
            (19.45, -99.13),
            (19.25, -99.05),
            (19.35, -99.18),
        ]

        for lat, lon in test_points:
            # KD-tree result
            kd_nearest, _ = tree.nearest_neighbor(lat, lon)

            # Búsqueda lineal (fuerza bruta)
            linear_nearest = min(
                servers,
                key=lambda s: _euclidean_dist(lat, lon, s.lat, s.lon)
            )

            assert kd_nearest.node_id == linear_nearest.node_id, (
                f"KD-tree retornó {kd_nearest.node_id} pero "
                f"la búsqueda lineal retornó {linear_nearest.node_id} "
                f"para el punto ({lat}, {lon})"
            )

    def test_distance_in_km(self):
        """La distancia retornada debe estar en km (no en grados)."""
        servers = make_cdmx_servers()
        tree = KDTree()
        tree.build(servers)
        # Punto a ~5 km del servidor central
        nearest, dist = tree.nearest_neighbor(19.44, -99.16)
        # La distancia debe ser plausible en km (no en grados ~0.05)
        assert 0.1 < dist < 200  # Entre 100m y 200km

    def test_two_servers_boundary(self):
        """
        Con dos servidores equidistantes, debe retornar uno de ellos
        (no importa cuál, pero no debe fallar).
        """
        s1 = make_server("SA", 10.0, 0.0)
        s2 = make_server("SB", -10.0, 0.0)
        tree = KDTree()
        tree.build([s1, s2])
        # Punto en el ecuador: equidistante de ambos
        nearest, dist = tree.nearest_neighbor(0.0, 0.0)
        assert nearest.node_id in ("SA", "SB")
        assert dist > 0


# ── Tests de integración con datos reales ─────────────────────────────────────

class TestKDTreeWithRealData:
    """Tests usando el grafo ISP cargado desde CSV."""

    def test_kdtree_with_loaded_servers(self):
        from src.data_loader import load_graph
        graph = load_graph()
        servers = graph.get_nodes_by_type("server")
        assert len(servers) > 0

        tree = KDTree()
        tree.build(servers)
        assert len(tree) == len(servers)

        # Buscar desde el centro de CDMX
        nearest, dist = tree.nearest_neighbor(19.4326, -99.1332)
        assert nearest is not None
        assert nearest.node_type == "server"
        assert dist > 0

    def test_kdtree_result_consistent_with_brute_force(self):
        """KD-tree debe coincidir con búsqueda lineal en datos reales."""
        from src.data_loader import load_graph
        graph = load_graph()
        servers = graph.get_nodes_by_type("server")

        tree = KDTree()
        tree.build(servers)

        # Cliente en Polanco
        lat, lon = 19.4334, -99.1945
        kd_nearest, _ = tree.nearest_neighbor(lat, lon)
        linear_nearest = min(
            servers,
            key=lambda s: _euclidean_dist(lat, lon, s.lat, s.lon)
        )
        assert kd_nearest.node_id == linear_nearest.node_id
