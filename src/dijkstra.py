"""
dijkstra.py — Dijkstra para ruta de menor latencia.

Implementación manual del algoritmo de Dijkstra usando min-heap.
Encuentra la ruta de menor latencia (ms) entre dos nodos del grafo ISP.

Complejidad:
    Tiempo: O((V + E) log V)  con min-heap
    Espacio: O(V)             para dist[] y prev[]

Por qué Dijkstra y no BFS:
    BFS encuentra el camino con menos saltos (hops), pero no minimiza
    la latencia total. Dijkstra usa pesos (latency_ms) y garantiza
    el camino óptimo en grafos con pesos no negativos.

Por qué no Bellman-Ford:
    Bellman-Ford soporta pesos negativos → O(VE).
    Las latencias siempre son ≥ 0, por lo que Dijkstra es correcto
    y más eficiente: O((V+E) log V) vs O(VE).
"""

import heapq
from typing import Dict, List, Optional, Tuple

from src.graph import Graph

# Valor que representa "infinito" para inicializar distancias
_INF = float("inf")


def dijkstra(
    graph: Graph,
    source_id: str,
    target_id: Optional[str] = None,
) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """
    Ejecuta Dijkstra desde source_id sobre el grafo.

    Implementación con min-heap (priority queue). En cada iteración
    extrae el nodo de menor distancia acumulada y relaja sus vecinos.

    Args:
        graph:     Grafo de la red ISP.
        source_id: ID del nodo origen.
        target_id: (Opcional) ID del nodo destino. Si se provee,
                   el algoritmo termina temprano al encontrar target.

    Returns:
        dist: dict[node_id → distancia_mínima_desde_source]
        prev: dict[node_id → nodo_previo_en_ruta_óptima]

    Raises:
        KeyError: Si source_id o target_id no existen en el grafo.
    """
    if not graph.node_exists(source_id):
        raise KeyError(f"Nodo origen '{source_id}' no existe en el grafo.")
    if target_id is not None and not graph.node_exists(target_id):
        raise KeyError(f"Nodo destino '{target_id}' no existe en el grafo.")

    # Inicializar distancias en infinito y prev en None
    dist: Dict[str, float] = {
        node_id: _INF for node_id in graph.get_all_node_ids()
    }
    prev: Dict[str, Optional[str]] = {
        node_id: None for node_id in graph.get_all_node_ids()
    }

    # La distancia al origen es 0
    dist[source_id] = 0.0

    # Min-heap: (distancia_acumulada, node_id)
    # heapq es un min-heap de Python stdlib — no implementa Dijkstra,
    # es solo la estructura de datos que usamos para la selección greedy.
    heap: List[Tuple[float, str]] = [(0.0, source_id)]

    # Conjunto de nodos ya procesados (visitados definitivamente)
    visited: set = set()

    while heap:
        # Extraer nodo con menor distancia acumulada — O(log V)
        current_dist, u = heapq.heappop(heap)

        # Si ya fue procesado, ignorar (puede haber duplicados en el heap)
        if u in visited:
            continue
        visited.add(u)

        # Terminación temprana si encontramos el destino
        if target_id is not None and u == target_id:
            break

        # Relajar aristas de los vecinos de u
        for (v, latency, _cost) in graph.get_neighbors(u):
            if v in visited:
                continue

            # ¿Encontramos un camino más corto hacia v a través de u?
            new_dist = current_dist + latency
            if new_dist < dist[v]:
                dist[v] = new_dist
                prev[v] = u
                # Insertar en heap con nueva distancia — O(log V)
                heapq.heappush(heap, (new_dist, v))

    return dist, prev


def reconstruct_path(
    prev: Dict[str, Optional[str]],
    source_id: str,
    target_id: str,
) -> List[str]:
    """
    Reconstruye el camino óptimo desde source hasta target.

    Sigue los punteros 'prev' desde target hasta source en reversa.

    Args:
        prev:      Diccionario de predecesores retornado por dijkstra().
        source_id: ID del nodo origen.
        target_id: ID del nodo destino.

    Returns:
        Lista de node_ids representando el camino [source, ..., target].
        Lista vacía si no hay camino.
    """
    path: List[str] = []
    current = target_id

    # Recorrer hacia atrás desde target hasta source
    while current is not None:
        path.append(current)
        current = prev.get(current)
        # Si llegamos al source, paramos
        if current == source_id:
            path.append(source_id)
            break
    else:
        # Si el while terminó sin break, no hay camino válido
        if not path or path[-1] != source_id:
            return []

    path.reverse()

    # Verificar que el camino empieza en source
    if not path or path[0] != source_id:
        return []

    return path


def shortest_path(
    graph: Graph,
    source_id: str,
    target_id: str,
) -> Tuple[float, List[str]]:
    """
    Calcula la ruta de menor latencia entre source y target.

    Función de conveniencia que combina dijkstra() + reconstruct_path().

    Args:
        graph:     Grafo de la red ISP.
        source_id: ID del nodo origen.
        target_id: ID del nodo destino.

    Returns:
        (latencia_total_ms, [source_id, ..., target_id])
        Si no hay camino, retorna (inf, []).

    Example:
        >>> latency, path = shortest_path(graph, "U01", "S01")
        >>> print(f"Latencia: {latency} ms, Ruta: {' → '.join(path)}")
    """
    dist, prev = dijkstra(graph, source_id, target_id)
    total_latency = dist.get(target_id, _INF)

    if total_latency == _INF:
        return _INF, []

    path = reconstruct_path(prev, source_id, target_id)
    return total_latency, path


def dijkstra_with_steps(graph: Graph, source_id: str) -> List[dict]:
    """
    Ejecuta Dijkstra capturando el estado de dist[] en cada iteración.
    Usado para la animación paso a paso en el dashboard y el timelapse del mapa.

    Args:
        graph:     Grafo de la red ISP.
        source_id: ID del nodo origen.

    Returns:
        Lista de dicts con estado en cada paso. Cada dict contiene:
          - current: nodo siendo procesado
          - dist:    distancias mínimas hasta ese paso
          - source:  nodo origen
          - visited: lista ordenada de nodos ya asentados
          - prev:    árbol de caminos mínimos (prev[v] = u)
    """
    dist: Dict[str, float] = {
        node_id: _INF for node_id in graph.get_all_node_ids()
    }
    prev: Dict[str, Optional[str]] = {
        node_id: None for node_id in graph.get_all_node_ids()
    }
    dist[source_id] = 0.0
    heap: List[Tuple[float, str]] = [(0.0, source_id)]
    visited: set = set()
    visited_order: List[str] = []
    steps: List[dict] = []

    while heap:
        current_dist, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        visited_order.append(u)

        for (v, latency, _cost) in graph.get_neighbors(u):
            if v in visited:
                continue
            new_dist = current_dist + latency
            if new_dist < dist[v]:
                dist[v] = new_dist
                prev[v] = u
                heapq.heappush(heap, (new_dist, v))

        steps.append({
            "current": u,
            "dist": dict(dist),
            "source": source_id,
            "visited": list(visited_order),
            "prev": dict(prev),
        })

    return steps
