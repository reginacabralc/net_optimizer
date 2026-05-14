"""
kdtree.py — KD-tree 2D para localizar el servidor más cercano.

Implementación manual de un KD-tree bidimensional (lat, lon).
Se construye con los nodos tipo 'server' del grafo ISP y permite
encontrar el servidor geográficamente más cercano a un nuevo cliente.

Complejidad:
    build:          O(n log n)  — ordenar en cada nivel
    nearest_neighbor: O(log n) promedio  (O(n) peor caso: datos lineales)
    Espacio:        O(n)

Por qué KD-tree y no búsqueda lineal:
    Búsqueda lineal: O(n) — recorrer todos los servidores
    KD-tree:         O(log n) promedio — divide el espacio recursivamente

    Con 5 servidores la diferencia es mínima, pero con 1000 servidores:
    Lineal:  1000 comparaciones
    KD-tree: ~10 comparaciones

Cómo funciona:
    - En cada nivel del árbol, se divide el espacio por un eje (lat o lon).
    - Nivel par → dividir por latitud (eje 0)
    - Nivel impar → dividir por longitud (eje 1)
    - El nodo raíz es el mediano de todos los puntos en el eje actual.
    - Búsqueda: desciende por el árbol descartando mitades del espacio.
"""

import math
from typing import List, Optional, Tuple

from src.models import Node


class _KDNode:
    """Nodo interno del KD-tree."""

    __slots__ = ("point", "left", "right")

    def __init__(
        self,
        point: Node,
        left: Optional["_KDNode"] = None,
        right: Optional["_KDNode"] = None,
    ) -> None:
        self.point = point        # El Node (servidor) en este nodo
        self.left = left          # Subárbol izquierdo (menor en el eje)
        self.right = right        # Subárbol derecho (mayor en el eje)


