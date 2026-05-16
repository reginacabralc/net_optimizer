"""
graph.py — Grafo no dirigido ponderado con lista de adyacencia.

Internamente usa el HashMap propio para indexar nodos y almacenar
las listas de adyacencia. Cada arista tiene dos pesos:
  - latency_ms: usado por Dijkstra
  - cost_usd:   usado por Prim
  - bandwidth_gbps: capacidad informativa del enlace

Complejidad de espacio: O(V + E)
"""

from typing import List, Optional, Tuple

from src.hash_map import HashMap
from src.models import Edge, Node


# Tipo de cada entrada en la lista de adyacencia:
# (neighbor_id, latency_ms, cost_usd, bandwidth_gbps)
AdjEntry = Tuple[str, float, float, float]


class Graph:
    """
    Grafo no dirigido y ponderado para la red ISP.

    Almacena nodos en un HashMap[node_id → Node] y
    la lista de adyacencia en HashMap[node_id → List[AdjEntry]].

    Adicionalmente mantiene un índice por nombre:
    HashMap[name → node_id] para búsqueda O(1) por nombre.
    """

    def __init__(self) -> None:
        """Inicializa el grafo vacío."""
        # Índice principal: node_id → Node
        self._nodes: HashMap = HashMap()
        # Lista de adyacencia: node_id → [(neighbor_id, latencia, costo, ancho_banda)]
        self._adj: HashMap = HashMap()
        # Índice por nombre: name → node_id
        self._name_index: HashMap = HashMap()

    # ── Inserción ────────────────────────────────────────────────────────────

    def add_node(self, node: Node) -> None:
        """
        Agrega un nodo al grafo.

        Si el node_id ya existe, sobreescribe el nodo.

        Parámetros:
            node: Objeto Node a insertar.
        """
        self._nodes.put(node.node_id, node)
        self._name_index.put(node.name, node.node_id)
        # Inicializar lista de adyacencia si no existe
        if not self._adj.contains(node.node_id):
            self._adj.put(node.node_id, [])

    def add_edge(self, edge: Edge) -> None:
        """
        Agrega una arista no dirigida al grafo.

        La arista se registra en ambas direcciones (origen→destino y destino→origen).

        Parámetros:
            edge: Objeto Edge con source, target, latency_ms, cost_usd y bandwidth_gbps.

        Raises:
            ValueError: Si alguno de los nodos no existe en el grafo.
        """
        if not self._nodes.contains(edge.source):
            raise ValueError(
                f"Nodo origen '{edge.source}' no existe en el grafo."
            )
        if not self._nodes.contains(edge.target):
            raise ValueError(
                f"Nodo destino '{edge.target}' no existe en el grafo."
            )

        # origen → destino
        neighbors_src: List[AdjEntry] = self._adj.get(edge.source)
        neighbors_src.append(
            (edge.target, edge.latency_ms, edge.cost_usd, edge.bandwidth_gbps)
        )

        # destino → origen (grafo no dirigido)
        neighbors_tgt: List[AdjEntry] = self._adj.get(edge.target)
        neighbors_tgt.append(
            (edge.source, edge.latency_ms, edge.cost_usd, edge.bandwidth_gbps)
        )

    # ── Consultas ─────────────────────────────────────────────────────────────

    def get_node(self, node_id: str) -> Node:
        """
        Retorna el nodo con el ID dado.

        Parámetros:
            node_id: Identificador del nodo.

        Retorna:
            Objeto Node.

        Raises:
            KeyError: Si el nodo no existe.
        """
        return self._nodes.get(node_id)

    def get_node_by_name(self, name: str) -> Node:
        """
        Retorna el nodo con el nombre dado (búsqueda O(1) via HashMap).

        Parámetros:
            name: Nombre legible del nodo (ej: 'Centro de Datos Norte').

        Retorna:
            Objeto Node.

        Raises:
            KeyError: Si el nombre no existe.
        """
        node_id = self._name_index.get(name)
        return self._nodes.get(node_id)

    def get_neighbors(self, node_id: str) -> List[AdjEntry]:
        """
        Retorna la lista de vecinos de un nodo.

        Parámetros:
            node_id: ID del nodo.

        Retorna:
            Lista de (neighbor_id, latency_ms, cost_usd, bandwidth_gbps).
        """
        return self._adj.get_or_default(node_id, [])

    def get_all_nodes(self) -> List[Node]:
        """
        Retorna todos los nodos del grafo.

        Retorna:
            Lista de objetos Node.
        """
        return self._nodes.values()

    def get_nodes_by_type(self, node_type: str) -> List[Node]:
        """
        Retorna todos los nodos de un tipo específico.

        Parámetros:
            node_type: 'server' | 'router' | 'switch' | 'user'

        Retorna:
            Lista filtrada de nodos.
        """
        return [n for n in self._nodes.values() if n.node_type == node_type]

    def get_all_node_ids(self) -> List[str]:
        """Retorna lista de todos los node_ids."""
        return self._nodes.keys()

    def node_exists(self, node_id: str) -> bool:
        """Verifica si un nodo existe."""
        return self._nodes.contains(node_id)

    def get_all_edges(self) -> List[Tuple[str, str, float, float, float]]:
        """
        Retorna todas las aristas del grafo (sin duplicados).

        Retorna:
            Lista de (source_id, target_id, latency_ms, cost_usd, bandwidth_gbps).
            Cada arista aparece una sola vez (origen < destino lexicográficamente).
        """
        seen = set()
        edges = []
        for node_id in self._adj.keys():
            for (neighbor, latency, cost, bandwidth) in self._adj.get(node_id):
                key = tuple(sorted([node_id, neighbor]))
                if key not in seen:
                    seen.add(key)
                    edges.append((node_id, neighbor, latency, cost, bandwidth))
        return edges

    # ── Propiedades ───────────────────────────────────────────────────────────

    @property
    def num_nodes(self) -> int:
        """Número de nodos en el grafo."""
        return len(self._nodes)

    @property
    def num_edges(self) -> int:
        """Número de aristas (no dirigidas, sin duplicados)."""
        return len(self.get_all_edges())

    @property
    def node_index(self) -> HashMap:
        """Acceso al HashMap de nodos (para demo y análisis)."""
        return self._nodes

    # ── Representación ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"Grafo(nodos={self.num_nodes}, aristas={self.num_edges})"

    def summary(self) -> str:
        """Retorna un resumen legible del grafo."""
        lines = [
            f"Red ISP — {self.num_nodes} nodos, {self.num_edges} aristas",
            "",
        ]
        type_counts = {}
        for node in self.get_all_nodes():
            type_counts[node.node_type] = type_counts.get(node.node_type, 0) + 1
        labels = {
            "server": "servidor",
            "router": "router",
            "switch": "switch",
            "user": "usuario",
        }
        for ntype, count in sorted(type_counts.items()):
            label = labels.get(ntype, ntype)
            lines.append(f"  {label:8s}: {count} nodo(s)")
        return "\n".join(lines)
