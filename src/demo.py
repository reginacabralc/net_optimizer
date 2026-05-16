"""
demo.py — Demo principal de NetOptimizer.

Script de demostración para la presentación de 10 minutos.
Corre con: python src/demo.py
           python src/demo.py --lat 19.4326 --lon -99.1332

Flujo del demo:
    1. Cargar la red ISP desde CSV
    2. Mostrar estadísticas del HashMap (índice de nodos)
    3. Tomar coordenadas GPS del nuevo cliente
    4. KD-tree: encontrar servidor más cercano
    5. Dijkstra: calcular ruta de menor latencia al servidor
    6. Prim: construir MST (red de fibra de costo mínimo)
    7. Visualizar todo en un gráfico matplotlib
"""

import argparse
import sys
import os
import time

# Agregar el directorio raíz al path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_graph
from src.dijkstra import shortest_path
from src.kdtree import KDTree
from src.prim import prim_mst, mst_summary
from src.visualize import plot_network

# ── Coordenadas por defecto del nuevo cliente ──────────────────────────────────
DEFAULT_LAT = 19.4326   # Centro histórico CDMX
DEFAULT_LON = -99.1332


def print_banner() -> None:
    """Imprime el banner de inicio del demo."""
    print("\n" + "═" * 60)
    print("  🌐  NetOptimizer — ISP Network Optimizer")
    print("      Variante 4 | Estructuras de Datos y Algoritmos")
    print("═" * 60 + "\n")