def _euclidean_dist(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia euclídea entre dos coordenadas GPS.

    Nota: Para distancias cortas (misma ciudad) la distancia euclídea
    es una aproximación razonable. Para distancias intercontinentales
    se usaría la fórmula de Haversine.

    Args:
        lat1, lon1: Coordenadas del punto 1.
        lat2, lon2: Coordenadas del punto 2.

    Returns:
        Distancia euclídea en grados (aproximación de distancia geográfica).
    """
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)


def _haversine_dist(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Distancia Haversine entre dos coordenadas GPS (en kilómetros).

    Fórmula exacta para distancia sobre la esfera terrestre.
    Se usa en el reporte final para mostrar km reales.

    Args:
        lat1, lon1: Coordenadas del punto 1 (grados decimales).
        lat2, lon2: Coordenadas del punto 2 (grados decimales).

    Returns:
        Distancia en kilómetros.
    """
    R = 6371.0  # Radio de la Tierra en km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class KDTree:
    """
    KD-tree 2D para búsqueda de vecino más cercano en coordenadas GPS.

    Uso:
        tree = KDTree()
        tree.build(server_nodes)
        nearest_node, distance_km = tree.nearest_neighbor(lat, lon)
    """

    def __init__(self) -> None:
        """Inicializa el KD-tree vacío."""
        self._root: Optional[_KDNode] = None
        self._size: int = 0

    def build(self, nodes: List[Node]) -> None:
        """
        Construye el KD-tree a partir de una lista de nodos (servidores).

        Algoritmo:
            1. En el nivel actual, elegir eje (0=lat, 1=lon) según profundidad.
            2. Ordenar los puntos por el eje elegido.
            3. El mediano se convierte en la raíz del subárbol.
            4. Recursión en la mitad izquierda y derecha.

        Esto garantiza un árbol balanceado con profundidad O(log n).

        Args:
            nodes: Lista de Node a insertar (típicamente servidores).

        Raises:
            ValueError: Si la lista está vacía.
        """
        if not nodes:
            raise ValueError("No se pueden construir KD-tree con lista vacía.")
        self._size = len(nodes)
        self._root = self._build_recursive(nodes, depth=0)

    def _build_recursive(
        self, nodes: List[Node], depth: int
    ) -> Optional[_KDNode]:
        """
        Construye el subárbol recursivamente.

        Args:
            nodes: Lista de nodos a insertar en este subárbol.
            depth: Profundidad actual (determina el eje de división).

        Returns:
            Raíz del subárbol construido, o None si nodes está vacío.
        """
        if not nodes:
            return None

        # Eje actual: 0 → latitud, 1 → longitud
        axis = depth % 2

        # Ordenar por el eje actual y elegir el mediano como raíz
        sorted_nodes = sorted(
            nodes, key=lambda n: n.lat if axis == 0 else n.lon
        )
        median_idx = len(sorted_nodes) // 2
        median_node = sorted_nodes[median_idx]

        # Construir subárboles izquierdo y derecho recursivamente
        left_subtree = self._build_recursive(
            sorted_nodes[:median_idx], depth + 1
        )
        right_subtree = self._build_recursive(
            sorted_nodes[median_idx + 1:], depth + 1
        )

        return _KDNode(
            point=median_node,
            left=left_subtree,
            right=right_subtree,
        )

    def nearest_neighbor(
        self, lat: float, lon: float
    ) -> Tuple[Optional[Node], float]:
        """
        Encuentra el servidor más cercano a la coordenada (lat, lon).

        Algoritmo de búsqueda:
            1. Descender por el árbol como si se insertara el punto.
            2. Al llegar a una hoja, actualizar el mejor candidato.
            3. Al subir, verificar si el otro subárbol puede contener
               un punto más cercano (comparando distancia con el plano
               de división del eje actual).
            4. Si sí, explorar el otro subárbol también.

        Args:
            lat: Latitud del nuevo cliente.
            lon: Longitud del nuevo cliente.

        Returns:
            (nodo_más_cercano, distancia_en_km)
            (None, inf) si el árbol está vacío.
        """
        if self._root is None:
            return None, float("inf")

        # Estado de la búsqueda: [mejor_nodo, mejor_distancia_euclídea]
        best: List = [None, float("inf")]

        self._search_recursive(self._root, lat, lon, depth=0, best=best)

        best_node = best[0]
        if best_node is None:
            return None, float("inf")

        # Calcular distancia real en km con Haversine
        dist_km = _haversine_dist(lat, lon, best_node.lat, best_node.lon)
        return best_node, dist_km

    def _search_recursive(
        self,
        node: Optional[_KDNode],
        lat: float,
        lon: float,
        depth: int,
        best: List,
    ) -> None:
        """
        Búsqueda recursiva del vecino más cercano.

        Args:
            node:  Nodo actual del KD-tree.
            lat:   Latitud del punto de consulta.
            lon:   Longitud del punto de consulta.
            depth: Profundidad actual.
            best:  [mejor_nodo, mejor_distancia] — se modifica in-place.
        """
        if node is None:
            return

        # Calcular distancia euclídea al punto actual
        current_dist = _euclidean_dist(lat, lon, node.point.lat, node.point.lon)

        # Actualizar mejor si este punto es más cercano
        if current_dist < best[1]:
            best[0] = node.point
            best[1] = current_dist

        # Eje actual y diferencia en ese eje
        axis = depth % 2
        diff = (lat - node.point.lat) if axis == 0 else (lon - node.point.lon)

        # Ir primero por el lado donde cae el punto de consulta
        close_side = node.left if diff <= 0 else node.right
        far_side = node.right if diff <= 0 else node.left

        # Explorar el lado cercano
        self._search_recursive(close_side, lat, lon, depth + 1, best)

        # Explorar el lado lejano SOLO si el plano de división
        # está más cerca que el mejor actual (podría haber un punto más cercano)
        if abs(diff) < best[1]:
            self._search_recursive(far_side, lat, lon, depth + 1, best)

    def __len__(self) -> int:
        return self._size

    def __repr__(self) -> str:
        return f"KDTree(size={self._size})"
