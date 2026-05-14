"""
prim.py — Prim para red de fibra de costo mínimo (MST).

Implementación manual del algoritmo de Prim usando min-heap.
Construye el Árbol de Expansión Mínima (MST) del grafo ISP
minimizando el costo de instalación de fibra óptica (cost_usd).

Complejidad:
    Tiempo: O(E log V)  con min-heap
    Espacio: O(V + E)

Por qué Prim y no Kruskal:
    Kruskal: O(E log E) — ordena todas las aristas primero.
    Prim:    O(E log V) — crece desde un nodo, más eficiente en
             grafos densos donde E >> V.
    La red ISP puede tener muchas conexiones redundantes → Prim gana.

    Kruskal requiere Union-Find para evitar ciclos.
    Prim usa un conjunto 'visited' más simple de implementar.

El MST responde la pregunta:
    ¿Cuál es la red mínima de cables de fibra que conecta TODOS
    los nodos de la red ISP con el menor costo total?
"""

import heapq
from typing import List, Optional, Set, Tuple

from src.graph import Graph
from src.models import Edge

# Infinito para inicialización
_INF = float("inf")


def prim_mst(
    graph: Graph,
    start_id: Optional[str] = None,
) -> Tuple[List[Edge], float]:
    """
    Construye el MST de menor costo usando el algoritmo de Prim.

    Inicia desde start_id y crece el árbol agregando siempre
    la arista de menor costo que conecte un nodo nuevo al árbol.

    Args:
        graph:    Grafo de la red ISP.
        start_id: ID del nodo inicial. Si es None, usa el primer nodo.

    Returns:
        (mst_edges, total_cost)
        mst_edges:  Lista de Edge que forman el MST.
        total_cost: Costo total en USD del MST.

    Raises:
        ValueError: Si el grafo está vacío.
        KeyError:   Si start_id no existe en el grafo.
    """
    all_ids = graph.get_all_node_ids()
    if not all_ids:
        raise ValueError("El grafo está vacío, no se puede calcular MST.")

    if start_id is None:
        start_id = all_ids[0]
    elif not graph.node_exists(start_id):
        raise KeyError(f"Nodo inicial '{start_id}' no existe.")

    # Conjunto de nodos ya incluidos en el MST
    in_mst: Set[str] = set()
    in_mst.add(start_id)

    # Aristas del MST resultante
    mst_edges: List[Edge] = []
    total_cost: float = 0.0

    # Min-heap: (cost_usd, source_id, target_id, latency_ms)
    # Iniciamos con todas las aristas del nodo inicial
    heap: List[Tuple[float, str, str, float]] = []
    for (neighbor, latency, cost) in graph.get_neighbors(start_id):
        heapq.heappush(heap, (cost, start_id, neighbor, latency))

    # Continuar hasta que el MST tenga V-1 aristas o no haya más candidatas
    while heap and len(mst_edges) < graph.num_nodes - 1:
        # Extraer la arista de menor costo — O(log E)
        cost, u, v, latency = heapq.heappop(heap)

        # Si v ya está en el MST, esta arista formaría un ciclo → saltar
        if v in in_mst:
            continue

        # Agregar v al MST
        in_mst.add(v)
        total_cost += cost

        # Registrar la arista como parte del MST
        mst_edges.append(Edge(
            source=u,
            target=v,
            latency_ms=latency,
            cost_usd=cost,
        ))

        # Agregar al heap las aristas de v hacia nodos aún no en el MST
        for (neighbor, neigh_latency, neigh_cost) in graph.get_neighbors(v):
            if neighbor not in in_mst:
                heapq.heappush(heap, (neigh_cost, v, neighbor, neigh_latency))

    # Advertir si el grafo no es conexo (no se pudo conectar todos los nodos)
    if len(mst_edges) < graph.num_nodes - 1:
        connected = len(in_mst)
        print(
            f"[PRIM] Advertencia: el grafo no es completamente conexo. "
            f"MST conecta {connected}/{graph.num_nodes} nodos."
        )

    return mst_edges, total_cost


def mst_summary(mst_edges: List[Edge], graph: Graph) -> str:
    """
    Genera un resumen legible del MST para la demo.

    Args:
        mst_edges: Lista de aristas del MST.
        graph:     Grafo para obtener nombres de nodos.

    Returns:
        String formateado con el resumen del MST.
    """
    lines = [
        f"MST — Red de fibra de costo mínimo",
        f"Aristas: {len(mst_edges)} | "
        f"Costo total: ${sum(e.cost_usd for e in mst_edges):,.0f} USD",
        "",
    ]
    for i, edge in enumerate(mst_edges, 1):
        try:
            src_name = graph.get_node(edge.source).name
            tgt_name = graph.get_node(edge.target).name
        except KeyError:
            src_name = edge.source
            tgt_name = edge.target
        lines.append(
            f"  {i:2d}. {src_name:28s} → {tgt_name:28s} "
            f"  ${edge.cost_usd:>8,.0f} USD  |  {edge.latency_ms} ms"
        )
    return "\n".join(lines)