def print_section(title: str) -> None:
    """Imprime un separador de sección."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print("─" * 60)


def run_demo(client_lat: float, client_lon: float) -> None:
    """
    Ejecuta el demo completo de NetOptimizer.

    Args:
        client_lat: Latitud del nuevo cliente.
        client_lon: Longitud del nuevo cliente.
    """
    print_banner()

    # ── PASO 1: Cargar datos ──────────────────────────────────────────────────
    print_section("PASO 1 — Cargando red ISP desde CSV")
    graph = load_graph(verbose=True)
    print(f"\n  {graph}")

    # ── PASO 2: HashMap — índice de nodos ────────────────────────────────────
    print_section("PASO 2 — HashMap propio (índice O(1) de nodos)")
    print(graph.node_index.stats())

    # Demo de búsqueda por nombre
    test_name = "Datacenter Norte"
    t0 = time.perf_counter()
    try:
        found = graph.get_node_by_name(test_name)
        t1 = time.perf_counter()
        print(f"\n  Búsqueda por nombre '{test_name}': encontrado")
        print(f"  → {found}")
        print(f"  → Tiempo: {(t1-t0)*1e6:.2f} µs  (O(1) promedio)")
    except KeyError:
        print(f"  Nodo '{test_name}' no encontrado.")

    # Comparación conceptual con búsqueda lineal
    print(f"\n  Comparación de complejidad:")
    print(f"  {'Operación':<20} {'HashMap':>12} {'Lista lineal':>15}")
    print(f"  {'─'*50}")
    print(f"  {'Búsqueda por nombre':<20} {'O(1) prom':>12} {'O(n)':>15}")
    print(f"  {'Inserción':<20} {'O(1) amort':>12} {'O(1)':>15}")
    print(f"  {'Eliminación':<20} {'O(1) prom':>12} {'O(n)':>15}")
    print(f"  {'Espacio':<20} {'O(n)':>12} {'O(n)':>15}")

    # ── PASO 3: KD-tree — servidor más cercano ───────────────────────────────
    print_section("PASO 3 — KD-tree: servidor más cercano")
    print(f"  Nuevo cliente en: ({client_lat}, {client_lon})")

    servers = graph.get_nodes_by_type("server")
    kd_tree = KDTree()
    kd_tree.build(servers)
    print(f"  KD-tree construido con {len(kd_tree)} servidores")

    nearest, dist_km = kd_tree.nearest_neighbor(client_lat, client_lon)
    print(f"\n  Servidor más cercano: {nearest.name}")
    print(f"  → ID: {nearest.node_id}")
    print(f"  → Distancia: {dist_km:.3f} km")
    print(f"  → Coordenadas: ({nearest.lat}, {nearest.lon})")

    # Mostrar distancias a todos los servidores (demostrar que es el más cercano)
    print(f"\n  Distancias a todos los servidores:")
    from src.kdtree import _haversine_dist
    for s in sorted(servers, key=lambda x: _haversine_dist(client_lat, client_lon, x.lat, x.lon)):
        d = _haversine_dist(client_lat, client_lon, s.lat, s.lon)
        marker = " ← MÁS CERCANO" if s.node_id == nearest.node_id else ""
        print(f"  {s.name:30s}: {d:6.3f} km{marker}")

    # ── PASO 4: Dijkstra — ruta de menor latencia ────────────────────────────
    print_section("PASO 4 — Dijkstra: ruta de menor latencia")

    # Usamos el servidor más cercano como destino
    # Elegimos un usuario de origen (el más cercano al cliente nuevo)
    users = graph.get_nodes_by_type("user")
    src_node = min(
        users,
        key=lambda u: _haversine_dist(client_lat, client_lon, u.lat, u.lon)
    )

    target_id = nearest.node_id
    source_id = src_node.node_id

    print(f"  Origen:  {graph.get_node(source_id).name} ({source_id})")
    print(f"  Destino: {graph.get_node(target_id).name} ({target_id})")

    latency, path = shortest_path(graph, source_id, target_id)

    if path:
        path_names = [graph.get_node(nid).name for nid in path]
        print(f"\n  Ruta de menor latencia:")
        print(f"  {' → '.join(path_names)}")
        print(f"  Latencia total: {latency:.1f} ms")
        print(f"  Saltos: {len(path) - 1}")
    else:
        print(f"\n  No se encontró ruta entre {source_id} y {target_id}")
        path = []

    # ── PASO 5: Prim — MST de menor costo ────────────────────────────────────
    print_section("PASO 5 — Prim: red de fibra de costo mínimo (MST)")

    first_server = graph.get_nodes_by_type("server")[0].node_id
    mst_edges, total_cost = prim_mst(graph, start_id=first_server)
    print(mst_summary(mst_edges, graph))
    print(f"\n  Ahorro vs conectar todo individualmente:")
    all_edge_cost = sum(c for (_, _, _, c, _) in graph.get_all_edges())
    print(f"  Costo de TODAS las aristas: ${all_edge_cost:>10,.0f} USD")
    print(f"  Costo del MST (Prim):       ${total_cost:>10,.0f} USD")
    print(f"  Ahorro:                     ${all_edge_cost - total_cost:>10,.0f} USD")

    # ── PASO 6: Visualización ─────────────────────────────────────────────────
    print_section("PASO 6 — Visualización")
    print("  Abriendo gráfico de la red ISP...")
    print("  (cierra la ventana para terminar el demo)\n")

    plot_network(
        graph=graph,
        mst_edges=mst_edges,
        dijkstra_path=path if path else None,
        nearest_server=nearest,
        new_client=(client_lat, client_lon),
        title=(
            f"NetOptimizer — Red ISP CDMX\n"
            f"Dijkstra: {latency:.0f} ms | "
            f"MST Prim: ${total_cost:,.0f} USD | "
            f"KD-tree: {nearest.name}"
        ),
        show=True,
    )

    print("═" * 60)
    print("  Demo finalizado. Proyecto: NetOptimizer — Variante 4")
    print("═" * 60 + "\n")


def main() -> None:
    """Entry point principal del demo."""
    parser = argparse.ArgumentParser(
        description="NetOptimizer — Demo de red ISP con Dijkstra, Prim y KD-tree"
    )
    parser.add_argument(
        "--lat",
        type=float,
        default=DEFAULT_LAT,
        help=f"Latitud del nuevo cliente (default: {DEFAULT_LAT})",
    )
    parser.add_argument(
        "--lon",
        type=float,
        default=DEFAULT_LON,
        help=f"Longitud del nuevo cliente (default: {DEFAULT_LON})",
    )
    args = parser.parse_args()

    run_demo(client_lat=args.lat, client_lon=args.lon)


if __name__ == "__main__":
    main()
